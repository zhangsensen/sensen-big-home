# AKShare API 更新说明

本文档记录了 AKShare 库 API 的变更情况以及我们在代码中的适配方案。

## API 变更概述

AKShare 作为一个活跃维护的开源项目，其 API 接口可能会随版本更新而变化。主要变化包括：

1. **参数名称变更**：如 `stock` 参数改为 `symbol`
2. **函数名称变更**：如 `stock_shareholding_change` 改为 `stock_gdfx_free_top_10_em`
3. **返回数据结构变化**：列名和数据格式可能有所调整

## 具体 API 调整

### 1. 财务数据接口

| 旧版接口 | 新版接口 | 变更说明 |
|---------|---------|---------|
| `ak.stock_financial_analysis_indicator(stock="000001")` | `ak.stock_financial_analysis_indicator(symbol="000001")` | 参数名由 `stock` 变更为 `symbol` |

### 2. 十大流通股东接口

| 旧版接口 | 新版接口 | 变更说明 |
|---------|---------|---------|
| `ak.stock_shareholding_change(stock="000001")` | `ak.stock_gdfx_free_top_10_em(symbol="000001")` | 完全替换为新的函数，参数也从 `stock` 变为 `symbol` |

### 3. 资金流向接口

| 旧版接口 | 新版接口 | 变更说明 |
|---------|---------|---------|
| `ak.stock_individual_fund_flow(stock="000001")` | `ak.stock_individual_fund_flow_rank(symbol="000001")` | 更换为推荐的函数，参数也从 `stock` 变为 `symbol` |

### 4. 北向资金接口

| 旧版接口 | 新版接口 | 变更说明 |
|---------|---------|---------|
| `ak.stock_em_hsgt_north_net_flow_in_detail(symbol="000001")` | `ak.stock_hk_ggt_components_em(symbol="000001")` | 更换为更稳定的北向资金接口函数 |

### 5. 大宗交易接口

| 旧版接口 | 新版接口 | 变更说明 |
|---------|---------|---------|
| `ak.stock_dzjy_detail(symbol="000001")` | `ak.stock_dzjy_mrmx(symbol="000001")` | 更换为官方文档中推荐的函数 |

## 代码适配方案

为了应对 API 变化，我们采取了以下适配策略：

### 1. 动态列名识别

针对返回数据结构可能发生变化的情况，我们实现了自动识别关键列的功能：

```python
# 例如：识别主力资金净流入相关列
net_inflow_col = None
for col in recent_flow.columns:
    if '主力净流入' in col or '主力净额' in col:
        net_inflow_col = col
        break
```

### 2. 异常处理与兼容性

增加了更健壮的错误处理，以应对可能的 API 变化：

```python
try:
    # 处理可能的不同格式（百分比或小数）
    val_str = str(val).strip().replace('%', '')
    if val_str and not val_str.startswith('-') and float(val_str) > 0:
        return True
except ValueError:
    continue
```

### 3. 数据获取重试机制

添加自动重试机制以提高稳定性：

```python
def get_data_with_retry(self, data_func, data_name, max_retries=3, retry_delay=2):
    for attempt in range(max_retries):
        try:
            data = data_func()
            if data is not None and not data.empty:
                return data
            # ... 重试逻辑 ...
```

## 建议与最佳实践

1. **定期更新 AKShare**：使用 `pip install --upgrade akshare` 保持最新版本
2. **运行兼容性测试**：使用 `python akshare_api_test.py` 检查 API 兼容性
3. **查阅官方文档**：在使用前查看 [AKShare 官方文档](https://akshare.akfamily.xyz/) 获取最新 API 信息
4. **增加错误处理**：为每个 API 调用增加适当的错误处理和回退机制

## 更新日志

- **2025-03-11**：初始版本，基于 AKShare 最新文档更新所有 API 调用 