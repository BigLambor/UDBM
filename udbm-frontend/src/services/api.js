import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 可以在这里添加认证token
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data;
  },
  error => {
    if (error.response) {
      // 服务器返回错误状态码
      console.error('API Error:', error.response.data);
      throw new Error(error.response.data.message || '请求失败');
    } else if (error.request) {
      // 网络错误
      console.error('Network Error:', error.request);
      throw new Error('网络连接失败');
    } else {
      // 其他错误
      console.error('Request Error:', error.message);
      throw new Error(error.message);
    }
  }
);

// 数据库相关API
export const databaseAPI = {
  // 获取数据库列表
  getDatabases: (params = {}) => api.get('/databases/', { params }),

  // 获取数据库详情
  getDatabase: (id) => api.get(`/databases/${id}`),

  // 创建数据库实例
  createDatabase: (data) => api.post('/databases/', data),

  // 更新数据库实例
  updateDatabase: (id, data) => api.put(`/databases/${id}`, data),

  // 删除数据库实例
  deleteDatabase: (id) => api.delete(`/databases/${id}`),

  // 测试数据库连接
  testConnection: (id) => api.post(`/databases/${id}/test-connection`),

  // 获取数据库分组
  getDatabaseGroups: () => api.get('/database-groups/'),

  // 创建数据库分组
  createDatabaseGroup: (data) => api.post('/database-groups/', data),
};

// 监控相关API
export const monitoringAPI = {
  // 获取监控指标
  getMetrics: (dbId, params) => api.get(`/databases/${dbId}/metrics`, { params }),

  // 获取告警列表
  getAlerts: (params = {}) => api.get('/alerts/', { params }),

  // 获取告警规则
  getAlertRules: () => api.get('/alert-rules/'),
};

// 备份相关API
export const backupAPI = {
  // 获取备份策略
  getBackupPolicies: () => api.get('/backup-policies/'),

  // 获取备份任务
  getBackupTasks: (params = {}) => api.get('/backup-tasks/', { params }),

  // 创建备份任务
  createBackup: (dbId, data) => api.post(`/databases/${dbId}/backup`, data),
};

// 巡检相关API
export const inspectionAPI = {
  // 获取巡检任务
  getInspectionTasks: (params = {}) => api.get('/inspection-tasks/', { params }),

  // 创建巡检任务
  createInspection: (dbId, data) => api.post(`/databases/${dbId}/inspection`, data),
};

// 用户相关API
export const userAPI = {
  // 获取用户列表
  getUsers: (params = {}) => api.get('/users/', { params }),

  // 获取用户信息
  getUser: (id) => api.get(`/users/${id}`),

  // 创建用户
  createUser: (data) => api.post('/users/', data),

  // 更新用户
  updateUser: (id, data) => api.put(`/users/${id}`, data),

  // 删除用户
  deleteUser: (id) => api.delete(`/users/${id}`),

  // 获取角色列表
  getRoles: () => api.get('/roles/'),
};

