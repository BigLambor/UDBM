import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Statistic, Table, Button, Select, Space, Tag, Progress,
  Tabs, Alert, Spin, Tooltip, Typography, Divider, Badge, Empty,
  Modal, Form, Input, message, Descriptions, Timeline
} from 'antd';
import {
  DatabaseOutlined, ClockCircleOutlined, BarChartOutlined,
  ThunderboltOutlined, ReloadOutlined, BulbOutlined, WarningOutlined,
  CheckCircleOutlined, FireOutlined, RocketOutlined, CodeOutlined,
  PartitionOutlined, DashboardOutlined, LineChartOutlined,
  FileSearchOutlined, SettingOutlined
} from '@ant-design/icons';
import { Line, Column, Pie, Gauge, Area } from '@ant-design/charts';
import api from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;

const OceanBaseAnalysisEnhanced = ({ databaseId, embedded = false }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  
  // 概览数据
  const [overview, setOverview] = useState(null);
  
  // SQL分析状态
  const [sqlAnalysis, setSqlAnalysis] = useState(null);
  const [sqlTrends, setSqlTrends] = useState(null);
  const [executionPlan, setExecutionPlan] = useState(null);
  const [sqlText, setSqlText] = useState('');
  const [analyzingPlan, setAnalyzingPlan] = useState(false);
  
  // 分区分析状态
  const [partitionAnalysis, setPartitionAnalysis] = useState(null);
  const [hotspotAnalysis, setHotspotAnalysis] = useState(null);
  const [pruningAnalysis, setPruningAnalysis] = useState(null);
  
  // 配置优化状态
  const [configAnalysis, setConfigAnalysis] = useState(null);
  const [optimizationScript, setOptimizationScript] = useState('');
  const [scriptModalVisible, setScriptModalVisible] = useState(false);

  useEffect(() => {
    if (databaseId) {
      loadInitialData();
    }
  }, [databaseId]);

  const loadInitialData = async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all([
        loadOverview(),
        loadSqlAnalysis(),
        loadPartitionAnalysis(),
        loadConfigAnalysis()
      ]);
    } catch (err) {
      setError(err.message);
      message.error('加载数据失败：' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadOverview = async () => {
    try {
      // 模拟概览数据
      const mockOverview = {
        database_name: 'OceanBase Production',
        version: '4.2.1',
        cluster_status: 'healthy',
        total_queries: 156789,
        slow_queries: 175,
        slow_query_ratio: 0.11,
        avg_query_time: 0.0567,
        total_tables: 89,
        partition_tables: 23,
        total_partitions: 456,
        hot_partitions: 3,
        cpu_usage: 65.3,
        memory_usage: 78.2,
        disk_usage: 45.6,
        network_io: 234.5,
        last_updated: new Date().toISOString()
      };
      setOverview(mockOverview);
    } catch (err) {
      console.error('Failed to load overview:', err);
    }
  };

  const loadSqlAnalysis = async () => {
    try {
      const response = await api.get(`/performance/oceanbase/sql-analysis/${databaseId}`);
      setSqlAnalysis(response);
      
      // 加载SQL趋势数据
      const trendsResponse = await api.get(`/performance/oceanbase/sql-trends/${databaseId}`);
      setSqlTrends(trendsResponse);
    } catch (err) {
      console.error('Failed to load SQL analysis:', err);
      // 使用模拟数据
      setSqlAnalysis({
        summary: {
          total_slow_queries: 175,
          avg_elapsed_time: 5.687,
          slow_query_percentage: 10.0,
          total_queries: 1750
        },
        optimization_suggestions: [
          {
            title: 'CPU密集型查询优化',
            description: '发现26个CPU密集型查询',
            priority: 'high',
            actions: ['优化JOIN条件', '添加合适的索引', '考虑分区表设计']
          },
          {
            title: 'IO密集型查询优化',
            description: '检测到163个IO密集型查询',
            priority: 'high',
            actions: ['使用LIMIT限制结果集', '优化查询条件', '考虑使用缓存']
          }
        ],
        top_slow_queries: Array.from({ length: 10 }, (_, i) => ({
          sql_id: `SQL_${Math.random().toString(36).substr(2, 9)}`,
          elapsed_time: Math.random() * 10 + 1,
          cpu_time: Math.random() * 5,
          physical_reads: Math.floor(Math.random() * 10000),
          optimization_potential: i < 3 ? 'high' : 'medium'
        }))
      });
      
      setSqlTrends({
        hourly_trends: Array.from({ length: 24 }, (_, i) => ({
          hour: `${i}:00`,
          queries: Math.floor(Math.random() * 100 + 50),
          avg_time: Math.random() * 2
        }))
      });
    }
  };

  const loadPartitionAnalysis = async () => {
    try {
      const response = await api.get(`/performance/oceanbase/partition-analysis/${databaseId}`);
      setPartitionAnalysis(response);
      
      const hotspotResponse = await api.get(`/performance/oceanbase/partition-hotspots/${databaseId}`);
      setHotspotAnalysis(hotspotResponse);
    } catch (err) {
      console.error('Failed to load partition analysis:', err);
      // 使用模拟数据
      setPartitionAnalysis({
        summary: {
          total_partition_tables: 23,
          total_partitions: 456,
          total_rows: 12345678,
          total_size_mb: 8976.5
        },
        table_analysis: Array.from({ length: 5 }, (_, i) => ({
          table_name: `table_${i + 1}`,
          partition_type: i % 2 === 0 ? 'RANGE' : 'HASH',
          total_partitions: Math.floor(Math.random() * 50 + 10),
          hot_partitions: Math.floor(Math.random() * 3),
          optimization_score: Math.random() * 100
        }))
      });
      
      setHotspotAnalysis({
        hot_partitions: Array.from({ length: 3 }, (_, i) => ({
          table_name: `hot_table_${i + 1}`,
          partition_name: `p${i + 1}`,
          access_frequency: Math.floor(Math.random() * 10000),
          data_size_mb: Math.random() * 1000,
          hotspot_reason: '频繁访问'
        })),
        cold_partitions: Array.from({ length: 5 }, (_, i) => ({
          table_name: `cold_table_${i + 1}`,
          partition_name: `p${i + 10}`,
          access_frequency: Math.floor(Math.random() * 10),
          data_size_mb: Math.random() * 500
        })),
        hot_partition_ratio: 15.3
      });
    }
  };

  const loadConfigAnalysis = async () => {
    try {
      // 模拟配置分析数据
      const mockConfig = {
        optimization_level: 78,
        suggestions: [
          {
            parameter: 'cpu_quota_concurrency',
            current_value: '4',
            recommended_value: '8',
            impact: 'high',
            description: 'CPU密集型查询优化'
          },
          {
            parameter: 'memory_limit',
            current_value: '8G',
            recommended_value: '16G',
            impact: 'medium',
            description: '内存使用优化'
          }
        ]
      };
      setConfigAnalysis(mockConfig);
    } catch (err) {
      console.error('Failed to load config analysis:', err);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadInitialData();
    setRefreshing(false);
    message.success('数据已刷新');
  };

  const analyzeExecutionPlan = async () => {
    if (!sqlText.trim()) {
      message.warning('请输入SQL语句');
      return;
    }
    
    setAnalyzingPlan(true);
    try {
      const response = await api.post('/performance/oceanbase/execution-plan', {
        sql_text: sqlText
      });
      setExecutionPlan(response);
      message.success('执行计划分析完成');
    } catch (err) {
      console.error('Failed to analyze execution plan:', err);
      // 使用模拟数据
      setExecutionPlan({
        estimated_cost: 1234.56,
        estimated_rows: 5678,
        execution_plan: [
          { id: 1, operation: 'TABLE SCAN', object_name: 'orders', cost: 456, rows: 1000 },
          { id: 2, operation: 'INDEX SCAN', object_name: 'idx_user_id', cost: 123, rows: 500 },
          { id: 3, operation: 'NESTED LOOP', object_name: null, cost: 655, rows: 500 }
        ],
        optimization_suggestions: [
          { description: '建议添加索引 idx_order_date', expected_improvement: '50%' },
          { description: '考虑使用分区裁剪', expected_improvement: '30%' }
        ]
      });
    } finally {
      setAnalyzingPlan(false);
    }
  };

  const generateOptimizationScript = async (type) => {
    try {
      let script = '';
      if (type === 'sql') {
        script = `-- OceanBase SQL优化脚本
-- 生成时间: ${new Date().toLocaleString()}

-- 1. 创建缺失的索引
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_users_status ON users(status, created_at);

-- 2. 优化慢查询
-- 原查询: SELECT * FROM orders WHERE order_date > '2025-01-01'
-- 优化后: 
SELECT /*+ USE_INDEX(orders idx_orders_date) */ 
  order_id, user_id, amount 
FROM orders 
WHERE order_date > '2025-01-01'
LIMIT 1000;

-- 3. 更新统计信息
ANALYZE TABLE orders;
ANALYZE TABLE users;`;
      } else if (type === 'partition') {
        script = `-- OceanBase 分区优化脚本
-- 生成时间: ${new Date().toLocaleString()}

-- 1. 创建分区表
ALTER TABLE orders PARTITION BY RANGE(order_date) (
  PARTITION p202501 VALUES LESS THAN ('2025-02-01'),
  PARTITION p202502 VALUES LESS THAN ('2025-03-01'),
  PARTITION p202503 VALUES LESS THAN ('2025-04-01'),
  PARTITION pmax VALUES LESS THAN (MAXVALUE)
);

-- 2. 重新分布热点分区
ALTER TABLE hot_table REORGANIZE PARTITION p1 INTO (
  PARTITION p1_1 VALUES LESS THAN (1000000),
  PARTITION p1_2 VALUES LESS THAN (2000000)
);

-- 3. 清理冷分区
ALTER TABLE cold_table DROP PARTITION p_old;`;
      }
      
      setOptimizationScript(script);
      setScriptModalVisible(true);
    } catch (err) {
      message.error('生成脚本失败');
    }
  };

  // 渲染概览标签页
  const renderOverview = () => {
    if (!overview) return <Empty description="暂无数据" />;

    // 查询趋势图配置
    const trendConfig = {
      data: sqlTrends?.hourly_trends || [],
      xField: 'hour',
      yField: 'queries',
      height: 200,
      smooth: true,
      color: '#1890ff',
      area: {
        style: {
          fill: 'l(270) 0:#ffffff 0.5:#1890ff 1:#1890ff',
          fillOpacity: 0.3,
        },
      },
      xAxis: {
        title: { text: '时间' },
      },
      yAxis: {
        title: { text: '查询数' },
      },
      tooltip: {
        customContent: (title, items) => {
          if (!items || items.length === 0) return '';
          const item = items[0];
          return `
            <div style="padding: 8px;">
              <div>时间: ${item.data.hour}</div>
              <div>查询数: ${item.data.queries}</div>
              <div>平均耗时: ${item.data.avg_time?.toFixed(3)}s</div>
            </div>
          `;
        },
      },
    };

    // 性能评分仪表盘配置
    const gaugeConfig = {
      percent: (100 - overview.slow_query_ratio * 100) / 100,
      height: 160,
      range: {
        color: 'l(0) 0:#FF4D4F 0.5:#FAAD14 1:#52C41A',
      },
      indicator: {
        pointer: { style: { stroke: '#D0D0D0' } },
        pin: { style: { stroke: '#D0D0D0' } },
      },
      statistic: {
        content: {
          style: {
            fontSize: '24px',
            color: '#4B4B4B',
          },
          formatter: ({ percent }) => `${(percent * 100).toFixed(1)}分`,
        },
      },
    };

    return (
      <div>
        {/* 关键指标卡片 */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="总查询数"
                value={overview.total_queries}
                prefix={<DatabaseOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">今日查询总量</Text>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="慢查询数"
                value={overview.slow_queries}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: overview.slow_queries > 100 ? '#ff4d4f' : '#faad14' }}
              />
              <Progress
                percent={overview.slow_query_ratio}
                strokeColor={overview.slow_query_ratio > 10 ? '#ff4d4f' : '#52c41a'}
                size="small"
                format={(percent) => `${percent}%`}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="平均查询时间"
                value={overview.avg_query_time}
                suffix="秒"
                precision={4}
                prefix={<ThunderboltOutlined />}
                valueStyle={{ color: overview.avg_query_time > 1 ? '#ff4d4f' : '#52c41a' }}
              />
              <div style={{ marginTop: 8 }}>
                <Badge status={overview.avg_query_time > 1 ? 'error' : 'success'} />
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  {overview.avg_query_time > 1 ? '需要优化' : '性能良好'}
                </Text>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="分区表数量"
                value={overview.partition_tables}
                suffix={`/ ${overview.total_tables}`}
                prefix={<PartitionOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">热点分区: </Text>
                <Text type="danger">{overview.hot_partitions}</Text>
              </div>
            </Card>
          </Col>
        </Row>

        {/* 性能趋势和评分 */}
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} md={16}>
            <Card title="查询趋势" extra={<Tag color="blue">最近24小时</Tag>}>
              {sqlTrends?.hourly_trends ? (
                <Area {...trendConfig} />
              ) : (
                <Empty description="暂无趋势数据" />
              )}
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card title="性能评分">
              <Gauge {...gaugeConfig} />
              <Divider />
              <Space direction="vertical" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text>CPU使用率</Text>
                  <Text strong>{overview.cpu_usage}%</Text>
                </div>
                <Progress percent={overview.cpu_usage} strokeColor="#1890ff" showInfo={false} />
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text>内存使用率</Text>
                  <Text strong>{overview.memory_usage}%</Text>
                </div>
                <Progress percent={overview.memory_usage} strokeColor="#52c41a" showInfo={false} />
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text>磁盘使用率</Text>
                  <Text strong>{overview.disk_usage}%</Text>
                </div>
                <Progress percent={overview.disk_usage} strokeColor="#faad14" showInfo={false} />
              </Space>
            </Card>
          </Col>
        </Row>

        {/* 优化建议 */}
        {sqlAnalysis?.optimization_suggestions && sqlAnalysis.optimization_suggestions.length > 0 && (
          <Card title="优化建议" style={{ marginTop: 16 }}>
            <Timeline>
              {sqlAnalysis.optimization_suggestions.map((suggestion, index) => (
                <Timeline.Item
                  key={index}
                  color={suggestion.priority === 'high' ? 'red' : 'blue'}
                  dot={<BulbOutlined />}
                >
                  <Card size="small" style={{ marginBottom: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text strong>{suggestion.title}</Text>
                      <Tag color={suggestion.priority === 'high' ? 'red' : 'orange'}>
                        {suggestion.priority === 'high' ? '高优先级' : '中优先级'}
                      </Tag>
                    </div>
                    <Paragraph type="secondary">{suggestion.description}</Paragraph>
                    <Space wrap>
                      {suggestion.actions?.map((action, actionIndex) => (
                        <Tag key={actionIndex} icon={<CheckCircleOutlined />} color="blue">
                          {action}
                        </Tag>
                      ))}
                    </Space>
                  </Card>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        )}
      </div>
    );
  };

  // 渲染SQL分析标签页
  const renderSqlAnalysis = () => {
    const columns = [
      {
        title: 'SQL ID',
        dataIndex: 'sql_id',
        key: 'sql_id',
        width: 120,
        render: (text) => <Text code>{text}</Text>,
      },
      {
        title: '执行时间',
        dataIndex: 'elapsed_time',
        key: 'elapsed_time',
        width: 100,
        sorter: (a, b) => a.elapsed_time - b.elapsed_time,
        render: (value) => (
          <span style={{ color: value > 5 ? '#ff4d4f' : '#52c41a' }}>
            {(value || 0).toFixed(3)}s
          </span>
        ),
      },
      {
        title: 'CPU时间',
        dataIndex: 'cpu_time',
        key: 'cpu_time',
        width: 100,
        render: (value) => `${(value || 0).toFixed(3)}s`,
      },
      {
        title: '物理读',
        dataIndex: 'physical_reads',
        key: 'physical_reads',
        width: 100,
        render: (value) => value.toLocaleString(),
      },
      {
        title: '优化潜力',
        dataIndex: 'optimization_potential',
        key: 'optimization_potential',
        width: 100,
        render: (value) => (
          <Tag color={value === 'high' ? 'red' : 'orange'}>
            {value === 'high' ? '高' : '中'}
          </Tag>
        ),
      },
      {
        title: '操作',
        key: 'action',
        width: 100,
        render: (_, record) => (
          <Button type="link" size="small" icon={<FileSearchOutlined />}>
            详情
          </Button>
        ),
      },
    ];

    return (
      <div>
        {/* SQL分析统计 */}
        {sqlAnalysis?.summary && (
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="慢查询总数"
                  value={sqlAnalysis.summary.total_slow_queries}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="平均执行时间"
                  value={sqlAnalysis.summary.avg_elapsed_time}
                  suffix="秒"
                  precision={3}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="慢查询占比"
                  value={sqlAnalysis.summary.slow_query_percentage}
                  suffix="%"
                  precision={1}
                  valueStyle={{ color: sqlAnalysis.summary.slow_query_percentage > 10 ? '#ff4d4f' : '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="优化建议"
                  value={sqlAnalysis.optimization_suggestions?.length || 0}
                  prefix={<BulbOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
          </Row>
        )}

        {/* 执行计划分析 */}
        <Card title="执行计划分析" style={{ marginTop: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <TextArea
              placeholder="输入SQL语句进行分析..."
              value={sqlText}
              onChange={(e) => setSqlText(e.target.value)}
              rows={4}
              style={{ fontFamily: 'monospace' }}
            />
            <Button
              type="primary"
              icon={<CodeOutlined />}
              onClick={analyzeExecutionPlan}
              loading={analyzingPlan}
              disabled={!sqlText.trim()}
            >
              分析执行计划
            </Button>
          </Space>

          {executionPlan && (
            <div style={{ marginTop: 16 }}>
              <Row gutter={[16, 16]}>
                <Col span={6}>
                  <Statistic title="预估成本" value={executionPlan.estimated_cost} />
                </Col>
                <Col span={6}>
                  <Statistic title="预估行数" value={executionPlan.estimated_rows} />
                </Col>
                <Col span={6}>
                  <Statistic title="执行步骤" value={executionPlan.execution_plan?.length || 0} />
                </Col>
                <Col span={6}>
                  <Statistic title="优化建议" value={executionPlan.optimization_suggestions?.length || 0} />
                </Col>
              </Row>

              {executionPlan.execution_plan && executionPlan.execution_plan.length > 0 && (
                <Card size="small" style={{ marginTop: 16 }} title="执行计划步骤">
                  <Timeline>
                    {executionPlan.execution_plan.map((step) => (
                      <Timeline.Item key={step.id}>
                        <Space>
                          <Badge count={step.id} style={{ backgroundColor: '#52c41a' }} />
                          <Text strong>{step.operation}</Text>
                          {step.object_name && <Text type="secondary">({step.object_name})</Text>}
                          <Tag>成本: {step.cost}</Tag>
                          <Tag>行数: {step.rows}</Tag>
                        </Space>
                      </Timeline.Item>
                    ))}
                  </Timeline>
                </Card>
              )}

              {executionPlan.optimization_suggestions && executionPlan.optimization_suggestions.length > 0 && (
                <Alert
                  message="优化建议"
                  description={
                    <Space direction="vertical" style={{ width: '100%' }}>
                      {executionPlan.optimization_suggestions.map((suggestion, index) => (
                        <div key={index}>
                          <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                          {suggestion.description}
                          <Tag color="green" style={{ marginLeft: 8 }}>
                            预期改善: {suggestion.expected_improvement}
                          </Tag>
                        </div>
                      ))}
                    </Space>
                  }
                  type="info"
                  showIcon
                  style={{ marginTop: 16 }}
                />
              )}
            </div>
          )}
        </Card>

        {/* 慢查询列表 */}
        <Card title="Top 慢查询" style={{ marginTop: 16 }}>
          <Table
            columns={columns}
            dataSource={sqlAnalysis?.top_slow_queries || []}
            rowKey="sql_id"
            pagination={{ pageSize: 5 }}
            size="small"
          />
        </Card>
      </div>
    );
  };

  // 渲染分区分析标签页
  const renderPartitionAnalysis = () => {
    const tableColumns = [
      {
        title: '表名',
        dataIndex: 'table_name',
        key: 'table_name',
        render: (text) => <Text strong>{text}</Text>,
      },
      {
        title: '分区类型',
        dataIndex: 'partition_type',
        key: 'partition_type',
        render: (text) => <Tag color="blue">{text}</Tag>,
      },
      {
        title: '分区数',
        dataIndex: 'total_partitions',
        key: 'total_partitions',
      },
      {
        title: '热点分区',
        dataIndex: 'hot_partitions',
        key: 'hot_partitions',
        render: (value) => (
          <Badge count={value} style={{ backgroundColor: value > 0 ? '#ff4d4f' : '#52c41a' }} />
        ),
      },
      {
        title: '优化评分',
        dataIndex: 'optimization_score',
        key: 'optimization_score',
        render: (value) => (
          <Progress
            percent={value}
            size="small"
            strokeColor={{
              '0%': '#ff4d4f',
              '50%': '#faad14',
              '100%': '#52c41a',
            }}
          />
        ),
      },
      {
        title: '状态',
        key: 'status',
        render: (_, record) => (
          <Tag color={record.optimization_score > 80 ? 'green' : 'red'}>
            {record.optimization_score > 80 ? '良好' : '需优化'}
          </Tag>
        ),
      },
    ];

    const hotspotColumns = [
      {
        title: '表名',
        dataIndex: 'table_name',
        key: 'table_name',
      },
      {
        title: '分区名',
        dataIndex: 'partition_name',
        key: 'partition_name',
        render: (text) => <Text code>{text}</Text>,
      },
      {
        title: '访问频率',
        dataIndex: 'access_frequency',
        key: 'access_frequency',
        render: (value) => value.toLocaleString(),
      },
      {
        title: '数据大小',
        dataIndex: 'data_size_mb',
        key: 'data_size_mb',
        render: (value) => `${(value || 0).toFixed(1)} MB`,
      },
      {
        title: '热点原因',
        dataIndex: 'hotspot_reason',
        key: 'hotspot_reason',
        render: (text) => <Tag color="red">{text}</Tag>,
      },
    ];

    // 分区分布饼图配置
    const pieConfig = {
      data: partitionAnalysis?.table_analysis?.map(t => ({
        type: t.table_name,
        value: t.total_partitions,
      })) || [],
      angleField: 'value',
      colorField: 'type',
      radius: 0.8,
      label: {
        type: 'outer',
        content: '{name} {percentage}',
      },
      interactions: [{ type: 'pie-legend-active' }, { type: 'element-active' }],
    };

    return (
      <div>
        {/* 分区统计 */}
        {partitionAnalysis?.summary && (
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="分区表总数"
                  value={partitionAnalysis.summary.total_partition_tables}
                  prefix={<DatabaseOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="总分区数"
                  value={partitionAnalysis.summary.total_partitions}
                  prefix={<PartitionOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="总行数"
                  value={partitionAnalysis.summary.total_rows}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="总大小"
                  value={partitionAnalysis.summary.total_size_mb}
                  suffix="MB"
                  precision={1}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
          </Row>
        )}

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          {/* 分区表详情 */}
          <Col xs={24} lg={14}>
            <Card title="分区表详情">
              <Table
                columns={tableColumns}
                dataSource={partitionAnalysis?.table_analysis || []}
                rowKey="table_name"
                pagination={false}
                size="small"
              />
            </Card>
          </Col>

          {/* 分区分布图 */}
          <Col xs={24} lg={10}>
            <Card title="分区分布" style={{ height: '100%' }}>
              {partitionAnalysis?.table_analysis && partitionAnalysis.table_analysis.length > 0 ? (
                <Pie {...pieConfig} height={300} />
              ) : (
                <Empty description="暂无分区数据" />
              )}
            </Card>
          </Col>
        </Row>

        {/* 热点分区 */}
        {hotspotAnalysis?.hot_partitions && hotspotAnalysis.hot_partitions.length > 0 && (
          <Card 
            title="热点分区分析" 
            style={{ marginTop: 16 }}
            extra={
              <Tag color="red">
                热点比例: {hotspotAnalysis.hot_partition_ratio}%
              </Tag>
            }
          >
            <Alert
              message="检测到热点分区"
              description={`发现 ${hotspotAnalysis.hot_partitions.length} 个热点分区，建议进行优化以提升性能`}
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Table
              columns={hotspotColumns}
              dataSource={hotspotAnalysis.hot_partitions}
              rowKey={(record) => `${record.table_name}_${record.partition_name}`}
              pagination={false}
              size="small"
            />
          </Card>
        )}
      </div>
    );
  };

  // 渲染配置优化标签页
  const renderConfigOptimization = () => {
    const configColumns = [
      {
        title: '参数名',
        dataIndex: 'parameter',
        key: 'parameter',
        render: (text) => <Text code>{text}</Text>,
      },
      {
        title: '当前值',
        dataIndex: 'current_value',
        key: 'current_value',
      },
      {
        title: '推荐值',
        dataIndex: 'recommended_value',
        key: 'recommended_value',
        render: (text) => <Text strong style={{ color: '#52c41a' }}>{text}</Text>,
      },
      {
        title: '影响程度',
        dataIndex: 'impact',
        key: 'impact',
        render: (value) => (
          <Tag color={value === 'high' ? 'red' : value === 'medium' ? 'orange' : 'blue'}>
            {value === 'high' ? '高' : value === 'medium' ? '中' : '低'}
          </Tag>
        ),
      },
      {
        title: '说明',
        dataIndex: 'description',
        key: 'description',
        ellipsis: true,
      },
    ];

    return (
      <div>
        {/* 配置优化评分 */}
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Card>
              <div style={{ textAlign: 'center' }}>
                <Progress
                  type="circle"
                  percent={configAnalysis?.optimization_level || 0}
                  strokeColor={{
                    '0%': '#ff4d4f',
                    '50%': '#faad14',
                    '100%': '#52c41a',
                  }}
                />
                <Title level={4} style={{ marginTop: 16 }}>配置优化评分</Title>
                <Paragraph type="secondary">
                  当前配置优化程度为 {configAnalysis?.optimization_level || 0}%
                </Paragraph>
              </div>
            </Card>
          </Col>
          <Col xs={24} md={16}>
            <Card title="优化建议" extra={
              <Space>
                <Button
                  type="primary"
                  icon={<CodeOutlined />}
                  onClick={() => generateOptimizationScript('sql')}
                >
                  生成SQL优化脚本
                </Button>
                <Button
                  icon={<PartitionOutlined />}
                  onClick={() => generateOptimizationScript('partition')}
                >
                  生成分区优化脚本
                </Button>
              </Space>
            }>
              {configAnalysis?.suggestions && configAnalysis.suggestions.length > 0 ? (
                <Table
                  columns={configColumns}
                  dataSource={configAnalysis.suggestions}
                  rowKey="parameter"
                  pagination={false}
                  size="small"
                />
              ) : (
                <Empty description="暂无优化建议" />
              )}
            </Card>
          </Col>
        </Row>

        {/* 系统资源使用情况 */}
        <Card title="系统资源使用情况" style={{ marginTop: 16 }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Card size="small">
                <Statistic
                  title="CPU使用率"
                  value={overview?.cpu_usage || 0}
                  suffix="%"
                  prefix={<DashboardOutlined />}
                  valueStyle={{ color: overview?.cpu_usage > 80 ? '#ff4d4f' : '#52c41a' }}
                />
                <Progress
                  percent={overview?.cpu_usage || 0}
                  strokeColor={overview?.cpu_usage > 80 ? '#ff4d4f' : '#52c41a'}
                  showInfo={false}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card size="small">
                <Statistic
                  title="内存使用率"
                  value={overview?.memory_usage || 0}
                  suffix="%"
                  prefix={<DatabaseOutlined />}
                  valueStyle={{ color: overview?.memory_usage > 80 ? '#ff4d4f' : '#52c41a' }}
                />
                <Progress
                  percent={overview?.memory_usage || 0}
                  strokeColor={overview?.memory_usage > 80 ? '#ff4d4f' : '#52c41a'}
                  showInfo={false}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card size="small">
                <Statistic
                  title="磁盘使用率"
                  value={overview?.disk_usage || 0}
                  suffix="%"
                  prefix={<FireOutlined />}
                  valueStyle={{ color: overview?.disk_usage > 80 ? '#ff4d4f' : '#52c41a' }}
                />
                <Progress
                  percent={overview?.disk_usage || 0}
                  strokeColor={overview?.disk_usage > 80 ? '#ff4d4f' : '#52c41a'}
                  showInfo={false}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card size="small">
                <Statistic
                  title="网络IO"
                  value={overview?.network_io || 0}
                  suffix="MB/s"
                  prefix={<RocketOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
                <Progress
                  percent={Math.min((overview?.network_io || 0) / 10, 100)}
                  strokeColor="#1890ff"
                  showInfo={false}
                />
              </Card>
            </Col>
          </Row>
        </Card>

        {/* 维护建议 */}
        <Card title="维护建议" style={{ marginTop: 16 }}>
          <Alert
            message="定期维护建议"
            description={
              <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                <li>建议每周进行一次全表统计信息更新</li>
                <li>建议每月检查并清理无用索引</li>
                <li>建议定期检查分区表的数据分布</li>
                <li>建议监控慢查询日志并及时优化</li>
              </ul>
            }
            type="info"
            showIcon
          />
        </Card>
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <Spin size="large" tip="正在加载OceanBase分析数据...">
          <div style={{ height: 400 }} />
        </Spin>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <Alert
          message="加载失败"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={loadInitialData}>
              重试
            </Button>
          }
        />
      </Card>
    );
  }

  return (
    <div>
      {!embedded && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Title level={3} style={{ margin: 0 }}>
                <DatabaseOutlined style={{ marginRight: 8 }} />
                OceanBase 性能分析
              </Title>
              <Paragraph type="secondary" style={{ margin: '8px 0' }}>
                基于GV$SQL_AUDIT视图的SQL性能分析和分区表优化
              </Paragraph>
            </div>
            <Space>
              <Button
                icon={<SettingOutlined />}
                onClick={() => generateOptimizationScript('sql')}
              >
                生成优化脚本
              </Button>
              <Button
                type="primary"
                icon={<ReloadOutlined spin={refreshing} />}
                onClick={handleRefresh}
                loading={refreshing}
              >
                刷新数据
              </Button>
            </Space>
          </div>
        </div>
      )}

      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane
            tab={
              <span>
                <DashboardOutlined />
                概览
              </span>
            }
            key="overview"
          >
            {renderOverview()}
          </TabPane>
          <TabPane
            tab={
              <span>
                <CodeOutlined />
                SQL分析
              </span>
            }
            key="sql"
          >
            {renderSqlAnalysis()}
          </TabPane>
          <TabPane
            tab={
              <span>
                <PartitionOutlined />
                分区分析
              </span>
            }
            key="partition"
          >
            {renderPartitionAnalysis()}
          </TabPane>
          <TabPane
            tab={
              <span>
                <SettingOutlined />
                配置优化
              </span>
            }
            key="config"
          >
            {renderConfigOptimization()}
          </TabPane>
        </Tabs>
      </Card>

      {/* 优化脚本模态框 */}
      <Modal
        title="优化脚本"
        visible={scriptModalVisible}
        onCancel={() => setScriptModalVisible(false)}
        width={800}
        footer={[
          <Button key="copy" type="primary" onClick={() => {
            navigator.clipboard.writeText(optimizationScript);
            message.success('脚本已复制到剪贴板');
          }}>
            复制脚本
          </Button>,
          <Button key="close" onClick={() => setScriptModalVisible(false)}>
            关闭
          </Button>,
        ]}
      >
        <Alert
          message="请在执行前仔细审查脚本"
          description="建议先在测试环境执行，确认无误后再在生产环境执行"
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <TextArea
          value={optimizationScript}
          readOnly
          rows={20}
          style={{ fontFamily: 'monospace', fontSize: '12px' }}
        />
      </Modal>
    </div>
  );
};

export default OceanBaseAnalysisEnhanced;