"""
日志配置模块
"""
import os
import sys
from pathlib import Path
from loguru import logger
from config.settings import get_config

def setup_logging():
    """设置日志配置"""
    config = get_config()
    
    # 移除默认的控制台handler
    logger.remove()
    
    # 确保logs目录存在
    log_dir = Path(config.log.log_file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=config.log.log_level,
        format=config.log.log_format,
        colorize=True
    )
    
    # 添加文件输出
    logger.add(
        config.log.log_file_path,
        level=config.log.log_level,
        format=config.log.log_format,
        rotation=config.log.log_rotation,
        retention=config.log.log_retention,
        compression="zip",
        encoding="utf-8"
    )
    
    logger.info("日志系统初始化完成")

def get_logger(name: str = None):
    """
    获取logger实例
    
    Args:
        name: logger名称
        
    Returns:
        logger实例
    """
    if name:
        return logger.bind(module=name)
    return logger

# 在模块导入时自动设置日志
setup_logging()