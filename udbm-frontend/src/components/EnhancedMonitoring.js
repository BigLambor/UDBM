import React, { useState, useEffect, useRef } from 'react';
import {
  Card, Row, Col, Statistic, Table, Tag, Button, Select, DatePicker,
  Space, Badge, Tooltip, Modal, Form, InputNumber, Switch, message,
  Alert, Timeline, Progress, Tabs, List, Avatar, Empty, Divider
} from 'antd';
import {
  WarningOutlined, CheckCircleOutlined, CloseCircleOutlined,
  BellOutlined, SettingOutlined, ReloadOutlined, FilterOutlined,
  LineChartOutlined, BarChartOutlined, DashboardOutlined,
  ThunderboltOutlined, DatabaseOutlined, ClockCircleOutlined,
  FireOutlined, EyeOutlined, NotificationOutlined
} from '@ant-design/icons';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { TabPane } = Tabs;

const EnhancedMonitoring = ({ databases = [] }) => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('alerts');
  const [alerts, setAlerts] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [alertRules, setAlertRules] = useState([]);
  const [selectedDatabase, setSelectedDatabase] = useState('all');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [timeRange, setTimeRange] = useState('24h');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30);
  const [ruleModalVisible, setRuleModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [form] = Form.useForm();
  const intervalRef = useRef();

  useEffect(() => {
    fetchMonitoringData();
    
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchMonitoringData, refreshInterval * 1000);
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [selectedDatabase, selectedSeverity, timeRange, autoRefresh, refreshInterval]);

  const fetchMonitoringData = async () => {
    setLoading(true);
    try {
      const [alertsData, metricsData, rulesData] = await Promise.all([
        fetchAlerts(),
        fetchMetrics(),
        fetchAlertRules()
      ]);
      
      setAlerts(alertsData);
      setMetrics(metricsData);
      setAlertRules(rulesData);
    } catch (error) {
      console.error('获取监控数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    // 模拟告警数据
    return [
      {
        id: 1,
        severity: 'critical',
        title: 'CPU使用率过高',
        message: 'PostgreSQL实例 prod-postgres-01 CPU使用率达到 92%，超过告警阈值 85%',
        database: 'prod-postgres-01',
        databaseType: 'postgresql',
        metric: 'cpu_usage',
        value: 92,
        threshold: 85,
        status: 'active',
        startTime: new Date(Date.now() - 15 * 60 * 1000),
        lastUpdate: new Date(Date.now() - 2 * 60 * 1000),
        duration: '15分钟',
        acknowledged: false,
        assignee: null
      },
      {
        id: 2,
        severity: 'warning',
        title: '连接数接近上限',
        message: 'MySQL实例 prod-mysql-01 当前连接数 180，接近最大连接数 200',
        database: 'prod-mysql-01',
        databaseType: 'mysql',
        metric: 'connection_count',
        value: 180,
        threshold: 160,
        status: 'active',
        startTime: new Date(Date.now() - 45 * 60 * 1000),
        lastUpdate: new Date(Date.now() - 5 * 60 * 1000),
        duration: '45分钟',
        acknowledged: true,
        assignee: '张三'
      },
      {
        id: 3,
        severity: 'info',
        title: '慢查询数量增加',
        message: 'PostgreSQL实例 prod-postgres-02 过去1小时慢查询数量为 23 个',
        database: 'prod-postgres-02',
        databaseType: 'postgresql',
        metric: 'slow_query_count',
        value: 23,
        threshold: 20,
        status: 'resolved',
        startTime: new Date(Date.now() - 2 * 60 * 60 * 1000),
        lastUpdate: new Date(Date.now() - 30 * 60 * 1000),
        duration: '1小时30分钟',
        acknowledged: true,
        assignee: '李四'
      },
      {
        id: 4,
        severity: 'warning',
        title: '磁盘空间不足',
        message: 'MongoDB实例 prod-mongo-01 磁盘使用率达到 78%',
        database: 'prod-mongo-01',
        databaseType: 'mongodb',
        metric: 'disk_usage',
        value: 78,
        threshold: 75,
        status: 'active',
        startTime: new Date(Date.now() - 3 * 60 * 60 * 1000),
        lastUpdate: new Date(Date.now() - 10 * 60 * 1000),
        duration: '3小时',
        acknowledged: false,
        assignee: null
      }
    ];
  };

  const fetchMetrics = async () => {
    // 模拟监控指标数据
    return {
      summary: {
        totalAlerts: 12,
        activeAlerts: 8,
        criticalAlerts: 2,
        warningAlerts: 5,
        infoAlerts: 1,
        resolvedToday: 15,
        avgResolutionTime: '25分钟',
        acknowledgedRate: 62.5
      },
      trends: {
        alertsByHour: [2, 1, 3, 5, 2, 4, 6, 3, 2, 1, 4, 7, 5, 3, 2, 4, 6, 8, 5, 3, 2, 1, 2, 3],
        alertsBySeverity: {
          critical: [1, 2, 1, 3, 2, 1, 2],
          warning: [3, 4, 2, 5, 3, 4, 5],
          info: [2, 1, 3, 2, 1, 2, 1]
        }
      },
      topDatabases: [
        { name: 'prod-postgres-01', alerts: 5, severity: 'critical' },
        { name: 'prod-mysql-01', alerts: 3, severity: 'warning' },
        { name: 'prod-mongo-01', alerts: 2, severity: 'warning' },
        { name: 'test-postgres-01', alerts: 2, severity: 'info' }
      ]
    };
  };

  const fetchAlertRules = async () => {
    // 模拟告警规则数据
    return [
      {
        id: 1,
        name: 'CPU使用率告警',
        description: '当CPU使用率超过阈值时触发告警',
        metric: 'cpu_usage',
        operator: '>',
        threshold: 85,
        severity: 'critical',
        enabled: true,
        databases: ['all'],
        notificationChannels: ['email', 'webhook'],
        cooldown: 300, // 5分钟
        created: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
      },
      {
        id: 2,
        name: '内存使用率告警',
        description: '当内存使用率超过阈值时触发告警',
        metric: 'memory_usage',
        operator: '>',
        threshold: 80,
        severity: 'warning',
        enabled: true,
        databases: ['prod-postgres-01', 'prod-mysql-01'],
        notificationChannels: ['email'],
        cooldown: 600, // 10分钟
        created: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000)
      },
      {
        id: 3,
        name: '连接数告警',
        description: '当活跃连接数超过阈值时触发告警',
        metric: 'connection_count',
        operator: '>',
        threshold: 160,
        severity: 'warning',
        enabled: true,
        databases: ['all'],
        notificationChannels: ['email', 'sms'],
        cooldown: 300,
        created: new Date(Date.now() - 21 * 24 * 60 * 60 * 1000)
      }
    ];
  };

  // 获取告警级别配置
  const getSeverityConfig = (severity) => {
    const configs = {
      critical: { color: '#f5222d', icon: CloseCircleOutlined, text: '严重' },
      warning: { color: '#faad14', icon: WarningOutlined, text: '警告' },
      info: { color: '#1890ff', icon: CheckCircleOutlined, text: '信息' }
    };
    return configs[severity] || configs.info;
  };

  // 确认告警
  const acknowledgeAlert = async (alert) => {
    try {
      // 这里应该调用API确认告警
      message.success('告警已确认');
      fetchMonitoringData();
    } catch (error) {
      message.error('确认告警失败');
    }
  };

  // 解决告警
  const resolveAlert = async (alert) => {
    Modal.confirm({
      title: '确认解决告警',
      content: `确定要将告警 "${alert.title}" 标记为已解决吗？`,
      onOk: async () => {
        try {
          // 这里应该调用API解决告警
          message.success('告警已解决');
          fetchMonitoringData();
        } catch (error) {
          message.error('解决告警失败');
        }
      }
    });
  };

  // 过滤告警数据
  const filteredAlerts = alerts.filter(alert => {
    const matchesDatabase = selectedDatabase === 'all' || alert.database === selectedDatabase;
    const matchesSeverity = selectedSeverity === 'all' || alert.severity === selectedSeverity;
    return matchesDatabase && matchesSeverity;
  });

  // 告警列表表格列定义
  const alertColumns = [
    {
      title: '级别',
      dataIndex: 'severity',
      key: 'severity',
      width: 80,
      render: (severity) => {
        const config = getSeverityConfig(severity);
        const IconComponent = config.icon;
        return (
          <Tag color={config.color}>
            <IconComponent style={{ marginRight: 4 }} />
            {config.text}
          </Tag>
        );
      }
    },
    {
      title: '告警信息',
      key: 'info',
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 500, marginBottom: 4 }}>
            {record.title}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.message}
          </div>
          <div style={{ marginTop: 4 }}>
            <Tag size="small">{record.database}</Tag>
            <Tag size="small" color="blue">{record.databaseType}</Tag>
          </div>
        </div>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status, record) => (
        <div>
          <Badge 
            status={status === 'active' ? 'error' : 'success'} 
            text={status === 'active' ? '活跃' : '已解决'} 
          />
          {record.acknowledged && (
            <div style={{ fontSize: '11px', color: '#52c41a', marginTop: 2 }}>
              ✓ 已确认
            </div>
          )}
        </div>
      )
    },
    {
      title: '持续时间',
      dataIndex: 'duration',
      key: 'duration',
      width: 100
    },
    {
      title: '负责人',
      dataIndex: 'assignee',
      key: 'assignee',
      width: 80,
      render: (assignee) => assignee || '-'
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          {!record.acknowledged && record.status === 'active' && (
            <Tooltip title="确认告警">
              <Button
                type="text"
                size="small"
                icon={<CheckCircleOutlined />}
                onClick={() => acknowledgeAlert(record)}
              />
            </Tooltip>
          )}
          {record.status === 'active' && (
            <Tooltip title="解决告警">
              <Button
                type="text"
                size="small"
                icon={<CloseCircleOutlined />}
                onClick={() => resolveAlert(record)}
              />
            </Tooltip>
          )}
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // 告警规则表格列定义
  const ruleColumns = [
    {
      title: '规则名称',
      dataIndex: 'name',
      key: 'name',
      render: (name, record) => (
        <div>
          <div style={{ fontWeight: 500 }}>{name}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.description}
          </div>
        </div>
      )
    },
    {
      title: '监控指标',
      dataIndex: 'metric',
      key: 'metric',
      render: (metric, record) => (
        <Tag>{metric} {record.operator} {record.threshold}</Tag>
      )
    },
    {
      title: '级别',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity) => {
        const config = getSeverityConfig(severity);
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled) => (
        <Badge status={enabled ? 'success' : 'default'} text={enabled ? '启用' : '禁用'} />
      )
    },
    {
      title: '通知方式',
      dataIndex: 'notificationChannels',
      key: 'notificationChannels',
      render: (channels) => (
        <Space>
          {channels.map(channel => (
            <Tag size="small" key={channel}>
              {channel === 'email' ? '邮件' : channel === 'sms' ? '短信' : channel}
            </Tag>
          ))}
        </Space>
      )
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="text" size="small" icon={<EditOutlined />}>
            编辑
          </Button>
          <Switch
            size="small"
            checked={record.enabled}
            onChange={(checked) => {
              // 切换规则启用状态
              message.success(checked ? '规则已启用' : '规则已禁用');
            }}
          />
        </Space>
      )
    }
  ];

  return (
    <div>
      {/* 顶部控制栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col flex="auto">
            <Space wrap>
              <Select
                value={selectedDatabase}
                onChange={setSelectedDatabase}
                style={{ width: 200 }}
                placeholder="选择数据库"
              >
                <Option value="all">全部数据库</Option>
                {databases.map(db => (
                  <Option key={db.id} value={db.name}>
                    {db.name}
                  </Option>
                ))}
              </Select>
              
              <Select
                value={selectedSeverity}
                onChange={setSelectedSeverity}
                style={{ width: 120 }}
                placeholder="告警级别"
              >
                <Option value="all">全部级别</Option>
                <Option value="critical">严重</Option>
                <Option value="warning">警告</Option>
                <Option value="info">信息</Option>
              </Select>
              
              <Select
                value={timeRange}
                onChange={setTimeRange}
                style={{ width: 120 }}
              >
                <Option value="1h">1小时</Option>
                <Option value="24h">24小时</Option>
                <Option value="7d">7天</Option>
                <Option value="30d">30天</Option>
              </Select>
            </Space>
          </Col>
          
          <Col>
            <Space>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <span style={{ marginRight: 8, fontSize: '14px' }}>自动刷新</span>
                <Switch
                  checked={autoRefresh}
                  onChange={setAutoRefresh}
                  size="small"
                />
              </div>
              
              <Button
                icon={<ReloadOutlined spin={loading} />}
                onClick={fetchMonitoringData}
                disabled={loading}
              >
                刷新
              </Button>
              
              <Button
                type="primary"
                icon={<SettingOutlined />}
                onClick={() => setRuleModalVisible(true)}
              >
                告警规则
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 监控统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃告警"
              value={metrics.summary?.activeAlerts || 0}
              prefix={<FireOutlined style={{ color: '#f5222d' }} />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="严重告警"
              value={metrics.summary?.criticalAlerts || 0}
              prefix={<WarningOutlined style={{ color: '#f5222d' }} />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日已解决"
              value={metrics.summary?.resolvedToday || 0}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均解决时间"
              value={metrics.summary?.avgResolutionTime || '0分钟'}
              prefix={<ClockCircleOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要内容区域 */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane
          tab={
            <span>
              <BellOutlined />
              活跃告警 ({filteredAlerts.filter(a => a.status === 'active').length})
            </span>
          }
          key="alerts"
        >
          <Card>
            <Table
              columns={alertColumns}
              dataSource={filteredAlerts}
              rowKey="id"
              loading={loading}
              pagination={{
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
              }}
              expandable={{
                expandedRowRender: (record) => (
                  <div style={{ padding: '12px 0' }}>
                    <Row gutter={16}>
                      <Col span={12}>
                        <div><strong>开始时间：</strong>{record.startTime.toLocaleString()}</div>
                        <div><strong>最后更新：</strong>{record.lastUpdate.toLocaleString()}</div>
                        <div><strong>监控指标：</strong>{record.metric}</div>
                      </Col>
                      <Col span={12}>
                        <div><strong>当前值：</strong>{record.value}</div>
                        <div><strong>告警阈值：</strong>{record.threshold}</div>
                        <div><strong>负责人：</strong>{record.assignee || '未分配'}</div>
                      </Col>
                    </Row>
                  </div>
                )
              }}
            />
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <SettingOutlined />
              告警规则 ({alertRules.length})
            </span>
          }
          key="rules"
        >
          <Card
            extra={
              <Button type="primary" icon={<PlusOutlined />}>
                新建规则
              </Button>
            }
          >
            <Table
              columns={ruleColumns}
              dataSource={alertRules}
              rowKey="id"
              loading={loading}
              pagination={false}
            />
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <BarChartOutlined />
              统计分析
            </span>
          }
          key="analytics"
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="告警趋势" extra={<LineChartOutlined />}>
                <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Empty description="图表组件待集成" />
                </div>
              </Card>
            </Col>
            
            <Col xs={24} lg={12}>
              <Card title="告警最多的数据库" extra={<DatabaseOutlined />}>
                <List
                  dataSource={metrics.topDatabases || []}
                  renderItem={(item) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={
                          <Avatar icon={<DatabaseOutlined />} style={{ backgroundColor: '#1890ff' }} />
                        }
                        title={item.name}
                        description={`${item.alerts} 个告警`}
                      />
                      <Tag color={getSeverityConfig(item.severity).color}>
                        {getSeverityConfig(item.severity).text}
                      </Tag>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* 告警规则配置模态框 */}
      <Modal
        title="告警规则配置"
        open={ruleModalVisible}
        onCancel={() => setRuleModalVisible(false)}
        width={800}
        footer={null}
      >
        <Alert
          message="告警规则配置"
          description="在这里可以配置各种监控指标的告警规则，包括阈值设置、通知方式等。"
          type="info"
          style={{ marginBottom: 16 }}
        />
        {/* 这里可以放置告警规则配置的详细表单 */}
      </Modal>
    </div>
  );
};

export default EnhancedMonitoring;