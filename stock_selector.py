#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A股选股策略
基于通过测试的AKShare API实现
实现复合型选股策略，包括基本面、技术面和资金面多维度筛选
"""

import os
import time
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

# 导入AKShare库
try:
    import akshare as ak
    print(f"成功导入 AKShare 库，版本: {ak.__version__}")
except ImportError:
    print("未安装 AKShare 库，请使用命令 pip install akshare 安装")
    exit(1)

# 定义输出目录
OUTPUT_DIR = "选股结果"

# 市场相关参数
MARKET_PARAMS = {
    "start_date": (datetime.now() - timedelta(days=365)).strftime("%Y%m%d"),  # 扩展到1年数据以分析趋势
    "end_date": datetime.now().strftime("%Y%m%d"),
}

# 筛选条件参数
FILTER_PARAMS = {
    # 基本面条件
    "growth_rate_min": 20.0,       # 最小增长率(%)
    "institutional_min": 3,         # 最小机构持股家数
    "min_market_cap": 5000000000,   # 最小市值(50亿)
    "max_market_cap": 30000000000,  # 最大市值(300亿)
    
    # 技术面条件
    "ma_days": 50,                  # 均线天数
    "amplitude_min": 15.0,          # 最小振幅(%)
    "volume_increase": 50.0,        # 成交量放大比例(%)
    
    # 资金面条件
    "main_inflow_min": 50000000,    # 最小主力净流入(5000万元)
    "north_increase_min": 0.5,      # 北向资金持股比例增幅(%)
}

class StockSelector:
    """股票选择器类，实现基于多因子的选股策略"""
    
    def __init__(self):
        """初始化选股器"""
        self.create_output_dir()
        self.selected_stocks = []
        
    def create_output_dir(self):
        """创建输出目录"""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
    def format_stock_code(self, symbol: str) -> str:
        """格式化股票代码"""
        symbol = symbol.zfill(6)
        if symbol.startswith(('0', '3')):
            return f"sz{symbol}"  # 深市
        elif symbol.startswith('6'):
            return f"sh{symbol}"  # 沪市
        return symbol
        
    def get_data_with_retry(self, data_func, data_name, max_retries=3, retry_delay=2):
        """带重试机制的数据获取函数"""
        for attempt in range(max_retries):
            try:
                data = data_func()
                if data is not None and not data.empty:
                    return data
                if attempt < max_retries - 1:
                    print(f"获取{data_name}数据为空，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
            except Exception as e:
                print(f"获取{data_name}数据出错: {e}")
                if attempt < max_retries - 1:
                    print(f"{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
        
        print(f"获取{data_name}数据失败，已达到最大重试次数")
        return pd.DataFrame()
    
    def get_a_stock_list(self) -> pd.DataFrame:
        """获取A股列表"""
        print("获取A股列表...")
        try:
            # 通过测试的API获取股票列表
            stock_list = self.get_data_with_retry(
                lambda: ak.stock_zh_a_spot_em(),
                "A股列表"
            )
            
            if stock_list.empty:
                return pd.DataFrame()
                
            # 重命名列，确保一致性
            if "代码" in stock_list.columns:
                stock_list.rename(columns={"代码": "股票代码", "名称": "股票名称"}, inplace=True)
                
            print(f"获取到 {len(stock_list)} 只股票")
            return stock_list
        except Exception as e:
            print(f"获取A股列表出错: {e}")
            return pd.DataFrame()
            
    def get_stock_history(self, symbol: str) -> pd.DataFrame:
        """获取股票历史数据"""
        try:
            # 使用通过测试的API获取历史数据
            history_data = self.get_data_with_retry(
                lambda: ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily", 
                    start_date=MARKET_PARAMS["start_date"], 
                    end_date=MARKET_PARAMS["end_date"],
                    adjust=""
                ),
                f"股票{symbol}历史数据"
            )
            
            if not history_data.empty and "日期" in history_data.columns:
                # 标准化列名
                history_data.rename(columns={
                    "日期": "date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "amount",
                    "振幅": "amplitude",
                    "涨跌幅": "pct_change",
                    "涨跌额": "change",
                    "换手率": "turnover"
                }, inplace=True)
                
                # 转换日期类型
                history_data["date"] = pd.to_datetime(history_data["date"])
                history_data.set_index("date", inplace=True)
                
                # 计算技术指标
                self.calculate_technical_indicators(history_data)
                
            return history_data
        except Exception as e:
            print(f"获取股票{symbol}历史数据出错: {e}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> None:
        """计算技术指标"""
        # 确保数据按日期排序
        df.sort_index(inplace=True)
        
        # 计算移动平均线
        df[f'MA{FILTER_PARAMS["ma_days"]}'] = df['close'].rolling(window=FILTER_PARAMS["ma_days"]).mean()
        
        # 计算MA5、MA10、MA20用于判断均线多头排列
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        
        # 计算成交量变化率
        df['volume_change'] = df['volume'].pct_change() * 100
    
    def get_financial_growth(self, symbol: str) -> Optional[Dict[str, float]]:
        """获取财务增长数据"""
        try:
            # 使用通过测试的API获取财务指标
            financial_data = self.get_data_with_retry(
                lambda: ak.stock_financial_analysis_indicator(symbol=symbol),
                f"股票{symbol}财务数据"
            )
            
            if financial_data.empty:
                return None
                
            result = {
                "revenue_growth": None,
                "profit_growth": None
            }
            
            # 查找相关增长指标列
            for col in financial_data.columns:
                if "营业收入同比增长" in col or "营收增长" in col:
                    try:
                        values = []
                        # 获取近2年数据
                        for i in range(min(8, len(financial_data))):  # 取前8个季度的数据
                            val_str = str(financial_data.iloc[i][col]).replace('%', '').strip()
                            if val_str and val_str != '--' and val_str != 'nan':
                                values.append(float(val_str))
                                
                        if values:
                            result["revenue_growth"] = sum(values) / len(values)  # 平均增长率
                    except Exception as e:
                        print(f"处理营收增长数据出错: {e}")
                
                if "净利润同比增长" in col:
                    try:
                        values = []
                        # 获取近2年数据
                        for i in range(min(8, len(financial_data))):  # 取前8个季度的数据
                            val_str = str(financial_data.iloc[i][col]).replace('%', '').strip()
                            if val_str and val_str != '--' and val_str != 'nan':
                                values.append(float(val_str))
                                
                        if values:
                            result["profit_growth"] = sum(values) / len(values)  # 平均增长率
                    except Exception as e:
                        print(f"处理净利润增长数据出错: {e}")
            
            return result
        except Exception as e:
            print(f"获取股票{symbol}财务增长数据出错: {e}")
            return None
        
    def get_fund_flow(self, symbol: str, days: int = 3) -> Dict[str, Any]:
        """获取资金流向数据"""
        result = {
            "today_inflow": None,
            "consecutive_inflow": False,
            "total_days": 0
        }
        
        try:
            # 获取个股资金流向数据
            fund_flow_data = self.get_data_with_retry(
                lambda: ak.stock_individual_fund_flow(symbol="个股"),
                "资金流向数据"
            )
            
            if fund_flow_data.empty:
                return result
                
            # 查找并返回对应股票的数据
            if "股票代码" in fund_flow_data.columns:
                stock_flow = fund_flow_data[fund_flow_data["股票代码"] == symbol]
                if not stock_flow.empty:
                    # 找到主力净流入相关列
                    net_inflow_col = None
                    for col in stock_flow.columns:
                        if '主力净流入' in col or '主力净额' in col:
                            net_inflow_col = col
                            break
                    
                    if net_inflow_col:
                        # 尝试获取当日净流入额
                        today_inflow_str = str(stock_flow[net_inflow_col].values[0])
                        try:
                            # 处理可能的单位（万、亿）
                            if '万' in today_inflow_str:
                                today_inflow_str = today_inflow_str.replace('万', '')
                                result["today_inflow"] = float(today_inflow_str) * 10000
                            elif '亿' in today_inflow_str:
                                today_inflow_str = today_inflow_str.replace('亿', '')
                                result["today_inflow"] = float(today_inflow_str) * 100000000
                            else:
                                result["today_inflow"] = float(today_inflow_str)
                        except:
                            result["today_inflow"] = None
            
            # 获取连续净流入天数
            # 由于当前API限制，我们无法获取历史资金流向数据
            # 这里使用模拟数据，实际应用中需要使用历史数据API
            # 连续净流入功能待实现
            result["consecutive_inflow"] = False
            result["total_days"] = 0
            
            return result
        except Exception as e:
            print(f"获取股票{symbol}资金流向数据出错: {e}")
            return result
            
    def get_top_holders(self, symbol: str) -> int:
        """获取前十大流通股东中的机构数量"""
        try:
            # 使用通过测试的API获取十大流通股东数据
            formatted_symbol = self.format_stock_code(symbol)
            
            # 注意：API参数根据测试结果调整
            holders_data = self.get_data_with_retry(
                lambda: ak.stock_gdfx_free_top_10_em(symbol=formatted_symbol, date="20231231"),
                f"股票{symbol}十大流通股东"
            )
            
            if holders_data.empty:
                return 0
                
            # 计算机构股东数量
            institution_count = 0
            
            # 查找股东名称列
            name_col = None
            for col in holders_data.columns:
                if "股东名称" in col or "持股机构" in col:
                    name_col = col
                    break
                    
            if not name_col:
                return 0
                
            # 检查每个股东是否为机构
            institution_keywords = [
                "基金", "证券", "保险", "社保", "养老", "投资", "资管", "信托", "银行", 
                "公司", "有限", "集团", "管理"
            ]
            
            for _, row in holders_data.iterrows():
                holder_name = row[name_col]
                # 检查是否为机构股东
                if any(keyword in holder_name for keyword in institution_keywords):
                    institution_count += 1
            
            return institution_count
        except Exception as e:
            print(f"获取股票{symbol}十大流通股东数据出错: {e}")
            return 0
            
    def get_north_bound_holding(self, symbol: str) -> Dict[str, Any]:
        """获取北向资金持股信息"""
        result = {
            "holding_ratio": None,
            "ratio_change": None
        }
        
        try:
            # 这里使用测试通过的API
            north_data = self.get_data_with_retry(
                lambda: ak.stock_hsgt_fund_flow_summary_em(),
                "北向资金概况"
            )
            
            # 北向资金持股细节难以通过现有API获取
            # 实际应用中可能需要更专业的数据源
            # 这里设置为None作为占位符
            
            return result
        except Exception as e:
            print(f"获取股票{symbol}北向资金数据出错: {e}")
            return result
            
    def get_unusual_trading(self, symbol: str) -> Dict[str, bool]:
        """获取异常交易数据（大宗交易、龙虎榜）"""
        result = {
            "block_trade": False,
            "top_list": False
        }
        
        try:
            # 获取大宗交易数据
            formatted_symbol = self.format_stock_code(symbol)
            
            # 使用测试通过的大宗交易API
            block_trade_data = self.get_data_with_retry(
                lambda: ak.stock_dzjy_mrtj(
                    start_date=MARKET_PARAMS["start_date"], 
                    end_date=MARKET_PARAMS["end_date"]
                ),
                "大宗交易统计"
            )
            
            if not block_trade_data.empty:
                # 查找对应股票的大宗交易记录
                for col in block_trade_data.columns:
                    if "证券代码" in col or "股票代码" in col:
                        if symbol in block_trade_data[col].values:
                            # 查找溢价成交相关列
                            for price_col in block_trade_data.columns:
                                if "溢价率" in price_col or "折溢率" in price_col:
                                    # 过滤出该股票的记录
                                    stock_trades = block_trade_data[block_trade_data[col] == symbol]
                                    if not stock_trades.empty:
                                        # 检查是否有溢价交易
                                        for _, trade in stock_trades.iterrows():
                                            try:
                                                premium_str = str(trade[price_col]).replace('%', '')
                                                if premium_str and premium_str != '--':
                                                    premium = float(premium_str)
                                                    if premium > 0:
                                                        result["block_trade"] = True
                                                        break
                                            except:
                                                pass
                                    break
                        break
            
            # 获取龙虎榜数据
            top_list_data = self.get_data_with_retry(
                lambda: ak.stock_lhb_detail_em(
                    start_date=MARKET_PARAMS["start_date"], 
                    end_date=MARKET_PARAMS["end_date"]
                ),
                "龙虎榜明细"
            )
            
            if not top_list_data.empty:
                # 查找对应股票的龙虎榜记录
                for col in top_list_data.columns:
                    if "证券代码" in col or "股票代码" in col:
                        if symbol in top_list_data[col].values:
                            result["top_list"] = True
                            break
            
            return result
        except Exception as e:
            print(f"获取股票{symbol}异常交易数据出错: {e}")
            return result
            
    def check_market_cap(self, symbol: str, stock_data: pd.DataFrame) -> bool:
        """检查股票市值是否在目标范围内"""
        try:
            # 在股票实时数据中查找市值相关列
            market_cap = None
            for col in stock_data.columns:
                if "总市值" in col or "市值" in col:
                    market_cap_str = str(stock_data[col]).replace(',', '')
                    
                    # 处理可能的单位（万、亿）
                    if '万' in market_cap_str:
                        market_cap_str = market_cap_str.replace('万', '')
                        market_cap = float(market_cap_str) * 10000
                    elif '亿' in market_cap_str:
                        market_cap_str = market_cap_str.replace('亿', '')
                        market_cap = float(market_cap_str) * 100000000
                    else:
                        market_cap = float(market_cap_str)
                    break
            
            if market_cap is None:
                return False
                
            # 检查市值是否在目标范围内
            return (market_cap >= FILTER_PARAMS["min_market_cap"] and 
                    market_cap <= FILTER_PARAMS["max_market_cap"])
        except Exception as e:
            print(f"检查股票{symbol}市值出错: {e}")
            return False
                
    def check_technical_conditions(self, history_data: pd.DataFrame) -> Dict[str, bool]:
        """检查技术面条件"""
        result = {
            "above_ma": False,
            "ma_alignment": False,
            "amplitude_ok": False,
            "volume_increase": False,
            "pattern_breakout": False
        }
        
        try:
            if history_data.empty:
                return result
                
            # 检查最近一个交易日收盘价是否站上50日均线
            latest_data = history_data.iloc[-1]
            if latest_data['close'] > latest_data[f'MA{FILTER_PARAMS["ma_days"]}']:
                result["above_ma"] = True
                
            # 检查均线多头排列（MA5 > MA10 > MA20）
            if (latest_data['MA5'] > latest_data['MA10'] and 
                latest_data['MA10'] > latest_data['MA20']):
                result["ma_alignment"] = True
                
            # 检查过去一个月振幅是否符合要求
            recent_data = history_data.iloc[-30:]  # 最近30天数据
            mean_amplitude = recent_data['amplitude'].mean()
            if mean_amplitude >= FILTER_PARAMS["amplitude_min"]:
                result["amplitude_ok"] = True
                
            # 检查成交量放大
            if latest_data['volume_change'] >= FILTER_PARAMS["volume_increase"]:
                result["volume_increase"] = True
                
            # 杯柄形态/三角形突破识别需要复杂的模式识别算法
            # 在这里简化为近期突破关键阻力位
            # 实际应用需要更复杂的技术分析
            result["pattern_breakout"] = (result["above_ma"] and 
                                         result["volume_increase"] and
                                         latest_data['close'] > latest_data['high'].shift(1).iloc[-1])
            
            return result
        except Exception as e:
            print(f"检查技术面条件出错: {e}")
            return result
                
    def filter_stocks(self, stock_list: pd.DataFrame) -> List[Dict[str, Any]]:
        """筛选股票"""
        selected_stocks = []
        
        total_stocks = len(stock_list)
        print(f"开始筛选 {total_stocks} 只股票...")
        
        # 处理列名，确保一致性
        price_col = None
        for col in stock_list.columns:
            if '最新价' in col or '现价' in col:
                price_col = col
                break
        
        if not price_col:
            print("无法找到价格列，请检查数据")
            return []
        
        # 对全部股票进行筛选
        count = 0
        for _, stock in stock_list.iterrows():
            count += 1
            if count % 50 == 0:
                print(f"已处理 {count}/{total_stocks} 只股票...")
            
            symbol = stock["股票代码"]
            name = stock["股票名称"]
            
            # 跳过ST股票和B股
            if "ST" in name or "st" in name or "B" in symbol or symbol.startswith('9'):
                continue
                
            # 获取历史数据
            history_data = self.get_stock_history(symbol)
            if history_data.empty:
                continue
                
            # 检查市值条件
            market_cap_ok = self.check_market_cap(symbol, stock)
            if not market_cap_ok:
                continue
                
            # 获取机构持股数据
            institution_count = self.get_top_holders(symbol)
            if institution_count < FILTER_PARAMS["institutional_min"]:
                continue
                
            # 获取财务增长数据
            growth_data = self.get_financial_growth(symbol)
            growth_ok = False
            if growth_data:
                revenue_growth_ok = (growth_data["revenue_growth"] is not None and 
                                    growth_data["revenue_growth"] >= FILTER_PARAMS["growth_rate_min"])
                profit_growth_ok = (growth_data["profit_growth"] is not None and 
                                   growth_data["profit_growth"] >= FILTER_PARAMS["growth_rate_min"])
                growth_ok = revenue_growth_ok or profit_growth_ok
            
            if not growth_ok:
                continue
                
            # 检查技术面条件
            tech_conditions = self.check_technical_conditions(history_data)
            tech_ok = (tech_conditions["above_ma"] and 
                      tech_conditions["ma_alignment"] and 
                      tech_conditions["amplitude_ok"])
            
            if not tech_ok:
                continue
                
            # 获取资金流向数据
            fund_flow = self.get_fund_flow(symbol)
            fund_flow_ok = (fund_flow["today_inflow"] is not None and 
                           fund_flow["today_inflow"] > FILTER_PARAMS["main_inflow_min"])
            
            # 获取北向资金数据
            north_data = self.get_north_bound_holding(symbol)
            north_ok = (north_data["ratio_change"] is not None and 
                       north_data["ratio_change"] >= FILTER_PARAMS["north_increase_min"])
            
            # 检查异常交易数据
            unusual_trading = self.get_unusual_trading(symbol)
            unusual_ok = unusual_trading["block_trade"] or unusual_trading["top_list"]
            
            # 计算综合得分
            score = 0
            if growth_ok: score += 2
            if institution_count >= FILTER_PARAMS["institutional_min"]: score += 2
            if market_cap_ok: score += 1
            if tech_conditions["above_ma"]: score += 1
            if tech_conditions["ma_alignment"]: score += 1
            if tech_conditions["amplitude_ok"]: score += 1
            if tech_conditions["volume_increase"]: score += 1
            if tech_conditions["pattern_breakout"]: score += 2
            if fund_flow_ok: score += 2
            if fund_flow["consecutive_inflow"]: score += 1
            if north_ok: score += 2
            if unusual_ok: score += 2
            
            # 筛选总得分达到10分以上的股票（满分16分）
            if score >= 10:
                # 如果满足所有条件，添加到选中列表
                stock_info = {
                    "股票代码": symbol,
                    "股票名称": name,
                    "最新价": stock[price_col],
                    "得分": score,
                    "基本面": {
                        "增长率": growth_data["revenue_growth"] if growth_data and growth_data["revenue_growth"] else 
                                growth_data["profit_growth"] if growth_data else None,
                        "机构持股数量": institution_count,
                    },
                    "技术面": {
                        "站上均线": tech_conditions["above_ma"],
                        "均线多头排列": tech_conditions["ma_alignment"],
                        "波动率达标": tech_conditions["amplitude_ok"],
                        "成交量放大": tech_conditions["volume_increase"],
                        "形态突破": tech_conditions["pattern_breakout"]
                    },
                    "资金面": {
                        "主力净流入": fund_flow["today_inflow"],
                        "连续净流入": fund_flow["consecutive_inflow"],
                        "北向资金增持": north_ok,
                        "大宗交易": unusual_trading["block_trade"],
                        "龙虎榜": unusual_trading["top_list"]
                    }
                }
                
                selected_stocks.append(stock_info)
                print(f"选中: {symbol} {name} (得分: {score})")
            
        return selected_stocks
        
    def save_results(self, selected_stocks: List[Dict[str, Any]]):
        """保存选股结果"""
        if not selected_stocks:
            print("没有符合条件的股票")
            return
            
        # 创建基础DataFrame
        basic_info = []
        for stock in selected_stocks:
            basic_info.append({
                "股票代码": stock["股票代码"],
                "股票名称": stock["股票名称"],
                "最新价": stock["最新价"],
                "得分": stock["得分"],
                "增长率": stock["基本面"]["增长率"] if stock["基本面"]["增长率"] else "N/A",
                "机构持股数量": stock["基本面"]["机构持股数量"],
                "主力净流入": stock["资金面"]["主力净流入"] if stock["资金面"]["主力净流入"] else "N/A",
                "大宗交易": "是" if stock["资金面"]["大宗交易"] else "否",
                "龙虎榜": "是" if stock["资金面"]["龙虎榜"] else "否",
                "均线排列": "多头排列" if stock["技术面"]["均线多头排列"] else "非多头排列",
                "成交量放大": "是" if stock["技术面"]["成交量放大"] else "否" 
            })
        
        result_df = pd.DataFrame(basic_info)
        
        # 生成文件名
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(OUTPUT_DIR, f"选股结果_{current_time}.csv")
        
        # 保存结果
        result_df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"选股结果已保存到: {filename}")
        
        # 同时保存为通用的文件名，供可视化程序使用
        standard_filename = os.path.join(OUTPUT_DIR, "latest_selected_stocks.csv")
        result_df.to_csv(standard_filename, index=False, encoding='utf-8-sig')
        print(f"最新选股结果已保存到: {standard_filename}")
        
        # 保存详细数据供高级分析使用
        detailed_filename = os.path.join(OUTPUT_DIR, f"选股详细结果_{current_time}.json")
        pd.DataFrame(selected_stocks).to_json(detailed_filename, orient='records', force_ascii=False)
        print(f"详细选股结果已保存到: {detailed_filename}")
        
    def run(self):
        """运行选股流程"""
        start_time = time.time()
        
        # 获取股票列表
        stock_list = self.get_a_stock_list()
        if stock_list.empty:
            print("获取股票列表失败，无法继续选股")
            return False
        
        # 筛选股票
        selected_stocks = self.filter_stocks(stock_list)
        
        # 保存结果
        self.save_results(selected_stocks)
        
        # 计算耗时
        elapsed_time = time.time() - start_time
        print(f"选股完成，共选出 {len(selected_stocks)} 只股票，耗时 {elapsed_time:.2f} 秒")
        
        # 保存结果到实例变量
        self.selected_stocks = selected_stocks
        
        return len(selected_stocks) > 0


def main():
    """主函数"""
    print("A股复合策略选股启动...")
    print("\n===== 选股条件 =====")
    print("【基本面】")
    print(f"• 高成长性：近2年营收/净利润同比增速 > {FILTER_PARAMS['growth_rate_min']}%")
    print(f"• 机构背书：机构持股数量 ≥ {FILTER_PARAMS['institutional_min']}家")
    print(f"• 市值优选：总市值{FILTER_PARAMS['min_market_cap']/100000000:.0f}-{FILTER_PARAMS['max_market_cap']/100000000:.0f}亿元")
    
    print("\n【技术面】")
    print(f"• 趋势通道：收盘价站上{FILTER_PARAMS['ma_days']}日均线且均线多头排列")
    print(f"• 成交量条件：突破日成交量放大{FILTER_PARAMS['volume_increase']}%以上")
    print(f"• 波动率要求：过去1个月振幅 ≥ {FILTER_PARAMS['amplitude_min']}%")
    
    print("\n【资金面】")
    print(f"• 主力资金：主力净流入额 > {FILTER_PARAMS['main_inflow_min']/10000:.0f}万元")
    print(f"• 北向资金：北向资金持股比例周增幅 ≥ {FILTER_PARAMS['north_increase_min']}%")
    print("• 异动信号：近期大宗交易溢价或龙虎榜机构买入")
    print("========================\n")
    
    # 创建选股器实例并运行
    selector = StockSelector()
    success = selector.run()
    
    if success:
        print("\n选股成功完成！")
    else:
        print("\n选股过程中遇到问题，请检查输出信息。")
    
    return success


if __name__ == "__main__":
    main() 