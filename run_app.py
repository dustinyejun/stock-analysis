#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A股选股系统 - 主启动文件
这个文件是为了确保在EXE打包时能够正确启动Streamlit应用
"""

import sys
import os
import io
import threading
import webbrowser
import time
from pathlib import Path

# 确保项目路径在sys.path中
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def fix_streamlit_for_exe():
    """修复 Streamlit 在 EXE 环境下的问题"""
    # 修复 sys.stdin 问题
    if not hasattr(sys.stdin, 'isatty'):
        sys.stdin = io.StringIO()
    
    # 修复 importlib.metadata 问题
    try:
        import importlib.metadata as metadata
    except ImportError:
        import importlib_metadata as metadata
    
    # 手动设置 streamlit 版本信息
    try:
        metadata.version('streamlit')
    except:
        # 如果找不到版本信息，设置一个默认版本
        import streamlit
        if not hasattr(streamlit, '__version__'):
            streamlit.__version__ = '1.28.0'

def open_browser_delayed():
    """延迟打开浏览器"""
    time.sleep(3)  # 等待3秒让服务器启动
    webbrowser.open('http://localhost:8501')

def main():
    """主启动函数"""
    print("=" * 60)
    print("A股选股系统启动中...")
    print("=" * 60)
    
    try:
        print("[步骤1/5] 正在检查Python环境...")
        print(f"Python版本: {sys.version}")
        print(f"当前目录: {os.getcwd()}")
        
        print("[步骤2/5] 正在初始化系统...")
        
        # 修复 EXE 环境问题
        fix_streamlit_for_exe()
        print("✓ 系统环境修复完成")
        
        print("[步骤3/5] 正在配置环境变量...")
        # 设置环境变量
        os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
        os.environ['STREAMLIT_SERVER_RUN_ON_SAVE'] = 'false'
        os.environ['STREAMLIT_GLOBAL_DEVELOPMENT_MODE'] = 'false'  # 禁用开发模式
        os.environ['STREAMLIT_SERVER_PORT'] = '8501'  # 通过环境变量设置端口
        print("✓ 环境变量配置完成")
        
        print("[步骤4/5] 正在准备浏览器...")
        # 启动浏览器线程
        browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
        browser_thread.start()
        print("✓ 浏览器准备完成")
        
        print("[步骤5/5] 正在导入Streamlit模块...")
        # 导入并启动应用
        from streamlit.web import cli
        print("✓ Streamlit模块导入成功")
        
        # 确定 app.py 的正确路径
        app_path = None
        possible_paths = [
            project_root / 'app.py',  # 开发环境路径
            Path(sys.executable).parent / 'app.py',  # EXE同目录
            Path(os.getcwd()) / 'app.py',  # 当前工作目录
        ]
        
        for path in possible_paths:
            if path.exists():
                app_path = str(path)
                break
        
        if not app_path:
            raise FileNotFoundError(f"找不到 app.py 文件。尝试的路径: {[str(p) for p in possible_paths]}")
        
        print(f"✓ 找到应用文件: {app_path}")
        
        # 构建启动参数 (移除可能冲突的port参数)
        sys.argv = [
            'streamlit', 
            'run', 
            app_path,
            '--server.headless=true',
            '--browser.gatherUsageStats=false',
            '--server.runOnSave=false',
            '--global.developmentMode=false',
            '--theme.base=light'
        ]
        
        print("服务器启动中，浏览器将自动打开...")
        print("如果浏览器未自动打开，请手动访问: http://localhost:8501")
        
        # 启动Streamlit应用
        cli.main()
        
    except KeyboardInterrupt:
        print("\n用户终止程序")
        sys.exit(0)
    except Exception as e:
        print(f"\n启动失败: {e}")
        print("\n错误详情:")
        import traceback
        traceback.print_exc()
        print("\n" + "="*50)
        print("常见解决方案:")
        print("1. 确保没有其他程序占用8501端口")
        print("2. 检查防火墙设置")
        print("3. 以管理员权限运行")
        print("="*50)
        input("\n按回车键退出...")
        return 1

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n程序启动时发生致命错误: {e}")
        print("\n完整错误信息:")
        import traceback
        traceback.print_exc()
        print("\n程序即将退出，请检查上述错误信息")
        input("按回车键退出...")
    except SystemExit:
        input("程序已退出，按回车键关闭窗口...")