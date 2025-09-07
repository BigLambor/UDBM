import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Card, Row, Col, Statistic, Progress, Alert, Button, Space, 
  List, Avatar, Badge, Divider, Timeline, Empty, Spin
} from 'antd';
import {
  DatabaseOutlined, ThunderboltOutlined, BarChartOutlined,
  CheckCircleOutlined, WarningOutlined, ClockCircleOutlined,
  RightOutlined, PlusOutlined, EyeOutlined, SettingOutlined,
  TrophyOutlined, RocketOutlined, FireOutlined, BulbOutlined
} from '@ant-design/icons';

import { databaseAPI, performanceAPI } from '../services/api';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [dashboardData, setDashboardData] = useState({
    databases: [],
    systemStats: null,
    recentAlerts: [],
    performanceSummary: null,
    quickActions: []
  });

  // 检测是否为移动端
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);

    return () => {
      window.removeEventListener('resize', checkMobile);
    };
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // 并行获取各种数据
      const [databases, systemStats, alerts] = await Promise.all([
        databaseAPI.getDatabases().catch(() => []),
        fetchSystemStats().catch(() => null),
        fetchRecentAlerts().catch(() => [])
      ]);

      setDashboardData({
        databases: Array.isArray(databases) ? databases : [],
        systemStats,
        recentAlerts: Array.isArray(alerts) ? alerts : [],
        performanceSummary: generatePerformanceSummary(databases),
        quickActions: generateQuickActions()
      });
    } catch (error) {
      console.error('获取仪表板数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemStats = async () => {
    // 模拟系统统计数据
    return {
      totalDatabases: 5,
      activeDatabases: 4,
      totalConnections: 127,
      avgResponseTime: 45,
      systemHealth: 85,
      alertsToday: 3,
      performanceScore: 78
    };
  };

  const fetchRecentAlerts = async () => {
    // 模拟最近告警数据
    return [
      {
        id: 1,
        level: 'warning',
        message: 'PostgreSQL实例CPU使用率达到85%',
        timestamp: new Date(Date.now() - 30 * 60 * 1000),
        database: 'prod-postgres-01'
      },
      {
        id: 2,
        level: 'info',
        message: '索引优化建议：users表需要添加复合索引',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
        database: 'prod-postgres-02'
      },
      {
        id: 3,
        level: 'critical',
        message: '连接池即将耗尽，当前使用率95%',
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
        database: 'prod-mysql-01'
      }
    ];
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

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <p style={{ marginTop: 16, color: '#666' }}>正在加载仪表板数据...</p>
      </div>
    );
  }

  // 移动端统计卡片组件
  const MobileStatsCard = ({ title, value, suffix, prefix, color }) => (
    <Card size="small" bodyStyle={{ padding: '12px', textAlign: 'center' }}>
      <Statistic
        title={<span style={{ fontSize: '12px', color: '#666' }}>{title}</span>}
        value={value}
        suffix={suffix}
        prefix={prefix}
        valueStyle={{ color, fontSize: '20px', fontWeight: 'bold' }}
      />
    </Card>
  );

  return (
    <div style={{ padding: isMobile ? '0' : '0' }}>
      {/* 核心指标 */}
      {isMobile ? (
        // 移动端：纵向排列的统计卡片
        <div style={{ marginBottom: 16 }}>
          <Row gutter={[8, 8]}>
            <Col span={12}>
              <MobileStatsCard
                title="数据库实例"
                value={dashboardData.systemStats?.totalDatabases || 0}
                suffix="个"
                prefix={<DatabaseOutlined />}
                color="#1890ff"
              />
            </Col>
            <Col span={12}>
              <MobileStatsCard
                title="活跃连接"
                value={dashboardData.systemStats?.totalConnections || 0}
                prefix={<RocketOutlined />}
                color="#52c41a"
              />
            </Col>
            <Col span={12}>
              <MobileStatsCard
                title="响应时间"
                value={dashboardData.systemStats?.avgResponseTime || 0}
                suffix="ms"
                prefix={<ClockCircleOutlined />}
                color="#faad14"
              />
            </Col>
            <Col span={12}>
              <MobileStatsCard
                title="今日告警"
                value={dashboardData.systemStats?.alertsToday || 0}
                prefix={<FireOutlined />}
                color="#f5222d"
              />
            </Col>
          </Row>
        </div>
      ) : (
        // 桌面端：横向排列的统计卡片
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
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
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {/* 系统健康状况 */}
        <Col xs={24} lg={8}>
          <Card title={
            <span>
              <BulbOutlined style={{ marginRight: 8, color: '#52c41a' }} />
              系统健康概览
            </span>
          }>
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <Progress
                type="circle"
                percent={dashboardData.systemStats?.systemHealth || 0}
                strokeColor={getHealthColor(dashboardData.systemStats?.systemHealth || 0)}
                size={120}
                format={percent => (
                  <div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{percent.toFixed(2)}%</div>
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
                  valueStyle={{ color: '#52c41a', fontSize: '18px' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="需关注"
                  value={dashboardData.performanceSummary?.needsAttention || 0}
                  suffix="个"
                  valueStyle={{ color: '#faad14', fontSize: '18px' }}
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
          >
            {dashboardData.recentAlerts.length > 0 ? (
              <List
                dataSource={dashboardData.recentAlerts}
                renderItem={item => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={getAlertIcon(item.level)}
                      title={item.message}
                      description={
                        <Space>
                          <span style={{ color: '#666' }}>{item.database}</span>
                          <Divider type="vertical" />
                          <span style={{ color: '#999', fontSize: '12px' }}>
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
          } bodyStyle={{ padding: isMobile ? '12px' : '16px' }}>
            {isMobile ? (
              // 移动端：垂直排列的操作按钮
              <Space direction="vertical" style={{ width: '100%' }}>
                {dashboardData.quickActions.map((action, index) => (
                  <Link key={index} to={action.link} style={{ width: '100%' }}>
                    <Button
                      type="default"
                      icon={action.icon}
                      size="large"
                      block
                      style={{
                        height: '48px',
                        borderColor: action.color,
                        color: action.color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: '500'
                      }}
                    >
                      {action.title}
                    </Button>
                  </Link>
                ))}
              </Space>
            ) : (
              // 桌面端：网格排列的操作卡片
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
                          color: '#262626',
                          marginBottom: 2
                        }}>
                          {action.title}
                        </div>
                      </Card>
                    </Link>
                  </Col>
                ))}
              </Row>
            )}
          </Card>
        </Col>
      </Row>

      {/* 数据库实例概览 - 优化布局，减少留白 */}
      {dashboardData.databases.length > 0 && (
        <Card 
          title={
            <span>
              <DatabaseOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              数据库实例概览
            </span>
          }
          extra={
            <Link to="/databases">
              管理全部 <RightOutlined />
            </Link>
          }
          style={{ marginTop: 16 }}
          bodyStyle={{ padding: '16px' }}
        >
          <Row gutter={[12, 12]}>
            {dashboardData.databases.slice(0, 8).map(db => (
              <Col xs={24} sm={12} md={8} lg={6} key={db.id}>
                <Card 
                  size="small" 
                  hoverable
                  bodyStyle={{ padding: '12px' }}
                  style={{ height: '100%' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: 6 }}>
                    <Avatar 
                      icon={<DatabaseOutlined />} 
                      style={{ backgroundColor: '#1890ff', marginRight: 8 }}
                      size="small"
                    />
                    <strong style={{ fontSize: '13px' }}>{db.name}</strong>
                    <Badge 
                      status={db.health_status === 'healthy' ? 'success' : 'warning'} 
                      style={{ marginLeft: 'auto' }}
                    />
                  </div>
                  <p style={{ margin: 0, color: '#666', fontSize: '11px' }}>
                    {db.host}:{db.port}
                  </p>
                  <p style={{ margin: '2px 0 0 0', color: '#999', fontSize: '10px' }}>
                    {db.environment} 环境
                  </p>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* 添加更多实用信息区域 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12}>
          <Card 
            title={
              <span>
                <BarChartOutlined style={{ marginRight: 8, color: '#52c41a' }} />
                性能趋势
              </span>
            }
            size="small"
            bodyStyle={{ padding: '16px' }}
          >
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="CPU使用率"
                  value={72}
                  suffix="%"
                  valueStyle={{ color: '#faad14', fontSize: '16px' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="内存使用率"
                  value={68}
                  suffix="%"
                  valueStyle={{ color: '#52c41a', fontSize: '16px' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="磁盘使用率"
                  value={45}
                  suffix="%"
                  valueStyle={{ color: '#1890ff', fontSize: '16px' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
        
        <Col xs={24} md={12}>
          <Card 
            title={
              <span>
                <ClockCircleOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                今日统计
              </span>
            }
            size="small"
            bodyStyle={{ padding: '16px' }}
          >
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="查询总数"
                  value={15420}
                  valueStyle={{ color: '#1890ff', fontSize: '16px' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="慢查询"
                  value={23}
                  valueStyle={{ color: '#f5222d', fontSize: '16px' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="错误数"
                  value={5}
                  valueStyle={{ color: '#faad14', fontSize: '16px' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
