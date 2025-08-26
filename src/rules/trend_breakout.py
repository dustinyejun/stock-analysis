"""
趋势突破选股规则实现  
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

from ..selection_rules import BaseSelectionRule, SelectionResult, RuleResult, RuleConfig


class TrendBreakoutRule(BaseSelectionRule):
    """
    趋势突破选股规则
    
    趋势突破特征：
    1. 多头趋势确立（短期均线>长期均线，股价>短期均线）
    2. 连续放量（量比持续>1.3，持续2天以上）
    3. 突破前期高点
    4. 价格和成交量都呈现上升趋势
    """
    
    def __init__(self, config: RuleConfig = None):
        """
        初始化趋势突破规则
        
        Args:
            config: 规则配置
        """
        default_config = RuleConfig(
            enabled=True,
            weight=1.0,
            params={
                'short_ma_period': 20,           # 短期均线周期
                'long_ma_period': 60,            # 长期均线周期  
                'volume_ratio_threshold': 1.3,   # 放量阈值
                'volume_expansion_days': 2,      # 持续放量天数
                'high_breakout_period': 60,      # 前期高点周期
                'breakout_margin': 0.01,         # 突破确认幅度（1%）
                'trend_confirmation_days': 3,    # 趋势确认天数
                'min_price_rise': 0.02,          # 最小价格涨幅（2%）
            },
            thresholds={
                'min_score': 65.0,              # 最低通过分数
                'high_score': 88.0,             # 高分阈值
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
        检查趋势突破条件
        
        Args:
            data: 股票原始数据
            indicators: 技术指标数据
            
        Returns:
            选股结果
        """
        try:
            # 获取配置参数
            short_ma_period = self.config.get_param('short_ma_period', 20)
            long_ma_period = self.config.get_param('long_ma_period', 60)
            volume_ratio_threshold = self.config.get_param('volume_ratio_threshold', 1.3)
            volume_expansion_days = self.config.get_param('volume_expansion_days', 2)
            high_breakout_period = self.config.get_param('high_breakout_period', 60)
            breakout_margin = self.config.get_param('breakout_margin', 0.01)
            trend_confirmation_days = self.config.get_param('trend_confirmation_days', 3)
            min_price_rise = self.config.get_param('min_price_rise', 0.02)
            
            # 确保有足够的历史数据
            required_data_length = max(long_ma_period, high_breakout_period, trend_confirmation_days)
            if len(data) < required_data_length:
                return SelectionResult(
                    symbol="",
                    rule_name=self.name,
                    result=RuleResult.ERROR,
                    details={'reason': 'insufficient_data', 'required': required_data_length}
                )
            
            # 检查必需的技术指标
            required_indicators = ['ma20', 'ma60', 'close', 'bullish_trend', 'volume_expansion', 'high_60', 'volume_ratio_5']
            missing_indicators = [ind for ind in required_indicators if ind not in indicators.columns]
            if missing_indicators:
                return SelectionResult(
                    symbol="",
                    rule_name=self.name,
                    result=RuleResult.ERROR,
                    details={'reason': 'missing_indicators', 'missing': missing_indicators}
                )
            
            # 获取最近几天的数据用于判断
            recent_data = indicators.tail(trend_confirmation_days)
            latest_data = indicators.iloc[-1]
            
            scores = []
            conditions_met = {}
            
            # 条件1: 检查多头趋势
            bullish_trend_days = recent_data['bullish_trend'].sum()
            trend_strength = bullish_trend_days / len(recent_data)  # 趋势强度（0-1）
            bullish_condition = trend_strength >= 0.67  # 至少2/3的时间在多头趋势
            
            conditions_met['bullish_trend'] = {
                'met': bullish_condition,
                'strength': trend_strength,
                'days': int(bullish_trend_days),
                'total_days': len(recent_data)
            }
            
            if bullish_condition:
                # 趋势强度越高，分数越高
                trend_score = 60 + trend_strength * 40
                scores.append(trend_score)
            else:
                # 部分趋势也给一些分数
                trend_score = trend_strength * 50
                scores.append(trend_score)
            
            # 条件2: 检查持续放量
            volume_expansion_days_count = recent_data['volume_expansion'].sum()
            volume_condition = volume_expansion_days_count >= volume_expansion_days
            avg_volume_ratio = recent_data['volume_ratio_5'].mean()
            
            conditions_met['volume_expansion'] = {
                'met': volume_condition,
                'days': int(volume_expansion_days_count),
                'required_days': volume_expansion_days,
                'avg_volume_ratio': avg_volume_ratio,
                'threshold': volume_ratio_threshold
            }
            
            if volume_condition:
                # 放量天数越多，量比越高，分数越高
                volume_score = 50 + (volume_expansion_days_count / len(recent_data)) * 30 + \
                              min((avg_volume_ratio - volume_ratio_threshold) * 20, 20)
                scores.append(volume_score)
            else:
                # 即使放量天数不够，量比高也给分
                volume_score = max(0, min(avg_volume_ratio / volume_ratio_threshold * 40, 40))
                scores.append(volume_score)
            
            # 条件3: 检查是否突破前期高点
            current_price = latest_data['close']
            period_high = latest_data['high_60']  # 60日最高价
            breakout_threshold = period_high * (1 + breakout_margin)
            breakout_condition = current_price >= breakout_threshold
            
            # 计算突破强度
            if period_high > 0:
                breakout_strength = (current_price - period_high) / period_high
            else:
                breakout_strength = 0
            
            conditions_met['high_breakout'] = {
                'met': breakout_condition,
                'current_price': current_price,
                'period_high': period_high,
                'breakout_strength': breakout_strength,
                'required_margin': breakout_margin
            }
            
            if breakout_condition:
                # 突破幅度越大，分数越高
                breakout_score = 70 + min(breakout_strength * 200, 30)
                scores.append(breakout_score)
            else:
                # 接近前期高点也给分
                closeness = current_price / period_high if period_high > 0 else 0
                breakout_score = max(0, (closeness - 0.9) * 500)  # 90%以上给分
                scores.append(breakout_score)
            
            # 条件4: 检查价格上升趋势
            price_changes = recent_data['daily_return'].dropna()
            positive_days = (price_changes > 0).sum()
            avg_return = price_changes.mean()
            cumulative_return = (1 + price_changes).prod() - 1
            
            price_trend_condition = cumulative_return >= min_price_rise
            
            conditions_met['price_trend'] = {
                'met': price_trend_condition,
                'positive_days': int(positive_days),
                'total_days': len(price_changes),
                'avg_daily_return': avg_return,
                'cumulative_return': cumulative_return,
                'required_return': min_price_rise
            }
            
            if price_trend_condition:
                # 涨幅越大，上涨天数比例越高，分数越高
                positive_ratio = positive_days / len(price_changes) if len(price_changes) > 0 else 0
                price_score = 50 + min(cumulative_return * 100, 30) + positive_ratio * 20
                scores.append(price_score)
            else:
                # 即使整体没涨够，单日表现好也给分
                price_score = max(0, min((cumulative_return + min_price_rise) * 50 / min_price_rise, 40))
                scores.append(price_score)
            
            # 额外加分项：RSI适中（不超买）
            if 'rsi' in indicators.columns:
                current_rsi = latest_data['rsi']
                if 30 <= current_rsi <= 70:  # RSI在合理范围
                    rsi_bonus = 10
                elif 70 < current_rsi <= 80:  # 略微超买，减少加分
                    rsi_bonus = 5
                else:
                    rsi_bonus = 0
            else:
                rsi_bonus = 0
            
            # 综合评分
            base_score = np.mean(scores) if scores else 0
            final_score = min(100, base_score + rsi_bonus)
            
            # 确定结果
            min_score = self.config.get_threshold('min_score', 65.0)
            high_score = self.config.get_threshold('high_score', 88.0)
            
            if final_score >= high_score:
                result = RuleResult.PASS
                confidence = 0.95
            elif final_score >= min_score:
                result = RuleResult.PARTIAL
                confidence = 0.75
            else:
                result = RuleResult.FAIL
                confidence = 0.55
            
            # 构建详细信息
            details = {
                'conditions': conditions_met,
                'scores': {
                    'trend_score': scores[0] if len(scores) > 0 else 0,
                    'volume_score': scores[1] if len(scores) > 1 else 0,
                    'breakout_score': scores[2] if len(scores) > 2 else 0,
                    'price_trend_score': scores[3] if len(scores) > 3 else 0,
                    'rsi_bonus': rsi_bonus,
                },
                'base_score': base_score,
                'final_score': final_score,
                'thresholds': {
                    'min_score': min_score,
                    'high_score': high_score
                },
                'rule_description': '趋势突破：多头趋势中放量突破前期高点'
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
            self.logger.error(f"趋势突破规则执行异常: {str(e)}")
            return SelectionResult(
                symbol="",
                rule_name=self.name,
                result=RuleResult.ERROR,
                details={'reason': 'execution_error', 'error': str(e)}
            )
    
    def get_rule_description(self) -> Dict[str, Any]:
        """获取规则描述信息"""
        return {
            'name': '趋势突破',
            'description': '寻找多头趋势中放量突破前期高点的股票',
            'conditions': [
                f"多头趋势（{self.config.get_param('short_ma_period', 20)}日MA > {self.config.get_param('long_ma_period', 60)}日MA，股价 > 短期MA）",
                f"连续放量（量比>={self.config.get_param('volume_ratio_threshold', 1.3)}，持续{self.config.get_param('volume_expansion_days', 2)}天以上）",
                f"突破{self.config.get_param('high_breakout_period', 60)}日内前期高点",
                f"价格上升趋势（近{self.config.get_param('trend_confirmation_days', 3)}日累计涨幅>={self.config.get_param('min_price_rise', 0.02)*100:.0f}%）"
            ],
            'parameters': self.config.params,
            'thresholds': self.config.thresholds
        }