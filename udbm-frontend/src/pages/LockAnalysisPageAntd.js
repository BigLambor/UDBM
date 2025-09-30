import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Statistic, Progress, Alert, Spin, Select,
  Button, Tabs, Table, Tag, Space, Tooltip, message, Switch,
  Badge, Divider, Modal, Form, InputNumber, Typography,
  Descriptions, Timeline, Empty, Result
} from 'antd';
import {
  LockOutlined, LineChartOutlined, SettingOutlined,
  FileTextOutlined, ReloadOutlined, PlayCircleOutlined,
  PauseCircleOutlined, DownloadOutlined, PlusOutlined,
  EyeOutlined, ClockCircleOutlined, WarningOutlined,
  CheckCircleOutlined, DashboardOutlined, ThunderboltOutlined,
  FireOutlined, AlertOutlined
} from '@ant-design/icons';

import LockAnalysisDashboardAntd from '../components/LockAnalysisDashboardAntd';
import DatabaseSelector from '../components/DatabaseSelector';
import DataSourceIndicator from '../components/DataSourceIndicator';
import LockAnalysisHelper from '../components/LockAnalysisHelper';
import { performanceAPI } from '../services/api';

const { Option } = Select;
const { TabPane } = Tabs;
const { Title, Text, Paragraph } = Typography;

