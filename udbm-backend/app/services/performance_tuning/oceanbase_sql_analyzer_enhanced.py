"""
OceanBase SQL性能分析器增强版 - 业界标杆级实现
包含智能SQL改写、根因分析、性能基线对比等高级功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from .oceanbase_sql_analyzer import OceanBaseSQLAnalyzer, SQLAuditRecord

logger = logging.getLogger(__name__)


class OceanBaseSQLAnalyzerEnhanced(OceanBaseSQLAnalyzer):
    """OceanBase SQL性能分析器增强版 - 业界标杆级实现"""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session)
        # SQL模式识别引擎
        self.pattern_engine = self._init_pattern_engine()
        # 性能基线
        self.performance_baseline = self._init_performance_baseline()
    
    def analyze_slow_queries_enhanced(self,
                                     database_id: int,
                                     threshold_seconds: float = 1.0,
                                     hours: int = 24) -> Dict[str, Any]:
        """增强的慢查询分析 - 结合AI和规则引擎"""
        # 调用父类方法获取基础分析
        basic_analysis = self.analyze_slow_queries(database_id, threshold_seconds, hours)
        
        # 获取慢查询数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        slow_queries = self.query_sql_audit(
            database_id=database_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        slow_queries = [q for q in slow_queries if q.elapsed_time >= threshold_seconds]
        
        # 增强分析
        enhanced_analysis = {
            **basic_analysis,
            "sql_patterns": self._identify_sql_patterns(slow_queries),
            "root_cause_analysis": self._perform_root_cause_analysis(slow_queries),
            "rewrite_suggestions": self._generate_sql_rewrite_suggestions(slow_queries),
            "baseline_comparison": self._compare_with_baseline(slow_queries),
            "analysis_quality_score": self._calculate_analysis_quality_score(slow_queries),
            "actionable_insights": self._generate_actionable_insights(slow_queries)
        }
        
        return enhanced_analysis
    
    def _init_pattern_engine(self) -> Dict[str, Any]:
        """初始化SQL模式识别引擎"""
        return {
            "anti_patterns": [
                {"name": "select_star", "pattern": r"SELECT\s+\*", "severity": "medium"},
                {"name": "leading_wildcard", "pattern": r"LIKE\s+'%", "severity": "high"},
                {"name": "no_limit", "pattern": r"ORDER\s+BY.*(?!LIMIT)", "severity": "medium"},
                {"name": "implicit_conversion", "pattern": r"WHERE.*\d+\s*=\s*'\d+'", "severity": "high"},
                {"name": "nested_subquery", "pattern": r"\(\s*SELECT.*\(\s*SELECT", "severity": "high"},
                {"name": "cartesian_product", "pattern": r"FROM.*,.*WHERE\s+(?!.*=)", "severity": "critical"}
            ],
            "best_practices": [
                {"name": "use_index_hint", "pattern": r"/\*\+.*INDEX.*\*/"},
                {"name": "use_limit", "pattern": r"LIMIT\s+\d+"},
                {"name": "specific_columns", "pattern": r"SELECT\s+[^*]+\s+FROM"},
                {"name": "partition_pruning", "pattern": r"WHERE.*partition_key"}
            ]
        }
    
    def _init_performance_baseline(self) -> Dict[str, Any]:
        """初始化性能基线 - 基于业界最佳实践"""
        return {
            "avg_elapsed_time": 0.5,  # 秒
            "avg_cpu_time": 0.3,
            "avg_physical_reads": 100,
            "avg_logical_reads": 500,
            "slow_query_threshold": 1.0,
            "cpu_intensive_ratio": 0.6,
            "io_intensive_threshold": 1000,
            "plan_cache_hit_ratio": 98.0,
            "optimal_response_time": 0.1  # 100ms
        }
    
    def _identify_sql_patterns(self, slow_queries: List[SQLAuditRecord]) -> Dict[str, Any]:
        """识别SQL模式"""
        patterns = {
            "anti_patterns_found": [],
            "pattern_frequency": {},
            "common_issues": [],
            "best_practice_adoption": 0.0,
            "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0}
        }
        
        anti_pattern_count = 0
        best_practice_count = 0
        
        for query in slow_queries:
            sql_text = query.query_sql
            
            # 检测反模式
            for anti_pattern in self.pattern_engine["anti_patterns"]:
                if re.search(anti_pattern["pattern"], sql_text, re.IGNORECASE):
                    anti_pattern_count += 1
                    pattern_name = anti_pattern["name"]
                    severity = anti_pattern.get("severity", "medium")
                    
                    patterns["pattern_frequency"][pattern_name] = patterns["pattern_frequency"].get(pattern_name, 0) + 1
                    patterns["severity_breakdown"][severity] = patterns["severity_breakdown"].get(severity, 0) + 1
                    
                    if pattern_name not in [p["name"] for p in patterns["anti_patterns_found"]]:
                        patterns["anti_patterns_found"].append({
                            "name": pattern_name,
                            "severity": severity,
                            "description": self._get_anti_pattern_description(pattern_name),
                            "recommendation": self._get_anti_pattern_recommendation(pattern_name),
                            "impact": self._estimate_pattern_impact(pattern_name)
                        })
            
            # 检测最佳实践
            for best_practice in self.pattern_engine["best_practices"]:
                if re.search(best_practice["pattern"], sql_text, re.IGNORECASE):
                    best_practice_count += 1
        
        # 计算最佳实践采用率
        total_checks = len(slow_queries) * len(self.pattern_engine["best_practices"])
        patterns["best_practice_adoption"] = (best_practice_count / total_checks * 100) if total_checks > 0 else 0
        
        # 生成常见问题汇总
        sorted_patterns = sorted(patterns["pattern_frequency"].items(), key=lambda x: x[1], reverse=True)
        for pattern_name, count in sorted_patterns[:5]:
            patterns["common_issues"].append({
                "issue": pattern_name,
                "occurrence_count": count,
                "percentage": (count / len(slow_queries) * 100) if slow_queries else 0,
                "priority": self._get_issue_priority(pattern_name, count, len(slow_queries))
            })
        
        return patterns
    
    def _perform_root_cause_analysis(self, slow_queries: List[SQLAuditRecord]) -> Dict[str, Any]:
        """深度根因分析"""
        root_causes = {
            "primary_causes": [],
            "contributing_factors": [],
            "correlation_analysis": {},
            "confidence_scores": {},
            "recommended_actions": []
        }
        
        # CPU密集型问题分析
        cpu_intensive = [q for q in slow_queries if q.cpu_time / q.elapsed_time > 0.8]
        if cpu_intensive:
            confidence = len(cpu_intensive) / len(slow_queries) * 100
            root_causes["primary_causes"].append({
                "cause": "cpu_intensive_queries",
                "description": "CPU密集型查询导致性能下降",
                "affected_queries": len(cpu_intensive),
                "percentage": confidence,
                "confidence": "high" if confidence > 50 else "medium",
                "root_reason": "可能由于全表扫描、复杂计算或JOIN顺序不当",
                "typical_symptoms": ["CPU使用率过高", "查询响应时间长", "系统整体响应变慢"]
            })
            root_causes["confidence_scores"]["cpu_intensive"] = confidence
        
        # IO密集型问题分析
        io_intensive = [q for q in slow_queries if q.physical_reads > 1000]
        if io_intensive:
            confidence = len(io_intensive) / len(slow_queries) * 100
            root_causes["primary_causes"].append({
                "cause": "io_intensive_queries",
                "description": "IO密集型查询导致性能下降",
                "affected_queries": len(io_intensive),
                "percentage": confidence,
                "confidence": "high" if confidence > 50 else "medium",
                "root_reason": "可能由于缺少索引、查询条件过宽或数据分布不均",
                "typical_symptoms": ["磁盘IO高", "读响应时间长", "缓存命中率低"]
            })
            root_causes["confidence_scores"]["io_intensive"] = confidence
        
        # 内存密集型问题分析
        mem_intensive = [q for q in slow_queries if q.mem_used > 50000]
        if mem_intensive:
            root_causes["contributing_factors"].append({
                "factor": "memory_intensive_operations",
                "description": "大量内存消耗操作",
                "affected_queries": len(mem_intensive),
                "impact": "medium",
                "typical_operations": ["排序", "分组", "子查询", "临时表"]
            })
        
        # 队列等待分析
        queue_wait = [q for q in slow_queries if q.queue_time > 0.1]
        if queue_wait:
            root_causes["contributing_factors"].append({
                "factor": "queue_waiting",
                "description": "RPC队列等待时间过长",
                "affected_queries": len(queue_wait),
                "impact": "high",
                "suggestion": "增加并发处理能力或优化连接池配置"
            })
        
        # 相关性分析
        if cpu_intensive and io_intensive:
            overlap = len(set([q.sql_id for q in cpu_intensive]) & set([q.sql_id for q in io_intensive]))
            root_causes["correlation_analysis"]["cpu_io_correlation"] = {
                "overlap_count": overlap,
                "overlap_percentage": (overlap / len(slow_queries) * 100) if slow_queries else 0,
                "interpretation": "CPU和IO问题共存，可能需要综合优化策略" if overlap > 0 else "问题相对独立，可分别处理"
            }
        
        # 生成推荐行动
        if cpu_intensive:
            root_causes["recommended_actions"].append({
                "priority": "high",
                "action": "优化CPU密集型查询",
                "steps": [
                    "检查并优化全表扫描查询",
                    "优化JOIN顺序和条件",
                    "添加合适的索引",
                    "考虑查询结果缓存"
                ]
            })
        
        if io_intensive:
            root_causes["recommended_actions"].append({
                "priority": "high",
                "action": "优化IO密集型查询",
                "steps": [
                    "创建缺失的索引",
                    "优化查询条件减少扫描范围",
                    "检查分区裁剪是否生效",
                    "考虑数据预聚合"
                ]
            })
        
        return root_causes
    
    def _generate_sql_rewrite_suggestions(self, slow_queries: List[SQLAuditRecord]) -> List[Dict[str, Any]]:
        """生成智能SQL改写建议"""
        suggestions = []
        
        for query in slow_queries[:15]:  # 分析top 15
            sql_text = query.query_sql
            rewrite_suggestion = {
                "original_sql": sql_text,
                "sql_id": query.sql_id,
                "current_performance": {
                    "elapsed_time": round(query.elapsed_time, 3),
                    "cpu_time": round(query.cpu_time, 3),
                    "physical_reads": query.physical_reads,
                    "rows_returned": query.rows_returned
                },
                "rewrite_options": [],
                "estimated_improvement": "0%",
                "priority": "low"
            }
            
            total_improvement = 0
            
            # SELECT * 优化
            if re.search(r"SELECT\s+\*", sql_text, re.IGNORECASE):
                improvement = 15
                total_improvement += improvement
                rewrite_suggestion["rewrite_options"].append({
                    "type": "column_specification",
                    "severity": "medium",
                    "description": "指定具体列名而非SELECT *",
                    "example": sql_text.replace("SELECT *", "SELECT id, name, created_at"),
                    "benefit": f"减少数据传输量，提升{improvement}%性能",
                    "effort": "low"
                })
            
            # LIKE '%...' 优化
            if re.search(r"LIKE\s+'%", sql_text, re.IGNORECASE):
                improvement = 65
                total_improvement += improvement
                rewrite_suggestion["rewrite_options"].append({
                    "type": "fulltext_search",
                    "severity": "high",
                    "description": "使用全文索引代替前导通配符LIKE",
                    "example": "-- 创建全文索引\nCREATE FULLTEXT INDEX idx_fulltext_content ON table_name(content);\n\n-- 修改查询\nSELECT * FROM table_name WHERE MATCH(content) AGAINST('search_term');",
                    "benefit": f"提升{improvement}%搜索性能",
                    "effort": "medium"
                })
            
            # 没有LIMIT的ORDER BY
            if re.search(r"ORDER\s+BY", sql_text, re.IGNORECASE) and not re.search(r"LIMIT", sql_text, re.IGNORECASE):
                improvement = 30
                total_improvement += improvement
                rewrite_suggestion["rewrite_options"].append({
                    "type": "add_limit",
                    "severity": "medium",
                    "description": "添加LIMIT子句限制结果集",
                    "example": sql_text.strip().rstrip(';') + " LIMIT 100;",
                    "benefit": f"减少排序和数据传输开销，提升{improvement}%性能",
                    "effort": "low"
                })
            
            # 多表JOIN优化
            join_count = sql_text.upper().count("JOIN")
            if join_count > 2:
                improvement = min(50, join_count * 15)
                total_improvement += improvement
                rewrite_suggestion["rewrite_options"].append({
                    "type": "join_optimization",
                    "severity": "high",
                    "description": "优化多表JOIN顺序和方式",
                    "example": "-- 使用HINT指定JOIN顺序\nSELECT /*+ LEADING(small_table, medium_table, large_table) USE_NL(medium_table) */ \n  columns\nFROM small_table\nJOIN medium_table ON ...\nJOIN large_table ON ...;",
                    "benefit": f"优化JOIN执行计划，提升{improvement}%性能",
                    "effort": "medium"
                })
            
            # 子查询优化
            if re.search(r"IN\s*\(\s*SELECT", sql_text, re.IGNORECASE):
                improvement = 40
                total_improvement += improvement
                rewrite_suggestion["rewrite_options"].append({
                    "type": "subquery_to_join",
                    "severity": "high",
                    "description": "将IN子查询改写为JOIN",
                    "example": "-- 原查询使用IN子查询\n-- 优化为JOIN\nSELECT t1.* \nFROM table1 t1\nJOIN (SELECT DISTINCT id FROM table2 WHERE ...) t2 ON t1.id = t2.id;",
                    "benefit": f"减少子查询执行次数，提升{improvement}%性能",
                    "effort": "medium"
                })
            
            # 隐式类型转换
            if re.search(r"WHERE.*\d+\s*=\s*'\d+'", sql_text, re.IGNORECASE):
                improvement = 35
                total_improvement += improvement
                rewrite_suggestion["rewrite_options"].append({
                    "type": "type_conversion",
                    "severity": "high",
                    "description": "避免隐式类型转换导致索引失效",
                    "example": "-- 确保比较双方类型一致\n-- 将 WHERE id = '123' 改为 WHERE id = 123",
                    "benefit": f"启用索引，提升{improvement}%性能",
                    "effort": "low"
                })
            
            # 计算总体改善和优先级
            if rewrite_suggestion["rewrite_options"]:
                # 考虑叠加效应（非线性）
                if total_improvement > 0:
                    rewrite_suggestion["estimated_improvement"] = f"{int(total_improvement * 0.7)}-{min(85, total_improvement)}%"
                    
                    if total_improvement >= 80:
                        rewrite_suggestion["priority"] = "critical"
                    elif total_improvement >= 50:
                        rewrite_suggestion["priority"] = "high"
                    elif total_improvement >= 30:
                        rewrite_suggestion["priority"] = "medium"
                    else:
                        rewrite_suggestion["priority"] = "low"
                    
                    suggestions.append(rewrite_suggestion)
        
        # 按优先级排序
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        suggestions.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return suggestions
    
    def _compare_with_baseline(self, slow_queries: List[SQLAuditRecord]) -> Dict[str, Any]:
        """与性能基线对比"""
        baseline = self.performance_baseline
        comparison = {
            "baseline_metrics": baseline,
            "current_metrics": {},
            "deviations": [],
            "overall_health": "good",
            "health_score": 100.0
        }
        
        if not slow_queries:
            return comparison
        
        # 计算当前指标
        avg_elapsed = sum(q.elapsed_time for q in slow_queries) / len(slow_queries)
        avg_cpu = sum(q.cpu_time for q in slow_queries) / len(slow_queries)
        avg_physical_reads = sum(q.physical_reads for q in slow_queries) / len(slow_queries)
        avg_logical_reads = sum(q.logical_reads for q in slow_queries) / len(slow_queries)
        
        comparison["current_metrics"] = {
            "avg_elapsed_time": round(avg_elapsed, 3),
            "avg_cpu_time": round(avg_cpu, 3),
            "avg_physical_reads": int(avg_physical_reads),
            "avg_logical_reads": int(avg_logical_reads),
            "slow_query_count": len(slow_queries)
        }
        
        health_score = 100.0
        
        # 执行时间偏差
        if avg_elapsed > baseline["avg_elapsed_time"] * 3:
            deviation_pct = ((avg_elapsed / baseline["avg_elapsed_time"] - 1) * 100)
            comparison["deviations"].append({
                "metric": "avg_elapsed_time",
                "baseline": baseline["avg_elapsed_time"],
                "current": round(avg_elapsed, 3),
                "deviation": f"+{deviation_pct:.1f}%",
                "severity": "critical",
                "description": "平均执行时间远高于基线，系统性能严重下降"
            })
            health_score -= 30
        elif avg_elapsed > baseline["avg_elapsed_time"] * 2:
            deviation_pct = ((avg_elapsed / baseline["avg_elapsed_time"] - 1) * 100)
            comparison["deviations"].append({
                "metric": "avg_elapsed_time",
                "baseline": baseline["avg_elapsed_time"],
                "current": round(avg_elapsed, 3),
                "deviation": f"+{deviation_pct:.1f}%",
                "severity": "high",
                "description": "平均执行时间明显高于基线"
            })
            health_score -= 20
        
        # 物理读偏差
        if avg_physical_reads > baseline["avg_physical_reads"] * 10:
            deviation_pct = ((avg_physical_reads / baseline["avg_physical_reads"] - 1) * 100)
            comparison["deviations"].append({
                "metric": "avg_physical_reads",
                "baseline": baseline["avg_physical_reads"],
                "current": int(avg_physical_reads),
                "deviation": f"+{deviation_pct:.1f}%",
                "severity": "critical",
                "description": "物理读次数远高于基线，IO成为严重瓶颈"
            })
            health_score -= 25
        elif avg_physical_reads > baseline["avg_physical_reads"] * 5:
            deviation_pct = ((avg_physical_reads / baseline["avg_physical_reads"] - 1) * 100)
            comparison["deviations"].append({
                "metric": "avg_physical_reads",
                "baseline": baseline["avg_physical_reads"],
                "current": int(avg_physical_reads),
                "deviation": f"+{deviation_pct:.1f}%",
                "severity": "high",
                "description": "物理读次数明显高于基线"
            })
            health_score -= 15
        
        # CPU时间偏差
        if avg_cpu > baseline["avg_cpu_time"] * 3:
            deviation_pct = ((avg_cpu / baseline["avg_cpu_time"] - 1) * 100)
            comparison["deviations"].append({
                "metric": "avg_cpu_time",
                "baseline": baseline["avg_cpu_time"],
                "current": round(avg_cpu, 3),
                "deviation": f"+{deviation_pct:.1f}%",
                "severity": "high",
                "description": "CPU时间消耗远高于基线"
            })
            health_score -= 15
        
        # 计算健康分数和状态
        comparison["health_score"] = max(0.0, health_score)
        
        if health_score >= 80:
            comparison["overall_health"] = "excellent"
        elif health_score >= 60:
            comparison["overall_health"] = "good"
        elif health_score >= 40:
            comparison["overall_health"] = "fair"
        elif health_score >= 20:
            comparison["overall_health"] = "poor"
        else:
            comparison["overall_health"] = "critical"
        
        return comparison
    
    def _calculate_analysis_quality_score(self, slow_queries: List[SQLAuditRecord]) -> float:
        """计算分析质量评分"""
        score = 0.0
        
        # 数据量评分 (25%)
        if len(slow_queries) >= 100:
            score += 25
        elif len(slow_queries) >= 50:
            score += 20
        else:
            score += (len(slow_queries) / 50) * 20
        
        # 数据多样性评分 (25%)
        if slow_queries:
            unique_sql_ids = len(set(q.sql_id for q in slow_queries))
            diversity_ratio = unique_sql_ids / len(slow_queries)
            score += diversity_ratio * 25
        
        # 时间范围评分 (20%)
        if slow_queries:
            time_range = (max(q.request_time for q in slow_queries) - 
                         min(q.request_time for q in slow_queries)).total_seconds()
            if time_range >= 3600:  # 1小时以上
                score += 20
            else:
                score += (time_range / 3600) * 20
        
        # 性能指标完整性评分 (20%)
        if slow_queries:
            complete_metrics = sum(1 for q in slow_queries 
                                 if q.cpu_time > 0 and q.physical_reads > 0 and q.mem_used > 0)
            completeness_ratio = complete_metrics / len(slow_queries)
            score += completeness_ratio * 20
        
        # 问题覆盖度评分 (10%)
        problem_types = set()
        for q in slow_queries:
            if q.cpu_time / q.elapsed_time > 0.8:
                problem_types.add("cpu_intensive")
            if q.physical_reads > 1000:
                problem_types.add("io_intensive")
            if q.mem_used > 50000:
                problem_types.add("mem_intensive")
            if q.queue_time > 0.1:
                problem_types.add("queue_wait")
        
        coverage_score = len(problem_types) / 4 * 10  # 最多4种问题类型
        score += coverage_score
        
        return min(100.0, score)
    
    def _generate_actionable_insights(self, slow_queries: List[SQLAuditRecord]) -> List[Dict[str, Any]]:
        """生成可执行的洞察建议"""
        insights = []
        
        # 洞察1: 最需要优化的查询
        if slow_queries:
            worst_query = max(slow_queries, key=lambda q: q.elapsed_time)
            insights.append({
                "type": "critical_query",
                "priority": "immediate",
                "title": "最慢查询需立即优化",
                "description": f"SQL ID {worst_query.sql_id} 执行时间达{worst_query.elapsed_time:.2f}秒，严重影响系统性能",
                "impact": "high",
                "actions": [
                    "分析该查询的执行计划",
                    "检查是否缺少索引",
                    "考虑添加查询缓存",
                    "评估是否可以异步处理"
                ]
            })
        
        # 洞察2: CPU密集型查询集中优化
        cpu_intensive = [q for q in slow_queries if q.cpu_time / q.elapsed_time > 0.8]
        if len(cpu_intensive) >= 5:
            insights.append({
                "type": "cpu_optimization",
                "priority": "high",
                "title": f"发现{len(cpu_intensive)}个CPU密集型查询",
                "description": "CPU密集型查询占比过高，需要系统性优化",
                "impact": "high",
                "actions": [
                    "批量检查全表扫描问题",
                    "优化JOIN顺序",
                    "增加适当索引",
                    "考虑查询改写"
                ]
            })
        
        # 洞察3: IO瓶颈优化
        io_intensive = [q for q in slow_queries if q.physical_reads > 1000]
        if len(io_intensive) >= 5:
            insights.append({
                "type": "io_optimization",
                "priority": "high",
                "title": f"发现{len(io_intensive)}个IO密集型查询",
                "description": "IO成为系统性能瓶颈，影响整体响应速度",
                "impact": "high",
                "actions": [
                    "创建缺失的索引",
                    "优化查询过滤条件",
                    "检查分区裁剪效果",
                    "考虑数据缓存策略"
                ]
            })
        
        # 洞察4: 查询模式优化
        select_star_count = sum(1 for q in slow_queries if re.search(r"SELECT\s+\*", q.query_sql, re.IGNORECASE))
        if select_star_count > len(slow_queries) * 0.3:
            insights.append({
                "type": "query_pattern",
                "priority": "medium",
                "title": "大量使用SELECT *反模式",
                "description": f"{select_star_count}个查询使用SELECT *，传输不必要的数据",
                "impact": "medium",
                "actions": [
                    "指定具体需要的列",
                    "减少网络传输开销",
                    "降低解析成本",
                    "建立SQL编码规范"
                ]
            })
        
        # 洞察5: 响应时间分布
        if slow_queries:
            avg_time = sum(q.elapsed_time for q in slow_queries) / len(slow_queries)
            max_time = max(q.elapsed_time for q in slow_queries)
            if max_time > avg_time * 5:
                insights.append({
                    "type": "response_time_variance",
                    "priority": "medium",
                    "title": "查询响应时间波动大",
                    "description": f"最慢查询({max_time:.2f}s)是平均值({avg_time:.2f}s)的{max_time/avg_time:.1f}倍",
                    "impact": "medium",
                    "actions": [
                        "识别异常慢查询",
                        "分析特定场景下的性能问题",
                        "建立性能监控告警",
                        "制定性能SLA标准"
                    ]
                })
        
        return insights
    
    def _get_anti_pattern_description(self, pattern_name: str) -> str:
        """获取反模式描述"""
        descriptions = {
            "select_star": "使用SELECT *会查询所有列，增加不必要的数据传输和内存消耗",
            "leading_wildcard": "前导通配符LIKE查询无法使用索引，导致全表扫描",
            "no_limit": "ORDER BY没有LIMIT会对所有结果排序，消耗大量CPU和内存资源",
            "implicit_conversion": "隐式类型转换会导致索引失效，引发全表扫描",
            "nested_subquery": "多层嵌套子查询性能较差，且难以优化",
            "cartesian_product": "笛卡尔积会产生大量中间结果，严重影响性能"
        }
        return descriptions.get(pattern_name, "未知反模式")
    
    def _get_anti_pattern_recommendation(self, pattern_name: str) -> str:
        """获取反模式建议"""
        recommendations = {
            "select_star": "明确指定需要的列名，只查询必要的数据",
            "leading_wildcard": "使用全文索引或重新设计查询条件",
            "no_limit": "添加LIMIT子句限制结果集大小，或使用分页",
            "implicit_conversion": "确保比较操作符两边的数据类型一致",
            "nested_subquery": "使用JOIN或CTE(WITH子句)改写查询",
            "cartesian_product": "添加正确的JOIN条件，避免笛卡尔积"
        }
        return recommendations.get(pattern_name, "请咨询DBA进行优化")
    
    def _estimate_pattern_impact(self, pattern_name: str) -> str:
        """估计反模式影响"""
        impacts = {
            "select_star": "10-20%性能损失",
            "leading_wildcard": "50-80%性能损失",
            "no_limit": "20-40%性能损失",
            "implicit_conversion": "30-60%性能损失",
            "nested_subquery": "40-70%性能损失",
            "cartesian_product": "90%+性能损失"
        }
        return impacts.get(pattern_name, "性能影响未知")
    
    def _get_issue_priority(self, pattern_name: str, count: int, total: int) -> str:
        """获取问题优先级"""
        percentage = (count / total * 100) if total > 0 else 0
        
        # 高严重性模式
        if pattern_name in ["cartesian_product", "leading_wildcard", "implicit_conversion"]:
            if percentage > 30:
                return "critical"
            elif percentage > 10:
                return "high"
            else:
                return "medium"
        # 中严重性模式
        elif pattern_name in ["nested_subquery", "no_limit"]:
            if percentage > 50:
                return "high"
            elif percentage > 20:
                return "medium"
            else:
                return "low"
        # 低严重性模式
        else:
            if percentage > 70:
                return "medium"
            else:
                return "low"