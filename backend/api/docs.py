# myquant/backend/api/docs.py
"""API 文档端点。

开源版只提供 MyQuant + QTrader 的文档：
- MyQuant：平台使用说明
- QTrader：框架用户文档（从 GitHub 仓库读取）

私有的 `stock_api_sdk` / `tdx_api_sdk` 已剥离，不再在此处暴露。
"""

from flask import Blueprint, jsonify
from backend.api.auth import login_required
import requests


docs_bp = Blueprint('docs', __name__)


def _fetch_text(url: str) -> str:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.text


@docs_bp.route('/docs/<project_name>', methods=['GET'])
@login_required
def get_documentation(project_name: str):
    if project_name == 'myquant':
        # 前端已有静态文档；这里保留 API 端点以兼容旧 UI
        # 直接提示用户查看仓库 docs/ 或前端 docs 页面。
        return jsonify({
            'project': 'myquant',
            'content': '开源版 MyQuant 文档请查看仓库 docs/ 目录，或前端 Docs 页面。'
        })

    if project_name == 'qtrader':
        # 从 GitHub 读取最新 QTrader 用户文档
        url = 'https://raw.githubusercontent.com/wdc63/pqtrader/main/USER_GUIDE.md'
        try:
            content = _fetch_text(url)
        except Exception as e:
            return jsonify({'error': f'拉取 QTrader 文档失败: {str(e)}'}), 502
        return jsonify({'project': 'qtrader', 'content': content})

    return jsonify({'error': f'无效的项目名称: {project_name}'}), 404
