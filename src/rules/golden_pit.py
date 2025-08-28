"""
黄金坑选股规则实现
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

from ..selection_rules import BaseSelectionRule, SelectionResult, RuleResult, RuleConfig


class GoldenPitRule(BaseSelectionRule):
    """
    黄金坑选股规则（简化版）
    
    黄金坑特征：
    1. 股价从前期高点回撤超过20%，形成"坑"
    2. 股价重新站上10日均线，确认突破
    
    简化逻辑说明：
    - 移除了大阳线强制要求，允许温和突破
    - 移除了成交量放大要求，适应存量资金推动的情况
    - 条件从4个简化为2个核心条件，提高选股灵敏度
    """
    
    def __init__(self, config: RuleConfig = None):
        """
        初始化黄金坑规则（简化版）
        
        Args:
            config: 规则配置
        """
        default_config = RuleConfig(
            enabled=True,
            weight=1.0,
            params={
                'drawdown_threshold': 0.20,      # 回调阈值（保留）
                'ma_period': 10,                 # 均线周期（保留）
                'high_lookback_period': 60,     # 前期高点回看周期（保留）
                # 移除的参数：
                # 'big_yang_min_return': 不再需要大阳线
                # 'big_yang_min_volume_ratio': 不再需要大阳线量比
                # 'volume_ratio_threshold': 不再强制要求放量
                # 'confirmation_days': 不再需要多日确认
            },
            thresholds={
                'min_score': 50.0,              # 降低最低通过分数
                'high_score': 75.0,             # 降低高分阈值
            }
        )
        
        if config:
            # 合并配置
            default_config.params.update(config.params)
            default_config.thresholds.update(config.thresholds)
            default_config.enabled = config.enabled
            default_config.weight = config.weight
            
        super().__init__("GoldenPit", default_config)
        
    def check_conditions(self, data: pd.DataFrame, indicators: pd.DataFrame) -> SelectionResult:
        """
        检查黄金坑条件（简化版）
        
        新逻辑：
        1. 深度回调：从前期高点回调≥20%
        2. 均线突破：当前股价 > 10日均线
        
        Args:
            data: 股票原始数据
            indicators: 技术指标数据
            
        Returns:
            选股结果
        """
        try:
            # 获取配置参数
            drawdown_threshold = self.config.get_param('drawdown_threshold', 0.20)
            ma_period = self.config.get_param('ma_period', 10)
            high_lookback_period = self.config.get_param('high_lookback_period', 60)
            
            # 确保有足够的历史数据
            if len(data) < max(high_lookback_period, ma_period):
                return SelectionResult(
                    symbol="",
                    rule_name=self.name,
                    result=RuleResult.ERROR,
                    details={'reason': 'insufficient_data', 'required': max(high_lookback_period, ma_period)}
                )
            
            # 检查必需的技术指标
            required_indicators = ['ma10', 'high_60', 'drawdown_60']
            missing_indicators = [ind for ind in required_indicators if ind not in indicators.columns]
            if missing_indicators:
                return SelectionResult(
                    symbol="",
                    rule_name=self.name,
                    result=RuleResult.ERROR,
                    details={'reason': 'missing_indicators', 'missing': missing_indicators}
                )
            
            # 获取最新数据
            latest_data = indicators.iloc[-1]
            
            scores = []
            conditions_met = {}
            
            # 条件1: 检查是否存在深度回调（黄金坑的"坑"）
            max_drawdown = indicators['drawdown_60'].min()  # drawdown是负值，min得到最大回调
            drawdown_condition = abs(max_drawdown) >= drawdown_threshold
            conditions_met['drawdown'] = {
                'met': drawdown_condition,
                'value': abs(max_drawdown),
                'threshold': drawdown_threshold
            }
            
            if drawdown_condition:
                # 回调越深，分数越高（权重50%）
                drawdown_score = min(100, 40 + (abs(max_drawdown) - drawdown_threshold) * 200)
                scores.append(drawdown_score)
            else:
                scores.append(0)
            
            # 条件2: 检查是否突破均线（黄金坑的"突破"）
            current_price = latest_data['close']
            ma_value = latest_data[f'ma{ma_period}'] if f'ma{ma_period}' in indicators.columns else latest_data['ma10']
            ma_breakout = current_price > ma_value
            ma_breakout_margin = (current_price - ma_value) / ma_value if ma_value > 0 else 0
            
            conditions_met['ma_breakout'] = {
                'met': ma_breakout,
                'price': current_price,
                'ma_value': ma_value,
                'margin': ma_breakout_margin
            }
            
            if ma_breakout:
                # 突破幅度越大，分数越高（权重50%）
                ma_score = min(100, 50 + ma_breakout_margin * 500)
                scores.append(ma_score)
            else:
                # 接近均线也给一些分数，但不能通过
                closeness = 1 - abs(ma_breakout_margin)
                ma_score = max(0, closeness * 30)
                scores.append(ma_score)
            
            # 综合评分（简化：两个条件等权重）
            final_score = np.mean(scores) if scores else 0
            
            # 确定结果（新逻辑：两个条件都必须满足）
            min_score = self.config.get_threshold('min_score', 50.0)  # 降低最低分数线
            high_score = self.config.get_threshold('high_score', 75.0)  # 降低高分线
            
            # 两个核心条件都满足才能通过
            both_conditions_met = drawdown_condition and ma_breakout
            
            if both_conditions_met and final_score >= high_score:
                result = RuleResult.PASS
                confidence = 0.9
            elif both_conditions_met and final_score >= min_score:
                result = RuleResult.PARTIAL
                confidence = 0.7
            else:
                result = RuleResult.FAIL
                confidence = 0.5
            
            # 构建详细信息
            details = {
                'conditions': conditions_met,
                'scores': {
                    'drawdown_score': scores[0] if len(scores) > 0 else 0,
                    'ma_breakout_score': scores[1] if len(scores) > 1 else 0,
                },
                'final_score': final_score,
                'both_conditions_met': both_conditions_met,
                'thresholds': {
                    'min_score': min_score,
                    'high_score': high_score
                },
                'rule_description': '黄金坑：深度回调≥20%后突破10日均线'
            }
            
            return SelectionResult(
                symbol="",
                rule_name=self.name,
                result=result,
                score=final_score,
                confidence=confidence,
                details=details
            )
            
        except Exception as e:
            self.logger.error(f"黄金坑规则执行异常: {str(e)}")
            return SelectionResult(
                symbol="",
                rule_name=self.name,
                result=RuleResult.ERROR,
                details={'reason': 'execution_error', 'error': str(e)}
            )
    
    def get_rule_description(self) -> Dict[str, Any]:
        """获取规则描述信息（简化版）"""
        return {
            'name': '黄金坑',
            'description': '寻找深度回调后重新站上均线的股票',
            'conditions': [
                f"前期高点回调超过{self.config.get_param('drawdown_threshold', 0.20)*100:.0f}%",
                f"股价重新站上{self.config.get_param('ma_period', 10)}日均线"
            ],
            'logic_type': 'simplified',  # 标识为简化版逻辑
            'parameters': self.config.params,
            'thresholds': self.config.thresholds
        }