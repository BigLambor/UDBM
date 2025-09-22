"""
OceanBase 分区表分析器
分析分区表设计、热点检测和分区策略优化
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import random
import hashlib
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PartitionType(Enum):
    """分区类型枚举"""
    RANGE = "RANGE"
    HASH = "HASH"
    LIST = "LIST"
    RANGE_HASH = "RANGE_HASH"
    LIST_HASH = "LIST_HASH"


@dataclass
class PartitionInfo:
    """分区信息数据结构"""
    table_name: str
    partition_name: str
    partition_type: PartitionType
    partition_key: str
    partition_value: str
    row_count: int
    data_size_mb: float
    last_updated: datetime
    is_hot: bool = False
    access_frequency: int = 0


@dataclass
class PartitionAnalysis:
    """分区分析结果"""
    table_name: str
    total_partitions: int
    hot_partitions: int
    cold_partitions: int
    data_distribution_score: float
    access_pattern_score: float
    optimization_score: float
    recommendations: List[Dict[str, Any]]


class OceanBasePartitionAnalyzer:
    """OceanBase 分区表分析器"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.use_real_data = False  # 首版使用Mock数据
    
    def analyze_partition_tables(self, database_id: int) -> Dict[str, Any]:
        """分析所有分区表"""
        partition_tables = self._get_partition_tables(database_id)
        
        analysis_results = {
            "summary": self._analyze_partition_summary(partition_tables),
            "table_analysis": [],
            "hotspot_analysis": self._analyze_hotspots(partition_tables),
            "distribution_analysis": self._analyze_data_distribution(partition_tables),
            "optimization_recommendations": [],
            "analysis_timestamp": datetime.now().isoformat(),
            "data_source": "mock_partition_data"
        }
        
        # 分析每个分区表
        for table in partition_tables:
            table_analysis = self._analyze_single_partition_table(table)
            analysis_results["table_analysis"].append(table_analysis)
        
        # 生成优化建议
        analysis_results["optimization_recommendations"] = self._generate_partition_optimization_recommendations(partition_tables)
        
        return analysis_results
    
    def analyze_partition_hotspots(self, database_id: int, table_name: Optional[str] = None) -> Dict[str, Any]:
        """分析分区热点"""
        partition_tables = self._get_partition_tables(database_id)
        
        if table_name:
            partition_tables = [t for t in partition_tables if t.table_name == table_name]
        
        hotspot_analysis = {
            "hot_partitions": [],
            "cold_partitions": [],
            "hotspot_patterns": {},
            "recommendations": [],
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        for table in partition_tables:
            partitions = self._get_table_partitions(table["table_name"])
            
            # 识别热点分区
            hot_partitions = [p for p in partitions if p.is_hot]
            cold_partitions = [p for p in partitions if not p.is_hot and p.access_frequency == 0]
            
            hotspot_analysis["hot_partitions"].extend([
                {
                    "table_name": p.table_name,
                    "partition_name": p.partition_name,
                    "partition_key": p.partition_key,
                    "access_frequency": p.access_frequency,
                    "data_size_mb": p.data_size_mb,
                    "hotspot_reason": self._identify_hotspot_reason(p)
                }
                for p in hot_partitions
            ])
            
            hotspot_analysis["cold_partitions"].extend([
                {
                    "table_name": p.table_name,
                    "partition_name": p.partition_name,
                    "partition_key": p.partition_key,
                    "data_size_mb": p.data_size_mb,
                    "last_accessed": p.last_updated.isoformat()
                }
                for p in cold_partitions
            ])
        
        # 分析热点模式
        hotspot_analysis["hotspot_patterns"] = self._analyze_hotspot_patterns(hotspot_analysis["hot_partitions"])
        
        # 生成热点优化建议
        hotspot_analysis["recommendations"] = self._generate_hotspot_recommendations(hotspot_analysis)
        
        return hotspot_analysis
    
    def analyze_partition_pruning(self, database_id: int, sql_queries: List[str]) -> Dict[str, Any]:
        """分析分区剪裁效果"""
        pruning_analysis = {
            "queries_with_pruning": [],
            "queries_without_pruning": [],
            "pruning_efficiency": 0.0,
            "recommendations": [],
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        for query in sql_queries:
            pruning_result = self._analyze_single_query_pruning(query)
            
            if pruning_result["has_pruning"]:
                pruning_analysis["queries_with_pruning"].append(pruning_result)
            else:
                pruning_analysis["queries_without_pruning"].append(pruning_result)
        
        # 计算剪裁效率
        total_queries = len(sql_queries)
        if total_queries > 0:
            pruning_analysis["pruning_efficiency"] = len(pruning_analysis["queries_with_pruning"]) / total_queries * 100
        
        # 生成剪裁优化建议
        pruning_analysis["recommendations"] = self._generate_pruning_recommendations(pruning_analysis)
        
        return pruning_analysis
    
    def generate_partition_optimization_script(self, analysis_results: Dict[str, Any]) -> str:
        """生成分区优化脚本"""
        script_lines = [
            "-- OceanBase 分区表优化脚本",
            f"-- 生成时间: {datetime.now().isoformat()}",
            "-- 基于分区分析结果",
            ""
        ]
        
        # 添加分区重构建议
        if "table_analysis" in analysis_results:
            script_lines.extend([
                "-- 分区表重构建议",
                "-- =================="
            ])
            
            for table_analysis in analysis_results["table_analysis"]:
                if table_analysis["optimization_score"] < 70:
                    script_lines.extend([
                        f"-- 表 {table_analysis['table_name']} 需要优化",
                        f"-- 当前优化评分: {table_analysis['optimization_score']:.1f}",
                        f"-- 建议: {table_analysis.get('primary_recommendation', '请查看详细分析')}",
                        ""
                    ])
        
        # 添加热点分区处理建议
        if "hotspot_analysis" in analysis_results:
            hot_partitions = analysis_results["hotspot_analysis"].get("hot_partitions", [])
            if hot_partitions:
                script_lines.extend([
                    "-- 热点分区处理建议",
                    "-- =================="
                ])
                
                for hot_partition in hot_partitions[:5]:  # 只显示前5个
                    script_lines.extend([
                        f"-- 热点分区: {hot_partition['table_name']}.{hot_partition['partition_name']}",
                        f"-- 访问频率: {hot_partition['access_frequency']}",
                        f"-- 建议: {hot_partition.get('hotspot_reason', '需要进一步分析')}",
                        ""
                    ])
        
        # 添加分区剪裁优化建议
        if "pruning_analysis" in analysis_results:
            pruning_efficiency = analysis_results["pruning_analysis"].get("pruning_efficiency", 0)
            if pruning_efficiency < 80:
                script_lines.extend([
                    "-- 分区剪裁优化建议",
                    "-- ==================",
                    "-- 当前剪裁效率较低，建议优化查询条件",
                    "-- 确保查询条件包含分区键",
                    "-- 考虑调整分区策略以支持更多查询模式",
                    ""
                ])
        
        # 添加通用优化建议
        script_lines.extend([
            "-- 通用分区优化建议",
            "-- ==================",
            "-- 1. 定期分析分区数据分布",
            "-- 2. 监控热点分区访问模式",
            "-- 3. 根据业务特点调整分区策略",
            "-- 4. 考虑使用组合分区解决复杂场景",
            "-- 5. 定期清理历史分区数据",
            ""
        ])
        
        return "\n".join(script_lines)
    
    def _get_partition_tables(self, database_id: int) -> List[Dict[str, Any]]:
        """获取分区表列表"""
        # 模拟分区表数据
        tables = [
            {
                "table_name": "orders",
                "partition_type": PartitionType.RANGE,
                "partition_key": "order_date",
                "total_partitions": 12,
                "total_rows": 1000000,
                "total_size_mb": 2048.5
            },
            {
                "table_name": "user_activities",
                "partition_type": PartitionType.HASH,
                "partition_key": "user_id",
                "total_partitions": 16,
                "total_rows": 5000000,
                "total_size_mb": 8192.0
            },
            {
                "table_name": "transaction_logs",
                "partition_type": PartitionType.RANGE_HASH,
                "partition_key": "transaction_date,account_id",
                "total_partitions": 24,
                "total_rows": 2000000,
                "total_size_mb": 4096.0
            },
            {
                "table_name": "product_catalog",
                "partition_type": PartitionType.LIST,
                "partition_key": "category",
                "total_partitions": 8,
                "total_rows": 500000,
                "total_size_mb": 1024.0
            }
        ]
        
        return tables
    
    def _get_table_partitions(self, table_name: str) -> List[PartitionInfo]:
        """获取表的分区信息"""
        partitions = []
        
        # 根据表名生成不同的分区数据
        if table_name == "orders":
            # 按月分区的订单表
            for i in range(12):
                month = datetime.now() - timedelta(days=i * 30)
                partition_name = f"p_{month.strftime('%Y%m')}"
                is_hot = i < 3  # 最近3个月是热点
                
                partitions.append(PartitionInfo(
                    table_name=table_name,
                    partition_name=partition_name,
                    partition_type=PartitionType.RANGE,
                    partition_key="order_date",
                    partition_value=f"'{month.strftime('%Y-%m-01')}'",
                    row_count=random.randint(50000, 150000),
                    data_size_mb=random.uniform(100.0, 500.0),
                    last_updated=month,
                    is_hot=is_hot,
                    access_frequency=random.randint(1000, 10000) if is_hot else random.randint(0, 100)
                ))
        
        elif table_name == "user_activities":
            # 按哈希分区的用户活动表
            for i in range(16):
                partition_name = f"p_{i:02d}"
                is_hot = random.random() < 0.2  # 20%的分区是热点
                
                partitions.append(PartitionInfo(
                    table_name=table_name,
                    partition_name=partition_name,
                    partition_type=PartitionType.HASH,
                    partition_key="user_id",
                    partition_value=f"hash_{i}",
                    row_count=random.randint(200000, 400000),
                    data_size_mb=random.uniform(200.0, 800.0),
                    last_updated=datetime.now() - timedelta(days=random.randint(0, 30)),
                    is_hot=is_hot,
                    access_frequency=random.randint(5000, 50000) if is_hot else random.randint(0, 1000)
                ))
        
        return partitions
    
    def _analyze_partition_summary(self, partition_tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析分区摘要"""
        total_tables = len(partition_tables)
        total_partitions = sum(t["total_partitions"] for t in partition_tables)
        total_rows = sum(t["total_rows"] for t in partition_tables)
        total_size_mb = sum(t["total_size_mb"] for t in partition_tables)
        
        partition_types = {}
        for table in partition_tables:
            ptype = table["partition_type"].value
            partition_types[ptype] = partition_types.get(ptype, 0) + 1
        
        return {
            "total_partition_tables": total_tables,
            "total_partitions": total_partitions,
            "total_rows": total_rows,
            "total_size_mb": round(total_size_mb, 2),
            "avg_partitions_per_table": round(total_partitions / total_tables, 1) if total_tables > 0 else 0,
            "partition_type_distribution": partition_types
        }
    
    def _analyze_single_partition_table(self, table: Dict[str, Any]) -> Dict[str, Any]:
        """分析单个分区表"""
        partitions = self._get_table_partitions(table["table_name"])
        
        hot_partitions = [p for p in partitions if p.is_hot]
        cold_partitions = [p for p in partitions if not p.is_hot]
        
        # 计算数据分布评分
        data_sizes = [p.data_size_mb for p in partitions]
        if data_sizes:
            avg_size = sum(data_sizes) / len(data_sizes)
            size_variance = sum((size - avg_size) ** 2 for size in data_sizes) / len(data_sizes)
            data_distribution_score = max(0, 100 - (size_variance / avg_size * 10))
        else:
            data_distribution_score = 100
        
        # 计算访问模式评分
        access_frequencies = [p.access_frequency for p in partitions]
        if access_frequencies:
            avg_freq = sum(access_frequencies) / len(access_frequencies)
            freq_variance = sum((freq - avg_freq) ** 2 for freq in access_frequencies) / len(access_frequencies)
            access_pattern_score = max(0, 100 - (freq_variance / avg_freq * 5)) if avg_freq > 0 else 100
        else:
            access_pattern_score = 100
        
        # 计算综合优化评分
        optimization_score = (data_distribution_score + access_pattern_score) / 2
        
        # 生成主要建议
        primary_recommendation = self._get_primary_recommendation(table, partitions, optimization_score)
        
        return {
            "table_name": table["table_name"],
            "partition_type": table["partition_type"].value,
            "total_partitions": len(partitions),
            "hot_partitions": len(hot_partitions),
            "cold_partitions": len(cold_partitions),
            "data_distribution_score": round(data_distribution_score, 1),
            "access_pattern_score": round(access_pattern_score, 1),
            "optimization_score": round(optimization_score, 1),
            "primary_recommendation": primary_recommendation,
            "partition_details": [
                {
                    "partition_name": p.partition_name,
                    "row_count": p.row_count,
                    "data_size_mb": round(p.data_size_mb, 2),
                    "is_hot": p.is_hot,
                    "access_frequency": p.access_frequency
                }
                for p in partitions[:10]  # 只显示前10个分区
            ]
        }
    
    def _analyze_hotspots(self, partition_tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析热点"""
        all_partitions = []
        for table in partition_tables:
            all_partitions.extend(self._get_table_partitions(table["table_name"]))
        
        hot_partitions = [p for p in all_partitions if p.is_hot]
        cold_partitions = [p for p in all_partitions if not p.is_hot]
        
        return {
            "total_hot_partitions": len(hot_partitions),
            "total_cold_partitions": len(cold_partitions),
            "hot_partition_ratio": len(hot_partitions) / len(all_partitions) * 100 if all_partitions else 0,
            "hot_partition_tables": list(set(p.table_name for p in hot_partitions)),
            "hotspot_severity": self._calculate_hotspot_severity(hot_partitions)
        }
    
    def _analyze_data_distribution(self, partition_tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析数据分布"""
        distribution_analysis = {
            "well_distributed_tables": [],
            "poorly_distributed_tables": [],
            "distribution_recommendations": []
        }
        
        for table in partition_tables:
            partitions = self._get_table_partitions(table["table_name"])
            if not partitions:
                continue
            
            # 计算数据分布均匀性
            data_sizes = [p.data_size_mb for p in partitions]
            avg_size = sum(data_sizes) / len(data_sizes)
            max_size = max(data_sizes)
            min_size = min(data_sizes)
            
            # 如果最大分区比平均大小大50%以上，认为分布不均匀
            if max_size > avg_size * 1.5:
                distribution_analysis["poorly_distributed_tables"].append({
                    "table_name": table["table_name"],
                    "max_partition_size": max_size,
                    "avg_partition_size": avg_size,
                    "size_ratio": max_size / avg_size
                })
            else:
                distribution_analysis["well_distributed_tables"].append(table["table_name"])
        
        return distribution_analysis
    
    def _generate_partition_optimization_recommendations(self, partition_tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成分区优化建议"""
        recommendations = []
        
        # 基于热点分析的建议
        hotspot_analysis = self._analyze_hotspots(partition_tables)
        if hotspot_analysis["hot_partition_ratio"] > 30:
            recommendations.append({
                "type": "hotspot_optimization",
                "priority": "high",
                "title": "分区热点优化",
                "description": f"发现{hotspot_analysis['hot_partition_ratio']:.1f}%的分区存在热点问题",
                "actions": [
                    "分析热点分区的访问模式",
                    "考虑调整分区键策略",
                    "使用组合分区分散热点",
                    "优化查询条件减少热点访问"
                ]
            })
        
        # 基于数据分布的建议
        distribution_analysis = self._analyze_data_distribution(partition_tables)
        if distribution_analysis["poorly_distributed_tables"]:
            recommendations.append({
                "type": "distribution_optimization",
                "priority": "medium",
                "title": "数据分布优化",
                "description": f"发现{len(distribution_analysis['poorly_distributed_tables'])}个表数据分布不均匀",
                "actions": [
                    "重新设计分区策略",
                    "调整分区边界",
                    "考虑使用哈希分区",
                    "定期重新平衡分区"
                ]
            })
        
        return recommendations
    
    def _identify_hotspot_reason(self, partition: PartitionInfo) -> str:
        """识别热点原因"""
        if partition.access_frequency > 10000:
            return "高频访问"
        elif partition.data_size_mb > 1000:
            return "数据量大"
        elif partition.row_count > 500000:
            return "行数过多"
        else:
            return "访问模式异常"
    
    def _analyze_hotspot_patterns(self, hot_partitions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析热点模式"""
        patterns = {
            "time_based_hotspots": 0,
            "size_based_hotspots": 0,
            "access_based_hotspots": 0,
            "table_hotspot_distribution": {}
        }
        
        for partition in hot_partitions:
            table_name = partition["table_name"]
            patterns["table_hotspot_distribution"][table_name] = patterns["table_hotspot_distribution"].get(table_name, 0) + 1
            
            # 简单的模式识别
            if partition["access_frequency"] > 5000:
                patterns["access_based_hotspots"] += 1
            if partition["data_size_mb"] > 500:
                patterns["size_based_hotspots"] += 1
        
        return patterns
    
    def _generate_hotspot_recommendations(self, hotspot_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成热点优化建议"""
        recommendations = []
        
        hot_partitions = hotspot_analysis.get("hot_partitions", [])
        if not hot_partitions:
            return recommendations
        
        # 基于热点数量的建议
        if len(hot_partitions) > 10:
            recommendations.append({
                "type": "hotspot_reduction",
                "priority": "high",
                "title": "减少热点分区数量",
                "description": f"发现{len(hot_partitions)}个热点分区，建议优化分区策略",
                "actions": [
                    "分析热点分区的共同特征",
                    "考虑调整分区键选择",
                    "使用更细粒度的分区",
                    "优化查询模式"
                ]
            })
        
        # 基于访问模式的建议
        high_freq_partitions = [p for p in hot_partitions if p["access_frequency"] > 10000]
        if high_freq_partitions:
            recommendations.append({
                "type": "access_optimization",
                "priority": "high",
                "title": "高频访问分区优化",
                "description": f"发现{len(high_freq_partitions)}个高频访问分区",
                "actions": [
                    "为高频分区添加缓存",
                    "优化相关查询的索引",
                    "考虑读写分离",
                    "监控分区性能指标"
                ]
            })
        
        return recommendations
    
    def _analyze_single_query_pruning(self, query: str) -> Dict[str, Any]:
        """分析单个查询的分区剪裁"""
        query_upper = query.upper()
        
        # 简单的剪裁分析逻辑
        has_where = "WHERE" in query_upper
        has_partition_key = any(key in query_upper for key in ["order_date", "user_id", "transaction_date", "category"])
        
        pruning_result = {
            "query": query,
            "has_pruning": has_where and has_partition_key,
            "pruning_columns": [],
            "estimated_partitions_scanned": 1 if has_where and has_partition_key else 10,
            "pruning_efficiency": 90 if has_where and has_partition_key else 10
        }
        
        # 识别剪裁列
        if "order_date" in query_upper:
            pruning_result["pruning_columns"].append("order_date")
        if "user_id" in query_upper:
            pruning_result["pruning_columns"].append("user_id")
        if "transaction_date" in query_upper:
            pruning_result["pruning_columns"].append("transaction_date")
        if "category" in query_upper:
            pruning_result["pruning_columns"].append("category")
        
        return pruning_result
    
    def _generate_pruning_recommendations(self, pruning_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成分区剪裁优化建议"""
        recommendations = []
        
        pruning_efficiency = pruning_analysis.get("pruning_efficiency", 0)
        queries_without_pruning = pruning_analysis.get("queries_without_pruning", [])
        
        if pruning_efficiency < 80:
            recommendations.append({
                "type": "pruning_optimization",
                "priority": "high",
                "title": "提高分区剪裁效率",
                "description": f"当前剪裁效率为{pruning_efficiency:.1f}%，建议优化",
                "actions": [
                    "确保查询条件包含分区键",
                    "优化WHERE子句中的分区键条件",
                    "避免在分区键上使用函数",
                    "考虑调整分区策略以支持更多查询模式"
                ]
            })
        
        if queries_without_pruning:
            recommendations.append({
                "type": "query_optimization",
                "priority": "medium",
                "title": "优化无剪裁查询",
                "description": f"发现{len(queries_without_pruning)}个查询无法进行分区剪裁",
                "actions": [
                    "重写查询以包含分区键条件",
                    "考虑创建覆盖索引",
                    "分析查询模式调整分区设计",
                    "使用查询提示强制剪裁"
                ]
            })
        
        return recommendations
    
    def _get_primary_recommendation(self, table: Dict[str, Any], partitions: List[PartitionInfo], optimization_score: float) -> str:
        """获取主要优化建议"""
        if optimization_score < 50:
            return "分区设计需要重大调整，建议重新设计分区策略"
        elif optimization_score < 70:
            return "分区设计存在一些问题，建议优化分区键和边界"
        elif optimization_score < 85:
            return "分区设计基本合理，建议微调以提高性能"
        else:
            return "分区设计良好，建议保持当前策略并持续监控"
    
    def _calculate_hotspot_severity(self, hot_partitions: List[PartitionInfo]) -> str:
        """计算热点严重程度"""
        if not hot_partitions:
            return "无热点"
        
        avg_frequency = sum(p.access_frequency for p in hot_partitions) / len(hot_partitions)
        
        if avg_frequency > 50000:
            return "严重"
        elif avg_frequency > 20000:
            return "中等"
        else:
            return "轻微"
