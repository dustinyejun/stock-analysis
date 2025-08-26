"""
股票数据获取模块
"""
import akshare as ak
import pandas as pd
import yfinance as yf
import numpy as np
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class StockDataFetcher:
    """股票数据获取器"""
    
    def __init__(self, data_source: str = "akshare", retry_times: int = 3):
        """
        初始化数据获取器
        
        Args:
            data_source: 数据源选择 ("akshare", "yfinance")
            retry_times: 重试次数
        """
        self.data_source = data_source
        self.retry_times = retry_times
        self.request_timeout = 30
        self.request_delay = 1
        
        # 内存存储
        self.stock_cache = {}
        self.stock_list_cache = None
        
    def get_stock_list(self, use_cache: bool = True) -> List[Dict]:
        """
        获取A股股票列表
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            股票列表，包含代码、名称等信息
        """
        # 检查缓存
        if use_cache and self.stock_list_cache is not None:
            print(f"使用缓存的股票列表，共 {len(self.stock_list_cache)} 只股票")
            return self.stock_list_cache
        
        try:
            if self.data_source == "akshare":
                print("从akshare获取A股股票列表")
                # 获取沪深A股列表  
                stock_list = ak.stock_info_a_code_name()
                
                if stock_list.empty:
                    print("获取的股票列表为空")
                    return []
                
                # 数据清洗和标准化
                stock_list = self._clean_stock_list(stock_list)
                result = stock_list.to_dict('records')
                
                # 缓存结果
                self.stock_list_cache = result
                
                print(f"成功获取A股股票列表，共 {len(result)} 只股票")
                return result
                
            elif self.data_source == "yfinance":
                # 备用数据源实现
                print("yfinance不支持直接获取A股列表，返回空列表")
                return []
                
        except Exception as e:
            error_msg = f"获取股票列表失败 (数据源: {self.data_source}): {str(e)}"
            print(error_msg)
            return []
    
    def _clean_stock_list(self, stock_list: pd.DataFrame) -> pd.DataFrame:
        """
        清洗股票列表数据
        
        Args:
            stock_list: 原始股票列表DataFrame
            
        Returns:
            清洗后的股票列表DataFrame
        """
        try:
            # 标准化列名
            if 'code' in stock_list.columns and 'name' in stock_list.columns:
                stock_list.rename(columns={'code': 'symbol', 'name': 'stock_name'}, inplace=True)
            
            # 添加市场信息
            if 'symbol' in stock_list.columns:
                def get_market(symbol):
                    if str(symbol).startswith('6'):
                        return '上交所'
                    elif str(symbol).startswith(('0', '3')):
                        return '深交所'
                    else:
                        return '其他'
                
                stock_list['market'] = stock_list['symbol'].apply(get_market)
            
            # 去重和过滤
            stock_list = stock_list.drop_duplicates(subset=['symbol'])
            stock_list = stock_list.dropna(subset=['symbol'])
            
            return stock_list
            
        except Exception as e:
            print(f"清洗股票列表数据失败: {str(e)}")
            return stock_list

    def get_stock_data(self, symbol: str, period: int = 250) -> Optional[pd.DataFrame]:
        """
        获取单只股票的历史数据
        
        Args:
            symbol: 股票代码 (如 "000001")
            period: 获取天数，默认250天
            
        Returns:
            包含OHLCV数据的DataFrame，索引为日期
        """
        try:
            # 检查缓存
            cache_key = f"{symbol}_{period}"
            if cache_key in self.stock_cache:
                cached_data = self.stock_cache[cache_key]
                if self._is_cache_valid(cached_data):
                    return cached_data['data']
            
            if self.data_source == "akshare":
                data = self._get_data_from_akshare(symbol, period)
            elif self.data_source == "yfinance":
                data = self._get_data_from_yfinance(symbol, period)
            else:
                return None
                
            # 验证和标准化数据
            if data is not None and not data.empty:
                data = self._validate_and_standardize_data(data)
                # 缓存数据
                self.stock_cache[cache_key] = {
                    'data': data,
                    'timestamp': datetime.now()
                }
                
            return data
            
        except Exception as e:
            print(f"获取股票 {symbol} 数据失败: {str(e)}")
            return None
            
    def _get_data_from_akshare(self, symbol: str, period: int) -> Optional[pd.DataFrame]:
        """使用akshare获取数据，简化网络配置"""
        try:
            print(f"正在获取股票 {symbol} 的数据...")
            
            # 清除所有代理环境变量
            import os
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
            old_env = {}
            for var in proxy_vars:
                if var in os.environ:
                    old_env[var] = os.environ.pop(var)
            
            try:
                # 直接使用akshare，简单重试
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        print(f"股票 {symbol} - 尝试第 {attempt + 1} 次...")
                        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
                        
                        if not df.empty:
                            # 数据处理
                            df['日期'] = pd.to_datetime(df['日期'])
                            df.set_index('日期', inplace=True)
                            
                            # 标准化列名
                            df.rename(columns={
                                '开盘': 'open',
                                '收盘': 'close', 
                                '最高': 'high',
                                '最低': 'low',
                                '成交量': 'volume'
                            }, inplace=True)
                            
                            # 只取最近period天的数据
                            df = df.tail(period)
                            
                            # 检查数据的新鲜度，排除退市和长期停牌的股票
                            if not df.empty:
                                latest_date = df.index[-1]
                                days_ago = (pd.Timestamp.now() - latest_date).days
                                
                                if days_ago > 30:  # 最新数据超过30天
                                    print(f"股票 {symbol} 数据过期（最新数据：{latest_date.date()}，{days_ago}天前），可能已退市或停牌，跳过")
                                    return None
                            
                            print(f"股票 {symbol} 数据获取成功，记录数：{len(df)}")
                            return df
                        else:
                            print(f"股票 {symbol} 返回空数据")
                            return None
                            
                    except Exception as e:
                        print(f"股票 {symbol} 第 {attempt + 1} 次尝试失败: {str(e)}")
                        if attempt < max_retries - 1:
                            time.sleep(3)  # 等待3秒后重试
                        else:
                            print(f"股票 {symbol} 所有重试失败，跳过")
                            return None
            finally:
                # 恢复环境变量
                for var, value in old_env.items():
                    os.environ[var] = value
            
            return None
            
        except Exception as e:
            print(f"获取股票 {symbol} 数据异常: {str(e)}")
            return None
            
    def _get_data_from_yfinance(self, symbol: str, period: int) -> Optional[pd.DataFrame]:
        """使用yfinance获取数据"""
        try:
            # 转换股票代码格式
            if len(symbol) == 6:
                if symbol.startswith('6'):
                    ticker = f"{symbol}.SS"  # 上交所
                else:
                    ticker = f"{symbol}.SZ"  # 深交所
            else:
                ticker = symbol
            
            # 获取数据
            stock = yf.Ticker(ticker)
            df = stock.history(period=f"{period}d")
            
            if df.empty:
                return None
                
            # 标准化列名
            df.columns = df.columns.str.lower()
            
            return df
            
        except Exception as e:
            print(f"yfinance获取数据异常: {str(e)}")
            return None

    def _validate_and_standardize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """验证和标准化股票数据"""
        try:
            # 基本验证
            if data.empty:
                return data
            
            # 确保必要的列存在
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in data.columns:
                    print(f"警告: 缺少必要列 {col}")
                    return data
            
            # 数据类型转换
            for col in ['open', 'high', 'low', 'close']:
                data[col] = pd.to_numeric(data[col], errors='coerce')
            
            data['volume'] = pd.to_numeric(data['volume'], errors='coerce')
            
            # 移除无效数据
            data = data.dropna()
            
            # 检查数据合理性
            data = data[
                (data['high'] >= data['low']) &
                (data['high'] >= data['open']) &
                (data['high'] >= data['close']) &
                (data['low'] <= data['open']) &
                (data['low'] <= data['close']) &
                (data['volume'] >= 0)
            ]
            
            return data
            
        except Exception as e:
            print(f"验证数据失败: {str(e)}")
            return data

    def batch_get_data(self, symbols: List[str], max_workers: int = 5, 
                  progress_callback: Optional[Callable] = None) -> Dict[str, pd.DataFrame]:
        """
        批量获取股票数据 - 使用并行处理提高效率
        
        Args:
            symbols: 股票代码列表
            max_workers: 最大并发线程数
            progress_callback: 进度回调函数
            
        Returns:
            字典，键为股票代码，值为数据DataFrame
        """
        results = {}
        print(f"开始并行获取 {len(symbols)} 只股票数据，最大并发数: {max_workers}")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_symbol = {
                executor.submit(self.get_stock_data, symbol): symbol 
                for symbol in symbols
            }
            
            print(f"已提交 {len(future_to_symbol)} 个任务到线程池")
            
            # 处理完成的任务
            completed = 0
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                completed += 1
                
                print(f"处理第 {completed}/{len(symbols)} 只股票: {symbol}")
                
                try:
                    data = future.result()
                    if data is not None and not data.empty:
                        results[symbol] = data
                        print(f"✅ {symbol} 数据获取成功，记录数: {len(data)}")
                    else:
                        print(f"❌ {symbol} 数据为空")
                except Exception as e:
                    print(f"❌ 获取 {symbol} 数据时出错: {str(e)}")
                
                # 调用进度回调
                if progress_callback:
                    progress_callback(completed, len(symbols), len(results))
                
                # 适当延时，避免过快请求
                time.sleep(0.1)
        
        print(f"并行获取完成，成功获取 {len(results)}/{len(symbols)} 只股票数据")
        return results

    def _is_cache_valid(self, cached_item: Dict, max_age_hours: int = 24) -> bool:
        """检查缓存是否有效"""
        try:
            if 'timestamp' not in cached_item:
                return False
                
            age = datetime.now() - cached_item['timestamp']
            return age.total_seconds() < max_age_hours * 3600
            
        except Exception:
            return False

    def get_realtime_price(self, symbol: str) -> Optional[float]:
        """
        获取实时股价
        
        Args:
            symbol: 股票代码
            
        Returns:
            实时价格，失败返回None
        """
        try:
            if self.data_source == "akshare":
                # 使用akshare获取实时价格
                df = ak.stock_zh_a_spot_em()
                if not df.empty:
                    stock_info = df[df['代码'] == symbol]
                    if not stock_info.empty:
                        return float(stock_info['最新价'].iloc[0])
            
            # 如果akshare失败，尝试获取历史数据的最新价格
            recent_data = self.get_stock_data(symbol, period=1)
            if recent_data is not None and not recent_data.empty:
                return recent_data['close'].iloc[-1]
                
            return None
            
        except Exception as e:
            print(f"获取 {symbol} 实时价格失败: {str(e)}")
            return None

    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票信息字典
        """
        try:
            # 从股票列表中查找
            stock_list = self.get_stock_list()
            for stock in stock_list:
                if stock.get('symbol') == symbol:
                    return {
                        'symbol': symbol,
                        'name': stock.get('stock_name', f'股票{symbol}'),
                        'market': stock.get('market', '未知')
                    }
            
            # 如果没找到，返回默认信息
            return {
                'symbol': symbol,
                'name': f'股票{symbol}',
                'market': '未知'
            }
            
        except Exception as e:
            print(f"获取股票 {symbol} 信息失败: {str(e)}")
            return None

    def clear_cache(self):
        """清除所有缓存"""
        self.stock_cache.clear()
        self.stock_list_cache = None
        print("缓存已清除")

    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        return {
            'stock_data_count': len(self.stock_cache),
            'stock_list_cached': self.stock_list_cache is not None
        }


def create_data_fetcher() -> StockDataFetcher:
    """
    创建数据获取器实例
    
    Returns:
        配置好的StockDataFetcher实例
    """
    return StockDataFetcher()


if __name__ == "__main__":
    print("=" * 50)
    print("数据获取模块测试")
    print("=" * 50)
    
    try:
        # 初始化数据获取器
        fetcher = StockDataFetcher()
        
        # 测试1: 获取股票列表
        print("\n1. 测试获取股票列表...")
        stock_list = fetcher.get_stock_list()
        if stock_list and len(stock_list) > 0:
            print(f"✅ 成功获取 {len(stock_list)} 只股票")
            print("前5只股票信息:")
            for i, stock in enumerate(stock_list[:5], 1):
                symbol = stock.get('symbol', '未知')
                name = stock.get('stock_name', stock.get('name', '未知'))
                market = stock.get('market', '未知')
                print(f"  {i}. {symbol} - {name} ({market})")
        else:
            print("❌ 获取股票列表失败")
        
        # 测试2: 获取股票数据
        print("\n2. 测试获取股票数据 (000001)...")
        stock_data = fetcher.get_stock_data("000001")
        if stock_data is not None and not stock_data.empty:
            print(f"✅ 成功获取股票 000001 数据，共 {len(stock_data)} 条记录")
            print(f"数据时间范围: {stock_data.index.min()} 到 {stock_data.index.max()}")
            print(f"最新收盘价: {stock_data['close'].iloc[-1]}")
            print("数据概览:")
            print(stock_data.tail(3))
        else:
            print("❌ 获取股票数据失败")
        
        # 测试3: 批量获取数据
        test_symbols = ["000001", "000002", "000004"]
        print(f"\n3. 测试批量获取数据 ({len(test_symbols)} 只股票)...")
        
        def progress_callback(current, total):
            progress = (current / total) * 100
            print(f"进度: {current}/{total} ({progress:.1f}%)")
        
        batch_results = fetcher.batch_get_data(
            symbols=test_symbols,
            progress_callback=progress_callback,
            max_workers=2
        )
        print(f"✅ 批量获取完成，成功获取 {len(batch_results)} 只股票数据")
        
        # 测试4: 缓存功能验证
        print("\n4. 测试缓存功能...")
        cache_info = fetcher.get_cache_info()
        print(f"✅ 缓存状态: 股票数据 {cache_info['stock_data_count']} 条, "
              f"股票列表已缓存: {cache_info['stock_list_cached']}")
        
        # 测试5: 股票信息获取
        print("\n5. 测试股票信息获取...")
        stock_info = fetcher.get_stock_info("000001")
        if stock_info:
            print(f"✅ 股票信息: {stock_info['symbol']} - {stock_info['name']} ({stock_info['market']})")
        else:
            print("❌ 获取股票信息失败")
        
        print("\n" + "=" * 50)
        print("✅ 数据获取模块测试完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()