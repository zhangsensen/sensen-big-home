"""
数据获取模块
支持多种数据源的股票数据获取
"""

from .akshare_fetcher import AKShareFetcher
from .base_fetcher import BaseFetcher

__all__ = ['AKShareFetcher', 'BaseFetcher'] 