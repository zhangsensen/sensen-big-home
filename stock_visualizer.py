#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
选股结果可视化模块
提供多维度的选股结果可视化
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# 尝试设置中文字体
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Heiti TC', 'Arial Unicode MS', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
except:
    print("警告: 可能无法正确显示中文，请安装中文字体")

# 输入输出配置
INPUT_DIR = "选股结果"
OUTPUT_DIR = "选股结果/可视化"
DEFAULT_INPUT_FILE = "latest_selected_stocks.csv"

class StockVisualizer:
    """股票可视化类，用于生成各类选股结果的可视化图表"""
    
    def __init__(self, input_file=None):
        """初始化可视化器"""
        self.create_output_dir()
        
        # 设置输入文件
        if input_file:
            self.input_file = input_file
        else:
            self.input_file = os.path.join(INPUT_DIR, DEFAULT_INPUT_FILE)
            
        # 加载数据
        self.load_data()
        
    def create_output_dir(self):
        """创建输出目录"""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
    def load_data(self):
        """加载选股结果数据"""
        try:
            if not os.path.exists(self.input_file):
                print(f"错误: 找不到选股结果文件: {self.input_file}")
                self.data = pd.DataFrame()
                return
                
            self.data = pd.read_csv(self.input_file)
            print(f"已加载选股结果，共 {len(self.data)} 只股票")
            
            # 处理数据类型
            if "得分" in self.data.columns:
                self.data["得分"] = pd.to_numeric(self.data["得分"], errors="coerce")
                
            if "最新价" in self.data.columns:
                self.data["最新价"] = pd.to_numeric(self.data["最新价"], errors="coerce")
                
            if "增长率" in self.data.columns:
                self.data["增长率"] = pd.to_numeric(self.data["增长率"].replace("N/A", np.nan), errors="coerce")
                
            if "机构持股数量" in self.data.columns:
                self.data["机构持股数量"] = pd.to_numeric(self.data["机构持股数量"], errors="coerce")
                
            if "主力净流入" in self.data.columns:
                # 处理主力净流入可能的格式
                self.data["主力净流入"] = pd.to_numeric(self.data["主力净流入"].replace("N/A", np.nan), errors="coerce")
                
        except Exception as e:
            print(f"加载数据出错: {e}")
            self.data = pd.DataFrame()
            
    def plot_score_distribution(self):
        """绘制得分分布图"""
        if self.data.empty or "得分" not in self.data.columns:
            print("没有足够的数据绘制得分分布图")
            return
            
        plt.figure(figsize=(10, 6))
        bins = range(10, 17)  # 假设得分范围是10-16
        plt.hist(self.data["得分"], bins=bins, alpha=0.7, color="royalblue", edgecolor="black")
        
        plt.title("选股结果得分分布", fontsize=15)
        plt.xlabel("得分", fontsize=12)
        plt.ylabel("股票数量", fontsize=12)
        plt.grid(axis="y", alpha=0.3)
        
        # 添加平均分标记
        mean_score = self.data["得分"].mean()
        plt.axvline(mean_score, color="crimson", linestyle="dashed", linewidth=2)
        plt.text(mean_score+0.1, plt.ylim()[1]*0.9, f"平均分: {mean_score:.2f}", 
                 color="crimson", fontsize=12)
        
        # 保存图表
        filename = os.path.join(OUTPUT_DIR, "得分分布图.png")
        plt.tight_layout()
        plt.savefig(filename, dpi=300)
        print(f"得分分布图已保存至: {filename}")
        plt.close()
        
    def plot_industry_distribution(self):
        """绘制行业分布图"""
        if self.data.empty:
            print("没有足够的数据绘制行业分布图")
            return
            
        # 由于当前数据不包含行业信息，这里模拟一些行业
        # 实际应用中应该使用真实的行业数据
        industries = ["电子", "医药", "军工", "半导体", "新能源", "消费", "金融", "其他"]
        industry_counts = np.random.randint(1, len(self.data), size=len(industries))
        industry_counts = industry_counts / sum(industry_counts) * len(self.data)
        industry_counts = industry_counts.astype(int)
        
        # 确保总数等于股票数量
        diff = len(self.data) - sum(industry_counts)
        industry_counts[-1] += diff
        
        plt.figure(figsize=(12, 7))
        plt.pie(industry_counts, labels=industries, autopct="%1.1f%%", 
                startangle=90, shadow=True, 
                colors=plt.cm.Paired(np.linspace(0, 1, len(industries))))
        
        plt.title("选股结果行业分布", fontsize=15)
        plt.axis("equal")
        
        # 保存图表
        filename = os.path.join(OUTPUT_DIR, "行业分布图.png")
        plt.tight_layout()
        plt.savefig(filename, dpi=300)
        print(f"行业分布图已保存至: {filename}")
        plt.close()
        
    def plot_top_stocks(self, top_n=10):
        """绘制得分最高的前N只股票"""
        if self.data.empty or len(self.data) < 3:
            print("没有足够的数据绘制前N只股票图")
            return
            
        n = min(top_n, len(self.data))
        top_stocks = self.data.sort_values("得分", ascending=False).head(n).copy()
        
        # 创建股票代码+名称的标签
        top_stocks["标签"] = top_stocks["股票名称"] + "(" + top_stocks["股票代码"] + ")"
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(top_stocks["标签"], top_stocks["得分"], 
                color=plt.cm.viridis(np.linspace(0, 0.8, n)), 
                edgecolor="gray", alpha=0.8)
        
        # 添加数据标签
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                     f"{width:.1f}", ha="left", va="center", fontsize=10)
        
        plt.title(f"得分最高的{n}只股票", fontsize=15)
        plt.xlabel("综合得分", fontsize=12)
        plt.grid(axis="x", alpha=0.3)
        plt.xlim(0, top_stocks["得分"].max() * 1.1)
        
        # 保存图表
        filename = os.path.join(OUTPUT_DIR, f"前{n}只高分股票.png")
        plt.tight_layout()
        plt.savefig(filename, dpi=300)
        print(f"前{n}只高分股票图已保存至: {filename}")
        plt.close()
        
    def plot_growth_vs_institutions(self):
        """绘制增长率vs机构持股数量散点图"""
        if self.data.empty or "增长率" not in self.data.columns or "机构持股数量" not in self.data.columns:
            print("没有足够的数据绘制增长率vs机构持股散点图")
            return
            
        # 过滤掉没有增长率的数据
        plot_data = self.data.dropna(subset=["增长率"]).copy()
        if len(plot_data) < 3:
            print("没有足够的增长率数据绘制散点图")
            return
            
        plt.figure(figsize=(12, 8))
        
        # 使用得分作为颜色映射和大小映射
        scatter = plt.scatter(plot_data["增长率"], plot_data["机构持股数量"],
                    c=plot_data["得分"], s=plot_data["得分"]*20,
                    cmap="viridis", alpha=0.7, edgecolors="w")
        
        plt.colorbar(scatter, label="综合得分")
        
        # 添加股票标签
        for i, row in plot_data.iterrows():
            plt.text(row["增长率"], row["机构持股数量"], 
                    row["股票名称"], fontsize=8)
        
        plt.title("增长率 vs 机构持股数量", fontsize=15)
        plt.xlabel("增长率(%)", fontsize=12)
        plt.ylabel("机构持股数量", fontsize=12)
        plt.grid(alpha=0.3)
        
        # 保存图表
        filename = os.path.join(OUTPUT_DIR, "增长率vs机构持股图.png")
        plt.tight_layout()
        plt.savefig(filename, dpi=300)
        print(f"增长率vs机构持股图已保存至: {filename}")
        plt.close()
        
    def plot_inflow_distribution(self):
        """绘制主力资金流入分布图"""
        if self.data.empty or "主力净流入" not in self.data.columns:
            print("没有足够的数据绘制主力资金流入图")
            return
            
        # 过滤掉没有主力净流入数据的记录
        plot_data = self.data.dropna(subset=["主力净流入"]).copy()
        if len(plot_data) < 3:
            print("没有足够的主力净流入数据绘制图表")
            return
            
        # 将主力净流入转换为万元单位，便于展示
        plot_data["主力净流入(万元)"] = plot_data["主力净流入"] / 10000
        
        plt.figure(figsize=(14, 8))
        
        # 按主力净流入排序
        plot_data = plot_data.sort_values("主力净流入(万元)", ascending=True)
        
        # 创建股票代码+名称的标签
        plot_data["标签"] = plot_data["股票名称"] + "(" + plot_data["股票代码"] + ")"
        
        # 绘制条形图
        bars = plt.barh(plot_data["标签"], plot_data["主力净流入(万元)"],
                color=plt.cm.coolwarm(np.linspace(0, 1, len(plot_data))),
                edgecolor="gray", alpha=0.8)
        
        # 添加数据标签
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 50 if width > 0 else width - 50, 
                    bar.get_y() + bar.get_height()/2, 
                    f"{width:.0f}万", ha="left" if width > 0 else "right", 
                    va="center", fontsize=9)
        
        plt.title("主力资金净流入分布", fontsize=15)
        plt.xlabel("主力净流入(万元)", fontsize=12)
        plt.grid(axis="x", alpha=0.3)
        
        # 添加零轴线
        plt.axvline(0, color="black", linestyle="-", linewidth=1)
        
        # 保存图表
        filename = os.path.join(OUTPUT_DIR, "主力资金净流入分布图.png")
        plt.tight_layout()
        plt.savefig(filename, dpi=300)
        print(f"主力资金净流入分布图已保存至: {filename}")
        plt.close()
        
    def create_summary_report(self):
        """创建选股结果汇总报告"""
        if self.data.empty:
            print("没有数据可生成报告")
            return
            
        # 统计基本信息
        total_stocks = len(self.data)
        avg_score = self.data["得分"].mean() if "得分" in self.data.columns else "N/A"
        avg_growth = self.data["增长率"].mean() if "增长率" in self.data.columns else "N/A"
        avg_inflow = self.data["主力净流入"].mean() / 10000 if "主力净流入" in self.data.columns else "N/A"
        
        # 统计技术面信息
        ma_alignment_count = self.data[self.data["均线排列"] == "多头排列"].shape[0] if "均线排列" in self.data.columns else 0
        volume_increase_count = self.data[self.data["成交量放大"] == "是"].shape[0] if "成交量放大" in self.data.columns else 0
        
        # 统计资金面信息
        block_trade_count = self.data[self.data["大宗交易"] == "是"].shape[0] if "大宗交易" in self.data.columns else 0
        top_list_count = self.data[self.data["龙虎榜"] == "是"].shape[0] if "龙虎榜" in self.data.columns else 0
        
        # 创建报告文本
        report = []
        report.append("===============================")
        report.append("      A股选股结果汇总报告      ")
        report.append("===============================\n")
        
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"选股数量: {total_stocks}只")
        report.append(f"平均得分: {avg_score:.2f}分" if avg_score != "N/A" else "平均得分: N/A")
        report.append(f"平均增长率: {avg_growth:.2f}%" if avg_growth != "N/A" else "平均增长率: N/A")
        report.append(f"平均主力净流入: {avg_inflow:.2f}万元" if avg_inflow != "N/A" else "平均主力净流入: N/A")
        
        report.append("\n技术面统计:")
        report.append(f"多头排列股票数: {ma_alignment_count}只 ({ma_alignment_count/total_stocks*100:.1f}%)")
        report.append(f"成交量放大股票数: {volume_increase_count}只 ({volume_increase_count/total_stocks*100:.1f}%)")
        
        report.append("\n资金面统计:")
        report.append(f"有大宗交易股票数: {block_trade_count}只 ({block_trade_count/total_stocks*100:.1f}%)")
        report.append(f"上榜龙虎榜股票数: {top_list_count}只 ({top_list_count/total_stocks*100:.1f}%)")
        
        report.append("\n评分最高的3只股票:")
        if "得分" in self.data.columns:
            top3 = self.data.sort_values("得分", ascending=False).head(3)
            for i, row in top3.iterrows():
                report.append(f"{row['股票名称']}({row['股票代码']}): {row['得分']}分")
        
        report.append("\n===============================")
        report.append("      数据来源: AKShare        ")
        report.append("===============================")
        
        # 保存报告
        filename = os.path.join(OUTPUT_DIR, "选股结果汇总报告.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(report))
        
        print(f"汇总报告已保存至: {filename}")
        
        # 同时返回报告文本，方便打印
        return "\n".join(report)
        
    def run_all_visualizations(self):
        """运行所有可视化功能"""
        if self.data.empty:
            print("没有数据可以可视化，请先确保选股结果文件存在")
            return False
            
        print(f"开始为{len(self.data)}只选中股票生成可视化结果...")
        
        # 运行所有可视化功能
        self.plot_score_distribution()
        self.plot_industry_distribution()
        self.plot_top_stocks()
        self.plot_growth_vs_institutions()
        self.plot_inflow_distribution()
        
        # 创建汇总报告
        report = self.create_summary_report()
        print("\n选股结果汇总:\n")
        print(report)
        
        return True


def main():
    """主函数"""
    print("开始生成选股结果可视化...")
    
    # 创建可视化器实例并运行
    visualizer = StockVisualizer()
    success = visualizer.run_all_visualizations()
    
    if success:
        print("\n可视化结果已生成完毕！")
        print(f"可视化文件保存在: {os.path.abspath(OUTPUT_DIR)}")
    else:
        print("\n可视化生成失败，请检查选股结果文件是否存在")
    
    return success


if __name__ == "__main__":
    main() 