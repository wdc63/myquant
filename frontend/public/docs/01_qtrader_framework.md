# MyQuant 平台 API 文档

欢迎使用 MyQuant 量化交易平台。本文档详细介绍平台提供的所有 API 接口，包括策略框架、行情数据和交易功能，旨在帮助您快速、高效地开发和回测您的量化策略。

---

<h1 id="qtrader-framework">一、QTrader 策略框架</h1>

平台策略层基于 QTrader 回测框架，其核心是事件驱动，并提供了丰富的 API 接口用于策略编写、账户管理和订单执行。

<h2 id="qtrader-quickstart">1.1 快速上手</h2>

所有策略都必须继承自 `qtrader.strategy.base.Strategy` 基类。开源版不再注入 `stock_api_client`。请通过 `context.data_provider`（数据合约）获取数据。

开源版不内置实盘接口（如果需要，请在私有环境自行实现并注入）。
1.  **`tdx_api_client（开源版不提供）`**: 一个可选的、全局共享的默认实例。它需要您在 `myquant_config.json` 中进行配置。
2.  **`create_tdx_api_client（开源版不提供）()`**: 一个工厂函数，允许您在策略代码中按需动态创建任意多个、任意配置的客户端实例。**（推荐）**

### 导入方式

```python
# 策略基类
from qtrader.strategy.base import Strategy

```

如果 `myquant_config.json` 提供了默认的通达信参数，`tdx_api_client（开源版不提供）` 会自动可用。但更推荐的做法是，在策略中调用 `create_tdx_api_client（开源版不提供）(base_url=..., api_key=...)` 来构造和管理您自己的客户端实例，以获得更好的灵活性和代码清晰度，请参加模版策略。

### 最小策略示例

```python
class MyStrategy(Strategy):
    def initialize(self, context: Context):
        """策略初始化，只在开始时运行一次"""
        context.logger.info("策略开始初始化...")
        context.user_data['symbols'] = ['600519'] # 设置股票池

    def handle_bar(self, context: Context):
        """每个Bar都会调用，这是策略的核心逻辑"""
        # 1. 获取行情数据
        symbol = context.user_data['symbols'][0]
        tick_data = context.data_provider.market.get_tick(code=symbol,date=context.current_dt.strftime('%Y-%m-%d %H:%M:%S'))
        if not tick_data or not tick_data.get(symbol):
            context.logger.warning(f"未能获取 {symbol} 的行情数据")
            return
        
        price = tick_data[symbol]['current_price']
        context.logger.info(f"获取到 {symbol} 的最新价格: {price}")

        # 2. 交易逻辑
        position = context.position_manager.get_position(symbol)
        if position is None: # 如果没有持仓，则买入
            context.order_manager.submit_order(
                symbol=symbol,
                amount=100,  # 正数为买入
                order_type="market"
            )
            context.logger.info(f"以市价单买入 100 股 {symbol}")
```

当策略需要与不同的通达信服务器交互时（例如主备切换），可在 `initialize` 等生命周期方法中调用 `create_tdx_api_client（开源版不提供）` 创建并管理多个实例，例如将它们保存在 `context.user_data` 中。

---

<h2 id="qtrader-lifecycle">1.2 生命周期方法</h2>

框架会在策略的生命周期中的特定时间点自动调用以下方法。您只需根据需要实现它们即可。

| 方法名 | 调用时机 | 是否必须实现 |
| :--- | :--- | :--- |
| `initialize(context)` | 回测开始时，仅调用一次 | **是** |
| `before_trading(context)` | 每个交易日开盘前 | 否 |
| `handle_bar(context)` | 策略核心逻辑，按配置频率（日/分钟）调用 | 否 |
| `after_trading(context)` | 每个交易日收盘后 | 否 |
| `broker_settle(context)` | 每日结算完成后（资金和持仓已是最终状态） | 否 |
| `on_end(context)` | 整个回测结束时，仅调用一次 | 否 |

---

<h2 id="qtrader-context">1.3 Context 上下文对象</h2>

`context` 对象是策略与回测引擎交互的唯一接口，它被作为参数传递给所有生命周期方法。

### 1.3.1 时间与环境

- `context.current_dt` (`datetime`): 获取回测系统的当前时间戳。
- `context.mode` (`str`): 获取当前运行模式 (`'backtest'` 或 `'simulation'`)。

### 1.3.2 自定义数据存储

- `context.user_data` (`dict`): 一个字典，用于在策略的整个生命周期中存储和传递任何您需要的数据。
- `context.set(key, value)`: `context.user_data[key] = value` 的便捷写法。
- `context.get(key, default=None)`: `context.user_data.get(key, default)` 的便捷写法。

### 1.3.3 账户状态 (`context.portfolio`)

提供账户的整体财务概览。

