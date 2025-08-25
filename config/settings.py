"""
项目配置文件
"""
from pydantic import BaseModel
from typing import List, Optional
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

class DataConfig(BaseModel):
    """数据获取配置"""
    # 数据源选择
    primary_source: str = "akshare"
    backup_source: str = "yfinance" 
    
    # 数据获取参数
    max_retry_times: int = 3
    request_timeout: int = 30
    request_delay: float = 0.5  # 请求间隔，避免频率限制

class SelectionConfig(BaseModel):
    """选股配置"""
    # 默认展示数量选项
    display_options: List[int] = [10, 20, 50, 100, 200]
    default_display_count: int = 20
    
    # 黄金坑策略参数
    golden_pit_decline_threshold: float = -0.20  # 跌幅阈值
    golden_pit_volume_ratio: float = 1.5  # 量比阈值
    golden_pit_big_yang_threshold: float = 0.05  # 大阳线涨幅阈值
    golden_pit_lookback_days: int = 60  # 前期高点回望天数
    
    # 趋势突破策略参数
    trend_breakout_yang_threshold: float = 0.03  # 大阳线涨幅阈值
    trend_breakout_volume_ratio: float = 1.3  # 量比阈值
    trend_breakout_consecutive_days: int = 2  # 连续天数要求
    trend_breakout_lookback_days: int = 240  # 前期高点回望天数(8个月)

class UIConfig(BaseModel):
    """界面配置"""
    app_title: str = "A股选股系统"
    page_icon: str = "📈"
    layout: str = "wide"
    sidebar_state: str = "collapsed"

class LogConfig(BaseModel):
    """日志配置"""
    log_level: str = "INFO"
    log_file_path: str = str(PROJECT_ROOT / "logs" / "stock_analysis_{time}.log")
    log_rotation: str = "1 day"
    log_retention: str = "30 days"
    log_format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"

class AppConfig(BaseModel):
    """应用总配置"""
    data: DataConfig = DataConfig()
    selection: SelectionConfig = SelectionConfig()
    ui: UIConfig = UIConfig()
    log: LogConfig = LogConfig()
    
    # 环境配置
    environment: str = "development"  # development, production
    debug: bool = True

# 全局配置实例
config = AppConfig()

def get_config() -> AppConfig:
    """获取配置实例"""
    return config

def update_config_from_env():
    """从环境变量更新配置"""
    # 可以根据需要添加环境变量读取逻辑
    if os.getenv("ENVIRONMENT"):
        config.environment = os.getenv("ENVIRONMENT")
    
    if os.getenv("DEBUG"):
        config.debug = os.getenv("DEBUG").lower() == "true"
    
    if os.getenv("LOG_LEVEL"):
        config.log.log_level = os.getenv("LOG_LEVEL")

# 初始化时更新配置
update_config_from_env()