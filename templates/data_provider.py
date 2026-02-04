"""示例 DataProvider（开源版）。

MyQuant 开源版不再内置/强绑定私有数据 SDK。
你可以用这个模板快速实现 QTrader 的数据合约：
- 交易日历
- 某时刻价格快照
- 标的静态信息

把它复制到你的策略目录下，并在 `config.yaml` + 平台运行器中指向它即可。
"""

from __future__ import annotations

import datetime
import random
from typing import Dict, List, Optional

from qtrader.data.interface import AbstractDataProvider


class MockDataProvider(AbstractDataProvider):
    def __init__(self):
        self._cache: Dict[tuple[str, str], float] = {}

    def get_trading_calendar(self, start: str, end: str) -> List[str]:
        start_date = datetime.datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end, "%Y-%m-%d")
        days: List[str] = []
        cur = start_date
        while cur <= end_date:
            if cur.weekday() < 5:
                days.append(cur.strftime("%Y-%m-%d"))
            cur += datetime.timedelta(days=1)
        return days

    def get_current_price(self, symbol: str, dt: datetime.datetime) -> Optional[Dict]:
        key = (symbol, dt.strftime("%Y-%m-%d"))
        base = self._cache.get(key)
        if base is None:
            base = 10 + random.random() * 5
            self._cache[key] = base
        price = base + (dt.hour - 9) * 0.1 + (dt.minute / 60) * 0.1 + random.uniform(-0.05, 0.05)
        price = round(price, 2)
        return {
            "current_price": price,
            "ask1": round(price * 1.001, 2),
            "bid1": round(price * 0.999, 2),
            "high_limit": round(base * 1.1, 2),
            "low_limit": round(base * 0.9, 2),
        }

    def get_symbol_info(self, symbol: str, date: str) -> Optional[Dict]:
        return {"symbol_name": symbol, "is_suspended": False}
