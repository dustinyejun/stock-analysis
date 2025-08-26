"""
技术指标计算模块
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
import logging
from functools import lru_cache
# from config import get_config
# from src.utils.exceptions import CalculationException

class CalculationException(Exception):
    """临时计算异常类"""
    def __init__(self, message: str, indicator: str = None):
        super().__init__(message)
        self.message = message
        self.indicator = indicator


class TechnicalIndicators:
    """技术指标计算器"""
    
    def __init__(self):
        """初始化技术指标计算器"""
        # self.config = get_config()()
        self.logger = logging.getLogger(__name__)
        
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
        try:
            if data.empty or window <= 0:
                raise CalculationException("无效的数据或窗口参数", indicator="moving_average")
            return data.rolling(window=window, min_periods=1).mean()
        except Exception as e:
            logging.getLogger(__name__).error(f"移动平均线计算失败: {str(e)}")
            raise CalculationException(f"移动平均线计算失败: {str(e)}", indicator="moving_average")
    
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
        try:
            if data.empty or window <= 0:
                raise CalculationException("无效的数据或窗口参数", indicator="exponential_moving_average")
            return data.ewm(span=window, adjust=False).mean()
        except Exception as e:
            logging.getLogger(__name__).error(f"指数移动平均线计算失败: {str(e)}")
            raise CalculationException(f"指数移动平均线计算失败: {str(e)}", indicator="exponential_moving_average")
    
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
        try:
            if volume.empty or window <= 0:
                raise CalculationException("无效的数据或窗口参数", indicator="volume_ratio")
            avg_volume = volume.rolling(window=window, min_periods=1).mean()
            return volume / avg_volume
        except Exception as e:
            logging.getLogger(__name__).error(f"量比计算失败: {str(e)}")
            raise CalculationException(f"量比计算失败: {str(e)}", indicator="volume_ratio")
    
    @staticmethod
    def price_change_rate(close: pd.Series) -> pd.Series:
        """
        计算涨跌幅
        
        Args:
            close: 收盘价序列
            
        Returns:
            涨跌幅序列
        """
        try:
            if close.empty:
                raise CalculationException("收盘价数据为空", indicator="price_change_rate")
            return close.pct_change()
        except Exception as e:
            logging.getLogger(__name__).error(f"涨跌幅计算失败: {str(e)}")
            raise CalculationException(f"涨跌幅计算失败: {str(e)}", indicator="price_change_rate")
    
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
        try:
            if data.empty or 'high' not in data.columns or window <= 0:
                raise CalculationException("无效的数据或窗口参数", indicator="find_high_points")
            return data['high'].rolling(window=window, min_periods=1).max()
        except Exception as e:
            logging.getLogger(__name__).error(f"前期高点识别失败: {str(e)}")
            raise CalculationException(f"前期高点识别失败: {str(e)}", indicator="find_high_points")
    
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
        try:
            if data.empty or 'low' not in data.columns or window <= 0:
                raise CalculationException("无效的数据或窗口参数", indicator="find_low_points")
            return data['low'].rolling(window=window, min_periods=1).min()
        except Exception as e:
            logging.getLogger(__name__).error(f"前期低点识别失败: {str(e)}")
            raise CalculationException(f"前期低点识别失败: {str(e)}", indicator="find_low_points")
    
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
        try:
            required_cols = ['close', 'volume']
            if data.empty or not all(col in data.columns for col in required_cols):
                raise CalculationException("数据缺少必要字段", indicator="detect_big_yang_line")
            
            # 计算当日涨跌幅
            daily_return = data['close'].pct_change()
            
            # 计算量比(相对于5日均量)
            volume_ratio = TechnicalIndicators.volume_ratio(data['volume'], 5)
            
            # 大阳线条件：涨幅>=min_return 且 量比>=min_volume_ratio
            big_yang = (daily_return >= min_return) & (volume_ratio >= min_volume_ratio)
            
            return big_yang
        except Exception as e:
            logging.getLogger(__name__).error(f"大阳线识别失败: {str(e)}")
            raise CalculationException(f"大阳线识别失败: {str(e)}", indicator="detect_big_yang_line")
    
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
        try:
            if data.empty or 'close' not in data.columns:
                raise CalculationException("数据缺少收盘价字段", indicator="detect_consecutive_yang_lines")
            
            daily_return = data['close'].pct_change()
            yang_line = daily_return >= min_return
            
            # 向量化计算连续阳线天数
            consecutive_count = pd.Series(0, index=data.index)
            count = 0
            
            for i in range(len(yang_line)):
                if yang_line.iloc[i]:
                    count += 1
                else:
                    count = 0
                consecutive_count.iloc[i] = count
            
            return consecutive_count >= min_days
        except Exception as e:
            logging.getLogger(__name__).error(f"连续阳线识别失败: {str(e)}")
            raise CalculationException(f"连续阳线识别失败: {str(e)}", indicator="detect_consecutive_yang_lines")
    
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
        try:
            if data.empty or 'volume' not in data.columns:
                raise CalculationException("数据缺少成交量字段", indicator="detect_volume_expansion")
            
            volume_ratio = TechnicalIndicators.volume_ratio(data['volume'], window)
            volume_expansion = volume_ratio >= min_ratio
            
            # 向量化计算连续放量天数
            consecutive_count = pd.Series(0, index=data.index)
            count = 0
            
            for i in range(len(volume_expansion)):
                if volume_expansion.iloc[i]:
                    count += 1
                else:
                    count = 0
                consecutive_count.iloc[i] = count
            
            return consecutive_count >= min_days
        except Exception as e:
            logging.getLogger(__name__).error(f"持续放量检测失败: {str(e)}")
            raise CalculationException(f"持续放量检测失败: {str(e)}", indicator="detect_volume_expansion")
    
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
        try:
            if data.empty or 'close' not in data.columns:
                raise CalculationException("数据缺少收盘价字段", indicator="check_bullish_trend")
            
            ma_short = TechnicalIndicators.moving_average(data['close'], short_window)
            ma_long = TechnicalIndicators.moving_average(data['close'], long_window)
            
            # 多头趋势条件：短期均线>长期均线 且 股价>短期均线
            bullish = (ma_short > ma_long) & (data['close'] > ma_short)
            
            return bullish
        except Exception as e:
            logging.getLogger(__name__).error(f"多头趋势判断失败: {str(e)}")
            raise CalculationException(f"多头趋势判断失败: {str(e)}", indicator="check_bullish_trend")
    
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
        try:
            if data.empty or 'close' not in data.columns:
                raise CalculationException("数据缺少收盘价字段", indicator="calculate_drawdown")
            
            # 计算前期高点
            rolling_high = TechnicalIndicators.find_high_points(data, high_window)
            
            # 计算回撤幅度
            drawdown = (data['close'] - rolling_high) / rolling_high
            
            # 计算最大回撤
            max_drawdown = drawdown.min()
            
            return drawdown, max_drawdown
        except Exception as e:
            logging.getLogger(__name__).error(f"回撤计算失败: {str(e)}")
            raise CalculationException(f"回撤计算失败: {str(e)}", indicator="calculate_drawdown")
    
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
        try:
            if data.empty or 'close' not in data.columns:
                raise CalculationException("数据缺少收盘价字段", indicator="calculate_volatility")
            
            daily_return = data['close'].pct_change()
            return daily_return.rolling(window=window, min_periods=1).std()
        except Exception as e:
            logging.getLogger(__name__).error(f"波动率计算失败: {str(e)}")
            raise CalculationException(f"波动率计算失败: {str(e)}", indicator="calculate_volatility")
    
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
        try:
            if data.empty or 'close' not in data.columns:
                raise CalculationException("数据缺少收盘价字段", indicator="calculate_rsi")
            
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        except Exception as e:
            logging.getLogger(__name__).error(f"RSI计算失败: {str(e)}")
            raise CalculationException(f"RSI计算失败: {str(e)}", indicator="calculate_rsi")
    
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
        try:
            if data.empty or 'close' not in data.columns:
                raise CalculationException("数据缺少收盘价字段", indicator="calculate_macd")
            
            ema_fast = TechnicalIndicators.exponential_moving_average(data['close'], fast)
            ema_slow = TechnicalIndicators.exponential_moving_average(data['close'], slow)
            
            dif = ema_fast - ema_slow
            dea = TechnicalIndicators.exponential_moving_average(dif, signal)
            macd = (dif - dea) * 2
            
            return dif, dea, macd
        except Exception as e:
            logging.getLogger(__name__).error(f"MACD计算失败: {str(e)}")
            raise CalculationException(f"MACD计算失败: {str(e)}", indicator="calculate_macd")
    
    def get_comprehensive_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
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
            result['ma5'] = self.moving_average(data['close'], 5)
            result['ma10'] = self.moving_average(data['close'], 10)
            result['ma20'] = self.moving_average(data['close'], 20)
            result['ma60'] = self.moving_average(data['close'], 60)
            
            # 成交量指标
            result['volume_ratio_5'] = self.volume_ratio(data['volume'], 5)
            result['volume_ratio_10'] = self.volume_ratio(data['volume'], 10)
            
            # 价格变化
            result['daily_return'] = self.price_change_rate(data['close'])
            
            # 前期高低点
            result['high_60'] = self.find_high_points(data, 60)
            result['high_240'] = self.find_high_points(data, 240)
            result['low_60'] = self.find_low_points(data, 60)
            
            # 回撤计算
            result['drawdown_60'], _ = self.calculate_drawdown(data, 60)
            
            # 趋势判断
            result['bullish_trend'] = self.check_bullish_trend(data)
            
            # 特殊形态识别
            result['big_yang'] = self.detect_big_yang_line(data)
            result['consecutive_yang'] = self.detect_consecutive_yang_lines(data)
            result['volume_expansion'] = self.detect_volume_expansion(data)
            
            # 技术指标
            result['rsi'] = self.calculate_rsi(data)
            dif, dea, macd = self.calculate_macd(data)
            result['dif'] = dif
            result['dea'] = dea
            result['macd'] = macd
            
            self.logger.info(f"成功计算综合技术指标，共 {len(result.columns)} 个指标")
            
        except Exception as e:
            self.logger.error(f"计算综合技术指标失败: {str(e)}")
            raise CalculationException(f"计算综合技术指标失败: {str(e)}", indicator="get_comprehensive_indicators")
            
        return result
    
    def validate_indicators(self, data: pd.DataFrame, indicators: pd.DataFrame) -> Dict[str, Any]:
        """
        验证技术指标计算结果
        
        Args:
            data: 原始数据
            indicators: 计算的指标数据
            
        Returns:
            验证结果字典
        """
        try:
            validation_results = {
                'data_integrity': True,
                'indicator_coverage': 0,
                'missing_values': {},
                'anomalies': [],
                'quality_score': 0
            }
            
            # 检查数据完整性
            if len(data) != len(indicators):
                validation_results['data_integrity'] = False
                validation_results['anomalies'].append("数据长度不匹配")
            
            # 检查指标覆盖度
            expected_indicators = ['ma5', 'ma10', 'ma20', 'volume_ratio_5', 'daily_return', 'rsi']
            present_indicators = [col for col in expected_indicators if col in indicators.columns]
            validation_results['indicator_coverage'] = len(present_indicators) / len(expected_indicators)
            
            # 检查缺失值
            for col in indicators.columns:
                if col not in data.columns:  # 只检查新计算的指标
                    missing_count = indicators[col].isna().sum()
                    if missing_count > 0:
                        validation_results['missing_values'][col] = missing_count
            
            # 计算质量评分
            quality_score = validation_results['indicator_coverage'] * 100
            if validation_results['data_integrity']:
                quality_score *= 1.0
            else:
                quality_score *= 0.5
            
            if len(validation_results['missing_values']) == 0:
                quality_score *= 1.0
            else:
                quality_score *= 0.8
            
            validation_results['quality_score'] = min(quality_score, 100)
            
            self.logger.info(f"指标验证完成，质量评分: {validation_results['quality_score']:.1f}")
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"指标验证失败: {str(e)}")
            return {
                'data_integrity': False,
                'indicator_coverage': 0,
                'missing_values': {},
                'anomalies': [f"验证异常: {str(e)}"],
                'quality_score': 0
            }


if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
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
                
                # 验证指标质量
                validation = indicators.validate_indicators(data, result)
                print(f"指标质量评分: {validation['quality_score']:.1f}/100")
                
                print("\n最新指标值:")
                latest_indicators = result.iloc[-1][['close', 'ma10', 'ma20', 'volume_ratio_5', 'daily_return', 'rsi']]
                for indicator, value in latest_indicators.items():
                    print(f"{indicator}: {value:.4f}")
                
                # 测试特殊形态识别
                big_yang_count = result['big_yang'].sum()
                consecutive_yang_count = result['consecutive_yang'].sum()
                volume_expansion_count = result['volume_expansion'].sum()
                
                print(f"\n形态识别统计:")
                print(f"大阳线天数: {big_yang_count}")
                print(f"连续阳线天数: {consecutive_yang_count}")
                print(f"持续放量天数: {volume_expansion_count}")
                
                print("✅ 技术指标计算模块测试完成")
            else:
                print("❌ 无法获取测试数据")
        else:
            print("❌ 无法获取股票列表")
            
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {str(e)}")
        import traceback
        traceback.print_exc()