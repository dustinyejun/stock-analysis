# 代码结构和开发规范

## 项目目录结构
```
stock-analysis/
├── src/                    # 核心源代码
│   ├── __init__.py
│   ├── data_fetcher.py    # 数据获取模块
│   └── indicators.py      # 技术指标计算
├── config/                 # 配置文件
├── tests/                  # 测试文件
├── docs/                   # 文档目录
├── logs/                   # 日志文件
├── scripts/                # 脚本文件
├── data/                   # 数据文件
├── requirements.txt        # Python依赖
├── stock_selection_requirements.md  # 需求文档
├── technical_design.md     # 技术设计
└── implementation_plan.md  # 实施计划
```

## 核心模块设计
1. **StockDataFetcher** - 股票数据获取器
2. **TechnicalIndicators** - 技术指标计算器
3. **SelectionRule** - 选股规则基类
4. **GoldenPitRule** - 黄金坑规则
5. **TrendBreakoutRule** - 趋势突破规则
6. **StockSelector** - 股票选择器

## 编码规范
- **代码风格**: 遵循PEP8标准
- **类型提示**: 使用Python类型注解
- **文档字符串**: 所有公开接口必须有docstring
- **错误处理**: 使用自定义异常类和装饰器
- **日志记录**: 使用loguru进行结构化日志

## 设计模式
- **策略模式**: 选股规则的实现
- **工厂模式**: 数据获取器的创建
- **装饰器模式**: 重试机制和错误处理
- **单例模式**: 配置管理器

## 代码质量要求
- 单元测试覆盖率 ≥ 80%
- 关键模块必须代码审查
- 所有公开接口必须有文档注释