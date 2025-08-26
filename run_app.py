#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A股选股系统 - 主启动文件
这个文件是为了确保在EXE打包时能够正确启动Streamlit应用
"""

import sys
import os
from pathlib import Path

# 确保项目路径在sys.path中
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def main():
    """主启动函数"""
    try:
        print("正在启动A股选股系统...")
        
        # 设置环境变量
        os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
        
        # 导入并启动应用
        import streamlit.web.cli as cli
        
        # 构建启动参数
        args = [
            'streamlit', 'run', 
            str(project_root / 'app.py'),
            '--server.port=8501',
            '--server.headless=true',
            '--browser.gatherUsageStats=false',
            '--theme.base=light'
        ]
        
        # 启动Streamlit应用
        sys.argv = args
        cli.main()
        
    except Exception as e:
        print(f"启动失败: {e}")
        input("按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()