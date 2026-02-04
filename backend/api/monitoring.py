# myquant/backend/api/monitoring.py
"""
实时监控WebSocket事件处理
"""

import socketio
import threading
import time
import requests
from flask import request
from flask_socketio import emit, disconnect

# 从新的 extensions 模块安全地导入 socketio 实例
from backend.extensions import socketio as main_socketio

# 订阅管理：{sid: {run_id, port, thread}}
subscriptions = {}

def fetch_and_emit(sid, port, run_id):
    """
    后台线程：定期从qtrader的Socket.IO获取数据并转发给前端
    """
    # 创建Socket.IO客户端连接到qtrader
    sio_client = socketio.Client()

    @sio_client.on('update')
    def on_update(data):
        # 收到qtrader的更新，转发给前端
        main_socketio.emit('monitoring_update', data, room=sid)

    try:
        # 尝试连接，设置10秒超时
        sio_client.connect(f'http://localhost:{port}', wait_timeout=100)
        
        # 保持连接，直到取消订阅或连接断开
        while sid in subscriptions and subscriptions[sid]['run_id'] == run_id:
            if not sio_client.connected:
                main_socketio.emit('error', {'message': f'与 {run_id} 的监控连接已断开'}, room=sid)
                break
            time.sleep(1)
        
    except Exception as e:
        # 打印详细的错误日志
        print(f"监控连接错误 (run_id: {run_id}, port: {port}): {e}")
        # 向前端发送明确的错误通知
        main_socketio.emit('error', {'message': f'无法连接到运行实例 {run_id} 的监控服务。该实例可能已崩溃或启动失败。'}, room=sid)
        
    finally:
        # 确保断开连接并清理订阅信息
        if sio_client.connected:
            sio_client.disconnect()
        if sid in subscriptions:
            del subscriptions[sid]

def register_socketio_events(socketio_server):
    """注册Socket.IO事件"""

    @socketio_server.on('subscribe')
    def handle_subscribe(data):
        """订阅某个运行实例的实时数据"""
        run_id = data.get('run_id')
        sid = request.sid  # Socket session ID

        if not run_id:
            emit('error', {'message': '缺少run_id'})
            return

        # 动态导入以避免循环依赖
        from backend.api.runs import active_runs
        if run_id not in active_runs:
            emit('error', {'message': f'运行实例 {run_id} 不存在或未运行'})
            return

        port = active_runs[run_id].get('port')
        if not port:
            emit('error', {'message': '未找到端口信息'})
            return

        # 取消之前的订阅（如果有）
        if sid in subscriptions:
            old_sub = subscriptions[sid]
            del subscriptions[sid]

        # 创建新的监控线程
        thread = threading.Thread(
            target=fetch_and_emit,
            args=(sid, port, run_id),
            daemon=True
        )
        thread.start()

        subscriptions[sid] = {
            'run_id': run_id,
            'port': port,
            'thread': thread
        }

        emit('subscribed', {'run_id': run_id})

    @socketio_server.on('unsubscribe')
    def handle_unsubscribe():
        """取消订阅"""
        sid = request.sid
        if sid in subscriptions:
            del subscriptions[sid]
            emit('unsubscribed', {})

    @socketio_server.on('disconnect')
    def handle_disconnect():
        """客户端断开连接"""
        sid = request.sid
        if sid in subscriptions:
            del subscriptions[sid]
