#!/bin/bash
# A股选股系统 EXE打包脚本（Linux/Mac版本）
# 注意：此脚本仅生成对应平台的可执行文件，不能生成Windows EXE

echo "========================================"
echo "    A股选股系统 打包工具"
echo "========================================"
echo

# 检查Python环境
echo "[1/6] 检查Python环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: 未找到Python环境，请先安装Python 3.9+"
    exit 1
fi

# 检查虚拟环境
echo "[2/6] 检查虚拟环境..."
if [ -f "venv/bin/activate" ]; then
    echo "发现虚拟环境，正在激活..."
    source venv/bin/activate
else
    echo "未找到虚拟环境，使用系统Python环境"
fi

# 安装打包依赖
echo "[3/6] 安装打包依赖..."
pip install pyinstaller auto-py-to-exe
pip install -r requirements.txt

# 清理之前的构建
echo "[4/6] 清理之前的构建文件..."
rm -rf build dist *.spec.backup

# 使用spec文件打包
echo "[5/6] 开始打包 (这可能需要几分钟)..."
pyinstaller app.spec

# 检查打包结果
echo "[6/6] 检查打包结果..."
if [ -f "dist/A股选股系统" ]; then
    echo
    echo "========================================"
    echo "           打包成功完成！"
    echo "========================================"
    echo "可执行文件位置: dist/A股选股系统"
    ls -lh dist/A股选股系统
    echo
    echo "建议测试: ./dist/A股选股系统 验证功能"
else
    echo
    echo "========================================"
    echo "           打包失败！"
    echo "========================================"
    echo "请检查错误信息并重试"
fi

echo
echo "按回车键退出..."
read