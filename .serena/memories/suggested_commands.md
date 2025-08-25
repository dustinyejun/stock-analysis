# 常用开发命令

## 环境管理
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (macOS/Linux)
source venv/bin/activate

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 更新requirements.txt
pip freeze > requirements.txt
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

## 数据库操作
```bash
# 初始化数据库
python scripts/init_database.py

# 数据库迁移
python scripts/migrate_database.py
```

## 应用启动
```bash
# 启动FastAPI服务
uvicorn main:app --reload

# 启动Streamlit界面
streamlit run app.py

# 运行选股任务
python src/stock_selector.py

# 运行数据更新任务
python scripts/update_data.py
```

## 系统命令 (macOS)
```bash
# 查看进程
ps aux | grep python

# 查看端口占用
lsof -i :8000

# 查看磁盘空间
df -h

# 查看内存使用
vm_stat

# 查找文件
find . -name "*.py" -type f
```

## Docker相关 (如果使用)
```bash
# 构建镜像
docker build -t stock-analysis .

# 运行容器
docker run -p 8000:8000 stock-analysis

# 查看容器日志
docker logs <container_id>
```

## Git操作
```bash
# 查看状态
git status

# 添加文件
git add .

# 提交更改
git commit -m "commit message"

# 推送代码
git push origin main
```