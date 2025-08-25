# A股选股系统技术设计文档

## 系统架构设计

### 总体架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据获取层     │    │   数据处理层     │    │   业务逻辑层     │
│  Data Source    │───▶│  Data Process   │───▶│ Business Logic  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   内存缓存层     │    │   计算引擎层     │    │  简单界面展示    │
│  Memory Cache   │    │ Compute Engine  │    │  Simple UI      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 技术栈选择
- **开发语言**: Python 3.9+
- **数据处理**: pandas, numpy
- **数据获取**: akshare, yfinance (备选)
- **前端界面**: Streamlit (简单页面展示)
- **配置管理**: pydantic
- **日志记录**: loguru

## 核心模块设计

### 1. 数据获取模块 (data_fetcher.py)
```python
class StockDataFetcher:
    """股票数据获取器"""
    
    def get_stock_list(self) -> List[str]:
        """获取A股股票列表"""
        
    def get_stock_data(self, symbol: str, period: int = 365) -> pd.DataFrame:
        """获取单只股票历史数据"""
        
    def get_realtime_price(self, symbol: str) -> float:
        """获取实时价格"""
        
    def batch_get_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """批量获取股票数据"""
```

### 2. 技术指标计算模块 (indicators.py)
```python
class TechnicalIndicators:
    """技术指标计算器"""
    
    @staticmethod
    def moving_average(data: pd.Series, window: int) -> pd.Series:
        """计算移动平均线"""
        
    @staticmethod
    def volume_ratio(volume: pd.Series, window: int) -> pd.Series:
        """计算量比"""
        
    @staticmethod
    def price_change_rate(close: pd.Series) -> pd.Series:
        """计算涨跌幅"""
        
    @staticmethod
    def find_high_points(data: pd.DataFrame, window: int) -> pd.Series:
        """寻找前期高点"""
```

### 3. 选股规则引擎 (selection_rules.py)
```python
class SelectionRule:
    """选股规则基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def apply(self, data: pd.DataFrame) -> bool:
        """应用规则，返回是否符合条件"""
        raise NotImplementedError

class GoldenPitRule(SelectionRule):
    """黄金坑规则"""
    
    def apply(self, data: pd.DataFrame) -> bool:
        """检查是否符合黄金坑条件"""

class TrendBreakoutRule(SelectionRule):
    """趋势突破规则"""
    
    def apply(self, data: pd.DataFrame) -> bool:
        """检查是否符合趋势突破条件"""
```

### 4. 选股引擎 (stock_selector.py)
```python
class StockSelector:
    """股票选择器"""
    
    def __init__(self, data_fetcher: StockDataFetcher):
        self.data_fetcher = data_fetcher
        self.rules = []
    
    def add_rule(self, rule: SelectionRule):
        """添加选股规则"""
        
    def scan_stocks(self) -> Dict[str, List[Dict]]:
        """扫描所有股票并应用规则"""
        
    def generate_report(self, results: Dict) -> str:
        """生成选股报告"""
```

## 数据处理设计

### 内存数据结构
系统使用纯内存处理，不持久化到数据库：

```python
# 股票数据结构
stock_data = {
    'symbol': str,      # 股票代码
    'name': str,        # 股票名称
    'data': pd.DataFrame,  # OHLCV数据
    'indicators': dict     # 计算的技术指标
}

# 选股结果结构
selection_result = {
    'symbol': str,
    'name': str,
    'current_price': float,
    'rule_name': str,
    'trigger_date': str,
    'indicators': dict,
    'reason': str
}
```

### 数据缓存策略
- **实时数据**: 程序运行期间保存在内存中
- **历史数据**: 按需获取，不做持久化
- **结果数据**: 直接展示，不保存历史记录

## 用户界面设计

### 简化界面架构
系统采用单页面Streamlit应用，提供最简洁的用户体验：

