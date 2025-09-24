"""
数据库锁分析服务
"""
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_

from app.models.lock_analysis import (
    LockEvent, LockWaitChain, LockContention, 
    LockOptimizationTask, LockAnalysisReport
)
from app.schemas.lock_analysis import (
    LockAnalysisRequest, LockDashboardResponse, 
    LockAnalysisSummaryResponse, LockOptimizationScriptResponse
)


class LockAnalyzer:
    """数据库锁分析器"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def analyze_locks_realtime(self, database_id: int) -> Dict[str, Any]:
        """实时锁分析"""
        try:
            # 获取当前锁状态
            current_locks = self._get_current_locks(database_id)
            
            # 分析等待链
            wait_chains = self._analyze_wait_chains(database_id)
            
            # 分析锁竞争
            contentions = self._analyze_lock_contentions(database_id)
            
            # 计算健康评分
            health_score = self._calculate_lock_health_score(current_locks, wait_chains, contentions)
            
            return {
                "database_id": database_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "current_locks": current_locks,
                "wait_chains": wait_chains,
                "contentions": contentions,
                "health_score": health_score,
                "recommendations": self._generate_realtime_recommendations(current_locks, wait_chains, contentions)
            }
        except Exception as e:
            raise Exception(f"实时锁分析失败: {str(e)}")
    
    def analyze_locks_historical(self, database_id: int, hours: int = 24) -> Dict[str, Any]:
        """历史锁分析"""
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            
            # 获取历史锁事件
            lock_events = self._get_historical_lock_events(database_id, start_time)
            
            # 分析锁趋势
            trends = self._analyze_lock_trends(database_id, start_time)
            
            # 分析热点对象
            hot_objects = self._analyze_hot_objects(database_id, start_time)
            
            # 分析死锁和超时
            deadlocks = self._analyze_deadlocks(database_id, start_time)
            timeouts = self._analyze_timeouts(database_id, start_time)
            
            return {
                "database_id": database_id,
                "analysis_period": f"最近{hours}小时",
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "lock_events": lock_events,
                "trends": trends,
                "hot_objects": hot_objects,
                "deadlocks": deadlocks,
                "timeouts": timeouts,
                "summary": self._generate_historical_summary(lock_events, trends, hot_objects)
            }
        except Exception as e:
            raise Exception(f"历史锁分析失败: {str(e)}")
    
    def analyze_wait_chains(self, database_id: int) -> List[Dict[str, Any]]:
        """分析锁等待链"""
        try:
            # 检测当前等待链
            wait_chains = self._detect_wait_chains(database_id)
            
            # 分析等待链严重程度
            analyzed_chains = []
            for chain in wait_chains:
                severity = self._assess_chain_severity(chain)
                suggestions = self._generate_chain_resolution_suggestions(chain)
                
                analyzed_chains.append({
                    **chain,
                    "severity_level": severity,
                    "resolution_suggestions": suggestions
                })
            
            return analyzed_chains
        except Exception as e:
            raise Exception(f"等待链分析失败: {str(e)}")
    
    def analyze_lock_contentions(self, database_id: int) -> List[Dict[str, Any]]:
        """分析锁竞争"""
        try:
            # 获取竞争统计
            contention_stats = self._get_contention_statistics(database_id)
            
            # 分析竞争模式
            analyzed_contentions = []
            for stat in contention_stats:
                pattern = self._identify_contention_pattern(stat)
                root_cause = self._analyze_root_cause(stat)
                suggestions = self._generate_contention_optimization_suggestions(stat, pattern)
                
                analyzed_contentions.append({
                    **stat,
                    "contention_pattern": pattern,
                    "root_cause": root_cause,
                    "optimization_suggestions": suggestions,
                    "priority_level": self._calculate_priority_level(stat, pattern)
                })
            
            return analyzed_contentions
        except Exception as e:
            raise Exception(f"锁竞争分析失败: {str(e)}")
    
    def generate_optimization_suggestions(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成锁优化建议"""
        suggestions = []
        
        # 基于等待链的建议
        if "wait_chains" in analysis_result:
            for chain in analysis_result["wait_chains"]:
                if chain.get("severity_level") in ["high", "critical"]:
                    suggestions.extend(self._generate_wait_chain_suggestions(chain))
        
        # 基于竞争的建议
        if "contentions" in analysis_result:
            for contention in analysis_result["contentions"]:
                if contention.get("priority_level") in ["high", "critical"]:
                    suggestions.extend(self._generate_contention_suggestions(contention))
        
        # 基于整体健康评分的建议
        health_score = analysis_result.get("health_score", 100)
        if health_score < 70:
            suggestions.extend(self._generate_health_based_suggestions(health_score))
        
        return self._prioritize_suggestions(suggestions)
    
    def create_optimization_task(self, database_id: int, task_config: Dict[str, Any]) -> LockOptimizationTask:
        """创建锁优化任务"""
        try:
            task = LockOptimizationTask(
                database_id=database_id,
                task_type=task_config["task_type"],
                task_name=task_config["task_name"],
                description=task_config.get("description"),
                task_config=json.dumps(task_config["task_config"]),
                target_objects=json.dumps(task_config["target_objects"]),
                priority=task_config.get("priority", 1),
                status="pending",
                scheduled_at=datetime.now()
            )
            
            self.session.add(task)
            self.session.commit()
            self.session.refresh(task)
            
            return task
        except Exception as e:
            self.session.rollback()
            raise Exception(f"创建优化任务失败: {str(e)}")
    
    def generate_optimization_script(self, analysis_result: Dict[str, Any], optimization_type: str) -> str:
        """生成锁优化脚本"""
        script_parts = []
        
        if optimization_type == "index_optimization":
            script_parts.append(self._generate_index_optimization_script(analysis_result))
        elif optimization_type == "query_optimization":
            script_parts.append(self._generate_query_optimization_script(analysis_result))
        elif optimization_type == "isolation_level":
            script_parts.append(self._generate_isolation_level_script(analysis_result))
        elif optimization_type == "config_optimization":
            script_parts.append(self._generate_config_optimization_script(analysis_result))
        else:
            script_parts.append(self._generate_comprehensive_optimization_script(analysis_result))
        
        return "\n\n".join(script_parts)
    
    def _get_current_locks(self, database_id: int) -> List[Dict[str, Any]]:
        """获取当前锁状态"""
        # 这里需要根据具体数据库类型实现
        # 对于演示，返回模拟数据
        return [
            {
                "lock_type": "table_lock",
                "lock_mode": "exclusive",
                "object_name": "users",
                "session_id": "12345",
                "wait_duration": 0.0,
                "query_text": "UPDATE users SET status = 'active'"
            },
            {
                "lock_type": "row_lock",
                "lock_mode": "shared",
                "object_name": "orders",
                "session_id": "12346",
                "wait_duration": 2.5,
                "query_text": "SELECT * FROM orders WHERE user_id = 100"
            }
        ]
    
    def _analyze_wait_chains(self, database_id: int) -> List[Dict[str, Any]]:
        """分析等待链"""
        # 模拟等待链分析
        return [
            {
                "chain_id": "chain_001",
                "chain_length": 3,
                "total_wait_time": 15.5,
                "head_session_id": "12345",
                "tail_session_id": "12347",
                "severity_level": "high"
            }
        ]
    
    def _analyze_lock_contentions(self, database_id: int) -> List[Dict[str, Any]]:
        """分析锁竞争"""
        # 模拟竞争分析
        return [
            {
                "object_name": "users",
                "contention_count": 25,
                "total_wait_time": 120.5,
                "avg_wait_time": 4.8,
                "contention_pattern": "hot_spot",
                "priority_level": "high"
            }
        ]
    
    def _calculate_lock_health_score(self, current_locks: List, wait_chains: List, contentions: List) -> float:
        """计算锁健康评分"""
        score = 100.0
        
        # 基于等待链扣分
        for chain in wait_chains:
            if chain.get("severity_level") == "critical":
                score -= 30
            elif chain.get("severity_level") == "high":
                score -= 20
            elif chain.get("severity_level") == "medium":
                score -= 10
        
        # 基于竞争扣分
        for contention in contentions:
            if contention.get("priority_level") == "critical":
                score -= 25
            elif contention.get("priority_level") == "high":
                score -= 15
            elif contention.get("priority_level") == "medium":
                score -= 8
        
        return max(0.0, score)
    
    def _generate_realtime_recommendations(self, current_locks: List, wait_chains: List, contentions: List) -> List[Dict[str, Any]]:
        """生成实时优化建议"""
        recommendations = []
        
        # 基于等待链的建议
        if any(chain.get("severity_level") in ["high", "critical"] for chain in wait_chains):
            recommendations.append({
                "type": "wait_chain_resolution",
                "priority": "high",
                "title": "解决锁等待链",
                "description": "检测到严重的锁等待链，建议立即处理",
                "actions": [
                    "检查阻塞查询的执行计划",
                    "考虑添加适当的索引",
                    "优化查询逻辑减少锁持有时间"
                ]
            })
        
        # 基于竞争的建议
        if any(contention.get("priority_level") in ["high", "critical"] for contention in contentions):
            recommendations.append({
                "type": "contention_optimization",
                "priority": "high",
                "title": "优化锁竞争",
                "description": "检测到严重的锁竞争，影响系统性能",
                "actions": [
                    "分析热点表的访问模式",
                    "考虑分区表或读写分离",
                    "优化事务大小和持续时间"
                ]
            })
        
        return recommendations
    
    def _get_historical_lock_events(self, database_id: int, start_time: datetime) -> List[Dict[str, Any]]:
        """获取历史锁事件"""
        # 模拟历史数据
        return [
            {
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "lock_type": "table_lock",
                "object_name": "products",
                "wait_duration": 5.2,
                "session_id": "12345"
            },
            {
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "lock_type": "row_lock",
                "object_name": "orders",
                "wait_duration": 3.8,
                "session_id": "12346"
            }
        ]
    
    def _analyze_lock_trends(self, database_id: int, start_time: datetime) -> Dict[str, Any]:
        """分析锁趋势"""
        return {
            "wait_time_trend": "increasing",
            "contention_frequency": "stable",
            "deadlock_frequency": "decreasing",
            "peak_hours": ["09:00-11:00", "14:00-16:00"]
        }
    
    def _analyze_hot_objects(self, database_id: int, start_time: datetime) -> List[Dict[str, Any]]:
        """分析热点对象"""
        return [
            {
                "object_name": "users",
                "contention_count": 45,
                "total_wait_time": 180.5,
                "avg_wait_time": 4.0,
                "rank": 1
            },
            {
                "object_name": "orders",
                "contention_count": 32,
                "total_wait_time": 120.3,
                "avg_wait_time": 3.8,
                "rank": 2
            }
        ]
    
    def _analyze_deadlocks(self, database_id: int, start_time: datetime) -> List[Dict[str, Any]]:
        """分析死锁"""
        return [
            {
                "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
                "involved_sessions": ["12345", "12346"],
                "involved_objects": ["users", "orders"],
                "resolution_time": 2.5
            }
        ]
    
    def _analyze_timeouts(self, database_id: int, start_time: datetime) -> List[Dict[str, Any]]:
        """分析超时"""
        return [
            {
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "session_id": "12347",
                "object_name": "products",
                "timeout_duration": 30.0
            }
        ]
    
    def _generate_historical_summary(self, lock_events: List, trends: Dict, hot_objects: List) -> Dict[str, Any]:
        """生成历史分析总结"""
        return {
            "total_events": len(lock_events),
            "avg_wait_time": sum(event.get("wait_duration", 0) for event in lock_events) / max(len(lock_events), 1),
            "trend_analysis": trends,
            "top_hot_objects": hot_objects[:5],
            "health_assessment": "需要关注" if len(hot_objects) > 3 else "良好"
        }
    
    def _detect_wait_chains(self, database_id: int) -> List[Dict[str, Any]]:
        """检测等待链"""
        # 模拟等待链检测
        return [
            {
                "chain_id": "chain_001",
                "chain_length": 3,
                "total_wait_time": 15.5,
                "head_session_id": "12345",
                "tail_session_id": "12347",
                "involved_objects": ["users", "orders", "products"]
            }
        ]
    
    def _assess_chain_severity(self, chain: Dict[str, Any]) -> str:
        """评估等待链严重程度"""
        chain_length = chain.get("chain_length", 0)
        total_wait_time = chain.get("total_wait_time", 0)
        
        if chain_length >= 5 or total_wait_time >= 30:
            return "critical"
        elif chain_length >= 3 or total_wait_time >= 15:
            return "high"
        elif chain_length >= 2 or total_wait_time >= 5:
            return "medium"
        else:
            return "low"
    
    def _generate_chain_resolution_suggestions(self, chain: Dict[str, Any]) -> List[str]:
        """生成等待链解决建议"""
        suggestions = []
        
        if chain.get("chain_length", 0) > 3:
            suggestions.append("等待链过长，建议检查事务设计，减少嵌套事务")
        
        if chain.get("total_wait_time", 0) > 20:
            suggestions.append("等待时间过长，建议优化查询性能或调整锁超时设置")
        
        suggestions.extend([
            "检查相关表的索引设计",
            "考虑使用更细粒度的锁",
            "优化查询执行顺序"
        ])
        
        return suggestions
    
    def _get_contention_statistics(self, database_id: int) -> List[Dict[str, Any]]:
        """获取竞争统计"""
        return [
            {
                "object_name": "users",
                "contention_count": 25,
                "total_wait_time": 120.5,
                "avg_wait_time": 4.8,
                "max_wait_time": 15.2,
                "affected_sessions": 8
            }
        ]
    
    def _identify_contention_pattern(self, stat: Dict[str, Any]) -> str:
        """识别竞争模式"""
        contention_count = stat.get("contention_count", 0)
        avg_wait_time = stat.get("avg_wait_time", 0)
        
        if contention_count > 50 and avg_wait_time > 10:
            return "hot_spot"
        elif avg_wait_time > 20:
            return "timeout_prone"
        elif contention_count > 30:
            return "frequent_contention"
        else:
            return "normal"
    
    def _analyze_root_cause(self, stat: Dict[str, Any]) -> str:
        """分析根本原因"""
        avg_wait_time = stat.get("avg_wait_time", 0)
        contention_count = stat.get("contention_count", 0)
        
        if avg_wait_time > 10:
            return "查询性能问题，缺少适当索引或查询优化不足"
        elif contention_count > 40:
            return "并发访问过于频繁，需要优化业务逻辑或考虑读写分离"
        else:
            return "正常的锁竞争，建议持续监控"
    
    def _generate_contention_optimization_suggestions(self, stat: Dict[str, Any], pattern: str) -> List[str]:
        """生成竞争优化建议"""
        suggestions = []
        
        if pattern == "hot_spot":
            suggestions.extend([
                "考虑对热点表进行分区",
                "实现读写分离架构",
                "优化业务逻辑减少对同一资源的并发访问"
            ])
        elif pattern == "timeout_prone":
            suggestions.extend([
                "增加锁超时时间",
                "优化查询性能减少锁持有时间",
                "检查是否有长时间运行的事务"
            ])
        elif pattern == "frequent_contention":
            suggestions.extend([
                "添加适当的索引",
                "优化查询执行计划",
                "考虑使用更细粒度的锁"
            ])
        
        return suggestions
    
    def _calculate_priority_level(self, stat: Dict[str, Any], pattern: str) -> str:
        """计算优先级"""
        if pattern in ["hot_spot", "timeout_prone"]:
            return "critical"
        elif pattern == "frequent_contention":
            return "high"
        else:
            return "medium"
    
    def _generate_wait_chain_suggestions(self, chain: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成等待链优化建议"""
        return [
            {
                "type": "wait_chain_optimization",
                "priority": "high",
                "title": f"优化等待链 {chain.get('chain_id')}",
                "description": f"等待链长度: {chain.get('chain_length')}, 总等待时间: {chain.get('total_wait_time')}秒",
                "actions": [
                    "检查事务设计，减少嵌套事务",
                    "优化查询性能",
                    "考虑使用乐观锁替代悲观锁"
                ]
            }
        ]
    
    def _generate_contention_suggestions(self, contention: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成竞争优化建议"""
        return [
            {
                "type": "contention_optimization",
                "priority": contention.get("priority_level", "medium"),
                "title": f"优化 {contention.get('object_name')} 表的锁竞争",
                "description": f"竞争次数: {contention.get('contention_count')}, 平均等待时间: {contention.get('avg_wait_time')}秒",
                "actions": [
                    "添加适当的索引",
                    "优化查询执行计划",
                    "考虑表分区或读写分离"
                ]
            }
        ]
    
    def _generate_health_based_suggestions(self, health_score: float) -> List[Dict[str, Any]]:
        """基于健康评分生成建议"""
        if health_score < 50:
            return [
                {
                    "type": "system_optimization",
                    "priority": "critical",
                    "title": "系统锁性能严重问题",
                    "description": f"当前锁健康评分: {health_score:.1f}，需要立即处理",
                    "actions": [
                        "全面检查锁配置",
                        "优化所有慢查询",
                        "考虑系统架构调整"
                    ]
                }
            ]
        elif health_score < 70:
            return [
                {
                    "type": "system_optimization",
                    "priority": "high",
                    "title": "系统锁性能需要优化",
                    "description": f"当前锁健康评分: {health_score:.1f}，建议优化",
                    "actions": [
                        "检查主要性能瓶颈",
                        "优化高竞争对象",
                        "调整锁相关配置"
                    ]
                }
            ]
        return []
    
    def _prioritize_suggestions(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对建议进行优先级排序"""
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(suggestions, key=lambda x: priority_order.get(x.get("priority", "low"), 3))
    
    def _generate_index_optimization_script(self, analysis_result: Dict[str, Any]) -> str:
        """生成索引优化脚本"""
        script = "-- 锁优化脚本 - 索引优化\n"
        script += "-- 生成时间: " + datetime.now().isoformat() + "\n\n"
        
        # 基于分析结果生成索引建议
        if "hot_objects" in analysis_result:
            for obj in analysis_result["hot_objects"][:3]:  # 前3个热点对象
                script += f"-- 为热点表 {obj['object_name']} 创建索引\n"
                script += f"CREATE INDEX idx_{obj['object_name']}_optimization ON {obj['object_name']}(id, created_at);\n\n"
        
        return script
    
    def _generate_query_optimization_script(self, analysis_result: Dict[str, Any]) -> str:
        """生成查询优化脚本"""
        script = "-- 锁优化脚本 - 查询优化\n"
        script += "-- 生成时间: " + datetime.now().isoformat() + "\n\n"
        
        script += "-- 优化建议:\n"
        script += "-- 1. 减少锁持有时间\n"
        script += "-- 2. 优化查询条件\n"
        script += "-- 3. 使用适当的隔离级别\n\n"
        
        return script
    
    def _generate_isolation_level_script(self, analysis_result: Dict[str, Any]) -> str:
        """生成隔离级别优化脚本"""
        script = "-- 锁优化脚本 - 隔离级别优化\n"
        script += "-- 生成时间: " + datetime.now().isoformat() + "\n\n"
        
        script += "-- 设置合适的隔离级别\n"
        script += "SET TRANSACTION ISOLATION LEVEL READ COMMITTED;\n\n"
        
        return script
    
    def _generate_config_optimization_script(self, analysis_result: Dict[str, Any]) -> str:
        """生成配置优化脚本"""
        script = "-- 锁优化脚本 - 配置优化\n"
        script += "-- 生成时间: " + datetime.now().isoformat() + "\n\n"
        
        script += "-- 锁相关配置优化\n"
        script += "-- innodb_lock_wait_timeout = 50\n"
        script += "-- innodb_deadlock_detect = ON\n"
        script += "-- innodb_print_all_deadlocks = ON\n\n"
        
        return script
    
    def _generate_comprehensive_optimization_script(self, analysis_result: Dict[str, Any]) -> str:
        """生成综合优化脚本"""
        script = "-- 锁优化脚本 - 综合优化\n"
        script += "-- 生成时间: " + datetime.now().isoformat() + "\n\n"
        
        # 组合所有优化建议
        script += self._generate_index_optimization_script(analysis_result)
        script += self._generate_query_optimization_script(analysis_result)
        script += self._generate_isolation_level_script(analysis_result)
        script += self._generate_config_optimization_script(analysis_result)
        
        return script