// 性能调优API
export const performanceAPI = {
  // 获取数据库列表（复用数据库API）
  getDatabases: (params = {}) => api.get('/databases/', { params }),

  // 性能监控仪表板
  getPerformanceDashboard: (databaseId, hours = 24) =>
    api.get(`/performance/dashboard/${databaseId}`, { params: { hours } }),

  // 慢查询分析
  getSlowQueries: (databaseId, params = {}) =>
    api.get(`/performance/slow-queries/${databaseId}`, { params }),

  captureSlowQueries: (databaseId, threshold = 1.0) =>
    api.post(`/performance/slow-queries/${databaseId}/capture`, { threshold_seconds: threshold }),

  getQueryPatterns: (databaseId, days = 7) =>
    api.get(`/performance/query-patterns/${databaseId}`, { params: { days } }),

  getPerformanceStatistics: (databaseId, days = 7) =>
    api.get(`/performance/statistics/${databaseId}`, { params: { days } }),

  analyzeQuery: (data) => api.post('/performance/analyze-query', data),

  // 索引优化
  getIndexSuggestions: (databaseId, params = {}) =>
    api.get(`/performance/index-suggestions/${databaseId}`, { params }),

  createIndexTask: (databaseId, data) =>
    api.post(`/performance/tasks/${databaseId}/create-index`, data),

  // 系统诊断
  performSystemDiagnosis: (databaseId) =>
    api.post(`/performance/diagnose/${databaseId}`),

  getSystemDiagnoses: (databaseId, limit = 10) =>
    api.get(`/performance/diagnoses/${databaseId}`, { params: { limit } }),

  // 调优任务管理
  getTuningTasks: (databaseId = null, params = {}) => {
    const url = databaseId ? `/performance/tasks/${databaseId}` : '/performance/tasks';
    return api.get(url, { params });
  },

  executeTask: (taskId) => api.post('/performance/tasks/execute', { task_id: taskId }),

  // 指标收集
  collectPerformanceMetrics: (databaseId) =>
    api.post(`/performance/collect-metrics/${databaseId}`),

  getPerformanceMetrics: (databaseId, params = {}) =>
    api.get(`/performance/metrics/${databaseId}`, { params }),

  getLatestMetrics: (databaseId) =>
    api.get(`/performance/latest-metrics/${databaseId}`),

  // 后台任务
  startBackgroundMetricCollection: (databaseId) =>
    api.post(`/performance/background/collect-metrics/${databaseId}`),

  startBackgroundSlowQueryCapture: (databaseId, threshold = 1.0) =>
    api.post(`/performance/background/capture-slow-queries/${databaseId}`, { threshold_seconds: threshold }),

  // 实时监控管理
  startRealtimeMonitoring: (databaseId, interval = 60) =>
    api.post(`/performance/realtime-monitoring/${databaseId}/start`, { interval_seconds: interval }),

  stopRealtimeMonitoring: (databaseId) =>
    api.post(`/performance/realtime-monitoring/${databaseId}/stop`),

  getMonitoringStatus: (databaseId) =>
    api.get(`/performance/monitoring-status/${databaseId}`),

  // 告警和建议
  getAlerts: (databaseId) =>
    api.get(`/performance/alerts/${databaseId}`),

  getSystemRecommendations: (databaseId) =>
    api.get(`/performance/recommendations/${databaseId}`),

  // 性能报告
  generatePerformanceReport: (databaseId, days = 7) =>
    api.post(`/performance/reports/${databaseId}/generate`, { days }),

  // 执行计划分析
  analyzeExecutionPlan: (databaseId, queryText) =>
    api.post(`/performance/analyze-execution-plan/${databaseId}`, { query_text: queryText }),

  getExecutionPlans: (databaseId, limit = 50) =>
    api.get(`/performance/execution-plans/${databaseId}`, { params: { limit } }),

  compareExecutionPlans: (plan1Id, plan2Id) =>
    api.post('/performance/compare-execution-plans', {
      plan1_id: plan1Id,
      plan2_id: plan2Id
    }),

  getExecutionPlanVisualization: (planId) =>
    api.get(`/performance/execution-plan-visualization/${planId}`),

  // 深度查询分析
  deepQueryAnalysis: (databaseId, queryText) =>
    api.post(`/performance/deep-query-analysis/${databaseId}`, { query_text: queryText }),

  // PostgreSQL特有API

  // 配置分析
  analyzePostgresConfig: (databaseId) =>
    api.get(`/performance/postgres/config-analysis/${databaseId}`),

  // VACUUM策略
  getVacuumStrategy: (databaseId) =>
    api.get(`/performance/postgres/vacuum-strategy/${databaseId}`),

  // 内存优化
  optimizeMemorySettings: (databaseId, systemInfo) =>
    api.post(`/performance/postgres/optimize-memory/${databaseId}`, systemInfo),

  // 连接优化
  optimizeConnectionSettings: (databaseId, workloadInfo) =>
    api.post(`/performance/postgres/optimize-connections/${databaseId}`, workloadInfo),

  // 生成调优脚本
  generateTuningScript: (databaseId, analysisResults) =>
    api.post(`/performance/postgres/generate-tuning-script/${databaseId}`, analysisResults),

  // VACUUM任务
  createVacuumTask: (databaseId, tableName, vacuumType = 'VACUUM') =>
    api.post(`/performance/postgres/create-vacuum-task/${databaseId}`, null, {
      params: { table_name: tableName, vacuum_type: vacuumType }
    }),

  // ANALYZE任务
  createAnalyzeTask: (databaseId, tableName) =>
    api.post(`/performance/postgres/create-analyze-task/${databaseId}`, null, {
      params: { table_name: tableName }
    }),

  // REINDEX任务
  createReindexTask: (databaseId, indexName) =>
    api.post(`/performance/postgres/create-reindex-task/${databaseId}`, null, {
      params: { index_name: indexName }
    }),

  // 表健康分析
  getTableHealthAnalysis: (databaseId) =>
    api.get(`/performance/postgres/table-health/${databaseId}`),

  // PostgreSQL索引建议
  getPostgresIndexRecommendations: (databaseId) =>
    api.get(`/performance/postgres/index-recommendations/${databaseId}`),

  // PostgreSQL性能洞察
  getPostgresPerformanceInsights: (databaseId) =>
    api.get(`/performance/postgres/performance-insights/${databaseId}`),

  // =====================================
  // MySQL 增强调优 API 接口
  // =====================================

  // MySQL 基础分析接口
  analyzeMySQLConfig: (databaseId) =>
    api.get(`/performance/mysql/config-analysis/${databaseId}`),

  analyzeMySQLStorageEngine: (databaseId) =>
    api.get(`/performance/mysql/storage-engine-analysis/${databaseId}`),

  analyzeMySQLHardware: (databaseId) =>
    api.get(`/performance/mysql/hardware-analysis/${databaseId}`),

  analyzeMySQLSecurity: (databaseId) =>
    api.get(`/performance/mysql/security-analysis/${databaseId}`),

  analyzeMySQLReplication: (databaseId) =>
    api.get(`/performance/mysql/replication-analysis/${databaseId}`),

  analyzeMySQLPartition: (databaseId) =>
    api.get(`/performance/mysql/partition-analysis/${databaseId}`),

  analyzeMySQLBackup: (databaseId) =>
    api.get(`/performance/mysql/backup-analysis/${databaseId}`),

  // MySQL 综合分析接口
  comprehensiveMySQLAnalysis: (databaseId, includeAreas) =>
    api.post(`/performance/mysql/comprehensive-analysis/${databaseId}`, {
      include_areas: includeAreas || ["config", "storage", "hardware", "security", "replication", "partition", "backup"]
    }),

  getMySQLOptimizationSummary: (databaseId) =>
    api.get(`/performance/mysql/optimization-summary/${databaseId}`),

  getMySQLPerformanceInsights: (databaseId) =>
    api.get(`/performance/mysql/performance-insights/${databaseId}`),

  // =====================================
  // OceanBase 调优 API 接口
  // =====================================

  analyzeOceanBaseConfig: (databaseId) =>
    api.get(`/performance/oceanbase/config-analysis/${databaseId}`),

  getOceanBaseMaintenanceStrategy: (databaseId) =>
    api.get(`/performance/oceanbase/maintenance-strategy/${databaseId}`),

  generateOceanBaseTuningScript: (databaseId, analysisResults) =>
    api.post(`/performance/oceanbase/generate-tuning-script/${databaseId}`, analysisResults),

  // MySQL 实用工具接口
  generateMySQLTuningScript: (databaseId, optimizationAreas) =>
    api.post(`/performance/mysql/generate-tuning-script/${databaseId}`, null, {
      params: { optimization_areas: optimizationAreas }
    }),

  quickMySQLOptimization: (databaseId, focusArea = 'performance') =>
    api.post(`/performance/mysql/quick-optimization/${databaseId}`, null, {
      params: { focus_area: focusArea }
    }),
};

// 健康检查API
export const healthAPI = {
  // 基础健康检查
  healthCheck: () => api.get('/health/'),

  // 数据库健康检查
  databaseHealthCheck: () => api.get('/health/database'),

  // 详细健康检查
  detailedHealthCheck: () => api.get('/health/detailed'),
};

export default api;
