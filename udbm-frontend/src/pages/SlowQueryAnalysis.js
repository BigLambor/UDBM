import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Select, Input, Space, Tag, Progress,
  Modal, Form, Alert, Spin, Tooltip, Statistic, Row, Col,
  Tabs, Descriptions, Typography, Divider
} from 'antd';
import {
  SearchOutlined, DatabaseOutlined, ClockCircleOutlined,
  BarChartOutlined, ThunderboltOutlined, ReloadOutlined,
  PlayCircleOutlined, FileTextOutlined, BulbOutlined,
  WarningOutlined, CheckCircleOutlined, SyncOutlined
} from '@ant-design/icons';
import { Bar, Column } from '@ant-design/charts';

import { performanceAPI } from '../services/api';
import DatabaseSelector from '../components/DatabaseSelector';
import DataSourceIndicator from '../components/DataSourceIndicator';

const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;
const { Title, Text, Paragraph } = Typography;

const SlowQueryAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [selectedDatabaseType, setSelectedDatabaseType] = useState('all');
  const [slowQueries, setSlowQueries] = useState([]);
  const [queryPatterns, setQueryPatterns] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [databases, setDatabases] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisModalVisible, setAnalysisModalVisible] = useState(false);
  const [selectedQuery, setSelectedQuery] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // 获取数据库列表
  useEffect(() => {
    fetchDatabases();
  }, []);

  // 获取慢查询数据
  useEffect(() => {
    if (selectedDatabase) {
      fetchSlowQueries();
      fetchQueryPatterns();
      fetchStatistics();
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

  const fetchSlowQueries = async () => {
    setLoading(true);
    try {
      const response = await performanceAPI.getSlowQueries(selectedDatabase.id);
      setSlowQueries(response || []);
    } catch (error) {
      console.error('获取慢查询失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchQueryPatterns = async () => {
    try {
      const response = await performanceAPI.getQueryPatterns(selectedDatabase.id);
      setQueryPatterns(response);
    } catch (error) {
      console.error('获取查询模式失败:', error);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await performanceAPI.getPerformanceStatistics(selectedDatabase.id);
      setStatistics(response);
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([
      fetchSlowQueries(),
      fetchQueryPatterns(),
      fetchStatistics()
    ]);
    setRefreshing(false);
  };

  const handleAnalyzeQuery = async (query) => {
    setAnalyzing(true);
    try {
      const response = await performanceAPI.analyzeQuery({
        query_text: query.query_text,
        execution_time: query.execution_time,
        rows_examined: query.rows_examined
      });
      setAnalysisResult(response);
      setSelectedQuery(query);
      setAnalysisModalVisible(true);
    } catch (error) {
      console.error('分析查询失败:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleCaptureSlowQueries = async () => {
    try {
      await performanceAPI.captureSlowQueries(selectedDatabase.id);
      await fetchSlowQueries();
    } catch (error) {
      console.error('捕获慢查询失败:', error);
    }
  };

  const getExecutionTimeColor = (time) => {
    if (time >= 10) return '#f5222e';
    if (time >= 5) return '#faad14';
    if (time >= 1) return '#52c41a';
    return '#1890ff';
  };

  const getImpactLevel = (score) => {
    if (score >= 80) return { level: '高', color: 'red' };
    if (score >= 60) return { level: '中', color: 'orange' };
    if (score >= 40) return { level: '低', color: 'blue' };
    return { level: '极低', color: 'green' };
  };

  // 慢查询表格列配置
  const columns = [
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
      title: '执行时间',
      dataIndex: 'execution_time',
      key: 'execution_time',
      width: 120,
      sorter: (a, b) => a.execution_time - b.execution_time,
      render: (time) => (
        <span style={{ color: getExecutionTimeColor(time) }}>
          <ClockCircleOutlined style={{ marginRight: 4 }} />
          {time ? time.toFixed(3) : 0}s
        </span>
      )
    },
    {
      title: '检查行数',
      dataIndex: 'rows_examined',
      key: 'rows_examined',
      width: 100,
      sorter: (a, b) => a.rows_examined - b.rows_examined,
      render: (rows) => rows?.toLocaleString() || '-'
    },
    {
      title: '返回行数',
      dataIndex: 'rows_sent',
      key: 'rows_sent',
      width: 100,
      sorter: (a, b) => a.rows_sent - b.rows_sent,
      render: (rows) => rows?.toLocaleString() || '-'
    },
    {
      title: 'SQL命令',
      dataIndex: 'sql_command',
      key: 'sql_command',
      width: 100,
      render: (command) => <Tag color="blue">{command}</Tag>
    },
    {
      title: '数据源',
      dataIndex: 'source',
      key: 'source',
      width: 100,
      render: (source) => (
        <DataSourceIndicator 
          source={source} 
          size="small"
          showText={false}
        />
      )
    },
    {
      title: '查询时间',
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
          <Tooltip title="分析查询">
            <Button
              type="text"
              size="small"
              icon={<BulbOutlined />}
              onClick={() => handleAnalyzeQuery(record)}
              loading={analyzing}
            />
          </Tooltip>
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<FileTextOutlined />}
              onClick={() => {
                setSelectedQuery(record);
                setAnalysisModalVisible(true);
              }}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // 查询模式图表配置
  const patternChartConfig = {
    data: queryPatterns?.most_common_patterns || [],
    xField: 'pattern',
    yField: 'count',
    height: 300,
    color: ({ pattern }) => {
      // 使用更现代的渐变色系，与页面整体风格保持一致
      const colors = [
        '#4A90E2', // 主蓝色
        '#50C878', // 绿色
        '#FFB84D', // 橙色
        '#E74C3C', // 红色
        '#9B59B6', // 紫色
        '#1ABC9C', // 青色
        '#F39C12', // 黄色
        '#34495E'  // 深灰色
      ];
      const data = queryPatterns?.most_common_patterns || [];
      const index = data.findIndex(p => p.pattern === pattern);
      return colors[index % colors.length];
    },
    columnWidthRatio: 0.5,
    maxColumnWidth: 50,
    minColumnWidth: 25,
    columnStyle: {
      radius: [6, 6, 0, 0],
      fill: ({ pattern }) => {
        // 添加渐变效果
        const colors = [
          'l(270) 0:#4A90E2 1:#6BB6FF',
          'l(270) 0:#50C878 1:#7ED321',
          'l(270) 0:#FFB84D 1:#F5A623',
          'l(270) 0:#E74C3C 1:#FF6B6B',
          'l(270) 0:#9B59B6 1:#BB6BD9',
          'l(270) 0:#1ABC9C 1:#26D0CE',
          'l(270) 0:#F39C12 1:#FFA500',
          'l(270) 0:#34495E 1:#5D6D7E'
        ];
        const data = queryPatterns?.most_common_patterns || [];
        const index = data.findIndex(p => p.pattern === pattern);
        return colors[index % colors.length];
      },
      stroke: '#ffffff',
      lineWidth: 1
    },
    xAxis: {
      title: { 
        text: '查询模式',
        style: {
          fontSize: 13,
          fontWeight: '500',
          fill: '#2c3e50'
        }
      },
      label: {
        rotate: 30,
        offset: 15,
        style: {
          textAlign: 'start',
          fontSize: 11,
          fill: '#5a6c7d'
        },
        formatter: (text) => {
          // 限制标签长度，确保可读性
          if (text.length > 10) {
            return text.substring(0, 10) + '...';
          }
          return text;
        }
      },
      line: {
        style: {
          stroke: '#e8e8e8',
          lineWidth: 1
        }
      },
      tickLine: {
        style: {
          stroke: '#e8e8e8',
          lineWidth: 1
        }
      }
    },
    yAxis: {
      title: { 
        text: '查询次数',
        style: {
          fontSize: 13,
          fontWeight: '500',
          fill: '#2c3e50'
        }
      },
      label: {
        style: {
          fontSize: 11,
          fill: '#5a6c7d'
        }
      },
      grid: {
        line: {
          style: {
            stroke: '#f5f5f5',
            lineWidth: 1,
            lineDash: [3, 3],
          }
        }
      },
      line: {
        style: {
          stroke: '#e8e8e8',
          lineWidth: 1
        }
      }
    },
    tooltip: {
      showTitle: false,
      customContent: (title, items) => {
        if (!items || items.length === 0) return '';
        const item = items[0];
        const data = item.data;
        return `
          <div style="padding: 12px; background: #fff; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <div style="font-weight: 600; color: #2c3e50; margin-bottom: 8px; font-size: 13px;">
              ${data.pattern}
            </div>
            <div style="color: #5a6c7d; font-size: 12px; line-height: 1.4;">
              <div>查询次数: <span style="color: #4A90E2; font-weight: 500;">${data.count}</span></div>
              <div>平均时间: <span style="color: #E74C3C; font-weight: 500;">${data.avg_time ? data.avg_time.toFixed(2) : 0}s</span></div>
              <div>影响分数: <span style="color: #9B59B6; font-weight: 500;">${data.impact_score || 0}</span></div>
            </div>
          </div>
        `;
      }
    },
    legend: false,
    interactions: [
      { type: 'active-region' },
      { type: 'element-highlight' }
    ],
    animation: {
      appear: {
        animation: 'scale-in-y',
        duration: 800,
        easing: 'easeOutCubic'
      }
    },
    autoFit: true,
    padding: [30, 30, 60, 80]
  };

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <h2 style={{ margin: 0 }}>
              <SearchOutlined style={{ marginRight: 8 }} />
              慢查询分析
            </h2>
            <p style={{ margin: '8px 0', color: '#666' }}>
              智能识别和分析不同数据库的慢查询，生成针对性优化建议
            </p>
          </div>
          <Space>
            <Button
              icon={<SyncOutlined />}
              onClick={handleCaptureSlowQueries}
              disabled={!selectedDatabase}
            >
              捕获慢查询
            </Button>
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

      {/* 统计信息卡片 */}
      {statistics && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="慢查询数量"
                value={statistics.slow_queries}
                suffix={`/ ${statistics.total_queries}`}
                valueStyle={{ color: '#f5222e' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="慢查询占比"
                value={statistics.slow_query_percentage}
                suffix="%"
                precision={2}
                valueStyle={{ color: statistics.slow_query_percentage > 5 ? '#f5222e' : '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="平均执行时间"
                value={statistics.avg_execution_time}
                suffix="s"
                precision={3}
                valueStyle={{ color: getExecutionTimeColor(statistics.avg_execution_time) }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="最大执行时间"
                value={statistics.max_execution_time}
                suffix="s"
                precision={3}
                valueStyle={{ color: '#f5222e' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Tabs defaultActiveKey="1">
        <TabPane tab="慢查询列表" key="1">
          <Card>
            <Table
              columns={columns}
              dataSource={slowQueries}
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

        <TabPane tab="查询模式分析" key="2">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={16}>
              <Card 
                title="常见查询模式" 
                style={{ height: '420px' }}
                bodyStyle={{ padding: '20px', height: '360px' }}
              >
                {queryPatterns?.most_common_patterns && queryPatterns.most_common_patterns.length > 0 ? (
                  <Column {...patternChartConfig} />
                ) : (
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center', 
                    height: '100%',
                    color: '#999',
                    fontSize: '14px'
                  }}>
                    暂无查询模式数据
                  </div>
                )}
              </Card>
            </Col>
            <Col xs={24} lg={8}>
              <Card 
                title="查询模式详情" 
                style={{ height: '420px' }}
                bodyStyle={{ padding: '16px', maxHeight: '360px', overflowY: 'auto' }}
              >
                {queryPatterns?.most_common_patterns && queryPatterns.most_common_patterns.length > 0 ? (
                  queryPatterns.most_common_patterns.map((pattern, index) => (
                    <Card
                      key={index}
                      size="small"
                      style={{ 
                        marginBottom: 12,
                        borderRadius: '8px',
                        border: '1px solid #f0f0f0',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
                      }}
                      bodyStyle={{ padding: '12px' }}
                      extra={
                        <Tag 
                          color={getImpactLevel(pattern.avg_time * 10).color}
                          style={{ borderRadius: '4px', fontSize: '11px' }}
                        >
                          影响: {getImpactLevel(pattern.avg_time * 10).level}
                        </Tag>
                      }
                    >
                      <div style={{ 
                        fontSize: '13px', 
                        color: '#2c3e50',
                        fontWeight: '500',
                        marginBottom: '8px',
                        lineHeight: '1.4'
                      }}>
                        {pattern.pattern}
                      </div>
                      <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        fontSize: '12px'
                      }}>
                        <span style={{ color: '#5a6c7d' }}>
                          <Text strong style={{ color: '#4A90E2' }}>{pattern.count}</Text> 次查询
                        </span>
                        <span style={{ color: '#5a6c7d' }}>
                          平均 <Text strong style={{ color: getExecutionTimeColor(pattern.avg_time) }}>
                            {pattern.avg_time ? pattern.avg_time.toFixed(2) : 0}s
                          </Text>
                        </span>
                      </div>
                      {pattern.impact_score && (
                        <div style={{ 
                          marginTop: '6px',
                          fontSize: '11px',
                          color: '#7f8c8d'
                        }}>
                          影响分数: <Text strong style={{ color: '#9B59B6' }}>
                            {pattern.impact_score}
                          </Text>
                        </div>
                      )}
                    </Card>
                  ))
                ) : (
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center', 
                    height: '100%',
                    color: '#999',
                    fontSize: '14px'
                  }}>
                    暂无查询模式详情
                  </div>
                )}
              </Card>
            </Col>
          </Row>

          <Card title="热点表分析" style={{ marginTop: 16 }}>
            <Row gutter={[16, 16]}>
              {queryPatterns?.top_tables?.map((table, index) => (
                <Col xs={24} sm={12} md={8} key={index}>
                  <Card size="small">
                    <Statistic
                      title={table.table}
                      value={table.query_count}
                      suffix="次查询"
                      valueStyle={{ color: '#1890ff' }}
                    />
                    <div style={{ marginTop: 8 }}>
                      平均执行时间: <Text strong style={{ color: getExecutionTimeColor(table.avg_time) }}>
                        {table.avg_time ? table.avg_time.toFixed(2) : 0}s
                      </Text>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        </TabPane>
      </Tabs>

      {/* 查询分析模态框 */}
      <Modal
        title="查询性能分析"
        open={analysisModalVisible}
        onCancel={() => setAnalysisModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setAnalysisModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {selectedQuery && (
          <div>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Descriptions title="查询基本信息" size="small" column={2}>
                <Descriptions.Item label="执行时间">
                  <Text strong style={{ color: getExecutionTimeColor(selectedQuery.execution_time) }}>
                    {selectedQuery.execution_time ? selectedQuery.execution_time.toFixed(3) : 0}s
                  </Text>
                </Descriptions.Item>
                <Descriptions.Item label="检查行数">
                  {selectedQuery.rows_examined?.toLocaleString() || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="返回行数">
                  {selectedQuery.rows_sent?.toLocaleString() || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="SQL命令">
                  <Tag color="blue">{selectedQuery.sql_command}</Tag>
                </Descriptions.Item>
              </Descriptions>
            </Card>

            <Card size="small" style={{ marginBottom: 16 }}>
              <Title level={5}>原始查询</Title>
              <TextArea
                value={selectedQuery.query_text}
                readOnly
                rows={4}
                style={{ fontFamily: 'monospace', fontSize: '12px' }}
              />
            </Card>

            {analysisResult && (
              <div>
                <Card size="small" style={{ marginBottom: 16 }}>
                  <Title level={5}>性能分析结果</Title>
                  <Row gutter={[16, 16]}>
                    <Col xs={12}>
                      <Statistic
                        title="查询复杂度评分"
                        value={analysisResult.query_complexity_score}
                        suffix="/100"
                        valueStyle={{
                          color: analysisResult.query_complexity_score > 70 ? '#f5222e' : '#52c41a'
                        }}
                      />
                    </Col>
                    <Col xs={12}>
                      <Statistic
                        title="执行效率评分"
                        value={analysisResult.efficiency_score}
                        suffix="/100"
                        valueStyle={{
                          color: analysisResult.efficiency_score < 70 ? '#f5222e' : '#52c41a'
                        }}
                      />
                    </Col>
                  </Row>
                </Card>

                <Card size="small">
                  <Title level={5}>优化建议</Title>
                  {analysisResult.suggestions.map((suggestion, index) => (
                    <Alert
                      key={index}
                      message={suggestion.description}
                      description={`影响程度: ${suggestion.impact} | 预期改善: ${suggestion.estimated_improvement}`}
                      type={suggestion.impact === 'high' ? 'error' : suggestion.impact === 'medium' ? 'warning' : 'info'}
                      showIcon
                      style={{ marginBottom: 8 }}
                    />
                  ))}
                </Card>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default SlowQueryAnalysis;
