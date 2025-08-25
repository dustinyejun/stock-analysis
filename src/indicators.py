"""
技术指标计算模块
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List
from loguru import logger


class TechnicalIndicators:
    """技术指标计算器"""
    
    @staticmethod
    def moving_average(data: pd.Series, window: int) -> pd.Series:
        """
        计算简单移动平均线
        
        Args:
            data: 价格序列
            window: 时间窗口
            
        Returns:
            移动平均线序列
        """
        return data.rolling(window=window, min_periods=1).mean()
    
    @staticmethod
    def exponential_moving_average(data: pd.Series, window: int) -> pd.Series:
        """
        计算指数移动平均线
        
        Args:
            data: 价格序列  
            window: 时间窗口
            
        Returns:
            指数移动平均线序列
        """
        return data.ewm(span=window, adjust=False).mean()
    
    @staticmethod
    def volume_ratio(volume: pd.Series, window: int) -> pd.Series:
        """
        计算量比
        
        Args:
            volume: 成交量序列
            window: 时间窗口
            
        Returns:
            量比序列
        """
        avg_volume = volume.rolling(window=window, min_periods=1).mean()
        return volume / avg_volume
    
    @staticmethod
    def price_change_rate(close: pd.Series) -> pd.Series:
        """
        计算涨跌幅
        
        Args:
            close: 收盘价序列
            
        Returns:
            涨跌幅序列
        """
        return close.pct_change()
    
    @staticmethod
    def find_high_points(data: pd.DataFrame, window: int) -> pd.Series:
        """
        寻找指定时间窗口内的最高点
        
        Args:
            data: 包含OHLC数据的DataFrame
            window: 时间窗口
            
        Returns:
            滚动最高价序列
        """
        return data['high'].rolling(window=window, min_periods=1).max()
    
    @staticmethod
    def find_low_points(data: pd.DataFrame, window: int) -> pd.Series:
        """
        寻找指定时间窗口内的最低点
        
        Args:
            data: 包含OHLC数据的DataFrame
            window: 时间窗口
            
        Returns:
            滚动最低价序列
        """
        return data['low'].rolling(window=window, min_periods=1).min()
    
    @staticmethod
    def detect_big_yang_line(data: pd.DataFrame, min_return: float = 0.05, 
                           min_volume_ratio: float = 1.5) -> pd.Series:
        """
        识别大阳线
        
        Args:
            data: 包含OHLCV数据的DataFrame
            min_return: 最小涨幅要求
            min_volume_ratio: 最小量比要求
            
        Returns:
            布尔序列，True表示大阳线
        """
        # 计算当日涨跌幅
        daily_return = data['close'].pct_change()
        
        # 计算量比(相对于5日均量)
        volume_ratio = TechnicalIndicators.volume_ratio(data['volume'], 5)
        
        # 大阳线条件：涨幅>=min_return 且 量比>=min_volume_ratio
        big_yang = (daily_return >= min_return) & (volume_ratio >= min_volume_ratio)
        
        return big_yang
    
    @staticmethod
    def detect_consecutive_yang_lines(data: pd.DataFrame, min_return: float = 0.03,
                                    min_days: int = 2) -> pd.Series:
        """
        识别连续阳线
        
        Args:
            data: 包含OHLCV数据的DataFrame
            min_return: 最小涨幅要求
            min_days: 最少连续天数
            
        Returns:
            布尔序列，True表示满足连续阳线条件
        """
        daily_return = data['close'].pct_change()
        yang_line = daily_return >= min_return
        
        # 计算连续阳线天数
        consecutive_count = pd.Series(0, index=data.index)
        count = 0
        
        for i in range(len(yang_line)):
            if yang_line.iloc[i]:
                count += 1
            else:
                count = 0
            consecutive_count.iloc[i] = count
        
        return consecutive_count >= min_days
    
    @staticmethod
    def detect_volume_expansion(data: pd.DataFrame, window: int = 10, 
                              min_ratio: float = 1.3, min_days: int = 2) -> pd.Series:
        """
        检测持续放量
        
        Args:
            data: 包含成交量数据的DataFrame
            window: 平均成交量计算窗口
            min_ratio: 最小量比要求
            min_days: 最少持续天数
            
        Returns:
            布尔序列，True表示满足持续放量条件
        """
        volume_ratio = TechnicalIndicators.volume_ratio(data['volume'], window)
        volume_expansion = volume_ratio >= min_ratio
        
        # 计算连续放量天数
        consecutive_count = pd.Series(0, index=data.index)
        count = 0
        
        for i in range(len(volume_expansion)):
            if volume_expansion.iloc[i]:
                count += 1
            else:
                count = 0
            consecutive_count.iloc[i] = count
        
        return consecutive_count >= min_days
    
    @staticmethod
    def check_bullish_trend(data: pd.DataFrame, short_window: int = 20, 
                          long_window: int = 60) -> pd.Series:
        """
        判断多头趋势
        
        Args:
            data: 包含收盘价数据的DataFrame
            short_window: 短期均线窗口
            long_window: 长期均线窗口
            
        Returns:
            布尔序列，True表示多头趋势
        """
        ma_short = TechnicalIndicators.moving_average(data['close'], short_window)
        ma_long = TechnicalIndicators.moving_average(data['close'], long_window)
        
        # 多头趋势条件：短期均线>长期均线 且 股价>短期均线
        bullish = (ma_short > ma_long) & (data['close'] > ma_short)
        
        return bullish
    
    @staticmethod
    def calculate_drawdown(data: pd.DataFrame, high_window: int) -> Tuple[pd.Series, float]:
        """
        计算回撤幅度
        
        Args:
            data: 包含价格数据的DataFrame
            high_window: 计算前期高点的窗口
            
        Returns:
            (回撤幅度序列, 最大回撤幅度)
        """
        # 计算前期高点
        rolling_high = TechnicalIndicators.find_high_points(data, high_window)
        
        # 计算回撤幅度
        drawdown = (data['close'] - rolling_high) / rolling_high
        
        # 计算最大回撤
        max_drawdown = drawdown.min()
        
        return drawdown, max_drawdown
    
    @staticmethod
    def calculate_volatility(data: pd.DataFrame, window: int = 20) -> pd.Series:
        """
        计算价格波动率
        
        Args:
            data: 包含收盘价数据的DataFrame
            window: 计算窗口
            
        Returns:
            波动率序列
        """
        daily_return = data['close'].pct_change()
        return daily_return.rolling(window=window, min_periods=1).std()
    
    @staticmethod
    def calculate_rsi(data: pd.DataFrame, window: int = 14) -> pd.Series:
        """
        计算相对强弱指标(RSI)
        
        Args:
            data: 包含收盘价数据的DataFrame
            window: 计算窗口
            
        Returns:
            RSI序列
        """
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, 
                      signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算MACD指标
        
        Args:
            data: 包含收盘价数据的DataFrame
            fast: 快线周期
            slow: 慢线周期  
            signal: 信号线周期
            
        Returns:
            (DIF, DEA, MACD柱)
        """
        ema_fast = TechnicalIndicators.exponential_moving_average(data['close'], fast)
        ema_slow = TechnicalIndicators.exponential_moving_average(data['close'], slow)
        
        dif = ema_fast - ema_slow
        dea = TechnicalIndicators.exponential_moving_average(dif, signal)
        macd = (dif - dea) * 2
        
        return dif, dea, macd
    
    @staticmethod
    def get_comprehensive_indicators(data: pd.DataFrame) -> pd.DataFrame:
        """
        计算综合技术指标
        
        Args:
            data: 包含OHLCV数据的DataFrame
            
        Returns:
            包含各种技术指标的DataFrame
        """
        result = data.copy()
        
        try:
            # 移动平均线
            result['ma5'] = TechnicalIndicators.moving_average(data['close'], 5)
            result['ma10'] = TechnicalIndicators.moving_average(data['close'], 10)
            result['ma20'] = TechnicalIndicators.moving_average(data['close'], 20)
            result['ma60'] = TechnicalIndicators.moving_average(data['close'], 60)
            
            # 成交量指标
            result['volume_ratio_5'] = TechnicalIndicators.volume_ratio(data['volume'], 5)
            result['volume_ratio_10'] = TechnicalIndicators.volume_ratio(data['volume'], 10)
            
            # 价格变化
            result['daily_return'] = TechnicalIndicators.price_change_rate(data['close'])
            
            # 前期高低点
            result['high_60'] = TechnicalIndicators.find_high_points(data, 60)
            result['high_240'] = TechnicalIndicators.find_high_points(data, 240)
            result['low_60'] = TechnicalIndicators.find_low_points(data, 60)
            
            # 回撤计算
            result['drawdown_60'], _ = TechnicalIndicators.calculate_drawdown(data, 60)
            
            # 趋势判断
            result['bullish_trend'] = TechnicalIndicators.check_bullish_trend(data)
            
            # 特殊形态识别
            result['big_yang'] = TechnicalIndicators.detect_big_yang_line(data)
            result['consecutive_yang'] = TechnicalIndicators.detect_consecutive_yang_lines(data)
            result['volume_expansion'] = TechnicalIndicators.detect_volume_expansion(data)
            
            # 技术指标
            result['rsi'] = TechnicalIndicators.calculate_rsi(data)
            dif, dea, macd = TechnicalIndicators.calculate_macd(data)
            result['dif'] = dif
            result['dea'] = dea
            result['macd'] = macd
            
            logger.info(f"成功计算综合技术指标，共 {len(result.columns)} 个指标")
            
        except Exception as e:
            logger.error(f"计算综合技术指标失败: {str(e)}")
            
        return result


if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from src.data_fetcher import StockDataFetcher
    
    # 获取测试数据
    fetcher = StockDataFetcher()
    stock_list = fetcher.get_stock_list()
    
    if stock_list:
        test_symbol = stock_list[0]['code']
        data = fetcher.get_stock_data(test_symbol, period=100)
        
        if data is not None:
            indicators = TechnicalIndicators()
            
            # 测试各种指标计算
            print(f"测试股票: {test_symbol}")
            print(f"数据范围: {data.index[0]} 到 {data.index[-1]}")
            
            # 计算综合指标
            result = indicators.get_comprehensive_indicators(data)
            print(f"计算完成，共 {len(result.columns)} 个字段")
            print("\n最新指标值:")
            print(result.iloc[-1][['close', 'ma10', 'ma20', 'volume_ratio_5', 'daily_return', 'rsi']])