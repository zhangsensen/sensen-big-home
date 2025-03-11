#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略配置文件
"""

# 交易标的配置
STOCK_CONFIG = {
    'symbol': '000001',  # 股票代码
    'name': '平安银行',   # 股票名称
    'start_date': '20230101',  # 回测起始日期
    'end_date': '20231231',    # 回测结束日期
    'period': 'weekly',         # K线周期：daily, weekly, monthly
}

# 技术指标参数
INDICATOR_CONFIG = {
    'macd_fast': 10,      # MACD快线周期
    'macd_slow': 20,      # MACD慢线周期
    'macd_signal': 9,     # MACD信号线周期
    'boll_period': 30,    # 布林带周期
    'boll_std': 2.0,      # 布林带标准差倍数
    'vol_period': 5,      # 成交量趋势周期
    'atr_period': 14,     # ATR周期
}

# 回测参数
BACKTEST_CONFIG = {
    'initial_capital': 1000000,  # 初始资金
    'commission': 0.0003,        # 手续费率
    'slippage': 0.0002,         # 滑点率
    'min_holding_days': 5,       # 最小持仓天数
}

# 交易参数
TRADE_CONFIG = {
    'position_size': 0.3,        # 单次交易资金比例
    'max_positions': 3,          # 最大持仓数量
    'stop_loss': 0.05,          # 止损比例
    'take_profit': 0.15,        # 止盈比例
}

# 数据缓存目录
DATA_CACHE_DIR = 'data_cache' 