"""
执行计划分析器
"""
from typing import Dict, List, Any, Optional
import json
import re
from datetime import datetime

class ExecutionPlanAnalyzer:
    """
    SQL执行计划分析器
    """
    
    def __init__(self):
        self.name = "ExecutionPlanAnalyzer"
    
    @staticmethod
    def analyze_plan(plan_text: str, database_type: str = "postgresql") -> Dict[str, Any]:
        """
        分析执行计划
        
        Args:
            plan_text: 执行计划文本
            database_type: 数据库类型
            
        Returns:
            分析结果字典
        """
        try:
            if database_type.lower() == "postgresql":
                return ExecutionPlanAnalyzer._analyze_postgres_plan(plan_text)
            else:
                return {
                    "success": False,
                    "message": f"暂不支持 {database_type} 数据库的执行计划分析",
                    "plan_summary": {},
                    "performance_issues": [],
                    "recommendations": []
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"执行计划分析失败: {str(e)}",
                "plan_summary": {},
                "performance_issues": [],
                "recommendations": []
            }
    
    @staticmethod
    def _analyze_postgres_plan(plan_text: str) -> Dict[str, Any]:
        """
        分析PostgreSQL执行计划
        """
        analysis = {
            "success": True,
            "message": "执行计划分析完成",
            "plan_summary": {
                "total_cost": 0.0,
                "startup_cost": 0.0,
                "rows": 0,
                "width": 0,
                "actual_time": 0.0,
                "planning_time": 0.0,
                "execution_time": 0.0
            },
            "performance_issues": [],
            "recommendations": [],
            "nodes": []
        }
        
        try:
            # 尝试解析JSON格式的执行计划
            if plan_text.strip().startswith('[') or plan_text.strip().startswith('{'):
                plan_json = json.loads(plan_text)
                if isinstance(plan_json, list) and len(plan_json) > 0:
                    plan_data = plan_json[0]
                    if "Plan" in plan_data:
                        analysis["plan_summary"] = ExecutionPlanAnalyzer._extract_plan_summary(plan_data["Plan"])
                        analysis["nodes"] = ExecutionPlanAnalyzer._extract_plan_nodes(plan_data["Plan"])
                        
                        # 提取执行时间信息
                        if "Planning Time" in plan_data:
                            analysis["plan_summary"]["planning_time"] = plan_data["Planning Time"]
                        if "Execution Time" in plan_data:
                            analysis["plan_summary"]["execution_time"] = plan_data["Execution Time"]
            else:
                # 解析文本格式的执行计划
                analysis["plan_summary"] = ExecutionPlanAnalyzer._parse_text_plan(plan_text)
            
            # 分析性能问题
            analysis["performance_issues"] = ExecutionPlanAnalyzer._identify_performance_issues(analysis)
            analysis["recommendations"] = ExecutionPlanAnalyzer._generate_recommendations(analysis)
            
        except json.JSONDecodeError:
            # 如果不是JSON格式，按文本解析
            analysis["plan_summary"] = ExecutionPlanAnalyzer._parse_text_plan(plan_text)
        except Exception as e:
            analysis["success"] = False
            analysis["message"] = f"执行计划解析失败: {str(e)}"
        
        return analysis
    
    @staticmethod
    def _extract_plan_summary(plan_node: Dict) -> Dict[str, Any]:
        """
        提取执行计划摘要信息
        """
        summary = {
            "total_cost": plan_node.get("Total Cost", 0.0),
            "startup_cost": plan_node.get("Startup Cost", 0.0),
            "rows": plan_node.get("Plan Rows", 0),
            "width": plan_node.get("Plan Width", 0),
            "actual_time": 0.0,
            "planning_time": 0.0,
            "execution_time": 0.0
        }
        
        # 提取实际执行时间
        if "Actual Total Time" in plan_node:
            summary["actual_time"] = plan_node["Actual Total Time"]
        
        return summary
    
    @staticmethod
    def _extract_plan_nodes(plan_node: Dict, level: int = 0) -> List[Dict]:
        """
        递归提取执行计划节点
        """
        nodes = []
        
        node_info = {
            "level": level,
            "node_type": plan_node.get("Node Type", "Unknown"),
            "relation_name": plan_node.get("Relation Name", ""),
            "alias": plan_node.get("Alias", ""),
            "startup_cost": plan_node.get("Startup Cost", 0.0),
            "total_cost": plan_node.get("Total Cost", 0.0),
            "plan_rows": plan_node.get("Plan Rows", 0),
            "plan_width": plan_node.get("Plan Width", 0),
            "actual_startup_time": plan_node.get("Actual Startup Time", 0.0),
            "actual_total_time": plan_node.get("Actual Total Time", 0.0),
            "actual_rows": plan_node.get("Actual Rows", 0),
            "actual_loops": plan_node.get("Actual Loops", 1)
        }
        
        nodes.append(node_info)
        
        # 递归处理子节点
        if "Plans" in plan_node:
            for child_plan in plan_node["Plans"]:
                nodes.extend(ExecutionPlanAnalyzer._extract_plan_nodes(child_plan, level + 1))
        
        return nodes
    
    @staticmethod
    def _parse_text_plan(plan_text: str) -> Dict[str, Any]:
        """
        解析文本格式的执行计划
        """
        summary = {
            "total_cost": 0.0,
            "startup_cost": 0.0,
            "rows": 0,
            "width": 0,
            "actual_time": 0.0,
            "planning_time": 0.0,
            "execution_time": 0.0
        }
        
        lines = plan_text.split('\n')
        for line in lines:
            line = line.strip()
            
            # 提取成本信息
            cost_match = re.search(r'cost=(\d+\.?\d*)\.\.(\d+\.?\d*)', line)
            if cost_match:
                summary["startup_cost"] = float(cost_match.group(1))
                summary["total_cost"] = float(cost_match.group(2))
            
            # 提取行数和宽度
            rows_match = re.search(r'rows=(\d+)', line)
            if rows_match:
                summary["rows"] = int(rows_match.group(1))
            
            width_match = re.search(r'width=(\d+)', line)
            if width_match:
                summary["width"] = int(width_match.group(1))
            
            # 提取实际执行时间
            time_match = re.search(r'actual time=(\d+\.?\d*)', line)
            if time_match:
                summary["actual_time"] = float(time_match.group(1))
            
            # 提取规划和执行时间
            if "Planning Time:" in line:
                planning_match = re.search(r'Planning Time:\s*(\d+\.?\d*)', line)
                if planning_match:
                    summary["planning_time"] = float(planning_match.group(1))
            
            if "Execution Time:" in line:
                execution_match = re.search(r'Execution Time:\s*(\d+\.?\d*)', line)
                if execution_match:
                    summary["execution_time"] = float(execution_match.group(1))
        
        return summary
    
    @staticmethod
    def _identify_performance_issues(analysis: Dict) -> List[Dict]:
        """
        识别性能问题
        """
        issues = []
        plan_summary = analysis["plan_summary"]
        
        # 高成本查询
        if plan_summary.get("total_cost", 0) > 10000:
            issues.append({
                "type": "high_cost",
                "severity": "high" if plan_summary["total_cost"] > 100000 else "medium",
                "description": f"查询成本过高: {plan_summary['total_cost']:.2f}",
                "recommendation": "考虑添加索引或优化查询条件"
            })
        
        # 长执行时间
        execution_time = plan_summary.get("execution_time", 0)
        if execution_time > 1000:  # 大于1秒
            issues.append({
                "type": "slow_execution",
                "severity": "high" if execution_time > 5000 else "medium",
                "description": f"执行时间过长: {execution_time:.2f}ms",
                "recommendation": "优化查询逻辑或添加合适的索引"
            })
        
        # 检查是否存在全表扫描
        nodes = analysis.get("nodes", [])
        for node in nodes:
            if node.get("node_type") == "Seq Scan" and node.get("actual_rows", 0) > 1000:
                issues.append({
                    "type": "seq_scan",
                    "severity": "medium",
                    "description": f"在表 {node.get('relation_name', 'unknown')} 上进行了全表扫描",
                    "recommendation": "考虑在相关列上添加索引"
                })
        
        return issues
    
    @staticmethod
    def _generate_recommendations(analysis: Dict) -> List[str]:
        """
        生成优化建议
        """
        recommendations = []
        
        issues = analysis.get("performance_issues", [])
        if not issues:
            recommendations.append("执行计划看起来正常，无明显性能问题")
            return recommendations
        
        # 基于识别的问题生成建议
        high_cost_issues = [i for i in issues if i["type"] == "high_cost"]
        if high_cost_issues:
            recommendations.append("查询成本较高，建议:")
            recommendations.append("  - 检查WHERE条件是否使用了合适的索引")
            recommendations.append("  - 考虑重写复杂的子查询")
            recommendations.append("  - 检查JOIN条件是否有索引支持")
        
        seq_scan_issues = [i for i in issues if i["type"] == "seq_scan"]
        if seq_scan_issues:
            recommendations.append("存在全表扫描，建议:")
            recommendations.append("  - 在经常用于WHERE条件的列上创建索引")
            recommendations.append("  - 在JOIN条件的列上创建索引")
            recommendations.append("  - 考虑使用复合索引优化多列查询")
        
        slow_execution_issues = [i for i in issues if i["type"] == "slow_execution"]
        if slow_execution_issues:
            recommendations.append("执行时间较长，建议:")
            recommendations.append("  - 优化查询逻辑，减少不必要的数据处理")
            recommendations.append("  - 考虑数据分页或限制返回结果集大小")
            recommendations.append("  - 检查是否需要更新表统计信息")
        
        return recommendations
