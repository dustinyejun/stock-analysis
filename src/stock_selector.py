"""
股票选择器模块 - 集成数据获取、技术指标计算和选股规则
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 临时导入处理
try:
    from src.data_fetcher import StockDataFetcher
    from src.indicators import TechnicalIndicators
    from src.selection_rules import RuleEngine, RuleRegistry, SelectionResult, RuleResult
    from src.rules import GoldenPitRule, TrendBreakoutRule
except ImportError:
    # 如果导入失败，创建占位符
    print("警告: 某些模块导入失败，使用测试模式")
    StockDataFetcher = None
    TechnicalIndicators = None


import time

class StockSelector:
    """
    股票选择器主类
    
    集成数据获取、技术指标计算和选股规则引擎，提供完整的选股功能
    """
    
    def __init__(self, data_fetcher=None, indicators_calculator=None, rule_engine=None):
        """
        初始化股票选择器
        
        Args:
            data_fetcher: 数据获取器实例
            indicators_calculator: 技术指标计算器实例
            rule_engine: 选股规则引擎实例
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.data_fetcher = data_fetcher or (StockDataFetcher() if StockDataFetcher else None)
        self.indicators_calculator = indicators_calculator or (TechnicalIndicators() if TechnicalIndicators else None)
        
        # 初始化规则引擎和注册默认规则
        if rule_engine is None:
            registry = RuleRegistry()
            self.rule_engine = RuleEngine(registry)
            self._register_default_rules()
        else:
            self.rule_engine = rule_engine
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'successful_scans': 0,
            'failed_scans': 0,
            'rules_applied': 0,
            'results_generated': 0
        }
    
    def _register_default_rules(self):
        """注册默认的选股规则"""
        try:
            # 注册黄金坑规则
            golden_pit = GoldenPitRule()
            self.rule_engine.add_rule(golden_pit)
            
            # 注册趋势突破规则
            trend_breakout = TrendBreakoutRule()
            self.rule_engine.add_rule(trend_breakout)
            
            self.logger.info("成功注册默认选股规则")
        except Exception as e:
            self.logger.error(f"注册默认规则失败: {str(e)}")
    
    def add_rule(self, rule):
        """
        添加自定义选股规则
        
        Args:
            rule: 选股规则实例
        """
        self.rule_engine.add_rule(rule)
    
    def scan_single_stock(self, symbol: str, period: int = 120, 
                         rule_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        扫描单只股票
        
        Args:
            symbol: 股票代码
            period: 数据周期（天数）
            rule_names: 要应用的规则名称列表
            
        Returns:
            扫描结果字典
        """
        try:
            self.stats['total_processed'] += 1
            
            # 获取股票数据
            if not self.data_fetcher:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'data_fetcher_not_available',
                    'results': [],
                    'composite_score': 0.0
                }
            
            stock_data = self.data_fetcher.get_stock_data(symbol, period=period)
            if stock_data is None or stock_data.empty:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'no_data_available',
                    'results': [],
                    'composite_score': 0.0
                }
            
            # 计算技术指标
            if not self.indicators_calculator:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'indicators_calculator_not_available',
                    'results': [],
                    'composite_score': 0.0
                }
            
            indicators_data = self.indicators_calculator.get_comprehensive_indicators(stock_data)
            
            # 应用选股规则
            results = self.rule_engine.apply_rules(symbol, stock_data, indicators_data, rule_names)
            
            # 计算综合评分
            composite_score, score_details = self.rule_engine.calculate_composite_score(results)
            
            self.stats['successful_scans'] += 1
            self.stats['rules_applied'] += len(results)
            self.stats['results_generated'] += len([r for r in results if r.result != RuleResult.ERROR])
            
            return {
                'symbol': symbol,
                'success': True,
                'results': results,
                'composite_score': composite_score,
                'score_details': score_details,
                'data_info': {
                    'data_length': len(stock_data),
                    'date_range': f"{stock_data.index[0].strftime('%Y-%m-%d')} to {stock_data.index[-1].strftime('%Y-%m-%d')}",
                    'indicators_count': len(indicators_data.columns)
                }
            }
            
        except Exception as e:
            self.stats['failed_scans'] += 1
            self.logger.error(f"扫描股票 {symbol} 失败: {str(e)}")
            return {
                'symbol': symbol,
                'success': False,
                'error': str(e),
                'results': [],
                'composite_score': 0.0
            }
    
    def scan_stocks(self, symbols: List[str], period: int = 120, 
                   rule_names: Optional[List[str]] = None,
                   max_workers: int = 5,
                   min_score: float = 60.0,
                   progress_callback: Optional[callable] = None) -> List[Dict[str, Any]]:
        """
        批量扫描股票
        
        Args:
            symbols: 股票代码列表
            period: 数据周期（天数）
            rule_names: 要应用的规则名称列表
            max_workers: 最大并发工作线程数
            min_score: 最低分数阈值
            progress_callback: 进度回调函数
            
        Returns:
            扫描结果列表，按综合评分降序排列
        """
        results = []
        processed_count = 0
        total_count = len(symbols)
        
        self.logger.info(f"开始批量扫描 {total_count} 只股票，使用 {max_workers} 个工作线程")
        start_time = time.time()
        
        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            future_to_symbol = {
                executor.submit(self.scan_single_stock, symbol, period, rule_names): symbol
                for symbol in symbols
            }
            
            # 收集结果
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                processed_count += 1
                
                try:
                    result = future.result()
                    if result['success'] and result['composite_score'] >= min_score:
                        results.append(result)
                        self.logger.debug(f"股票 {symbol} 通过筛选，评分: {result['composite_score']:.1f}")
                    elif result['success']:
                        self.logger.debug(f"股票 {symbol} 评分不足，评分: {result['composite_score']:.1f}")
                    else:
                        self.logger.warning(f"股票 {symbol} 扫描失败: {result.get('error', 'unknown_error')}")
                        
                except Exception as e:
                    self.logger.error(f"处理股票 {symbol} 时发生异常: {str(e)}")
                
                # 调用进度回调
                if progress_callback:
                    try:
                        progress_callback(processed_count, total_count, len(results))
                    except Exception as e:
                        self.logger.warning(f"进度回调执行失败: {str(e)}")
                
                # 定期输出进度
                if processed_count % 50 == 0 or processed_count == total_count:
                    elapsed_time = time.time() - start_time
                    avg_time = elapsed_time / processed_count
                    remaining_time = avg_time * (total_count - processed_count)
                    
                    self.logger.info(
                        f"进度: {processed_count}/{total_count} ({processed_count/total_count*100:.1f}%), "
                        f"符合条件: {len(results)}只, "
                        f"已用时: {elapsed_time:.1f}s, "
                        f"预计剩余: {remaining_time:.1f}s"
                    )
        
        # 按综合评分降序排列
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        total_time = time.time() - start_time
        self.logger.info(
            f"批量扫描完成！总用时: {total_time:.1f}s, "
            f"平均每只股票: {total_time/total_count:.2f}s, "
            f"找到 {len(results)} 只符合条件的股票"
        )
        
        return results

    def scan_stocks_advanced(self, symbols: List[str], period: int = 120,
                             rule_names: Optional[List[str]] = None,
                             max_workers: int = 5,
                             min_score: float = 60.0,
                             batch_size: int = 100,
                             save_results: bool = False,
                             result_file: str = None) -> Dict[str, Any]:
        """
        高级批量扫描功能，支持批处理、结果保存等
        
        Args:
            symbols: 股票代码列表
            period: 数据周期（天数）
            rule_names: 要应用的规则名称列表
            max_workers: 最大并发工作线程数
            min_score: 最低分数阈值
            batch_size: 批处理大小
            save_results: 是否保存结果
            result_file: 结果文件路径
            
        Returns:
            包含扫描结果和统计信息的字典
        """
        start_time = time.time()
        total_results = []
        batch_stats = []
        
        self.logger.info(f"开始高级批量扫描 {len(symbols)} 只股票，批处理大小: {batch_size}")
        
        # 分批处理
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i + batch_size]
            batch_start_time = time.time()
            
            self.logger.info(f"处理第 {i//batch_size + 1} 批，股票数量: {len(batch_symbols)}")
            
            # 批量扫描
            batch_results = self.scan_stocks(
                batch_symbols, period, rule_names, max_workers, min_score,
                progress_callback=lambda processed, total, found: 
                    self.logger.debug(f"批内进度: {processed}/{total}, 找到: {found}")
            )
            
            total_results.extend(batch_results)
            
            # 记录批次统计
            batch_time = time.time() - batch_start_time
            batch_stats.append({
                'batch_number': i//batch_size + 1,
                'symbols_count': len(batch_symbols),
                'results_count': len(batch_results),
                'processing_time': batch_time,
                'avg_time_per_stock': batch_time / len(batch_symbols)
            })
            
            self.logger.info(f"第 {i//batch_size + 1} 批完成，用时: {batch_time:.1f}s，找到 {len(batch_results)} 只股票")
        
        # 最终排序
        total_results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        # 生成综合统计
        total_time = time.time() - start_time
        comprehensive_stats = {
            'total_symbols': len(symbols),
            'qualified_stocks': len(total_results),
            'qualification_rate': len(total_results) / len(symbols) * 100,
            'total_processing_time': total_time,
            'avg_time_per_stock': total_time / len(symbols),
            'batches_processed': len(batch_stats),
            'batch_stats': batch_stats
        }
        
        # 保存结果到文件
        if save_results:
            result_data = {
                'scan_time': start_time,
                'parameters': {
                    'period': period,
                    'rule_names': rule_names,
                    'min_score': min_score,
                    'batch_size': batch_size
                },
                'statistics': comprehensive_stats,
                'results': total_results
            }
            
            if not result_file:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                result_file = f"scan_results_{timestamp}.json"
            
            try:
                import json
                import os
                
                # 确保results目录存在
                os.makedirs('results', exist_ok=True)
                result_path = os.path.join('results', result_file)
                
                with open(result_path, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2, default=str)
                
                self.logger.info(f"扫描结果已保存到: {result_path}")
                comprehensive_stats['result_file'] = result_path
                
            except Exception as e:
                self.logger.error(f"保存结果失败: {str(e)}")
        
        self.logger.info(
            f"高级扫描完成！总用时: {total_time:.1f}s，"
            f"找到 {len(total_results)} 只符合条件的股票，"
            f"合格率: {comprehensive_stats['qualification_rate']:.2f}%"
        )
        
        return {
            'results': total_results,
            'statistics': comprehensive_stats,
            'rule_descriptions': self.get_rule_descriptions(),
            'selector_statistics': self.get_statistics()
        }

    
    def format_results_summary(self, results: List[Dict[str, Any]], 
                               top_n: int = 20) -> Dict[str, Any]:
        """
        格式化扫描结果摘要
        
        Args:
            results: 扫描结果列表
            top_n: 显示前N只股票的详细信息
            
        Returns:
            格式化后的结果摘要
        """
        if not results:
            return {
                'summary': '未找到符合条件的股票',
                'total_count': 0,
                'top_stocks': [],
                'score_distribution': {},
                'rule_performance': {}
            }
        
        # 基本统计
        total_count = len(results)
        scores = [r['composite_score'] for r in results]
        avg_score = sum(scores) / len(scores)
        
        # 分数分布
        score_ranges = {
            '90-100': len([s for s in scores if 90 <= s <= 100]),
            '80-89': len([s for s in scores if 80 <= s < 90]),
            '70-79': len([s for s in scores if 70 <= s < 80]),
            '60-69': len([s for s in scores if 60 <= s < 70])
        }
        
        # 规则表现统计
        rule_stats = {}
        for result in results:
            for rule_result in result.get('results', []):
                rule_name = rule_result.rule_name
                if rule_name not in rule_stats:
                    rule_stats[rule_name] = {'pass': 0, 'fail': 0, 'partial': 0}
                
                if rule_result.result.name == 'PASS':
                    rule_stats[rule_name]['pass'] += 1
                elif rule_result.result.name == 'FAIL':
                    rule_stats[rule_name]['fail'] += 1
                elif rule_result.result.name == 'PARTIAL':
                    rule_stats[rule_name]['partial'] += 1
        
        # 前N只股票详情
        top_stocks = []
        for i, result in enumerate(results[:top_n]):
            stock_info = {
                'rank': i + 1,
                'symbol': result['symbol'],
                'composite_score': result['composite_score'],
                'rule_results': []
            }
            
            # 添加每个规则的结果
            for rule_result in result.get('results', []):
                stock_info['rule_results'].append({
                    'rule_name': rule_result.rule_name,
                    'result': rule_result.result.name,
                    'score': rule_result.score,
                    'confidence': rule_result.confidence,
                    'reason': rule_result.reason[:100] + '...' if len(rule_result.reason) > 100 else rule_result.reason
                })
            
            top_stocks.append(stock_info)
        
        return {
            'summary': f'找到 {total_count} 只符合条件的股票',
            'total_count': total_count,
            'average_score': round(avg_score, 2),
            'highest_score': max(scores),
            'lowest_score': min(scores),
            'score_distribution': score_ranges,
            'rule_performance': rule_stats,
            'top_stocks': top_stocks
        }
    
    def export_results_to_csv(self, results: List[Dict[str, Any]], 
                              filename: str = None) -> str:
        """
        导出结果到CSV文件
        
        Args:
            results: 扫描结果列表
            filename: 输出文件名
            
        Returns:
            导出文件路径
        """
        import csv
        import os
        from datetime import datetime
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stock_selection_results_{timestamp}.csv"
        
        # 确保results目录存在
        os.makedirs('results', exist_ok=True)
        filepath = os.path.join('results', filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                # 定义CSV列
                fieldnames = [
                    'rank', 'symbol', 'composite_score', 
                    'golden_pit_result', 'golden_pit_score', 'golden_pit_confidence',
                    'trend_breakout_result', 'trend_breakout_score', 'trend_breakout_confidence',
                    'data_length', 'date_range', 'indicators_count'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for rank, result in enumerate(results, 1):
                    row_data = {
                        'rank': rank,
                        'symbol': result['symbol'],
                        'composite_score': round(result['composite_score'], 2)
                    }
                    
                    # 添加数据信息
                    data_info = result.get('data_info', {})
                    row_data.update({
                        'data_length': data_info.get('data_length', ''),
                        'date_range': data_info.get('date_range', ''),
                        'indicators_count': data_info.get('indicators_count', '')
                    })
                    
                    # 添加规则结果
                    for rule_result in result.get('results', []):
                        rule_name = rule_result.rule_name.lower().replace(' ', '_')
                        row_data.update({
                            f'{rule_name}_result': rule_result.result.name,
                            f'{rule_name}_score': round(rule_result.score, 2),
                            f'{rule_name}_confidence': round(rule_result.confidence, 2)
                        })
                    
                    writer.writerow(row_data)
            
            self.logger.info(f"结果已导出到CSV文件: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"导出CSV文件失败: {str(e)}")
            return None

    
    def save_scan_history(self, scan_results: Dict[str, Any], 
                          metadata: Dict[str, Any] = None) -> str:
        """
        保存扫描历史记录
        
        Args:
            scan_results: 扫描结果数据
            metadata: 额外的元数据信息
            
        Returns:
            历史记录文件路径
        """
        import json
        import os
        from datetime import datetime
        
        timestamp = datetime.now()
        history_data = {
            'scan_id': timestamp.strftime("%Y%m%d_%H%M%S"),
            'timestamp': timestamp.isoformat(),
            'metadata': metadata or {},
            'results_summary': {
                'total_stocks_scanned': scan_results.get('statistics', {}).get('total_symbols', 0),
                'qualified_stocks': len(scan_results.get('results', [])),
                'processing_time': scan_results.get('statistics', {}).get('total_processing_time', 0),
                'qualification_rate': scan_results.get('statistics', {}).get('qualification_rate', 0)
            },
            'parameters': scan_results.get('statistics', {}).get('parameters', {}),
            'top_10_results': scan_results.get('results', [])[:10]  # 只保存前10个结果
        }
        
        # 确保history目录存在
        os.makedirs('history', exist_ok=True)
        
        # 保存详细历史记录
        history_file = f"scan_history_{history_data['scan_id']}.json"
        history_path = os.path.join('history', history_file)
        
        try:
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2, default=str)
            
            # 更新历史记录索引
            self._update_history_index(history_data)
            
            self.logger.info(f"扫描历史记录已保存: {history_path}")
            return history_path
            
        except Exception as e:
            self.logger.error(f"保存历史记录失败: {str(e)}")
            return None
    
    def _update_history_index(self, history_data: Dict[str, Any]):
        """更新历史记录索引"""
        import json
        import os
        
        index_path = os.path.join('history', 'scan_history_index.json')
        
        # 读取现有索引
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            except:
                index_data = {'scans': []}
        else:
            index_data = {'scans': []}
        
        # 添加新记录
        index_entry = {
            'scan_id': history_data['scan_id'],
            'timestamp': history_data['timestamp'],
            'total_stocks': history_data['results_summary']['total_stocks_scanned'],
            'qualified_stocks': history_data['results_summary']['qualified_stocks'],
            'qualification_rate': history_data['results_summary']['qualification_rate'],
            'processing_time': history_data['results_summary']['processing_time']
        }
        
        index_data['scans'].insert(0, index_entry)  # 最新的在前面
        
        # 只保留最近50次扫描记录
        if len(index_data['scans']) > 50:
            index_data['scans'] = index_data['scans'][:50]
        
        # 保存更新后的索引
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"更新历史索引失败: {str(e)}")
    
    def get_scan_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取扫描历史记录
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            历史记录列表
        """
        import json
        import os
        
        index_path = os.path.join('history', 'scan_history_index.json')
        
        if not os.path.exists(index_path):
            return []
        
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            return index_data.get('scans', [])[:limit]
            
        except Exception as e:
            self.logger.error(f"读取历史记录失败: {str(e)}")
            return []
    
    def scan_all_stocks(self, period: int = 120, 
                       rule_names: Optional[List[str]] = None,
                       max_workers: int = 5,
                       min_score: float = 60.0,
                       limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        扫描所有股票
        
        Args:
            period: 数据周期（天数）
            rule_names: 要应用的规则名称列表
            max_workers: 最大并发工作线程数
            min_score: 最低分数阈值
            limit: 最大处理股票数量限制
            
        Returns:
            扫描结果列表，按综合评分降序排列
        """
        if not self.data_fetcher:
            self.logger.error("数据获取器不可用")
            return []
        
        # 获取股票列表
        stock_list = self.data_fetcher.get_stock_list()
        if not stock_list:
            self.logger.error("无法获取股票列表")
            return []
        
        # 提取股票代码
        symbols = [stock['code'] for stock in stock_list]
        
        # 应用数量限制
        if limit and limit < len(symbols):
            symbols = symbols[:limit]
            self.logger.info(f"应用数量限制，只处理前 {limit} 只股票")
        
        return self.scan_stocks(symbols, period, rule_names, max_workers, min_score)
    
    def get_rule_descriptions(self) -> List[Dict[str, Any]]:
        """获取所有规则的描述信息"""
        descriptions = []
        
        for rule_name in self.rule_engine.registry.list_rules():
            rule = self.rule_engine.registry.get_rule(rule_name)
            if rule and hasattr(rule, 'get_rule_description'):
                descriptions.append(rule.get_rule_description())
            else:
                descriptions.append({
                    'name': rule_name,
                    'description': '规则描述不可用',
                    'conditions': [],
                    'parameters': {},
                    'thresholds': {}
                })
        
        return descriptions
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取选择器统计信息"""
        engine_stats = self.rule_engine.get_statistics()
        
        return {
            'selector_stats': self.stats,
            'rule_engine_stats': engine_stats,
            'performance': {
                'success_rate': self.stats['successful_scans'] / self.stats['total_processed'] if self.stats['total_processed'] > 0 else 0,
                'avg_rules_per_scan': self.stats['rules_applied'] / self.stats['total_processed'] if self.stats['total_processed'] > 0 else 0,
            }
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
            'total_processed': 0,
            'successful_scans': 0,
            'failed_scans': 0,
            'rules_applied': 0,
            'results_generated': 0
        }
        
        # 重置规则引擎统计
        for rule_name in self.rule_engine.registry.list_rules():
            rule = self.rule_engine.registry.get_rule(rule_name)
            if rule:
                rule.reset_statistics()
        
        self.rule_engine.clear_history()
        self.logger.info("统计信息已重置")


def create_test_stock_selector():
    """创建用于测试的股票选择器实例"""
    return StockSelector()


if __name__ == "__main__":
    # 测试代码
    print("🧪 股票选择器测试")
    
    try:
        # 创建选择器
        selector = StockSelector()
        print("✅ 股票选择器创建成功")
        
        # 获取规则描述
        rules = selector.get_rule_descriptions()
        print(f"✅ 获取规则描述成功: {len(rules)} 条规则")
        
        for rule in rules:
            print(f"  - {rule['name']}: {rule['description']}")
        
        # 获取统计信息
        stats = selector.get_statistics()
        print(f"✅ 统计信息获取成功: {stats['rule_engine_stats']['registry']['total_rules']} 条规则")
        
        # 测试单只股票扫描（使用模拟数据）
        if selector.data_fetcher and selector.indicators_calculator:
            print("🔄 测试单只股票扫描...")
            result = selector.scan_single_stock("000001", period=60)
            if result['success']:
                print(f"✅ 单只股票扫描成功: 综合评分 {result['composite_score']:.1f}")
            else:
                print(f"⚠️ 单只股票扫描失败: {result.get('error', 'unknown_error')}")
        else:
            print("⚠️ 数据获取或指标计算模块不可用，跳过扫描测试")
        
        print("🎉 股票选择器基础测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()