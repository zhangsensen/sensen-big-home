#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理工具
用于快速修改回测参数
"""

import os
import sys
import argparse
from datetime import datetime

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from quant_framework.config import (
    STOCK_CONFIG,
    INDICATOR_CONFIG,
    BACKTEST_CONFIG,
    TRADE_CONFIG
)

def validate_date(date_str):
    """验证日期格式"""
    try:
        datetime.strptime(date_str, '%Y%m%d')
        return True
    except ValueError:
        return False

def update_config():
    parser = argparse.ArgumentParser(description='修改回测配置参数')
    
    # 添加股票相关参数
    parser.add_argument('--symbol', type=str, help='股票代码')
    parser.add_argument('--name', type=str, help='股票名称')
    parser.add_argument('--start-date', type=str, help='回测开始日期 (YYYYMMDD)')
    parser.add_argument('--end-date', type=str, help='回测结束日期 (YYYYMMDD)')
    parser.add_argument('--period', choices=['daily', 'weekly', 'monthly'], help='K线周期')
    
    # 添加技术指标参数
    parser.add_argument('--macd-fast', type=int, help='MACD快线周期')
    parser.add_argument('--macd-slow', type=int, help='MACD慢线周期')
    parser.add_argument('--macd-signal', type=int, help='MACD信号线周期')
    parser.add_argument('--boll-period', type=int, help='布林带周期')
    parser.add_argument('--boll-std', type=float, help='布林带标准差倍数')
    parser.add_argument('--vol-period', type=int, help='成交量趋势周期')
    parser.add_argument('--atr-period', type=int, help='ATR周期')
    
    # 添加回测参数
    parser.add_argument('--initial-capital', type=float, help='初始资金')
    parser.add_argument('--commission', type=float, help='手续费率')
    parser.add_argument('--slippage', type=float, help='滑点率')
    parser.add_argument('--min-holding-days', type=int, help='最小持仓天数')
    
    # 添加交易参数
    parser.add_argument('--position-size', type=float, help='单次交易资金比例')
    parser.add_argument('--max-positions', type=int, help='最大持仓数量')
    parser.add_argument('--stop-loss', type=float, help='止损比例')
    parser.add_argument('--take-profit', type=float, help='止盈比例')
    
    args = parser.parse_args()
    
    # 更新配置文件
    config_path = os.path.join(project_root, 'quant_framework', 'config.py')
    with open(config_path, 'r', encoding='utf-8') as f:
        config_content = f.read()
    
    # 更新股票配置
    if args.symbol:
        config_content = config_content.replace(
            f"'symbol': '{STOCK_CONFIG['symbol']}'",
            f"'symbol': '{args.symbol}'"
        )
    if args.name:
        config_content = config_content.replace(
            f"'name': '{STOCK_CONFIG['name']}'",
            f"'name': '{args.name}'"
        )
    if args.start_date and validate_date(args.start_date):
        config_content = config_content.replace(
            f"'start_date': '{STOCK_CONFIG['start_date']}'",
            f"'start_date': '{args.start_date}'"
        )
    if args.end_date and validate_date(args.end_date):
        config_content = config_content.replace(
            f"'end_date': '{STOCK_CONFIG['end_date']}'",
            f"'end_date': '{args.end_date}'"
        )
    if args.period:
        config_content = config_content.replace(
            f"'period': '{STOCK_CONFIG['period']}'",
            f"'period': '{args.period}'"
        )
    
    # 更新技术指标配置
    if args.macd_fast:
        config_content = config_content.replace(
            f"'macd_fast': {INDICATOR_CONFIG['macd_fast']}",
            f"'macd_fast': {args.macd_fast}"
        )
    if args.macd_slow:
        config_content = config_content.replace(
            f"'macd_slow': {INDICATOR_CONFIG['macd_slow']}",
            f"'macd_slow': {args.macd_slow}"
        )
    if args.macd_signal:
        config_content = config_content.replace(
            f"'macd_signal': {INDICATOR_CONFIG['macd_signal']}",
            f"'macd_signal': {args.macd_signal}"
        )
    if args.boll_period:
        config_content = config_content.replace(
            f"'boll_period': {INDICATOR_CONFIG['boll_period']}",
            f"'boll_period': {args.boll_period}"
        )
    if args.boll_std:
        config_content = config_content.replace(
            f"'boll_std': {INDICATOR_CONFIG['boll_std']}",
            f"'boll_std': {args.boll_std}"
        )
    if args.vol_period:
        config_content = config_content.replace(
            f"'vol_period': {INDICATOR_CONFIG['vol_period']}",
            f"'vol_period': {args.vol_period}"
        )
    if args.atr_period:
        config_content = config_content.replace(
            f"'atr_period': {INDICATOR_CONFIG['atr_period']}",
            f"'atr_period': {args.atr_period}"
        )
    
    # 更新回测配置
    if args.initial_capital:
        config_content = config_content.replace(
            f"'initial_capital': {BACKTEST_CONFIG['initial_capital']}",
            f"'initial_capital': {args.initial_capital}"
        )
    if args.commission:
        config_content = config_content.replace(
            f"'commission': {BACKTEST_CONFIG['commission']}",
            f"'commission': {args.commission}"
        )
    if args.slippage:
        config_content = config_content.replace(
            f"'slippage': {BACKTEST_CONFIG['slippage']}",
            f"'slippage': {args.slippage}"
        )
    if args.min_holding_days:
        config_content = config_content.replace(
            f"'min_holding_days': {BACKTEST_CONFIG['min_holding_days']}",
            f"'min_holding_days': {args.min_holding_days}"
        )
    
    # 更新交易配置
    if args.position_size:
        config_content = config_content.replace(
            f"'position_size': {TRADE_CONFIG['position_size']}",
            f"'position_size': {args.position_size}"
        )
    if args.max_positions:
        config_content = config_content.replace(
            f"'max_positions': {TRADE_CONFIG['max_positions']}",
            f"'max_positions': {args.max_positions}"
        )
    if args.stop_loss:
        config_content = config_content.replace(
            f"'stop_loss': {TRADE_CONFIG['stop_loss']}",
            f"'stop_loss': {args.stop_loss}"
        )
    if args.take_profit:
        config_content = config_content.replace(
            f"'take_profit': {TRADE_CONFIG['take_profit']}",
            f"'take_profit': {args.take_profit}"
        )
    
    # 保存更新后的配置
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("配置已更新")
    
    # 打印当前配置
    print("\n当前配置:")
    print(f"股票代码: {STOCK_CONFIG['symbol']}")
    print(f"股票名称: {STOCK_CONFIG['name']}")
    print(f"开始日期: {STOCK_CONFIG['start_date']}")
    print(f"结束日期: {STOCK_CONFIG['end_date']}")
    print(f"K线周期: {STOCK_CONFIG['period']}")

if __name__ == "__main__":
    update_config() 