#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
选股策略运行脚本
运行选股和可视化流程
"""

import os
import sys
import time
import argparse
from datetime import datetime

# 检查是否安装了所需的库
try:
    import akshare
    import pandas
    import numpy
    import matplotlib
except ImportError as e:
    print(f"错误: 缺少必要的库: {e}")
    print("请安装所需的库: pip install akshare pandas numpy matplotlib")
    sys.exit(1)


def run_stock_selector():
    """运行选股策略"""
    print("\n===============================")
    print("        开始运行选股策略        ")
    print("===============================\n")
    
    try:
        from stock_selector import main as selector_main
        selector_main()
        return True
    except Exception as e:
        print(f"选股策略运行失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def run_stock_visualizer():
    """运行选股结果可视化"""
    print("\n===============================")
    print("      开始可视化选股结果        ")
    print("===============================\n")
    
    try:
        from stock_visualizer import main as visualizer_main
        visualizer_main()
        return True
    except Exception as e:
        print(f"选股结果可视化失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='A股选股策略运行工具')
    parser.add_argument('--select-only', action='store_true', help='仅运行选股策略')
    parser.add_argument('--visualize-only', action='store_true', help='仅运行可视化')
    parser.add_argument('--no-visualize', action='store_true', help='不运行可视化')
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 记录开始时间
    start_time = time.time()
    
    # 显示运行信息
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目录: {os.path.abspath('.')}")
    
    # 根据参数运行相应的模块
    if args.select_only:
        # 仅运行选股
        run_stock_selector()
    elif args.visualize_only:
        # 仅运行可视化
        run_stock_visualizer()
    else:
        # 运行完整流程
        selector_success = run_stock_selector()
        
        # 如果选股成功且未禁用可视化，则运行可视化
        if selector_success and not args.no_visualize:
            run_stock_visualizer()
    
    # 计算运行时间
    run_time = time.time() - start_time
    print(f"\n运行完成，总耗时: {run_time:.2f} 秒")


if __name__ == "__main__":
    main() 