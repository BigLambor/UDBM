import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Statistic, Progress, Alert, Spin, Select,
  Button, Tabs, Table, Tag, Space, Tooltip, message, Switch,
  Skeleton, Result, Empty, Badge, Avatar, Divider
} from 'antd';
import {
  DashboardOutlined, DatabaseOutlined, ClockCircleOutlined,
  WarningOutlined, CheckCircleOutlined, SyncOutlined,
  BarChartOutlined, LineChartOutlined, PieChartOutlined,
  ThunderboltOutlined, AlertOutlined, ReloadOutlined,
  RiseOutlined, FallOutlined, MinusOutlined, FireOutlined,
  TrophyOutlined, RocketOutlined
} from '@ant-design/icons';
import { Line, Bar, Pie } from '@ant-design/charts';

import { performanceAPI } from '../services/api';
import DatabaseSelector from '../components/DatabaseSelector';
import DatabaseSpecificMetrics from '../components/DatabaseSpecificMetrics';
import PerformanceMetricCard from '../components/PerformanceMetricCard';
import DataSourceIndicator from '../components/DataSourceIndicator';
import OceanBaseAnalysisEnhanced from '../components/OceanBaseAnalysisEnhanced';

const { Option } = Select;
const { TabPane } = Tabs;

const PerformanceDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [selectedDatabaseType, setSelectedDatabaseType] = useState('all');
  const [dashboardData, setDashboardData] = useState(null);
  const [databases, setDatabases] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [realtimeMode, setRealtimeMode] = useState(false);
  const [monitoringStatus, setMonitoringStatus] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [realtimeInterval, setRealtimeInterval] = useState(null);
  const [performanceTrend, setPerformanceTrend] = useState(null);
  const [systemOverview, setSystemOverview] = useState(null);
  
  // PostgreSQL 特有数据
  const [postgresInsights, setPostgresInsights] = useState(null);
  const [tableHealth, setTableHealth] = useState(null);
  const [vacuumStrategy, setVacuumStrategy] = useState(null);
  const [configAnalysis, setConfigAnalysis] = useState(null);
  
  // MySQL 特有数据
  const [mysqlInsights, setMysqlInsights] = useState(null);
  const [mysqlConfigAnalysis, setMysqlConfigAnalysis] = useState(null);
  const [mysqlOptimizationSummary, setMysqlOptimizationSummary] = useState(null);
  
  // OceanBase 特有数据（复用configAnalysis/vacuumStrategy槽位）
  const [oceanBaseConfigAnalysis, setOceanBaseConfigAnalysis] = useState(null);
  const [oceanBaseMaintenance, setOceanBaseMaintenance] = useState(null);
  
  const [loadingStates, setLoadingStates] = useState({
    dashboard: false,
    monitoring: false,
    alerts: false,
    postgres: false,
    mysql: false
  });
  const [errorStates, setErrorStates] = useState({
    dashboard: null,
    monitoring: null,
    alerts: null,
    postgres: null,
    mysql: null
  });

  // 获取数据库列表
  useEffect(() => {
    fetchDatabases();
  }, []);

  // 获取仪表板数据
  useEffect(() => {
    if (selectedDatabase && selectedDatabase.id) {
      fetchDashboardData();
      fetchMonitoringStatus();
      fetchAlerts();
      
      // 如果是PostgreSQL，获取特有数据
      if (selectedDatabase.type === 'postgresql') {
        fetchPostgreSQLSpecificData();
      }
      
      // 如果是MySQL，获取特有数据
      if (selectedDatabase.type === 'mysql') {
        fetchMySQLSpecificData();
      }
      // 如果是OceanBase，获取特有数据
      if (selectedDatabase.type === 'oceanbase') {
        fetchOceanBaseSpecificData();
      }
    }
  }, [selectedDatabase]);

  // 实时监控
  useEffect(() => {
    if (realtimeMode && selectedDatabase && selectedDatabase.id) {
      const interval = setInterval(() => {
        fetchDashboardData();
        fetchAlerts();
      }, 30000); // 每30秒更新一次

      setRealtimeInterval(interval);
      return () => clearInterval(interval);
    } else if (realtimeInterval) {
      clearInterval(realtimeInterval);
      setRealtimeInterval(null);
    }
  }, [realtimeMode, selectedDatabase]);

  const fetchDatabases = async () => {
    try {
      const response = await performanceAPI.getDatabases();
      setDatabases(Array.isArray(response) ? response : []);
      if (Array.isArray(response) && response.length > 0 && !selectedDatabase) {
        setSelectedDatabase(response[0]);
      }
    } catch (error) {
      console.error('获取数据库列表失败:', error);
    }
  };

  const fetchDashboardData = async () => {
    if (!selectedDatabase || !selectedDatabase.id) {
      console.warn('没有选择数据库实例');
      return;
    }

    setLoadingStates(prev => ({ ...prev, dashboard: true }));
    setErrorStates(prev => ({ ...prev, dashboard: null }));

    try {
      const response = await performanceAPI.getPerformanceDashboard(selectedDatabase.id);
      setDashboardData(response);

      // 计算性能趋势
      if (response?.time_series_data?.metrics) {
        const trend = calculatePerformanceTrend(response.time_series_data.metrics);
        setPerformanceTrend(trend);
      }

      // 生成系统概览
      if (response?.current_stats) {
        const overview = generateSystemOverview(response.current_stats);
        setSystemOverview(overview);
      }

    } catch (error) {
      console.error('获取仪表板数据失败:', error);
      setErrorStates(prev => ({
        ...prev,
        dashboard: error.message || '获取仪表板数据失败'
      }));
    } finally {
      setLoadingStates(prev => ({ ...prev, dashboard: false }));
    }
  };

  const fetchMonitoringStatus = async () => {
    if (!selectedDatabase || !selectedDatabase.id) {
      console.warn('没有选择数据库实例');
      return;
    }

    setLoadingStates(prev => ({ ...prev, monitoring: true }));
    setErrorStates(prev => ({ ...prev, monitoring: null }));

    try {
      const response = await performanceAPI.getMonitoringStatus(selectedDatabase.id);
      setMonitoringStatus(response);
    } catch (error) {
      console.error('获取监控状态失败:', error);
      setErrorStates(prev => ({
        ...prev,
        monitoring: error.message || '获取监控状态失败'
      }));
    } finally {
      setLoadingStates(prev => ({ ...prev, monitoring: false }));
    }
  };

  // 获取PostgreSQL特有数据
  const fetchPostgreSQLSpecificData = async () => {
    if (!selectedDatabase || !selectedDatabase.id) {
      console.warn('没有选择数据库实例');
      return;
    }

    setLoadingStates(prev => ({ ...prev, postgres: true }));
    setErrorStates(prev => ({ ...prev, postgres: null }));

    try {
      const [insights, health, vacuum, config] = await Promise.all([
        performanceAPI.getPostgresPerformanceInsights(selectedDatabase.id),
        performanceAPI.getTableHealthAnalysis(selectedDatabase.id),
        performanceAPI.getVacuumStrategy(selectedDatabase.id),
        performanceAPI.analyzePostgresConfig(selectedDatabase.id)
      ]);

      setPostgresInsights(insights);
      setTableHealth(health);
      setVacuumStrategy(vacuum);
      setConfigAnalysis(config);
    } catch (error) {
      console.error('获取PostgreSQL特有数据失败:', error);
      setErrorStates(prev => ({
        ...prev,
        postgres: error.message || '获取PostgreSQL特有数据失败'
      }));
    } finally {
      setLoadingStates(prev => ({ ...prev, postgres: false }));
    }
  };

  // 获取MySQL特有数据
  const fetchMySQLSpecificData = async () => {
    if (!selectedDatabase || !selectedDatabase.id) {
      console.warn('没有选择数据库实例');
      return;
    }

    setLoadingStates(prev => ({ ...prev, mysql: true }));
    setErrorStates(prev => ({ ...prev, mysql: null }));

    try {
      const [insights, config, summary] = await Promise.all([
        performanceAPI.getMySQLPerformanceInsights(selectedDatabase.id),
        performanceAPI.analyzeMySQLConfig(selectedDatabase.id),
        performanceAPI.getMySQLOptimizationSummary(selectedDatabase.id)
      ]);

      setMysqlInsights(insights);
      setMysqlConfigAnalysis(config);
      setMysqlOptimizationSummary(summary);
    } catch (error) {
      console.error('获取MySQL特有数据失败:', error);
      setErrorStates(prev => ({
        ...prev,
        mysql: error.message || '获取MySQL特有数据失败'
      }));
    } finally {
      setLoadingStates(prev => ({ ...prev, mysql: false }));
    }
  };

  // 获取OceanBase特有数据
  const fetchOceanBaseSpecificData = async () => {
    if (!selectedDatabase || !selectedDatabase.id) {
      console.warn('没有选择数据库实例');
      return;
    }

    setLoadingStates(prev => ({ ...prev, postgres: true }));
    setErrorStates(prev => ({ ...prev, postgres: null }));

    try {
      const [config, maintenance] = await Promise.all([
        performanceAPI.analyzeOceanBaseConfig(selectedDatabase.id),
        performanceAPI.getOceanBaseMaintenanceStrategy(selectedDatabase.id)
      ]);

      setOceanBaseConfigAnalysis(config);
      setOceanBaseMaintenance(maintenance);
      // 将OceanBase数据复用到通用槽位，便于下游组件显示
      setConfigAnalysis(config);
      setVacuumStrategy(maintenance);
    } catch (error) {
      console.error('获取OceanBase特有数据失败:', error);
      setErrorStates(prev => ({
        ...prev,
        postgres: error.message || '获取OceanBase特有数据失败'
      }));
    } finally {
      setLoadingStates(prev => ({ ...prev, postgres: false }));
    }
  };

  const fetchAlerts = async () => {
    if (!selectedDatabase || !selectedDatabase.id) {
      console.warn('没有选择数据库实例');
      return;
    }

    setLoadingStates(prev => ({ ...prev, alerts: true }));
    setErrorStates(prev => ({ ...prev, alerts: null }));

    try {
      const response = await performanceAPI.getAlerts(selectedDatabase.id);
      setAlerts(response.alerts || []);
    } catch (error) {
      console.error('获取告警失败:', error);
      setErrorStates(prev => ({
        ...prev,
        alerts: error.message || '获取告警失败'
      }));
    } finally {
      setLoadingStates(prev => ({ ...prev, alerts: false }));
    }
  };

  // 计算性能趋势
  const calculatePerformanceTrend = (metrics) => {
    if (!metrics || metrics.length < 2) return null;

    const recent = metrics.slice(-10); // 最近10个数据点
    const cpuTrend = calculateTrend(recent.map(m => m.cpu_usage));
    const memoryTrend = calculateTrend(recent.map(m => m.memory_usage));
    const qpsTrend = calculateTrend(recent.map(m => m.qps));

    return {
      cpu: cpuTrend,
      memory: memoryTrend,
      qps: qpsTrend,
      overall: (cpuTrend.value + memoryTrend.value + qpsTrend.value) / 3
    };
  };

  // 计算单个指标的趋势
  const calculateTrend = (values) => {
    if (values.length < 2) return { value: 0, direction: 'stable' };

    const firstHalf = values.slice(0, Math.floor(values.length / 2));
    const secondHalf = values.slice(Math.floor(values.length / 2));

    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;

    const change = ((secondAvg - firstAvg) / firstAvg) * 100;

    let direction = 'stable';
    if (Math.abs(change) > 5) {
      direction = change > 0 ? 'increasing' : 'decreasing';
    }

    return { value: change, direction };
  };

  // 生成系统概览
  const generateSystemOverview = (currentStats) => {
    const overview = {
      healthScore: 85, // 计算健康评分
      bottlenecks: [],
      recommendations: [],
      performance: {}
    };

    // 计算健康评分
    let healthScore = 100;
    if (currentStats.cpu_usage > 80) healthScore -= 20;
    if (currentStats.memory_usage > 80) healthScore -= 15;
    if (currentStats.active_connections > 80) healthScore -= 10;
    if (currentStats.qps < 50) healthScore -= 10;

    overview.healthScore = Math.max(0, healthScore);

    // 识别瓶颈
    if (currentStats.cpu_usage > 80) {
      overview.bottlenecks.push({
        type: 'cpu',
        severity: 'high',
        description: `CPU使用率过高: ${currentStats.cpu_usage}%`
      });
    }

    if (currentStats.memory_usage > 85) {
      overview.bottlenecks.push({
        type: 'memory',
        severity: 'critical',
        description: `内存使用率严重过高: ${currentStats.memory_usage}%`
      });
    }

    // 生成建议
    if (currentStats.cpu_usage > 70) {
      overview.recommendations.push({
        type: 'optimization',
        priority: 'high',
        title: 'CPU优化建议',
        description: '考虑优化查询性能或增加CPU资源'
      });
    }

    return overview;
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setErrorStates({ dashboard: null, monitoring: null, alerts: null, postgres: null, mysql: null });

    const promises = [
      fetchDashboardData(),
      fetchMonitoringStatus(),
      fetchAlerts()
    ];

    // 根据数据库类型添加特有数据刷新
    if (selectedDatabase?.type === 'postgresql') {
      promises.push(fetchPostgreSQLSpecificData());
    } else if (selectedDatabase?.type === 'mysql') {
      promises.push(fetchMySQLSpecificData());
    } else if (selectedDatabase?.type === 'oceanbase') {
      promises.push(fetchOceanBaseSpecificData());
    }

    await Promise.all(promises);
    setRefreshing(false);
  };

  const handleToggleRealtime = async () => {
    if (!selectedDatabase || !selectedDatabase.id) {
      message.error('请先选择数据库实例');
      return;
    }

    if (!realtimeMode) {
      // 开启实时监控
      try {
        await performanceAPI.startRealtimeMonitoring(selectedDatabase.id, 60);
        setRealtimeMode(true);
        message.success('实时监控已开启');
      } catch (error) {
        message.error('开启实时监控失败');
      }
    } else {
      // 关闭实时监控
      try {
        await performanceAPI.stopRealtimeMonitoring(selectedDatabase.id);
        setRealtimeMode(false);
        message.success('实时监控已关闭');
      } catch (error) {
        message.error('关闭实时监控失败');
      }
    }
  };

  const getHealthStatusColor = (score) => {
    if (score >= 80) return '#52c41a';
    if (score >= 60) return '#faad14';
    return '#f5222e';
  };

  const getHealthStatusText = (score) => {
    if (score >= 80) return '健康';
    if (score >= 60) return '警告';
    return '异常';
  };

  // CPU使用率图表配置
  const cpuChartConfig = {
    data: dashboardData?.time_series_data?.metrics || [],
    xField: 'timestamp',
    yField: 'cpu_usage',
    seriesField: 'type',
    smooth: true,
    color: ['#1890ff', '#52c41a', '#faad14'],
    xAxis: {
      title: { text: '时间' },
      label: {
        formatter: (text) => new Date(text).toLocaleTimeString()
      }
    },
    yAxis: {
      title: { text: 'CPU使用率 (%)' },
      min: 0,
      max: 100
    }
  };

  // 内存使用率图表配置
  const memoryChartConfig = {
    data: dashboardData?.time_series_data?.metrics || [],
    xField: 'timestamp',
    yField: 'memory_usage',
    seriesField: 'type',
    smooth: true,
    color: ['#722ed1', '#13c2c2'],
    xAxis: {
      title: { text: '时间' },
      label: {
        formatter: (text) => new Date(text).toLocaleTimeString()
      }
    },
    yAxis: {
      title: { text: '内存使用量 (MB)' },
      min: 0
    }
  };

  // QPS图表配置
  const qpsChartConfig = {
    data: dashboardData?.time_series_data?.metrics || [],
    xField: 'timestamp',
    yField: 'qps',
    seriesField: 'type',
    smooth: true,
    color: ['#fa8c16'],
    xAxis: {
      title: { text: '时间' },
      label: {
        formatter: (text) => new Date(text).toLocaleTimeString()
      }
    },
    yAxis: {
      title: { text: '每秒查询数 (QPS)' },
      min: 0
    }
  };

  // 告警表格列配置
  const alertColumns = [
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      render: (level) => {
        const colors = {
          critical: 'red',
          warning: 'orange',
          info: 'blue'
        };
        return <Tag color={colors[level] || 'default'}>{level ? level.toUpperCase() : '未知'}</Tag>;
      }
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => new Date(timestamp).toLocaleString()
    }
  ];

  // 显示错误状态
  if (errorStates.dashboard) {
    return (
      <Result
        status="error"
        title="数据加载失败"
        subTitle={errorStates.dashboard}
        extra={
          <Button type="primary" onClick={handleRefresh}>
            重新加载
          </Button>
        }
      />
    );
  }

  // 显示加载状态
  if (loadingStates.dashboard && !dashboardData) {
    return (
      <div style={{ padding: '24px' }}>
        <Skeleton active />
        <Skeleton active />
        <Skeleton active />
      </div>
    );
  }

  // 显示空状态
  if (!dashboardData && !loadingStates.dashboard) {
    return (
      <Empty
        description="暂无性能数据"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      >
        <Button type="primary" onClick={handleRefresh}>
          加载数据
        </Button>
      </Empty>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <h2 style={{ margin: 0 }}>
              <DashboardOutlined style={{ marginRight: 8 }} />
              性能监控仪表板
            </h2>
            <p style={{ margin: '8px 0', color: '#666' }}>
              统一监控所有数据库类型的性能指标，智能适配不同数据库的特有功能
            </p>
          </div>
          <Space>
            <span style={{ marginRight: 8 }}>
              实时监控:
              <Switch
                checked={realtimeMode}
                onChange={handleToggleRealtime}
                style={{ marginLeft: 8 }}
                disabled={!selectedDatabase}
              />
            </span>
            <Button
              type="primary"
              icon={<ReloadOutlined spin={refreshing} />}
              onClick={handleRefresh}
              loading={refreshing}
              disabled={!selectedDatabase}
            >
              刷新数据
            </Button>
          </Space>
        </div>
        
        {/* 数据库选择器 */}
        <DatabaseSelector
          databases={databases}
          selectedDatabase={selectedDatabase}
          onDatabaseChange={setSelectedDatabase}
          selectedType={selectedDatabaseType}
          onTypeChange={setSelectedDatabaseType}
          loading={loading}
        />
      </div>

      {/* 关键指标卡片 */}
      {dashboardData?.current_stats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6}>
            <PerformanceMetricCard
              title="CPU使用率"
              value={Number(dashboardData.current_stats.cpu_usage).toFixed(2)}
              unit="%"
              status={dashboardData.current_stats.cpu_usage > 80 ? 'critical' : dashboardData.current_stats.cpu_usage > 60 ? 'warning' : 'normal'}
              progressValue={dashboardData.current_stats.cpu_usage}
              progressMax={100}
              dataSource={dashboardData.data_source || 'mock_data'}
              trend={performanceTrend?.cpu_trend || 'stable'}
              trendValue={performanceTrend?.cpu_change || ''}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <PerformanceMetricCard
              title="内存使用量"
              value={Number(dashboardData.current_stats.memory_usage).toFixed(0)}
              unit="MB"
              status={dashboardData.current_stats.memory_usage > 6000 ? 'critical' : dashboardData.current_stats.memory_usage > 4000 ? 'warning' : 'normal'}
              progressValue={Math.min(100, (dashboardData.current_stats.memory_usage / 8192) * 100)}
              progressMax={100}
              dataSource={dashboardData.data_source || 'mock_data'}
              trend={performanceTrend?.memory_trend || 'stable'}
              trendValue={performanceTrend?.memory_change || ''}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <PerformanceMetricCard
              title="活跃连接数"
              value={dashboardData.current_stats.active_connections}
              unit=""
              precision={0}
              status={dashboardData.current_stats.active_connections > 80 ? 'critical' : dashboardData.current_stats.active_connections > 50 ? 'warning' : 'normal'}
              progressValue={Math.min(100, (dashboardData.current_stats.active_connections / 100) * 100)}
              progressMax={100}
              dataSource={dashboardData.data_source || 'mock_data'}
              trend={performanceTrend?.connections_trend || 'stable'}
              trendValue={performanceTrend?.connections_change || ''}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <PerformanceMetricCard
              title="每秒查询数"
              value={Number(dashboardData.current_stats.qps).toFixed(1)}
              unit="QPS"
              status="normal"
              dataSource={dashboardData.data_source || 'mock_data'}
              trend={performanceTrend?.qps_trend || 'stable'}
              trendValue={performanceTrend?.qps_change || ''}
            />
          </Col>
        </Row>
      )}

      {/* 系统健康评分和性能趋势 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          {dashboardData?.system_health_score && (
            <Card>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <h3 style={{ margin: 0 }}>
                    <TrophyOutlined style={{ marginRight: 8 }} />
                    系统健康评分
                  </h3>
                  <p style={{ margin: '8px 0', color: '#666' }}>
                    基于CPU、内存、连接池等关键指标的综合评分
                  </p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{
                    fontSize: '36px',
                    fontWeight: 'bold',
                    color: getHealthStatusColor(dashboardData.system_health_score),
                    marginBottom: '8px'
                  }}>
                    {Number(dashboardData.system_health_score).toFixed(2)}
                  </div>
                  <Tag color={getHealthStatusColor(dashboardData.system_health_score)} style={{ fontSize: '12px' }}>
                    {dashboardData.system_health_score >= 80 ? '优秀' :
                     dashboardData.system_health_score >= 60 ? '良好' : '需要优化'}
                  </Tag>
                </div>
              </div>
              <Progress
                percent={dashboardData.system_health_score}
                strokeColor={getHealthStatusColor(dashboardData.system_health_score)}
                status={dashboardData.system_health_score >= 60 ? 'active' : 'exception'}
                showInfo={false}
              />
            </Card>
          )}
        </Col>

        <Col xs={24} lg={12}>
          {performanceTrend && (
            <Card>
              <h3 style={{ margin: 0 }}>
                <RocketOutlined style={{ marginRight: 8 }} />
                性能趋势分析
              </h3>
              <div style={{ marginTop: 16 }}>
                <Row gutter={[16, 16]}>
                  <Col xs={8}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#1890ff' }}>
                        CPU
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 4 }}>
                        {performanceTrend.cpu.direction === 'increasing' && (
                          <RiseOutlined style={{ color: '#f5222e', marginRight: 4 }} />
                        )}
                        {performanceTrend.cpu.direction === 'decreasing' && (
                          <FallOutlined style={{ color: '#52c41a', marginRight: 4 }} />
                        )}
                        {performanceTrend.cpu.direction === 'stable' && (
                          <MinusOutlined style={{ color: '#faad14', marginRight: 4 }} />
                        )}
                        <span style={{ fontSize: '14px' }}>
                          {performanceTrend.cpu.value > 0 ? '+' : ''}
                          {performanceTrend.cpu.value.toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  </Col>
                  <Col xs={8}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#722ed1' }}>
                        内存
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 4 }}>
                        {performanceTrend.memory.direction === 'increasing' && (
                          <RiseOutlined style={{ color: '#f5222e', marginRight: 4 }} />
                        )}
                        {performanceTrend.memory.direction === 'decreasing' && (
                          <FallOutlined style={{ color: '#52c41a', marginRight: 4 }} />
                        )}
                        {performanceTrend.memory.direction === 'stable' && (
                          <MinusOutlined style={{ color: '#faad14', marginRight: 4 }} />
                        )}
                        <span style={{ fontSize: '14px' }}>
                          {performanceTrend.memory.value > 0 ? '+' : ''}
                          {performanceTrend.memory.value.toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  </Col>
                  <Col xs={8}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fa8c16' }}>
                        QPS
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 4 }}>
                        {performanceTrend.qps.direction === 'increasing' && (
                          <RiseOutlined style={{ color: '#52c41a', marginRight: 4 }} />
                        )}
                        {performanceTrend.qps.direction === 'decreasing' && (
                          <FallOutlined style={{ color: '#f5222e', marginRight: 4 }} />
                        )}
                        {performanceTrend.qps.direction === 'stable' && (
                          <MinusOutlined style={{ color: '#faad14', marginRight: 4 }} />
                        )}
                        <span style={{ fontSize: '14px' }}>
                          {performanceTrend.qps.value > 0 ? '+' : ''}
                          {performanceTrend.qps.value.toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  </Col>
                </Row>
              </div>
            </Card>
          )}
        </Col>
      </Row>

      {/* 图表展示区域 */}
      <Tabs defaultActiveKey="1" style={{ marginBottom: 24 }}>
        <TabPane tab="CPU监控" key="1">
          <Card title="CPU使用率趋势">
            <Line {...cpuChartConfig} />
          </Card>
        </TabPane>
        <TabPane tab="内存监控" key="2">
          <Card title="内存使用量趋势">
            <Line {...memoryChartConfig} />
          </Card>
        </TabPane>
        <TabPane tab="查询性能" key="3">
          <Card title="QPS趋势">
            <Line {...qpsChartConfig} />
          </Card>
        </TabPane>
      </Tabs>

      {/* 告警信息 */}
      {alerts && alerts.length > 0 && (
        <Card
          title={
            <span>
              <AlertOutlined style={{ marginRight: 8 }} />
              活动告警 ({alerts.length})
            </span>
          }
          style={{ marginBottom: 24 }}
        >
          <Table
            columns={alertColumns}
            dataSource={alerts}
            pagination={false}
            size="small"
            rowKey={(record, index) => index}
          />
        </Card>
      )}

      {/* 监控状态 */}
      {monitoringStatus && (
        <Card title="监控状态" style={{ marginBottom: 24 }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="监控状态"
                value={monitoringStatus.monitoring_active ? "运行中" : "已停止"}
                valueStyle={{ color: monitoringStatus.monitoring_active ? '#52c41a' : '#f5222e' }}
                prefix={<CheckCircleOutlined />}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="收集间隔"
                value={`${monitoringStatus.collection_interval_seconds}s`}
                prefix={<ClockCircleOutlined />}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="今日指标"
                value={monitoringStatus.metrics_collected_today}
                prefix={<BarChartOutlined />}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="今日告警"
                value={monitoringStatus.alerts_today}
                valueStyle={{ color: monitoringStatus.alerts_today > 0 ? '#faad14' : '#52c41a' }}
                prefix={<WarningOutlined />}
              />
            </Col>
          </Row>
          {monitoringStatus.last_collection && (
            <div style={{ marginTop: 16, fontSize: '12px', color: '#666' }}>
              最后收集时间: {new Date(monitoringStatus.last_collection).toLocaleString()}
            </div>
          )}
        </Card>
      )}

      {/* 性能建议 */}
      <Card title="性能优化建议">
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Alert
              message="CPU优化建议"
              description={
                dashboardData?.current_stats?.cpu_usage > 80
                  ? "CPU使用率过高，建议优化查询或增加服务器资源"
                  : "CPU使用率正常，继续监控"
              }
              type={dashboardData?.current_stats?.cpu_usage > 80 ? "warning" : "success"}
              showIcon
            />
          </Col>
          <Col xs={24} md={8}>
            <Alert
              message="内存优化建议"
              description={
                dashboardData?.current_stats?.memory_usage > 6000
                  ? "内存使用量较大，建议检查内存泄漏或增加内存"
                  : "内存使用正常"
              }
              type={dashboardData?.current_stats?.memory_usage > 6000 ? "warning" : "success"}
              showIcon
            />
          </Col>
          <Col xs={24} md={8}>
            <Alert
              message="连接池建议"
              description={
                dashboardData?.current_stats?.active_connections > 40
                  ? "活跃连接数较多，建议检查连接池配置"
                  : "连接数正常"
              }
              type={dashboardData?.current_stats?.active_connections > 40 ? "info" : "success"}
              showIcon
            />
          </Col>
        </Row>
      </Card>

      {/* 数据库特性监控 */}
      <DatabaseSpecificMetrics
        database={selectedDatabase}
        dashboardData={dashboardData}
        postgresInsights={postgresInsights}
        tableHealth={tableHealth}
        vacuumStrategy={vacuumStrategy}
        configAnalysis={configAnalysis}
        mysqlInsights={mysqlInsights}
        mysqlConfigAnalysis={mysqlConfigAnalysis}
        mysqlOptimizationSummary={mysqlOptimizationSummary}
      />
    </div>
  );
};

export default PerformanceDashboard;
