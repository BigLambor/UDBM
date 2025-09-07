import React from 'react';
import { Tag, Tooltip, Badge } from 'antd';
import { 
  DatabaseOutlined, 
  ExperimentOutlined, 
  CheckCircleOutlined,
  ExclamationCircleOutlined 
} from '@ant-design/icons';

const DataSourceIndicator = ({ 
  source = 'unknown', 
  size = 'default',
  showText = true,
  style = {}
}) => {
  // 数据源配置
  const sourceConfig = {
    real_data: {
      color: 'success',
      icon: <DatabaseOutlined />,
      text: '真实数据',
      description: '来自PostgreSQL实例的真实性能数据'
    },
    mock_data: {
      color: 'warning', 
      icon: <ExperimentOutlined />,
      text: '演示数据',
      description: '用于演示的模拟数据，基于真实场景设计'
    },
    mixed: {
      color: 'processing',
      icon: <Badge status="processing" />,
      text: '混合数据',
      description: '部分真实数据，部分演示数据'
    },
    unknown: {
      color: 'default',
      icon: <ExclamationCircleOutlined />,
      text: '未知来源',
      description: '数据来源未明确标识'
    }
  };

  const config = sourceConfig[source] || sourceConfig.unknown;

  if (!showText) {
    return (
      <Tooltip title={config.description}>
        <Tag 
          color={config.color} 
          size={size}
          icon={config.icon}
          style={style}
        />
      </Tooltip>
    );
  }

  return (
    <Tooltip title={config.description}>
      <Tag 
        color={config.color} 
        size={size}
        icon={config.icon}
        style={style}
      >
        {config.text}
      </Tag>
    </Tooltip>
  );
};

export default DataSourceIndicator;
