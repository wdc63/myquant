# myquant/backend/clients.py
"""平台可选的外部客户端（已开源版剥离私有 SDK）。

历史上 MyQuant 会暴露：
- `stock_api_client`（来自 `stock_api_sdk`）
- `tdx_api_client` / `create_tdx_api_client`（来自 `tdx_api_sdk`）

但这两套 SDK 属于私有数据/实盘依赖，不适合开源仓库强绑定。

开源版策略应当只依赖 QTrader：
- 回测/模拟所需的数据通过 `DataProvider`（数据合约）提供
- 若你需要接入私有数据/实盘，可在你的私有仓库实现并注入

为保持向后兼容：
- 这里仍然导出同名符号，但默认值为 `None`，并在访问时给出明确提示。
"""

from __future__ import annotations

from typing import Optional, Any


class _RemovedDependencyProxy:
    def __init__(self, name: str, hint: str):
        self._name = name
        self._hint = hint

    def __getattr__(self, item: str) -> Any:
        raise RuntimeError(f"{self._name} 在开源版已移除：{self._hint}")

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(f"{self._name} 在开源版已移除：{self._hint}")


stock_api_client: Optional[Any] = None
"""开源版不再提供 stock_api_client（私有 stock_api_sdk 依赖已移除）。"""

tdx_api_client: Optional[Any] = None
"""开源版不再提供 tdx_api_client（私有 tdx_api_sdk 依赖已移除）。"""


def create_tdx_api_client(*, base_url: str, api_key: str) -> Any:  # noqa: ARG001
    """保留函数名用于兼容旧策略，但开源版默认不可用。"""
    proxy = _RemovedDependencyProxy(
        name="create_tdx_api_client",
        hint="请在私有环境提供 tdx_api_sdk，或改为使用 QTrader 的 DataProvider/模拟撮合。",
    )
    return proxy(base_url=base_url, api_key=api_key)
