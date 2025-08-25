"""
自定义异常类
"""

class StockAnalysisException(Exception):
    """股票分析异常基类"""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

class DataFetchException(StockAnalysisException):
    """数据获取异常"""
    
    def __init__(self, message: str, symbol: str = None, source: str = None):
        super().__init__(message, "DATA_FETCH_ERROR")
        self.symbol = symbol
        self.source = source

class DataValidationException(StockAnalysisException):
    """数据验证异常"""
    
    def __init__(self, message: str, symbol: str = None):
        super().__init__(message, "DATA_VALIDATION_ERROR")
        self.symbol = symbol

class CalculationException(StockAnalysisException):
    """计算异常"""
    
    def __init__(self, message: str, symbol: str = None, indicator: str = None):
        super().__init__(message, "CALCULATION_ERROR")
        self.symbol = symbol
        self.indicator = indicator

class ConfigException(StockAnalysisException):
    """配置异常"""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, "CONFIG_ERROR")
        self.config_key = config_key

class UIException(StockAnalysisException):
    """界面异常"""
    
    def __init__(self, message: str, component: str = None):
        super().__init__(message, "UI_ERROR")
        self.component = component