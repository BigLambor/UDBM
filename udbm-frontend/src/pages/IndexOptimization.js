import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Select, Space, Tag, Progress,
  Modal, Alert, Spin, Tooltip, Statistic, Row, Col,
  Tabs, Descriptions, Typography, Popconfirm, message
} from 'antd';
import {
  DatabaseOutlined, BarChartOutlined, ThunderboltOutlined,
  ReloadOutlined, PlayCircleOutlined, CheckCircleOutlined,
  WarningOutlined, BulbOutlined, DeleteOutlined, PlusOutlined,
  ClockCircleOutlined, TrophyOutlined
} from '@ant-design/icons';

import { performanceAPI } from '../services/api';
import DatabaseSelector from '../components/DatabaseSelector';

const { Option } = Select;
const { TabPane } = Tabs;
const { Title, Text } = Typography;

const IndexOptimization = () => {
  const [loading, setLoading] = useState(false);
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [selectedDatabaseType, setSelectedDatabaseType] = useState('all');
  const [indexSuggestions, setIndexSuggestions] = useState([]);
  const [tuningTasks, setTuningTasks] = useState([]);
  const [databases, setDatabases] = useState([]);
  const [executingTask, setExecutingTask] = useState(null);
  const [taskModalVisible, setTaskModalVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // 获取数据库列表
  useEffect(() => {
    fetchDatabases();
  }, []);

  // 获取数据
  useEffect(() => {
    if (selectedDatabase) {
      fetchIndexSuggestions();
      fetchTuningTasks();
    }
  }, [selectedDatabase]);

  const fetchDatabases = async () => {
    try {
      const response = await performanceAPI.getDatabases();
      setDatabases(Array.isArray(response) ? response : []);
      if (Array.isArray(response) && response.length > 0 && !selectedDatabase) {
        setSelectedDatabase(response[0]);
      }
    } catch (error) {
      console.error('获取数据库列表失败:', error);
    }
  };

  const fetchIndexSuggestions = async () => {
    setLoading(true);
    try {
      const response = await performanceAPI.getIndexSuggestions(selectedDatabase.id);
      setIndexSuggestions(response || []);
    } catch (error) {
      console.error('获取索引建议失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTuningTasks = async () => {
    try {
      const response = await performanceAPI.getTuningTasks(selectedDatabase.id);
      setTuningTasks(response || []);
    } catch (error) {
      console.error('获取调优任务失败:', error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([
      fetchIndexSuggestions(),
      fetchTuningTasks()
    ]);
    setRefreshing(false);
  };

  const handleCreateIndexTask = async (suggestion) => {
    try {
      const response = await performanceAPI.createIndexTask(selectedDatabase.id, {
        table_name: suggestion.table_name,
        column_names: suggestion.column_names,
        index_type: suggestion.index_type,
        reason: suggestion.reason
      });

      message.success('索引创建任务已提交');
      await fetchTuningTasks();
    } catch (error) {
      console.error('创建索引任务失败:', error);
      message.error('创建索引任务失败');
    }
  };

  const handleExecuteTask = async (taskId) => {
    setExecutingTask(taskId);
    try {
      const response = await performanceAPI.executeTask(taskId);

      if (response.success) {
        message.success(response.message || '任务执行成功');
      } else {
        message.error(response.error || '任务执行失败');
      }

      await fetchTuningTasks();
    } catch (error) {
      console.error('执行任务失败:', error);
      message.error('执行任务失败');
    } finally {
      setExecutingTask(null);
    }
  };

  const getImpactColor = (score) => {
    if (score >= 80) return '#f5222e';
    if (score >= 60) return '#faad14';
    if (score >= 40) return '#1890ff';
    return '#52c41a';
  };

  const getImpactLevel = (score) => {
    if (score >= 80) return '高';
    if (score >= 60) return '中';
    if (score >= 40) return '低';
    return '极低';
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'orange',
      running: 'blue',
      completed: 'green',
      failed: 'red',
      cancelled: 'gray'
    };
    return colors[status] || 'default';
  };

  const getStatusText = (status) => {
    const texts = {
      pending: '待执行',
      running: '执行中',
      completed: '已完成',
      failed: '失败',
      cancelled: '已取消'
    };
    return texts[status] || status;
  };

  // 索引建议表格列配置
  const suggestionColumns = [
    {
      title: '表名',
      dataIndex: 'table_name',
      key: 'table_name',
      width: 150,
      render: (table) => <Text strong>{table}</Text>
    },
    {
      title: '列名',
      dataIndex: 'column_names',
      key: 'column_names',
      width: 200,
      render: (columns) => (
        <div>
          {Array.isArray(columns) ? columns.map((col, index) => (
            <Tag key={index} size="small" style={{ marginBottom: 2 }}>
              {col}
            </Tag>
          )) : <Tag size="small">{columns}</Tag>}
        </div>
      )
    },
    {
      title: '索引类型',
      dataIndex: 'index_type',
      key: 'index_type',
      width: 100,
      render: (type) => <Tag color="blue">{type ? type.toUpperCase() : '未知'}</Tag>
    },
    {
      title: '影响评分',
      dataIndex: 'impact_score',
      key: 'impact_score',
      width: 120,
      sorter: (a, b) => a.impact_score - b.impact_score,
      render: (score) => (
        <div>
          <Progress
            percent={score}
            size="small"
            strokeColor={getImpactColor(score)}
            showInfo={false}
          />
          <div style={{ textAlign: 'center', marginTop: 4 }}>
            <Text style={{ color: getImpactColor(score) }}>
              {score}/100 ({getImpactLevel(score)})
            </Text>
          </div>
        </div>
      )
    },
    {
      title: '建议原因',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true,
      render: (reason) => (
        <Tooltip title={reason}>
          <Text style={{ maxWidth: 200 }} ellipsis>{reason}</Text>
        </Tooltip>
      )
    },
    {
      title: '预期改善',
      dataIndex: 'estimated_improvement',
      key: 'estimated_improvement',
      width: 150,
      render: (improvement) => (
        <Text type="success">{improvement}</Text>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          {record.status === 'pending' && (
            <Tooltip title="创建索引">
              <Button
                type="primary"
                size="small"
                icon={<PlusOutlined />}
                onClick={() => handleCreateIndexTask(record)}
              >
                创建
              </Button>
            </Tooltip>
          )}
          {record.status === 'applied' && (
            <Tooltip title="已应用">
              <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '16px' }} />
            </Tooltip>
          )}
        </Space>
      )
    }
  ];

  // 调优任务表格列配置
  const taskColumns = [
    {
      title: '任务名称',
      dataIndex: 'task_name',
      key: 'task_name',
      width: 200,
      render: (name) => <Text strong>{name}</Text>
    },
    {
      title: '任务类型',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 120,
      render: (type) => {
        const typeMap = {
          index_creation: '索引创建',
          query_rewrite: '查询重写',
          config_tuning: '配置调优'
        };
        return <Tag color="blue">{typeMap[type] || type}</Tag>;
      }
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority) => {
        const colors = { 5: 'red', 4: 'orange', 3: 'yellow', 2: 'blue', 1: 'green' };
        return <Tag color={colors[priority] || 'default'}>P{priority}</Tag>;
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (time) => new Date(time).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          {record.status === 'pending' && (
            <Tooltip title="执行任务">
              <Button
                type="primary"
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={() => handleExecuteTask(record.id)}
                loading={executingTask === record.id}
              >
                执行
              </Button>
            </Tooltip>
          )}
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<BulbOutlined />}
              onClick={() => {
                setSelectedTask(record);
                setTaskModalVisible(true);
              }}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <h2 style={{ margin: 0 }}>
              <BarChartOutlined style={{ marginRight: 8 }} />
              索引优化
            </h2>
            <p style={{ margin: '8px 0', color: '#666' }}>
              智能分析不同数据库的索引使用情况，推荐最适合的索引类型
            </p>
          </div>
          <Space>
            <Button
              type="primary"
              icon={<ReloadOutlined spin={refreshing} />}
              onClick={handleRefresh}
              loading={refreshing}
              disabled={!selectedDatabase}
            >
              刷新数据
            </Button>
          </Space>
        </div>
        
        {/* 数据库选择器 */}
        <DatabaseSelector
          databases={databases}
          selectedDatabase={selectedDatabase}
          onDatabaseChange={setSelectedDatabase}
          selectedType={selectedDatabaseType}
          onTypeChange={setSelectedDatabaseType}
          loading={loading}
        />
      </div>

      {/* 统计信息 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="待优化建议"
              value={indexSuggestions.filter(s => s.status === 'pending').length}
              suffix="个"
              valueStyle={{ color: '#faad14' }}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="进行中任务"
              value={tuningTasks.filter(t => t.status === 'running').length}
              suffix="个"
              valueStyle={{ color: '#1890ff' }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已完成任务"
              value={tuningTasks.filter(t => t.status === 'completed').length}
              suffix="个"
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="优化成功率"
              value={85.6}
              suffix="%"
              valueStyle={{ color: '#52c41a' }}
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="1">
        <TabPane tab="索引建议" key="1">
          <Card>
            <Alert
              message="索引优化建议"
              description="系统基于查询模式分析和执行计划，为您生成最优的索引创建建议。建议按影响程度排序，优先处理高影响的建议。"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Table
              columns={suggestionColumns}
              dataSource={indexSuggestions}
              rowKey="id"
              loading={loading}
              pagination={{
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                defaultSortOrder: 'descend'
              }}
              scroll={{ x: 1200 }}
            />
          </Card>
        </TabPane>

        <TabPane tab="调优任务" key="2">
          <Card>
            <Table
              columns={taskColumns}
              dataSource={tuningTasks}
              rowKey="id"
              loading={loading}
              pagination={{
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
              }}
              scroll={{ x: 1200 }}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* 任务详情模态框 */}
      <Modal
        title="调优任务详情"
        open={taskModalVisible}
        onCancel={() => setTaskModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setTaskModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {selectedTask && (
          <div>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Descriptions title="任务基本信息" size="small" column={2}>
                <Descriptions.Item label="任务名称">
                  <Text strong>{selectedTask.task_name}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="任务类型">
                  <Tag color="blue">
                    {selectedTask.task_type === 'index_creation' ? '索引创建' :
                     selectedTask.task_type === 'query_rewrite' ? '查询重写' :
                     selectedTask.task_type === 'config_tuning' ? '配置调优' :
                     selectedTask.task_type}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="优先级">
                  <Tag color={
                    selectedTask.priority >= 4 ? 'red' :
                    selectedTask.priority >= 3 ? 'orange' :
                    selectedTask.priority >= 2 ? 'blue' : 'green'
                  }>
                    P{selectedTask.priority}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Tag color={getStatusColor(selectedTask.status)}>
                    {getStatusText(selectedTask.status)}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="创建时间">
                  {new Date(selectedTask.created_at).toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="执行时间">
                  {selectedTask.started_at ? new Date(selectedTask.started_at).toLocaleString() : '-'}
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {selectedTask.description && (
              <Card size="small" style={{ marginBottom: 16 }}>
                <Title level={5}>任务描述</Title>
                <Text>{selectedTask.description}</Text>
              </Card>
            )}

            {selectedTask.execution_sql && (
              <Card size="small" style={{ marginBottom: 16 }}>
                <Title level={5}>执行SQL</Title>
                <pre style={{
                  backgroundColor: '#f5f5f5',
                  padding: '8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  overflow: 'auto'
                }}>
                  {selectedTask.execution_sql}
                </pre>
              </Card>
            )}

            {selectedTask.execution_result && (
              <Card size="small">
                <Title level={5}>执行结果</Title>
                <Alert
                  message={selectedTask.execution_result}
                  type={selectedTask.status === 'completed' ? 'success' : 'error'}
                  showIcon
                />
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default IndexOptimization;
