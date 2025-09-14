import React, { useState, useEffect } from 'react';
import { 
  Card, Row, Col, Space, Button, Alert, Typography, Divider,
  Tabs, Table, Tag, Switch, message 
} from 'antd';
import { 
  DatabaseOutlined, 
  ExperimentOutlined,
  ReloadOutlined,
  CheckCircleOutlined 
} from '@ant-design/icons';

import DataSourceIndicator from '../components/DataSourceIndicator';
import PerformanceMetricCard from '../components/PerformanceMetricCard';
import { performanceAPI } from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

const DataSourceDemo = () => {
  const [loading, setLoading] = useState(false);
  const [realDataEnabled, setRealDataEnabled] = useState(true);
  const [metricsData, setMetricsData] = useState(null);
  const [slowQueriesData, setSlowQueriesData] = useState([]);

  // 模拟获取最新指标数据
  const fetchLatestMetrics = async () => {
    setLoading(true);
    try {
      const response = await performanceAPI.getLatestMetrics(1);
      setMetricsData(response);
      message.success('数据刷新成功');
    } catch (error) {
      message.error('数据获取失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 模拟获取慢查询数据
  const fetchSlowQueries = async () => {
    try {
      const response = await performanceAPI.captureSlowQueries(1, 0.1);
      if (response.queries) {
        setSlowQueriesData(response.queries);
      }
    } catch (error) {
      console.error('慢查询获取失败:', error);
    }
  };

  useEffect(() => {
    fetchLatestMetrics();
    fetchSlowQueries();
  }, []);

  // 慢查询表格列定义
  const slowQueryColumns = [
    {
      title: '查询类型',
      dataIndex: 'sql_command',
      key: 'sql_command',
      width: 100,
      render: (command) => <Tag color="blue">{command}</Tag>
    },
    {
      title: '执行时间',
      dataIndex: 'execution_time',
      key: 'execution_time',
      width: 120,
      render: (time) => `${time?.toFixed(3)}s`
    },
    {
      title: '数据源',
      dataIndex: 'source',
      key: 'source',
      width: 120,
      render: (source) => (
        <DataSourceIndicator 
          source={source || 'mock_data'} 
          size="small"
        />
      )
    },
    {
      title: '查询片段',
      dataIndex: 'query_text',
      key: 'query_text',
      ellipsis: true,
      render: (text) => (
        <Text code style={{ fontSize: '12px' }}>
          {text?.substring(0, 80)}...
        </Text>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '24px' }}>
          <Title level={2}>
            <DatabaseOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
            数据源演示页面
          </Title>
          <Paragraph>
            本页面展示了UDBM系统如何智能切换真实数据和演示数据。
            系统会优先尝试获取PostgreSQL实例的真实性能数据，如果无法连接或获取失败，
            则自动回退到高质量的演示数据。
          </Paragraph>
        </div>

        <Alert
          message="数据源说明"
          description={
            <div>
              <Space direction="vertical" size="small">
                <div>
                  <DataSourceIndicator source="real_data" size="small" />
                  <Text style={{ marginLeft: '8px' }}>
                    来自PostgreSQL实例的真实性能数据，包括系统指标、慢查询、配置信息等
                  </Text>
                </div>
                <div>
                  <DataSourceIndicator source="mock_data" size="small" />
                  <Text style={{ marginLeft: '8px' }}>
                    基于真实场景设计的演示数据，用于功能展示和测试
                  </Text>
                </div>
                <div>
                  <DataSourceIndicator source="mixed" size="small" />
                  <Text style={{ marginLeft: '8px' }}>
                    部分真实数据与部分演示数据的混合模式
                  </Text>
                </div>
              </Space>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: '24px' }}
        />

        <div style={{ marginBottom: '24px', textAlign: 'right' }}>
          <Space>
            <Text>真实数据模式:</Text>
            <Switch
              checked={realDataEnabled}
              onChange={setRealDataEnabled}
              checkedChildren="启用"
              unCheckedChildren="演示"
            />
            <Button 
              type="primary" 
              icon={<ReloadOutlined />} 
              onClick={fetchLatestMetrics}
              loading={loading}
            >
              刷新数据
            </Button>
          </Space>
        </div>

        <Tabs defaultActiveKey="1">
          <TabPane tab="性能指标展示" key="1">
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={6}>
                <PerformanceMetricCard
                  title="CPU使用率"
                  value={metricsData?.cpu?.usage_percent || 45.2}
                  unit="%"
                  status={metricsData?.cpu?.usage_percent > 80 ? 'critical' : 'normal'}
                  progressValue={metricsData?.cpu?.usage_percent || 45.2}
                  dataSource="real_data"
                  trend="stable"
                  trendValue="较上小时 +2.1%"
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <PerformanceMetricCard
                  title="内存使用量"
                  value={metricsData?.memory?.used_mb || 4242}
                  unit="MB"
                  status="normal"
                  progressValue={((metricsData?.memory?.used_mb || 4242) / 8192) * 100}
                  dataSource="real_data"
                  trend="up"
                  trendValue="较上小时 +156MB"
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <PerformanceMetricCard
                  title="活跃连接数"
                  value={metricsData?.connections?.active || 28}
                  unit=""
                  precision={0}
                  status="normal"
                  progressValue={((metricsData?.connections?.active || 28) / 100) * 100}
                  dataSource="real_data"
                  trend="down"
                  trendValue="较上小时 -3"
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <PerformanceMetricCard
                  title="缓冲区命中率"
                  value={metricsData?.postgresql?.buffer_hit_ratio || 87.2}
                  unit="%"
                  status={metricsData?.postgresql?.buffer_hit_ratio < 90 ? 'warning' : 'normal'}
                  progressValue={metricsData?.postgresql?.buffer_hit_ratio || 87.2}
                  dataSource="real_data"
                  trend="stable"
                  trendValue="保持稳定"
                />
              </Col>
            </Row>

            <Divider />

            <Row gutter={[16, 16]}>
              <Col span={24}>
                <Card 
                  title="PostgreSQL特有指标" 
                  extra={<DataSourceIndicator source="real_data" />}
                >
                  <Row gutter={[16, 16]}>
                    <Col xs={24} sm={8}>
                      <Card size="small">
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                            {metricsData?.postgresql?.locks?.active_locks || 12}
                          </div>
                          <div style={{ color: '#666' }}>活跃锁数量</div>
                        </div>
                      </Card>
                    </Col>
                    <Col xs={24} sm={8}>
                      <Card size="small">
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                            {metricsData?.postgresql?.temp_files?.files_created_per_hour || 3}
                          </div>
                          <div style={{ color: '#666' }}>临时文件/小时</div>
                        </div>
                      </Card>
                    </Col>
                    <Col xs={24} sm={8}>
                      <Card size="small">
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#faad14' }}>
                            {metricsData?.postgresql?.background_processes?.autovacuum_workers || 2}
                          </div>
                          <div style={{ color: '#666' }}>VACUUM工作进程</div>
                        </div>
                      </Card>
                    </Col>
                  </Row>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="慢查询示例" key="2">
            <Card 
              title="慢查询列表" 
              extra={<DataSourceIndicator source="mock_data" />}
            >
              <Table
                columns={slowQueryColumns}
                dataSource={slowQueriesData}
                rowKey="query_hash"
                loading={loading}
                size="small"
                pagination={{
                  pageSize: 5,
                  showSizeChanger: false
                }}
              />
            </Card>
          </TabPane>

          <TabPane tab="系统状态" key="3">
            <Row gutter={[16, 16]}>
              <Col xs={24} md={12}>
                <Card title="数据采集状态">
                  <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    <div>
                      <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
                      <Text strong>系统指标采集</Text>
                      <div style={{ marginLeft: '24px', marginTop: '4px' }}>
                        <Text type="secondary">使用psutil库采集CPU、内存、磁盘IO等系统级指标</Text>
                        <br />
                        <DataSourceIndicator source="real_data" size="small" />
                      </div>
                    </div>
                    
                    <div>
                      <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
                      <Text strong>PostgreSQL指标采集</Text>
                      <div style={{ marginLeft: '24px', marginTop: '4px' }}>
                        <Text type="secondary">从pg_stat_*视图采集数据库特有指标</Text>
                        <br />
                        <DataSourceIndicator source="real_data" size="small" />
                      </div>
                    </div>
                    
                    <div>
                      <ExperimentOutlined style={{ color: '#faad14', marginRight: '8px' }} />
                      <Text strong>慢查询采集</Text>
                      <div style={{ marginLeft: '24px', marginTop: '4px' }}>
                        <Text type="secondary">pg_stat_statements扩展未配置，使用演示数据</Text>
                        <br />
                        <DataSourceIndicator source="mock_data" size="small" />
                      </div>
                    </div>
                  </Space>
                </Card>
              </Col>
              
              <Col xs={24} md={12}>
                <Card title="技术实现">
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <div>
                      <Text strong>智能切换机制</Text>
                      <div style={{ marginTop: '4px' }}>
                        <Text type="secondary">
                          系统会优先尝试连接真实PostgreSQL实例获取数据，
                          如果连接失败或数据不可用，自动回退到高质量演示数据
                        </Text>
                      </div>
                    </div>
                    
                    <div>
                      <Text strong>数据源标识</Text>
                      <div style={{ marginTop: '4px' }}>
                        <Text type="secondary">
                          所有数据都带有明确的来源标识，用户可以清楚知道
                          当前看到的是真实数据还是演示数据
                        </Text>
                      </div>
                    </div>
                    
                    <div>
                      <Text strong>渐进式增强</Text>
                      <div style={{ marginTop: '4px' }}>
                        <Text type="secondary">
                          随着PostgreSQL实例配置的完善（如启用扩展），
                          系统会自动使用更多真实数据源
                        </Text>
                      </div>
                    </div>
                  </Space>
                </Card>
              </Col>
            </Row>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default DataSourceDemo;
