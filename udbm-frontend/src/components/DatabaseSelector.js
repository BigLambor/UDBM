import React, { useState, useEffect } from 'react';
import { Select, Space, Tag, Tooltip, Badge } from 'antd';
import {
  DatabaseOutlined,
  ThunderboltOutlined,
  FilterOutlined
} from '@ant-design/icons';

const { Option } = Select;

// 数据库类型图标和颜色配置
const DATABASE_TYPES = {
  postgresql: {
    icon: '🐘',
    color: '#336791',
    name: 'PostgreSQL'
  },
  mysql: {
    icon: '🐬',
    color: '#4479A1',
    name: 'MySQL'
  },
  oracle: {
    icon: '🔶',
    color: '#F80000',
    name: 'Oracle'
  },
  sqlserver: {
    icon: '⚡',
    color: '#CC2927',
    name: 'SQL Server'
  },
  mongodb: {
    icon: '🍃',
    color: '#47A248',
    name: 'MongoDB'
  }
};

const DatabaseSelector = ({ 
  databases = [], 
  selectedDatabase, 
  onDatabaseChange,
  selectedType,
  onTypeChange,
  showTypeFilter = true,
  showStats = true,
  loading = false,
  style = {}
}) => {
  const [filteredDatabases, setFilteredDatabases] = useState(databases);

  // 根据类型过滤数据库
  useEffect(() => {
    if (selectedType && selectedType !== 'all') {
      setFilteredDatabases(databases.filter(db => db.type === selectedType));
    } else {
      setFilteredDatabases(databases);
    }
  }, [databases, selectedType]);

  // 获取数据库类型统计
  const getTypeStats = () => {
    const stats = {};
    databases.forEach(db => {
      stats[db.type] = (stats[db.type] || 0) + 1;
    });
    return stats;
  };

  const typeStats = getTypeStats();

  // 渲染数据库选项
  const renderDatabaseOption = (database) => {
    const typeConfig = DATABASE_TYPES[database.type] || {
      icon: '🗃️',
      color: '#666',
      name: database.type ? database.type.toUpperCase() : '未知类型'
    };

    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ marginRight: 8, fontSize: '16px' }}>
            {typeConfig.icon}
          </span>
          <div>
            <div style={{ fontWeight: 500 }}>{database.name}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              {typeConfig.name} • {database.host}:{database.port}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {database.status === 'active' ? (
            <Badge status="success" />
          ) : (
            <Badge status="error" />
          )}
        </div>
      </div>
    );
  };

  // 渲染类型过滤选项
  const renderTypeOption = (type) => {
    const typeConfig = DATABASE_TYPES[type] || {
      icon: '🗃️',
      color: '#666',
      name: type ? type.toUpperCase() : '未知类型'
    };
    const count = typeStats[type] || 0;

    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ marginRight: 8, fontSize: '16px' }}>
            {typeConfig.icon}
          </span>
          <span>{typeConfig.name}</span>
        </div>
        <Badge count={count} size="small" />
      </div>
    );
  };

  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: '16px',
      padding: '12px 16px',
      backgroundColor: '#fafafa',
      borderRadius: '8px',
      border: '1px solid #f0f0f0',
      ...style 
    }}>
      {/* 数据库实例选择器 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <DatabaseOutlined style={{ color: '#1890ff' }} />
        <span style={{ fontWeight: 500, color: '#666' }}>数据库实例:</span>
        <Select
          value={selectedDatabase?.id}
          onChange={(value) => {
            const database = databases.find(db => db.id === value);
            onDatabaseChange?.(database);
          }}
          placeholder="选择数据库实例"
          style={{ minWidth: 280 }}
          loading={loading}
          showSearch
          filterOption={(input, option) => {
            const database = databases.find(db => db.id === option.value);
            return database?.name.toLowerCase().includes(input.toLowerCase()) ||
                   database?.host.toLowerCase().includes(input.toLowerCase());
          }}
          optionLabelProp="label"
        >
          {filteredDatabases.map(database => (
            <Option 
              key={database.id} 
              value={database.id}
              label={`${DATABASE_TYPES[database.type]?.icon || '🗃️'} ${database.name}`}
            >
              {renderDatabaseOption(database)}
            </Option>
          ))}
        </Select>
      </div>

      {/* 数据库类型过滤器 */}
      {showTypeFilter && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FilterOutlined style={{ color: '#52c41a' }} />
          <span style={{ fontWeight: 500, color: '#666' }}>类型筛选:</span>
          <Select
            value={selectedType}
            onChange={onTypeChange}
            placeholder="所有类型"
            style={{ minWidth: 150 }}
            allowClear
          >
            <Option value="all">
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <span style={{ marginRight: 8 }}>🗂️</span>
                <span>所有类型</span>
                <Badge count={databases.length} size="small" style={{ marginLeft: 8 }} />
              </div>
            </Option>
            {Object.keys(typeStats).map(type => (
              <Option key={type} value={type}>
                {renderTypeOption(type)}
              </Option>
            ))}
          </Select>
        </div>
      )}

      {/* 当前选择信息 */}
      {selectedDatabase && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ThunderboltOutlined style={{ color: '#fa8c16' }} />
          <Tag 
            color={DATABASE_TYPES[selectedDatabase.type]?.color || '#666'}
            style={{ margin: 0 }}
          >
            {DATABASE_TYPES[selectedDatabase.type]?.name || (selectedDatabase.type ? selectedDatabase.type.toUpperCase() : '未知类型')}
          </Tag>
          {selectedDatabase.status === 'active' ? (
            <Tag color="success" style={{ margin: 0 }}>活跃</Tag>
          ) : (
            <Tag color="error" style={{ margin: 0 }}>非活跃</Tag>
          )}
        </div>
      )}

      {/* 统计信息 */}
      {showStats && databases.length > 0 && (
        <div style={{ 
          marginLeft: 'auto',
          fontSize: '12px', 
          color: '#666',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <Tooltip title="数据库实例统计">
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <DatabaseOutlined />
              <span>总计: {databases.length}</span>
            </div>
          </Tooltip>
          <Tooltip title="活跃实例数量">
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Badge status="success" />
              <span>活跃: {databases.filter(db => db.status === 'active').length}</span>
            </div>
          </Tooltip>
        </div>
      )}
    </div>
  );
};

export default DatabaseSelector;
