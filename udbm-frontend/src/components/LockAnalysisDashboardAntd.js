import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Statistic, Progress, Alert, Spin, Select,
  Button, Tabs, Table, Tag, Space, Tooltip, message, Badge,
  Divider, Typography, Empty, Timeline, List
} from 'antd';
import {
  LockOutlined, WarningOutlined, CheckCircleOutlined,
  ClockCircleOutlined, FireOutlined, ThunderboltOutlined,
  AlertOutlined, ReloadOutlined, DownloadOutlined,
  SettingOutlined, LineChartOutlined, BarChartOutlined,
  DashboardOutlined
} from '@ant-design/icons';
import { Line, Column, Pie, Area } from '@ant-design/charts';
import { performanceAPI } from '../services/api';

const { TabPane } = Tabs;
const { Title, Text, Paragraph } = Typography;

const LockAnalysisDashboardAntd = ({ databaseId }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('1');
  const [selectedOptimization, setSelectedOptimization] = useState(null);
  const [databaseInfo, setDatabaseInfo] = useState(null);
  const [noDataReason, setNoDataReason] = useState(null);

  useEffect(() => {
    if (databaseId) {
      fetchDatabaseInfo();
      fetchDashboardData();
      const interval = setInterval(fetchDashboardData, 30000); // 30秒刷新一次
      return () => clearInterval(interval);
    }
  }, [databaseId]);

  const fetchDatabaseInfo = async () => {
    try {
      const response = await performanceAPI.getDatabaseById(databaseId);
      setDatabaseInfo(response);
    } catch (err) {
      console.error('获取数据库信息失败:', err);
    }
  };

  const fetchDashboardData = async () => {
    if (!databaseId) return;
    
    try {
      setLoading(true);
      setError(null);
      setNoDataReason(null);
      
      const response = await performanceAPI.getLockDashboard(databaseId);
      
      if (response && Object.keys(response).length > 0) {
        setDashboardData(response);
      } else {
        setDashboardData(null);
        setNoDataReason('no_data');
      }
    } catch (err) {
      console.error('获取锁分析数据失败:', err);
      
      // 根据错误类型设置不同的提示
      if (err.response?.status === 404) {
        setNoDataReason('not_supported');
        setError('当前数据库类型暂不支持锁分析功能');
      } else if (err.response?.status === 503) {
        setNoDataReason('unavailable');
        setError('数据库连接不可用，请检查数据库状态');
      } else if (err.response?.data?.detail?.includes('permission')) {
        setNoDataReason('permission');
        setError('没有权限访问锁分析数据，请联系管理员');
      } else {
        setNoDataReason('error');
        setError('获取锁分析数据失败: ' + (err.response?.data?.detail || err.message));
      }
      
      setDashboardData(null);
    } finally {
      setLoading(false);
    }
  };

  const getHealthScoreColor = (score) => {
    if (score >= 90) return '#52c41a';
    if (score >= 70) return '#faad14';
    if (score >= 50) return '#fa8c16';
    return '#f5222d';
  };

  const getSeverityColor = (severity) => {
    const colors = {
      low: '#52c41a',
      medium: '#faad14',
      high: '#fa8c16',
      critical: '#f5222d'
    };
    return colors[severity] || '#8c8c8c';
  };

  const getSeverityTag = (severity) => {
    const severityMap = {
      low: { color: 'success', text: '低' },
      medium: { color: 'warning', text: '中' },
      high: { color: 'orange', text: '高' },
      critical: { color: 'error', text: '严重' }
    };
    const config = severityMap[severity] || { color: 'default', text: '未知' };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 根据数据库类型返回不同的提示信息
  const getNoDataMessage = () => {
    if (!databaseInfo) {
      return {
        title: '暂无锁分析数据',
        description: '请确保已选择数据库并且数据库连接正常',
        showAction: true
      };
    }

    const dbType = databaseInfo.type?.toLowerCase();
    
    switch (noDataReason) {
      case 'not_supported':
        return {
          title: `${dbType?.toUpperCase() || '该'} 数据库暂不支持锁分析`,
          description: `锁分析功能目前支持 PostgreSQL、MySQL 和 OceanBase 数据库`,
          showAction: false
        };
      case 'unavailable':
        return {
          title: '数据库连接不可用',
          description: '请检查数据库连接状态，确保数据库正在运行',
          showAction: true
        };
      case 'permission':
        return {
          title: '权限不足',
          description: '您没有访问锁分析数据的权限，请联系管理员',
          showAction: false
        };
      case 'no_data':
        return {
          title: '当前没有锁数据',
          description: '数据库当前没有活跃的锁或等待事件，这通常是正常情况',
          showAction: true
        };
      case 'error':
      default:
        return {
          title: '加载失败',
          description: error || '获取锁分析数据时发生错误',
          showAction: true
        };
    }
  };

  if (loading && !dashboardData) {
    return (
      <div style={{ textAlign: 'center', padding: '50px 0' }}>
        <Spin size="large" tip="正在加载锁分析数据..." />
      </div>
    );
  }

  if (error || !dashboardData) {
    const messageInfo = getNoDataMessage();
    return (
      <Card>
        <Empty
          description={
            <div>
              <Title level={5}>{messageInfo.title}</Title>
              <Paragraph type="secondary">{messageInfo.description}</Paragraph>
            </div>
          }
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          {messageInfo.showAction && (
            <Button type="primary" onClick={fetchDashboardData}>
              重新加载
            </Button>
          )}
        </Empty>
      </Card>
    );
  }

  const {
    database_type,
    overall_health_score = 0,
    lock_efficiency_score = 0,
    contention_severity = 'low',
    current_locks = 0,
    waiting_locks = 0,
    deadlock_count_today = 0,
    timeout_count_today = 0,
    hot_objects = [],
    active_wait_chains = [],
    top_contentions = [],
    optimization_suggestions = [],
    lock_trends = {},
    // 数据库特定指标
    pg_specific_metrics,
    mysql_specific_metrics,
    oceanbase_specific_metrics
  } = dashboardData;

  // 准备趋势图数据
  const trendData = lock_trends?.wait_time?.map((point, index) => ({
    time: new Date(point.timestamp).toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    }),
    等待时间: point.value,
    竞争次数: lock_trends.contention_count?.[index]?.value || 0
  })) || [];

  // 锁类型分布数据
  const lockTypeData = [
    { type: '表锁', value: Math.max(current_locks - waiting_locks, 0), percent: 0.5 },
    { type: '行锁', value: waiting_locks, percent: 0.3 },
    { type: '页锁', value: Math.floor(current_locks * 0.2), percent: 0.2 }
  ];

  // 趋势图配置
  const trendConfig = {
    data: trendData,
    xField: 'time',
    yField: '等待时间',
    smooth: true,
    color: '#1890ff',
    point: {
      size: 3,
      shape: 'circle',
    },
    tooltip: {
      showCrosshairs: true,
    },
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
  };

  // 饼图配置
  const pieConfig = {
    data: lockTypeData,
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    label: {
      type: 'outer',
      content: '{name} {percentage}',
    },
    interactions: [
      {
        type: 'pie-legend-active',
      },
      {
        type: 'element-active',
      },
    ],
  };

  // 热点对象表格列定义
  const hotObjectColumns = [
    {
      title: '对象名称',
      dataIndex: 'object_name',
      key: 'object_name',
      ellipsis: true,
    },
    {
      title: '竞争次数',
      dataIndex: 'contention_count',
      key: 'contention_count',
      sorter: (a, b) => a.contention_count - b.contention_count,
    },
    {
      title: '总等待时间(s)',
      dataIndex: 'total_wait_time',
      key: 'total_wait_time',
      render: (val) => val?.toFixed(2) || '0.00',
      sorter: (a, b) => a.total_wait_time - b.total_wait_time,
    },
    {
      title: '平均等待时间(s)',
      dataIndex: 'avg_wait_time',
      key: 'avg_wait_time',
      render: (val) => val?.toFixed(2) || '0.00',
    },
    {
      title: '优先级',
      dataIndex: 'priority_level',
      key: 'priority_level',
      render: (priority) => getSeverityTag(priority || 'medium'),
    },
  ];

  // 等待链表格列定义
  const waitChainColumns = [
    {
      title: '链ID',
      dataIndex: 'chain_id',
      key: 'chain_id',
      width: 100,
    },
    {
      title: '链长度',
      dataIndex: 'chain_length',
      key: 'chain_length',
      width: 80,
    },
    {
      title: '总等待时间(s)',
      dataIndex: 'total_wait_time',
      key: 'total_wait_time',
      render: (val) => val?.toFixed(2) || '0.00',
    },
    {
      title: '严重程度',
      dataIndex: 'severity_level',
      key: 'severity_level',
      render: (severity) => getSeverityTag(severity),
    },
    {
      title: '头会话',
      dataIndex: 'head_session_id',
      key: 'head_session_id',
    },
    {
      title: '尾会话',
      dataIndex: 'tail_session_id',
      key: 'tail_session_id',
    },
  ];

  return (
    <div>
      {/* 头部操作栏 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Space>
            <Badge status="processing" text="实时监控中" />
            <Divider type="vertical" />
            <Text type="secondary">
              最后更新: {new Date().toLocaleTimeString('zh-CN')}
            </Text>
          </Space>
        </Col>
        <Col>
          <Space>
            <Tooltip title="刷新数据">
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchDashboardData}
                loading={loading}
              />
            </Tooltip>
            <Tooltip title="生成报告">
              <Button icon={<DownloadOutlined />} />
            </Tooltip>
            <Tooltip title="监控设置">
              <Button icon={<SettingOutlined />} />
            </Tooltip>
          </Space>
        </Col>
      </Row>

      {/* 关键指标卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="整体健康评分"
              value={overall_health_score}
              precision={1}
              valueStyle={{ color: getHealthScoreColor(overall_health_score) }}
              prefix={<DashboardOutlined />}
              suffix="分"
            />
            <Progress
              percent={overall_health_score}
              strokeColor={getHealthScoreColor(overall_health_score)}
              showInfo={false}
              size="small"
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="当前锁数量"
              value={current_locks}
              valueStyle={{ color: '#1890ff' }}
              prefix={<LockOutlined />}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">等待中: </Text>
              <Text strong>{waiting_locks}</Text>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日死锁"
              value={deadlock_count_today}
              valueStyle={{ color: deadlock_count_today > 0 ? '#f5222d' : '#52c41a' }}
              prefix={deadlock_count_today > 0 ? <AlertOutlined /> : <CheckCircleOutlined />}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">超时: </Text>
              <Text strong>{timeout_count_today}</Text>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <Text type="secondary">竞争严重程度</Text>
                <div style={{ marginTop: 8 }}>
                  {getSeverityTag(contention_severity)}
                </div>
              </div>
              <WarningOutlined
                style={{
                  fontSize: 32,
                  color: getSeverityColor(contention_severity)
                }}
              />
            </div>
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">锁效率: </Text>
              <Text strong>{lock_efficiency_score.toFixed(1)}%</Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 标签页内容 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane
            tab={
              <span>
                <LineChartOutlined />
                趋势分析
              </span>
            }
            key="1"
          >
            <Row gutter={[16, 16]}>
              <Col span={16}>
                <Card title="锁等待时间趋势" size="small">
                  <Line {...trendConfig} height={300} />
                </Card>
              </Col>
              <Col span={8}>
                <Card title="锁类型分布" size="small">
                  <Pie {...pieConfig} height={300} />
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane
            tab={
              <span>
                <FireOutlined />
                竞争分析
              </span>
            }
            key="2"
          >
            <Card title="热点对象竞争分析" size="small">
              <Table
                columns={hotObjectColumns}
                dataSource={hot_objects}
                rowKey="object_name"
                size="small"
                pagination={{ pageSize: 10 }}
                locale={{
                  emptyText: <Empty description="暂无热点对象" />
                }}
              />
            </Card>
          </TabPane>

          <TabPane
            tab={
              <span>
                <ClockCircleOutlined />
                等待链
              </span>
            }
            key="3"
          >
            <Card title="活跃等待链" size="small">
              {active_wait_chains?.length > 0 ? (
                <Table
                  columns={waitChainColumns}
                  dataSource={active_wait_chains}
                  rowKey="chain_id"
                  size="small"
                  pagination={{ pageSize: 10 }}
                />
              ) : (
                <Empty description="当前无活跃等待链" />
              )}
            </Card>
          </TabPane>

          <TabPane
            tab={
              <span>
                <SettingOutlined />
                优化建议
              </span>
            }
            key="4"
          >
            <List
              dataSource={optimization_suggestions}
              renderItem={(item) => (
                <Card style={{ marginBottom: 16 }}>
                  <Row justify="space-between">
                    <Col span={20}>
                      <Title level={5}>{item.title}</Title>
                      <Paragraph type="secondary">{item.description}</Paragraph>
                      {item.actions && item.actions.length > 0 && (
                        <div>
                          <Text strong>建议操作:</Text>
                          <ul style={{ marginTop: 8 }}>
                            {item.actions.map((action, index) => (
                              <li key={index}>
                                <Text>{action}</Text>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </Col>
                    <Col span={4} style={{ textAlign: 'right' }}>
                      {getSeverityTag(item.priority)}
                      <Button
                        type="link"
                        size="small"
                        style={{ marginTop: 8, display: 'block' }}
                        onClick={() => {
                          setSelectedOptimization(item);
                          message.info('优化建议详情功能开发中');
                        }}
                      >
                        查看详情
                      </Button>
                    </Col>
                  </Row>
                </Card>
              )}
              locale={{
                emptyText: <Empty description="暂无优化建议" />
              }}
            />
          </TabPane>

          {/* 数据库特定指标标签页 */}
          {(database_type === 'postgresql' || database_type === 'mysql' || database_type === 'oceanbase') && (
            <TabPane
              tab={
                <span>
                  <BarChartOutlined />
                  {database_type?.toUpperCase()} 特定指标
                </span>
              }
              key="5"
            >
              <Card>
                {database_type === 'postgresql' && pg_specific_metrics && (
                  <div>
                    <Title level={5}>PostgreSQL 锁指标</Title>
                    <Row gutter={[16, 16]}>
                      <Col span={6}>
                        <Statistic
                          title="Advisory Locks"
                          value={pg_specific_metrics.advisory_locks || 0}
                          prefix={<LockOutlined />}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="Relation Locks"
                          value={pg_specific_metrics.relation_locks || 0}
                          prefix={<LockOutlined />}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="Transaction Locks"
                          value={pg_specific_metrics.transaction_locks || 0}
                          prefix={<LockOutlined />}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="Autovacuum Workers"
                          value={pg_specific_metrics.autovacuum_workers || 0}
                          valueStyle={{ color: pg_specific_metrics.vacuum_running ? '#52c41a' : '#8c8c8c' }}
                        />
                      </Col>
                    </Row>
                  </div>
                )}

                {database_type === 'mysql' && mysql_specific_metrics && (
                  <div>
                    <Title level={5}>MySQL InnoDB 锁指标</Title>
                    <Row gutter={[16, 16]}>
                      <Col span={6}>
                        <Statistic
                          title="InnoDB Row Locks"
                          value={mysql_specific_metrics.innodb_row_locks || 0}
                          prefix={<LockOutlined />}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="Table Locks"
                          value={mysql_specific_metrics.innodb_table_locks || 0}
                          prefix={<LockOutlined />}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="Gap Locks"
                          value={mysql_specific_metrics.gap_locks || 0}
                          prefix={<AlertOutlined />}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="Next-Key Locks"
                          value={mysql_specific_metrics.next_key_locks || 0}
                          prefix={<LockOutlined />}
                        />
                      </Col>
                    </Row>
                    <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                      <Col span={6}>
                        <Statistic
                          title="Metadata Locks"
                          value={mysql_specific_metrics.metadata_locks || 0}
                          prefix={<LockOutlined />}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="Auto-Inc Locks"
                          value={mysql_specific_metrics.auto_inc_locks || 0}
                          prefix={<ThunderboltOutlined />}
                        />
                      </Col>
                    </Row>
                  </div>
                )}

                {database_type === 'oceanbase' && oceanbase_specific_metrics && (
                  <div>
                    <Title level={5}>OceanBase 锁指标</Title>
                    <Row gutter={[16, 16]}>
                      <Col span={6}>
                        <Statistic
                          title="分布式锁"
                          value={oceanbase_specific_metrics.distributed_locks || 0}
                          prefix={<LockOutlined />}
                          valueStyle={{ color: '#1890ff' }}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="本地锁"
                          value={oceanbase_specific_metrics.local_locks || 0}
                          prefix={<LockOutlined />}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="分区锁"
                          value={oceanbase_specific_metrics.partition_locks || 0}
                          prefix={<LockOutlined />}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="全局索引锁"
                          value={oceanbase_specific_metrics.global_index_locks || 0}
                          prefix={<LockOutlined />}
                        />
                      </Col>
                    </Row>
                    {oceanbase_specific_metrics.tenant_locks && (
                      <div style={{ marginTop: 16 }}>
                        <Title level={5}>租户级锁统计</Title>
                        <Row gutter={[16, 16]}>
                          {Object.entries(oceanbase_specific_metrics.tenant_locks).map(([tenant, count]) => (
                            <Col span={8} key={tenant}>
                              <Card size="small">
                                <Statistic
                                  title={`租户: ${tenant}`}
                                  value={count}
                                  prefix={<LockOutlined />}
                                />
                              </Card>
                            </Col>
                          ))}
                        </Row>
                      </div>
                    )}
                  </div>
                )}
              </Card>
            </TabPane>
          )}
        </Tabs>
      </Card>
    </div>
  );
};

export default LockAnalysisDashboardAntd;