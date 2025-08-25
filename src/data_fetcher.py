"""
股票数据获取模块
"""
import akshare as ak
import pandas as pd
import yfinance as yf
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger
import time
import requests


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
        
    def get_stock_list(self) -> List[Dict]:
        """
        获取A股股票列表
        
        Returns:
            股票列表，包含代码、名称等信息
        """
        try:
            if self.data_source == "akshare":
                # 获取沪深A股列表
                stock_list = ak.stock_info_a_code_name()
                return stock_list.to_dict('records')
            else:
                # 备用数据源实现
                logger.warning("使用备用数据源获取股票列表")
                return []
                
        except Exception as e:
            logger.error(f"获取股票列表失败: {str(e)}")
            return []
    
    def get_stock_data(self, symbol: str, period: int = 365) -> Optional[pd.DataFrame]:
        """
        获取单只股票历史数据
        
        Args:
            symbol: 股票代码
            period: 数据天数
            
        Returns:
            包含OHLCV数据的DataFrame
        """
        for attempt in range(self.retry_times):
            try:
                if self.data_source == "akshare":
                    # 计算开始日期
                    end_date = datetime.now().strftime('%Y%m%d')
                    start_date = (datetime.now() - timedelta(days=period)).strftime('%Y%m%d')
                    
                    # 获取日K数据
                    data = ak.stock_zh_a_hist(
                        symbol=symbol,
                        period="daily", 
                        start_date=start_date,
                        end_date=end_date,
                        adjust=""
                    )
                    
                    if data.empty:
                        logger.warning(f"股票 {symbol} 数据为空")
                        return None
                        
                    # 标准化列名
                    data = data.rename(columns={
                        '日期': 'date',
                        '开盘': 'open',
                        '收盘': 'close', 
                        '最高': 'high',
                        '最低': 'low',
                        '成交量': 'volume',
                        '成交额': 'amount'
                    })
                    
                    # 设置日期索引
                    data['date'] = pd.to_datetime(data['date'])
                    data.set_index('date', inplace=True)
                    
                    # 确保数据类型正确
                    for col in ['open', 'close', 'high', 'low', 'volume', 'amount']:
                        if col in data.columns:
                            data[col] = pd.to_numeric(data[col], errors='coerce')
                    
                    logger.info(f"成功获取股票 {symbol} 数据，共 {len(data)} 条记录")
                    return data
                    
                else:
                    # yfinance备用实现
                    ticker = yf.Ticker(f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ")
                    data = ticker.history(period=f"{period}d")
                    
                    if data.empty:
                        return None
                        
                    # 标准化列名
                    data = data.rename(columns={
                        'Open': 'open',
                        'Close': 'close',
                        'High': 'high', 
                        'Low': 'low',
                        'Volume': 'volume'
                    })
                    
                    return data
                    
            except Exception as e:
                logger.warning(f"获取股票 {symbol} 数据失败 (尝试 {attempt + 1}/{self.retry_times}): {str(e)}")
                if attempt < self.retry_times - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    logger.error(f"股票 {symbol} 数据获取最终失败")
                    return None
                    
        return None
    
    def get_realtime_price(self, symbol: str) -> Optional[float]:
        """
        获取股票实时价格
        
        Args:
            symbol: 股票代码
            
        Returns:
            当前价格
        """
        try:
            if self.data_source == "akshare":
                # 获取实时行情
                data = ak.stock_zh_a_spot_em()
                stock_data = data[data['代码'] == symbol]
                
                if not stock_data.empty:
                    return float(stock_data['最新价'].iloc[0])
                    
            logger.warning(f"无法获取股票 {symbol} 实时价格")
            return None
            
        except Exception as e:
            logger.error(f"获取股票 {symbol} 实时价格失败: {str(e)}")
            return None
    
    def batch_get_data(self, symbols: List[str], period: int = 365) -> Dict[str, pd.DataFrame]:
        """
        批量获取股票数据
        
        Args:
            symbols: 股票代码列表
            period: 数据天数
            
        Returns:
            股票代码到数据的映射
        """
        results = {}
        total = len(symbols)
        
        logger.info(f"开始批量获取 {total} 只股票数据")
        
        for i, symbol in enumerate(symbols):
            logger.info(f"正在获取 {symbol} 数据 ({i+1}/{total})")
            
            data = self.get_stock_data(symbol, period)
            if data is not None:
                results[symbol] = data
            
            # 避免请求过于频繁
            time.sleep(0.1)
            
        logger.info(f"批量获取完成，成功获取 {len(results)} 只股票数据")
        return results
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        验证数据完整性
        
        Args:
            data: 股票数据
            
        Returns:
            数据是否有效
        """
        if data is None or data.empty:
            return False
            
        # 检查必要列
        required_columns = ['open', 'close', 'high', 'low', 'volume']
        for col in required_columns:
            if col not in data.columns:
                logger.error(f"缺少必要列: {col}")
                return False
                
        # 检查空值
        if data[required_columns].isnull().any().any():
            logger.warning("数据中存在空值")
            
        # 检查异常值
        if (data['high'] < data['low']).any():
            logger.error("数据中存在最高价小于最低价的异常")
            return False
            
        if (data['close'] > data['high']).any() or (data['close'] < data['low']).any():
            logger.error("数据中存在收盘价超出最高最低价范围的异常")
            return False
            
        return True


if __name__ == "__main__":
    # 测试代码
    fetcher = StockDataFetcher()
    
    # 测试获取股票列表
    stock_list = fetcher.get_stock_list()
    print(f"获取到 {len(stock_list)} 只股票")
    
    # 测试获取单只股票数据
    if stock_list:
        test_symbol = stock_list[0]['code']
        data = fetcher.get_stock_data(test_symbol, period=100)
        if data is not None:
            print(f"股票 {test_symbol} 数据预览:")
            print(data.head())
            print(f"数据验证结果: {fetcher.validate_data(data)}")