| 属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| `initial_cash` | `float` | 初始资金 |
| `net_worth` | `float` | **账户净资产** |
| `total_assets` | `float` | 总资产 |
| `cash` | `float` | 总现金 |
| `available_cash` | `float` | **可用资金** |
| `margin` | `float` | 占用的保证金（用于空头持仓） |
| `returns` | `float` | 基于初始资金的累计收益率 |
| `long_positions_value` | `float` | 多头持仓市值 |
| `short_positions_value` | `float` | 空头持仓市值（正值，表示负债） |

### 1.3.4 持仓管理 (`context.position_manager`)

提供对当前所有持仓的详细访问。

#### get_position(symbol: str, direction: str = "long") -> Position | None

获取指定证券和方向的持仓。

- **参数**:
    - `symbol` (`str`): 证券代码。
    - `direction` (`str`): 方向，`"long"` (多头) 或 `"short"` (空头)。
- **返回**: `Position` 对象或 `None`。

#### get_all_positions() -> list[Position]

获取当前所有的持仓对象列表。

#### Position 持仓对象属性

| 属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| `symbol` | `str` | 证券代码 |
| `total_amount` | `int` | 总持仓数量 (恒为正数) |
| `available_amount` | `int` | **可卖出数量** (已考虑T+1规则) |
| `avg_cost` | `float` | 持仓成本价 |
| `market_value` | `float` | 当前市值 |
| `unrealized_pnl` | `float` | 未实现盈亏 |
| `direction` | `str` | 持仓方向 (`"long"` 或 `"short"`) |

**示例:**
```python
# 获取茅台的多头持仓
position = context.position_manager.get_position("600519", direction="long")
if position:
    print(f"持仓数量: {position.total_amount}")
    print(f"可卖数量: {position.available_amount}")
    print(f"成本价: {position.avg_cost}")
```

### 1.3.5 订单管理 (`context.order_manager`)

所有交易操作都通过 `OrderManager` 完成。

#### submit_order(symbol, amount, order_type, price=None) -> str | None

**核心下单函数**。

- **参数**:
    - `symbol` (`str`): 证券代码。
    - `amount` (`int`): **下单数量。正数为买入，负数为卖出。**
    - `order_type` (`str`): 订单类型，`"market"` (市价单) 或 `"limit"` (限价单)。
    - `price` (`float`, 可选): 如果是限价单，则必须提供此价格。
- **返回**: 如果下单成功，返回唯一的订单 ID (`order_id`) 字符串。

**示例:**
```python
# 市价买入 100 股
order_id_buy = context.order_manager.submit_order(
    symbol="600519",
    amount=100,
    order_type="market"
)

# 限价卖出 200 股
order_id_sell = context.order_manager.submit_order(
    symbol="000001",
    amount=-200,
    order_type="limit",
    price=15.5
)
```

#### cancel_order(order_id: str) -> bool

根据订单 ID 撤销一个未成交的订单。

#### get_open_orders() -> list[Order]

获取所有当前状态为 `OPEN` (未成交) 的订单列表。

#### get_filled_orders_today() -> list[Order]

获取当日所有已成交 (`FILLED`) 的订单列表。

#### get_all_orders_history() -> list[Order]

获取过去所有交易日的已成交订单。

#### Order 订单对象属性

| 属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | `str` | 订单的唯一ID |
| `symbol` | `str` | 证券代码 |
| `amount` | `int` | 订单数量 (恒为正数) |
| `side` | `str` | 交易方向 (`"BUY"` 或 `"SELL"`) |
| `order_type` | `str` | 订单类型 (`"MARKET"` 或 `"LIMIT"`) |
| `limit_price` | `float` | 限价单的价格 |
| `status` | `str` | 订单状态 (`"OPEN"`, `"FILLED"`, `"CANCELLED"`) |
| `created_time` | `datetime` | 订单创建时间 |
| `filled_time` | `datetime` | 订单成交时间 |
| `filled_price` | `float` | 订单成交均价 |
| `commission` | `float` | 交易手续费 |

### 1.3.6 日志记录

- `context.logger.info("...")`: 记录普通信息
- `context.logger.warning("...")`: 记录警告信息
- `context.logger.error("...")`: 记录错误信息

### 1.3.7 高级功能方法

#### add_schedule(time_str: str)

在默认的 `handle_bar` 调用时间之外，增加自定义的策略调用时间点。**只能在 `initialize()` 中调用**。

- **参数**:
    - `time_str` (`str`): 时间字符串，格式 "HH:MM:SS"
- **使用场景**: 多时间点交易策略（如开盘、午盘、收盘分别执行不同逻辑）

**示例**:
```python
def initialize(self, context: Context):
    # 除了默认的14:55调用，还在以下时间点调用handle_bar
    context.add_schedule("09:35:00")  # 开盘后5分钟
    context.add_schedule("11:25:00")  # 午盘前5分钟
    context.add_schedule("14:55:00")  # 收盘前5分钟
```

