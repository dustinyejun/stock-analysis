# 🎯 A股智能选股系统

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.48.1-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

> 专业的A股股票筛选工具，基于技术分析和量化策略，帮助投资者快速发现优质投资标的。**支持打包为独立EXE文件，无需Python环境即可运行！**

## 🎯 系统特性

### 核心功能
- **🎯 真实数据**: 接入akshare、yfinance等数据源，获取真实A股行情数据，自动过滤退市和停牌股票
- **🤖 智能选股**: 基于技术分析的多维度选股策略，真实算法评分
- **⚡ 实时扫描**: 支持从测试模式到全市场的多级扫描（5-1300只股票）
- **🔧 规则引擎**: 黄金坑、趋势突破等成熟选股规则，真实条件判断
- **📊 结果分析**: 详细的选股结果和规则表现分析，分规则专业展示
- **💾 数据导出**: 支持CSV、JSON等多种格式导出真实交易数据

### 技术架构
- **后端**: Python 3.9+, pandas, numpy
- **数据源**: akshare (主), yfinance (备)，真实A股数据
- **界面**: Streamlit Web应用，智能模式切换
- **计算**: 向量化技术指标计算，24种专业指标
- **架构**: 面向对象设计，模块化架构，生产级代码质量

## 🚀 快速开始

### 方法1: 使用EXE文件 (推荐) 🎯

**无需安装Python环境，双击即可使用！**

1. **下载EXE程序**
   ```
   从GitHub Releases下载 A股选股系统.exe
   或在Windows电脑上使用build_exe.bat打包生成
   ```

2. **运行程序**
   ```
   双击 A股选股系统.exe
   等待5-15秒启动(首次启动需要解压)
   程序会自动在浏览器中打开界面
   ```

3. **开始选股**
   - 在左侧配置扫描板块和选股规则
   - 点击"🚀 开始选股扫描"按钮
   - 查看实时扫描进度和结果展示

### 方法2: 源码运行 (开发者)

```bash
# 1. 克隆项目
git clone https://github.com/dustinyejun/stock-analysis.git
cd stock-analysis

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动应用
streamlit run app.py
```

### 方法3: Windows下EXE打包

```bash
# 在Windows 10/11 x86_64环境下
# 1. 一键打包(推荐)
build_exe.bat

# 2. 手动打包
pip install -r requirements.txt
pyinstaller app.spec

# 3. 获取EXE文件
# 生成的文件: dist/A股选股系统.exe
```

## 📊 支持的选股策略

### 1. 黄金坑规则
- **策略描述**: 检测深度回撤后的反转突破机会
- **关键条件**:
  - 股价从高点回撤超过20%
  - 出现大阳线突破(涨幅≥5%, 量比≥1.5)
  - 突破10日均线
  - 伴随放量确认
- **专属展示**: 当前价格、触发日期、前期高点、最大跌幅、大阳线涨幅、10日均线

### 2. 趋势突破规则
- **策略描述**: 识别多头趋势和放量突破信号
- **关键条件**:
  - 确认多头趋势(短期均线 > 长期均线)
  - 连续放量(量比>1.3, 持续2天+)
  - 突破前期高点
  - 价格上升趋势确立
- **专属展示**: 当前价格、触发日期、前期高点、突破幅度、连续放量天数、平均量比

## 🔧 技术指标

系统支持24种技术指标计算：

### 趋势指标
- 移动平均线 (MA5, MA10, MA20, MA60)
- 指数移动平均线 (EMA)

### 动量指标
- RSI (相对强弱指标)
- MACD (移动平均收敛发散)
- 威廉指标 (WR)

### 成交量指标
- 量比 (Volume Ratio)
- 成交量移动平均

### 价格指标
- 布林带 (Bollinger Bands)
- 支撑阻力位识别
- 前期高低点分析

## 📁 项目结构

```
stock-analysis/
├── app.py                    # Streamlit Web应用主入口
├── src/                      # 核心源码目录
│   ├── data_fetcher.py       # 股票数据获取模块
│   ├── indicators.py         # 技术指标计算模块
│   ├── selection_rules.py    # 选股规则引擎
│   ├── stock_selector.py     # 主选股器类
│   └── rules/                # 具体选股规则实现
│       ├── golden_pit.py     # 黄金坑规则
│       └── trend_breakout.py # 趋势突破规则
├── results/                  # 扫描结果存储目录
├── history/                  # 历史记录存储目录
├── tests/                    # 测试代码
├── docs/                     # 文档目录
├── requirements.txt          # Python依赖列表
└── README.md                # 项目说明文档
```

## 🎮 Web界面功能

