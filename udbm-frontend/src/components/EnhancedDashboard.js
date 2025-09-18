import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  Card, Row, Col, Statistic, Progress, Alert, Button, Space, 
  List, Avatar, Badge, Divider, Timeline, Empty, Spin, Tabs,
  Select, Input, Tag, Tooltip, Grid
} from 'antd';
import {
  DatabaseOutlined, ThunderboltOutlined, BarChartOutlined,
  CheckCircleOutlined, WarningOutlined, ClockCircleOutlined,
  RightOutlined, PlusOutlined, EyeOutlined, SettingOutlined,
  TrophyOutlined, RocketOutlined, FireOutlined, BulbOutlined,
  SearchOutlined, FilterOutlined, GlobalOutlined, TeamOutlined
} from '@ant-design/icons';

import { databaseAPI, performanceAPI } from '../services/api';

const { TabPane } = Tabs;
const { Option } = Select;
const { Search } = Input;

// 数据库类型配置
const DATABASE_TYPES = {
  postgresql: {
    icon: '🐘',
    color: '#336791',
    name: 'PostgreSQL',
    description: '开源关系型数据库'
  },
  mysql: {
    icon: '🐬',
    color: '#4479A1',
    name: 'MySQL',
    description: '流行的关系型数据库'
  },
  mongodb: {
    icon: '🍃',
    color: '#47A248',
    name: 'MongoDB',
    description: '文档型NoSQL数据库'
  },
  redis: {
    icon: '⚡',
    color: '#DC382D',
    name: 'Redis',
    description: '内存键值存储'
  },
  oracle: {
    icon: '🔶',
    color: '#F80000',
    name: 'Oracle',
    description: '企业级数据库'
  },
  sqlserver: {
    icon: '🏢',
    color: '#CC2927',
    name: 'SQL Server',
    description: '微软数据库'
  }
};

const EnhancedDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [selectedEnvironment, setSelectedEnvironment] = useState('all');
  
  const [dashboardData, setDashboardData] = useState({
    databases: [],
    systemStats: null,
    recentAlerts: [],
    performanceSummary: null,
    quickActions: [],
    typeStats: {},
    environmentStats: {}
  });

  // 响应式检测
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [databases, systemStats, alerts] = await Promise.all([
        databaseAPI.getDatabases().catch(() => []),
        fetchSystemStats().catch(() => null),
        fetchRecentAlerts().catch(() => [])
      ]);

      const typeStats = generateTypeStats(databases);
      const environmentStats = generateEnvironmentStats(databases);

      setDashboardData({
        databases: Array.isArray(databases) ? databases : [],
        systemStats,
        recentAlerts: Array.isArray(alerts) ? alerts : [],
        performanceSummary: generatePerformanceSummary(databases),
        quickActions: generateQuickActions(),
        typeStats,
        environmentStats
      });
    } catch (error) {
      console.error('获取仪表板数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemStats = async () => {
    return {
      totalDatabases: 127,
      activeDatabases: 115,
      totalConnections: 1847,
      avgResponseTime: 45,
      systemHealth: 85,
      alertsToday: 8,
      performanceScore: 78,
      cpuUsage: 72,
      memoryUsage: 68,
      diskUsage: 45,
      networkIO: 1.2
    };
  };

  const fetchRecentAlerts = async () => {
    return [
      {
        id: 1,
        level: 'critical',
        message: 'PostgreSQL实例CPU使用率达到92%',
        timestamp: new Date(Date.now() - 5 * 60 * 1000),
        database: 'prod-postgres-01',
        type: 'postgresql'
      },
      {
        id: 2,
        level: 'warning',
        message: '连接数接近上限 (180/200)',
        timestamp: new Date(Date.now() - 10 * 60 * 1000),
        database: 'test-mysql-02',
        type: 'mysql'
      },
      {
        id: 3,
        level: 'warning',
        message: '索引优化建议：users表需要添加复合索引',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
        database: 'prod-postgres-02',
        type: 'postgresql'
      },
      {
        id: 4,
        level: 'info',
        message: 'MongoDB副本集同步延迟增加',
        timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000),
        database: 'prod-mongo-01',
        type: 'mongodb'
      }
    ];
  };

  const generateTypeStats = (databases) => {
    const stats = {};
    databases.forEach(db => {
      const type = db.type || 'unknown';
      if (!stats[type]) {
        stats[type] = {
          total: 0,
          healthy: 0,
          warning: 0,
          critical: 0
        };
      }
      stats[type].total++;
      if (db.health_status === 'healthy') stats[type].healthy++;
      else if (db.health_status === 'warning') stats[type].warning++;
      else if (db.health_status === 'critical') stats[type].critical++;
    });
    return stats;
  };

  const generateEnvironmentStats = (databases) => {
    const stats = {};
    databases.forEach(db => {
      const env = db.environment || 'unknown';
      if (!stats[env]) {
        stats[env] = {
          total: 0,
          healthy: 0,
          warning: 0,
          critical: 0,
          avgCpu: 0,
          avgMemory: 0
        };
      }
      stats[env].total++;
      if (db.health_status === 'healthy') stats[env].healthy++;
      else if (db.health_status === 'warning') stats[env].warning++;
      else if (db.health_status === 'critical') stats[env].critical++;
    });
    
    // 模拟CPU和内存使用率
    Object.keys(stats).forEach(env => {
      stats[env].avgCpu = env === 'production' ? 72 : env === 'staging' ? 45 : 35;
      stats[env].avgMemory = env === 'production' ? 68 : env === 'staging' ? 52 : 40;
    });
    
    return stats;
  };

  const generatePerformanceSummary = (databases) => {
    const totalDatabases = databases.length;
    const healthyDatabases = databases.filter(db => db.health_status === 'healthy').length;
    const healthRatio = totalDatabases > 0 ? (healthyDatabases / totalDatabases) * 100 : 0;

    return {
      healthRatio,
      totalDatabases,
      healthyDatabases,
      needsAttention: totalDatabases - healthyDatabases
    };
  };

  const generateQuickActions = () => {
    return [
      {
        title: '添加数据库实例',
        description: '快速添加新的数据库实例进行监控',
        icon: <PlusOutlined />,
        link: '/databases',
        color: '#1890ff'
      },
      {
        title: '性能监控',
        description: '查看实时性能指标和趋势分析',
        icon: <BarChartOutlined />,
        link: '/performance/dashboard',
        color: '#52c41a'
      },
      {
        title: '慢查询分析',
        description: '分析和优化数据库慢查询',
        icon: <ThunderboltOutlined />,
        link: '/performance/slow-queries',
        color: '#faad14'
      },
      {
        title: '系统诊断',
        description: '全面检查系统健康状况',
        icon: <SettingOutlined />,
        link: '/performance/system-diagnosis',
        color: '#f5222d'
      }
    ];
  };

  // 过滤数据库实例
  const filteredDatabases = useMemo(() => {
    return dashboardData.databases.filter(db => {
      const matchesSearch = !searchTerm || 
        db.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        db.host.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesType = selectedType === 'all' || db.type === selectedType;
      const matchesEnvironment = selectedEnvironment === 'all' || db.environment === selectedEnvironment;
      
      return matchesSearch && matchesType && matchesEnvironment;
    });
  }, [dashboardData.databases, searchTerm, selectedType, selectedEnvironment]);

  const getHealthColor = (ratio) => {
    if (ratio >= 80) return '#52c41a';
    if (ratio >= 60) return '#faad14';
    return '#f5222d';
  };

  const getAlertIcon = (level) => {
    const icons = {
      critical: <WarningOutlined style={{ color: '#f5222d' }} />,
      warning: <WarningOutlined style={{ color: '#faad14' }} />,
      info: <CheckCircleOutlined style={{ color: '#1890ff' }} />
    };
    return icons[level] || <CheckCircleOutlined />;
  };

  const getEnvironmentColor = (env) => {
    const colors = {
      production: '#f5222d',
      staging: '#faad14',
      development: '#52c41a'
    };
    return colors[env] || '#666';
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <p style={{ marginTop: 16, color: '#666' }}>正在加载仪表板数据...</p>
      </div>
    );
  }

  // 渲染总览标签页
  const renderOverviewTab = () => (
    <div>
      {/* 核心指标统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="数据库实例"
              value={dashboardData.systemStats?.totalDatabases || 0}
              suffix="个"
              prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃连接"
              value={dashboardData.systemStats?.totalConnections || 0}
              prefix={<RocketOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均响应时间"
              value={dashboardData.systemStats?.avgResponseTime || 0}
              suffix="ms"
              prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日告警"
              value={dashboardData.systemStats?.alertsToday || 0}
              prefix={<FireOutlined style={{ color: '#f5222d' }} />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 系统健康概览 */}
        <Col xs={24} lg={8}>
          <Card title={
            <span>
              <BulbOutlined style={{ marginRight: 8, color: '#52c41a' }} />
              系统健康概览
            </span>
          } style={{ height: '100%' }}>
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <Progress
                type="circle"
                percent={dashboardData.systemStats?.systemHealth || 0}
                strokeColor={getHealthColor(dashboardData.systemStats?.systemHealth || 0)}
                size={120}
                format={percent => (
                  <div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{percent.toFixed(1)}%</div>
                    <div style={{ fontSize: '12px', color: '#666' }}>健康度</div>
                  </div>
                )}
              />
            </div>
            
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="健康实例"
                  value={dashboardData.performanceSummary?.healthyDatabases || 0}
                  suffix={`/ ${dashboardData.performanceSummary?.totalDatabases || 0}`}
                  valueStyle={{ color: '#52c41a', fontSize: '16px' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="需关注"
                  value={dashboardData.performanceSummary?.needsAttention || 0}
                  suffix="个"
                  valueStyle={{ color: '#faad14', fontSize: '16px' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>

        {/* 最近告警 */}
        <Col xs={24} lg={8}>
          <Card 
            title={
              <span>
                <WarningOutlined style={{ marginRight: 8, color: '#faad14' }} />
                最近告警
              </span>
            }
            extra={
              <Link to="/monitoring">
                查看全部 <RightOutlined />
              </Link>
            }
            style={{ height: '100%' }}
          >
            {dashboardData.recentAlerts.length > 0 ? (
              <List
                size="small"
                dataSource={dashboardData.recentAlerts.slice(0, 4)}
                renderItem={item => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={getAlertIcon(item.level)}
                      title={<span style={{ fontSize: '13px' }}>{item.message}</span>}
                      description={
                        <Space size={4}>
                          <Tag size="small" color={DATABASE_TYPES[item.type]?.color || '#666'}>
                            {DATABASE_TYPES[item.type]?.name || item.type}
                          </Tag>
                          <span style={{ color: '#999', fontSize: '11px' }}>
                            {item.timestamp.toLocaleString()}
                          </span>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Empty 
                description="暂无告警信息" 
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                style={{ padding: '20px 0' }}
              />
            )}
          </Card>
        </Col>
        
        {/* 快速操作 */}
        <Col xs={24} lg={8}>
          <Card title={
            <span>
              <RocketOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              快速操作
            </span>
          } style={{ height: '100%' }}>
            <Row gutter={[8, 8]}>
              {dashboardData.quickActions.map((action, index) => (
                <Col xs={12} key={index}>
                  <Link to={action.link}>
                    <Card
                      size="small"
                      hoverable
                      style={{
                        textAlign: 'center',
                        borderColor: action.color,
                        transition: 'all 0.3s'
                      }}
                      bodyStyle={{ padding: '12px 8px' }}
                    >
                      <div style={{
                        fontSize: '20px',
                        color: action.color,
                        marginBottom: 4
                      }}>
                        {action.icon}
                      </div>
                      <div style={{
                        fontSize: '12px',
                        fontWeight: 'bold',
                        color: '#262626'
                      }}>
                        {action.title}
                      </div>
                    </Card>
                  </Link>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );

  // 渲染数据库类型标签页
  const renderDatabaseTypeTab = () => (
    <div>
      {/* 数据库类型统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {Object.entries(dashboardData.typeStats).map(([type, stats]) => {
          const typeConfig = DATABASE_TYPES[type] || { icon: '🗃️', color: '#666', name: type };
          const healthRatio = stats.total > 0 ? (stats.healthy / stats.total) * 100 : 0;
          
          return (
            <Col xs={24} sm={12} md={8} lg={6} key={type}>
              <Card hoverable style={{ height: '100%' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '32px', marginBottom: 8 }}>
                    {typeConfig.icon}
                  </div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: 4 }}>
                    {typeConfig.name}
                  </div>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: typeConfig.color, marginBottom: 8 }}>
                    {stats.total}
                  </div>
                  <div style={{ marginBottom: 12 }}>
                    <Progress
                      percent={healthRatio}
                      strokeColor={getHealthColor(healthRatio)}
                      size="small"
                      showInfo={false}
                    />
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      健康度 {healthRatio.toFixed(1)}%
                    </div>
                  </div>
                  <Space size={8}>
                    <Tag color="green">健康 {stats.healthy}</Tag>
                    <Tag color="orange">警告 {stats.warning}</Tag>
                    <Tag color="red">严重 {stats.critical}</Tag>
                  </Space>
                </div>
              </Card>
            </Col>
          );
        })}
      </Row>
      
      {/* 数据库实例网格 */}
      <Card title="数据库实例" style={{ marginTop: 16 }}>
        <div style={{ marginBottom: 16 }}>
          <Space wrap>
            <Search
              placeholder="搜索数据库实例..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ width: 200 }}
              prefix={<SearchOutlined />}
            />
            <Select
              value={selectedType}
              onChange={setSelectedType}
              style={{ width: 150 }}
              placeholder="选择类型"
            >
              <Option value="all">全部类型</Option>
              {Object.entries(DATABASE_TYPES).map(([key, config]) => (
                <Option key={key} value={key}>
                  {config.icon} {config.name}
                </Option>
              ))}
            </Select>
            <Select
              value={selectedEnvironment}
              onChange={setSelectedEnvironment}
              style={{ width: 150 }}
              placeholder="选择环境"
            >
              <Option value="all">全部环境</Option>
              <Option value="production">生产环境</Option>
              <Option value="staging">测试环境</Option>
              <Option value="development">开发环境</Option>
            </Select>
          </Space>
        </div>
        
        <div className="database-instance-grid">
          {filteredDatabases.map(db => {
            const typeConfig = DATABASE_TYPES[db.type] || { icon: '🗃️', color: '#666', name: db.type };
            
            return (
              <div key={db.id} className="database-instance-card">
                <Card 
                  size="small" 
                  hoverable
                  bodyStyle={{ padding: '16px' }}
                  style={{ height: '100%' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
                    <span style={{ fontSize: '24px', marginRight: 12 }}>
                      {typeConfig.icon}
                    </span>
                    <strong style={{ fontSize: '16px', flex: 1 }}>{db.name}</strong>
                    <Badge 
                      status={db.health_status === 'healthy' ? 'success' : 
                             db.health_status === 'warning' ? 'warning' : 'error'} 
                    />
                  </div>
                  <div style={{ fontSize: '13px', color: '#666', marginBottom: 8 }}>
                    {db.host}:{db.port}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Tag 
                      size="small" 
                      color={getEnvironmentColor(db.environment)}
                    >
                      {db.environment}
                    </Tag>
                    <Tag size="small" color={typeConfig.color}>
                      {typeConfig.name}
                    </Tag>
                  </div>
                </Card>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );

  // 渲染环境视图标签页
  const renderEnvironmentTab = () => (
    <div>
      {/* 环境统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {Object.entries(dashboardData.environmentStats).map(([env, stats]) => {
          const envConfig = {
            production: { name: '生产环境', color: '#f5222d', icon: '🔴' },
            staging: { name: '测试环境', color: '#faad14', icon: '🟡' },
            development: { name: '开发环境', color: '#52c41a', icon: '🟢' }
          };
          const config = envConfig[env] || { name: env, color: '#666', icon: '⚪' };
          
          return (
            <Col xs={24} md={8} key={env}>
              <Card>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
                  <span style={{ fontSize: '24px', marginRight: 12 }}>
                    {config.icon}
                  </span>
                  <div>
                    <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                      {config.name}
                    </div>
                    <div style={{ fontSize: '20px', fontWeight: 'bold', color: config.color }}>
                      {stats.total} 个实例
                    </div>
                  </div>
                </div>
                
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="CPU使用率"
                      value={stats.avgCpu}
                      suffix="%"
                      valueStyle={{ fontSize: '16px', color: config.color }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="内存使用率"
                      value={stats.avgMemory}
                      suffix="%"
                      valueStyle={{ fontSize: '16px', color: config.color }}
                    />
                  </Col>
                </Row>
                
                <Divider style={{ margin: '12px 0' }} />
                
                <Space>
                  <Tag color="green">健康 {stats.healthy}</Tag>
                  <Tag color="orange">警告 {stats.warning}</Tag>
                  <Tag color="red">严重 {stats.critical}</Tag>
                </Space>
              </Card>
            </Col>
          );
        })}
      </Row>
    </div>
  );

  return (
    <div style={{ padding: isMobile ? '8px' : '0' }}>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        size={isMobile ? 'small' : 'default'}
        tabBarStyle={{ marginBottom: 16 }}
      >
        <TabPane 
          tab={
            <span>
              <GlobalOutlined />
              总览
            </span>
          } 
          key="overview"
        >
          {renderOverviewTab()}
        </TabPane>
        
        <TabPane 
          tab={
            <span>
              <DatabaseOutlined />
              数据库类型
            </span>
          } 
          key="database-type"
        >
          {renderDatabaseTypeTab()}
        </TabPane>
        
        <TabPane 
          tab={
            <span>
              <TeamOutlined />
              环境视图
            </span>
          } 
          key="environment"
        >
          {renderEnvironmentTab()}
        </TabPane>
      </Tabs>
    </div>
  );
};

export default EnhancedDashboard;