#### set_initial_state(cash: float, positions: list[dict])

覆盖配置文件中的初始资金和持仓，设置一个自定义的期初状态。**只能在 `initialize()` 中调用一次**。

- **参数**:
    - `cash` (`float`): 初始现金
    - `positions` (`list[dict]`): 初始持仓列表，每个字典包含：
        - `'symbol'` (`str`, 必须): 证券代码
        - `'amount'` (`int`, 必须): 持仓数量（正数=多头，负数=空头）
        - `'avg_cost'` (`float`, 可选): 成本价
        - `'symbol_name'` (`str`, 可选): 证券名称

**使用场景**: 从特定的非零状态开始回测，测试调仓策略等

**示例**:
```python
def initialize(self, context: Context):
    # 设置初始状态：100万现金 + 1000股茅台
    context.set_initial_state(
        cash=1000000.0,
        positions=[
            {
                'symbol': '600519',
                'amount': 1000,
                'avg_cost': 1800.0,
                'symbol_name': '贵州茅台'
            }
        ]
    )
```

#### align_account_state(cash: float, positions: list[dict])

将系统内部的账户状态（现金和持仓）与外部实际账户状态进行强制对齐。**建议在 `broker_settle()` 中调用**。

- **参数**: 与 `set_initial_state` 完全相同
- **使用场景**: 模拟交易或实盘中，修正可能存在的状态漂移

**示例**:
```python
def broker_settle(self, context: Context):
    # 每日结算后，对齐实盘账户
    if context.mode == 'simulation':
        # 开源版不内置实盘接口；如需对齐账户，请在私有环境自行实现并调用。

        # 转换格式
        positions = []
        for holding in real_holdings:
            positions.append({
                'symbol': holding['证券代码'],
                'amount': holding['证券数量'],
                'avg_cost': holding['成本价'],
                'symbol_name': holding['证券名称']
            })

        # 对齐账户状态
        context.align_account_state(
            cash=real_balance['可用'],
            positions=positions
        )
```

---

<h2 id="qtrader-config">1.4 配置文件说明</h2>

平台运行时会自动生成和使用 `config.yaml` 配置文件。以下是关键配置项的说明：

### 1.4.1 引擎核心配置

```yaml
engine:
  mode: backtest                  # 运行模式: backtest (回测) / simulation (模拟盘)
  frequency: daily                # 运行频率: daily / minute / tick
  tick_interval_seconds: 3        # Tick模式下的秒数间隔
  start_date: "2023-01-01"        # 回测开始日期
  end_date: "2023-12-31"          # 回测结束日期
  strategy_name: "MyStrategy"     # 策略名称（可选）
  enable_intraday_statistics: true # 记录盘中收益统计（仅tick/minute模式）
  intraday_update_frequency: 5    # 盘中收益更新频率（分钟）
```

### 1.4.2 账户与交易规则

```yaml
account:
  initial_cash: 1000000           # 初始资金
  trading_rule: 'T+1'             # 交易制度: 'T+1' 或 'T+0'
  trading_mode: 'long_only'       # 交易模式: 'long_only' (仅多头) 或 'long_short' (多空)
  order_lot_size: 100             # 订单最小单位 (A股为100股)
  short_margin_rate: 0.2          # 做空保证金比例
```

### 1.4.3 生命周期钩子

```yaml
lifecycle:
  # 交易时段定义 (适用于分钟/Tick频率)
  trading_sessions:
    - ["09:30:00", "11:30:00"]
    - ["13:00:00", "15:00:00"]

  # 策略钩子执行时间点
  hooks:
    before_trading: "09:15:00"    # 盘前准备
    handle_bar: "14:55:00"        # 日频策略运行时间
    after_trading: "15:05:00"     # 盘后处理
    broker_settle: "15:30:00"     # 日终结算
```

**多时间点配置**（可选）:
```yaml
lifecycle:
  hooks:
    handle_bar_times:             # 使用列表指定多个时间点
      - "10:00:00"
      - "14:00:00"
      - "14:55:00"
```

### 1.4.4 撮合与费用

```yaml
matching:
  slippage:
    type: fixed                   # 滑点类型 (目前仅支持 fixed)
    rate: 0.001                   # 固定滑点率 (千分之一)

  commission:
    buy_commission: 0.0002        # 买入佣金率 (万分之二)
    sell_commission: 0.0002       # 卖出佣金率 (万分之二)
    buy_tax: 0.0                  # 买入印花税率 (A股为0)
    sell_tax: 0.001               # 卖出印花税率 (千分之一)
    min_commission: 5.0           # 单笔最低佣金 (元)
```

### 1.4.5 基准与报告

