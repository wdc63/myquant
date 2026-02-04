# myquant/backend/extensions.py
"""
用于实例化扩展，解决循环导入问题。
"""

from flask_socketio import SocketIO

# 创建一个全局的、未初始化的socketio实例
socketio = SocketIO()
