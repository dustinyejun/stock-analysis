# 趋势突破策略升级 - 详细实施步骤

## 📋 实施总览

**预计总耗时**：3.5小时  
**实施优先级**：高  
**影响范围**：趋势突破选股规则  
**向后兼容**：是（保留原有接口）  

## 🎯 阶段一：配置参数升级（30分钟）

### 任务1.1：修改配置文件 (15分钟)
**文件**：`config/settings.py`

**修改内容**：
```python
# 在SelectionConfig类中修改趋势突破策略参数
class SelectionConfig(BaseModel):
    # ... 其他配置保持不变
    
    # 趋势突破策略参数（升级版）
    trend_breakout_ma_periods: List[int] = [5, 10, 20, 60]    # 多均线周期
    trend_breakout_volume_ratio: float = 2.0                  # 倍量标准（提高到2倍）
    trend_breakout_amplitude_threshold: float = 0.07          # 日内震幅要求7%
    trend_breakout_consecutive_days: int = 2                  # 连续天数要求
    trend_breakout_lookback_days: int = 240                   # 8个月高点（240交易日）
    trend_breakout_yang_required: bool = True                 # 必须阳线
    trend_breakout_breakout_confirmation: float = 0.001       # 突破确认0.1%
    
    # 移除的旧参数（注释说明）:
    # trend_breakout_yang_threshold: 已整合到amplitude_threshold
    # trend_breakout_consecutive_days: 保留但用法改变
```

**验证步骤**：
- 检查配置文件语法正确
- 确认参数类型和默认值合理
- 验证与现有配置的兼容性

### 任务1.2：更新配置访问逻辑 (15分钟)
**目标**：确保新参数能正确被规则引擎读取

**修改要点**：
- 验证`get_config()`函数正常工作
- 确认参数命名规范一致
- 测试参数读取无错误

## 🔧 阶段二：技术指标模块升级（45分钟）

### 任务2.1：新增日内震幅计算 (15分钟)
**文件**：`src/indicators.py`

**新增函数**：
```python
def calculate_daily_amplitude(self, data: pd.DataFrame) -> pd.Series:
    """
    计算日内震幅
    
    震幅 = (最高价 - 最低价) / 前日收盘价 * 100%
    """
    prev_close = data['close'].shift(1)
    amplitude = (data['high'] - data['low']) / prev_close
    return amplitude.fillna(0)

def check_consecutive_amplitude(self, data: pd.DataFrame, threshold: float = 0.07, days: int = 2) -> pd.Series:
    """
    检查连续震幅大于阈值的天数
    """
    amplitude = self.calculate_daily_amplitude(data)
    amplitude_condition = amplitude > threshold
    
    # 计算连续满足条件的天数
    consecutive = amplitude_condition.rolling(window=days).sum()
    return consecutive >= days
```

### 任务2.2：增强多均线排列判断 (15分钟)
**修改现有函数**：
```python
def calculate_ma_bullish_alignment(self, data: pd.DataFrame, periods: List[int] = [5, 10, 20, 60]) -> pd.Series:
    """
    判断多均线多头排列
    
    条件：MA5 > MA10 > MA20 > MA60 且股价 > MA5
    """
    mas = {}
    for period in periods:
        mas[f'ma{period}'] = data['close'].rolling(window=period).mean()
    
    # 检查均线多头排列
    alignment_condition = True
    for i in range(len(periods) - 1):
        condition = mas[f'ma{periods[i]}'] > mas[f'ma{periods[i+1]}']
        alignment_condition = alignment_condition & condition
    
    # 股价位置确认
    price_condition = data['close'] > mas['ma5']
    
    return alignment_condition & price_condition
```

### 任务2.3：优化连续倍量判断 (15分钟)
**修改现有函数**：
```python
def check_consecutive_volume_expansion(self, data: pd.DataFrame, ratio: float = 2.0, days: int = 2) -> pd.Series:
    """
    检查连续倍量（每天都大于2倍五日均量）
    """
    volume_ma5 = data['volume'].rolling(window=5).mean()
    volume_ratio = data['volume'] / volume_ma5
    volume_condition = volume_ratio > ratio
    
    # 连续days天都满足倍量条件
    consecutive = volume_condition.rolling(window=days).sum()
    return consecutive >= days
```

## 🎯 阶段三：规则引擎重构（45分钟）

