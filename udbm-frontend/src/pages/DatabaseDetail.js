import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Card, Button, Descriptions, Tag, Space, message, Spin,
  Statistic, Row, Col, Alert, Tabs
} from 'antd';
import {
  SyncOutlined, CheckCircleOutlined, CloseCircleOutlined,
  DatabaseOutlined, ClockCircleOutlined, UserOutlined
} from '@ant-design/icons';

import { databaseAPI } from '../services/api';

const { TabPane } = Tabs;

const DatabaseDetail = () => {
  const { id } = useParams();
  const [database, setDatabase] = useState(null);
  const [loading, setLoading] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionResult, setConnectionResult] = useState(null);

  // 获取数据库详情
  const fetchDatabase = async () => {
    setLoading(true);
    try {
      const data = await databaseAPI.getDatabase(id);
      setDatabase(data);
    } catch (error) {
      message.error('获取数据库详情失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchDatabase();
    }
  }, [id]);

  // 测试数据库连接
  const testConnection = async () => {
    setTestingConnection(true);
    setConnectionResult(null);
    try {
      const result = await databaseAPI.testConnection(id);
      setConnectionResult(result);
      if (result.success) {
        message.success(`连接测试成功 (响应时间: ${result.response_time.toFixed(3)}s)`);
        // 重新获取数据库信息
        fetchDatabase();
      } else {
        message.error(`连接测试失败: ${result.message}`);
      }
    } catch (error) {
      setConnectionResult({ success: false, message: error.message });
      message.error('连接测试失败: ' + error.message);
    } finally {
      setTestingConnection(false);
    }
  };

  // 获取状态标签
  const getStatusTag = (status) => {
    const statusConfig = {
      active: { color: 'green', text: '活跃' },
      inactive: { color: 'orange', text: '停用' },
      maintenance: { color: 'blue', text: '维护中' },
      error: { color: 'red', text: '错误' }
    };
    const config = statusConfig[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 获取健康状态标签
  const getHealthStatusTag = (healthStatus) => {
    const healthConfig = {
      healthy: { color: 'green', text: '健康', icon: CheckCircleOutlined },
      warning: { color: 'orange', text: '警告', icon: ClockCircleOutlined },
      critical: { color: 'red', text: '严重', icon: CloseCircleOutlined },
      unknown: { color: 'default', text: '未知', icon: ClockCircleOutlined }
    };
    const config = healthConfig[healthStatus] || { color: 'default', text: healthStatus };
    const IconComponent = config.icon;
    return (
      <Tag color={config.color}>
        <IconComponent style={{ marginRight: 4 }} />
        {config.text}
      </Tag>
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
    return types[typeId] || `类型${typeId}`;
  };

  if (loading && !database) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!database) {
    return (
      <Alert
        message="数据库不存在"
        description="未找到指定的数据库实例信息"
        type="error"
        showIcon
      />
    );
  }

  return (
    <div>
      <Card
        title={
          <Space>
            <DatabaseOutlined />
            {database.name}
          </Space>
        }
        extra={
          <Button
            type="primary"
            icon={<SyncOutlined spin={testingConnection} />}
            onClick={testConnection}
            loading={testingConnection}
          >
            测试连接
          </Button>
        }
      >
        <Tabs defaultActiveKey="1">
          <TabPane tab="基本信息" key="1">
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={6}>
                <Statistic
                  title="状态"
                  value={database.status}
                  valueStyle={{ color: database.status === 'active' ? '#3f8600' : '#cf1322' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="健康状态"
                  value={getHealthStatusTag(database.health_status)}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="环境"
                  value={database.environment}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="类型"
                  value={getDatabaseTypeName(database.type_id)}
                />
              </Col>
            </Row>

            <Descriptions bordered column={2}>
              <Descriptions.Item label="实例名称">{database.name}</Descriptions.Item>
              <Descriptions.Item label="数据库类型">{getDatabaseTypeName(database.type_id)}</Descriptions.Item>
              <Descriptions.Item label="主机地址">{database.host}</Descriptions.Item>
              <Descriptions.Item label="端口号">{database.port}</Descriptions.Item>
              <Descriptions.Item label="数据库名">{database.database_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="用户名">{database.username || '-'}</Descriptions.Item>
              <Descriptions.Item label="环境">{database.environment}</Descriptions.Item>
              <Descriptions.Item label="状态">{getStatusTag(database.status)}</Descriptions.Item>
              <Descriptions.Item label="健康状态">{getHealthStatusTag(database.health_status)}</Descriptions.Item>
              <Descriptions.Item label="最后健康检查">
                {database.last_health_check ?
                  new Date(database.last_health_check).toLocaleString() :
                  '-'
                }
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {new Date(database.created_at).toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {new Date(database.updated_at).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>
          </TabPane>

          <TabPane tab="连接信息" key="2">
            <Card title="连接详情" size="small">
              <Descriptions column={1}>
                <Descriptions.Item label="连接字符串">
                  <code>
                    {database.type_id === 1 ? 'postgresql://' :
                     database.type_id === 2 ? 'mysql://' :
                     database.type_id === 3 ? 'mongodb://' :
                     database.type_id === 4 ? 'redis://' :
                     database.type_id === 5 ? 'mysql://' :  // OceanBase使用MySQL协议
                     database.type_id === 6 ? 'oracle://' : ''}
                    {database.username ? `${database.username}@` : ''}
                    {database.host}:{database.port}
                    {database.database_name ? `/${database.database_name}` : ''}
                  </code>
                </Descriptions.Item>
                <Descriptions.Item label="JDBC URL">
                  <code>
                    {database.type_id === 1 ? 'jdbc:postgresql://' :
                     database.type_id === 2 ? 'jdbc:mysql://' :
                     database.type_id === 5 ? 'jdbc:mysql://' :  // OceanBase使用MySQL协议
                     database.type_id === 6 ? 'jdbc:oracle:thin:@' : 'jdbc:'}
                    {database.host}:{database.port}
                    {database.database_name ? `/${database.database_name}` : ''}
                  </code>
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {connectionResult && (
              <Card title="连接测试结果" size="small" style={{ marginTop: 16 }}>
                <Alert
                  message={connectionResult.success ? "连接成功" : "连接失败"}
                  description={
                    <div>
                      <p>响应时间: {connectionResult.response_time.toFixed(3)}s</p>
                      {connectionResult.error_details && (
                        <p>错误详情: {connectionResult.error_details}</p>
                      )}
                      {connectionResult.database_info && (
                        <div>
                          <p>数据库信息:</p>
                          <ul>
                            <li>版本: {connectionResult.database_info.version || '未知'}</li>
                            <li>数据库大小: {connectionResult.database_info.database_size || '未知'}</li>
                            <li>活跃连接数: {connectionResult.database_info.active_connections || '未知'}</li>
                            <li>表数量: {connectionResult.database_info.table_count || '未知'}</li>
                          </ul>
                        </div>
                      )}
                    </div>
                  }
                  type={connectionResult.success ? "success" : "error"}
                  showIcon
                />
              </Card>
            )}
          </TabPane>

          <TabPane tab="监控信息" key="3">
            <Alert
              message="监控功能开发中"
              description="该功能将在后续版本中提供，包括实时指标监控、性能分析等功能。"
              type="info"
              showIcon
            />
          </TabPane>

          <TabPane tab="备份恢复" key="4">
            <Alert
              message="备份恢复功能开发中"
              description="该功能将在后续版本中提供，包括自动备份、手动备份、数据恢复等功能。"
              type="info"
              showIcon
            />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default DatabaseDetail;