### 主要页面
1. **主页**: 系统介绍和快速开始指南
2. **扫描配置**: 设置扫描参数和规则选择
3. **开始扫描**: 执行股票筛选和进度监控
4. **扫描结果**: 详细结果展示和分析
5. **导出&历史**: 结果导出和历史记录查看

### 配置选项
- **扫描板块**: 沪市主板(600xxx)、深市主板(000xxx,002xxx)、创业板(300xxx)、科创板(688xxx)、全部板块
- **结果数量**: 10-500只股票可选
- **评分阈值**: 0-100分可调，基于真实算法评分
- **规则选择**: 支持多规则组合使用，真实条件判断
- **并发设置**: 1-10个工作线程，恢复并行模式提升扫描速度
- **导出格式**: CSV、JSON、Excel，真实交易数据

### 结果展示
- **分规则显示**: 黄金坑和趋势突破规则结果分开展示
- **专属字段**: 每个规则显示其特定的关键指标
- **智能标签页**: 根据启用规则动态生成展示界面
- **综合视图**: 保留传统的列表、详细、分析视图
- **历史记录**: 过往扫描记录查看

## 📈 性能特性

- **🔄 智能模式**: 自动检测真实数据可用性，优雅降级到演示模式
- **⚡ 并发处理**: 支持多线程并发获取真实股票数据，网络恢复后自动启用并行模式
- **📦 批量优化**: 智能分批处理，平衡性能和网络稳定性
- **📊 进度监控**: 实时显示扫描进度和统计，透明化处理过程  
- **🛡️ 异常处理**: 完善的错误处理和恢复机制，数据源自动切换
- **🎯 智能过滤**: 自动过滤退市和停牌股票（>30天无交易），确保选股结果的实用性
- **🎯 界面优化**: 解决了遮罩层重复问题，提供流畅的扫描体验
- **⚡ 响应速度**: 测试模式秒级响应，并行模式下中等规模1-2分钟完成

## 🧪 测试验证

### 运行测试
```bash
# 数据获取模块测试  
python src/data_fetcher.py

# 真实选股器测试
python src/real_stock_selector.py

# 界面功能测试（自动检测真实/演示模式）
streamlit run app.py
```

### 测试覆盖
- ✅ **真实数据获取**: akshare数据源连接正常
- ✅ **技术指标计算**: 24种指标计算准确
- ✅ **规则引擎**: 黄金坑、趋势突破规则真实判断
- ✅ **选股器集成**: 端到端真实选股流程
- ✅ **界面功能**: 智能模式切换和完整交互
- ✅ **结果展示**: 分规则专业显示和数据导出
- ✅ **智能过滤**: 退市和停牌股票自动过滤功能

## 💡 使用建议

### 初学者
1. 建议从"测试模式"开始熟悉系统
2. 先使用单一规则，理解选股逻辑
3. 观察不同参数设置的结果差异

### 进阶用户
1. 可以组合多个规则使用
2. 调整评分阈值获得最优结果
3. 利用历史记录分析规则表现

### 专业用户
1. 可以扩展自定义选股规则
2. 优化并发参数提升扫描速度
3. 结合导出数据进行深度分析

## ⚠️ 免责声明

本系统仅供学习和研究使用，不构成任何投资建议。
- 系统基于技术分析，无法预测市场变化
- 历史表现不代表未来收益
- 投资有风险，决策需谨慎
- 使用者需要自行承担投资风险

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目：

1. Fork本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue: [GitHub Issues](https://github.com/yourname/stock-analysis/issues)
- 邮件联系: your.email@example.com

## 📦 EXE打包特性

### 🎯 独立运行优势
- ✅ **零环境依赖**: 无需安装Python、pip或任何依赖库
- ✅ **一键启动**: 双击EXE文件即可使用，如同普通软件
- ✅ **完整功能**: 包含所有选股功能，性能与源码版本一致
- ✅ **用户友好**: 适合非技术人员使用，降低使用门槛

### 💻 系统要求
- **操作系统**: Windows 10/11 (64位)
- **内存**: 4GB以上RAM
- **网络**: 需要互联网连接获取股票数据
- **硬盘**: 500MB可用空间

### 📁 打包文档
- [📖 用户使用手册](USER_MANUAL.md) - 详细操作指南
- [⚙️ EXE打包说明](BUILD_INSTRUCTIONS.md) - Windows环境打包教程
- [✅ 打包检查清单](PACKAGING_CHECKLIST.md) - 打包前完整检查

---

**开发状态**: ✅ 已完成 | **版本**: v1.0.0 | **最后更新**: 2025年8月26日  
**项目状态**: 🚀 生产就绪 | **EXE支持**: ✅ 完整配置 | **GitHub**: [github.com/dustinyejun/stock-analysis](https://github.com/dustinyejun/stock-analysis)