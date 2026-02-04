# myquant/templates/strategy.py

"""
开源版策略模板（仅依赖 QTrader）。

- 数据获取：通过 `context.data_provider`（DataProvider 数据合约）
- 实盘/私有数据：请在私有环境自行实现并注入（本仓库不包含任何私有 SDK）
"""

# --- 框架核心组件 ---
# 导入策略基类，所有策略都必须继承自此类
from qtrader.strategy.base import Strategy

# --- 平台API客户端 ---
# 从平台后端导入API客户端:

# --- 第三方库 ---
# 导入策略需要的第三方库
import pandas as pd

class DualMovingAverageStrategy(Strategy):
    """
    双均线交叉策略模板。
    - 当短期均线向上穿越长期均线（金叉）时买入；
    - 当短期均线向下跌破长期均线（死叉）时卖出。
    """

    def initialize(self, context):
        """
        回测/模拟开始时执行一次，用于初始化参数与状态。
        """
        context.logger.info("--> [HOOK] initialize: 策略开始初始化...")

        # --- 策略参数设置 ---
        context.user_data['symbol'] = '000001.SZ'  # 以平安银行为例
        context.user_data['short_ma_period'] = 5
        context.user_data['long_ma_period'] = 10
        
                api_key='your_primary_api_key',
            ),
            #     api_key='your_backup_api_key',
            # ),
        }

        # --- 状态变量初始化 ---
        # 初始化时获取足量的历史数据作为基础
        symbol = context.user_data['symbol']
        long_period = context.user_data['long_ma_period']
        
        # TODO: 用你的 DataProvider 获取历史数据（例如从CSV/数据库拉取一段 close 序列）
        initial_bars = None
        )
        
        if initial_bars and symbol in initial_bars and initial_bars[symbol]:
            # initial_bars移除最新一天（最后一个）的数据（该数据在回测第一个交易日获取）
            initial_bars[symbol] = initial_bars[symbol][:-1]
            df = pd.DataFrame(initial_bars[symbol])
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
            df['close'] = df['close'].astype(float)
            context.user_data['history_df'] = df
        else:
            context.user_data['history_df'] = pd.DataFrame() # 初始化为空

        context.logger.info(
            "    策略参数: symbol=%s, short_ma=%s, long_ma=%s",
            context.user_data['symbol'],
            context.user_data['short_ma_period'],
            context.user_data['long_ma_period'],
        )
        context.logger.info(
            "    初始化完成，获取了 %d 条历史K线。", len(context.user_data.get('history_df', []))
        )

    def before_trading(self, context):
        """
        每个交易日开盘前执行一次，可用于准备工作。
        """
        context.logger.info(
            "--> [HOOK] before_trading: %s",
            context.current_dt.strftime('%Y-%m-%d'),
        )

    def handle_bar(self, context):
        """
        策略核心逻辑，按配置频率在每根 K 线结束时调用。
        """
        context.logger.debug("--> [HOOK] handle_bar: %s", context.current_dt)
        symbol = context.user_data['symbol']
        short_period = context.user_data['short_ma_period']
        long_period = context.user_data['long_ma_period']
        history_df = context.user_data.get('history_df')

        # --- 1. 增量更新历史数据 ---
        # 每个 bar 只获取最新的一根 K 线
        # TODO: 用你的 DataProvider 获取历史数据（例如从CSV/数据库拉取一段 close 序列）
        initial_bars = None
        )

        if not latest_bar_data or symbol not in latest_bar_data or not latest_bar_data[symbol]:
            context.logger.warning("无法获取最新的K线数据，跳过当前 bar。")
            return

        # 将新 K 线添加到 DataFrame
        new_bar = latest_bar_data[symbol][0]
        new_bar_time = pd.to_datetime(new_bar['time'])
        
        # 避免重复添加
        if new_bar_time not in history_df.index:
            new_df_row = pd.DataFrame([new_bar])
            new_df_row['time'] = pd.to_datetime(new_df_row['time'])
            new_df_row.set_index('time', inplace=True)
            new_df_row['close'] = new_df_row['close'].astype(float)
            
            history_df = pd.concat([history_df, new_df_row])
            
            # 保持 DataFrame 大小，防止内存无限增长
            max_len = long_period + 10
            if len(history_df) > max_len:
                history_df = history_df.iloc[-max_len:]
                
            context.user_data['history_df'] = history_df

        if len(history_df) < long_period + 1:
            context.logger.warning(
                "历史数据不足 %s 根，无法判断交叉，跳过当前 bar。", long_period + 1
            )
            return

        # --- 2. 计算技术指标 ---
        # 计算短期和长期移动平均线
        short_ma = history_df['close'].rolling(window=short_period).mean()
        long_ma = history_df['close'].rolling(window=long_period).mean()

        current_short_ma = short_ma.iloc[-1]
        current_long_ma = long_ma.iloc[-1]
        last_short_ma = short_ma.iloc[-2]
        last_long_ma = long_ma.iloc[-2]

        context.logger.debug(
            "    均线: short_ma=%.2f, long_ma=%.2f",
            current_short_ma,
            current_long_ma,
        )

        # --- 3. 生成交易信号 ---
        is_golden_cross = last_short_ma <= last_long_ma and current_short_ma > current_long_ma
        is_death_cross = last_short_ma >= last_long_ma and current_short_ma < current_long_ma

        # --- 4. 执行交易 ---
        position = context.position_manager.get_position(symbol, direction='long')

        # live_trade_client = (
        #     else （开源版不提供实盘客户端）
        # )

        if is_golden_cross:
            if position:
                context.logger.info("    金叉信号，但已持有 %s，跳过买入。", symbol)
            else:
                current_price = history_df['close'].iloc[-1]
                cash_to_use = context.portfolio.available_cash * 0.95
                amount_to_buy = int(cash_to_use / current_price)
                lot_size = context.config.get('account', {}).get('order_lot_size', 100)
                amount_to_buy = (amount_to_buy // lot_size) * lot_size

                if amount_to_buy > 0:
                    context.logger.info(
                        "    金叉信号出现！准备以市价单买入 %s 股 %s。",
                        amount_to_buy,
                        symbol,
                    )
                    context.order_manager.submit_order(
                        symbol=symbol,
                        amount=amount_to_buy,
                        order_type='MARKET',
                    )

                    # if live_trade_client:
                    #     live_trade_client.buy(
                    #         price=current_price,
                    #         quantity=amount_to_buy,
                    #     )
                else:
                    context.logger.warning("    金叉信号出现，但可用现金不足，无法下单。")

        elif is_death_cross:
            if position:
                context.logger.info(
                    "    死叉信号出现！准备以市价单卖出全部 %s 持仓，共 %s 股。",
                    symbol,
                    position.total_amount,
                )
                context.order_manager.submit_order(
                    symbol=symbol,
                    amount=-position.total_amount,
                    order_type='MARKET',
                )

                # 实盘示例：使用指定连接执行卖出，取消以下注释。
                # if live_trade_client:
                #     live_trade_client.sell(
                #         price=history_df['close'].iloc[-1],
                #         quantity=position.total_amount,
                #     )
            else:
                context.logger.info("    死叉信号，但当前无 %s 持仓，跳过卖出。", symbol)

    def after_trading(self, context):
        """
        每个交易日收盘后执行一次，可用于清理和记录。
        """
        context.logger.info(
            "--> [HOOK] after_trading: %s",
            context.current_dt.strftime('%Y-%m-%d'),
        )

    def on_end(self, context):
        """
        回测/模拟结束时执行一次。
        """
        context.logger.info("--> [HOOK] on_end: 回测/模拟结束。")
        net_worth = context.portfolio.net_worth
        context.logger.info("    最终净资产: %.2f", net_worth)