const LockAnalysisPageAntd = () => {
  const [activeTab, setActiveTab] = useState('1');
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [selectedDatabaseType, setSelectedDatabaseType] = useState('all');
  const [databases, setDatabases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 分析相关状态
  const [analysisModalVisible, setAnalysisModalVisible] = useState(false);
  const [analysisForm] = Form.useForm();
  const [analysisResult, setAnalysisResult] = useState(null);
  
  // 监控相关状态
  const [monitoringStatus, setMonitoringStatus] = useState(null);
  const [monitoringModalVisible, setMonitoringModalVisible] = useState(false);
  const [monitoringForm] = Form.useForm();
  
  // 报告相关状态
  const [reports, setReports] = useState([]);
  const [reportModalVisible, setReportModalVisible] = useState(false);
  const [reportForm] = Form.useForm();
  
  // 优化任务相关状态
  const [optimizationTasks, setOptimizationTasks] = useState([]);

  useEffect(() => {
    fetchDatabases();
  }, []);

  useEffect(() => {
    if (selectedDatabase && selectedDatabase.id) {
      fetchMonitoringStatus();
      fetchReports();
      fetchOptimizationTasks();
    }
  }, [selectedDatabase]);

  const fetchDatabases = async () => {
    try {
      const response = await performanceAPI.getDatabases();
      setDatabases(Array.isArray(response) ? response : []);
      if (Array.isArray(response) && response.length > 0 && !selectedDatabase) {
        setSelectedDatabase(response[0]);
      }
    } catch (err) {
      console.error('获取数据库列表失败:', err);
      message.error('获取数据库列表失败');
    }
  };

  const fetchMonitoringStatus = async () => {
    if (!selectedDatabase || !selectedDatabase.id) return;
    try {
      const response = await performanceAPI.getLockMonitoringStatus(selectedDatabase.id);
      setMonitoringStatus(response);
    } catch (err) {
      console.error('获取监控状态失败:', err);
      // 不显示错误消息，静默处理
    }
  };

  const fetchReports = async () => {
    if (!selectedDatabase || !selectedDatabase.id) return;
    try {
      const response = await performanceAPI.getLockAnalysisReports(selectedDatabase.id);
      setReports(response || []);
    } catch (err) {
      console.error('获取报告列表失败:', err);
      // 不显示错误消息，静默处理
    }
  };
  
  const fetchOptimizationTasks = async () => {
    if (!selectedDatabase || !selectedDatabase.id) return;
    try {
      const response = await performanceAPI.getOptimizationTasks(selectedDatabase.id);
      setOptimizationTasks(response || []);
    } catch (err) {
      console.error('获取优化任务失败:', err);
      // 不显示错误消息，静默处理
    }
  };

  const handleAnalysis = async (values) => {
    if (!selectedDatabase || !selectedDatabase.id) {
      message.warning('请先选择数据库');
      return;
    }
    try {
      setLoading(true);
      const response = await performanceAPI.analyzeLocks(selectedDatabase.id, {
        database_id: selectedDatabase.id,
        analysis_type: values.analysisType,
        time_range_hours: values.timeRange,
        include_wait_chains: true,
        include_contention: true,
        min_wait_time: 0.1
      });
      setAnalysisResult(response);
      setAnalysisModalVisible(false);
      message.success('锁分析执行成功');
    } catch (err) {
      message.error('分析失败: ' + (err.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };

  const handleStartMonitoring = async (values) => {
    if (!selectedDatabase || !selectedDatabase.id) {
      message.warning('请先选择数据库');
      return;
    }
    try {
      await performanceAPI.startLockMonitoring(selectedDatabase.id, values.collectionInterval);
      setMonitoringModalVisible(false);
      fetchMonitoringStatus();
      message.success('锁监控已启动');
    } catch (err) {
      message.error('启动监控失败: ' + (err.message || '未知错误'));
    }
  };

  const handleStopMonitoring = async () => {
    if (!selectedDatabase || !selectedDatabase.id) {
      message.warning('请先选择数据库');
      return;
    }
    try {
      await performanceAPI.stopLockMonitoring(selectedDatabase.id);
      fetchMonitoringStatus();
      message.success('锁监控已停止');
    } catch (err) {
      message.error('停止监控失败: ' + (err.message || '未知错误'));
    }
  };

  const handleGenerateReport = async (values) => {
    if (!selectedDatabase || !selectedDatabase.id) {
      message.warning('请先选择数据库');
      return;
    }
    try {
      setLoading(true);
      await performanceAPI.generateLockAnalysisReport(
        selectedDatabase.id,
        values.reportType,
        values.days
      );
      setReportModalVisible(false);
      fetchReports();
      message.success('报告生成成功');
    } catch (err) {
      message.error('生成报告失败: ' + (err.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };

  const getMonitoringStatusTag = (status) => {
    const statusMap = {
      running: { color: 'success', text: '运行中', icon: <PlayCircleOutlined /> },
      stopped: { color: 'error', text: '已停止', icon: <PauseCircleOutlined /> },
      paused: { color: 'warning', text: '已暂停', icon: <PauseCircleOutlined /> }
    };
    const config = statusMap[status] || { color: 'default', text: '未知', icon: null };
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  const getSeverityTag = (severity) => {
    const severityMap = {
      low: { color: 'success', text: '低' },
      medium: { color: 'warning', text: '中' },
      high: { color: 'orange', text: '高' },
      critical: { color: 'error', text: '严重' }
    };
    const config = severityMap[severity] || { color: 'default', text: '未知' };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 优化任务表格列定义
  const taskColumns = [
    {
      title: '任务名称',
      dataIndex: 'task_name',
      key: 'task_name',
    },
    {
      title: '任务类型',
      dataIndex: 'task_type',
      key: 'task_type',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusMap = {
          pending: { color: 'default', text: '待执行' },
          running: { color: 'processing', text: '执行中' },
          completed: { color: 'success', text: '已完成' },
          failed: { color: 'error', text: '失败' }
        };
        const config = statusMap[status] || { color: 'default', text: status };
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority) => getSeverityTag(priority)
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time) => new Date(time).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EyeOutlined />}>
            查看
          </Button>
        </Space>
      ),
    },
  ];

  // 报告表格列定义
  const reportColumns = [
    {
      title: '报告类型',
      dataIndex: 'report_type',
      key: 'report_type',
      render: (type) => {
        const typeMap = {
          daily: '日报',
          weekly: '周报',
          monthly: '月报',
          custom: '自定义'
        };
        return typeMap[type] || type;
      }
    },
    {
      title: '分析周期',
      key: 'period',
      render: (_, record) => (
        <span>
          {new Date(record.analysis_period_start).toLocaleDateString()} - 
          {new Date(record.analysis_period_end).toLocaleDateString()}
        </span>
      )
    },
    {
      title: '健康评分',
      dataIndex: 'overall_health_score',
      key: 'overall_health_score',
      render: (score) => (
        <Progress
          percent={score}
          size="small"
          strokeColor={score >= 80 ? '#52c41a' : score >= 60 ? '#faad14' : '#f5222d'}
          format={(percent) => `${percent?.toFixed(1)}`}
        />
      )
    },
    {
      title: '竞争严重程度',
      dataIndex: 'contention_severity',
      key: 'contention_severity',
      render: (severity) => getSeverityTag(severity)
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time) => new Date(time).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button type="link" size="small" icon={<EyeOutlined />} />
          </Tooltip>
          <Tooltip title="下载报告">
            <Button type="link" size="small" icon={<DownloadOutlined />} />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={3}>
          <LockOutlined style={{ marginRight: 8 }} />
          数据库锁分析
        </Title>
      </div>

      {/* 数据库选择和监控状态 */}
      <DatabaseSelector
        databases={databases}
        selectedDatabase={selectedDatabase}
        onDatabaseChange={setSelectedDatabase}
        selectedType={selectedDatabaseType}
        onTypeChange={setSelectedDatabaseType}
        showTypeFilter={true}
        showStats={true}
        loading={loading}
        style={{ marginBottom: 16 }}
      />
      
      {/* 数据源指示器 */}
      {selectedDatabase && (
        <DataSourceIndicator
          database={selectedDatabase}
          isConnected={true}
          style={{ marginBottom: 16 }}
        />
      )}
      
      {/* 监控状态卡片 */}
      {selectedDatabase && (
        <Card style={{ marginBottom: 16 }}>
          <Row gutter={[16, 16]} align="middle">
            <Col span={6}>
              <Space>
                <Text>监控状态:</Text>
                {getMonitoringStatusTag(monitoringStatus?.status)}
              </Space>
            </Col>
            <Col span={6}>
              <Badge
                status={monitoringStatus?.status === 'running' ? 'processing' : 'default'}
                text={`收集间隔: ${monitoringStatus?.collection_interval || 60}秒`}
              />
            </Col>
            <Col span={6}>
              <Badge
                count={monitoringStatus?.total_events_collected || 0}
                showZero
                overflowCount={999999}
                style={{ backgroundColor: '#52c41a' }}
              >
                <Text>已收集事件</Text>
              </Badge>
            </Col>
            <Col span={6}>
              <Text type="secondary">
                数据库类型: {selectedDatabase.type ? selectedDatabase.type.toUpperCase() : '未知'}
              </Text>
            </Col>
          </Row>
        </Card>
      )}

      {/* 操作按钮 */}
      <Space style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={() => setAnalysisModalVisible(true)}
        >
          执行分析
        </Button>
        <Button
          icon={<SettingOutlined />}
          onClick={() => setMonitoringModalVisible(true)}
        >
          监控设置
        </Button>
        <Button
          icon={<DownloadOutlined />}
          onClick={() => setReportModalVisible(true)}
        >
          生成报告
        </Button>
        {monitoringStatus?.status === 'running' ? (
          <Button
            danger
            icon={<PauseCircleOutlined />}
            onClick={handleStopMonitoring}
          >
            停止监控
          </Button>
        ) : (
          <Button
            type="default"
            icon={<PlayCircleOutlined />}
            onClick={() => setMonitoringModalVisible(true)}
          >
            启动监控
          </Button>
        )}
        <Button
          icon={<ReloadOutlined />}
          onClick={() => {
            fetchMonitoringStatus();
            fetchReports();
            fetchOptimizationTasks();
            message.success('数据已刷新');
          }}
        >
          刷新
        </Button>
      </Space>

      {/* 主要内容标签页 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane
            tab={
              <span>
                <DashboardOutlined />
                实时监控
              </span>
            }
            key="1"
          >
            {selectedDatabase ? (
              <LockAnalysisDashboardAntd databaseId={selectedDatabase.id} />
            ) : (
              <Empty
                description="请选择数据库"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </TabPane>

          <TabPane
            tab={
              <span>
                <LineChartOutlined />
                历史分析
              </span>
            }
            key="2"
          >
            {analysisResult ? (
              <div>
                <Alert
                  message="分析完成"
                  description={`分析时间: ${analysisResult.analysis_timestamp}`}
                  type="success"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Card title="分析结果概览" size="small">
                      <Descriptions column={1} size="small">
                        <Descriptions.Item label="分析类型">
                          {analysisResult.analysis_type}
                        </Descriptions.Item>
                        <Descriptions.Item label="数据库ID">
                          {analysisResult.database_id}
                        </Descriptions.Item>
                        <Descriptions.Item label="分析时间">
                          {new Date(analysisResult.analysis_timestamp).toLocaleString()}
                        </Descriptions.Item>
                      </Descriptions>
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card title="关键指标" size="small">
                      <Descriptions column={1} size="small">
                        <Descriptions.Item label="健康评分">
                          <Progress
                            percent={analysisResult.result?.health_score || 0}
                            size="small"
                            strokeColor={
                              analysisResult.result?.health_score >= 80
                                ? '#52c41a'
                                : analysisResult.result?.health_score >= 60
                                ? '#faad14'
                                : '#f5222d'
                            }
                          />
                        </Descriptions.Item>
                        <Descriptions.Item label="当前锁数">
                          {analysisResult.result?.current_locks?.length || 0}
                        </Descriptions.Item>
                        <Descriptions.Item label="等待链数">
                          {analysisResult.result?.wait_chains?.length || 0}
                        </Descriptions.Item>
                      </Descriptions>
                    </Card>
                  </Col>
                </Row>
              </div>
            ) : (
              <Empty
                description="暂无分析结果"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button type="primary" onClick={() => setAnalysisModalVisible(true)}>
                  立即分析
                </Button>
              </Empty>
            )}
          </TabPane>

          <TabPane
            tab={
              <span>
                <SettingOutlined />
                优化任务
              </span>
            }
            key="3"
          >
            <div style={{ marginBottom: 16 }}>
              <Button type="primary" icon={<PlusOutlined />}>
                创建任务
              </Button>
              <Button 
                icon={<ReloadOutlined />} 
                onClick={fetchOptimizationTasks}
                style={{ marginLeft: 8 }}
              >
                刷新
              </Button>
            </div>
            <Table
              columns={taskColumns}
              dataSource={optimizationTasks}
              rowKey="id"
              loading={loading}
              locale={{
                emptyText: <Empty description="暂无优化任务" />
              }}
            />
          </TabPane>

          <TabPane
            tab={
              <span>
                <FileTextOutlined />
                分析报告
              </span>
            }
            key="4"
          >
            <div style={{ marginBottom: 16 }}>
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={() => setReportModalVisible(true)}
              >
                生成报告
              </Button>
            </div>
            <Table
              columns={reportColumns}
              dataSource={reports}
              rowKey="id"
              loading={loading}
              locale={{
                emptyText: <Empty description="暂无分析报告" />
              }}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 分析对话框 */}
      <Modal
        title="执行锁分析"
        visible={analysisModalVisible}
        onOk={() => analysisForm.submit()}
        onCancel={() => setAnalysisModalVisible(false)}
        confirmLoading={loading}
      >
        <Form
          form={analysisForm}
          layout="vertical"
          onFinish={handleAnalysis}
          initialValues={{
            analysisType: 'realtime',
            timeRange: 24
          }}
        >
          <Form.Item
            name="analysisType"
            label="分析类型"
            rules={[{ required: true, message: '请选择分析类型' }]}
          >
            <Select>
              <Option value="realtime">实时分析</Option>
              <Option value="historical">历史分析</Option>
              <Option value="comprehensive">综合分析</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="timeRange"
            label="时间范围(小时)"
            rules={[
              { required: true, message: '请输入时间范围' },
              { type: 'number', min: 1, max: 168, message: '时间范围应在1-168小时之间' }
            ]}
          >
            <InputNumber min={1} max={168} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 监控设置对话框 */}
      <Modal
        title="锁监控设置"
        visible={monitoringModalVisible}
        onOk={() => monitoringForm.submit()}
        onCancel={() => setMonitoringModalVisible(false)}
      >
        <Form
          form={monitoringForm}
          layout="vertical"
          onFinish={handleStartMonitoring}
          initialValues={{
            collectionInterval: 60
          }}
        >
          <Form.Item
            name="collectionInterval"
            label="收集间隔(秒)"
            rules={[
              { required: true, message: '请输入收集间隔' },
              { type: 'number', min: 10, max: 3600, message: '收集间隔应在10-3600秒之间' }
            ]}
            help="建议设置60-300秒之间的值"
          >
            <InputNumber min={10} max={3600} style={{ width: '100%' }} />
          </Form.Item>
          <Alert
            message="监控将自动收集锁事件数据，用于后续分析"
            type="info"
            showIcon
          />
        </Form>
      </Modal>

      {/* 报告生成对话框 */}
      <Modal
        title="生成锁分析报告"
        visible={reportModalVisible}
        onOk={() => reportForm.submit()}
        onCancel={() => setReportModalVisible(false)}
        confirmLoading={loading}
      >
        <Form
          form={reportForm}
          layout="vertical"
          onFinish={handleGenerateReport}
          initialValues={{
            reportType: 'custom',
            days: 7
          }}
        >
          <Form.Item
            name="reportType"
            label="报告类型"
            rules={[{ required: true, message: '请选择报告类型' }]}
          >
            <Select>
              <Option value="daily">日报</Option>
              <Option value="weekly">周报</Option>
              <Option value="monthly">月报</Option>
              <Option value="custom">自定义</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="days"
            label="分析天数"
            rules={[
              { required: true, message: '请输入分析天数' },
              { type: 'number', min: 1, max: 30, message: '分析天数应在1-30天之间' }
            ]}
          >
            <InputNumber min={1} max={30} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default LockAnalysisPageAntd;