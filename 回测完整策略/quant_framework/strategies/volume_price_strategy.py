#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
量价驱动策略
基于A股市场特性，结合技术分析和资金流监控
"""

import numpy as np
import pandas as pd
import talib
from datetime import datetime, timedelta
from .base_strategy import BaseStrategy

class VolumePriceStrategy(BaseStrategy):
    """
    量价驱动策略类
    结合趋势共振、量价异常、资金流向等多维度分析
    """
    
    def __init__(self, 
                 symbol,
                 macd_fast=12,
                 macd_slow=26,
                 macd_signal=9,
                 boll_period=20,
                 boll_std=2.0,
                 vol_period=5,
                 atr_period=14,
                 initial_capital=1000000):
        """
        初始化策略参数
        
        参数:
            symbol (str): 交易标的代码
            macd_fast (int): MACD快线周期
            macd_slow (int): MACD慢线周期
            macd_signal (int): MACD信号线周期
            boll_period (int): 布林带周期
            boll_std (float): 布林带标准差倍数
            vol_period (int): 成交量趋势周期
            atr_period (int): ATR周期
            initial_capital (float): 初始资金
        """
        super().__init__()
        self.symbol = symbol
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.boll_period = boll_period
        self.boll_std = boll_std
        self.vol_period = vol_period
        self.atr_period = atr_period
        self.initial_capital = initial_capital
        
        # 策略状态变量
        self.position = 0  # 当前持仓
        self.cash = initial_capital  # 当前现金
        self.last_price = 0  # 最新价格
        self.stop_loss = 0  # 止损价
        self.target_price = 0  # 目标价
        
        # 技术指标缓存
        self.indicators = {}
        
    def calculate_indicators(self, df):
        """
        计算技术指标
        
        参数:
            df (pd.DataFrame): 包含OHLCV数据的DataFrame
            
        返回:
            dict: 计算得到的技术指标
        """
        # 确保数据类型正确
        df = df.astype({
            'open': 'float64',
            'high': 'float64',
            'low': 'float64',
            'close': 'float64',
            'volume': 'float64'
        })
        
        # 计算MACD
        macd, signal, hist = talib.MACD(df['close'],
                                      fastperiod=self.macd_fast,
                                      slowperiod=self.macd_slow,
                                      signalperiod=self.macd_signal)
        
        # 计算布林带
        upper, middle, lower = talib.BBANDS(df['close'],
                                          timeperiod=self.boll_period,
                                          nbdevup=self.boll_std,
                                          nbdevdn=self.boll_std)
        
        # 计算布林带宽度
        bandwidth = (upper - lower) / middle * 100
        
        # 计算ATR
        atr = talib.ATR(df['high'], df['low'], df['close'], timeperiod=self.atr_period)
        
        # 计算量价背离指数
        vol_dev = self.volume_deviation(df['close'], df['volume'])
        
        # 计算5分钟量能增幅（需要5分钟数据，这里用日线数据模拟）
        volume_growth = df['volume'].pct_change(periods=1) * 100
        
        # 计算量比
        volume_ratio = df['volume'] / df['volume'].rolling(window=5).mean()
        
        # 添加趋势过滤器
        # 1. 计算多个周期的MA
        ma20 = talib.MA(df['close'], timeperiod=20)
        ma60 = talib.MA(df['close'], timeperiod=60)
        
        # 2. 计算趋势强度指标RSI
        rsi = talib.RSI(df['close'], timeperiod=14)
        
        # 3. 计算趋势方向指标ADX
        adx = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
        
        # 4. 计算价格动量
        momentum = talib.MOM(df['close'], timeperiod=10)
        
        # 将所有指标转换为pandas Series
        return {
            'macd': pd.Series(macd, index=df.index),
            'signal': pd.Series(signal, index=df.index),
            'hist': pd.Series(hist, index=df.index),
            'upper': pd.Series(upper, index=df.index),
            'middle': pd.Series(middle, index=df.index),
            'lower': pd.Series(lower, index=df.index),
            'bandwidth': pd.Series(bandwidth, index=df.index),
            'atr': pd.Series(atr, index=df.index),
            'volume_deviation': pd.Series(vol_dev, index=df.index),
            'volume_growth': volume_growth,
            'volume_ratio': volume_ratio,
            'ma20': pd.Series(ma20, index=df.index),
            'ma60': pd.Series(ma60, index=df.index),
            'rsi': pd.Series(rsi, index=df.index),
            'adx': pd.Series(adx, index=df.index),
            'momentum': pd.Series(momentum, index=df.index)
        }
    
    def volume_deviation(self, close, volume):
        """
        计算量价背离指数
        
        参数:
            close (pd.Series): 收盘价序列
            volume (pd.Series): 成交量序列
            
        返回:
            np.array: 量价背离指数
        """
        # 计算价格趋势
        price_trend = talib.LINEARREG(close, timeperiod=self.vol_period)
        # 计算成交量趋势
        vol_trend = talib.LINEARREG(volume, timeperiod=self.vol_period)
        
        # 计算相关系数
        correlation = np.zeros(len(close))
        for i in range(self.vol_period, len(close)):
            if i >= self.vol_period:
                correlation[i] = np.corrcoef(
                    price_trend[i-self.vol_period:i],
                    vol_trend[i-self.vol_period:i]
                )[0,1]
        
        return correlation
    
    def generate_signals(self, df):
        """
        生成交易信号
        """
        signals = pd.Series(0, index=df.index)
        
        # 计算技术指标并保存
        self.indicators = self.calculate_indicators(df)
        
        # 添加调试信息
        print("\n指标值和信号统计:")
        
        # 记录上次交易日期
        last_trade_date = None
        min_hold_days = 5  # 最小持仓天数
        
        for i in range(len(df)):
            if i < self.macd_slow:  # 跳过前期数据不足的部分
                continue
            
            current_date = df.index[i]
            
            # 检查最小持仓时间
            if last_trade_date is not None:
                days_since_last_trade = (current_date - last_trade_date).days
                if days_since_last_trade < min_hold_days:
                    continue
            
            # 趋势过滤器
            trend_up = (
                self.indicators['ma20'].iloc[i] > self.indicators['ma60'].iloc[i] and  # 短期均线在长期均线上方
                self.indicators['rsi'].iloc[i] > 50 and  # RSI大于50表示上升趋势
                self.indicators['adx'].iloc[i] > 20 and  # ADX大于20表示趋势明显
                self.indicators['momentum'].iloc[i] > 0  # 动量为正
            )
            
            # MACD金叉
            macd_golden_cross = (
                self.indicators['hist'].iloc[i] > 0 and 
                self.indicators['hist'].iloc[i-1] <= 0 and
                self.indicators['macd'].iloc[i] > self.indicators['macd'].iloc[i-1]  # MACD向上
            )
            
            # 布林带挤压
            boll_squeeze = (
                self.indicators['bandwidth'].iloc[i] < 20 and  # 带宽收窄
                df['close'].iloc[i] > self.indicators['middle'].iloc[i]  # 价格在中轨上方
            )
            
            # 量价异常
            volume_deviation = (
                self.indicators['volume_deviation'].iloc[i] < 0.1 and  # 量价背离
                self.indicators['volume_growth'].iloc[i] > 0  # 成交量增长
            )
            
            # 量能验证
            volume_surge = (
                self.indicators['volume_growth'].iloc[i] > 10 and  # 当日放量
                self.indicators['volume_ratio'].iloc[i] > 1.0  # 量比大于1
            )
            
            # 生成买入信号 - 必须有趋势支撑
            if trend_up and (
                (macd_golden_cross and boll_squeeze) or  # 趋势确认信号
                (volume_deviation and volume_surge)  # 量价配合信号
            ):
                signals.iloc[i] = 1
                last_trade_date = current_date
                if i % 50 == 0:
                    print(f"\n日期 {df.index[i]}:")
                    print(f"MACD hist: {self.indicators['hist'].iloc[i]:.4f}")
                    print(f"RSI: {self.indicators['rsi'].iloc[i]:.4f}")
                    print(f"ADX: {self.indicators['adx'].iloc[i]:.4f}")
                    print(f"Signal: BUY")
            
            # 生成卖出信号 - 任一条件满足即卖出
            elif (
                # 趋势反转
                (self.indicators['hist'].iloc[i] < 0 and 
                 self.indicators['hist'].iloc[i-1] >= 0) or
                # 均线死叉
                (self.indicators['ma20'].iloc[i] < self.indicators['ma60'].iloc[i] and
                 self.indicators['ma20'].iloc[i-1] >= self.indicators['ma60'].iloc[i-1]) or
                # RSI超买
                self.indicators['rsi'].iloc[i] > 80 or
                # 价格突破布林带上轨
                df['close'].iloc[i] > self.indicators['upper'].iloc[i] or
                # 量能衰竭
                (self.indicators['volume_ratio'].iloc[i] < 0.8 and
                 self.indicators['volume_growth'].iloc[i] < -10)
            ):
                signals.iloc[i] = -1
                last_trade_date = current_date
                if i % 50 == 0:
                    print(f"\n日期 {df.index[i]}:")
                    print(f"MACD hist: {self.indicators['hist'].iloc[i]:.4f}")
                    print(f"RSI: {self.indicators['rsi'].iloc[i]:.4f}")
                    print(f"Volume ratio: {self.indicators['volume_ratio'].iloc[i]:.4f}")
                    print(f"Signal: SELL")
        
        # 打印信号统计
        print(f"\n信号统计:")
        print(f"买入信号数量: {len(signals[signals == 1])}")
        print(f"卖出信号数量: {len(signals[signals == -1])}")
        print(f"总交易信号数量: {len(signals[signals != 0])}")
        
        return signals
    
    def calculate_position_size(self, signal, close_price, available_cash):
        """
        计算仓位大小
        
        参数:
            signal (int): 交易信号
            close_price (float): 收盘价
            available_cash (float): 可用资金
            
        返回:
            int: 交易数量
        """
        if signal == 0:
            return 0
            
        # 根据趋势强度动态调整仓位
        trend_strength = min(
            self.indicators['adx'].iloc[-1] / 50,  # ADX强度
            self.indicators['rsi'].iloc[-1] / 70    # RSI强度
        )
        
        # 计算ATR动态仓位
        position_size = available_cash * 0.01 * trend_strength / (self.indicators['atr'].iloc[-1] or close_price * 0.01)
        
        # 根据信号调整方向
        position_size *= signal
        
        # 确保是100的整数倍（A股最小交易单位）
        position_size = int(position_size / 100) * 100
        
        return position_size
    
    def on_bar(self, df):
        """
        处理每个交易周期的数据
        
        参数:
            df (pd.DataFrame): 当前交易周期的OHLCV数据
            
        返回:
            dict: 交易决策信息
        """
        # 更新技术指标
        self.indicators = self.calculate_indicators(df)
        
        # 生成交易信号
        signals = self.generate_signals(df)
        current_signal = signals.iloc[-1]
        
        # 获取最新价格
        close_price = df['close'].iloc[-1]
        self.last_price = close_price
        
        # 计算交易数量
        trade_volume = self.calculate_position_size(
            current_signal,
            close_price,
            self.cash if current_signal > 0 else abs(self.position) * close_price
        )
        
        # 更新目标价和止损价
        if trade_volume > 0:
            # 动态设置止盈止损
            atr = self.indicators['atr'].iloc[-1]
            rsi = self.indicators['rsi'].iloc[-1]
            
            # 根据RSI调整止盈倍数：RSI越高，止盈越快
            profit_factor = 3.0 - (rsi - 50) / 50
            
            # 根据ADX调整止损倍数：趋势越强，止损越宽松
            adx = self.indicators['adx'].iloc[-1]
            loss_factor = 1.5 + (adx / 100)
            
            self.target_price = close_price + profit_factor * atr
            self.stop_loss = close_price - loss_factor * atr
        
        return {
            'signal': current_signal,
            'price': close_price,
            'volume': trade_volume,
            'position': self.position,
            'cash': self.cash,
            'target_price': self.target_price,
            'stop_loss': self.stop_loss
        }
    
    def update_position(self, trade_volume, trade_price):
        """
        更新持仓状态
        
        参数:
            trade_volume (int): 交易数量
            trade_price (float): 交易价格
        """
        if trade_volume != 0:
            cost = trade_volume * trade_price
            self.position += trade_volume
            self.cash -= cost 