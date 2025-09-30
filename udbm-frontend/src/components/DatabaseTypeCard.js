import React from 'react';
import { Card, Row, Col, Statistic, Progress, Tag, Space, Tooltip, Badge } from 'antd';
import { 
  DatabaseOutlined, 
  CheckCircleOutlined, 
  WarningOutlined, 
  CloseCircleOutlined,
  EyeOutlined,
  SettingOutlined,
  BarChartOutlined
} from '@ant-design/icons';

// 数据库类型配置 - 参考业界标准
const DATABASE_TYPE_CONFIG = {
  postgresql: {
    name: 'PostgreSQL',
    icon: '🐘',
    color: '#336791',
    gradient: 'linear-gradient(135deg, #336791 0%, #4a7c95 100%)',
    description: '开源关系型数据库',
    features: ['ACID', 'JSON支持', '全文搜索']
  },
  mysql: {
    name: 'MySQL',
    icon: '🐬',
    color: '#4479A1',
    gradient: 'linear-gradient(135deg, #4479A1 0%, #5a8bb1 100%)',
    description: '流行的关系型数据库',
    features: ['高性能', '易用性', '社区支持']
  },
  oceanbase: {
    name: 'OceanBase',
    icon: '🌊',
    color: '#3b82f6',
    gradient: 'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)',
    description: '分布式云原生数据库',
    features: ['高可用', '水平扩展', 'MySQL/Oracle语法兼容']
  },
  mongodb: {
    name: 'MongoDB',
    icon: '🍃',
    color: '#47A248',
    gradient: 'linear-gradient(135deg, #47A248 0%, #5cb85c 100%)',
    description: '文档型NoSQL数据库',
    features: ['文档存储', '水平扩展', '灵活模式']
  },
  redis: {
    name: 'Redis',
    icon: '⚡',
    color: '#DC382D',
    gradient: 'linear-gradient(135deg, #DC382D 0%, #e74c3c 100%)',
    description: '内存键值存储',
    features: ['高性能', '数据结构', '持久化']
  },
  oracle: {
    name: 'Oracle',
    icon: '🔶',
    color: '#F80000',
    gradient: 'linear-gradient(135deg, #F80000 0%, #ff1a1a 100%)',
    description: '企业级数据库',
    features: ['企业级', '高可用', '安全性']
  },
  sqlserver: {
    name: 'SQL Server',
    icon: '🏢',
    color: '#CC2927',
    gradient: 'linear-gradient(135deg, #CC2927 0%, #d63031 100%)',
    description: '微软数据库',
    features: ['Windows集成', '商业智能', '云原生']
  }
};

