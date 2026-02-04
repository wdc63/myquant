# myquant/backend/api/runs.py
"""
运行管理API - 处理回测和模拟的启动、控制、查询
"""

from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import subprocess
import yaml
import json
import time
import signal
import psutil
import requests
import shutil
import socket
import tempfile
import csv
from datetime import datetime
from backend.api.auth import login_required
from backend.extensions import socketio

runs_bp = Blueprint('runs', __name__)

# 策略根目录
STRATEGIES_DIR = Path(__file__).parent.parent.parent / 'strategies'

# 备注存储文件
NOTES_FILE = Path(__file__).parent.parent.parent / 'data' / 'run_notes.json'

# 运行实例管理（内存存储）
# 格式: {run_id: {strategy, mode, pid, port, start_time, status, workspace_dir, is_paused, last_heartbeat}}
active_runs = {}

# 端口管理
# 从全局配置加载监控端口范围
config_path = Path(__file__).resolve().parent.parent.parent / 'myquant_config.json'
with open(config_path, 'r', encoding='utf-8') as f:
    global_config = json.load(f)

monitoring_config = global_config.get('monitoring', {})
port_start = monitoring_config.get('port_range_start', 8051)
port_end = monitoring_config.get('port_range_end', 8100)

PORT_RANGE = range(port_start, port_end)  # 可用端口范围
used_ports = set()