```python
# 主界面布局
st.title("A股选股系统")

# 参数设置区域
col1, col2 = st.columns(2)
with col1:
    max_results = st.selectbox("最大展示数量", [10, 20, 50, 100, 200])
with col2:
    st.empty()  # 预留扩展空间

# 操作按钮
if st.button("开始选股", type="primary", use_container_width=True):
    # 执行选股逻辑
    pass

# 结果展示区域
if results:
    st.subheader("筛选结果")
    
    # 按规则分组显示
    tabs = st.tabs(["黄金坑策略", "趋势突破策略"])
    
    with tabs[0]:
        st.dataframe(golden_pit_results)
    
    with tabs[1]:
        st.dataframe(trend_breakout_results)
```

### 界面功能特性
1. **极简设计**: 只有必要的控件和显示区域
2. **一键操作**: 用户只需点击"开始选股"按钮
3. **结果分组**: 按选股规则分别展示结果
4. **数量控制**: 通过下拉框限制展示股票数量
5. **实时反馈**: 显示筛选进度和状态信息

## 核心算法实现

### 规则一：黄金坑算法
```python
def check_golden_pit_condition(data: pd.DataFrame) -> Tuple[bool, Dict]:
    """
    检查黄金坑条件
    
    Args:
        data: 包含OHLCV的股票数据
        
    Returns:
        (是否符合条件, 详细指标)
    """
    # 1. 计算前期高点(60日内最高价)
    high_60d = data['high'].rolling(60).max()
    recent_high = high_60d.iloc[-60]
    
    # 2. 计算当前跌幅
    current_price = data['close'].iloc[-1]
    decline_rate = (current_price - recent_high) / recent_high
    
    if decline_rate > -0.20:  # 跌幅不足20%
        return False, {}
    
    # 3. 寻找大阳线
    daily_return = data['close'].pct_change()
    volume_ratio = data['volume'] / data['volume'].rolling(5).mean()
    
    # 最近5天内是否有大阳线
    recent_data = data.tail(5)
    big_yang_condition = (
        (recent_data['close'].pct_change() >= 0.05) & 
        (recent_data['volume'] / recent_data['volume'].rolling(5).mean() >= 1.5)
    )
    
    if not big_yang_condition.any():
        return False, {}
    
    # 4. 检查是否站上10日均线
    ma10 = data['close'].rolling(10).mean().iloc[-1]
    above_ma10 = current_price > ma10
    
    if not above_ma10:
        return False, {}
    
    # 返回符合条件及详细指标
    return True, {
        'recent_high': recent_high,
        'decline_rate': decline_rate,
        'current_price': current_price,
        'ma10': ma10,
        'big_yang_date': recent_data[big_yang_condition].index[-1] if big_yang_condition.any() else None
    }
```

### 规则二：趋势突破算法
```python
def check_trend_breakout_condition(data: pd.DataFrame) -> Tuple[bool, Dict]:
    """
    检查趋势突破条件
    
    Args:
        data: 包含OHLCV的股票数据
        
    Returns:
        (是否符合条件, 详细指标)
    """
    # 1. 判断多头趋势
    ma20 = data['close'].rolling(20).mean()
    ma60 = data['close'].rolling(60).mean()
    current_price = data['close'].iloc[-1]
    
    bullish_trend = (ma20.iloc[-1] > ma60.iloc[-1]) and (current_price > ma20.iloc[-1])
    
    if not bullish_trend:
        return False, {}
    
    # 2. 检查连续大阳线
    daily_return = data['close'].pct_change()
    recent_returns = daily_return.tail(5)
    
    consecutive_yang = 0
    for ret in recent_returns:
        if ret >= 0.03:
            consecutive_yang += 1
        else:
            consecutive_yang = 0
        if consecutive_yang >= 2:
            break
    
    if consecutive_yang < 2:
        return False, {}
    
    # 3. 检查持续放量
    volume_avg = data['volume'].rolling(10).mean()
    volume_ratio = data['volume'] / volume_avg
    
    consecutive_volume = 0
    for ratio in volume_ratio.tail(5):
        if ratio >= 1.3:
            consecutive_volume += 1
        else:
            consecutive_volume = 0
        if consecutive_volume >= 2:
            break
    
    if consecutive_volume < 2:
        return False, {}
    
    # 4. 检查突破8个月高点
    high_240d = data['high'].rolling(240).max().iloc[-1]
    breakthrough = current_price > high_240d
    
    if not breakthrough:
        return False, {}
    
    return True, {
        'ma20': ma20.iloc[-1],
        'ma60': ma60.iloc[-1],
        'current_price': current_price,
        'high_240d': high_240d,
        'consecutive_yang_days': consecutive_yang,
        'consecutive_volume_days': consecutive_volume,
        'breakthrough_rate': (current_price - high_240d) / high_240d
    }
```

