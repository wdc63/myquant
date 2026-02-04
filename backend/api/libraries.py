# myquant/backend/api/libraries.py
"""
库管理 API
提供内置库信息查询、自定义库安装/卸载功能
"""

from flask import Blueprint, request, jsonify, session
import json
import subprocess
import sys
from pathlib import Path
import logging
import uuid
from backend.extensions import socketio

logger = logging.getLogger(__name__)

libraries_bp = Blueprint('libraries', __name__)

# 配置文件路径
CONFIG_PATH = Path(__file__).parent.parent.parent / 'myquant_config.json'

# 内置库定义（平台提供的回测和金融计算相关库）
BUILTIN_LIBRARIES = {
    # === 核心框架 ===
    'qtrader': {
        'name': 'QTrader 量化回测框架',
        'category': '核心框架',
        'description': '事件驱动的量化回测框架，提供完整的策略开发、回测执行、性能分析和可视化功能',
        'version': '1.0.0',
        # 开源版 MyQuant 只依赖 QTrader（通过 pip 安装），不再从父目录读取私有仓库。
        'requirements_path': None
    },

    # === 数据处理与分析 ===
    'pandas': {
        'name': 'pandas',
        'category': '数据处理',
        'description': '强大的数据结构和数据分析工具，量化回测的基础库，用于处理时间序列数据、计算技术指标',
        'version': '>=2.0.0',
        'requirements_path': None
    },
    'numpy': {
        'name': 'NumPy',
        'category': '数据处理',
        'description': '科学计算基础库，提供高效的多维数组操作和数学函数，用于金融指标计算和矩阵运算',
        'version': '>=1.24.0',
        'requirements_path': None
    },

    # === 金融性能分析 ===
    'empyrical': {
        'name': 'empyrical-reloaded',
        'category': '金融分析',
        'description': '专业的金融性能指标计算库，提供年化收益、夏普率、最大回撤、索提诺比率等风险指标',
        'version': '>=0.5.8',
        'requirements_path': None
    },

    # === 技术指标计算 ===
    'ta': {
        'name': 'ta (Technical Analysis Library)',
        'category': '技术分析',
        'description': '基于pandas的技术分析指标库，提供趋势、动量、波动率、成交量等40+常用技术指标（MA、RSI、MACD、布林带等）',
        'version': '>=0.11.0',
        'requirements_path': None
    },
    'talib': {
        'name': 'TA-Lib',
        'category': '技术分析',
        'description': '金融市场技术分析的权威库，提供150+技术指标函数（需预先安装C/C++底层库），性能优异，广泛应用于专业量化交易',
        'version': '>=0.4.0',
        'requirements_path': None
    },

    # === 统计分析 ===
    'scipy': {
        'name': 'SciPy',
        'category': '科学计算',
        'description': '科学计算库，提供优化算法、统计分布、线性代数、信号处理等功能，用于量化模型构建和统计检验',
        'version': '>=1.10.0',
        'requirements_path': None
    },
    'statsmodels': {
        'name': 'statsmodels',
        'category': '统计分析',
        'description': '统计建模库，提供时间序列分析（ARIMA、GARCH）、回归分析、协整检验等统计模型',
        'version': '>=0.14.0',
        'requirements_path': None
    },

    # === 机器学习基础 ===
    'scikit-learn': {
        'name': 'scikit-learn',
        'category': '机器学习',
        'description': '经典机器学习库，提供分类、回归、聚类算法，用于构建量价预测、因子选股等策略',
        'version': '>=1.3.0',
        'requirements_path': None
    },

    # === 数据可视化 ===
    'matplotlib': {
        'name': 'Matplotlib',
        'category': '可视化',
        'description': 'Python绘图库，用于绘制K线图、指标图、收益曲线等，支持自定义图表样式',
        'version': '>=3.7.0',
        'requirements_path': None
    },

    # === 日期时间处理 ===
    'python-dateutil': {
        'name': 'python-dateutil',
        'category': '工具库',
        'description': '日期时间处理扩展库，提供灵活的日期解析、时区转换、交易日计算等功能',
        'version': '>=2.8.0',
        'requirements_path': None
    }
}


