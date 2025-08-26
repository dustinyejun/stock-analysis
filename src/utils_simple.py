"""
简化工具模块
"""
import logging
import sys
from typing import Any

def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

class DataFetchException(Exception):
    """数据获取异常"""
    pass

class DataValidationException(Exception):
    """数据验证异常"""
    pass

def with_retry(func):
    """重试装饰器"""
    def wrapper(*args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(1)
        return None
    return wrapper

def log_execution(func):
    """执行日志装饰器"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__name__)
        logger.info(f"开始执行 {func.__name__}")
        result = func(*args, **kwargs)
        logger.info(f"完成执行 {func.__name__}")
        return result
    return wrapper

def with_logging(func):
    """日志装饰器"""
    return log_execution(func)