```yaml
benchmark:
  symbol: "000300"                # 基准标的代码 (如沪深300)

report:
  auto_open: true                 # 回测结束后是否自动打开报告
```

### 1.4.6 工作区配置

```yaml
workspace:
  # root_dir: "qtrader_runs"      # 可选，全局根目录
  create_code_snapshot: true      # 是否创建策略代码快照
  create_config_snapshot: true    # 是否创建配置文件快照
  create_data_provider_snapshot: true # 是否创建数据提供者快照
  auto_save_state: false          # 是否自动保存状态（每10天）
  auto_save_interval: 10          # 自动保存间隔（天）
  auto_save_mode: 'overwrite'     # 保存模式: 'overwrite' / 'increment'
```
---

<h2 id="qtrader-dataprovider">1.5 数据提供者 (Data Provider)</h2>

QTrader 的数据源是可插拔的。其核心引擎与数据获取层完全分离，遵循“依赖倒置原则”。这意味着，理论上您可以通过实现标准接口，轻松接入任何自定义的外部数据源（如本地文件、数据库或第三方API）。

### 平台内置数据提供者

在 **MyQuant 平台**中，您**无需**手动编写数据提供者。平台会把你的 `data_provider.py` 作为数据提供者传给 QTrader；策略通过 `context.data_provider` 获取数据。

开源版不提供 `stock_api_client`。你需要在 `data_provider.py` 中实现数据合约。

### 自定义数据提供者 (高级)

对于需要接入**私有数据源**或有特殊需求的专家用户，QTrader 仍然保留了自定义数据提供者的能力。任何自定义数据源都必须创建一个继承自 `qtrader.data.interface.AbstractDataProvider` 的子类，并完整实现其所有抽象方法。

下面是 `AbstractDataProvider` 的完整接口定义，包含了所有需要实现的方法及其详细说明：

```python
# qtrader/data/interface.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

class AbstractDataProvider(ABC):
    """
    数据提供者抽象基类 (Abstract Base Class for Data Providers)。

    本接口定义了 QTrader 核心引擎与所有外部数据源之间的标准“契约”。
    任何想要接入 QTrader 的数据源（无论是来自本地文件、数据库还是实时 API），
    都必须创建一个继承自本类的子类，并完整实现其所有抽象方法。
    """
    
    @abstractmethod
    def get_trading_calendar(self, start: str, end: str) -> List[str]:
        """
        获取指定日期范围内的所有交易日。

        此方法是回测时间循环的基础。`Scheduler` 在回测开始时会调用此方法
        一次，以确定需要遍历的所有交易日。

        Args:
            start (str): 开始日期 (格式: 'YYYY-MM-DD')。
            end (str): 结束日期 (格式: 'YYYY-MM-DD')。

        Returns:
            List[str]: 一个按升序排列的交易日字符串列表 (['YYYY-MM-DD', ...])。
                       如果指定范围内没有交易日，应返回空列表。
        """
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str, dt: datetime) -> Optional[Dict]:
        """
        获取指定证券在特定时间点的实时价格快照。

        这是框架中被调用最频繁的方法之一。`MatchingEngine` 在每次尝试撮合
        订单时，以及在每日结算更新持仓市值时，都会调用此方法来获取最新价格。

        Args:
            symbol (str): 证券代码。
            dt (datetime): 查询的时间点。

        Returns:
            Optional[Dict]: 一个包含价格信息的字典。如果此刻该证券无有效价格数据
                            （例如，未上市或数据缺失），应返回 None。
                            字典结构:
                            {
                                'current_price': float,  # 当前价 (必须提供)
                                'ask1': float,           # 卖一价 (可选, 用于更精确的市价单撮合)
                                'bid1': float,           # 买一价 (可选, 用于更精确的市价单撮合)
                                'high_limit': float,     # 当日涨停价 (可选, 用于风控)
                                'low_limit': float,      # 当日跌停价 (可选, 用于风控)
                            }
        """
        pass
    
    @abstractmethod
    def get_symbol_info(self, symbol: str, date: str) -> Optional[Dict]:
        """
        获取指定证券在特定日期的静态信息。

        `MatchingEngine` 在处理订单前会调用此方法，以检查诸如停牌等状态，
        避免在不应交易的证券上下单。

        Args:
            symbol (str): 证券代码。
            date (str): 查询的日期 (格式: 'YYYY-MM-DD')。

        Returns:
            Optional[Dict]: 一个包含静态信息的字典。如果无该证券信息，返回 None。
                            字典结构:
                            {
                                'symbol_name': str,  # 证券的中文或英文名称
                                'is_suspended': bool, # 在 `date` 这一天是否处于停牌状态
                            }
        """
        pass
```
更多 DataProvider 说明见「数据提供者（Data Provider）」文档。

---