## 性能优化策略

### 1. 数据缓存
- 使用Redis缓存实时数据
- 本地SQLite缓存历史数据
- 设置合理的缓存过期时间

### 2. 并发处理
- 使用多线程/多进程批量获取数据
- 异步处理股票筛选任务
- 数据库连接池管理

### 3. 增量更新
- 只更新当日新增数据
- 增量计算技术指标
- 差分备份策略

### 4. 算法优化
- 向量化计算替代循环
- 预计算常用指标
- 索引优化查询性能

## 错误处理与监控

### 异常处理策略
```python
class StockAnalysisException(Exception):
    """股票分析异常基类"""
    pass

class DataFetchException(StockAnalysisException):
    """数据获取异常"""
    pass

class CalculationException(StockAnalysisException):
    """计算异常"""
    pass

def with_retry(max_retries: int = 3):
    """重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == max_retries - 1:
                        raise
                    time.sleep(2 ** i)  # 指数退避
        return wrapper
    return decorator
```

### 日志记录
```python
from loguru import logger

# 配置日志
logger.add("logs/stock_analysis_{time}.log", rotation="1 day", retention="30 days")

# 记录关键操作
logger.info(f"开始获取股票数据: {symbol}")
logger.warning(f"数据获取失败，正在重试: {symbol}")
logger.error(f"股票 {symbol} 计算异常: {str(e)}")
```

## EXE打包配置

### 打包工具选择
- **主要工具**: PyInstaller 5.13.0+
- **辅助工具**: auto-py-to-exe 2.38.0+ (可视化界面)
- **打包模式**: 单文件模式 (--onefile)

### 打包脚本配置
```python
# build.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config/*', 'config/'),
        ('data/*', 'data/'),
        ('logs', 'logs/'),
    ],
    hiddenimports=[
        'akshare',
        'pandas',
        'numpy',
        'sqlalchemy',
        'streamlit',
        'fastapi',
        'pydantic',
        'loguru'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyd = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyd,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='股票选择器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设为False隐藏控制台窗口
    icon='assets/icon.ico',  # 应用图标
)
```

### 打包命令
```bash
# 生成spec文件
pyinstaller --onefile --windowed --name="股票选择器" main.py

# 使用spec文件打包
pyinstaller build.spec

# 使用auto-py-to-exe (图形界面)
auto-py-to-exe
```

### 打包优化策略
1. **依赖优化**: 移除不必要的包依赖
2. **文件压缩**: 使用UPX压缩可执行文件
3. **启动优化**: 延迟导入非关键模块
4. **资源嵌入**: 将配置文件和资源文件打包

### 打包注意事项
- 确保所有依赖包版本兼容
- 处理路径相关问题(使用相对路径)
- 测试打包后的exe文件功能完整性
- 处理杀毒软件误报问题

## 部署配置

### 环境要求
```yaml
# requirements.txt
pandas>=1.5.0
numpy>=1.24.0
akshare>=1.9.0
fastapi>=0.100.0
streamlit>=1.25.0
sqlalchemy>=2.0.0
psycopg2>=2.9.0
apscheduler>=3.10.0
pydantic>=2.0.0
loguru>=0.7.0
redis>=4.5.0
# 打包工具
pyinstaller>=5.13.0
auto-py-to-exe>=2.38.0
```

### Docker配置
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

### 环境变量配置
```env
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/stock_db
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
DATA_SOURCE=akshare
SCHEDULE_TIME=15:30
```

## 测试策略

### 单元测试
- 技术指标计算准确性
- 选股规则逻辑正确性
- 数据获取模块稳定性

### 集成测试
- 端到端选股流程
- 数据库操作正确性
- API接口功能完整性

### 回测验证
- 历史数据回测选股效果
- 不同参数组合测试
- 风险指标验证