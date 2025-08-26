@echo off
chcp 65001 > nul 2>&1
REM A股选股系统 EXE打包脚本
REM 在Windows环境下运行此脚本进行打包

echo ========================================
echo    A股选股系统 EXE打包工具
echo ========================================
echo.

REM 检查Python环境
echo [1/6] 检查Python环境...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python环境，请先安装Python 3.9+
    pause
    exit /b 1
)

REM 检查虚拟环境（可选）
echo [2/6] 检查虚拟环境...
if exist "venv\Scripts\activate.bat" (
    echo 发现虚拟环境，正在激活...
    call venv\Scripts\activate.bat
) else (
    echo 未找到虚拟环境，使用系统Python环境
)

REM 安装打包依赖
echo [3/6] 安装打包依赖...
pip install pyinstaller auto-py-to-exe
pip install -r requirements.txt

REM 清理之前的构建
echo [4/6] 清理之前的构建文件...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec.backup" del /q *.spec.backup

REM 使用spec文件打包
echo [5/6] 开始打包 (这可能需要几分钟)...
pyinstaller app.spec

REM 检查打包结果
echo [6/6] 检查打包结果...
if exist "dist\A股选股系统.exe" (
    echo.
    echo ========================================
    echo           打包成功完成！
    echo ========================================
    echo EXE文件位置: dist\A股选股系统.exe
    dir /b dist\A股选股系统.exe
    echo.
    echo 文件大小:
    for %%I in (dist\A股选股系统.exe) do echo %%~zI bytes
    echo.
    echo 建议测试: 双击运行 dist\A股选股系统.exe 验证功能
) else (
    echo.
    echo ========================================
    echo           打包失败！
    echo ========================================
    echo 请检查错误信息并重试
)

echo.
echo 按任意键退出...
pause > nul