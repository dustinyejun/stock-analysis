# -*- mode: python ; coding: utf-8 -*-

# A股选股系统 PyInstaller 配置文件
# 使用方法: pyinstaller app.spec

import os
import sys
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent

block_cipher = None

# 隐式导入的模块 - 确保打包时包含这些模块
hiddenimports = [
    'streamlit',
    'streamlit.web.cli',
    'streamlit.runtime.scriptrunner.script_runner', 
    'streamlit.runtime.state.session_state_proxy',
    'pandas',
    'numpy',
    'akshare',
    'requests',
    'pydantic',
    'loguru',
    'yfinance',
    'python_dotenv',
    'altair',
    'plotly',
    'PIL',
    'toml',
    'click',
    'tornado',
    'watchdog',
    'validators',
    'packaging',
    'importlib_metadata',
    'tzdata',
]

# 需要排除的模块 - 减少文件大小
excludes = [
    'matplotlib',
    'jupyter',
    'IPython',
    'notebook',
    'qtpy',
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'tkinter',
    '_tkinter',
    'unittest',
    'test',
    'tests',
    'pytest',
]

# 需要包含的数据文件
datas = [
    # 如果有配置文件需要打包，取消下面的注释
    # ('.env.example', '.'),
    # ('config/', 'config/'),
]

# 分析主程序
a = Analysis(
    ['run_app.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 去重处理
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 创建可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='A股选股系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用UPX压缩（如果安装了UPX）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 可选：添加图标文件
    # icon='icon.ico',  # 如果有图标文件，取消注释
)