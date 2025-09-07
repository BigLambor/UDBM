"""
PostgreSQL Provider 适配器
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.performance_tuning.system_monitor import SystemMonitor
from app.services.performance_tuning.slow_query_analyzer import SlowQueryAnalyzer
from app.services.performance_tuning.postgres_config_optimizer import PostgreSQLConfigOptimizer
from app.services.performance_tuning.tuning_executor import TuningExecutor


class _PGMonitor:
    def __init__(self, session: Session):
        self._m = SystemMonitor(session)

    def dashboard(self, database_id: int, hours: int = 24) -> Dict[str, Any]:
        return self._m.get_performance_dashboard(database_id, hours)

    def collect_metrics(self, database_id: int) -> List[Dict[str, Any]]:
        return self._m.collect_system_metrics(database_id)

    def save_metrics(self, metrics: List[Dict[str, Any]]):
        return self._m.save_performance_metrics(metrics)

    def history(self, database_id: int, metric_type: str, hours: int = 24):
        return self._m.get_metrics_history(database_id, metric_type, hours)

    def latest_metrics(self, database_id: int) -> Dict[str, Any]:
        return self._m.get_latest_metrics(database_id)

    def alerts(self, database_id: int) -> List[Dict[str, Any]]:
        return self._m.check_alerts(database_id)

    def recommendations(self, database_id: int) -> List[Dict[str, Any]]:
        return self._m.get_system_recommendations(database_id)

    def report(self, database_id: int, days: int = 7) -> Dict[str, Any]:
        return self._m.generate_performance_report(database_id, days)

    def start_realtime(self, database_id: int, interval_seconds: int = 60) -> Dict[str, Any]:
        return self._m.start_realtime_monitoring(database_id, interval_seconds)

    def stop_realtime(self, database_id: int) -> Dict[str, Any]:
        return self._m.stop_realtime_monitoring(database_id)

    def status(self, database_id: int) -> Dict[str, Any]:
        return self._m.get_monitoring_status(database_id)


class _PGSlowQueries:
    def __init__(self, session: Session):
        self._s = SlowQueryAnalyzer(session)

    def list(self, database_id: int, limit: int, offset: int):
        return self._s.get_slow_queries(database_id, limit, offset)

    def capture(self, database_id: int, threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
        return self._s.capture_slow_queries(database_id, threshold_seconds)

    def save(self, slow_query_data: Dict[str, Any]):
        return self._s.save_slow_query(slow_query_data)

    def analyze_text(self, query_text: str, execution_time: float, rows_examined: int) -> Dict[str, Any]:
        return self._s.generate_optimization_suggestions(query_text, execution_time, rows_examined)

    def patterns(self, database_id: int, days: int = 7) -> Dict[str, Any]:
        return self._s.analyze_query_patterns(database_id, days)

    def statistics(self, database_id: int, days: int = 7) -> Dict[str, Any]:
        return self._s.get_query_statistics(database_id, days)


class _PGConfig:
    def __init__(self, session: Session):
        self._o = PostgreSQLConfigOptimizer(session)

    def analyze_config(self, database_id: int) -> Dict[str, Any]:
        return self._o.analyze_configuration(database_id)

    def maintenance_strategy(self, database_id: int) -> Dict[str, Any]:
        return self._o.generate_vacuum_strategy(database_id)

    def optimize_memory(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        return self._o.optimize_memory_settings(system_info)

    def optimize_connections(self, workload_info: Dict[str, Any]) -> Dict[str, Any]:
        return self._o.optimize_connection_settings(workload_info)

    def generate_tuning_script(self, analysis_results: Dict[str, Any]) -> str:
        return self._o.generate_performance_tuning_script(analysis_results)


class _PGExecutor:
    def __init__(self, session: Session):
        self._session = session
        self._e = TuningExecutor(session)

    def execute_task(self, task_id: int) -> Dict[str, Any]:
        return self._e.execute_task(task_id)

    def stats(self, database_id: Optional[int] = None) -> Dict[str, Any]:
        return self._e.get_task_statistics(database_id)


class PostgresProvider:
    def __init__(self, session: Session):
        self.monitor = _PGMonitor(session)
        self.slow_queries = _PGSlowQueries(session)
        self.optimizer = _PGConfig(session)
        self.executor = _PGExecutor(session)

