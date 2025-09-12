import React from 'react';
import { Card, Avatar, Badge, Tag, Space, Tooltip, Button, Progress, Divider, Row, Col } from 'antd';
import { 
  DatabaseOutlined, 
  CheckCircleOutlined, 
  WarningOutlined, 
  CloseCircleOutlined,
  SettingOutlined,
  BarChartOutlined,
  ToolOutlined,
  ClockCircleOutlined,
  EnvironmentOutlined,
  LinkOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';

// 数据库类型配置
const DATABASE_TYPE_CONFIG = {
  postgresql: { icon: '🐘', color: '#336791', name: 'PostgreSQL' },
  mysql: { icon: '🐬', color: '#4479A1', name: 'MySQL' },
  mongodb: { icon: '🍃', color: '#47A248', name: 'MongoDB' },
  redis: { icon: '⚡', color: '#DC382D', name: 'Redis' },
  oracle: { icon: '🔶', color: '#F80000', name: 'Oracle' },
  sqlserver: { icon: '🏢', color: '#CC2927', name: 'SQL Server' }
};

// 环境配置
const ENVIRONMENT_CONFIG = {
  production: { color: '#f5222d', icon: '🔴', name: '生产环境' },
  staging: { color: '#faad14', icon: '🟡', name: '测试环境' },
  development: { color: '#52c41a', icon: '🟢', name: '开发环境' }
};

const DatabaseInstanceCard = ({ 
  database, 
  onClick, 
  onConfig, 
  onMonitor, 
  onTools,
  showActions = true
}) => {
  const typeConfig = DATABASE_TYPE_CONFIG[database.type] || DATABASE_TYPE_CONFIG.postgresql;
  const envConfig = ENVIRONMENT_CONFIG[database.environment] || { 
    color: '#666', 
    icon: '⚪', 
    name: database.environment 
  };

  // 健康状态配置
  const getHealthConfig = (status) => {
    const configs = {
      healthy: { 
        color: '#52c41a', 
        icon: CheckCircleOutlined, 
        text: '健康',
        bgColor: '#f6ffed',
        borderColor: '#b7eb8f'
      },
      warning: { 
        color: '#faad14', 
        icon: WarningOutlined, 
        text: '警告',
        bgColor: '#fffbe6',
        borderColor: '#ffe58f'
      },
      critical: { 
        color: '#f5222d', 
        icon: CloseCircleOutlined, 
        text: '严重',
        bgColor: '#fff2f0',
        borderColor: '#ffccc7'
      },
      unknown: { 
        color: '#8c8c8c', 
        icon: DatabaseOutlined, 
        text: '未知',
        bgColor: '#fafafa',
        borderColor: '#d9d9d9'
      }
    };
    return configs[status] || configs.unknown;
  };

  const healthConfig = getHealthConfig(database.health_status);

  // 模拟性能数据 - 实际项目中应该从API获取
  const performanceData = {
    cpuUsage: Math.floor(Math.random() * 100),
    memoryUsage: Math.floor(Math.random() * 100),
    connectionCount: Math.floor(Math.random() * 200),
    lastCheck: new Date(Date.now() - Math.floor(Math.random() * 60) * 60 * 1000)
  };

  const getPerformanceColor = (value, thresholds = { warning: 70, critical: 85 }) => {
    if (value >= thresholds.critical) return '#f5222d';
    if (value >= thresholds.warning) return '#faad14';
    return '#52c41a';
  };

  const formatLastCheck = (date) => {
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / (1000 * 60));
    
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}小时前`;
    const days = Math.floor(hours / 24);
    return `${days}天前`;
  };

  return (
    <Card
      hoverable
      onClick={onClick}
      style={{
        height: '100%',
        borderRadius: '12px',
        border: `1px solid ${healthConfig.borderColor}`,
        background: healthConfig.bgColor,
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        cursor: 'pointer',
        position: 'relative',
        overflow: 'hidden'
      }}
      bodyStyle={{ padding: '16px' }}
      className="database-instance-card"
    >
      {/* 健康状态指示条 */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: `linear-gradient(90deg, ${healthConfig.color} 0%, ${healthConfig.color}80 100%)`,
          borderRadius: '12px 12px 0 0'
        }}
      />

      {/* 头部区域 */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'flex-start', 
        justifyContent: 'space-between',
        marginBottom: 12
      }}>
        <div style={{ display: 'flex', alignItems: 'center', flex: 1, minWidth: 0 }}>
          <Avatar
            size={40}
            style={{ 
              backgroundColor: typeConfig.color,
              marginRight: 8,
              flexShrink: 0
            }}
            icon={<DatabaseOutlined />}
          />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              marginBottom: 4,
              gap: 8
            }}>
              <h4 style={{ 
                margin: 0, 
                fontSize: '16px',
                fontWeight: 600,
                color: '#262626',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {database.name}
              </h4>
              <Badge
                status={database.health_status === 'healthy' ? 'success' : 
                       database.health_status === 'warning' ? 'warning' : 'error'}
                text={
                  <span style={{ 
                    fontSize: '11px',
                    color: healthConfig.color,
                    fontWeight: 500
                  }}>
                    {healthConfig.text}
                  </span>
                }
              />
            </div>
            
            <div style={{ 
              fontSize: '12px', 
              color: '#8c8c8c',
              marginBottom: 8,
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}>
              <span>{typeConfig.icon} {typeConfig.name}</span>
              <span style={{ color: '#d9d9d9' }}>•</span>
              <span>{envConfig.icon} {envConfig.name}</span>
            </div>
          </div>
        </div>

        {/* 快速操作按钮 */}
        {showActions && (
          <Space size={4}>
            <Tooltip title="配置管理">
              <Button
                type="text"
                size="small"
                icon={<SettingOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  onConfig?.(database);
                }}
                style={{ 
                  color: '#8c8c8c',
                  border: 'none',
                  boxShadow: 'none'
                }}
              />
            </Tooltip>
            <Tooltip title="性能监控">
              <Button
                type="text"
                size="small"
                icon={<BarChartOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  onMonitor?.(database);
                }}
                style={{ 
                  color: '#8c8c8c',
                  border: 'none',
                  boxShadow: 'none'
                }}
              />
            </Tooltip>
            <Tooltip title="工具集">
              <Button
                type="text"
                size="small"
                icon={<ToolOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  onTools?.(database);
                }}
                style={{ 
                  color: '#8c8c8c',
                  border: 'none',
                  boxShadow: 'none'
                }}
              />
            </Tooltip>
          </Space>
        )}
      </div>

      {/* 关键性能指标 - 突出显示 */}
      <div style={{ 
        marginBottom: 12,
        padding: '12px',
        background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)',
        borderRadius: '8px',
        border: '1px solid #e9ecef'
      }}>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: '12px',
          textAlign: 'center'
        }}>
          <div>
            <div style={{ 
              fontSize: '18px', 
              fontWeight: 'bold',
              color: getPerformanceColor(performanceData.cpuUsage),
              marginBottom: '2px'
            }}>
              {performanceData.cpuUsage}%
            </div>
            <div style={{ fontSize: '10px', color: '#666', textTransform: 'uppercase' }}>
              CPU
            </div>
          </div>
          <div>
            <div style={{ 
              fontSize: '18px', 
              fontWeight: 'bold',
              color: getPerformanceColor(performanceData.memoryUsage),
              marginBottom: '2px'
            }}>
              {performanceData.memoryUsage}%
            </div>
            <div style={{ fontSize: '10px', color: '#666', textTransform: 'uppercase' }}>
              内存
            </div>
          </div>
          <div>
            <div style={{ 
              fontSize: '18px', 
              fontWeight: 'bold',
              color: getPerformanceColor(performanceData.connectionCount, { warning: 150, critical: 180 }),
              marginBottom: '2px'
            }}>
              {performanceData.connectionCount}
            </div>
            <div style={{ fontSize: '10px', color: '#666', textTransform: 'uppercase' }}>
              连接数
            </div>
          </div>
        </div>
      </div>

      {/* 底部信息 - 简化版 */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        paddingTop: 8,
        borderTop: '1px solid #f0f0f0',
        fontSize: '11px',
        color: '#8c8c8c'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <ClockCircleOutlined style={{ fontSize: '10px' }} />
          <span>{formatLastCheck(performanceData.lastCheck)}</span>
        </div>
        
        {showActions && (
          <Space size={4}>
            <Tooltip title="配置">
              <Button
                type="text"
                size="small"
                icon={<SettingOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  onConfig?.(database);
                }}
                style={{ fontSize: '12px', padding: '2px 4px' }}
              />
            </Tooltip>
            <Tooltip title="监控">
              <Button
                type="text"
                size="small"
                icon={<BarChartOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  onMonitor?.(database);
                }}
                style={{ fontSize: '12px', padding: '2px 4px' }}
              />
            </Tooltip>
          </Space>
        )}
      </div>

      {/* 悬停效果样式 */}
      <style jsx>{`
        .database-instance-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(0,0,0,0.12);
          border-color: ${typeConfig.color}40;
        }
      `}</style>
    </Card>
  );
};

export default DatabaseInstanceCard;
