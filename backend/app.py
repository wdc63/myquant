# myquant/backend/app.py
"""
MyQuant Platform - 主应用入口
单用户量化策略回测和模拟交易平台
"""

import sys
import os
from pathlib import Path

# 添加 myquant 目录到Python路径，以便使用相对于myquant的绝对导入
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, session
from flask_cors import CORS
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'myquant-secret-key-change-in-production'
app.config['JSON_AS_ASCII'] = False  # 支持中文JSON

# 加载全局配置
config_path = Path(__file__).parent.parent / 'myquant_config.json'
with open(config_path, 'r', encoding='utf-8') as f:
    global_config = json.load(f)

# 启用CORS
# 动态从全局配置读取Vite端口，以设置CORS策略
vite_port = global_config.get('frontend_dev', {}).get('vite_port', 5173)
frontend_origin = f"http://localhost:{vite_port}"
CORS(app, origins=[frontend_origin], supports_credentials=True)

# 创建SocketIO实例
from backend.extensions import socketio
socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

logger.info("SDK客户端初始化成功")

# 注册蓝图
from backend.api.auth import auth_bp
from backend.api.strategies import strategies_bp
from backend.api.runs import runs_bp
from backend.api.docs import docs_bp
from backend.api.libraries import libraries_bp

app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(strategies_bp, url_prefix='/api')
app.register_blueprint(runs_bp, url_prefix='/api')
app.register_blueprint(docs_bp, url_prefix='/api')
app.register_blueprint(libraries_bp, url_prefix='/api')

# 导入Socket.IO事件处理器
from backend.api.monitoring import register_socketio_events
register_socketio_events(socketio)

# 启动后台清理线程
import threading
import time
from datetime import datetime
import psutil

def cleanup_idle_paused_runs():
    """后台线程：定期检查并清理空闲的暂停实例"""
    from backend.api.runs import active_runs, release_port

    while True:
        time.sleep(60)  # 每分钟检查一次

        try:
            now = datetime.now()
            timeout_seconds = 600  # 10分钟

            for run_id, info in list(active_runs.items()):
                # 检查条件：暂停 + 超时
                if info.get('is_paused') and \
                   (now - info.get('last_heartbeat', now)).total_seconds() > timeout_seconds:

                    logger.info(f"清理空闲的暂停实例: {run_id}")

                    # 终止进程
                    pid = info.get('pid')
                    if pid:
                        try:
                            process = psutil.Process(pid)
                            process.terminate()
                            process.wait(timeout=5)
                        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                            try:
                                process.kill()
                            except:
                                pass
                        except Exception as e:
                            logger.warning(f"终止进程 {pid} 失败: {e}")

                    # 释放端口
                    port = info.get('port')
                    if port:
                        release_port(port)

                    # 从 active_runs 移除
                    del active_runs[run_id]

                    # 通知前端：仍然是暂停状态（进程终止但 pause.pkl 还在）
                    socketio.emit('run_status_changed', {
                        'run_id': run_id,
                        'status': 'paused',
                        'is_paused': True
                    })

                    logger.info(f"已清理: {run_id}")

        except Exception as e:
            logger.error(f"清理线程发生错误: {e}")

# 健康检查端点
@app.route('/api/health')
def health():
    return {'status': 'ok', 'message': 'MyQuant Platform is running'}

if __name__ == '__main__':
    host = global_config['server']['host']
    port = global_config['server']['port']

    # 启动清理线程
    cleanup_thread = threading.Thread(target=cleanup_idle_paused_runs, daemon=True)
    cleanup_thread.start()
    logger.info("后台清理线程已启动")

    logger.info(f"启动 MyQuant Platform 服务器: http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
