#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AKShare API 兼容性测试脚本
用于检查当前环境中可用的 AKShare API 函数
"""

import inspect
import time
import pandas as pd
from typing import List, Dict, Any, Optional
import traceback

# 导入 akshare 库
try:
    import akshare as ak
    print(f"成功导入 AKShare 库，版本: {ak.__version__}")
except ImportError:
    print("未安装 AKShare 库，请使用命令 pip install akshare 安装")
    exit(1)

# 测试的 API 函数列表
TEST_APIS = {
    "股票数据": {
        # 日线数据
        "stock_zh_a_hist": {"symbol": "000001", "period": "daily", "start_date": "20240301", "end_date": "20240310", "adjust": ""},
        
        # 财务数据
        "stock_financial_analysis_indicator": {"symbol": "000001"},
        
        # 股东数据 - 更新API - 修正市场标识和日期
        "stock_gdfx_free_top_10_em": {"symbol": "sz000001", "date": "20231231"},
        
        # 资金流向 - 更新API和参数
        "stock_individual_fund_flow_rank": {"indicator": "今日"},
        "stock_individual_fund_flow": {"symbol": "大盘"},
        
        # 北向资金 - 使用正确的API
        "stock_hsgt_fund_flow_summary_em": {},
        
        # 大宗交易 - 更新API和参数
        "stock_dzjy_mrtj": {"start_date": "20240301", "end_date": "20240310"},
        
        # 龙虎榜 - 更新参数
        "stock_lhb_detail_em": {"start_date": "20240301", "end_date": "20240310"}
    }
}

def test_api(api_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """测试单个 API 的可用性和参数兼容性"""
    result = {
        "api_name": api_name,
        "status": "失败",
        "error": None,
        "columns": None,
        "row_count": 0,
        "execution_time": 0
    }
    
    try:
        # 获取 API 函数
        if not hasattr(ak, api_name):
            result["error"] = f"AKShare 库中没有 {api_name} 函数"
            return result
        
        api_func = getattr(ak, api_name)
        
        # 获取函数签名
        sig = inspect.signature(api_func)
        valid_params = {}
        
        # 检查参数有效性
        for param_name, param_value in params.items():
            if param_name in sig.parameters:
                valid_params[param_name] = param_value
            else:
                print(f"警告: {api_name} 不接受参数 '{param_name}'，可用参数: {list(sig.parameters.keys())}")
        
        # 执行 API 调用并计时
        start_time = time.time()
        data = api_func(**valid_params)
        end_time = time.time()
        
        # 处理结果
        if isinstance(data, pd.DataFrame):
            result["status"] = "成功"
            result["columns"] = list(data.columns)
            result["row_count"] = len(data)
            result["execution_time"] = end_time - start_time
            if not data.empty:
                # 显示前3行数据的预览
                print(f"\n{api_name} 数据预览(前3行):")
                print(data.head(3))
        else:
            result["status"] = "成功但返回非DataFrame"
            result["execution_time"] = end_time - start_time
            
    except Exception as e:
        result["error"] = str(e)
        print(f"测试 {api_name} 时出错: {e}")
        print(traceback.format_exc())
        
    return result

def run_tests() -> Dict[str, List[Dict[str, Any]]]:
    """运行所有 API 测试"""
    results = {}
    
    for category, apis in TEST_APIS.items():
        print(f"\n\n=== 测试 {category} API ===\n")
        category_results = []
        
        for api_name, params in apis.items():
            print(f"\n测试 {api_name}...")
            result = test_api(api_name, params)
            category_results.append(result)
            
            status_emoji = "✅" if result["status"] == "成功" else "❌"
            print(f"{status_emoji} {api_name}: {result['status']}")
            if result["status"] == "成功" and isinstance(result["row_count"], int):
                print(f"  - 数据行数: {result['row_count']}")
                print(f"  - 列名: {result['columns']}")
            elif result["error"]:
                print(f"  - 错误: {result['error']}")
            
            print(f"  - 执行时间: {result['execution_time']:.2f} 秒")
            
            # 在测试之间暂停一下，避免请求过快
            time.sleep(1)
            
        results[category] = category_results
        
    return results

def generate_report(results: Dict[str, List[Dict[str, Any]]]) -> None:
    """生成测试报告"""
    print("\n\n============= AKShare API 兼容性测试报告 =============\n")
    
    success_count = 0
    fail_count = 0
    
    for category, category_results in results.items():
        print(f"\n## {category}")
        print("-" * 80)
        print(f"{'API名称':<30} | {'状态':<10} | {'数据行数':<10} | {'错误信息'}")
        print("-" * 80)
        
        for result in category_results:
            status = result["status"]
            if status == "成功":
                success_count += 1
                status_display = "✅ 成功"
            else:
                fail_count += 1
                status_display = "❌ 失败"
                
            error_msg = result["error"] if result["error"] else ""
            row_count = result["row_count"] if result["row_count"] else "-"
            
            print(f"{result['api_name']:<30} | {status_display:<10} | {row_count:<10} | {error_msg}")
    
    total = success_count + fail_count
    print("\n总结:")
    print(f"总测试 API 数量: {total}")
    print(f"成功: {success_count} ({success_count/total*100:.1f}%)")
    print(f"失败: {fail_count} ({fail_count/total*100:.1f}%)")
    
    print("\n推荐操作:")
    if fail_count > 0:
        print("1. 更新 AKShare 库: pip install --upgrade akshare")
        print("2. 查阅最新的 AKShare 文档以获取正确的 API 用法")
        print("3. 修改代码以使用成功测试的 API 替代失败的 API")
    else:
        print("所有 API 测试通过，当前环境兼容性良好")

if __name__ == "__main__":
    print("开始测试 AKShare API 兼容性...")
    test_results = run_tests()
    generate_report(test_results)
    print("\n测试完成。") 