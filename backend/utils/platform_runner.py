# myquant/backend/utils/platform_runner.py
"""
MyQuant平台专用的QTrader启动器。

它的核心职责是设置正确的 Python 环境（将 myquant 项目的根目录添加到 sys.path），
以便策略代码能够成功 `from myquant.backend.clients import ...`，
然后调用 qtrader 的标准回测运行器。
"""

import sys
import argparse
import os
from pathlib import Path

# 确保 myquant 模块可以被导入
# 我们需要将项目的根目录（即 myquant 目录的父目录）添加到环境变量中
project_root = Path(__file__).resolve().parent.parent.parent.parent

# 获取当前的 PYTHONPATH，并把我们的项目根目录加在最前面
current_python_path = os.environ.get('PYTHONPATH', '')
new_python_path = str(project_root) + os.pathsep + current_python_path
os.environ['PYTHONPATH'] = new_python_path

# 同样也添加到 sys.path 以防万一
sys.path.insert(0, str(project_root))


from qtrader.runner.backtest_runner import BacktestRunner

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MyQuant Platform Runner')
    parser.add_argument('--config', required=True, help='配置文件路径')
    parser.add_argument('--strategy', help='策略文件路径')
    parser.add_argument('--data-provider', help='数据提供者文件路径')
    parser.add_argument('--start-paused', action='store_true', help='启动后立即暂停')
    parser.add_argument('--resume-from', help='从暂停状态文件恢复')

    args = parser.parse_args()

    print("=" * 60)
    print("MyQuant Platform Runner - 正在启动 QTrader...")
    print(f"PYTHONPATH set to: {os.environ['PYTHONPATH']}")
    print(f"Config: {args.config}")

    if args.resume_from:
        # 从暂停状态恢复
        print(f"Resume from: {args.resume_from}")
        print("=" * 60)
        BacktestRunner.run_resume(
            state_file=args.resume_from,
            config_path=args.config,
            data_provider_path=args.data_provider,
            start_paused=args.start_paused
        )
    else:
        # 全新启动
        print(f"Strategy: {args.strategy}")
        print(f"Data Provider: {args.data_provider}")
        print("=" * 60)
        BacktestRunner.run_new(
            config_path=args.config,
            strategy_path=args.strategy,
            data_provider_path=args.data_provider,
            start_paused=args.start_paused
        )