import React, { useState, useEffect } from 'react';
import {
  Card, Button, Select, Input, Space, Table, Alert, Spin,
  Tooltip, Statistic, Row, Col, Tabs, Descriptions,
  Typography, Modal, Form, message, Tag, Progress
} from 'antd';
import {
  DatabaseOutlined, BarChartOutlined, PlayCircleOutlined,
  FileTextOutlined, BulbOutlined, ReloadOutlined,
  CheckCircleOutlined, WarningOutlined, ClockCircleOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';

import { performanceAPI } from '../services/api';
import DatabaseSelector from '../components/DatabaseSelector';

const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;
const { Title, Text, Paragraph } = Typography;
const { TextArea: DescTextArea } = Input;

const ExecutionPlanAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [selectedDatabaseType, setSelectedDatabaseType] = useState('all');
  const [databases, setDatabases] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [executionPlans, setExecutionPlans] = useState([]);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [analysisModalVisible, setAnalysisModalVisible] = useState(false);
  const [comparisonModalVisible, setComparisonModalVisible] = useState(false);
  const [selectedPlans, setSelectedPlans] = useState([]);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [queryText, setQueryText] = useState('');

  // 获取数据库列表
  useEffect(() => {
    fetchDatabases();
  }, []);

  // 获取执行计划历史
  useEffect(() => {
    if (selectedDatabase) {
      fetchExecutionPlans();
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

  const fetchExecutionPlans = async () => {
    setLoading(true);
    try {
      const response = await performanceAPI.getExecutionPlans(selectedDatabase.id);
      setExecutionPlans(response.execution_plans || []);
    } catch (error) {
      console.error('获取执行计划失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzePlan = async () => {
    if (!queryText.trim()) {
      message.warning('请输入要分析的SQL查询');
      return;
    }

    setAnalyzing(true);
    try {
      const response = await performanceAPI.analyzeExecutionPlan(selectedDatabase.id, queryText);
      setCurrentAnalysis(response);
      setAnalysisModalVisible(true);
      await fetchExecutionPlans(); // 刷新列表
    } catch (error) {
      console.error('分析执行计划失败:', error);
      message.error('分析执行计划失败');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleComparePlans = async () => {
    if (selectedPlans.length !== 2) {
      message.warning('请选择两个执行计划进行比较');
      return;
    }

    try {
      const response = await performanceAPI.compareExecutionPlans(
        selectedPlans[0],
        selectedPlans[1]
      );
      setComparisonResult(response);
      setComparisonModalVisible(true);
    } catch (error) {
      console.error('比较执行计划失败:', error);
      message.error('比较执行计划失败');
    }
  };

  const getPerformanceColor = (score) => {
    if (score >= 80) return '#52c41a';
    if (score >= 60) return '#faad14';
    return '#f5222e';
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: '#f5222e',
      high: '#fa541c',
      medium: '#faad14',
      low: '#52c41a'
    };
    return colors[severity] || '#d9d9d9';
  };

  // 执行计划表格列配置
  const planColumns = [
    {
      title: '查询哈希',
      dataIndex: 'query_hash',
      key: 'query_hash',
      width: 120,
      ellipsis: true,
      render: (hash) => (
        <Tooltip title={hash}>
          <Text code style={{ fontSize: '12px' }}>{hash.substring(0, 8)}...</Text>
        </Tooltip>
      )
    },
    {
      title: '查询内容',
      dataIndex: 'query_text',
      key: 'query_text',
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text}>
          <Text style={{ maxWidth: 200 }} ellipsis>{text}</Text>
        </Tooltip>
      )
    },
    {
      title: '性能评分',
      dataIndex: 'analysis_result',
      key: 'performance_score',
      width: 120,
      render: (analysis) => {
        if (!analysis) return '-';
        const score = analysis.performance_score;
        return (
          <div>
            <Progress
              percent={score}
              size="small"
              strokeColor={getPerformanceColor(score)}
              showInfo={false}
            />
            <div style={{ textAlign: 'center', marginTop: 4 }}>
              <Text style={{ color: getPerformanceColor(score), fontSize: '12px' }}>
                {score}/100
              </Text>
            </div>
          </div>
        );
      }
    },
    {
      title: '瓶颈数量',
      dataIndex: 'analysis_result',
      key: 'bottlenecks',
      width: 100,
      render: (analysis) => {
        if (!analysis) return '-';
        const count = analysis.bottlenecks?.length || 0;
        return (
          <Tag color={count > 2 ? 'red' : count > 0 ? 'orange' : 'green'}>
            {count}
          </Tag>
        );
      }
    },
    {
      title: '分析时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 150,
      render: (timestamp) => new Date(timestamp).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<FileTextOutlined />}
              onClick={() => {
                setCurrentAnalysis({
                  execution_plan: { plan_text: record.plan_text },
                  analysis: record.analysis_result,
                  recommendations: []
                });
                setAnalysisModalVisible(true);
              }}
            />
          </Tooltip>
          <input
            type="checkbox"
            checked={selectedPlans.includes(record.id)}
            onChange={(e) => {
              if (e.target.checked) {
                if (selectedPlans.length < 2) {
                  setSelectedPlans([...selectedPlans, record.id]);
                }
              } else {
                setSelectedPlans(selectedPlans.filter(id => id !== record.id));
              }
            }}
          />
        </Space>
      )
    }
  ];

  const renderAnalysisResult = () => {
    if (!currentAnalysis) return null;

    const { execution_plan, analysis, recommendations } = currentAnalysis;

    return (
      <div>
        {/* 执行计划文本 */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <Title level={5}>执行计划</Title>
          <pre style={{
            backgroundColor: '#f5f5f5',
            padding: '12px',
            borderRadius: '4px',
            fontSize: '12px',
            fontFamily: 'monospace',
            overflow: 'auto',
            maxHeight: '300px'
          }}>
            {execution_plan.plan_text}
          </pre>
        </Card>

        {/* 性能分析结果 */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <Title level={5}>性能分析</Title>
          <Row gutter={[16, 16]}>
            <Col xs={12}>
              <Statistic
                title="性能评分"
                value={analysis.performance_score}
                suffix="/100"
                valueStyle={{ color: getPerformanceColor(analysis.performance_score) }}
              />
            </Col>
            <Col xs={12}>
              <Statistic
                title="发现瓶颈"
                value={analysis.bottlenecks?.length || 0}
                valueStyle={{ color: analysis.bottlenecks?.length > 0 ? '#f5222e' : '#52c41a' }}
              />
            </Col>
          </Row>
        </Card>

        {/* 瓶颈详情 */}
        {analysis.bottlenecks && analysis.bottlenecks.length > 0 && (
          <Card size="small" style={{ marginBottom: 16 }}>
            <Title level={5} style={{ color: '#f5222e' }}>发现的性能瓶颈</Title>
            {analysis.bottlenecks.map((bottleneck, index) => (
              <Alert
                key={index}
                message={
                  <div>
                    <Text strong>{bottleneck.type ? bottleneck.type.toUpperCase() : '未知类型'}</Text>
                    <Tag
                      color={getSeverityColor(bottleneck.severity)}
                      style={{ marginLeft: 8 }}
                    >
                      {bottleneck.severity}
                    </Tag>
                  </div>
                }
                description={bottleneck.description}
                type={bottleneck.severity === 'critical' ? 'error' : 'warning'}
                showIcon
                style={{ marginBottom: 8 }}
              />
            ))}
          </Card>
        )}

        {/* 优化建议 */}
        {recommendations && recommendations.length > 0 && (
          <Card size="small">
            <Title level={5}>优化建议</Title>
            {recommendations.map((rec, index) => (
              <Alert
                key={index}
                message={rec.title}
                description={
                  <div>
                    <Text>{rec.description}</Text>
                    <br />
                    <Text strong>预计改善: {rec.estimated_improvement}</Text>
                    <br />
                    <Text code>{rec.sql_suggestion}</Text>
                  </div>
                }
                type={rec.priority === 'high' ? 'warning' : 'info'}
                showIcon
                style={{ marginBottom: 8 }}
              />
            ))}
          </Card>
        )}
      </div>
    );
  };

  const renderComparisonResult = () => {
    if (!comparisonResult) return null;

    return (
      <div>
        <Row gutter={[16, 16]}>
          <Col xs={12}>
            <Card size="small">
              <Title level={5}>执行计划 1</Title>
              <Statistic
                title="性能评分"
                value={comparisonResult.plan1.performance_score}
                suffix="/100"
                valueStyle={{ color: getPerformanceColor(comparisonResult.plan1.performance_score) }}
              />
              <div style={{ marginTop: 8 }}>
                <Text>瓶颈数量: {comparisonResult.plan1.bottlenecks_count}</Text>
              </div>
            </Card>
          </Col>
          <Col xs={12}>
            <Card size="small">
              <Title level={5}>执行计划 2</Title>
              <Statistic
                title="性能评分"
                value={comparisonResult.plan2.performance_score}
                suffix="/100"
                valueStyle={{ color: getPerformanceColor(comparisonResult.plan2.performance_score) }}
              />
              <div style={{ marginTop: 8 }}>
                <Text>瓶颈数量: {comparisonResult.plan2.bottlenecks_count}</Text>
              </div>
            </Card>
          </Col>
        </Row>

        <Card size="small" style={{ marginTop: 16 }}>
          <Title level={5}>比较结果</Title>
          <Descriptions size="small" column={2}>
            <Descriptions.Item label="评分差异">
              <Text
                style={{
                  color: comparisonResult.improvement.score_difference > 0 ? '#52c41a' : '#f5222e'
                }}
              >
                {comparisonResult.improvement.score_difference > 0 ? '+' : ''}
                {comparisonResult.improvement.score_difference}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="瓶颈减少">
              <Text
                style={{
                  color: comparisonResult.improvement.bottlenecks_reduced > 0 ? '#52c41a' : '#d9d9d9'
                }}
              >
                {comparisonResult.improvement.bottlenecks_reduced > 0 ? '-' : ''}
                {Math.abs(comparisonResult.improvement.bottlenecks_reduced)}
              </Text>
            </Descriptions.Item>
          </Descriptions>
        </Card>
      </div>
    );
  };

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0 }}>
            <DatabaseOutlined style={{ marginRight: 8 }} />
            执行计划分析
          </h2>
          <p style={{ margin: '8px 0', color: '#666' }}>
            深度分析SQL执行计划，识别性能瓶颈并生成优化建议
          </p>
        </div>
        <Space>
          <Button
            type="primary"
            icon={<ReloadOutlined spin={loading} />}
            onClick={fetchExecutionPlans}
            loading={loading}
            disabled={!selectedDatabase}
          >
            刷新列表
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
        style={{ marginBottom: 16 }}
      />

      <Tabs defaultActiveKey="1">
        <TabPane tab="执行计划分析" key="1">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="SQL查询输入">
                <TextArea
                  rows={8}
                  placeholder="请输入要分析的SQL查询语句..."
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  style={{ fontFamily: 'monospace' }}
                />
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleAnalyzePlan}
                  loading={analyzing}
                  style={{ marginTop: 16, width: '100%' }}
                >
                  分析执行计划
                </Button>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="快速统计">
                <Row gutter={[16, 16]}>
                  <Col xs={12}>
                    <Statistic
                      title="总分析次数"
                      value={executionPlans.length}
                      prefix={<BarChartOutlined />}
                    />
                  </Col>
                  <Col xs={12}>
                    <Statistic
                      title="平均性能评分"
                      value={executionPlans.length > 0 ?
                        Math.round(executionPlans
                          .filter(p => p.analysis_result)
                          .reduce((sum, p) => sum + (p.analysis_result?.performance_score || 0), 0) /
                          executionPlans.filter(p => p.analysis_result).length) : 0
                      }
                      suffix="/100"
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Col>
                </Row>
              </Card>

              <Card title="常见问题类型" style={{ marginTop: 16 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Alert
                    message="全表扫描"
                    description="查询没有使用索引进行全表扫描"
                    type="warning"
                    showIcon
                    style={{ fontSize: '12px' }}
                  />
                  <Alert
                    message="文件排序"
                    description="查询使用了文件排序，影响性能"
                    type="warning"
                    showIcon
                    style={{ fontSize: '12px' }}
                  />
                  <Alert
                    message="临时表"
                    description="查询使用了临时表，增加I/O开销"
                    type="info"
                    showIcon
                    style={{ fontSize: '12px' }}
                  />
                </Space>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="执行计划历史" key="2">
          <Card>
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Button
                  type="primary"
                  onClick={handleComparePlans}
                  disabled={selectedPlans.length !== 2}
                  icon={<BarChartOutlined />}
                >
                  比较选中计划
                </Button>
                <Text type="secondary">
                  已选择 {selectedPlans.length} 个执行计划
                  {selectedPlans.length > 0 && ` (ID: ${selectedPlans.join(', ')})`}
                </Text>
              </Space>
            </div>

            <Table
              columns={planColumns}
              dataSource={executionPlans}
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

      {/* 执行计划分析结果模态框 */}
      <Modal
        title="执行计划分析结果"
        open={analysisModalVisible}
        onCancel={() => setAnalysisModalVisible(false)}
        width={1000}
        footer={[
          <Button key="close" onClick={() => setAnalysisModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {renderAnalysisResult()}
      </Modal>

      {/* 执行计划比较模态框 */}
      <Modal
        title="执行计划比较结果"
        open={comparisonModalVisible}
        onCancel={() => setComparisonModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setComparisonModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {renderComparisonResult()}
      </Modal>
    </div>
  );
};

export default ExecutionPlanAnalysis;
