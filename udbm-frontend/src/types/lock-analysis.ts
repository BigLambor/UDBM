/**
 * 锁分析模块类型定义
 * 
 * 与后端API完全对应的TypeScript类型
 */

// ==================== 仪表板响应 V2 ====================

export interface LockDashboardResponseV2 {
  meta: DashboardMeta;
  metrics: Record<string, MetricValue>;
  trends: Record<string, TrendPoint[]>;
  alerts: Alert[];
  details: DashboardDetails;
}

// ==================== 元数据 ====================

export interface DashboardMeta {
  database_id: number;
  database_type: string;
  collection_timestamp: string;
  analysis_timestamp: string;
  time_range: TimeRange;
  data_source: string;
  is_live: boolean;
  cache_hit: boolean;
  duration_ms: number;
}

export interface TimeRange {
  start: string;
  end: string;
  duration: string;
}

// ==================== 指标值 ====================

export interface MetricValue {
  value: number | string;
  unit?: string;
  status: MetricStatus;
  threshold?: number;
  change_percent?: number;
  previous_value?: number | string;
}

export type MetricStatus = 'good' | 'normal' | 'warning' | 'critical';

// ==================== 趋势数据 ====================

export interface TrendPoint {
  timestamp: string;
  value: number;
  label?: string;
}

// ==================== 告警 ====================

export interface Alert {
  id: string;
  severity: AlertSeverity;
  type: AlertType;
  title: string;
  message: string;
  timestamp: string;
  affected_objects?: string[];
  recommended_actions?: Action[];
}

export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low';
export type AlertType = 'deadlock' | 'timeout' | 'high_wait' | 'contention' | 'health';

export interface Action {
  id: string;
  label: string;
  type: ActionType;
  payload: Record<string, any>;
}

export type ActionType = 'navigate' | 'api_call' | 'external_link';

// ==================== 详细数据 ====================

export interface DashboardDetails {
  hot_objects: ContentionObject[];
  active_wait_chains: WaitChainSummary[];
  top_recommendations: OptimizationAdvice[];
  lock_type_distribution: Record<string, number>;
}

export interface ContentionObject {
  object_name: string;
  contention_count: number;
  total_wait_time: number;
  avg_wait_time: number;
  max_wait_time: number;
  priority: string;
  affected_sessions?: number;
}

export interface WaitChainSummary {
  chain_id: string;
  chain_length: number;
  total_wait_time: number;
  severity: string;
  head_session: string;
  tail_session: string;
  is_cycle?: boolean;
}

export interface OptimizationAdvice {
  advice_id: string;
  type: string;
  priority: string;
  title: string;
  description: string;
  object_name?: string;
  impact_score: number;
  sql_script?: string;
  rollback_script?: string;
  estimated_improvement: string;
  actions: string[];
}

// ==================== 数据库信息 ====================

export interface Database {
  id: number;
  name: string;
  type: string;
  host: string;
  port: number;
  status: string;
}

// ==================== 监控配置 ====================

export interface MonitoringConfig {
  enabled: boolean;
  collection_interval: number;
  retention_days: number;
  alert_thresholds: AlertThresholds;
}

export interface AlertThresholds {
  wait_time_p99: number;
  deadlock_count: number;
  chain_length: number;
  timeout_rate: number;
}

// ==================== 辅助类型 ====================

export interface TimeRangeOption {
  value: string;
  label: string;
  duration: number; // milliseconds
}

export const TIME_RANGE_OPTIONS: TimeRangeOption[] = [
  { value: '5m', label: '过去5分钟', duration: 5 * 60 * 1000 },
  { value: '15m', label: '过去15分钟', duration: 15 * 60 * 1000 },
  { value: '1h', label: '过去1小时', duration: 60 * 60 * 1000 },
  { value: '6h', label: '过去6小时', duration: 6 * 60 * 60 * 1000 },
  { value: '24h', label: '过去24小时', duration: 24 * 60 * 60 * 1000 },
  { value: '7d', label: '过去7天', duration: 7 * 24 * 60 * 60 * 1000 }
];

// ==================== 工具函数类型 ====================

export interface FormatOptions {
  decimals?: number;
  unit?: string;
  compact?: boolean;
}
