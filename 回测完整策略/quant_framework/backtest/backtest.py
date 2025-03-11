import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ..utils.performance_metrics import calculate_performance_metrics
from .portfolio import Portfolio

class Backtest:
    """
    回测类，用于回测策略
    """
    
    def __init__(self, data, strategy, initial_capital=1000000, slippage=0.0, commission=0.0003):
        """
        初始化回测
        
        参数:
            data (dict): 数据字典，格式为 {symbol: dataframe}
            strategy (BaseStrategy): 策略对象
            initial_capital (float): 初始资金，默认为1000000
            slippage (float): 滑点，默认为0.0
            commission (float): 手续费率，默认为0.0003
        """
        self.data = data
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.slippage = slippage
        self.commission = commission
        
        self.portfolio = Portfolio(initial_capital)
        self.results = None
    
    def run(self, start_date=None, end_date=None):
        """
        运行回测
        
        参数:
            start_date (str or datetime, optional): 开始日期，默认为None，表示从最早的数据开始
            end_date (str or datetime, optional): 结束日期，默认为None，表示到最晚的数据结束
            
        返回:
            pandas.DataFrame: 回测结果
        """
        # 获取数据
        symbol = list(self.data.keys())[0]  # 获取第一个标的的代码
        df = self.data[symbol]  # 获取数据
        
        # 筛选日期范围
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]
        
        # 重置策略和投资组合
        self.portfolio.reset()
        
        # 记录每日数据
        daily_data = []
        
        # 生成交易信号
        signals = self.strategy.generate_signals(df)
        print(f"\n交易执行统计:")  # 添加调试信息
        
        # 遍历每一天
        for i in range(len(df)):
            date = df.index[i]
            price = df['close'].iloc[i]
            signal = signals.iloc[i]
            
            # 计算交易数量
            if signal == 1:  # 买入信号
                # 计算可买入数量（考虑手续费）
                available_cash = self.portfolio.cash * (1 - self.commission)
                shares = int(available_cash / (price * (1 + self.slippage)) / 100) * 100  # 确保是100的整数倍
                if shares > 0:
                    # 执行买入
                    cost = shares * price * (1 + self.slippage)
                    commission_fee = cost * self.commission
                    self.portfolio.cash -= (cost + commission_fee)
                    self.portfolio.positions[symbol] = self.portfolio.positions.get(symbol, 0) + shares
                    print(f"买入执行 - 日期: {date}, 价格: {price}, 数量: {shares}")  # 添加调试信息
                    
            elif signal == -1:  # 卖出信号
                # 获取当前持仓
                current_shares = self.portfolio.positions.get(symbol, 0)
                if current_shares > 0:
                    # 执行卖出
                    revenue = current_shares * price * (1 - self.slippage)
                    commission_fee = revenue * self.commission
                    self.portfolio.cash += (revenue - commission_fee)
                    self.portfolio.positions[symbol] = 0
                    print(f"卖出执行 - 日期: {date}, 价格: {price}, 数量: {current_shares}")  # 添加调试信息
            
            # 计算当日持仓市值
            position_value = sum(
                shares * df['close'].iloc[i]
                for symbol, shares in self.portfolio.positions.items()
            )
            
            # 记录每日数据
            daily_data.append({
                'date': date,
                'cash': self.portfolio.cash,
                'position_value': position_value,
                'total_value': self.portfolio.cash + position_value
            })
        
        # 转换为DataFrame
        self.results = pd.DataFrame(daily_data)
        self.results.set_index('date', inplace=True)
        
        # 计算收益率
        self.results['returns'] = self.results['total_value'].pct_change()
        
        # 计算累积收益率
        self.results['cumulative_returns'] = (1 + self.results['returns']).cumprod() - 1
        
        return self.results
    
    def get_performance_metrics(self, benchmark_returns=None, risk_free_rate=0.0, periods_per_year=252):
        """
        获取绩效指标
        
        参数:
            benchmark_returns (pandas.Series, optional): 基准收益率序列，默认为None
            risk_free_rate (float): 无风险利率，默认为0.0
            periods_per_year (int): 一年的周期数，日频为252，周频为52，月频为12，默认为252
            
        返回:
            pandas.DataFrame: 绩效指标
        """
        if self.results is None:
            raise ValueError("请先运行回测")
        
        return calculate_performance_metrics(self.results['returns'], benchmark_returns, risk_free_rate, periods_per_year)
    
    def plot_results(self, benchmark_returns=None):
        """
        绘制回测结果
        
        参数:
            benchmark_returns (pandas.Series, optional): 基准收益率序列，默认为None
            
        返回:
            matplotlib.figure.Figure: 图形对象
        """
        if self.results is None:
            raise ValueError("请先运行回测")
        
        # 创建图形
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        # 绘制资产价值
        ax1.plot(self.results.index, self.results['total_value'], label='Total Value')
        ax1.plot(self.results.index, self.results['cash'], label='Cash', linestyle='--', alpha=0.5)
        ax1.plot(self.results.index, self.results['position_value'], label='Position Value', linestyle='--', alpha=0.5)
        
        # 设置图形属性
        ax1.set_title('Portfolio Value')
        ax1.set_ylabel('Value')
        ax1.legend()
        ax1.grid(True)
        
        # 绘制累积收益率
        ax2.plot(self.results.index, self.results['cumulative_returns'], label='Strategy')
        
        # 如果有基准收益率，也绘制
        if benchmark_returns is not None:
            # 确保基准收益率和策略收益率有相同的索引
            common_index = self.results.index.intersection(benchmark_returns.index)
            benchmark_returns = benchmark_returns.loc[common_index]
            
            # 计算基准的累积收益率
            benchmark_cumulative_returns = (1 + benchmark_returns).cumprod() - 1
            
            # 绘制基准累积收益率
            ax2.plot(benchmark_cumulative_returns.index, benchmark_cumulative_returns, label='Benchmark')
        
        # 设置图形属性
        ax2.set_title('Cumulative Returns')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Cumulative Returns')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        
        return fig
    
    def plot_drawdown(self):
        """
        绘制回撤图
        
        返回:
            matplotlib.figure.Figure: 图形对象
        """
        if self.results is None:
            raise ValueError("请先运行回测")
        
        # 计算回撤
        cumulative_returns = self.results['cumulative_returns']
        cumulative_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - cumulative_max) / (1 + cumulative_max)
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 绘制回撤
        ax.fill_between(drawdown.index, drawdown, 0, color='r', alpha=0.3)
        ax.plot(drawdown.index, drawdown, color='r', alpha=0.5)
        
        # 设置图形属性
        ax.set_title('Drawdown')
        ax.set_xlabel('Date')
        ax.set_ylabel('Drawdown')
        ax.grid(True)
        
        return fig
    
    def plot_monthly_returns(self):
        """
        绘制月度收益率热图
        
        返回:
            matplotlib.figure.Figure: 图形对象
        """
        if self.results is None:
            raise ValueError("请先运行回测")
        
        # 计算月度收益率
        monthly_returns = self.results['returns'].resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        # 创建月度收益率表格
        monthly_returns_table = pd.DataFrame(monthly_returns)
        monthly_returns_table['year'] = monthly_returns_table.index.year
        monthly_returns_table['month'] = monthly_returns_table.index.month
        monthly_returns_table = monthly_returns_table.pivot(index='year', columns='month', values='returns')
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 绘制热图
        import seaborn as sns
        sns.heatmap(monthly_returns_table, annot=True, fmt='.1%', cmap='RdYlGn', center=0, ax=ax)
        
        # 设置图形属性
        ax.set_title('Monthly Returns')
        ax.set_xlabel('Month')
        ax.set_ylabel('Year')
        
        # 设置x轴标签为月份名称
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ax.set_xticklabels(month_names)
        
        return fig
    
    def plot_trade_analysis(self):
        """
        绘制交易分析图
        
        返回:
            matplotlib.figure.Figure: 图形对象
        """
        if self.results is None:
            raise ValueError("请先运行回测")
        
        # 获取交易历史
        trades = self.strategy.get_history()
        
        if not trades:
            return None
        
        # 转换为DataFrame
        trades_df = pd.DataFrame(trades)
        
        # 计算每笔交易的盈亏
        trades_df['profit'] = 0.0
        
        # 按照symbol和日期排序
        trades_df.sort_values(['symbol', 'date'], inplace=True)
        
        # 计算每笔交易的盈亏
        for symbol in trades_df['symbol'].unique():
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            
            buy_price = None
            buy_quantity = 0
            
            for i, trade in symbol_trades.iterrows():
                if trade['action'] == 'buy':
                    buy_price = trade['price']
                    buy_quantity = trade['quantity']
                elif trade['action'] == 'sell' and buy_price is not None:
                    sell_price = trade['price']
                    sell_quantity = trade['quantity']
                    
                    # 计算盈亏
                    profit = (sell_price - buy_price) * min(buy_quantity, sell_quantity)
                    trades_df.loc[i, 'profit'] = profit
                    
                    # 更新买入价格和数量
                    if buy_quantity > sell_quantity:
                        buy_quantity -= sell_quantity
                    else:
                        buy_price = None
                        buy_quantity = 0
        
        # 创建图形
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 绘制交易盈亏
        ax1.bar(range(len(trades_df)), trades_df['profit'], color=['g' if p > 0 else 'r' for p in trades_df['profit']])
        
        # 设置图形属性
        ax1.set_title('Trade Profit/Loss')
        ax1.set_xlabel('Trade')
        ax1.set_ylabel('Profit/Loss')
        ax1.grid(True)
        
        # 绘制盈亏分布
        ax2.hist(trades_df['profit'], bins=50, color='b', alpha=0.7)
        
        # 设置图形属性
        ax2.set_title('Profit/Loss Distribution')
        ax2.set_xlabel('Profit/Loss')
        ax2.set_ylabel('Frequency')
        ax2.grid(True)
        
        plt.tight_layout()
        
        return fig 