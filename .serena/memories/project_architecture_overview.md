# A股选股系统 - 架构总览

## 系统架构
### 核心模块结构
```
stock-analysis/
├── src/
│   ├── data_fetcher.py        # 数据获取层
│   ├── indicators.py          # 技术指标计算
│   ├── selection_rules.py     # 规则引擎框架
│   ├── stock_selector.py      # 主选股器
│   └── rules/                 # 具体选股规则
│       ├── golden_pit.py      # 黄金坑策略
│       └── trend_breakout.py  # 趋势突破策略
├── tests/                     # 测试代码
└── docs/                      # 文档
```

## 技术栈
- **语言**: Python 3.8+
- **数据处理**: pandas, numpy
- **并发**: ThreadPoolExecutor
- **配置**: dataclass + dict
- **日志**: Python logging
- **类型提示**: typing

## 设计模式
1. **抽象工厂**: BaseSelectionRule 定义统一接口
2. **注册表模式**: RuleRegistry 管理规则实例
3. **策略模式**: 不同选股规则可动态切换
4. **建造者模式**: 配置驱动的规则构建
5. **观察者模式**: 统计信息收集和监控

## 数据流
```
原始股票数据 -> 技术指标计算 -> 规则引擎应用 -> 评分排序 -> 结果输出
```

## 核心类关系
- `StockSelector`: 主控制器，协调各组件
- `RuleEngine`: 规则执行引擎
- `RuleRegistry`: 规则注册管理
- `BaseSelectionRule`: 规则抽象基类
- `SelectionResult`: 规则执行结果
- `RuleConfig`: 规则配置管理

## 扩展性设计
1. **规则扩展**: 继承BaseSelectionRule即可添加新规则
2. **指标扩展**: indicators模块支持新指标添加  
3. **数据源扩展**: data_fetcher接口化支持多数据源
4. **评分扩展**: 支持自定义评分算法和权重

## 性能优化
- 多线程并发处理
- 数据预计算和缓存
- 批量操作减少I/O
- 内存优化的数据结构