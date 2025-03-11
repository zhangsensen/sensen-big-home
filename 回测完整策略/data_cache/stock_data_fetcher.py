#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票数据获取脚本
支持日线、60分钟、30分钟、15分钟和5分钟级别的数据
"""

import os
import sys
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

# 数据配置
STOCK_CONFIG = {
    'symbol': '002085',  # 股票代码
    'name': '万丰奥威',  # 股票名称
    'start_date': '20250201',  # 开始日期
    'end_date': '20250310',  # 结束日期
    'periods': [  # 数据周期
        '60',  # 60分钟线
        '15',  # 15分钟线
        '5',  # 5分钟线
        'daily',  # 日线
    ]
}

# 数据保存路径
DATA_PATH = os.path.dirname(os.path.abspath(__file__))


def format_stock_code(symbol: str) -> str:
    """格式化股票代码"""
    symbol = symbol.zfill(6)
    if symbol.startswith(('0', '3')):
        return f"sz{symbol}"  # 深市
    elif symbol.startswith('6'):
        return f"sh{symbol}"  # 沪市
    return symbol


def get_stock_data(symbol: str, period: str, start_date: str, end_date: str, adjust: str = 'qfq') -> pd.DataFrame:
    """
    获取股票数据
    """
    try:
        print(f"正在获取 {symbol} 的 {period} 数据...")
        formatted_symbol = format_stock_code(symbol)

        if period == 'daily':
            # 日线数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

            if df is not None and not df.empty:
                df['date'] = pd.to_datetime(df['日期'])
                df.rename(columns={
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '涨跌幅': 'pct_change',
                    '涨跌额': 'change',
                    '换手率': 'turnover'
                }, inplace=True)
        else:
            # 分钟数据，使用正确的接口名称
            try:
                print(f"尝试获取分钟数据: {formatted_symbol}, 周期: {period}分钟")
                df = ak.stock_zh_a_minute(
                    symbol=formatted_symbol,
                    period=period,
                    adjust=adjust
                )
                print("原始数据预览:")
                print(df.head())

                if df is not None and not df.empty:
                    # 确保日期列存在
                    date_column = 'day' if 'day' in df.columns else 'datetime' if 'datetime' in df.columns else None
                    if date_column:
                        df['date'] = pd.to_datetime(df[date_column])
                        # 过滤日期范围
                        start = pd.to_datetime(start_date)
                        end = pd.to_datetime(end_date)
                        df = df[df['date'].between(start, end)]
                    else:
                        print("警告: 未找到日期列")
                        print("可用的列:", df.columns.tolist())
            except Exception as e:
                print(f"获取分钟数据时出错: {e}")
                print("尝试使用备用接口...")
                # 可以在这里添加备用的分钟数据接口
                return pd.DataFrame()

        if df is not None and not df.empty:
            print(f"获取到 {len(df)} 条数据")

            # 设置索引
            if 'date' in df.columns:
                df.set_index('date', inplace=True)

            # 选择需要的列
            available_columns = df.columns.tolist()
            print("可用的列:", available_columns)

            needed_columns = ['open', 'high', 'low', 'close', 'volume']
            if 'amount' in available_columns:
                needed_columns.append('amount')

            # 确保所有需要的列都存在
            existing_columns = [col for col in needed_columns if col in available_columns]
            if len(existing_columns) != len(needed_columns):
                print("警告: 部分列缺失")
                print("需要的列:", needed_columns)
                print("实际的列:", existing_columns)

            df = df[existing_columns]
            return df
        else:
            print("获取到的数据为空")
            return pd.DataFrame()

    except Exception as e:
        print(f"获取数据失败: {e}")
        print("错误类型:", type(e).__name__)
        import traceback
        print("详细错误信息:")
        print(traceback.format_exc())
        return pd.DataFrame()


def save_data(df: pd.DataFrame, symbol: str, period: str, start_date: str, end_date: str):
    """
    保存数据到CSV文件

    参数:
        df (pd.DataFrame): 股票数据
        symbol (str): 股票代码
        period (str): 数据周期
        start_date (str): 开始日期
        end_date (str): 结束日期
    """
    if df.empty:
        return

    # 创建保存目录
    save_dir = os.path.join(DATA_PATH, symbol)
    os.makedirs(save_dir, exist_ok=True)

    # 生成文件名
    filename = f"{symbol}_{period}_{start_date}_{end_date}.csv"
    filepath = os.path.join(save_dir, filename)

    # 保存数据
    df.to_csv(filepath)
    print(f"数据已保存到: {filepath}")

    # 显示数据统计
    print("\n数据统计:")
    print(f"数据条数: {len(df)}")
    print(f"日期范围: {df.index.min()} 至 {df.index.max()}")
    print("\n数据预览:")
    print(df.head())
    print("\n基本统计:")
    print(df.describe())


def main():
    """主函数"""
    # 创建数据目录
    os.makedirs(DATA_PATH, exist_ok=True)

    # 获取当前配置
    symbol = STOCK_CONFIG['symbol']
    start_date = STOCK_CONFIG['start_date']
    end_date = STOCK_CONFIG['end_date']
    periods = STOCK_CONFIG['periods']

    print(f"\n当前配置:")
    print(f"股票代码: {symbol}")
    print(f"股票名称: {STOCK_CONFIG['name']}")
    print(f"开始日期: {start_date}")
    print(f"结束日期: {end_date}")
    print(f"数据周期: {periods}\n")

    # 获取并保存数据
    for period in periods:
        df = get_stock_data(symbol, period, start_date, end_date)
        if not df.empty:
            save_data(df, symbol, period, start_date, end_date)
        print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    main()