"""
趋势突破选股规则实现（升级版）
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

from ..selection_rules import BaseSelectionRule, SelectionResult, RuleResult, RuleConfig


class TrendBreakoutRule(BaseSelectionRule):
    """
    趋势突破选股规则（升级版）
    
    升级后的趋势突破特征：
    1. 多头趋势确立：均线多头排列（MA5>MA10>MA20>MA60）且股价>MA5
    2. 连续倍量突破：连续2天每天成交量>5日均量×2倍
    3. 大震幅阳线：连续2天震幅>7%且为阳线
    4. 突破8个月高点：收盘价>240个交易日内最高价
    
    升级说明：
    - 提高成交量标准：从1.3倍提升到2倍（真正的倍量）
    - 增加震幅要求：新增7%日内震幅确认强势
    - 延长高点周期：从60天延长到240天（8个月）
    - 简化趋势判断：改为直观的均线多头排列
    - 提高评分标准：70/90分通过线，确保选股质量
    """
    
    def __init__(self, config: RuleConfig = None):
        """
        初始化趋势突破规则（升级版）
        
        Args:
            config: 规则配置
        """
        default_config = RuleConfig(
            enabled=True,
            weight=1.0,
            params={
                'ma_periods': [5, 10, 20, 60],          # 多均线周期
                'volume_ratio_threshold': 2.0,          # 倍量标准（提高到2倍）
                'amplitude_threshold': 0.07,            # 日内震幅要求7%
                'consecutive_days': 2,                  # 连续天数要求
                'high_lookback_period': 240,            # 8个月高点（240交易日）
                'yang_required': True,                  # 必须阳线
                'breakout_confirmation': 0.001,         # 突破确认0.1%
            },
            thresholds={
                'min_score': 70.0,                      # 提高最低通过分数
                'high_score': 90.0,                     # 提高高分阈值
            }
        )
        
        if config:
            # 合并配置
            default_config.params.update(config.params)
            default_config.thresholds.update(config.thresholds)
            default_config.enabled = config.enabled
            default_config.weight = config.weight
            
        super().__init__("TrendBreakout", default_config)
        
    def check_conditions(self, data: pd.DataFrame, indicators: pd.DataFrame) -> SelectionResult:
        """
        检查趋势突破条件（升级版）
        
        新逻辑：
        1. 多头趋势：均线多头排列且股价>MA5
        2. 连续倍量：连续2天每天成交量>5日均量×2倍  
        3. 大震幅阳线：连续2天震幅>7%且为阳线
        4. 突破8个月高点：收盘价>240日内最高价
        
        Args:
            data: 股票原始数据
            indicators: 技术指标数据
            
        Returns:
            选股结果
        """
        try:
            # 获取升级后的配置参数
            ma_periods = self.config.get_param('ma_periods', [5, 10, 20, 60])
            volume_ratio = self.config.get_param('volume_ratio_threshold', 2.0)
            amplitude_threshold = self.config.get_param('amplitude_threshold', 0.07)
            consecutive_days = self.config.get_param('consecutive_days', 2)
            lookback_days = self.config.get_param('high_lookback_period', 240)
            yang_required = self.config.get_param('yang_required', True)
            breakout_confirmation = self.config.get_param('breakout_confirmation', 0.001)
            
            # 确保有足够的历史数据
            required_data_length = max(lookback_days, max(ma_periods) if ma_periods else 60)
            if len(data) < required_data_length:
                return SelectionResult(
                    symbol="",
                    rule_name=self.name,
                    result=RuleResult.ERROR,
                    details={'reason': 'insufficient_data', 'required': required_data_length}
                )
            
            # 检查必需的技术指标
            required_indicators = [
                'ma_bullish_alignment', 'consecutive_volume_expansion', 
                'consecutive_amplitude', 'consecutive_yang', 'high_240', 'close'
            ]
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
            
            # 条件1: 多头趋势确认（简化判断）
            bullish_trend = latest_data.get('ma_bullish_alignment', False)
            conditions_met['bullish_trend'] = {
                'met': bullish_trend,
                'description': '均线多头排列且股价>MA5',
                'ma_periods': ma_periods
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
                'days_required': consecutive_days,
                'description': f'连续{consecutive_days}天倍量（>{volume_ratio}倍五日均量）'
            }
            
            if consecutive_volume:
                scores.append(90)
            else:
                scores.append(0)
            
            # 条件3: 连续大震幅阳线
            consecutive_amp = latest_data.get('consecutive_amplitude', False)
            consecutive_yang = latest_data.get('consecutive_yang', False) if yang_required else True
            amp_yang_condition = consecutive_amp and consecutive_yang
            
            conditions_met['amplitude_yang'] = {
                'met': amp_yang_condition,
                'amplitude_threshold': amplitude_threshold,
                'consecutive_amplitude': consecutive_amp,
                'consecutive_yang': consecutive_yang,
                'yang_required': yang_required,
                'description': f'连续{consecutive_days}天震幅>{amplitude_threshold*100}%且为阳线'
            }
            
            if amp_yang_condition:
                scores.append(90)
            else:
                scores.append(0)
            
            # 条件4: 突破8个月高点
            current_price = latest_data['close']
            high_240 = latest_data.get('high_240', 0)
            breakout_threshold = high_240 * (1 + breakout_confirmation)
            breakout_condition = current_price > breakout_threshold
            
            # 计算突破强度
            if high_240 > 0:
                breakout_strength = (current_price - high_240) / high_240
            else:
                breakout_strength = 0
            
            conditions_met['breakout_240'] = {
                'met': breakout_condition,
                'current_price': current_price,
                'high_240': high_240,
                'breakout_threshold': breakout_threshold,
                'breakout_strength': breakout_strength,
                'lookback_days': lookback_days,
                'description': f'突破{lookback_days}个交易日内最高价'
            }
            
            if breakout_condition:
                # 突破幅度越大分数越高
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
            
            # 构建详细信息
            details = {
                'conditions': conditions_met,
                'scores': {
                    'bullish_trend_score': scores[0] if len(scores) > 0 else 0,
                    'consecutive_volume_score': scores[1] if len(scores) > 1 else 0,
                    'amplitude_yang_score': scores[2] if len(scores) > 2 else 0,
                    'breakout_240_score': scores[3] if len(scores) > 3 else 0,
                },
                'final_score': final_score,
                'all_conditions_met': all_conditions_met,
                'thresholds': {
                    'min_score': min_score,
                    'high_score': high_score
                },
                'rule_description': '趋势突破（升级版）：多头趋势中连续倍量大震幅突破8个月高点',
                'upgrade_features': [
                    f'倍量标准提高到{volume_ratio}倍',
                    f'震幅要求{amplitude_threshold*100}%',
                    f'突破{lookback_days}日高点',
                    '均线多头排列简化判断'
                ]
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
            self.logger.error(f"趋势突破规则（升级版）执行异常: {str(e)}")
            return SelectionResult(
                symbol="",
                rule_name=self.name,
                result=RuleResult.ERROR,
                details={'reason': 'execution_error', 'error': str(e)}
            )
    
    def get_rule_description(self) -> Dict[str, Any]:
        """获取规则描述信息（升级版）"""
        ma_periods = self.config.get_param('ma_periods', [5, 10, 20, 60])
        volume_ratio = self.config.get_param('volume_ratio_threshold', 2.0)
        amplitude_threshold = self.config.get_param('amplitude_threshold', 0.07)
        consecutive_days = self.config.get_param('consecutive_days', 2)
        lookback_days = self.config.get_param('high_lookback_period', 240)
        
        return {
            'name': '趋势突破（升级版）',
            'description': '多头趋势中连续倍量大震幅突破8个月高点的强势股票',
            'version': 'enhanced',
            'conditions': [
                f"均线多头排列（MA{ma_periods[0]}>MA{ma_periods[1]}>MA{ma_periods[2]}>MA{ma_periods[3]}）且股价>MA{ma_periods[0]}",
                f"连续{consecutive_days}天倍量（每天>{volume_ratio}倍五日均量）",
                f"连续{consecutive_days}天大震幅阳线（震幅>{amplitude_threshold*100}%）",
                f"突破{lookback_days}个交易日内最高价"
            ],
            'key_improvements': [
                '成交量标准从1.3倍提升到2倍',
                '新增7%日内震幅要求',
                '高点回望从60天延长到240天',
                '简化多头趋势判断逻辑',
                '提高通过分数线到70/90分'
            ],
            'parameters': self.config.params,
            'thresholds': self.config.thresholds,
            'suitable_for': [
                '强势股捕捉',
                '重要技术突破',
                '中短期趋势跟随',
                '经典技术形态识别'
            ]
        }