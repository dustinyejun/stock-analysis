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
    黄金坑选股规则
    
    黄金坑特征：
    1. 股价从前期高点回撤超过20%
    2. 出现大阳线（单日涨幅>=5%，量比>=1.5）
    3. 股价突破10日均线
    4. 成交量放大（量比>=1.3）
    """
    
    def __init__(self, config: RuleConfig = None):
        """
        初始化黄金坑规则
        
        Args:
            config: 规则配置
        """
        default_config = RuleConfig(
            enabled=True,
            weight=1.0,
            params={
                'drawdown_threshold': 0.20,      # 回撤阈值
                'big_yang_min_return': 0.05,     # 大阳线最小涨幅
                'big_yang_min_volume_ratio': 1.5, # 大阳线最小量比
                'ma_period': 10,                  # 均线周期
                'volume_ratio_threshold': 1.3,   # 放量阈值
                'high_lookback_period': 60,      # 前期高点回看周期
                'confirmation_days': 3,          # 确认天数
            },
            thresholds={
                'min_score': 60.0,              # 最低通过分数
                'high_score': 85.0,             # 高分阈值
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
        检查黄金坑条件
        
        Args:
            data: 股票原始数据
            indicators: 技术指标数据
            
        Returns:
            选股结果
        """
        try:
            # 获取配置参数
            drawdown_threshold = self.config.get_param('drawdown_threshold', 0.20)
            big_yang_min_return = self.config.get_param('big_yang_min_return', 0.05)
            big_yang_min_volume_ratio = self.config.get_param('big_yang_min_volume_ratio', 1.5)
            ma_period = self.config.get_param('ma_period', 10)
            volume_ratio_threshold = self.config.get_param('volume_ratio_threshold', 1.3)
            high_lookback_period = self.config.get_param('high_lookback_period', 60)
            confirmation_days = self.config.get_param('confirmation_days', 3)
            
            # 确保有足够的历史数据
            if len(data) < max(high_lookback_period, ma_period, confirmation_days):
                return SelectionResult(
                    symbol="",
                    rule_name=self.name,
                    result=RuleResult.ERROR,
                    details={'reason': 'insufficient_data', 'required': max(high_lookback_period, ma_period)}
                )
            
            # 检查必需的技术指标
            required_indicators = ['ma10', 'volume_ratio_5', 'daily_return', 'big_yang', 'high_60', 'drawdown_60']
            missing_indicators = [ind for ind in required_indicators if ind not in indicators.columns]
            if missing_indicators:
                return SelectionResult(
                    symbol="",
                    rule_name=self.name,
                    result=RuleResult.ERROR,
                    details={'reason': 'missing_indicators', 'missing': missing_indicators}
                )
            
            # 获取最近几天的数据用于判断
            recent_data = indicators.tail(confirmation_days)
            latest_data = indicators.iloc[-1]
            
            scores = []
            conditions_met = {}
            
            # 条件1: 检查是否存在大幅回撤（黄金坑的"坑"）
            max_drawdown = indicators['drawdown_60'].min()  # drawdown是负值，min得到最大回撤
            drawdown_condition = abs(max_drawdown) >= drawdown_threshold
            conditions_met['drawdown'] = {
                'met': drawdown_condition,
                'value': abs(max_drawdown),
                'threshold': drawdown_threshold
            }
            
            if drawdown_condition:
                # 回撤越深，分数越高（但有上限）
                drawdown_score = min(100, 50 + (abs(max_drawdown) - drawdown_threshold) * 200)
                scores.append(drawdown_score)
            else:
                scores.append(0)
            
            # 条件2: 检查是否出现大阳线（黄金坑的"反转"）
            big_yang_days = recent_data['big_yang'].sum()
            big_yang_condition = big_yang_days > 0
            conditions_met['big_yang'] = {
                'met': big_yang_condition,
                'days': int(big_yang_days),
                'recent_days': confirmation_days
            }
            
            if big_yang_condition:
                # 大阳线天数越多，分数越高
                big_yang_score = min(100, 60 + big_yang_days * 15)
                scores.append(big_yang_score)
            else:
                scores.append(0)
            
            # 条件3: 检查是否突破均线（黄金坑的"突破"）
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
                # 突破幅度越大，分数越高
                ma_score = min(100, 70 + ma_breakout_margin * 300)
                scores.append(ma_score)
            else:
                # 接近均线也给一些分数
                closeness = 1 - abs(ma_breakout_margin)
                ma_score = max(0, closeness * 50)
                scores.append(ma_score)
            
            # 条件4: 检查放量情况（确认资金关注）
            recent_volume_ratio = recent_data['volume_ratio_5'].mean()
            volume_condition = recent_volume_ratio >= volume_ratio_threshold
            conditions_met['volume_expansion'] = {
                'met': volume_condition,
                'ratio': recent_volume_ratio,
                'threshold': volume_ratio_threshold
            }
            
            if volume_condition:
                # 量比越高，分数越高
                volume_score = min(100, 50 + (recent_volume_ratio - volume_ratio_threshold) * 50)
                scores.append(volume_score)
            else:
                # 即使没有放量，也给一定基础分
                volume_score = max(0, recent_volume_ratio / volume_ratio_threshold * 40)
                scores.append(volume_score)
            
            # 综合评分
            final_score = np.mean(scores) if scores else 0
            
            # 确定结果
            min_score = self.config.get_threshold('min_score', 60.0)
            high_score = self.config.get_threshold('high_score', 85.0)
            
            if final_score >= high_score:
                result = RuleResult.PASS
                confidence = 0.9
            elif final_score >= min_score:
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
                    'big_yang_score': scores[1] if len(scores) > 1 else 0,
                    'ma_breakout_score': scores[2] if len(scores) > 2 else 0,
                    'volume_score': scores[3] if len(scores) > 3 else 0,
                },
                'final_score': final_score,
                'thresholds': {
                    'min_score': min_score,
                    'high_score': high_score
                },
                'rule_description': '黄金坑：深度回撤后出现大阳线突破均线放量'
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
        """获取规则描述信息"""
        return {
            'name': '黄金坑',
            'description': '寻找深度回撤后反转突破的股票',
            'conditions': [
                f"前期高点回撤超过{self.config.get_param('drawdown_threshold', 0.20)*100:.0f}%",
                f"出现大阳线（涨幅>={self.config.get_param('big_yang_min_return', 0.05)*100:.0f}%，量比>={self.config.get_param('big_yang_min_volume_ratio', 1.5)}）",
                f"突破{self.config.get_param('ma_period', 10)}日均线",
                f"成交量放大（量比>={self.config.get_param('volume_ratio_threshold', 1.3)}）"
            ],
            'parameters': self.config.params,
            'thresholds': self.config.thresholds
        }