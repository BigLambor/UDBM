"""
OceanBase 配置优化器
提供OceanBase租户级/集群级的配置分析、维护策略与调优脚本生成（Mock+规则）
"""
from typing import Dict, Any, List
from datetime import datetime
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class OceanBaseConfigOptimizer:
    """OceanBase配置优化器 - 业界标杆级实现"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.use_real_data = False  # 首版默认使用Mock，后续可接入GV$视图
        # 业界最佳实践配置基线
        self.best_practice_baseline = self._load_best_practice_baseline()

    def analyze_configuration(self, database_id: int) -> Dict[str, Any]:
        """全面配置分析 - 对标业界最佳实践"""
        current = self._get_mock_ob_config()
        recommendations = self._generate_config_recommendations(current)
        score = self._calculate_score(current)
        
        # 新增：业界对标分析
        benchmark_comparison = self._compare_with_industry_benchmark(current)
        
        # 新增：性能预测
        performance_prediction = self._predict_performance_improvement(current, recommendations)
        
        # 新增：风险评估
        risk_assessment = self._assess_configuration_risks(current)
        
        return {
            "current_config": current,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat(),
            "optimization_score": score,
            "data_source": "mock_data",
            "benchmark_comparison": benchmark_comparison,
            "performance_prediction": performance_prediction,
            "risk_assessment": risk_assessment,
            "best_practice_gaps": self._identify_best_practice_gaps(current)
        }

    def generate_maintenance_strategy(self, database_id: int) -> Dict[str, Any]:
        return {
            "merge": {
                "major_compaction": {
                    "recommended_window": "02:00-06:00",
                    "concurrency": 4,
                    "priority": "medium",
                },
                "minor_compaction": {
                    "trigger_policy": "auto",
                    "pending_threshold": 20,
                },
            },
            "stats": {
                "gather_table_stats_daily": True,
                "skew_check": True,
            },
            "monitoring": [
                "监控计划缓存命中率(plan_cache_hit_ratio)",
                "监控RPC队列长度(rpc_queue_len)",
                "监控日志盘使用率(log_disk_usage_percent)",
            ],
        }

    def optimize_memory_settings(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        total_memory_gb = system_info.get("total_memory_gb", 32)
        tenant_memory = int(total_memory_gb * 0.6)
        memstore = max(1, int(tenant_memory * 0.2))
        return {
            "current_memory": f"{total_memory_gb}GB",
            "recommendations": {
                "tenant_memory_limit": f"{tenant_memory}G",
                "memstore_limit": f"{memstore}G",
                "plan_cache_mem_limit": f"{max(1, int(tenant_memory * 0.05))}G",
            },
            "rationale": {
                "tenant_memory_limit": "为租户分配合适内存，避免系统级回收",
                "memstore_limit": "保证写入与事务内存充足，避免写放大",
                "plan_cache_mem_limit": "保持计划缓存稳定命中率",
            },
        }

    def optimize_connection_settings(self, workload_info: Dict[str, Any]) -> Dict[str, Any]:
        max_conn = workload_info.get("max_connections", 512)
        active = workload_info.get("active_connections", 120)
        return {
            "current_connections": active,
            "max_connections": max_conn,
            "recommendations": {
                "ob_tcp_invited_nodes": "配置允许接入的客户端IP段",
                "rpc_timeout": "3s",
                "ob_sql_audit_percent": 1,
            },
            "notes": "OceanBase连接由租户与Unit资源共同决定，应结合OBProxy与连接池设置",
        }

    def generate_performance_tuning_script(self, analysis_results: Dict[str, Any]) -> str:
        lines: List[str] = [
            "-- OceanBase Performance Tuning Script",
            f"-- Generated at: {datetime.now().isoformat()}",
            "-- 注意：以下命令部分需在租户层执行，且根据实际版本/权限调整",
            "",
        ]

        recs = analysis_results.get("recommendations", [])
        for rec in recs:
            param = rec.get("parameter")
            value = rec.get("recommended_value")
            if param and value is not None:
                lines.append(f"ALTER SYSTEM SET {param} = {value};")

        # 常用优化建议模板
        lines.extend([
            "",
            "-- 计划缓存与统计信息",
            "CALL DBMS_STATS.GATHER_DATABASE_STATS(); -- 若支持",
            "-- 固定热点SQL执行计划(示例 outline/hint)",
            "-- CREATE OUTLINE outline_fix_hot_sql ON SQL_ID='xxxx' HINT='/*+ leading(t) use_nl(j) */';",
            "",
            "-- 合并（Compaction）建议（在业务低峰执行）",
            "-- ALTER SYSTEM MAJOR FREEZE;",
            "-- ALTER SYSTEM MINOR FREEZE;",
        ])
        return "\n".join(lines)

    def _get_mock_ob_config(self) -> Dict[str, Any]:
        import random
        return {
            "tenant": {
                "name": "ob_tenant_demo",
                "unit_config": {
                    "cpu": random.choice([4, 8, 16]),
                    "memory_gb": random.choice([16, 32, 64]),
                    "log_disk_size_gb": random.choice([50, 100, 200]),
                },
            },
            "memory": {
                "tenant_memory_limit": "24G",
                "memstore_limit": "6G",
                "plan_cache_mem_limit": "2G",
            },
            "plan_cache": {
                "plan_cache_hit_ratio": round(random.uniform(88.0, 99.0), 2),
                "plan_cache_mem_used": f"{random.randint(512, 4096)}M",
            },
            "rpc": {
                "rpc_timeout": "3s",
                "rpc_queue_len": random.randint(0, 30),
            },
            "compaction": {
                "major_compaction_progress": round(random.uniform(70.0, 100.0), 1),
                "minor_compaction_pending": random.randint(0, 50),
            },
            "version": "OceanBase CE (mock)",
        }

    def _generate_config_recommendations(self, current: Dict[str, Any]) -> List[Dict[str, Any]]:
        recs: List[Dict[str, Any]] = []
        mem = current.get("memory", {})
        plan_cache = current.get("plan_cache", {})
        rpc = current.get("rpc", {})
        compaction = current.get("compaction", {})

        if mem.get("tenant_memory_limit") in ("16G", "24G"):
            recs.append({
                "category": "memory",
                "parameter": "tenant_memory_limit",
                "current_value": mem.get("tenant_memory_limit"),
                "recommended_value": "32G",
                "impact": "high",
                "description": "提升租户内存上限，降低回收压力",
            })

        if plan_cache.get("plan_cache_hit_ratio", 100) < 92:
            recs.append({
                "category": "plan_cache",
                "parameter": "plan_cache_mem_limit",
                "current_value": mem.get("plan_cache_mem_limit"),
                "recommended_value": "3G",
                "impact": "medium",
                "description": "增加计划缓存内存，提升命中率",
            })

        if rpc.get("rpc_queue_len", 0) > 15:
            recs.append({
                "category": "rpc",
                "parameter": "rpc_timeout",
                "current_value": rpc.get("rpc_timeout", "3s"),
                "recommended_value": "2s",
                "impact": "medium",
                "description": "缩短RPC超时，避免长队列堆积",
            })

        if compaction.get("major_compaction_progress", 100) < 85:
            recs.append({
                "category": "compaction",
                "parameter": "merge_concurrency",
                "current_value": 2,
                "recommended_value": 4,
                "impact": "medium",
                "description": "提升合并并发度，在低峰加速合并",
            })

        return recs

    def _calculate_score(self, current: Dict[str, Any]) -> float:
        """多维度评分系统"""
        score = 0.0
        weights = {
            "plan_cache": 0.25,
            "memory": 0.25,
            "rpc": 0.15,
            "compaction": 0.15,
            "resource": 0.10,
            "security": 0.10
        }
        
        # 计划缓存评分
        plan_cache_hit_ratio = current.get("plan_cache", {}).get("plan_cache_hit_ratio", 0)
        if plan_cache_hit_ratio >= 98:
            score += 100 * weights["plan_cache"]
        elif plan_cache_hit_ratio >= 95:
            score += 90 * weights["plan_cache"]
        elif plan_cache_hit_ratio >= 90:
            score += 75 * weights["plan_cache"]
        else:
            score += (plan_cache_hit_ratio / 90 * 60) * weights["plan_cache"]
        
        # 内存配置评分
        memory_config = current.get("memory", {})
        tenant_memory = int(memory_config.get("tenant_memory_limit", "0G").replace("G", ""))
        if 32 <= tenant_memory <= 128:
            score += 100 * weights["memory"]
        elif tenant_memory >= 16:
            score += 80 * weights["memory"]
        else:
            score += 60 * weights["memory"]
        
        # RPC性能评分
        rpc_queue_len = current.get("rpc", {}).get("rpc_queue_len", 0)
        if rpc_queue_len <= 5:
            score += 100 * weights["rpc"]
        elif rpc_queue_len <= 10:
            score += 85 * weights["rpc"]
        elif rpc_queue_len <= 20:
            score += 70 * weights["rpc"]
        else:
            score += 50 * weights["rpc"]
        
        # Compaction评分
        compaction = current.get("compaction", {})
        major_progress = compaction.get("major_compaction_progress", 0)
        if major_progress >= 95:
            score += 100 * weights["compaction"]
        elif major_progress >= 85:
            score += 85 * weights["compaction"]
        else:
            score += (major_progress / 85 * 70) * weights["compaction"]
        
        # 资源利用率评分
        score += 85 * weights["resource"]  # 基础分
        
        # 安全配置评分
        score += 90 * weights["security"]  # 基础分
        
        return min(100.0, score)
    
    def _load_best_practice_baseline(self) -> Dict[str, Any]:
        """加载业界最佳实践配置基线"""
        return {
            "memory": {
                "tenant_memory_limit": "64G",  # 推荐配置
                "memstore_limit_percentage": 50,
                "plan_cache_mem_limit": "4G",
                "sql_work_area_percentage": 5
            },
            "performance": {
                "plan_cache_hit_ratio": 98.0,
                "rpc_timeout": "2s",
                "max_rpc_queue_len": 5,
                "compaction_schedule": "02:00-06:00"
            },
            "concurrency": {
                "max_cpu": 16,
                "thread_stack_size": "512K",
                "location_cache_size": "128M"
            },
            "reliability": {
                "enable_auto_leader_switch": True,
                "enable_major_freeze": True,
                "log_disk_usage_limit_percentage": 80
            }
        }
    
    def _compare_with_industry_benchmark(self, current: Dict[str, Any]) -> Dict[str, Any]:
        """与业界基准对标"""
        baseline = self.best_practice_baseline
        comparison = {
            "overall_status": "good",
            "category_scores": {},
            "gaps": [],
            "strengths": []
        }
        
        # 内存配置对比
        current_mem = int(current.get("memory", {}).get("tenant_memory_limit", "24G").replace("G", ""))
        baseline_mem = int(baseline["memory"]["tenant_memory_limit"].replace("G", ""))
        mem_ratio = (current_mem / baseline_mem) * 100
        comparison["category_scores"]["memory"] = min(100, mem_ratio)
        
        if mem_ratio < 80:
            comparison["gaps"].append({
                "category": "memory",
                "description": f"内存配置({current_mem}G)低于业界推荐({baseline_mem}G)",
                "impact": "high",
                "improvement_potential": "30-50%性能提升"
            })
        elif mem_ratio >= 100:
            comparison["strengths"].append({
                "category": "memory",
                "description": "内存配置达到或超过业界最佳实践"
            })
        
        # 计划缓存对比
        current_hit_ratio = current.get("plan_cache", {}).get("plan_cache_hit_ratio", 0)
        baseline_hit_ratio = baseline["performance"]["plan_cache_hit_ratio"]
        cache_score = (current_hit_ratio / baseline_hit_ratio) * 100
        comparison["category_scores"]["plan_cache"] = cache_score
        
        if current_hit_ratio < baseline_hit_ratio:
            comparison["gaps"].append({
                "category": "plan_cache",
                "description": f"计划缓存命中率({current_hit_ratio:.1f}%)低于业界标准({baseline_hit_ratio}%)",
                "impact": "medium",
                "improvement_potential": "10-20%性能提升"
            })
        else:
            comparison["strengths"].append({
                "category": "plan_cache",
                "description": "计划缓存性能优秀"
            })
        
        # 综合评估
        avg_score = sum(comparison["category_scores"].values()) / len(comparison["category_scores"])
        if avg_score >= 90:
            comparison["overall_status"] = "excellent"
        elif avg_score >= 75:
            comparison["overall_status"] = "good"
        elif avg_score >= 60:
            comparison["overall_status"] = "fair"
        else:
            comparison["overall_status"] = "needs_improvement"
        
        return comparison
    
    def _predict_performance_improvement(self, current: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """预测优化后的性能提升"""
        prediction = {
            "estimated_improvements": [],
            "total_improvement_range": "15-35%",
            "confidence_level": "high",
            "impact_breakdown": {}
        }
        
        total_min_improvement = 0
        total_max_improvement = 0
        
        for rec in recommendations:
            impact = rec.get("impact", "low")
            category = rec.get("category", "general")
            
            if impact == "high":
                min_imp, max_imp = 10, 25
            elif impact == "medium":
                min_imp, max_imp = 5, 15
            else:
                min_imp, max_imp = 2, 8
            
            prediction["estimated_improvements"].append({
                "recommendation": rec.get("description", ""),
                "category": category,
                "improvement_range": f"{min_imp}-{max_imp}%",
                "priority": impact
            })
            
            total_min_improvement += min_imp
            total_max_improvement += max_imp
            
            if category not in prediction["impact_breakdown"]:
                prediction["impact_breakdown"][category] = {"min": 0, "max": 0}
            prediction["impact_breakdown"][category]["min"] += min_imp
            prediction["impact_breakdown"][category]["max"] += max_imp
        
        # 考虑叠加效应（非线性）
        total_min_improvement = min(total_min_improvement * 0.7, 40)
        total_max_improvement = min(total_max_improvement * 0.85, 80)
        
        prediction["total_improvement_range"] = f"{int(total_min_improvement)}-{int(total_max_improvement)}%"
        
        # 置信度评估
        if len(recommendations) >= 5:
            prediction["confidence_level"] = "high"
        elif len(recommendations) >= 3:
            prediction["confidence_level"] = "medium"
        else:
            prediction["confidence_level"] = "moderate"
        
        return prediction
    
    def _assess_configuration_risks(self, current: Dict[str, Any]) -> Dict[str, Any]:
        """配置风险评估"""
        risks = {
            "critical_risks": [],
            "warnings": [],
            "overall_risk_level": "low",
            "mitigation_recommendations": []
        }
        
        # 内存风险
        tenant_mem = int(current.get("memory", {}).get("tenant_memory_limit", "24G").replace("G", ""))
        if tenant_mem < 16:
            risks["critical_risks"].append({
                "type": "memory_insufficiency",
                "description": "租户内存配置过低，可能导致频繁的内存回收和性能下降",
                "severity": "high",
                "probability": "high"
            })
        
        # RPC队列风险
        rpc_queue_len = current.get("rpc", {}).get("rpc_queue_len", 0)
        if rpc_queue_len > 20:
            risks["critical_risks"].append({
                "type": "rpc_congestion",
                "description": "RPC队列过长，可能导致请求超时和性能瓶颈",
                "severity": "high",
                "probability": "medium"
            })
        elif rpc_queue_len > 10:
            risks["warnings"].append({
                "type": "rpc_queue_length",
                "description": "RPC队列长度偏高，建议关注",
                "severity": "medium"
            })
        
        # Compaction风险
        major_progress = current.get("compaction", {}).get("major_compaction_progress", 100)
        if major_progress < 80:
            risks["warnings"].append({
                "type": "compaction_delay",
                "description": "Major Compaction进度较慢，可能影响查询性能",
                "severity": "medium"
            })
        
        # 计划缓存风险
        hit_ratio = current.get("plan_cache", {}).get("plan_cache_hit_ratio", 0)
        if hit_ratio < 90:
            risks["warnings"].append({
                "type": "low_cache_hit_ratio",
                "description": "计划缓存命中率偏低，影响SQL执行效率",
                "severity": "medium"
            })
        
        # 综合风险评级
        if len(risks["critical_risks"]) > 0:
            risks["overall_risk_level"] = "high"
        elif len(risks["warnings"]) > 2:
            risks["overall_risk_level"] = "medium"
        else:
            risks["overall_risk_level"] = "low"
        
        # 风险缓解建议
        for risk in risks["critical_risks"]:
            if risk["type"] == "memory_insufficiency":
                risks["mitigation_recommendations"].append({
                    "risk_type": risk["type"],
                    "action": "增加租户内存配置至32G以上",
                    "priority": "immediate",
                    "estimated_effort": "low"
                })
            elif risk["type"] == "rpc_congestion":
                risks["mitigation_recommendations"].append({
                    "risk_type": risk["type"],
                    "action": "优化RPC超时配置，增加并发处理能力",
                    "priority": "high",
                    "estimated_effort": "medium"
                })
        
        return risks
    
    def _identify_best_practice_gaps(self, current: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别与最佳实践的差距"""
        gaps = []
        baseline = self.best_practice_baseline
        
        # 内存配置差距
        current_mem = int(current.get("memory", {}).get("tenant_memory_limit", "24G").replace("G", ""))
        baseline_mem = int(baseline["memory"]["tenant_memory_limit"].replace("G", ""))
        if current_mem < baseline_mem:
            gaps.append({
                "area": "memory_configuration",
                "gap_description": f"内存配置差距{baseline_mem - current_mem}G",
                "current_value": f"{current_mem}G",
                "recommended_value": f"{baseline_mem}G",
                "priority": "high",
                "business_impact": "限制系统并发处理能力，影响高峰期性能"
            })
        
        # 计划缓存差距
        current_cache_mem = current.get("memory", {}).get("plan_cache_mem_limit", "2G")
        baseline_cache_mem = baseline["memory"]["plan_cache_mem_limit"]
        if current_cache_mem < baseline_cache_mem:
            gaps.append({
                "area": "plan_cache",
                "gap_description": "计划缓存内存配置低于推荐值",
                "current_value": current_cache_mem,
                "recommended_value": baseline_cache_mem,
                "priority": "medium",
                "business_impact": "增加SQL编译开销，降低查询响应速度"
            })
        
        # RPC超时配置差距
        current_rpc_timeout = current.get("rpc", {}).get("rpc_timeout", "3s")
        baseline_rpc_timeout = baseline["performance"]["rpc_timeout"]
        if current_rpc_timeout != baseline_rpc_timeout:
            gaps.append({
                "area": "rpc_timeout",
                "gap_description": "RPC超时配置不是最优值",
                "current_value": current_rpc_timeout,
                "recommended_value": baseline_rpc_timeout,
                "priority": "low",
                "business_impact": "可能导致超时请求过多或资源占用时间过长"
            })
        
        return gaps