const DatabaseTypeCard = ({ 
  type, 
  stats, 
  onClick, 
  isSelected = false,
  showActions = true 
}) => {
  const config = DATABASE_TYPE_CONFIG[type] || DATABASE_TYPE_CONFIG.postgresql;
  const healthRatio = stats.total > 0 ? (stats.healthy / stats.total) * 100 : 0;
  
  // 健康状态颜色 - 参考业界标准
  const getHealthColor = (ratio) => {
    if (ratio >= 90) return '#52c41a';
    if (ratio >= 70) return '#faad14';
    if (ratio >= 50) return '#fa8c16';
    return '#f5222d';
  };

  const getHealthStatus = (ratio) => {
    if (ratio >= 90) return 'excellent';
    if (ratio >= 70) return 'good';
    if (ratio >= 50) return 'warning';
    return 'critical';
  };

  const healthStatus = getHealthStatus(healthRatio);
  const healthColor = getHealthColor(healthRatio);

  return (
    <Card
      hoverable
      onClick={onClick}
      style={{
        height: '100%',
        border: isSelected ? `2px solid ${config.color}` : '1px solid #f0f0f0',
        borderRadius: '12px',
        boxShadow: isSelected 
          ? `0 8px 24px rgba(0,0,0,0.12), 0 0 0 1px ${config.color}20`
          : '0 2px 8px rgba(0,0,0,0.06)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        cursor: 'pointer',
        position: 'relative',
        overflow: 'hidden'
      }}
      bodyStyle={{ padding: '20px' }}
    >
      {/* 选中状态指示器 */}
      {isSelected && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '4px',
            background: config.gradient,
            borderRadius: '12px 12px 0 0'
          }}
        />
      )}

      {/* 头部区域 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div
              style={{
                fontSize: '32px',
                marginRight: 12,
                filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))'
              }}
            >
              {config.icon}
            </div>
            <div>
              <h3 style={{ 
                margin: 0, 
                fontSize: '18px', 
                fontWeight: 600,
                color: '#262626'
              }}>
                {config.name}
              </h3>
              <p style={{ 
                margin: 0, 
                fontSize: '12px', 
                color: '#8c8c8c',
                lineHeight: 1.4
              }}>
                {config.description}
              </p>
            </div>
          </div>
          
          {/* 健康状态指示器 */}
          <div style={{ textAlign: 'right' }}>
            <Badge
              status={healthStatus === 'excellent' ? 'success' : 
                     healthStatus === 'good' ? 'processing' : 
                     healthStatus === 'warning' ? 'warning' : 'error'}
              text={
                <span style={{ 
                  fontSize: '12px', 
                  fontWeight: 500,
                  color: healthColor
                }}>
                  {(healthRatio || 0).toFixed(1)}%
                </span>
              }
            />
          </div>
        </div>

        {/* 健康度进度条 */}
        <Progress
          percent={healthRatio}
          strokeColor={{
            '0%': healthColor,
            '100%': healthColor,
          }}
          trailColor="#f0f0f0"
          strokeWidth={6}
          showInfo={false}
          style={{ marginBottom: 12 }}
        />
      </div>

      {/* 统计信息 */}
      <Row gutter={[8, 8]} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ 
              fontSize: '20px', 
              fontWeight: 600, 
              color: config.color,
              lineHeight: 1.2
            }}>
              {stats.total}
            </div>
            <div style={{ 
              fontSize: '11px', 
              color: '#8c8c8c',
              marginTop: 2
            }}>
              总实例
            </div>
          </div>
        </Col>
        <Col span={8}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ 
              fontSize: '20px', 
              fontWeight: 600, 
              color: '#52c41a',
              lineHeight: 1.2
            }}>
              {stats.healthy}
            </div>
            <div style={{ 
              fontSize: '11px', 
              color: '#8c8c8c',
              marginTop: 2
            }}>
              健康
            </div>
          </div>
        </Col>
        <Col span={8}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ 
              fontSize: '20px', 
              fontWeight: 600, 
              color: '#faad14',
              lineHeight: 1.2
            }}>
              {stats.warning + stats.critical}
            </div>
            <div style={{ 
              fontSize: '11px', 
              color: '#8c8c8c',
              marginTop: 2
            }}>
              异常
            </div>
          </div>
        </Col>
      </Row>

      {/* 特性标签 */}
      <div style={{ marginBottom: 16 }}>
        <Space wrap size={[4, 4]}>
          {config.features.map((feature, index) => (
            <Tag
              key={index}
              size="small"
              style={{
                background: `${config.color}10`,
                color: config.color,
                border: `1px solid ${config.color}30`,
                borderRadius: '4px',
                fontSize: '10px',
                fontWeight: 500
              }}
            >
              {feature}
            </Tag>
          ))}
        </Space>
      </div>

      {/* 操作按钮 */}
      {showActions && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between',
          paddingTop: 12,
          borderTop: '1px solid #f0f0f0'
        }}>
          <Tooltip title="查看实例">
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '6px 12px',
                borderRadius: '6px',
                background: '#f8f9fa',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontSize: '12px',
                color: '#666'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#e9ecef';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#f8f9fa';
              }}
            >
              <EyeOutlined style={{ marginRight: 4, fontSize: '12px' }} />
              查看
            </div>
          </Tooltip>
          
          <Tooltip title="性能监控">
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '6px 12px',
                borderRadius: '6px',
                background: '#f8f9fa',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontSize: '12px',
                color: '#666'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#e9ecef';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#f8f9fa';
              }}
            >
              <BarChartOutlined style={{ marginRight: 4, fontSize: '12px' }} />
              监控
            </div>
          </Tooltip>
          
          <Tooltip title="配置管理">
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '6px 12px',
                borderRadius: '6px',
                background: '#f8f9fa',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontSize: '12px',
                color: '#666'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#e9ecef';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#f8f9fa';
              }}
            >
              <SettingOutlined style={{ marginRight: 4, fontSize: '12px' }} />
              配置
            </div>
          </Tooltip>
        </div>
      )}
    </Card>
  );
};

export default DatabaseTypeCard;
