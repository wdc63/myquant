# myquant/backend/api/auth.py
"""
认证API - 处理用户登录和会话管理
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
import json
from pathlib import Path

auth_bp = Blueprint('auth', __name__)

# 加载全局配置
config_path = Path(__file__).parent.parent.parent / 'myquant_config.json'
with open(config_path, 'r', encoding='utf-8') as f:
    global_config = json.load(f)

def login_required(f):
    """装饰器：要求用户已登录"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': '未登录，请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    请求体: {"password": "..."}
    """
    data = request.get_json()
    password = data.get('password', '')

    correct_password = global_config['auth']['password']

    if password == correct_password:
        session['logged_in'] = True
        session.permanent = True
        return jsonify({'success': True, 'message': '登录成功'})
    else:
        return jsonify({'success': False, 'message': '密码错误'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用户登出"""
    session.clear()
    return jsonify({'success': True, 'message': '已登出'})

@auth_bp.route('/check-auth', methods=['GET'])
def check_auth():
    """检查当前登录状态"""
    if session.get('logged_in'):
        return jsonify({'logged_in': True})
    else:
        return jsonify({'logged_in': False})
