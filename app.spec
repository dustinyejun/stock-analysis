# -*- mode: python ; coding: utf-8 -*-

# A股选股系统 PyInstaller 配置文件
# 使用方法: pyinstaller app.spec

import os
import sys
from pathlib import Path

# 获取项目根目录
try:
    project_root = Path(__file__).parent
except NameError:
    # 如果 __file__ 未定义，使用当前工作目录
    project_root = Path(os.getcwd())

block_cipher = None

# 隐式导入的模块 - 确保打包时包含这些模块
hiddenimports = [
    'streamlit',
    'streamlit.web.cli',
    'streamlit.web.bootstrap',
    'streamlit.web.server',
    'streamlit.web.server.routes',
    'streamlit.runtime.scriptrunner.script_runner', 
    'streamlit.runtime.state.session_state_proxy',
    'streamlit.runtime.legacy_caching',
    'streamlit.runtime.caching',
    'streamlit.components.v1',
    'streamlit.elements',
    'streamlit.proto',
    'pandas',
    'numpy',
    'akshare',
    'akshare.stock',
    'akshare.tool',
    'akshare.energy',
    'akshare.futures',
    'akshare.option',
    'akshare.bond',
    'akshare.fund',
    'akshare.crawler',
    'akshare.utils',
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
    'tornado.web',
    'tornado.template',
    'jinja2',
    'watchdog',
    'validators',
    'packaging',
    'importlib_metadata',
    'importlib.metadata',
    'tzdata',
    'webbrowser',
    'threading',
    'io',
    'time',
    # 项目模块
    'src',
    'src.real_stock_selector',
    'src.data_fetcher',
    'src.indicators',
    'src.selection_rules',
    'src.stock_selector',
    'src.rules',
    'src.rules.golden_pit',
    'src.rules.trend_breakout',
    'src.utils',
    'src.utils.decorators',
    'src.utils.exceptions',
    'src.utils.logger',
    'src.utils_simple',
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
import streamlit
streamlit_path = Path(streamlit.__file__).parent

# 获取 akshare 路径并包含其数据文件
try:
    import akshare
    akshare_path = Path(akshare.__file__).parent
    akshare_datas = [(str(akshare_path), 'akshare')]  # 包含整个 akshare 目录
except:
    akshare_datas = []

datas = [
    ('app.py', '.'),  # 将 app.py 打包到根目录
    ('src/', 'src/'),  # 包含整个 src 目录
    (str(streamlit_path / 'static'), 'streamlit/static'),  # Streamlit 静态文件
    (str(streamlit_path / 'runtime'), 'streamlit/runtime'),  # Streamlit 运行时文件
] + akshare_datas  # 添加 akshare 数据文件

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
    console=True,  # 显示控制台窗口以便调试
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 可选：添加图标文件
    # icon='icon.ico',  # 如果有图标文件，取消注释
)