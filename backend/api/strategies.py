# myquant/backend/api/strategies.py
"""
策略管理API - 处理策略的创建、读取、更新、删除
"""

from flask import Blueprint, request, jsonify
from pathlib import Path
import shutil
import re
from .auth import login_required

strategies_bp = Blueprint('strategies', __name__)

# 策略根目录
STRATEGIES_DIR = Path(__file__).parent.parent.parent / 'strategies'
TEMPLATES_DIR = Path(__file__).parent.parent.parent / 'templates'

# 确保目录存在
STRATEGIES_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

def is_valid_strategy_name(name):
    """验证策略名称是否合法"""
    # 只允许字母、数字、下划线、中文
    pattern = re.compile(r'^[\w\u4e00-\u9fa5]+$')
    return pattern.match(name) is not None and len(name) > 0 and len(name) <= 50

@strategies_bp.route('/strategies', methods=['GET'])
@login_required
def list_strategies():
    """
    列出所有策略
    返回: [{"name": "...", "created_at": "...", "path": "..."}]
    """
    strategies = []
    for strategy_dir in STRATEGIES_DIR.iterdir():
        if strategy_dir.is_dir() and not strategy_dir.name.startswith('.'):
            # 获取创建时间
            stat = strategy_dir.stat()
            strategies.append({
                'name': strategy_dir.name,
                'created_at': stat.st_ctime,
                'path': str(strategy_dir)
            })

    # 按创建时间倒序排列
    strategies.sort(key=lambda x: x['created_at'], reverse=True)

    return jsonify({'strategies': strategies})

@strategies_bp.route('/strategies', methods=['POST'])
@login_required
def create_strategy():
    """
    创建新策略
    请求体: {"name": "策略名称"}
    """
    data = request.get_json()
    strategy_name = data.get('name', '').strip()

    # 验证策略名称
    if not is_valid_strategy_name(strategy_name):
        return jsonify({
            'success': False,
            'message': '策略名称不合法，只允许字母、数字、下划线和中文，长度1-50个字符'
        }), 400

    strategy_dir = STRATEGIES_DIR / strategy_name

    # 检查是否已存在
    if strategy_dir.exists():
        return jsonify({
            'success': False,
            'message': f'策略 "{strategy_name}" 已存在'
        }), 400

    try:
        # 创建策略目录
        strategy_dir.mkdir(parents=True)

        # 复制模板文件
        template_files = ['strategy.py', 'config.yaml', 'data_provider.py']
        for template_file in template_files:
            src = TEMPLATES_DIR / template_file
            dst = strategy_dir / template_file
            if src.exists():
                shutil.copy2(src, dst)
            else:
                return jsonify({
                    'success': False,
                    'message': f'模板文件 {template_file} 不存在'
                }), 500

        return jsonify({
            'success': True,
            'message': f'策略 "{strategy_name}" 创建成功',
            'strategy': {'name': strategy_name}
        })

    except Exception as e:
        # 如果创建失败，清理已创建的目录
        if strategy_dir.exists():
            shutil.rmtree(strategy_dir)
        return jsonify({
            'success': False,
            'message': f'创建策略失败: {str(e)}'
        }), 500

@strategies_bp.route('/strategies/<strategy_name>', methods=['DELETE'])
@login_required
def delete_strategy(strategy_name):
    """删除策略"""
    strategy_dir = STRATEGIES_DIR / strategy_name

    if not strategy_dir.exists():
        return jsonify({
            'success': False,
            'message': f'策略 "{strategy_name}" 不存在'
        }), 404

    # 安全检查：删除前确认没有正在运行的实例
    from backend.api.runs import active_runs, delete_notes_by_strategy  # 使用局部导入，避免循环依赖和启动问题
    for run_id, run_info in list(active_runs.items()):
        if run_info.get('strategy') == strategy_name:
            return jsonify({
                'success': False,
                'message': f'无法删除，策略 "{strategy_name}" 有正在运行或暂停的实例。请先停止所有相关运行。'
            }), 400

    try:
        # 删除策略目录
        shutil.rmtree(strategy_dir)

        # 删除该策略的所有备注
        delete_notes_by_strategy(strategy_name)

        return jsonify({
            'success': True,
            'message': f'策略 "{strategy_name}" 已删除'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除策略失败: {str(e)}'
        }), 500

@strategies_bp.route('/strategies/<strategy_name>/files', methods=['GET'])
@login_required
def get_strategy_files(strategy_name):
    """
    获取策略的三个核心文件内容
    返回: {"strategy": "...", "config": "...", "data_provider": "..."}
    """
    strategy_dir = STRATEGIES_DIR / strategy_name

    if not strategy_dir.exists():
        return jsonify({'error': f'策略 "{strategy_name}" 不存在'}), 404

    files = {
        'strategy.py': '',
        'config.yaml': '',
        'data_provider.py': ''
    }

    for filename in files.keys():
        file_path = strategy_dir / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    files[filename] = f.read()
            except Exception as e:
                files[filename] = f'# 读取文件失败: {str(e)}'

    return jsonify({'files': files})

@strategies_bp.route('/strategies/<strategy_name>/files/<filename>', methods=['PUT'])
@login_required
def update_strategy_file(strategy_name, filename):
    """
    更新策略文件内容
    请求体: {"content": "文件内容"}
    """
    # 只允许更新三个核心文件
    allowed_files = ['strategy.py', 'config.yaml', 'data_provider.py']
    if filename not in allowed_files:
        return jsonify({
            'success': False,
            'message': f'不允许更新文件 "{filename}"'
        }), 400

    strategy_dir = STRATEGIES_DIR / strategy_name
    if not strategy_dir.exists():
        return jsonify({
            'success': False,
            'message': f'策略 "{strategy_name}" 不存在'
        }), 404

    data = request.get_json()
    content = data.get('content', '')

    file_path = strategy_dir / filename

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({
            'success': True,
            'message': f'文件 "{filename}" 已保存'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'保存文件失败: {str(e)}'
        }), 500
