#!/usr/bin/env python3
"""
简单的Mock后端服务，用于测试MySQL接口
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import random

app = FastAPI(title="UDBM Mock Backend", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock数据生成函数
def generate_mysql_insights():
    """生成MySQL性能洞察Mock数据"""
    return {
        "database_id": 1,
        "performance_score": random.randint(60, 95),
        "health_status": {
            "status": random.choice(["excellent", "good", "fair"]),
            "description": "MySQL运行状况良好",
            "health_score": random.randint(70, 95),
            "critical_issues": random.randint(0, 3)
        },
        "bottlenecks": [
            {
                "type": "cpu",
                "severity": "medium",
                "description": f"CPU使用率偏高 ({random.randint(70, 90)}%)",
                "impact": "查询响应时间增加"
            },
            {
                "type": "memory",
                "severity": "low",
                "description": f"内存使用率正常 ({random.randint(50, 70)}%)",
                "impact": "暂无明显影响"
            }
        ],
        "optimization_opportunities": [
            {
                "type": "configuration",
                "title": "配置参数优化",
                "description": "MySQL配置参数存在优化空间",
                "estimated_benefit": "20-40% 性能提升",
                "effort": "medium"
            },
            {
                "type": "index",
                "title": "索引优化",
                "description": "发现可优化的索引配置",
                "estimated_benefit": "15-30% 查询性能提升",
                "effort": "low"
            }
        ],
        "key_metrics": {
            "cpu_usage": random.randint(40, 80),
            "memory_usage": random.randint(50, 85),
            "active_connections": random.randint(10, 50),
            "qps": random.randint(100, 500)
        },
        "generated_at": datetime.now().isoformat()
    }

def generate_mysql_config_analysis():
    """生成MySQL配置分析Mock数据"""
    return {
        "optimization_score": random.randint(65, 90),
        "recommendations": [
            {
                "parameter": "innodb_buffer_pool_size",
                "current_value": "128M",
                "recommended_value": "512M",
                "impact": "high",
                "description": "InnoDB缓冲池大小偏小，建议根据可用内存调整"
            },
            {
                "parameter": "max_connections",
                "current_value": "151",
                "recommended_value": "300",
                "impact": "medium",
                "description": "最大连接数可以适当增加以支持更多并发"
            },
            {
                "parameter": "query_cache_size",
                "current_value": "0",
                "recommended_value": "64M",
                "impact": "medium",
                "description": "启用查询缓存可以提高重复查询的性能"
            }
        ],
        "analysis_timestamp": datetime.now().isoformat()
    }

def generate_mysql_optimization_summary():
    """生成MySQL优化总结Mock数据"""
    return {
        "overall_health_score": random.randint(70, 95),
        "optimization_statistics": {
            "high_impact_recommendations": random.randint(2, 8),
            "medium_impact_recommendations": random.randint(5, 15),
            "low_impact_recommendations": random.randint(3, 10),
            "critical_security_issues": random.randint(0, 3),
            "total_recommendations": random.randint(10, 30)
        },
        "summary": {
            "strengths": [
                "数据库基础配置正确",
                "索引使用合理",
                "连接池配置适当"
            ],
            "areas_for_improvement": [
                "InnoDB缓冲池可以进一步优化",
                "部分查询存在优化空间",
                "安全配置需要加强"
            ],
            "priority_actions": [
                "调整innodb_buffer_pool_size参数",
                "启用慢查询日志分析",
                "配置SSL加密连接"
            ]
        },
        "generated_at": datetime.now().isoformat()
    }

# 健康检查接口
@app.get("/api/v1/health/")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "UDBM Mock Backend"
    }

# 数据库列表接口
@app.get("/api/v1/databases/")
async def get_databases():
    """获取数据库列表"""
    return [
        {
            "id": 1,
            "name": "prod-postgres-01",
            "type": "postgresql",
            "host": "192.168.1.100",
            "port": 5432,
            "database_name": "production_db",
            "username": "postgres",
            "status": "active",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": 2,
            "name": "prod-mysql-01",
            "type": "mysql",
            "host": "192.168.1.101",
            "port": 3306,
            "database_name": "production_db",
            "username": "mysql",
            "status": "active",
            "created_at": "2024-01-15T11:00:00Z",
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": 3,
            "name": "test-postgres-01",
            "type": "postgresql",
            "host": "192.168.1.102",
            "port": 5432,
            "database_name": "test_db",
            "username": "postgres",
            "status": "active",
            "created_at": "2024-01-16T09:15:00Z",
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": 4,
            "name": "test-mysql-01",
            "type": "mysql",
            "host": "192.168.1.103",
            "port": 3306,
            "database_name": "test_db",
            "username": "mysql",
            "status": "active",
            "created_at": "2024-01-16T09:30:00Z",
            "updated_at": datetime.now().isoformat()
        }
    ]

# MySQL性能调优接口
@app.get("/api/v1/performance/mysql/config-analysis/{database_id}")
async def mysql_config_analysis(database_id: int):
    return generate_mysql_config_analysis()

@app.get("/api/v1/performance/mysql/storage-engine-analysis/{database_id}")
async def mysql_storage_engine_analysis(database_id: int):
    return {
        "storage_engines": {
            "InnoDB": {
                "usage_percentage": random.randint(80, 95),
                "optimization_score": random.randint(75, 90),
                "recommendations": [
                    "调整innodb_buffer_pool_size",
                    "优化innodb_log_file_size"
                ]
            },
            "MyISAM": {
                "usage_percentage": random.randint(5, 20),
                "optimization_score": random.randint(60, 80),
                "recommendations": [
                    "考虑迁移到InnoDB"
                ]
            }
        },
        "analysis_timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/performance/mysql/hardware-analysis/{database_id}")
async def mysql_hardware_analysis(database_id: int):
    return {
        "cpu_optimization": {
            "current_usage": random.randint(40, 80),
            "recommendations": ["增加CPU核心数", "优化查询并发度"]
        },
        "memory_optimization": {
            "total_memory": "8GB",
            "mysql_usage": "3.2GB",
            "recommendations": ["增加内存", "调整缓冲池大小"]
        },
        "disk_optimization": {
            "io_utilization": random.randint(30, 70),
            "recommendations": ["使用SSD存储", "分离数据和日志文件"]
        },
        "analysis_timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/performance/mysql/security-analysis/{database_id}")
async def mysql_security_analysis(database_id: int):
    return {
        "security_score": random.randint(60, 85),
        "vulnerabilities": [
            {
                "severity": "high",
                "issue": "Root用户允许远程登录",
                "solution": "限制root用户只能本地登录",
                "sql": "DELETE FROM mysql.user WHERE User='root' AND Host!='localhost';"
            },
            {
                "severity": "medium", 
                "issue": "未启用SSL加密",
                "solution": "配置SSL证书启用加密连接",
                "sql": "-- 需要配置SSL证书文件"
            }
        ],
        "analysis_timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/performance/mysql/replication-analysis/{database_id}")
async def mysql_replication_analysis(database_id: int):
    return {
        "replication_status": "not_configured",
        "recommendations": [
            "配置主从复制提高可用性",
            "设置读写分离",
            "配置半同步复制"
        ],
        "analysis_timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/performance/mysql/partition-analysis/{database_id}")
async def mysql_partition_analysis(database_id: int):
    return {
        "partition_candidates": [
            {
                "table_name": "user_logs",
                "size_gb": 15.2,
                "partition_strategy": "RANGE by date",
                "estimated_improvement": "40-60% 查询性能提升"
            }
        ],
        "analysis_timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/performance/mysql/backup-analysis/{database_id}")
async def mysql_backup_analysis(database_id: int):
    return {
        "backup_status": "configured",
        "backup_frequency": "daily",
        "optimization_recommendations": [
            {
                "severity": "medium",
                "solution": "配置增量备份策略",
                "benefits": ["减少备份时间", "节省存储空间"]
            }
        ],
        "analysis_timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/performance/mysql/optimization-summary/{database_id}")
async def mysql_optimization_summary(database_id: int):
    return generate_mysql_optimization_summary()

@app.get("/api/v1/performance/mysql/performance-insights/{database_id}")
async def mysql_performance_insights(database_id: int):
    return generate_mysql_insights()

@app.post("/api/v1/performance/mysql/comprehensive-analysis/{database_id}")
async def mysql_comprehensive_analysis(database_id: int, request_data: dict = None):
    return {
        "database_id": database_id,
        "analysis_timestamp": datetime.now().isoformat(),
        "included_areas": request_data.get("include_areas", []) if request_data else [],
        "analysis_results": {
            "config": generate_mysql_config_analysis(),
            "storage": {"optimization_score": random.randint(70, 90)},
            "hardware": {"cpu_score": random.randint(60, 85)},
            "security": {"security_score": random.randint(65, 80)}
        },
        "summary": generate_mysql_optimization_summary()
    }

@app.post("/api/v1/performance/mysql/generate-tuning-script/{database_id}")
async def mysql_generate_tuning_script(database_id: int, request_data: dict = None):
    return {
        "tuning_script": """-- MySQL性能调优脚本
