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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('1');
  const [selectedOptimization, setSelectedOptimization] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // 30秒刷新一次
    return () => clearInterval(interval);
  }, [databaseId]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await performanceAPI.getLockDashboard(databaseId);
      setDashboardData(response);
      setError(null);
    } catch (err) {
      setError('获取锁分析数据失败: ' + (err.response?.data?.detail || err.message));
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

  if (loading && !dashboardData) {
    return (
      <div style={{ textAlign: 'center', padding: '50px 0' }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="加载失败"
        description={error}
        type="error"
        showIcon
        action={
          <Button size="small" onClick={fetchDashboardData}>
            重试
          </Button>
        }
      />
    );
  }

  if (!dashboardData) {
    return (
      <Empty
        description="暂无锁分析数据"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
  }

  const {
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
    lock_trends = {}
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
        </Tabs>
      </Card>
    </div>
  );
};

export default LockAnalysisDashboardAntd;