def is_port_in_use(port: int) -> bool:
    """通过尝试绑定一个临时套接字来检查端口是否在系统级别被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # 尝试绑定到 127.0.0.1，避免暴露到网络
            s.bind(("127.0.0.1", port))
        except socket.error:
            # 如果绑定失败，说明端口已被占用
            return True
    # 绑定成功后，套接字会立即在 with 语句结束时关闭，端口被释放
    return False

def get_available_port():
    """获取一个真正未被使用的端口"""
    for port in PORT_RANGE:
        # 双重检查：既不在我们的内存记录中，也不在系统级别被占用
        if port not in used_ports and not is_port_in_use(port):
            used_ports.add(port)
            return port
    raise RuntimeError("没有可用端口，请检查是否有僵尸进程占用了端口或增加端口范围")

def release_port(port):
    """释放端口"""
    if port in used_ports:
        used_ports.discard(port)

def load_notes():
    """加载所有备注"""
    if not NOTES_FILE.exists():
        NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
        return {}
    try:
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载备注文件失败: {e}")
        return {}

def save_notes(notes):
    """保存备注"""
    try:
        NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(NOTES_FILE, 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存备注文件失败: {e}")
        return False

def get_note(run_id):
    """获取单个run的备注"""
    notes = load_notes()
    return notes.get(run_id, '')

def set_note(run_id, note):
    """设置单个run的备注"""
    notes = load_notes()
    notes[run_id] = note
    return save_notes(notes)

def delete_note(run_id):
    """删除单个run的备注"""
    notes = load_notes()
    if run_id in notes:
        del notes[run_id]
        return save_notes(notes)
    return True

def delete_notes_by_strategy(strategy_name):
    """删除某个策略的所有备注"""
    notes = load_notes()
    # 找出所有属于该策略的run_id（格式：strategy_name_mode_timestamp_time）
    keys_to_delete = [run_id for run_id in notes.keys() if run_id.startswith(f"{strategy_name}_")]
    for key in keys_to_delete:
        del notes[key]
    if keys_to_delete:
        return save_notes(notes)
    return True

def is_process_running(pid):
    """检查进程是否在运行"""
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def get_run_status_from_workspace(workspace_dir):
    """
    从工作区文件中推断运行状态
    返回: finished, interrupted, paused, corrupted
    """
    workspace_path = Path(workspace_dir)

    if not workspace_path.exists():
        return 'corrupted'

    final_pkl = list(workspace_path.glob('*_final.pkl'))
    interrupt_pkl = list(workspace_path.glob('*_interrupt.pkl'))
    report_html = workspace_path / 'report.html'
    pause_pkl = list(workspace_path.glob('*_pause.pkl'))

    # 优先检查最终状态 + 报告
    if (final_pkl or interrupt_pkl) and report_html.exists():
        if final_pkl:
            return 'finished'
        else:
            return 'interrupted'

    # 然后检查是否为暂停状态
    elif pause_pkl:
        return 'paused'

    # 如果都找不到，则状态损坏或未知
    else:
        return 'corrupted'

def get_final_return(workspace_dir):
    """
    从 equity.csv 读取最终收益率
    返回: float 或 None
    """
    workspace_path = Path(workspace_dir)
    equity_csv = workspace_path / 'equity.csv'

    if not equity_csv.exists():
        return None

    try:
        with open(equity_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows and 'returns' in rows[-1]:
                # 最后一行的 return 列
                return float(rows[-1]['returns'])
    except Exception as e:
        print(f"Error reading equity.csv: {e}")
        return None

    return None

def get_backtest_date_range(workspace_dir):
    """
    从 snapshot_config.yaml 读取回测起止日期
    返回: (start_date, end_date) 或 (None, None)
    """
    workspace_path = Path(workspace_dir)
    config_snapshot = workspace_path / 'snapshot_config.yaml'

    if not config_snapshot.exists():
        return None, None
    try:
        with open(config_snapshot, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            start_date = config.get('engine', {}).get('start_date')
            end_date = config.get('engine', {}).get('end_date')
            return start_date, end_date
    except Exception as e:
        return None, None

def _get_historical_workspace_dir(run_id):
    """从run_id解析历史运行的工作区路径"""
    parts = run_id.split('_')
    # run_id 格式: {strategy_name}_{mode}_{timestamp}_{time}
    # 例如: my_strategy_backtest_20251021_024635
    if len(parts) < 4:
        return None
    
    # 最后两部分是工作区名称 (时间戳)
    workspace_name = f"{parts[-2]}_{parts[-1]}"
    # 再往前一部分是模式 (mode)
    mode = parts[-3]
    # 再之前的所有部分都是策略名称
    strategy_name = '_'.join(parts[:-3])

    if mode not in ['backtest', 'simulation']:
        return None

    strategy_dir = STRATEGIES_DIR / strategy_name
    if not strategy_dir.exists():
        return None

    strategy_file_stem = (strategy_dir / 'strategy.py').stem
    workspace_dir = strategy_dir / strategy_file_stem / mode / workspace_name
    
    return workspace_dir if workspace_dir.exists() else None

@runs_bp.route('/strategies/<strategy_name>/runs', methods=['GET'])
@login_required
def list_runs(strategy_name):
    """
    列出策略的所有运行实例
    返回: {backtest: [...], simulation: [...]}
    """
    strategy_dir = STRATEGIES_DIR / strategy_name

    if not strategy_dir.exists():
        return jsonify({'error': f'策略 "{strategy_name}" 不存在'}), 404

    runs = {'backtest': [], 'simulation': []}

    for mode in ['backtest', 'simulation']:
        # 根据qtrader的默认行为，工作区在 'strategy' 子目录下
        strategy_file_stem = (strategy_dir / 'strategy.py').stem
        mode_dir = strategy_dir / strategy_file_stem / mode
        if not mode_dir.exists():
            continue

        # 遍历所有运行实例目录
        for run_dir in sorted(mode_dir.iterdir(), reverse=True):
            if run_dir.is_dir() and not run_dir.name.startswith('.'):
                # 生成run_id
                run_id = f"{strategy_name}_{mode}_{run_dir.name}"

                # 检查是否在active_runs中
                if run_id in active_runs:
                    run_info = active_runs[run_id]
                    pid = run_info.get('pid')
                    if pid and is_process_running(pid):
                        # 进程活着，检查是否暂停
                        if run_info.get('is_paused', False):
                            status = 'paused'
                        else:
                            status = 'running'
                    else:
                        # 进程已停止，从active_runs移除
                        del active_runs[run_id]
                        release_port(run_info.get('port'))
                        status = get_run_status_from_workspace(run_dir)
                else:
                    # 从工作区推断状态
                    status = get_run_status_from_workspace(run_dir)

                run_info = {
                    'run_id': run_id,
                    'workspace_dir': str(run_dir),
                    'start_time': run_dir.stat().st_ctime,
                    'status': status,
                    'is_paused': status == 'paused',
                    'is_running': run_id in active_runs,  # 标识是否在活动列表中（运行中或运行时暂停）
                    'note': get_note(run_id)  # 添加备注字段
                }

                # 获取回测起止日期
                start_date, end_date = get_backtest_date_range(run_dir)
                if start_date and end_date:
                    run_info['start_date'] = start_date
                    run_info['end_date'] = end_date

                # 如果是已完成状态，获取最终收益率
                if status == 'finished' or status == 'interrupted':
                    final_return = get_final_return(run_dir)
                    if final_return is not None:
                        run_info['final_return'] = final_return

                runs[mode].append(run_info)

    return jsonify({'runs': runs})

@runs_bp.route('/strategies/<strategy_name>/runs', methods=['POST'])
@login_required
def start_run(strategy_name):
    """
    启动新的回测或模拟
    请求体: {"mode": "backtest" | "simulation"}
    """
    data = request.get_json()
    mode = data.get('mode', 'backtest')

    if mode not in ['backtest', 'simulation']:
        return jsonify({'error': '无效的运行模式'}), 400

    strategy_dir = STRATEGIES_DIR / strategy_name
    if not strategy_dir.exists():
        return jsonify({'error': f'策略 "{strategy_name}" 不存在'}), 404

    # 读取原始配置
    config_path = strategy_dir / 'config.yaml'
    if not config_path.exists():
        return jsonify({'error': '配置文件不存在'}), 404

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        return jsonify({'error': f'配置文件解析失败: {str(e)}'}), 500

    # 分配端口
    try:
        port = get_available_port()
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500

    # 修改配置
    if 'server' not in config:
        config['server'] = {}
    config['server']['enable'] = True
    config['server']['port'] = port
    config['server']['auto_open_browser'] = False

    if 'report' not in config:
        config['report'] = {}

    if 'engine' not in config:
        config['engine'] = {}
    config['engine']['mode'] = mode

    # 创建临时配置文件
    temp_config_path = strategy_dir / f'_temp_config_{int(time.time())}.yaml'
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)

    # 启动qtrader进程
    strategy_file = strategy_dir / 'strategy.py'
    data_provider_file = strategy_dir / 'data_provider.py'

    # 使用platform_runner.py启动
    runner_script = Path(__file__).parent.parent / 'utils' / 'platform_runner.py'

    cmd = [
        'python', str(runner_script),
        '--config', str(temp_config_path),
        '--strategy', str(strategy_file),
        '--data-provider', str(data_provider_file)
    ]

    process = None
    try:
        # 启动子进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0
        )

        # 轮询HTTP端点，等待 qtrader 的内部服务器完全就绪
        wait_time = 20
        end_time = time.time() + wait_time
        server_ready = False
        import requests

        while time.time() < end_time:
            try:
                # 尝试向 qtrader 服务器的根URL发送一个真正的HTTP GET请求
                response = requests.get(f"http://127.0.0.1:{port}/", timeout=0.5)
                # 只有收到 200 OK 状态码，才代表服务完全准备就绪
                if response.status_code == 200:
                    server_ready = True
                    break
            except (requests.ConnectionError, requests.Timeout):
                # 如果连接被拒绝或超时，说明服务还未就绪，短暂等待后重试
                time.sleep(0.5)

        if not server_ready:
            raise RuntimeError(f"在 {wait_time} 秒内 qtrader 服务器未能启动或响应。")

        # 服务器已就绪，现在可以安全地查找工作区目录了
        strategy_file_stem = (strategy_dir / 'strategy.py').stem
        mode_dir = strategy_dir / strategy_file_stem / mode
        workspaces = sorted(mode_dir.glob('*'), key=lambda p: p.stat().st_ctime, reverse=True)
        if not workspaces:
            raise RuntimeError("qtrader 服务器已启动，但未找到对应的工作区目录。")
        workspace_dir = workspaces[0]

        # 生成run_id
        run_id = f"{strategy_name}_{mode}_{workspace_dir.name}"

        # 记录运行信息
        active_runs[run_id] = {
            'strategy': strategy_name,
            'mode': mode,
            'pid': process.pid,
            'port': port,
            'start_time': time.time(),
            'status': 'running',
            'workspace_dir': str(workspace_dir),
            'temp_config': str(temp_config_path),
            'is_paused': False,
            'last_heartbeat': datetime.now()
        }

        # 创建关联文件，用于在任何情况下都能找到并清理临时配置
        try:
            link_file_path = strategy_dir / f".{run_id}.link"
            with open(link_file_path, 'w', encoding='utf-8') as f:
                f.write(temp_config_path.name)
        except Exception as e:
            print(f"警告: 未能创建临时配置的关联文件: {e}")

        print(f"[{strategy_name}] 回测已启动，监控端口: {port}")

        # 通知前端更新
        socketio.emit('dashboard_update', {'strategy_name': strategy_name})

        return jsonify({
            'success': True,
            'message': f'{mode} 启动成功',
            'run_id': run_id,
            'port': port
        })

    except Exception as e:
        # 确保在启动失败时能终止已创建的子进程
        if process and process.poll() is None:
            try:
                p = psutil.Process(process.pid)
                p.kill()  # 强制终止进程及其所有子进程
            except psutil.NoSuchProcess:
                pass  # 进程可能已经自行退出
        
        release_port(port)
        if temp_config_path.exists():
            temp_config_path.unlink()
        return jsonify({'error': f'启动失败: {str(e)}'}), 500


@runs_bp.route('/runs/<run_id>/status', methods=['GET'])
@login_required
def get_run_status(run_id):
    """获取运行实例的状态"""
    if run_id in active_runs:
        run_info = active_runs[run_id]
        pid = run_info.get('pid')

        if pid and is_process_running(pid):
            return jsonify({
                'status': 'running',
                'port': run_info.get('port'),
                'workspace_dir': run_info.get('workspace_dir')
            })
        else:
            # 进程已停止，从工作区推断状态
            workspace_dir = run_info.get('workspace_dir')
            status = get_run_status_from_workspace(workspace_dir)

            # 清理active_runs
            print(f"[{run_info.get('strategy')}] 回测已结束。")

            socketio.emit('dashboard_update', {'strategy_name': run_info.get('strategy')})
            del active_runs[run_id]
            release_port(run_info.get('port'))

            return jsonify({
                'status': status,
                'workspace_dir': workspace_dir
            })
    else:
        workspace_dir = _get_historical_workspace_dir(run_id)
        if not workspace_dir or not workspace_dir.exists():
            return jsonify({'error': '运行实例不存在'}), 404
        
        status = get_run_status_from_workspace(workspace_dir)
        return jsonify({
            'status': status,
            'workspace_dir': str(workspace_dir)
        })

@runs_bp.route('/runs/<run_id>/control', methods=['POST'])
@login_required
def control_run(run_id):
    """
    控制运行实例
    请求体: {"action": "pause" | "resume" | "stop"}
    """
    data = request.get_json()
    action = data.get('action')

    if run_id not in active_runs:
        return jsonify({'error': '运行实例不在活动列表中'}), 404

    run_info = active_runs[run_id]
    port = run_info.get('port')

    if not port:
        return jsonify({'error': '未找到端口信息'}), 500

    # 向qtrader进程的HTTP API发送控制请求
    try:
        response = requests.post(
            f'http://localhost:{port}/api/control',
            json={'action': action},
            timeout=5
        )
        response.raise_for_status()

        # 更新状态
        if action == 'pause':
            active_runs[run_id]['is_paused'] = True
            socketio.emit('run_status_changed', {
                'run_id': run_id,
                'is_paused': True
            })
        elif action == 'resume':
            active_runs[run_id]['is_paused'] = False
            socketio.emit('run_status_changed', {
                'run_id': run_id,
                'is_paused': False
            })

        # 通知前端更新
        socketio.emit('dashboard_update', {'strategy_name': run_info.get('strategy')})

        return jsonify({
            'success': True,
            'message': f'操作 {action} 执行成功',
            'response': response.json()
        })

    except Exception as e:
        print(f"!!! CONTROL_RUN FAILED for run {run_id} with action {action} !!!")
        print(f"!!! ERROR: {e} !!!")
        return jsonify({
            'error': f'控制操作失败: {str(e)}'
        }), 500

@runs_bp.route('/runs/<run_id>/resume', methods=['POST'])
@login_required
def resume_run(run_id):
    """
    从暂停状态恢复运行（启动新进程）
    用于处理paused状态但进程已终止的情况
    支持start_paused参数以暂停模式启动
    """
    # 获取请求参数
    data = request.get_json() or {}
    start_paused = data.get('start_paused', False)

    # 获取工作区目录
    workspace_dir = _get_historical_workspace_dir(run_id)
    if not workspace_dir or not workspace_dir.exists():
        return jsonify({'error': '无效的run_id或找不到工作区'}), 400

    # 检查是否存在暂停pkl文件
    pause_pkl = list(workspace_dir.glob('*_pause.pkl'))
    if not pause_pkl:
        return jsonify({'error': '未找到暂停状态文件，无法恢复'}), 404

    pause_pkl_path = pause_pkl[0]

    # 解析run_id获取策略信息
    parts = run_id.split('_')
    if len(parts) < 4:
        return jsonify({'error': '无效的run_id格式'}), 400

    mode = parts[-3]
    strategy_name = '_'.join(parts[:-3])
    strategy_dir = STRATEGIES_DIR / strategy_name

    if not strategy_dir.exists():
        return jsonify({'error': f'策略 "{strategy_name}" 不存在'}), 404

    # 从 workspace 的 snapshot 读取配置（而不是策略目录的config.yaml）
    snapshot_config_path = workspace_dir / 'snapshot_config.yaml'
    if not snapshot_config_path.exists():
        return jsonify({'error': '未找到配置快照文件'}), 404

    try:
        with open(snapshot_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        return jsonify({'error': f'配置快照解析失败: {str(e)}'}), 500

    # 分配新端口
    try:
        port = get_available_port()
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500

    # 修改配置
    if 'server' not in config:
        config['server'] = {}
    config['server']['enable'] = True
    config['server']['port'] = port
    config['server']['auto_open_browser'] = False

    if 'engine' not in config:
        config['engine'] = {}
    config['engine']['mode'] = mode

    # 创建临时配置文件
    temp_config_path = strategy_dir / f'_temp_config_resume_{int(time.time())}.yaml'
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)

    # 使用platform_runner.py启动恢复
    runner_script = Path(__file__).parent.parent / 'utils' / 'platform_runner.py'
    data_provider_file = strategy_dir / 'data_provider.py'

    cmd = [
        'python', str(runner_script),
        '--config', str(temp_config_path),
        '--resume-from', str(pause_pkl_path),
        '--data-provider', str(data_provider_file)
    ]

    # 如果指定以暂停模式启动，添加参数
    if start_paused:
        cmd.append('--start-paused')

    process = None
    try:
        # 启动子进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0
        )

        # 等待服务器启动
        wait_time = 20
        end_time = time.time() + wait_time
        server_ready = False

        while time.time() < end_time:
            try:
                response = requests.get(f"http://127.0.0.1:{port}/", timeout=0.5)
                if response.status_code == 200:
                    server_ready = True
                    break
            except (requests.ConnectionError, requests.Timeout):
                time.sleep(0.5)

        if not server_ready:
            process.kill()
            release_port(port)
            if temp_config_path.exists():
                temp_config_path.unlink()
            raise RuntimeError(f"在 {wait_time} 秒内 qtrader 服务器未能启动或响应。")

        # 记录运行信息
        active_runs[run_id] = {
            'strategy': strategy_name,
            'mode': mode,
            'pid': process.pid,
            'port': port,
            'start_time': time.time(),
            'status': 'running',
            'workspace_dir': str(workspace_dir),
            'temp_config': str(temp_config_path),
            'is_paused': start_paused,
            'last_heartbeat': datetime.now()
        }

        # 创建关联文件，用于在任何情况下都能找到并清理临时配置
        try:
            link_file_path = strategy_dir / f".{run_id}.link"
            with open(link_file_path, 'w', encoding='utf-8') as f:
                f.write(temp_config_path.name)
        except Exception as e:
            print(f"警告: 未能创建临时配置的关联文件: {e}")

        print(f"[{strategy_name}] 从暂停状态恢复运行，监控端口: {port}")

        # 通知前端更新
        socketio.emit('dashboard_update', {'strategy_name': strategy_name})

        return jsonify({
            'success': True,
            'message': '从暂停状态恢复成功',
            'run_id': run_id,
            'port': port
        })

    except Exception as e:
        # 确保在恢复失败时能终止已创建的子进程
        if process and process.poll() is None:
            try:
                p = psutil.Process(process.pid)
                p.kill()  # 强制终止进程及其所有子进程
            except psutil.NoSuchProcess:
                pass  # 进程可能已经自行退出

        release_port(port)
        if temp_config_path.exists():
            temp_config_path.unlink()
        return jsonify({'error': f'恢复失败: {str(e)}'}), 500

@runs_bp.route('/runs/<run_id>/report', methods=['GET'])
@login_required
def get_report(run_id):
    """获取回测报告HTML"""
    if run_id in active_runs:
        workspace_dir = Path(active_runs[run_id]['workspace_dir'])
    else:
        workspace_dir = _get_historical_workspace_dir(run_id)
        if not workspace_dir:
            return jsonify({'error': '无效的run_id或找不到工作区'}), 400

    report_path = workspace_dir / 'report.html'

    if not report_path.exists():
        return jsonify({'error': '报告文件不存在'}), 404

    return send_file(report_path, mimetype='text/html')

@runs_bp.route('/runs/<run_id>/files', methods=['GET'])
@login_required
def list_run_files(run_id):
    """列出运行实例的所有文件"""
    if run_id in active_runs:
        workspace_dir = Path(active_runs[run_id]['workspace_dir'])
    else:
        workspace_dir = _get_historical_workspace_dir(run_id)
        if not workspace_dir:
            return jsonify({'error': '无效的run_id或找不到工作区'}), 400

    if not workspace_dir.exists():
        return jsonify({'error': '工作区不存在'}), 404

    files = []
    for file_path in workspace_dir.rglob('*'):
        if file_path.is_file():
            files.append({
                'name': file_path.name,
                'relative_path': str(file_path.relative_to(workspace_dir)),
                'size': file_path.stat().st_size
            })

    return jsonify({'files': files})

@runs_bp.route('/runs/<run_id>/download/<path:filepath>', methods=['GET'])
@login_required
def download_file(run_id, filepath):
    """下载运行实例的文件"""
    if run_id in active_runs:
        workspace_dir = Path(active_runs[run_id]['workspace_dir'])
    else:
        workspace_dir = _get_historical_workspace_dir(run_id)
        if not workspace_dir:
            return jsonify({'error': '无效的run_id或找不到工作区'}), 400

    file_path = workspace_dir / filepath

    if not file_path.exists() or not file_path.is_file():
        return jsonify({'error': '文件不存在'}), 404

    # 安全检查：确保文件在工作区内
    try:
        file_path.relative_to(workspace_dir)
    except ValueError:
        return jsonify({'error': '非法文件路径'}), 403

    return send_file(file_path, as_attachment=True)

@runs_bp.route('/runs/<run_id>/final_status', methods=['GET'])
@login_required
def get_final_status(run_id):
    """
    获取运行结束后的最终状态，会等待报告生成。
    """
    if run_id in active_runs:
        # 如果仍在 active_runs 中，说明是刚刚结束，信息是准确的
        workspace_dir = Path(active_runs[run_id]['workspace_dir'])
    else:
        # 如果已不在 active_runs 中，说明是历史运行
        workspace_dir = _get_historical_workspace_dir(run_id)

    if not workspace_dir or not workspace_dir.exists():
        return jsonify({'error': '找不到运行工作区'}), 404

    report_path = workspace_dir / 'report.html'

    # 等待最多5秒，让qtrader有时间生成报告
    wait_time = 5
    for _ in range(wait_time):
        if report_path.exists():
            return jsonify({'status': 'finished', 'report_ready': True})
        time.sleep(1)

    # 如果5秒后报告仍不存在
    # 检查是否存在中断文件，以提供更准确的状态
    interrupt_pkl = list(workspace_dir.glob('*_interrupt.pkl'))
    if interrupt_pkl:
        return jsonify({'status': 'interrupted', 'report_ready': False})

    return jsonify({'status': 'unknown_error', 'report_ready': False})

@runs_bp.route('/runs/<run_id>/download-workspace', methods=['GET'])
@login_required
def download_workspace(run_id):
    """
    打包并下载整个workspace目录
    """
    if run_id in active_runs:
        workspace_dir = Path(active_runs[run_id]['workspace_dir'])
    else:
        workspace_dir = _get_historical_workspace_dir(run_id)
        if not workspace_dir:
            return jsonify({'error': '无效的run_id或找不到工作区'}), 400

    if not workspace_dir.exists():
        return jsonify({'error': '工作区不存在'}), 404

    try:
        # 创建临时目录用于存放zip文件
        temp_dir = tempfile.mkdtemp()
        zip_path = Path(temp_dir) / f'{run_id}_workspace'

        # 打包整个workspace目录
        archive_path = shutil.make_archive(
            str(zip_path),
            'zip',
            workspace_dir.parent,
            workspace_dir.name
        )

        # 发送文件后自动清理临时文件
        return send_file(
            archive_path,
            as_attachment=True,
            download_name=f'{run_id}_workspace.zip',
            mimetype='application/zip'
        )
    except Exception as e:
        return jsonify({'error': f'打包失败: {str(e)}'}), 500

@runs_bp.route('/runs/<run_id>/delete', methods=['DELETE'])
@login_required
def delete_workspace(run_id):
    """
    删除整个workspace目录，并清理关联的临时配置文件
    """
    # 检查是否在运行中
    if run_id in active_runs:
        return jsonify({'error': '无法删除运行中的实例，请先停止'}), 400

    workspace_dir = _get_historical_workspace_dir(run_id)
    if not workspace_dir:
        # 即使工作区不存在，也应该尝试清理关联文件
        print(f"警告: 找不到工作区，但仍将尝试清理关联文件。")

    try:
        # 清理关联的临时配置文件
        try:
            strategy_name = '_'.join(run_id.split('_')[:-3])
            strategy_dir = STRATEGIES_DIR / strategy_name
            link_file_path = strategy_dir / f".{run_id}.link"

            if link_file_path.exists():
                with open(link_file_path, 'r', encoding='utf-8') as f:
                    temp_config_filename = f.read().strip()
                
                if temp_config_filename:
                    temp_config_path = strategy_dir / temp_config_filename
                    if temp_config_path.exists():
                        temp_config_path.unlink()
                        print(f"关联的临时配置文件已删除: {temp_config_path}")
                
                link_file_path.unlink()
        except Exception as e:
            print(f"清理关联的临时配置文件失败: {e}")

        # 删除整个workspace目录
        if workspace_dir and workspace_dir.exists():
            shutil.rmtree(workspace_dir)

        # 删除对应的备注
        delete_note(run_id)

        return jsonify({
            'success': True,
            'message': '工作区及关联文件已删除'
        })
    except Exception as e:
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

@runs_bp.route('/runs/<run_id>/note', methods=['PUT'])
@login_required
def update_note(run_id):
    """
    更新运行实例的备注
    请求体: {"note": "备注内容"}
    """
    data = request.get_json()
    note = data.get('note', '')

    # 验证run_id是否存在（可以是活动的或历史的）
    if run_id not in active_runs:
        workspace_dir = _get_historical_workspace_dir(run_id)
        if not workspace_dir:
            return jsonify({'error': '运行实例不存在'}), 404

    # 保存备注
    if set_note(run_id, note):
        return jsonify({
            'success': True,
            'message': '备注更新成功',
            'note': note
        })
    else:
        return jsonify({'error': '备注保存失败'}), 500


# Socket.IO 事件处理器
@socketio.on('run_heartbeat')
def handle_run_heartbeat(data):
    """接收前端发送的心跳，更新最后活跃时间"""
    run_id = data.get('run_id')
    if run_id and run_id in active_runs:
        active_runs[run_id]['last_heartbeat'] = datetime.now()