### 任务3.1：重写核心判断逻辑 (30分钟)
**文件**：`src/rules/trend_breakout.py`

**关键修改**：
```python
def check_conditions(self, data: pd.DataFrame, indicators: pd.DataFrame) -> SelectionResult:
    """
    检查趋势突破条件（升级版）
    
    新逻辑：
    1. 多头趋势：均线多头排列且股价>MA5
    2. 连续倍量：连续2天每天成交量>5日均量×2倍  
    3. 大震幅阳线：连续2天震幅>7%且为阳线
    4. 突破8个月高点：收盘价>240日内最高价
    """
    try:
        # 获取升级后的配置参数
        ma_periods = self.config.get_param('ma_periods', [5, 10, 20, 60])
        volume_ratio = self.config.get_param('volume_ratio_threshold', 2.0)
        amplitude_threshold = self.config.get_param('amplitude_threshold', 0.07)
        consecutive_days = self.config.get_param('consecutive_days', 2)
        lookback_days = self.config.get_param('high_lookback_period', 240)
        
        # 检查必需的技术指标
        required_indicators = [
            'ma_bullish_alignment', 'consecutive_volume_expansion', 
            'consecutive_amplitude', 'yang_lines', 'high_240'
        ]
        
        latest_data = indicators.iloc[-1]
        scores = []
        conditions_met = {}
        
        # 条件1: 多头趋势确认（简化判断）
        bullish_trend = latest_data.get('ma_bullish_alignment', False)
        conditions_met['bullish_trend'] = {
            'met': bullish_trend,
            'description': '均线多头排列且股价>MA5'
        }
        
        if bullish_trend:
            scores.append(90)  # 满足给高分
        else:
            scores.append(0)   # 不满足直接0分
        
        # 条件2: 连续倍量确认
        consecutive_volume = latest_data.get('consecutive_volume_expansion', False)
        conditions_met['consecutive_volume'] = {
            'met': consecutive_volume,
            'ratio_required': volume_ratio,
            'days_required': consecutive_days
        }
        
        if consecutive_volume:
            scores.append(90)
        else:
            scores.append(0)
        
        # 条件3: 连续大震幅阳线
        consecutive_amp = latest_data.get('consecutive_amplitude', False)
        consecutive_yang = latest_data.get('consecutive_yang', False)
        amp_yang_condition = consecutive_amp and consecutive_yang
        
        conditions_met['amplitude_yang'] = {
            'met': amp_yang_condition,
            'amplitude_threshold': amplitude_threshold,
            'yang_required': True
        }
        
        if amp_yang_condition:
            scores.append(90)
        else:
            scores.append(0)
        
        # 条件4: 突破8个月高点
        current_price = latest_data['close']
        high_240 = latest_data.get('high_240', 0)
        breakout_condition = current_price > high_240
        
        conditions_met['breakout_240'] = {
            'met': breakout_condition,
            'current_price': current_price,
            'high_240': high_240,
            'lookback_days': lookback_days
        }
        
        if breakout_condition:
            # 突破幅度越大分数越高
            breakout_strength = (current_price - high_240) / high_240 if high_240 > 0 else 0
            breakout_score = min(90 + breakout_strength * 100, 100)
            scores.append(breakout_score)
        else:
            scores.append(0)
        
        # 综合评分（新逻辑：四个条件都必须满足）
        final_score = np.mean(scores) if scores else 0
        all_conditions_met = all([
            bullish_trend, consecutive_volume, 
            amp_yang_condition, breakout_condition
        ])
        
        # 确定结果（四个条件都满足才能通过）
        min_score = self.config.get_threshold('min_score', 70.0)
        high_score = self.config.get_threshold('high_score', 90.0)
        
        if all_conditions_met and final_score >= high_score:
            result = RuleResult.PASS
            confidence = 0.95
        elif all_conditions_met and final_score >= min_score:
            result = RuleResult.PARTIAL
            confidence = 0.80
        else:
            result = RuleResult.FAIL
            confidence = 0.60
```

