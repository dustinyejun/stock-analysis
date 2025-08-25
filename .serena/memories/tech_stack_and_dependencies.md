# 技术栈和依赖

## 核心技术栈
- **Python**: 3.9+
- **数据处理**: pandas (>=1.5.0), numpy (>=1.24.0)
- **数据源**: akshare (>=1.9.0), yfinance (>=0.2.0)
- **前端界面**: Streamlit (>=1.25.0)
- **数据模型**: Pydantic (>=2.0.0)
- **日志**: loguru (>=0.7.0)

## 开发和测试工具
- **HTTP客户端**: requests (>=2.31.0)
- **环境变量**: python-dotenv (>=1.0.0)
- **测试框架**: pytest (>=7.4.0)

## 打包工具
- **主要打包工具**: pyinstaller (>=5.13.0)
- **图形化打包界面**: auto-py-to-exe (>=2.38.0)

## 系统要求
- **操作系统**: macOS (Darwin), Linux, Windows
- **Python版本**: 3.9或更高
- **内存**: 推荐4GB以上 (简化架构后降低要求)
- **存储**: 至少1GB可用空间

## 简化说明
项目已移除以下复杂依赖：
- ~~FastAPI~~ (不需要API服务)
- ~~SQLAlchemy + PostgreSQL~~ (不使用数据库)
- ~~Redis~~ (不需要缓存服务)
- ~~APScheduler~~ (不需要定时任务)
- ~~uvicorn + jinja2~~ (不需要Web服务器)

## 安装命令
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt
```

## EXE打包相关
最终产品需要打包成独立的EXE可执行文件，使用PyInstaller进行打包：
- 目标文件大小：预计50-80MB (简化后体积更小)
- 支持Windows 7及以上版本
- 用户无需安装Python环境即可运行