import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Card, Row, Col, Statistic, Progress, Alert, Button, Space, 
  List, Avatar, Badge, Divider, Timeline, Empty, Spin, Tag
} from 'antd';
import {
  DatabaseOutlined, ThunderboltOutlined, BarChartOutlined,
  CheckCircleOutlined, WarningOutlined, ClockCircleOutlined,
  RightOutlined, PlusOutlined, EyeOutlined, SettingOutlined,
  TrophyOutlined, RocketOutlined, FireOutlined, BulbOutlined
} from '@ant-design/icons';

import { databaseAPI, performanceAPI } from '../services/api';
import DatabaseTypeCard from '../components/DatabaseTypeCard';
import DatabaseInstanceCard from '../components/DatabaseInstanceCard';
import LargeScaleInstanceView from '../components/LargeScaleInstanceView';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [viewMode, setViewMode] = useState('overview'); // 'overview' | 'large-scale'
  const [showLargeScaleHint, setShowLargeScaleHint] = useState(false);
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
        quickActions: generateQuickActions(),
        typeStats: generateTypeStats(databases)
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

  // 生成数据库类型统计 - 参考业界标准
  const generateTypeStats = (databases) => {
    const typeMap = {
      postgresql: { total: 0, healthy: 0, warning: 0, critical: 0 },
      mysql: { total: 0, healthy: 0, warning: 0, critical: 0 },
      oceanbase: { total: 0, healthy: 0, warning: 0, critical: 0 },
      mongodb: { total: 0, healthy: 0, warning: 0, critical: 0 },
      redis: { total: 0, healthy: 0, warning: 0, critical: 0 },
      oracle: { total: 0, healthy: 0, warning: 0, critical: 0 },
      sqlserver: { total: 0, healthy: 0, warning: 0, critical: 0 }
    };

    databases.forEach(db => {
      const type = getDatabaseTypeName(db.type_id).toLowerCase();
      if (typeMap[type]) {
        typeMap[type].total++;
        if (db.health_status === 'healthy') {
          typeMap[type].healthy++;
        } else if (db.health_status === 'warning') {
          typeMap[type].warning++;
        } else if (db.health_status === 'critical') {
          typeMap[type].critical++;
        }
      }
    });

    // 只返回有数据的类型
    return Object.fromEntries(
      Object.entries(typeMap).filter(([_, stats]) => stats.total > 0)
    );
  };

  // 获取数据库类型名称
  const getDatabaseTypeName = (typeId) => {
    const types = {
      1: 'PostgreSQL',
      2: 'MySQL',
      3: 'MongoDB',
      4: 'Redis',
      5: 'OceanBase',
      6: 'Oracle',
      7: 'SQL Server'
    };
    return types[typeId] || 'Unknown';
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
      {/* 全局状态概览栏 */}
      <Card 
        style={{ 
          marginBottom: 16, 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          border: 'none',
          color: 'white'
        }}
        bodyStyle={{ padding: '16px 24px' }}
      >
        <Row align="middle" justify="space-between">
          <Col>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
              <DatabaseOutlined style={{ fontSize: '24px', marginRight: 12 }} />
              <h2 style={{ margin: 0, color: 'white', fontSize: '20px' }}>
                统一数据库管理平台
              </h2>
              <Badge 
                count="实时监控中" 
                style={{ 
                  backgroundColor: '#52c41a', 
                  marginLeft: 16,
                  fontSize: '12px'
                }} 
              />
            </div>
            <p style={{ margin: 0, color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>
              统一监控和管理多种数据库类型，提供智能化的性能分析和优化建议
            </p>
          </Col>
          <Col>
            <Space size="large">
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff4d4f' }}>
                  {dashboardData.systemStats?.alertsToday || 0}
                </div>
                <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.8)' }}>严重告警</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#faad14' }}>
                  {Math.floor((dashboardData.systemStats?.alertsToday || 0) * 1.5)}
                </div>
                <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.8)' }}>警告</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                  {dashboardData.performanceSummary?.healthyDatabases || 0}
                </div>
                <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.8)' }}>健康实例</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                  {dashboardData.systemStats?.totalDatabases || 0}
                </div>
                <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.8)' }}>总实例数</div>
              </div>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 核心指标卡片 */}
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
                title="今日告警"
                value={dashboardData.systemStats?.alertsToday || 0}
                prefix={<FireOutlined />}
                color="#f5222d"
              />
            </Col>
          </Row>
        </div>
      ) : (
        // 桌面端：增强的统计卡片
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={12}>
            <Card 
              hoverable
              style={{ 
                borderLeft: '4px solid #1890ff',
                boxShadow: '0 2px 8px rgba(24, 144, 255, 0.1)'
              }}
            >
              <Statistic
                title="数据库实例"
                value={dashboardData.systemStats?.totalDatabases || 0}
                suffix="个"
                prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
                valueStyle={{ color: '#1890ff', fontSize: '24px' }}
              />
              <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                活跃: {dashboardData.systemStats?.activeDatabases || 0} 个
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={12}>
            <Card 
              hoverable
              style={{ 
                borderLeft: '4px solid #f5222d',
                boxShadow: '0 2px 8px rgba(245, 34, 45, 0.1)'
              }}
            >
              <Statistic
                title="今日告警"
                value={dashboardData.systemStats?.alertsToday || 0}
                prefix={<FireOutlined style={{ color: '#f5222d' }} />}
                valueStyle={{ color: '#f5222d', fontSize: '24px' }}
              />
              <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                已解决: {Math.floor((dashboardData.systemStats?.alertsToday || 0) * 0.3)} 个
              </div>
            </Card>
          </Col>
        </Row>
      )}

      {/* 数据库类型分布区域 - 参考设计提案 */}
      <Card 
        title={
          <span>
            <DatabaseOutlined style={{ marginRight: 8, color: '#1890ff' }} />
            数据库类型分布
          </span>
        }
        style={{ marginBottom: 24 }}
        bodyStyle={{ padding: '20px' }}
      >
        <Row gutter={[16, 16]}>
          {Object.entries(dashboardData.typeStats || {}).map(([type, stats]) => (
            <Col xs={24} sm={12} md={8} lg={6} key={type}>
              <DatabaseTypeCard
                type={type}
                stats={stats}
                onClick={() => {
                  // 可以添加点击处理逻辑，比如跳转到特定类型的实例列表
                  console.log(`点击了 ${type} 类型`);
                }}
                showActions={true}
              />
            </Col>
          ))}
          
          {/* 如果没有数据，显示空状态 */}
          {Object.keys(dashboardData.typeStats || {}).length === 0 && (
            <Col span={24}>
              <div style={{ 
                textAlign: 'center', 
                padding: '40px 20px',
                color: '#8c8c8c'
              }}>
                <DatabaseOutlined style={{ fontSize: '48px', marginBottom: 16 }} />
                <p style={{ margin: 0, fontSize: '16px' }}>暂无数据库实例</p>
                <p style={{ margin: '8px 0 0 0', fontSize: '14px' }}>
                  点击右上角按钮添加第一个数据库实例
                </p>
              </div>
            </Col>
          )}
        </Row>
      </Card>

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

      {/* 大规模实例管理提示 */}
      {dashboardData.databases.length > 100 && !showLargeScaleHint && (
        <Alert
          message="检测到大量数据库实例"
          description={
            <div>
              <p style={{ margin: '0 0 8px 0' }}>
                当前有 <strong>{dashboardData.databases.length}</strong> 个数据库实例，建议使用列表模式进行高效管理。
              </p>
              <Space>
                <Button 
                  type="primary" 
                  size="small"
                  onClick={() => {
                    setViewMode('large-scale');
                    setShowLargeScaleHint(true);
                  }}
                >
                  切换到列表模式
                </Button>
                <Button 
                  size="small"
                  onClick={() => setShowLargeScaleHint(true)}
                >
                  稍后提醒
                </Button>
              </Space>
            </div>
          }
          type="info"
          showIcon
          closable
          onClose={() => setShowLargeScaleHint(true)}
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 数据库实例概览 - 支持大规模管理 */}
      {dashboardData.databases.length > 0 && (
        <Card 
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <DatabaseOutlined style={{ color: '#1890ff' }} />
              <span>数据库实例概览</span>
              {dashboardData.databases.length > 50 && (
                <Tag color="orange" style={{ margin: 0 }}>
                  {dashboardData.databases.length} 个实例
                </Tag>
              )}
              {dashboardData.databases.length > 100 && (
                <Tag color="red" style={{ margin: 0 }}>
                  大规模
                </Tag>
              )}
            </div>
          }
          extra={
            <Space>
              {dashboardData.databases.length > 20 && (
                <Button
                  type={viewMode === 'large-scale' ? 'primary' : 'default'}
                  onClick={() => setViewMode(viewMode === 'large-scale' ? 'overview' : 'large-scale')}
                  size="small"
                  icon={viewMode === 'large-scale' ? <EyeOutlined /> : <BarChartOutlined />}
                >
                  {viewMode === 'large-scale' ? '卡片视图' : '列表视图'}
                </Button>
              )}
              <Link to="/databases">
                管理全部 <RightOutlined />
              </Link>
            </Space>
          }
          style={{ marginTop: 16 }}
          bodyStyle={{ padding: '20px' }}
        >
          {viewMode === 'large-scale' ? (
            <LargeScaleInstanceView
              instances={dashboardData.databases}
              loading={loading}
              onInstanceClick={(instance) => {
                console.log(`点击了实例: ${instance.name}`);
                // 可以跳转到实例详情页
              }}
              onRefresh={fetchDashboardData}
            />
          ) : (
            <div className="database-instance-grid">
              {dashboardData.databases.slice(0, 8).map(db => (
                <div key={db.id} className="database-instance-card">
                  <DatabaseInstanceCard
                    database={db}
                    onClick={() => {
                      // 可以添加点击处理逻辑，比如跳转到实例详情页
                      console.log(`点击了实例: ${db.name}`);
                    }}
                    onConfig={(database) => {
                      console.log(`配置实例: ${database.name}`);
                      // 可以打开配置对话框或跳转到配置页面
                    }}
                    onMonitor={(database) => {
                      console.log(`监控实例: ${database.name}`);
                      // 可以跳转到性能监控页面
                    }}
                    onTools={(database) => {
                      console.log(`工具集: ${database.name}`);
                      // 可以打开工具集面板
                    }}
                    showActions={true}
                  />
                </div>
              ))}
            </div>
          )}
          
          {/* 如果实例数量超过8个且为概览模式，显示更多按钮 */}
          {viewMode === 'overview' && dashboardData.databases.length > 8 && (
            <div style={{ 
              textAlign: 'center', 
              marginTop: 16,
              padding: '16px',
              border: '2px dashed #d9d9d9',
              borderRadius: '8px',
              background: '#fafafa'
            }}>
              <p style={{ margin: '0 0 12px 0', color: '#8c8c8c' }}>
                还有 {dashboardData.databases.length - 8} 个数据库实例
              </p>
              <Space>
                <Link to="/databases">
                  <Button type="primary" ghost>
                    查看全部实例
                  </Button>
                </Link>
                {dashboardData.databases.length > 50 && (
                  <Button 
                    type="default" 
                    onClick={() => setViewMode('large-scale')}
                  >
                    切换到列表模式
                  </Button>
                )}
              </Space>
            </div>
          )}
        </Card>
      )}

    </div>
  );
};

export default Dashboard;
