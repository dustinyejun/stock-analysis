"""
选股规则引擎模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime


class RuleResult(Enum):
    """规则执行结果枚举"""
    PASS = "pass"        # 通过
    FAIL = "fail"        # 不通过
    PARTIAL = "partial"  # 部分通过
    ERROR = "error"      # 执行错误


@dataclass
class SelectionResult:
    """选股结果数据类"""
    symbol: str
    rule_name: str
    result: RuleResult
    score: float = 0.0
    confidence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'symbol': self.symbol,
            'rule_name': self.rule_name,
            'result': self.result.value,
            'score': self.score,
            'confidence': self.confidence,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass  
class RuleConfig:
    """规则配置数据类"""
    enabled: bool = True
    weight: float = 1.0
    params: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, float] = field(default_factory=dict)
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """获取参数值"""
        return self.params.get(key, default)
    
    def get_threshold(self, key: str, default: float = 0.0) -> float:
        """获取阈值"""
        return self.thresholds.get(key, default)


class BaseSelectionRule(ABC):
    """选股规则基类"""
    
    def __init__(self, name: str, config: Optional[RuleConfig] = None):
        """
        初始化选股规则
        
        Args:
            name: 规则名称
            config: 规则配置
        """
        self.name = name
        self.config = config or RuleConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        self._execution_count = 0
        self._success_count = 0
        self._error_count = 0
    
    @abstractmethod
    def check_conditions(self, data: pd.DataFrame, indicators: pd.DataFrame) -> SelectionResult:
        """
        检查选股条件
        
        Args:
            data: 股票原始数据
            indicators: 技术指标数据
            
        Returns:
            选股结果
        """
        pass
    
    def apply(self, symbol: str, data: pd.DataFrame, indicators: pd.DataFrame) -> SelectionResult:
        """
        应用选股规则
        
        Args:
            symbol: 股票代码
            data: 股票原始数据  
            indicators: 技术指标数据
            
        Returns:
            选股结果
        """
        try:
            self._execution_count += 1
            
            if not self.config.enabled:
                return SelectionResult(
                    symbol=symbol,
                    rule_name=self.name,
                    result=RuleResult.FAIL,
                    details={'reason': 'rule_disabled'}
                )
            
            # 数据有效性检查
            validation_result = self.validate_data(data, indicators)
            if not validation_result['valid']:
                return SelectionResult(
                    symbol=symbol,
                    rule_name=self.name,
                    result=RuleResult.ERROR,
                    details={'reason': 'data_validation_failed', 'errors': validation_result['errors']}
                )
            
            # 执行具体的条件检查
            result = self.check_conditions(data, indicators)
            result.symbol = symbol
            result.rule_name = self.name
            
            if result.result != RuleResult.ERROR:
                self._success_count += 1
            else:
                self._error_count += 1
            
            self.logger.info(f"规则 {self.name} 应用于股票 {symbol}: {result.result.value} (得分: {result.score:.2f})")
            return result
            
        except Exception as e:
            self._error_count += 1
            self.logger.error(f"规则 {self.name} 执行异常: {str(e)}")
            return SelectionResult(
                symbol=symbol,
                rule_name=self.name,
                result=RuleResult.ERROR,
                details={'reason': 'execution_exception', 'error': str(e)}
            )
    
    def validate_data(self, data: pd.DataFrame, indicators: pd.DataFrame) -> Dict[str, Any]:
        """
        验证输入数据的有效性
        
        Args:
            data: 原始股票数据
            indicators: 技术指标数据
            
        Returns:
            验证结果字典
        """
        errors = []
        
        # 检查数据是否为空
        if data.empty:
            errors.append("原始数据为空")
        if indicators.empty:
            errors.append("技术指标数据为空")
            
        # 检查数据长度一致性
        if not data.empty and not indicators.empty and len(data) != len(indicators):
            errors.append(f"数据长度不一致: 原始数据{len(data)}行, 技术指标{len(indicators)}行")
        
        # 检查必需的字段
        required_data_fields = ['open', 'high', 'low', 'close', 'volume']
        missing_data_fields = [field for field in required_data_fields if field not in data.columns]
        if missing_data_fields:
            errors.append(f"原始数据缺少字段: {missing_data_fields}")
            
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取规则执行统计信息"""
        success_rate = self._success_count / self._execution_count if self._execution_count > 0 else 0
        error_rate = self._error_count / self._execution_count if self._execution_count > 0 else 0
        
        return {
            'name': self.name,
            'enabled': self.config.enabled,
            'weight': self.config.weight,
            'execution_count': self._execution_count,
            'success_count': self._success_count,
            'error_count': self._error_count,
            'success_rate': success_rate,
            'error_rate': error_rate
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self._execution_count = 0
        self._success_count = 0
        self._error_count = 0


class RuleRegistry:
    """规则注册表"""
    
    def __init__(self):
        self._rules: Dict[str, BaseSelectionRule] = {}
        self.logger = logging.getLogger(f"{__name__}.RuleRegistry")
    
    def register(self, rule: BaseSelectionRule) -> None:
        """
        注册选股规则
        
        Args:
            rule: 选股规则实例
        """
        if rule.name in self._rules:
            self.logger.warning(f"规则 {rule.name} 已存在，将被覆盖")
        
        self._rules[rule.name] = rule
        self.logger.info(f"注册选股规则: {rule.name}")
    
    def get_rule(self, name: str) -> Optional[BaseSelectionRule]:
        """
        获取指定名称的规则
        
        Args:
            name: 规则名称
            
        Returns:
            规则实例，如果不存在返回None
        """
        return self._rules.get(name)
    
    def list_rules(self) -> List[str]:
        """获取所有注册的规则名称"""
        return list(self._rules.keys())
    
    def get_enabled_rules(self) -> List[BaseSelectionRule]:
        """获取所有启用的规则"""
        return [rule for rule in self._rules.values() if rule.config.enabled]
    
    def remove_rule(self, name: str) -> bool:
        """
        移除指定规则
        
        Args:
            name: 规则名称
            
        Returns:
            是否成功移除
        """
        if name in self._rules:
            del self._rules[name]
            self.logger.info(f"移除选股规则: {name}")
            return True
        return False
    
    def clear(self) -> None:
        """清空所有规则"""
        self._rules.clear()
        self.logger.info("清空所有选股规则")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取所有规则的统计信息"""
        return {
            'total_rules': len(self._rules),
            'enabled_rules': len(self.get_enabled_rules()),
            'rules_stats': [rule.get_statistics() for rule in self._rules.values()]
        }


class RuleEngine:
    """选股规则引擎"""
    
    def __init__(self, registry: Optional[RuleRegistry] = None):
        """
        初始化规则引擎
        
        Args:
            registry: 规则注册表，如果为None则创建新的
        """
        self.registry = registry or RuleRegistry()
        self.logger = logging.getLogger(f"{__name__}.RuleEngine")
        self._execution_history: List[Dict[str, Any]] = []
    
    def add_rule(self, rule: BaseSelectionRule) -> None:
        """添加选股规则"""
        self.registry.register(rule)
    
    def apply_rules(self, symbol: str, data: pd.DataFrame, indicators: pd.DataFrame, 
                   rule_names: Optional[List[str]] = None) -> List[SelectionResult]:
        """
        应用选股规则
        
        Args:
            symbol: 股票代码
            data: 股票原始数据
            indicators: 技术指标数据
            rule_names: 指定要应用的规则名称列表，为None时应用所有启用的规则
            
        Returns:
            选股结果列表
        """
        results = []
        
        # 确定要应用的规则
        if rule_names is None:
            rules_to_apply = self.registry.get_enabled_rules()
        else:
            rules_to_apply = []
            for name in rule_names:
                rule = self.registry.get_rule(name)
                if rule:
                    rules_to_apply.append(rule)
                else:
                    self.logger.warning(f"规则 {name} 不存在")
        
        # 应用规则
        for rule in rules_to_apply:
            result = rule.apply(symbol, data, indicators)
            results.append(result)
        
        # 记录执行历史
        execution_record = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'rules_applied': len(rules_to_apply),
            'results': [result.to_dict() for result in results]
        }
        self._execution_history.append(execution_record)
        
        self.logger.info(f"为股票 {symbol} 应用了 {len(rules_to_apply)} 条规则")
        return results
    
    def calculate_composite_score(self, results: List[SelectionResult]) -> Tuple[float, Dict[str, Any]]:
        """
        计算综合评分
        
        Args:
            results: 选股结果列表
            
        Returns:
            (综合评分, 详细信息)
        """
        if not results:
            return 0.0, {'reason': 'no_results'}
        
        # 过滤掉错误结果
        valid_results = [r for r in results if r.result != RuleResult.ERROR]
        if not valid_results:
            return 0.0, {'reason': 'all_errors'}
        
        # 计算加权平均分数
        total_weight = 0.0
        weighted_score = 0.0
        
        for result in valid_results:
            rule = self.registry.get_rule(result.rule_name)
            if rule:
                weight = rule.config.weight
                # PASS结果使用原始分数，FAIL结果分数为0，PARTIAL结果使用原始分数
                if result.result == RuleResult.FAIL:
                    score = 0.0
                else:
                    score = result.score
                
                weighted_score += score * weight
                total_weight += weight
        
        composite_score = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # 统计各种结果的数量
        pass_count = sum(1 for r in valid_results if r.result == RuleResult.PASS)
        fail_count = sum(1 for r in valid_results if r.result == RuleResult.FAIL)
        partial_count = sum(1 for r in valid_results if r.result == RuleResult.PARTIAL)
        error_count = len(results) - len(valid_results)
        
        details = {
            'composite_score': composite_score,
            'total_rules': len(results),
            'valid_rules': len(valid_results),
            'pass_count': pass_count,
            'fail_count': fail_count,
            'partial_count': partial_count,
            'error_count': error_count,
            'pass_rate': pass_count / len(valid_results) if valid_results else 0.0
        }
        
        return composite_score, details
    
    def get_execution_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取执行历史
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            执行历史记录列表
        """
        if limit is None:
            return self._execution_history.copy()
        else:
            return self._execution_history[-limit:].copy()
    
    def clear_history(self) -> None:
        """清空执行历史"""
        self._execution_history.clear()
        self.logger.info("清空执行历史")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        registry_stats = self.registry.get_statistics()
        
        return {
            'registry': registry_stats,
            'execution_history_count': len(self._execution_history),
        }


# 全局规则注册表和引擎实例
default_registry = RuleRegistry()
default_engine = RuleEngine(default_registry)


if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    print("🧪 选股规则引擎基础框架测试")
    
    # 测试规则注册表
    registry = RuleRegistry()
    print(f"✅ 规则注册表创建成功")
    
    # 测试规则引擎  
    engine = RuleEngine(registry)
    print(f"✅ 规则引擎创建成功")
    
    # 测试数据结构
    config = RuleConfig(
        enabled=True,
        weight=1.5,
        params={'min_return': 0.05, 'min_volume_ratio': 1.3},
        thresholds={'confidence': 0.8}
    )
    print(f"✅ 规则配置创建成功: weight={config.weight}, params={len(config.params)}")
    
    result = SelectionResult(
        symbol="000001",
        rule_name="test_rule",
        result=RuleResult.PASS,
        score=85.5,
        confidence=0.92
    )
    print(f"✅ 选股结果创建成功: {result.symbol} - {result.result.value} (score: {result.score})")
    
    # 测试统计信息
    stats = engine.get_statistics()
    print(f"✅ 统计信息获取成功: {stats['registry']['total_rules']} 条规则")
    
    print("🎉 选股规则引擎基础框架测试完成!")