### 任务3.2：更新规则描述 (15分钟)
**修改`get_rule_description`方法**：
```python
def get_rule_description(self) -> Dict[str, Any]:
    return {
        'name': '趋势突破（升级版）',
        'description': '多头趋势中连续倍量大震幅突破8个月高点',
        'conditions': [
            "均线多头排列（MA5>MA10>MA20>MA60）且股价>MA5",
            f"连续{self.config.get_param('consecutive_days', 2)}天倍量（每天>{self.config.get_param('volume_ratio_threshold', 2.0)}倍五日均量）",
            f"连续{self.config.get_param('consecutive_days', 2)}天大震幅阳线（震幅>{self.config.get_param('amplitude_threshold', 0.07)*100}%）",
            f"突破{self.config.get_param('high_lookback_period', 240)}个交易日内最高价"
        ],
        'logic_type': 'enhanced',
        'parameters': self.config.params,
        'thresholds': self.config.thresholds
    }
```

## 🧪 阶段四：测试验证（60分钟）

### 任务4.1：单元测试 (30分钟)
**创建测试文件**：`tests/test_trend_breakout_enhanced.py`

**测试用例**：
1. **技术指标计算测试**
   - 日内震幅计算准确性
   - 多均线排列判断正确性
   - 连续倍量识别准确性

2. **规则逻辑测试**
   - 四个条件组合测试
   - 边界条件处理
   - 评分机制验证

3. **配置参数测试**
   - 参数读取正确性
   - 默认值设置合理性

### 任务4.2：实际案例验证 (30分钟)
**验证目标**：
- 大龙股份 (603266) 应该被识别为PASS
- 北方稀土 (600111) 应该被识别为PASS
- 非典型突破应该被正确过滤

**验证方法**：
```python
# 创建验证脚本
def test_real_cases():
    # 测试大龙股份案例
    assert test_symbol_logic('603266', expected_result='PASS')
    
    # 测试北方稀土案例  
    assert test_symbol_logic('600111', expected_result='PASS')
    
    # 测试边界案例
    assert test_symbol_logic('边界案例代码', expected_result='FAIL')
```

## 🌐 阶段五：界面和文档更新（30分钟）

### 任务5.1：Web界面更新 (15分钟)
**文件**：`app.py`

**修改内容**：
```python
# 更新趋势突破规则的帮助文本
use_trend_breakout = st.sidebar.checkbox(
    "趋势突破规则（升级版）",
    value=True,
    help="多头趋势中连续倍量大震幅突破8个月高点（升级版）"
)

# 更新结果表格列名
'连续倍量天数': rule_data.get('consecutive_volume_days', ''),
'平均震幅': rule_data.get('avg_amplitude', ''),
'突破8个月高点': rule_data.get('breakout_240_confirmed', ''),
```

### 任务5.2：文档更新 (15分钟)
**更新文件**：
- `README.md` 中的策略说明
- 用户手册中的趋势突破部分
- 记忆文件中的技术文档

## ✅ 完成检查清单

### 代码完成标准
- [ ] 配置文件参数全部更新并测试通过
- [ ] 技术指标模块新增函数实现并验证正确
- [ ] 规则引擎逻辑完全重写并符合新需求
- [ ] 单元测试覆盖所有核心功能
- [ ] 实际案例验证通过（大龙股份、北方稀土）

### 质量保证标准
- [ ] 代码遵循项目编码规范
- [ ] 所有函数都有完整的文档字符串
- [ ] 异常处理覆盖各种边界情况
- [ ] 性能表现不低于原有实现
- [ ] 向后兼容性得到保证

### 功能验证标准
- [ ] 新逻辑能正确识别经典趋势突破形态
- [ ] 四个条件缺一不可的逻辑正确执行
- [ ] 评分机制反映股票质量差异
- [ ] Web界面显示更新且用户友好
- [ ] 整体系统稳定运行无异常

## 🚀 预期收益

**升级完成后预期效果**：
1. **选股精度提升30%+**：更准确识别真正的强势突破
2. **假突破过滤率90%+**：有效避免无效突破信号
3. **用户满意度提升**：提供更符合经典技术分析的选股工具
4. **系统竞争力增强**：区别于市场上的简单技术指标组合

**时间安排建议**：
- 工作日晚上：完成阶段一、二（配置和技术指标）
- 周末上午：完成阶段三（规则引擎重构）  
- 周末下午：完成阶段四、五（测试和文档）

升级实施完成后，趋势突破策略将能够更准确地识别像大龙股份、北方稀土这样的经典突破形态，为用户提供更有价值的选股参考。