def load_config():
    """加载配置文件"""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config):
    """保存配置文件"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def read_requirements(requirements_path):
    """读取requirements.txt文件"""
    if not requirements_path.exists():
        return []

    with open(requirements_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    dependencies = []
    for line in lines:
        line = line.strip()
        # 跳过注释和空行
        if line and not line.startswith('#'):
            dependencies.append(line)

    return dependencies


@libraries_bp.route('/libraries', methods=['GET'])
def get_libraries():
    """获取所有库信息（内置 + 自定义）"""
    try:
        # 读取内置库的依赖
        builtin_libs = []
        for lib_id, lib_info in BUILTIN_LIBRARIES.items():
            # 如果有 requirements_path，读取依赖；否则该库本身就是依赖
            if lib_info['requirements_path']:
                dependencies = read_requirements(lib_info['requirements_path'])
            else:
                dependencies = []

            builtin_libs.append({
                'id': lib_id,
                'name': lib_info['name'],
                'category': lib_info['category'],
                'description': lib_info['description'],
                'version': lib_info['version'],
                'type': 'builtin',
                'dependencies': dependencies
            })

        # 读取自定义库
        config = load_config()
        custom_libs = config.get('custom_libraries', [])

        return jsonify({
            'success': True,
            'builtin': builtin_libs,
            'custom': custom_libs
        })

    except Exception as e:
        logger.error(f"获取库列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@libraries_bp.route('/libraries/python_version', methods=['GET'])
def get_python_version():
    """获取当前后端运行的Python版本"""
    try:
        # sys.version 提供了详细的版本信息，包括编译器等
        python_version = sys.version
        return jsonify({'success': True, 'python_version': python_version})
    except Exception as e:
        logger.error(f"获取Python版本失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@libraries_bp.route('/libraries/install', methods=['POST'])
def install_library():
    """安装自定义库"""
    try:
        data = request.json
        password = data.get('password')
        library_name = data.get('library_name', '').strip()
        description = data.get('description', '').strip()  # 用户提供的描述
        task_id = data.get('task_id')  # 前端传来的任务ID，用于SocketIO推送

        # 验证密码
        config = load_config()
        if password != config['auth']['password']:
            return jsonify({'success': False, 'message': '密码错误'}), 401

        if not library_name:
            return jsonify({'success': False, 'message': '库名不能为空'}), 400

        # 检查是否为内置库（不区分大小写，防止通过大小写绕过）
        library_name_lower = library_name.lower()

        # 内置库名称映射（包括常见的变体）
        builtin_lib_names = {
            # 核心框架
            'qtrader': '核心框架',


            # 数据处理
            'pandas': '数据处理',
            'numpy': '数据处理',

            # 金融分析
            'empyrical': '金融分析',
            'empyrical-reloaded': '金融分析',

            # 技术分析
            'ta': '技术分析',
            'talib': '技术分析',
            'ta-lib': '技术分析',

            # 统计分析
            'scipy': '统计分析',
            'statsmodels': '统计分析',

            # 机器学习
            'scikit-learn': '机器学习',
            'sklearn': '机器学习',

            # 可视化
            'matplotlib': '可视化',

            # 工具库
            'python-dateutil': '工具库',
            'dateutil': '工具库'
        }

        # 检查是否与内置库冲突
        if library_name_lower in builtin_lib_names:
            category = builtin_lib_names[library_name_lower]
            return jsonify({
                'success': False,
                'message': f'{library_name} 是平台内置库（{category}），无需额外安装。请在内置库列表中查看。'
            }), 400

        # 检查是否已在自定义库列表中
        custom_libs = config.get('custom_libraries', [])
        if any(lib['name'].lower() == library_name_lower for lib in custom_libs):
            return jsonify({'success': False, 'message': f'{library_name} 已在自定义库列表中'}), 400

        # 使用pip安装（使用 Popen 实时捕获输出并通过SocketIO推送）
        logger.info(f"正在安装库: {library_name}")

        # 使用 Popen 实时读取输出
        process = subprocess.Popen(
            [sys.executable, '-m', 'pip', 'install', '--verbose', library_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 将stderr合并到stdout
            text=True,
            bufsize=1,  # 行缓冲
            universal_newlines=True
        )

        # 实时读取输出并通过SocketIO推送
        pip_output_lines = []
        for line in process.stdout:
            pip_output_lines.append(line)
            # 实时推送到前端
            if task_id:
                socketio.emit('pip_output', {
                    'task_id': task_id,
                    'line': line
                })

        # 等待进程结束
        return_code = process.wait(timeout=300)
        pip_output = ''.join(pip_output_lines)

        # 如果输出为空，添加默认信息
        if not pip_output.strip():
            pip_output = f"pip install {library_name} 执行完成（无详细输出）"

        if return_code != 0:
            logger.error(f"安装失败，返回码: {return_code}")
            return jsonify({
                'success': False,
                'message': '安装失败，请查看详细输出',
                'pip_output': pip_output,
                'error': f'进程返回码: {return_code}'
            }), 500

        # 获取安装后的版本信息
        version_result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', library_name],
            capture_output=True,
            text=True
        )

        version = 'unknown'
        if version_result.returncode == 0:
            for line in version_result.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':', 1)[1].strip()
                    break

        # 添加到配置
        new_lib = {
            'name': library_name,
            'version': version,
            'description': description if description else f'自定义安装的 {library_name} 库',
            'installed_at': None  # 可以添加时间戳
        }
        custom_libs.append(new_lib)
        config['custom_libraries'] = custom_libs
        save_config(config)

        logger.info(f"库安装成功: {library_name} ({version})")
        return jsonify({
            'success': True,
            'message': f'{library_name} ({version}) 安装成功',
            'library': new_lib,
            'pip_output': pip_output
        })

    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': '安装超时（5分钟），请稍后重试'}), 500
    except Exception as e:
        logger.error(f"安装库失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@libraries_bp.route('/libraries/uninstall', methods=['POST'])
def uninstall_library():
    """卸载自定义库"""
    try:
        data = request.json
        password = data.get('password')
        library_name = data.get('library_name', '').strip()
        task_id = data.get('task_id')  # 前端传来的任务ID，用于SocketIO推送

        # 验证密码
        config = load_config()
        if password != config['auth']['password']:
            return jsonify({'success': False, 'message': '密码错误'}), 401

        if not library_name:
            return jsonify({'success': False, 'message': '库名不能为空'}), 400

        # 检查是否在自定义库列表中
        custom_libs = config.get('custom_libraries', [])
        lib_to_remove = None
        for lib in custom_libs:
            if lib['name'] == library_name:
                lib_to_remove = lib
                break

        if not lib_to_remove:
            return jsonify({'success': False, 'message': f'{library_name} 不在自定义库列表中'}), 400

        # 使用pip卸载（使用 Popen 实时捕获输出并通过SocketIO推送）
        logger.info(f"正在卸载库: {library_name}")

        # 使用 Popen 实时读取输出
        process = subprocess.Popen(
            [sys.executable, '-m', 'pip', 'uninstall', '-y', '--verbose', library_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 将stderr合并到stdout
            text=True,
            bufsize=1,  # 行缓冲
            universal_newlines=True
        )

        # 实时读取输出并通过SocketIO推送
        pip_output_lines = []
        for line in process.stdout:
            pip_output_lines.append(line)
            # 实时推送到前端
            if task_id:
                socketio.emit('pip_output', {
                    'task_id': task_id,
                    'line': line
                })

        # 等待进程结束
        return_code = process.wait(timeout=60)
        pip_output = ''.join(pip_output_lines)

        # 如果输出为空，添加默认信息
        if not pip_output.strip():
            pip_output = f"pip uninstall {library_name} 执行完成（无详细输出）"

        # 从配置中移除（即使pip卸载失败也继续）
        custom_libs.remove(lib_to_remove)
        config['custom_libraries'] = custom_libs
        save_config(config)

        if return_code != 0:
            logger.warning(f"pip卸载返回非零状态码: {return_code}，但已从配置移除")
            return jsonify({
                'success': True,
                'message': f'{library_name} 已从配置移除（pip卸载可能有警告）',
                'pip_output': pip_output,
                'warning': 'pip卸载返回非零状态码，但库已从平台配置中移除'
            })

        logger.info(f"库卸载成功: {library_name}")
        return jsonify({
            'success': True,
            'message': f'{library_name} 卸载成功',
            'pip_output': pip_output
        })

    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': '卸载超时，请稍后重试'}), 500
    except Exception as e:
        logger.error(f"卸载库失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
