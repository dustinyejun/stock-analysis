"""
装饰器工具
"""
import time
import functools
from typing import Any, Callable, Type, Union
from .logger import get_logger
from .exceptions import StockAnalysisException

logger = get_logger(__name__)

def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], tuple] = Exception
):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避因子
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"函数 {func.__name__} 在重试 {max_retries} 次后仍然失败: {str(e)}")
                        raise
                    
                    logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {str(e)}，{current_delay:.1f}秒后重试")
                    time.sleep(current_delay)
                    current_delay *= backoff
                    
            return None  # 不会执行到这里
        return wrapper
    return decorator

def log_execution(include_args: bool = False, include_result: bool = False):
    """
    日志记录装饰器
    
    Args:
        include_args: 是否记录函数参数
        include_result: 是否记录函数返回值
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            func_name = f"{func.__module__}.{func.__name__}"
            
            # 记录开始执行
            if include_args:
                logger.debug(f"开始执行 {func_name}, 参数: args={args}, kwargs={kwargs}")
            else:
                logger.debug(f"开始执行 {func_name}")
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                if include_result:
                    logger.debug(f"完成执行 {func_name}, 耗时: {execution_time:.3f}秒, 结果: {result}")
                else:
                    logger.debug(f"完成执行 {func_name}, 耗时: {execution_time:.3f}秒")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"执行 {func_name} 失败, 耗时: {execution_time:.3f}秒, 错误: {str(e)}")
                raise
                
        return wrapper
    return decorator

def handle_exceptions(
    default_return: Any = None,
    raise_on_error: bool = True,
    log_error: bool = True
):
    """
    异常处理装饰器
    
    Args:
        default_return: 异常时的默认返回值
        raise_on_error: 是否重新抛出异常
        log_error: 是否记录异常日志
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"函数 {func.__name__} 执行异常: {str(e)}")
                
                if raise_on_error:
                    raise
                else:
                    return default_return
                    
        return wrapper
    return decorator

def validate_data(validator_func: Callable = None):
    """
    数据验证装饰器
    
    Args:
        validator_func: 验证函数，接收函数参数并返回布尔值
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if validator_func:
                if not validator_func(*args, **kwargs):
                    raise StockAnalysisException(f"函数 {func.__name__} 参数验证失败")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator