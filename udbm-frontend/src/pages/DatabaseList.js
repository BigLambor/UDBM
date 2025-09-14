import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Card, Button, Table, Tag, Space, Modal, Form, Input, Select,
  message, Tooltip, Popconfirm, List, Avatar, Row, Col, Grid
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, SyncOutlined,
  DatabaseOutlined, CheckCircleOutlined, CloseCircleOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';

import { databaseAPI } from '../services/api';

const { Option } = Select;

const DatabaseList = () => {
  const [databases, setDatabases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingDatabase, setEditingDatabase] = useState(null);
  const [form] = Form.useForm();
  const [testingConnection, setTestingConnection] = useState(null);
  const [isMobile, setIsMobile] = useState(false);
  const navigate = useNavigate();

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

  // 获取数据库列表
  const fetchDatabases = async () => {
    setLoading(true);
    try {
      const response = await databaseAPI.getDatabases();
      // 后端返回格式: 直接返回数据库实例数组
      const data = Array.isArray(response) ? response : [];
      setDatabases(data);
    } catch (error) {
      console.error('获取数据库列表失败:', error);
      message.error('获取数据库列表失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatabases();
  }, []);

  // 打开创建/编辑模态框
  const openModal = (database = null) => {
    setEditingDatabase(database);
    if (database) {
      form.setFieldsValue(database);
    } else {
      form.resetFields();
      form.setFieldsValue({
        type_id: 1, // 默认PostgreSQL
        environment: 'development',
        status: 'active'
      });
    }
    setModalVisible(true);
  };

  // 关闭模态框
  const closeModal = () => {
    setModalVisible(false);
    setEditingDatabase(null);
    form.resetFields();
  };

  // 提交表单
  const handleSubmit = async (values) => {
    try {
      if (editingDatabase) {
        await databaseAPI.updateDatabase(editingDatabase.id, values);
        message.success('数据库实例更新成功');
      } else {
        await databaseAPI.createDatabase(values);
        message.success('数据库实例创建成功');
      }
      closeModal();
      fetchDatabases();
    } catch (error) {
      message.error('操作失败: ' + error.message);
    }
  };

  // 删除数据库实例
  const handleDelete = async (id) => {
    try {
      await databaseAPI.deleteDatabase(id);
      message.success('数据库实例删除成功');
      fetchDatabases();
    } catch (error) {
      message.error('删除失败: ' + error.message);
    }
  };

  // 测试数据库连接
  const testConnection = async (database) => {
    setTestingConnection(database.id);
    try {
      const result = await databaseAPI.testConnection(database.id);
      if (result.success) {
        message.success(`连接测试成功 (响应时间: ${result.response_time.toFixed(3)}s)`);
        // 更新数据库状态
        fetchDatabases();
      } else {
        message.error(`连接测试失败: ${result.message}`);
      }
    } catch (error) {
      message.error('连接测试失败: ' + error.message);
    } finally {
      setTestingConnection(null);
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
      warning: { color: 'orange', text: '警告', icon: QuestionCircleOutlined },
      critical: { color: 'red', text: '严重', icon: CloseCircleOutlined },
      unknown: { color: 'default', text: '未知', icon: QuestionCircleOutlined }
    };
    const config = healthConfig[healthStatus] || { color: 'default', text: healthStatus || '未知', icon: QuestionCircleOutlined };
    const IconComponent = config.icon || QuestionCircleOutlined;
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
      5: 'SQLite'
    };
    return types[typeId] || `类型${typeId}`;
  };

  // 表格列定义
  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Link to={`/databases/${record.id}`}>
          <DatabaseOutlined style={{ marginRight: 8 }} />
          {text}
        </Link>
      )
    },
    {
      title: '类型',
      dataIndex: 'type_id',
      key: 'type_id',
      render: (typeId) => getDatabaseTypeName(typeId)
    },
    {
      title: '主机:端口',
      key: 'host_port',
      render: (_, record) => `${record.host}:${record.port}`
    },
    {
      title: '数据库',
      dataIndex: 'database_name',
      key: 'database_name',
      render: (text) => text || '-'
    },
    {
      title: '环境',
      dataIndex: 'environment',
      key: 'environment',
      render: (env) => <Tag color="blue">{env}</Tag>
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: getStatusTag
    },
    {
      title: '健康状态',
      dataIndex: 'health_status',
      key: 'health_status',
      render: getHealthStatusTag
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="测试连接">
            <Button
              type="text"
              icon={<SyncOutlined spin={testingConnection === record.id} />}
              onClick={() => testConnection(record)}
              loading={testingConnection === record.id}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => openModal(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个数据库实例吗?"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  console.log('开始渲染DatabaseList组件');

  // 如果有错误，先显示简单的内容进行调试
  if (loading && databases.length === 0) {
    return (
      <div>
        <h2>数据库实例管理</h2>
        <p>正在加载数据库列表...</p>
      </div>
    );
  }

  // 移动端卡片布局
  const renderMobileView = () => (
    <div>
      <div style={{ marginBottom: 16, textAlign: 'center' }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => openModal()}
          size="large"
          style={{ width: isMobile ? '100%' : 'auto' }}
        >
          添加数据库实例
        </Button>
      </div>

      <List
        loading={loading}
        dataSource={databases}
        renderItem={database => (
          <List.Item
            style={{ padding: '8px 0' }}
            actions={[
              <Tooltip title="测试连接">
                <Button
                  type="text"
                  icon={<SyncOutlined spin={testingConnection === database.id} />}
                  onClick={() => testConnection(database)}
                  loading={testingConnection === database.id}
                />
              </Tooltip>,
              <Tooltip title="编辑">
                <Button
                  type="text"
                  icon={<EditOutlined />}
                  onClick={() => openModal(database)}
                />
              </Tooltip>,
              <Popconfirm
                title="确定要删除这个数据库实例吗?"
                onConfirm={() => handleDelete(database.id)}
                okText="确定"
                cancelText="取消"
              >
                <Button type="text" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            ]}
          >
            <List.Item.Meta
              avatar={
                <Avatar
                  icon={<DatabaseOutlined />}
                  style={{ backgroundColor: '#1890ff' }}
                  size="large"
                />
              }
              title={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>{database.name}</span>
                  {getHealthStatusTag(database.health_status)}
                </div>
              }
              description={
                <div>
                  <div style={{ marginBottom: '4px' }}>
                    <strong>类型:</strong> {getDatabaseTypeName(database.type_id)} |
                    <strong>环境:</strong> {database.environment}
                  </div>
                  <div style={{ color: '#666', fontSize: '12px' }}>
                    {database.host}:{database.port}
                    {database.database_name && ` / ${database.database_name}`}
                  </div>
                </div>
              }
              onClick={() => navigate(`/databases/${database.id}`)}
              style={{ cursor: 'pointer' }}
            />
          </List.Item>
        )}
        style={{ cursor: 'pointer' }}
      />
    </div>
  );

  // 桌面端表格布局
  const renderDesktopView = () => (
    <Table
      columns={columns}
      dataSource={databases}
      rowKey="id"
      loading={loading}
      pagination={{
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
      }}
    />
  );

  return (
    <div>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
            <span>数据库实例管理</span>
            {!isMobile && (
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => openModal()}
              >
                添加数据库
              </Button>
            )}
          </div>
        }
        extra={isMobile ? (
          <div style={{ marginTop: 8, width: '100%' }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => openModal()}
              block
            >
              添加数据库
            </Button>
          </div>
        ) : null}
      >
        {isMobile ? renderMobileView() : renderDesktopView()}
      </Card>

      {/* 创建/编辑数据库实例模态框 */}
      <Modal
        title={editingDatabase ? "编辑数据库实例" : "添加数据库实例"}
        open={modalVisible}
        onCancel={closeModal}
        footer={null}
        width={isMobile ? '95%' : 600}
        style={isMobile ? { top: 20, maxWidth: 'none' } : {}}
        bodyStyle={isMobile ? { padding: '16px' } : {}}
        destroyOnClose
      >
        <Form
          form={form}
          layout={isMobile ? "vertical" : "vertical"}
          onFinish={handleSubmit}
          size={isMobile ? "large" : "middle"}
        >
          <Form.Item
            name="name"
            label="实例名称"
            rules={[{ required: true, message: '请输入实例名称' }]}
          >
            <Input placeholder="例如: 生产环境主库" />
          </Form.Item>

          <Form.Item
            name="type_id"
            label="数据库类型"
            rules={[{ required: true, message: '请选择数据库类型' }]}
          >
            <Select placeholder="选择数据库类型">
              <Option value={1}>PostgreSQL</Option>
              <Option value={2}>MySQL</Option>
              <Option value={3}>MongoDB</Option>
              <Option value={4}>Redis</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="host"
            label="主机地址"
            rules={[{ required: true, message: '请输入主机地址' }]}
          >
            <Input placeholder="例如: localhost 或 192.168.1.100" />
          </Form.Item>

          <Form.Item
            name="port"
            label="端口号"
            rules={[{ required: true, message: '请输入端口号' }]}
          >
            <Input type="number" placeholder="例如: 5432" />
          </Form.Item>

          <Form.Item
            name="database_name"
            label="数据库名"
          >
            <Input placeholder="数据库名称（可选）" />
          </Form.Item>

          <Form.Item
            name="username"
            label="用户名"
          >
            <Input placeholder="数据库用户名（可选）" />
          </Form.Item>

          <Form.Item
            name="password_encrypted"
            label="密码"
          >
            <Input.Password placeholder="数据库密码（可选）" />
          </Form.Item>

          <Form.Item
            name="environment"
            label="环境"
            rules={[{ required: true, message: '请选择环境' }]}
          >
            <Select>
              <Option value="development">开发环境</Option>
              <Option value="staging">测试环境</Option>
              <Option value="production">生产环境</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="status"
            label="状态"
            rules={[{ required: true, message: '请选择状态' }]}
          >
            <Select>
              <Option value="active">活跃</Option>
              <Option value="inactive">停用</Option>
              <Option value="maintenance">维护中</Option>
            </Select>
          </Form.Item>

          <Form.Item style={{ textAlign: isMobile ? 'center' : 'right', marginBottom: 0, marginTop: 24 }}>
            <Space direction={isMobile ? 'vertical' : 'horizontal'} style={{ width: isMobile ? '100%' : 'auto' }}>
              <Button
                onClick={closeModal}
                style={isMobile ? { width: '100%' } : {}}
                size={isMobile ? 'large' : 'middle'}
              >
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                style={isMobile ? { width: '100%' } : {}}
                size={isMobile ? 'large' : 'middle'}
              >
                {editingDatabase ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DatabaseList;
