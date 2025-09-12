import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Statistic, Progress, Alert, Tabs, Table, Tag,
  Button, Space, Modal, Form, Input, Select as AntSelect, message,
  Descriptions, Tooltip, Badge, Empty, Spin, Collapse, Typography,
  Divider, List, notification
} from 'antd';
import {
  DatabaseOutlined, BarChartOutlined, ThunderboltOutlined,
  ToolOutlined, SettingOutlined, TableOutlined, ClockCircleOutlined,
  CheckCircleOutlined, WarningOutlined, AlertOutlined, SecurityScanOutlined,
  HddOutlined, CloudServerOutlined, PartitionOutlined, SafetyOutlined,
  SyncOutlined, RocketOutlined, FileTextOutlined, DownloadOutlined,
  TrophyOutlined, BugOutlined, FireOutlined
} from '@ant-design/icons';
import { Line, Bar, Pie } from '@ant-design/charts';

import { performanceAPI } from '../services/api';

const { TabPane } = Tabs;
const { Option } = AntSelect;
const { Panel } = Collapse;
const { Title, Text, Paragraph } = Typography;

// PostgreSQL 特性组件
const PostgreSQLMetrics = ({ database, dashboardData, postgresInsights, tableHealth, vacuumStrategy, configAnalysis }) => {
  const [vacuumModalVisible, setVacuumModalVisible] = useState(false);
  const [analyzeModalVisible, setAnalyzeModalVisible] = useState(false);
  const [reindexModalVisible, setReindexModalVisible] = useState(false);

  const getHealthStatusColor = (score) => {
    if (score >= 90) return '#52c41a';
    if (score >= 75) return '#faad14';
    return '#f5222e';
  };

  // 缓冲区命中率图表配置
  const bufferHitRatioChartConfig = {
    data: dashboardData?.time_series_data?.metrics || [],
    xField: 'timestamp',
    yField: 'buffer_hit_ratio',
    smooth: true,
    color: '#1890ff',
    xAxis: {
      title: { text: '时间' },
      label: {
        formatter: (text) => new Date(text).toLocaleTimeString()
      }
    },
    yAxis: {
      title: { text: '缓冲区命中率 (%)' },
      min: 0,
      max: 100
    }
  };

  return (
    <div>
      {/* PostgreSQL 核心指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={8}>
          <Card>
            <Statistic
              title="PostgreSQL性能评分"
              value={postgresInsights?.performance_score || 0}
              suffix="/100"
              valueStyle={{ color: getHealthStatusColor(postgresInsights?.performance_score || 0) }}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card>
            <Statistic
              title="缓冲区命中率"
              value={dashboardData?.current_stats?.buffer_hit_ratio || 0}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{
                color: (dashboardData?.current_stats?.buffer_hit_ratio || 0) >= 90 ? '#52c41a' : '#faad14'
              }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card>
            <Statistic
              title="表膨胀比率"
              value={postgresInsights?.health_status?.table_bloat_ratio || 0}
              suffix="倍"
              prefix={<TableOutlined />}
              valueStyle={{
                color: (postgresInsights?.health_status?.table_bloat_ratio || 0) <= 1.5 ? '#52c41a' : '#f5222e'
              }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="1">
        <TabPane tab="PostgreSQL指标" key="1">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="缓冲区命中率趋势">
                <Line {...bufferHitRatioChartConfig} />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="PostgreSQL特有指标">
                {dashboardData?.current_stats && (
                  <Row gutter={[16, 16]}>
                    <Col xs={12}>
                      <Statistic
                        title="WAL缓冲区写入"
                        value={dashboardData.current_stats.wal_buffers_written || 0}
                        suffix="blocks/sec"
                        valueStyle={{ fontSize: '14px' }}
                      />
                    </Col>
                    <Col xs={12}>
                      <Statistic
                        title="活跃锁数量"
                        value={dashboardData.current_stats.active_locks || 0}
                        valueStyle={{ fontSize: '14px' }}
                      />
                    </Col>
                    <Col xs={12}>
                      <Statistic
                        title="临时文件创建"
                        value={dashboardData.current_stats.temp_files_created || 0}
                        suffix="files/hour"
                        valueStyle={{ fontSize: '14px' }}
                      />
                    </Col>
                    <Col xs={12}>
                      <Statistic
                        title="AutoVacuum工作进程"
                        value={dashboardData.current_stats.autovacuum_workers || 0}
                        valueStyle={{ fontSize: '14px' }}
                      />
                    </Col>
                  </Row>
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="表健康分析" key="2">
          <Card
            title="表健康状况"
            extra={
              <Space>
                <Button
                  type="primary"
                  icon={<ToolOutlined />}
                  onClick={() => setVacuumModalVisible(true)}
                >
                  创建VACUUM任务
                </Button>
                <Button
                  icon={<SettingOutlined />}
                  onClick={() => setAnalyzeModalVisible(true)}
                >
                  创建ANALYZE任务
                </Button>
              </Space>
            }
          >
            {tableHealth?.recommendations ? (
              <Table
                columns={[
                  { title: '表名', dataIndex: 'table', key: 'table' },
                  { title: '优先级', dataIndex: 'priority', key: 'priority', render: (priority) => <Tag color={priority === 'critical' ? 'red' : 'orange'}>{priority}</Tag> },
                  { title: '建议操作', dataIndex: 'action', key: 'action', render: (action) => <Tag color="geekblue">{action}</Tag> },
                  { title: '原因', dataIndex: 'reason', key: 'reason', ellipsis: true }
                ]}
                dataSource={tableHealth.recommendations}
                pagination={false}
                size="small"
                rowKey={(record, index) => index}
              />
            ) : (
              <Empty description="暂无表健康分析数据" />
            )}
          </Card>
        </TabPane>

        <TabPane tab="VACUUM策略" key="3">
          <Card title="VACUUM维护策略">
            {vacuumStrategy ? (
              <Row gutter={[16, 16]}>
                <Col xs={24} md={8}>
                  <Card size="small" title="紧急维护任务">
                    <Badge count={vacuumStrategy.immediate_actions?.length || 0} color="red">
                      <span>需要立即处理的表</span>
                    </Badge>
                    {vacuumStrategy.immediate_actions?.map((action, index) => (
                      <div key={index} style={{ marginTop: 8 }}>
                        <Tag color="red">{action.action}</Tag>
                        <span style={{ marginLeft: 8 }}>{action.table}</span>
                      </div>
                    ))}
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card size="small" title="定期维护任务">
                    <Badge count={vacuumStrategy.scheduled_maintenance?.length || 0} color="orange">
                      <span>定期维护的表</span>
                    </Badge>
                    {vacuumStrategy.scheduled_maintenance?.map((task, index) => (
                      <div key={index} style={{ marginTop: 8 }}>
                        <Tag color="orange">{task.action}</Tag>
                        <span style={{ marginLeft: 8 }}>{task.table}</span>
                      </div>
                    ))}
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card size="small" title="AutoVacuum配置">
                    <div style={{ fontSize: '12px' }}>
                      {vacuumStrategy.autovacuum_tuning && Object.entries(vacuumStrategy.autovacuum_tuning).map(([key, value]) => (
                        <div key={key} style={{ marginBottom: 4 }}>
                          <strong>{key}:</strong> {value}
                        </div>
                      ))}
                    </div>
                  </Card>
                </Col>
              </Row>
            ) : (
              <Empty description="暂无VACUUM策略数据" />
            )}
          </Card>
        </TabPane>

        <TabPane tab="配置优化" key="4">
          <Card title="PostgreSQL配置优化建议">
            {configAnalysis?.recommendations ? (
              <div>
                <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                  <Col xs={24} md={8}>
                    <Statistic
                      title="配置优化评分"
                      value={configAnalysis.optimization_score}
                      suffix="/100"
                      valueStyle={{
                        color: configAnalysis.optimization_score >= 80 ? '#52c41a' : '#faad14'
                      }}
                    />
                  </Col>
                  <Col xs={24} md={8}>
                    <Statistic
                      title="建议数量"
                      value={configAnalysis.recommendations.length}
                      prefix={<SettingOutlined />}
                    />
                  </Col>
                  <Col xs={24} md={8}>
                    <Statistic
                      title="高优先级建议"
                      value={configAnalysis.recommendations.filter(r => r.impact === 'high').length}
                      valueStyle={{ color: '#f5222e' }}
                    />
                  </Col>
                </Row>
                <Table
                  columns={[
                    { title: '参数', dataIndex: 'parameter', key: 'parameter' },
                    { title: '当前值', dataIndex: 'current_value', key: 'current_value' },
                    { title: '建议值', dataIndex: 'recommended_value', key: 'recommended_value', render: (text) => <Tag color="green">{text}</Tag> },
                    { title: '影响程度', dataIndex: 'impact', key: 'impact', render: (impact) => <Tag color={impact === 'high' ? 'red' : 'orange'}>{impact}</Tag> },
                    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true }
                  ]}
                  dataSource={configAnalysis.recommendations}
                  pagination={false}
                  size="small"
                  rowKey="parameter"
                />
              </div>
            ) : (
              <Empty description="暂无配置优化建议" />
            )}
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

// MySQL 特性组件 - 完全重写集成真实功能
const MySQLMetrics = ({ 
  database, 
  dashboardData, 
  mysqlInsights: propMysqlInsights, 
  mysqlConfigAnalysis: propMysqlConfigAnalysis, 
  mysqlOptimizationSummary: propMysqlOptimizationSummary 
}) => {
  const [loading, setLoading] = useState(false);
  const [mysqlInsights, setMysqlInsights] = useState(propMysqlInsights);
  const [configAnalysis, setConfigAnalysis] = useState(propMysqlConfigAnalysis);
  const [optimizationSummary, setOptimizationSummary] = useState(propMysqlOptimizationSummary);
  const [comprehensiveAnalysis, setComprehensiveAnalysis] = useState(null);
  const [tuningScript, setTuningScript] = useState(null);
  const [quickOptimization, setQuickOptimization] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [scriptModalVisible, setScriptModalVisible] = useState(false);
  const [optimizationModalVisible, setOptimizationModalVisible] = useState(false);

  // 当prop数据更新时同步到本地状态
  useEffect(() => {
    setMysqlInsights(propMysqlInsights);
  }, [propMysqlInsights]);

  useEffect(() => {
    setConfigAnalysis(propMysqlConfigAnalysis);
  }, [propMysqlConfigAnalysis]);

  useEffect(() => {
    setOptimizationSummary(propMysqlOptimizationSummary);
  }, [propMysqlOptimizationSummary]);

  // 获取综合分析
  const fetchComprehensiveAnalysis = async (includeAreas) => {
    if (!database?.id) return;
    
    try {
      const analysis = await performanceAPI.comprehensiveMySQLAnalysis(database.id, includeAreas);
      setComprehensiveAnalysis(analysis);
      message.success('综合分析完成');
    } catch (error) {
      console.error('获取综合分析失败:', error);
      message.error('综合分析失败: ' + error.message);
    }
  };

  // 生成调优脚本
  const generateTuningScript = async (optimizationAreas) => {
    if (!database?.id) return;
    
    try {
      const script = await performanceAPI.generateMySQLTuningScript(database.id, optimizationAreas);
      setTuningScript(script);
      setScriptModalVisible(true);
      message.success('调优脚本生成成功');
    } catch (error) {
      console.error('生成调优脚本失败:', error);
      message.error('调优脚本生成失败: ' + error.message);
    }
  };

  // 快速优化
  const performQuickOptimization = async (focusArea) => {
    if (!database?.id) return;
    
    try {
      const optimization = await performanceAPI.quickMySQLOptimization(database.id, focusArea);
      setQuickOptimization(optimization);
      setOptimizationModalVisible(true);
      message.success('快速优化分析完成');
    } catch (error) {
      console.error('快速优化失败:', error);
      message.error('快速优化失败: ' + error.message);
    }
  };

  // 下载调优脚本
  const downloadTuningScript = () => {
    if (!tuningScript?.tuning_script) return;
    
    const element = document.createElement('a');
    const file = new Blob([tuningScript.tuning_script], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `mysql_tuning_script_${database.id}_${Date.now()}.sql`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const getHealthStatusColor = (score) => {
    if (score >= 80) return '#52c41a';
    if (score >= 60) return '#faad14';
    return '#f5222e';
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'blue';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>正在加载MySQL性能数据...</div>
      </div>
    );
  }

  // 如果没有任何MySQL数据，显示加载提示
  if (!mysqlInsights && !configAnalysis && !optimizationSummary) {
    return (
      <div>
        <Alert
          message="MySQL 增强调优模块"
          description="正在加载MySQL性能分析数据，包括配置优化、存储引擎分析、安全检查等8个维度的全面分析。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Card style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16, color: '#666' }}>
            正在获取MySQL性能洞察数据...
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div>
      {/* MySQL 核心指标概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={6}>
          <Card>
            <Statistic
              title="MySQL性能评分"
              value={mysqlInsights?.performance_score || 0}
              suffix="/100"
              valueStyle={{ color: getHealthStatusColor(mysqlInsights?.performance_score || 0) }}
              prefix={<TrophyOutlined />}
            />
            <Progress
              percent={mysqlInsights?.performance_score || 0}
              strokeColor={getHealthStatusColor(mysqlInsights?.performance_score || 0)}
              showInfo={false}
              size="small"
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={6}>
          <Card>
            <Statistic
              title="系统健康状态"
              value={mysqlInsights?.health_status?.status || 'unknown'}
              valueStyle={{ 
                color: mysqlInsights?.health_status?.status === 'excellent' ? '#52c41a' : 
                       mysqlInsights?.health_status?.status === 'good' ? '#1890ff' : '#faad14'
              }}
              prefix={<CheckCircleOutlined />}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>
              {mysqlInsights?.health_status?.description || '状态未知'}
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={6}>
          <Card>
            <Statistic
              title="性能瓶颈"
              value={mysqlInsights?.bottlenecks?.length || 0}
              valueStyle={{ 
                color: (mysqlInsights?.bottlenecks?.length || 0) === 0 ? '#52c41a' : '#f5222d'
              }}
              prefix={<BugOutlined />}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>
              发现的性能问题数量
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={6}>
          <Card>
            <Statistic
              title="优化机会"
              value={mysqlInsights?.optimization_opportunities?.length || 0}
              valueStyle={{ color: '#1890ff' }}
              prefix={<RocketOutlined />}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>
              可优化的配置项
            </div>
          </Card>
        </Col>
      </Row>

      {/* 快速操作按钮 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col>
          <Button
            type="primary"
            icon={<BarChartOutlined />}
            onClick={() => fetchComprehensiveAnalysis()}
            loading={loading}
          >
            综合分析
          </Button>
        </Col>
        <Col>
          <Button
            icon={<FileTextOutlined />}
            onClick={() => generateTuningScript(['config', 'storage', 'security'])}
          >
            生成调优脚本
          </Button>
        </Col>
        <Col>
          <Button
            icon={<ThunderboltOutlined />}
            onClick={() => performQuickOptimization('performance')}
          >
            快速优化
          </Button>
        </Col>
        <Col>
          <Button
            icon={<SecurityScanOutlined />}
            onClick={() => performQuickOptimization('security')}
          >
            安全检查
          </Button>
        </Col>
      </Row>

      {/* 详细分析标签页 */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="概览" key="overview">
          <Row gutter={[16, 16]}>
            {/* 性能瓶颈 */}
            <Col xs={24} lg={12}>
              <Card title={<><BugOutlined style={{ marginRight: 8 }} />性能瓶颈</>}>
                {mysqlInsights?.bottlenecks?.length > 0 ? (
                  <List
                    dataSource={mysqlInsights.bottlenecks}
                    renderItem={(item, index) => (
                      <List.Item key={index}>
                        <List.Item.Meta
                          avatar={<Badge status="error" />}
                          title={
                            <Space>
                              <Tag color={getSeverityColor(item.severity)}>{item.severity}</Tag>
                              {item.type}
                            </Space>
                          }
                          description={item.description}
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <Empty description="未发现明显的性能瓶颈" />
                )}
              </Card>
            </Col>

            {/* 优化机会 */}
            <Col xs={24} lg={12}>
              <Card title={<><RocketOutlined style={{ marginRight: 8 }} />优化机会</>}>
                {mysqlInsights?.optimization_opportunities?.length > 0 ? (
                  <List
                    dataSource={mysqlInsights.optimization_opportunities}
                    renderItem={(item, index) => (
                      <List.Item key={index}>
                        <List.Item.Meta
                          avatar={<Badge status="processing" />}
                          title={item.title}
                          description={
                            <div>
                              <div>{item.description}</div>
                              <div style={{ marginTop: 4 }}>
                                <Tag color="green">预期收益: {item.estimated_benefit}</Tag>
                                <Tag color="blue">实施难度: {item.effort}</Tag>
                              </div>
                            </div>
                          }
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <Empty description="暂无优化建议" />
                )}
              </Card>
            </Col>
          </Row>

          {/* 关键指标 */}
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col xs={24}>
              <Card title={<><BarChartOutlined style={{ marginRight: 8 }} />关键指标</>}>
                <Row gutter={[16, 16]}>
                  <Col xs={12} md={6}>
                    <Statistic
                      title="CPU使用率"
                      value={mysqlInsights?.key_metrics?.cpu_usage || 0}
                      suffix="%"
                      valueStyle={{ fontSize: '16px' }}
                    />
                  </Col>
                  <Col xs={12} md={6}>
                    <Statistic
                      title="内存使用率"
                      value={mysqlInsights?.key_metrics?.memory_usage || 0}
                      suffix="%"
                      valueStyle={{ fontSize: '16px' }}
                    />
                  </Col>
                  <Col xs={12} md={6}>
                    <Statistic
                      title="活跃连接"
                      value={mysqlInsights?.key_metrics?.active_connections || 0}
                      valueStyle={{ fontSize: '16px' }}
                    />
                  </Col>
                  <Col xs={12} md={6}>
                    <Statistic
                      title="QPS"
                      value={mysqlInsights?.key_metrics?.qps || 0}
                      valueStyle={{ fontSize: '16px' }}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="配置分析" key="config">
          <Card title={<><SettingOutlined style={{ marginRight: 8 }} />配置优化分析</>}>
            {configAnalysis ? (
              <div>
                <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                  <Col xs={24} md={8}>
                    <Statistic
                      title="配置优化评分"
                      value={configAnalysis.optimization_score || 0}
                      suffix="/100"
                      valueStyle={{ color: getHealthStatusColor(configAnalysis.optimization_score || 0) }}
                    />
                  </Col>
                  <Col xs={24} md={8}>
                    <Statistic
                      title="优化建议"
                      value={configAnalysis.recommendations?.length || 0}
                      prefix={<ToolOutlined />}
                    />
                  </Col>
                  <Col xs={24} md={8}>
                    <Statistic
                      title="高优先级"
                      value={configAnalysis.recommendations?.filter(r => r.impact === 'high').length || 0}
                      valueStyle={{ color: '#f5222d' }}
                    />
                  </Col>
                </Row>

                {configAnalysis.recommendations?.length > 0 && (
                  <Table
                    columns={[
                      { title: '参数', dataIndex: 'parameter', key: 'parameter' },
                      { title: '当前值', dataIndex: 'current_value', key: 'current_value' },
                      { 
                        title: '建议值', 
                        dataIndex: 'recommended_value', 
                        key: 'recommended_value',
                        render: (text) => <Tag color="green">{text}</Tag>
                      },
                      { 
                        title: '影响程度', 
                        dataIndex: 'impact', 
                        key: 'impact',
                        render: (impact) => <Tag color={getSeverityColor(impact)}>{impact}</Tag>
                      },
                      { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true }
                    ]}
                    dataSource={configAnalysis.recommendations}
                    pagination={{ pageSize: 10 }}
                    size="small"
                    rowKey="parameter"
                  />
                )}
              </div>
            ) : (
              <Empty description="配置分析数据加载中..." />
            )}
          </Card>
        </TabPane>

        <TabPane tab="综合分析" key="comprehensive">
          <Card 
            title={<><DatabaseOutlined style={{ marginRight: 8 }} />综合分析结果</>}
            extra={
              <Button
                type="primary"
                icon={<SyncOutlined />}
                onClick={() => fetchComprehensiveAnalysis()}
                size="small"
              >
                重新分析
              </Button>
            }
          >
            {comprehensiveAnalysis ? (
              <div>
                <Alert
                  message={`分析完成时间: ${new Date(comprehensiveAnalysis.analysis_timestamp).toLocaleString()}`}
                  type="info"
                  style={{ marginBottom: 16 }}
                />

                <Collapse>
                  {Object.entries(comprehensiveAnalysis.analysis_results || {}).map(([key, value]) => (
                    <Panel 
                      header={
                        <Space>
                          <Tag color="blue">{key.toUpperCase()}</Tag>
                          {key === 'config' && <SettingOutlined />}
                          {key === 'storage' && <HddOutlined />}
                          {key === 'hardware' && <CloudServerOutlined />}
                          {key === 'security' && <SecurityScanOutlined />}
                          {key === 'replication' && <SyncOutlined />}
                          {key === 'partition' && <PartitionOutlined />}
                          {key === 'backup' && <SafetyOutlined />}
                          {key === 'config' ? '配置优化' :
                           key === 'storage' ? '存储引擎' :
                           key === 'hardware' ? '硬件优化' :
                           key === 'security' ? '安全配置' :
                           key === 'replication' ? '主从复制' :
                           key === 'partition' ? '分区策略' :
                           key === 'backup' ? '备份策略' : key}
                        </Space>
                      }
                      key={key}
                    >
                      <div style={{ maxHeight: '300px', overflow: 'auto' }}>
                        <pre style={{ fontSize: '12px', background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                          {JSON.stringify(value, null, 2)}
                        </pre>
                      </div>
                    </Panel>
                  ))}
                </Collapse>

                {comprehensiveAnalysis.summary && (
                  <Card title="优化总结" style={{ marginTop: 16 }}>
                    <Row gutter={[16, 16]}>
                      <Col xs={24} md={8}>
                        <Statistic
                          title="整体健康评分"
                          value={comprehensiveAnalysis.summary.overall_health_score || 0}
                          suffix="/100"
                          valueStyle={{ color: getHealthStatusColor(comprehensiveAnalysis.summary.overall_health_score || 0) }}
                        />
                      </Col>
                      <Col xs={24} md={8}>
                        <Statistic
                          title="高影响建议"
                          value={comprehensiveAnalysis.summary.optimization_statistics?.high_impact_recommendations || 0}
                          valueStyle={{ color: '#f5222d' }}
                        />
                      </Col>
                      <Col xs={24} md={8}>
                        <Statistic
                          title="安全问题"
                          value={comprehensiveAnalysis.summary.optimization_statistics?.critical_security_issues || 0}
                          valueStyle={{ color: '#ff4d4f' }}
                        />
                      </Col>
                    </Row>
                  </Card>
                )}
              </div>
            ) : (
              <Empty 
                description="点击上方按钮开始综合分析"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </Card>
        </TabPane>
      </Tabs>

      {/* 调优脚本模态框 */}
      <Modal
        title="MySQL调优脚本"
        visible={scriptModalVisible}
        onCancel={() => setScriptModalVisible(false)}
        width={800}
        footer={[
          <Button key="download" type="primary" icon={<DownloadOutlined />} onClick={downloadTuningScript}>
            下载脚本
          </Button>,
          <Button key="close" onClick={() => setScriptModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {tuningScript && (
          <div>
            <Alert
              message={`生成时间: ${new Date(tuningScript.generated_at).toLocaleString()}`}
              description={tuningScript.description}
              type="info"
              style={{ marginBottom: 16 }}
            />
            <div style={{ maxHeight: '400px', overflow: 'auto' }}>
              <pre style={{ 
                background: '#f5f5f5', 
                padding: '12px', 
                borderRadius: '4px',
                fontSize: '12px',
                lineHeight: '1.4'
              }}>
                {tuningScript.tuning_script}
              </pre>
            </div>
          </div>
        )}
      </Modal>

      {/* 快速优化模态框 */}
      <Modal
        title="快速优化建议"
        visible={optimizationModalVisible}
        onCancel={() => setOptimizationModalVisible(false)}
        width={700}
        footer={[
          <Button key="close" type="primary" onClick={() => setOptimizationModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {quickOptimization && (
          <div>
            <Alert
              message={`优化重点: ${quickOptimization.focus_area}`}
              description={`生成时间: ${new Date(quickOptimization.generated_at).toLocaleString()}`}
              type="info"
              style={{ marginBottom: 16 }}
            />
            
            {quickOptimization.quick_recommendations?.length > 0 && (
              <div>
                <Title level={5}>优化建议</Title>
                <List
                  dataSource={quickOptimization.quick_recommendations}
                  renderItem={(item, index) => (
                    <List.Item key={index}>
                      <List.Item.Meta
                        title={
                          <Space>
                            <Tag color={getSeverityColor(item.impact)}>{item.impact}</Tag>
                            {item.category}
                          </Space>
                        }
                        description={
                          <div>
                            <Paragraph>{item.action}</Paragraph>
                            {item.sql && (
                              <pre style={{ 
                                background: '#f0f0f0', 
                                padding: '8px', 
                                fontSize: '12px',
                                borderRadius: '4px'
                              }}>
                                {item.sql}
                              </pre>
                            )}
                            {item.estimated_improvement && (
                              <Tag color="green">预期改善: {item.estimated_improvement}</Tag>
                            )}
                          </div>
                        }
                      />
                    </List.Item>
                  )}
                />
              </div>
            )}

            {quickOptimization.next_steps?.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Title level={5}>下一步操作</Title>
                <List
                  size="small"
                  dataSource={quickOptimization.next_steps}
                  renderItem={(item, index) => (
                    <List.Item key={index}>
                      <Text>{index + 1}. {item}</Text>
                    </List.Item>
                  )}
                />
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

// Oracle 特性组件
const OracleMetrics = ({ database, dashboardData }) => {
  return (
    <div>
      <Alert
        message="Oracle 特性监控"
        description="Oracle特有的监控指标和功能即将推出，包括SGA/PGA监控、AWR报告分析等。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="SGA命中率"
              value={98.2}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="PGA使用率"
              value={76.5}
              suffix="%"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="等待事件"
              value={3}
              prefix={<AlertOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

// SQL Server 特性组件
const SQLServerMetrics = ({ database, dashboardData }) => {
  return (
    <div>
      <Alert
        message="SQL Server 特性监控"
        description="SQL Server特有的监控指标和功能即将推出，包括缓冲区管理、索引碎片分析等。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="缓冲区命中率"
              value={94.8}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="锁等待时间"
              value={45}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="索引碎片率"
              value={12.3}
              suffix="%"
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

// 主组件
const DatabaseSpecificMetrics = ({ 
  database, 
  dashboardData,
  // PostgreSQL 特有数据
  postgresInsights,
  tableHealth,
  vacuumStrategy,
  configAnalysis,
  // MySQL 特有数据
  mysqlInsights,
  mysqlConfigAnalysis,
  mysqlOptimizationSummary
}) => {
  if (!database) {
    return (
      <Card>
        <Empty 
          description="请先选择一个数据库实例"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  const renderSpecificMetrics = () => {
    switch (database.type) {
      case 'postgresql':
        return (
          <PostgreSQLMetrics
            database={database}
            dashboardData={dashboardData}
            postgresInsights={postgresInsights}
            tableHealth={tableHealth}
            vacuumStrategy={vacuumStrategy}
            configAnalysis={configAnalysis}
          />
        );
      case 'mysql':
        return (
          <MySQLMetrics 
            database={database} 
            dashboardData={dashboardData}
            mysqlInsights={mysqlInsights}
            mysqlConfigAnalysis={mysqlConfigAnalysis}
            mysqlOptimizationSummary={mysqlOptimizationSummary}
          />
        );
      case 'oracle':
        return <OracleMetrics database={database} dashboardData={dashboardData} />;
      case 'sqlserver':
        return <SQLServerMetrics database={database} dashboardData={dashboardData} />;
      default:
        return (
          <Card>
            <Alert
              message={`${database.type ? database.type.toUpperCase() : '未知类型'} 数据库监控`}
              description={`${database.type ? database.type.toUpperCase() : '未知类型'} 数据库的特有监控功能正在开发中，敬请期待。`}
              type="info"
              showIcon
            />
          </Card>
        );
    }
  };

  return (
    <div>
      <Card 
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <DatabaseOutlined />
            <span>{database.type ? database.type.toUpperCase() : '未知类型'} 特性监控</span>
            <Tag color="blue">{database.name}</Tag>
          </div>
        }
        style={{ marginTop: 16 }}
      >
        {renderSpecificMetrics()}
      </Card>
    </div>
  );
};

export default DatabaseSpecificMetrics;
