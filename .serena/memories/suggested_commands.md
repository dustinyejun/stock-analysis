# 常用开发命令

## 环境管理
```bash
# 激活虚拟环境 (macOS/Linux)
source venv/bin/activate

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 更新requirements.txt
pip freeze > requirements.txt
```

## 应用运行
```bash
# 测试基础框架
python -c "
import sys; sys.path.append('.')
from config import get_config
from src.utils import get_logger
config = get_config()
logger = get_logger('test')
logger.info('框架测试成功')
print(f'环境: {config.environment}')
"

# 启动Streamlit界面 (后续阶段)
streamlit run main.py

# 测试数据获取 (第二阶段已完成)
python -c "
import sys; sys.path.append('.')
from src.data_fetcher import StockDataFetcher
fetcher = StockDataFetcher()
print('=== 数据获取模块测试 ===')
# 获取股票列表
stocks = fetcher.get_stock_list()
print(f'股票列表: {len(stocks)}只')
# 获取单只股票数据
data = fetcher.get_stock_data('000001', period=30)
print(f'数据获取: {len(data) if data is not None else 0}条记录')
# 批量获取测试
batch_data = fetcher.batch_get_data(['000001', '000002'], period=10)
print(f'批量获取: {len(batch_data)}只股票')
print('✅ 数据获取模块功能正常')
"

# 测试数据质量验证
python -c "
import sys; sys.path.append('.')
from src.data_fetcher import StockDataFetcher
fetcher = StockDataFetcher()
data = fetcher.get_stock_data('000001', period=30)
if data is not None:
    validation = fetcher.validate_batch_data_integrity({'000001': data})
    quality_score = validation['000001']['data_quality_score']
    print(f'数据质量评分: {quality_score:.1f}/100')
"

# 测试智能重试机制
python -c "
import sys; sys.path.append('.')
from src.data_fetcher import StockDataFetcher
fetcher = StockDataFetcher()
data = fetcher.get_stock_data_with_smart_retry('000001', period=30)
print(f'智能重试获取: {len(data) if data is not None else 0}条记录')
"
```

## 开发和测试
```bash
# 运行单元测试
pytest tests/

# 运行特定测试文件
pytest tests/test_indicators.py

# 生成测试覆盖率报告
pytest --cov=src tests/

# 代码格式化 (如果使用black)
black src/

# 代码检查 (如果使用flake8)
flake8 src/
```

## Git操作
```bash
# 查看状态
git status

# 添加文件
git add .

# 提交更改
git commit -m "commit message"

# 查看提交历史
git log --oneline

# 查看差异
git diff
```

## 打包相关
```bash
# 生成spec文件
pyinstaller --onefile --windowed --name="股票选择器" main.py

# 使用spec文件打包
pyinstaller build.spec

# 使用auto-py-to-exe (图形界面)
auto-py-to-exe
```

## 系统命令 (macOS)
```bash
# 查看进程
ps aux | grep python

# 查看端口占用
lsof -i :8501

# 查看磁盘空间
df -h

# 查看内存使用
vm_stat

# 查找文件
find . -name "*.py" -type f

# 查看Python路径
which python
```

## 项目管理
```bash
# 查看项目结构
tree -I 'venv|__pycache__|*.pyc|.git'

# 统计代码行数
find . -name "*.py" -exec wc -l {} + | tail -n 1

# 查看日志文件
tail -f logs/stock_analysis_*.log

# 清理缓存文件
find . -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
```

## 环境变量
```bash
# 查看环境变量
cat .env

# 设置临时环境变量
export LOG_LEVEL=DEBUG

# 重置环境配置
cp .env.example .env
```

## 故障排查
```bash
# 检查Python路径
python -c "import sys; print(sys.path)"

# 检查包安装
pip list | grep pandas

# 验证模块导入
python -c "import pandas; import streamlit; print('依赖正常')"

# 查看错误日志
tail -n 50 logs/stock_analysis_*.log
```