---

<h1 id="data-provider">二、数据提供者（Data Provider）</h1>

MyQuant 开源版不内置任何私有数据 SDK。

平台只依赖 QTrader，并通过 **DataProvider（数据合约）** 获取回测/模拟所需的最小数据集。

---

<h2 id="data-contract">2.1 数据合约（必须实现的 3 个方法）</h2>

你需要实现 `qtrader.data.interface.AbstractDataProvider`：

- `get_trading_calendar(start, end)`：返回交易日列表
- `get_current_price(symbol, dt)`：返回某时刻价格快照（至少包含 `current_price`）
- `get_symbol_info(symbol, date)`：返回标的静态信息（名称、是否停牌）

返回结构参考：

```python
{
  "current_price": 10.0,
  "ask1": 10.01,
  "bid1": 9.99,
  "high_limit": 11.0,
  "low_limit": 9.0
}
```

---

<h2 id="template">2.2 模板</h2>

仓库提供 Mock 模板：

- `templates/data_provider.py`

新策略创建时会复制为：

- `<策略目录>/data_provider.py`

你可以直接把 Mock 改成：CSV / SQLite / 你自己的 API 服务。

---

<h2 id="wire">2.3 MyQuant 如何使用 DataProvider</h2>

平台运行回测/模拟时，会把以下文件路径传给 QTrader：

- `--strategy <策略目录>/strategy.py`
- `--config <策略目录>/config.yaml`
- `--data-provider <策略目录>/data_provider.py`

因此策略逻辑不需要依赖任何外部 SDK，只需要通过 `context.data_provider` 取数据即可。
