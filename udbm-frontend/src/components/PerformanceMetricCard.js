import React from 'react';
import { Card, Statistic, Progress, Space, Typography } from 'antd';
import { 
  ArrowUpOutlined, 
  ArrowDownOutlined,
  MinusOutlined 
} from '@ant-design/icons';
import DataSourceIndicator from './DataSourceIndicator';

const { Text } = Typography;

const PerformanceMetricCard = ({
  title,
  value,
  unit = '',
  precision = 2,
  trend = null, // 'up', 'down', 'stable'
  trendValue = null,
  progressValue = null,
  progressMax = 100,
  status = 'normal', // 'normal', 'warning', 'critical'
  dataSource = 'unknown',
  loading = false,
  style = {},
  size = 'default'
}) => {
  // 状态颜色配置
  const statusColors = {
    normal: '#52c41a',
    warning: '#faad14', 
    critical: '#f5222d'
  };

  // 趋势图标
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <ArrowUpOutlined style={{ color: '#f5222d' }} />;
      case 'down':
        return <ArrowDownOutlined style={{ color: '#52c41a' }} />;
      case 'stable':
        return <MinusOutlined style={{ color: '#1890ff' }} />;
      default:
        return null;
    }
  };

  // 获取进度条颜色
  const getProgressColor = () => {
    if (progressValue >= 90) return '#f5222d';
    if (progressValue >= 70) return '#faad14';
    return '#52c41a';
  };

  const cardSize = size === 'small' ? 'small' : 'default';

  return (
    <Card 
      size={cardSize}
      loading={loading}
      style={style}
      extra={
        <DataSourceIndicator 
          source={dataSource}
          size="small"
          showText={false}
        />
      }
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        <Statistic
          title={title}
          value={value}
          precision={precision}
          suffix={unit}
          valueStyle={{ 
            color: statusColors[status],
            fontSize: size === 'small' ? '20px' : '24px'
          }}
        />
        
        {/* 趋势信息 */}
        {trend && trendValue && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {getTrendIcon()}
            <Text 
              type={trend === 'up' ? 'danger' : trend === 'down' ? 'success' : 'secondary'}
              style={{ fontSize: '12px' }}
            >
              {trendValue}
            </Text>
          </div>
        )}

        {/* 进度条 */}
        {progressValue !== null && (
          <Progress
            percent={progressValue}
            size="small"
            strokeColor={getProgressColor()}
            format={(percent) => `${percent.toFixed(2)}%`}
            style={{ margin: 0 }}
          />
        )}
      </Space>
    </Card>
  );
};

export default PerformanceMetricCard;