-- 生成时间: """ + datetime.now().isoformat() + """

-- InnoDB缓冲池优化
SET GLOBAL innodb_buffer_pool_size = 536870912; -- 512MB

-- 连接数优化
SET GLOBAL max_connections = 300;

-- 查询缓存优化
SET GLOBAL query_cache_size = 67108864; -- 64MB
SET GLOBAL query_cache_type = 1;

-- 日志优化
SET GLOBAL innodb_log_file_size = 268435456; -- 256MB

-- 安全配置
-- 建议在配置文件中设置以下参数:
-- bind-address = 127.0.0.1
-- ssl-cert = /path/to/cert.pem
-- ssl-key = /path/to/key.pem
""",
        "generated_at": datetime.now().isoformat(),
        "database_id": database_id,
        "optimization_areas": request_data.get("optimization_areas", []) if request_data else [],
        "description": "MySQL综合性能调优脚本，包含多维度优化配置"
    }

@app.post("/api/v1/performance/mysql/quick-optimization/{database_id}")
async def mysql_quick_optimization(database_id: int, request_data: dict = None):
    focus_area = request_data.get("focus_area", "performance") if request_data else "performance"
    
    recommendations = []
    if focus_area == "performance":
        recommendations = [
            {
                "category": "配置优化",
                "action": "增加InnoDB缓冲池大小到系统内存的70-80%",
                "impact": "high",
                "sql": "SET GLOBAL innodb_buffer_pool_size = 536870912;",
                "estimated_improvement": "30-50% 查询性能提升"
            },
            {
                "category": "索引优化",
                "action": "为频繁查询的列添加索引",
                "impact": "high",
                "estimated_improvement": "40-70% 查询速度提升"
            }
        ]
    elif focus_area == "security":
        recommendations = [
            {
                "category": "安全加固",
                "action": "禁用root远程登录",
                "impact": "critical",
                "sql": "DELETE FROM mysql.user WHERE User='root' AND Host!='localhost'; FLUSH PRIVILEGES;"
            },
            {
                "category": "安全加固", 
                "action": "启用SSL加密连接",
                "impact": "high",
                "sql": "-- 需要配置SSL证书"
            }
        ]
    
    return {
        "database_id": database_id,
        "focus_area": focus_area,
        "quick_recommendations": recommendations,
        "generated_at": datetime.now().isoformat(),
        "next_steps": [
            "执行高优先级建议",
            "监控性能变化",
            "定期评估优化效果"
        ]
    }

# 慢查询分析接口
@app.get("/api/v1/performance/slow-queries/{database_id}")
async def get_slow_queries(database_id: int):
    """获取慢查询列表"""
    return {
        "slow_queries": [
            {
                "id": 1,
                "query_text": "SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.created_at >= '2024-01-01' AND c.region = 'Asia' ORDER BY o.total_amount DESC LIMIT 100",
                "execution_time": 2.45,
                "rows_examined": 125000,
                "rows_sent": 100,
                "timestamp": "2024-01-20T10:30:15Z",
                "database_name": "production",
                "user": "app_user",
                "lock_time": 0.001,
                "frequency": 15
            },
            {
                "id": 2,
                "query_text": "UPDATE products SET stock_quantity = stock_quantity - 1 WHERE id IN (SELECT product_id FROM order_items WHERE order_id = 12345)",
                "execution_time": 1.82,
                "rows_examined": 50000,
                "rows_sent": 0,
                "timestamp": "2024-01-20T10:25:30Z",
                "database_name": "production",
                "user": "app_user",
                "lock_time": 0.005,
                "frequency": 8
            },
            {
                "id": 3,
                "query_text": "SELECT COUNT(*) FROM user_activities WHERE activity_type = 'login' AND created_at BETWEEN '2024-01-01' AND '2024-01-20'",
                "execution_time": 3.21,
                "rows_examined": 2500000,
                "rows_sent": 1,
                "timestamp": "2024-01-20T10:20:45Z",
                "database_name": "production",
                "user": "analytics_user",
                "lock_time": 0.002,
                "frequency": 25
            },
            {
                "id": 4,
                "query_text": "DELETE FROM temp_reports WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY)",
                "execution_time": 1.95,
                "rows_examined": 180000,
                "rows_sent": 0,
                "timestamp": "2024-01-20T09:15:20Z",
                "database_name": "production",
                "user": "cleanup_job",
                "lock_time": 0.008,
                "frequency": 3
            }
        ],
        "total_count": 4,
        "generated_at": datetime.now().isoformat()
    }

@app.post("/api/v1/performance/slow-queries/{database_id}/capture")
async def capture_slow_queries(database_id: int, request_data: dict = None):
    """捕获慢查询"""
    threshold = request_data.get("threshold_seconds", 1.0) if request_data else 1.0
    
    return {
        "message": f"慢查询捕获已启动，阈值: {threshold}秒",
        "queries": [
            {
                "id": 5,
                "query_text": "SELECT u.*, p.profile_data FROM users u LEFT JOIN profiles p ON u.id = p.user_id WHERE u.last_login < '2024-01-01'",
                "execution_time": threshold + random.uniform(0.5, 2.0),
                "rows_examined": random.randint(10000, 100000),
                "rows_sent": random.randint(100, 5000),
                "timestamp": datetime.now().isoformat(),
                "database_name": "production",
                "user": "app_user",
                "lock_time": random.uniform(0.001, 0.01),
                "frequency": random.randint(1, 20)
            }
        ],
        "captured_at": datetime.now().isoformat(),
        "threshold_seconds": threshold
    }

@app.get("/api/v1/performance/query-patterns/{database_id}")
async def get_query_patterns(database_id: int):
    """获取查询模式分析"""
    return {
        "query_patterns": [
            {
                "pattern_type": "SELECT",
                "count": 1250,
                "avg_execution_time": 0.85,
                "total_execution_time": 1062.5,
                "percentage": 45.2,
                "sample_query": "SELECT * FROM orders WHERE status = ?"
            },
            {
                "pattern_type": "UPDATE",
                "count": 890,
                "avg_execution_time": 1.2,
                "total_execution_time": 1068.0,
                "percentage": 32.1,
                "sample_query": "UPDATE products SET stock_quantity = ? WHERE id = ?"
            },
            {
                "pattern_type": "INSERT",
                "count": 450,
                "avg_execution_time": 0.65,
                "total_execution_time": 292.5,
                "percentage": 16.3,
                "sample_query": "INSERT INTO user_activities (user_id, activity_type, created_at) VALUES (?, ?, ?)"
            },
            {
                "pattern_type": "DELETE",
                "count": 180,
                "avg_execution_time": 1.8,
                "total_execution_time": 324.0,
                "percentage": 6.4,
                "sample_query": "DELETE FROM temp_data WHERE created_at < ?"
            }
        ],
        "analysis_period": "last_24_hours",
        "total_queries": 2770,
        "generated_at": datetime.now().isoformat()
    }

@app.get("/api/v1/performance/statistics/{database_id}")
async def get_performance_statistics(database_id: int):
    """获取性能统计信息"""
    return {
        "query_statistics": {
            "total_queries": random.randint(15000, 25000),
            "slow_queries": random.randint(50, 200),
            "slow_query_percentage": round(random.uniform(0.5, 3.0), 2),
            "avg_query_time": round(random.uniform(0.1, 0.8), 3),
            "max_query_time": round(random.uniform(5.0, 15.0), 2),
            "queries_per_second": round(random.uniform(100, 500), 1)
        },
        "connection_statistics": {
            "active_connections": random.randint(20, 80),
            "max_connections": 200,
            "connection_usage_percentage": round(random.uniform(10, 40), 1),
            "aborted_connections": random.randint(0, 5),
            "threads_connected": random.randint(15, 75)
        },
        "table_statistics": {
            "total_tables": random.randint(50, 150),
            "largest_table_size_mb": round(random.uniform(500, 2000), 1),
            "total_data_size_gb": round(random.uniform(10, 100), 2),
            "fragmented_tables": random.randint(3, 15)
        },
        "index_statistics": {
            "total_indexes": random.randint(200, 800),
            "unused_indexes": random.randint(5, 25),
            "duplicate_indexes": random.randint(2, 10),
            "index_efficiency": round(random.uniform(75, 95), 1)
        },
        "generated_at": datetime.now().isoformat(),
        "analysis_period": "last_24_hours"
    }

if __name__ == "__main__":
    print("🚀 启动MySQL性能调优Mock后端服务...")
    uvicorn.run(app, host="0.0.0.0", port=8000)