"""
真实股票选择器 - 用于实际选股
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Callable
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入相关模块
try:
    from src.data_fetcher import StockDataFetcher
    from src.indicators import TechnicalIndicators
    from src.selection_rules import RuleEngine, RuleRegistry, SelectionResult, RuleResult
    from src.rules.golden_pit import GoldenPitRule
    from src.rules.trend_breakout import TrendBreakoutRule
except ImportError as e:
    print(f"导入模块失败: {e}")
    # 创建占位符类以避免错误
    class StockDataFetcher:
        def batch_get_data(self, *args, **kwargs):
            return {}
    
    class TechnicalIndicators:
        def calculate_all(self, *args, **kwargs):
            return pd.DataFrame()


class RealStockSelector:
    """真实股票选择器"""
    
    def __init__(self):
        """初始化选股器"""
        self.data_fetcher = StockDataFetcher()
        self.indicators = TechnicalIndicators()
        
        # 初始化规则引擎
        self.registry = RuleRegistry()
        self.golden_pit_rule = GoldenPitRule()
        self.trend_breakout_rule = TrendBreakoutRule()
        
        # 注册规则
        self.registry.register(self.golden_pit_rule)
        self.registry.register(self.trend_breakout_rule)
        
        self.engine = RuleEngine(self.registry)
    
    def scan_stocks_advanced(self, symbols: List[str], rule_names: List[str] = None,
                           min_score: float = 60.0, max_workers: int = 5,
                           save_results: bool = False, progress_callback: Callable = None,
                           max_results: int = 50) -> Dict[str, Any]:
        """
        高级股票扫描
        
        Args:
            symbols: 股票代码列表
            rule_names: 启用的规则名称列表
            min_score: 最低评分阈值
            max_workers: 最大并发数
            save_results: 是否保存结果
            progress_callback: 进度回调函数
            max_results: 最大返回结果数
            
        Returns:
            扫描结果字典
        """
        try:
            results = []
            total_symbols = len(symbols)
            processed = 0
            
            # 分批处理，避免内存过载
            batch_size = min(50, max_workers * 10)
            
            for i in range(0, total_symbols, batch_size):
                batch_symbols = symbols[i:i + batch_size]
                
                # 获取这批股票的数据
                print(f"正在获取第 {i//batch_size + 1} 批数据 ({len(batch_symbols)} 只股票)...")
                stock_data_dict = self.data_fetcher.batch_get_data(
                    symbols=batch_symbols,
                    max_workers=max_workers,
                    progress_callback=None  # 内部不使用回调
                )
                
                # 处理每只股票
                for symbol in batch_symbols:
                    processed += 1
                    
                    # 更新进度
                    if progress_callback:
                        progress_callback(processed, total_symbols, len(results))
                    
                    # 检查是否有数据
                    if symbol not in stock_data_dict:
                        continue
                        
                    stock_data = stock_data_dict[symbol]
                    if stock_data.empty:
                        continue
                    
                    # 计算技术指标
                    try:
                        indicators_df = self.indicators.get_comprehensive_indicators(stock_data)
                        if indicators_df.empty:
                            continue
                    except Exception as e:
                        print(f"计算 {symbol} 技术指标失败: {e}")
                        continue
                    
                    # 应用选股规则
                    try:
                        rule_results = []
                        composite_score = 0
                        valid_rule_count = 0
                        rule_specific_data = {}
                        
                        # 检查每个启用的规则
                        for rule_name in (rule_names or ['GoldenPit', 'TrendBreakout']):
                            if rule_name == 'GoldenPit':
                                result = self.golden_pit_rule.check_conditions(stock_data, indicators_df)
                            elif rule_name == 'TrendBreakout': 
                                result = self.trend_breakout_rule.check_conditions(stock_data, indicators_df)
                            else:
                                continue
                            
                            result.symbol = symbol
                            rule_results.append(result)
                            
                            if result.result in [RuleResult.PASS, RuleResult.PARTIAL]:
                                composite_score += result.score
                                valid_rule_count += 1
                                
                                # 提取规则特定数据
                                rule_specific_data[rule_name] = self._extract_rule_data(
                                    rule_name, stock_data, indicators_df, result
                                )
                        
                        # 计算综合评分
                        if valid_rule_count > 0:
                            composite_score = composite_score / valid_rule_count
                        
                        # 检查是否符合最低评分要求
                        if composite_score >= min_score:
                            # 获取股票名称
                            stock_name = self._get_stock_name(symbol)
                            
                            stock_result = {
                                'symbol': symbol,
                                'stock_name': stock_name,
                                'composite_score': composite_score,
                                'results': rule_results,
                                'rule_data': rule_specific_data,
                                'data_info': {
                                    'data_length': len(stock_data),
                                    'date_range': f"{stock_data.index.min().strftime('%Y-%m-%d')} to {stock_data.index.max().strftime('%Y-%m-%d')}",
                                    'indicators_count': len(indicators_df.columns)
                                },
                                'score_details': {r.rule_name: r.score for r in rule_results}
                            }
                            
                            results.append(stock_result)
                            
                    except Exception as e:
                        print(f"处理 {symbol} 规则时出错: {e}")
                        continue
                    
                    # 添加小延时避免过度消耗资源
                    time.sleep(0.01)
            
            # 按评分排序
            results.sort(key=lambda x: x['composite_score'], reverse=True)
            
            # 限制返回结果数量
            qualified_results = results[:max_results] if len(results) > max_results else results
            
            # 保存结果（如果需要）
            if save_results and qualified_results:
                self._save_scan_results(qualified_results)
            
            return {
                'results': qualified_results,
                'statistics': {
                    'total_symbols': total_symbols,
                    'qualified_stocks': len(results),
                    'returned_stocks': len(qualified_results),
                    'qualification_rate': len(results) / total_symbols * 100 if total_symbols > 0 else 0,
                    'total_processing_time': processed * 0.1  # 粗略估算
                }
            }
            
        except Exception as e:
            print(f"扫描过程中出现异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'results': [],
                'statistics': {
                    'total_symbols': len(symbols),
                    'qualified_stocks': 0,
                    'returned_stocks': 0,
                    'qualification_rate': 0,
                    'total_processing_time': 0
                }
            }
    
    def _extract_rule_data(self, rule_name: str, stock_data: pd.DataFrame, 
                          indicators_df: pd.DataFrame, result: Any) -> Dict[str, Any]:
        """提取规则特定的数据用于显示"""
        try:
            latest_data = stock_data.iloc[-1]
            latest_indicators = indicators_df.iloc[-1]
            
            if rule_name == 'GoldenPit':
                # 计算前期高点（60日最高价）
                high_60d = stock_data['high'].rolling(60).max().iloc[-1]
                current_price = latest_data['close']
                max_drawdown = (current_price - high_60d) / high_60d
                
                return {
                    'current_price': round(current_price, 2),
                    'trigger_date': stock_data.index[-1].strftime('%Y-%m-%d'),
                    'previous_high': round(high_60d, 2),
                    'max_drawdown': f"{max_drawdown*100:.1f}%",
                    'big_yang_gain': f"{((current_price - stock_data['close'].iloc[-2]) / stock_data['close'].iloc[-2] * 100):.1f}%",
                    'ma10': round(latest_indicators.get('ma10', current_price), 2)
                }
            
            elif rule_name == 'TrendBreakout':
                # 计算突破数据
                prev_high = stock_data['high'].rolling(20).max().iloc[-2]  # 前期高点
                current_price = latest_data['close']
                breakout_margin = (current_price - prev_high) / prev_high
                
                # 计算平均量比
                avg_volume_ratio = indicators_df.get('volume_ratio_5', pd.Series([1.5])).iloc[-5:].mean()
                
                return {
                    'current_price': round(current_price, 2),
                    'trigger_date': stock_data.index[-1].strftime('%Y-%m-%d'),
                    'previous_high': round(prev_high, 2),
                    'breakout_margin': f"{breakout_margin*100:+.1f}%",
                    'volume_days': "3天",  # 简化显示
                    'avg_volume_ratio': round(avg_volume_ratio, 2)
                }
            
        except Exception as e:
            print(f"提取 {rule_name} 规则数据时出错: {e}")
        
        # 返回默认值
        return {
            'current_price': 0.0,
            'trigger_date': '未知',
            'previous_high': 0.0,
            'max_drawdown': '0.0%',
            'big_yang_gain': '0.0%',
            'ma10': 0.0
        }
    
    def _get_stock_name(self, symbol: str) -> str:
        """获取股票名称"""
        try:
            # 使用数据获取器获取真实股票名称
            stock_info = self.data_fetcher.get_stock_info(symbol)
            if stock_info and stock_info.get('name'):
                name = stock_info['name']
                # 如果名称不是占位符格式，就使用它
                if name != f"股票{symbol}":
                    return name
        except Exception as e:
            print(f"获取股票 {symbol} 名称失败: {e}")
        
        # 如果获取失败或者是占位符，返回默认格式
        return f"股票{symbol}"
    
    def _save_scan_results(self, results: List[Dict]) -> None:
        """保存扫描结果"""
        try:
            import json
            import os
            from datetime import datetime
            
            # 确保results目录存在
            results_dir = "results"
            os.makedirs(results_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"scan_results_{timestamp}.json"
            filepath = os.path.join(results_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
                
            print(f"扫描结果已保存到: {filepath}")
            
        except Exception as e:
            print(f"保存扫描结果失败: {e}")


def create_stock_selector() -> RealStockSelector:
    """创建真实股票选择器实例"""
    return RealStockSelector()


if __name__ == "__main__":
    # 简单测试
    selector = RealStockSelector()
    test_symbols = ["000001", "000002"]
    
    print("开始测试真实选股器...")
    results = selector.scan_stocks_advanced(
        symbols=test_symbols,
        rule_names=['GoldenPit'],
        max_results=10
    )
    
    print(f"测试完成，找到 {len(results['results'])} 只符合条件的股票")
    for result in results['results']:
        print(f"- {result['symbol']}: {result['composite_score']:.1f}分")