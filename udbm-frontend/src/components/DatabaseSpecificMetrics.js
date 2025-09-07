import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Statistic, Progress, Alert, Tabs, Table, Tag,
  Button, Space, Modal, Form, Input, Select as AntSelect, message,
  Descriptions, Tooltip, Badge, Empty
} from 'antd';
import {
  DatabaseOutlined, BarChartOutlined, ThunderboltOutlined,
  ToolOutlined, SettingOutlined, TableOutlined, ClockCircleOutlined,
  CheckCircleOutlined, WarningOutlined, AlertOutlined
} from '@ant-design/icons';
import { Line, Bar } from '@ant-design/charts';

const { TabPane } = Tabs;
const { Option } = AntSelect;

// PostgreSQL 特性组件
const PostgreSQLMetrics = ({ database, dashboardData, postgresInsights, tableHealth, vacuumStrategy, configAnalysis }) => {
  const [vacuumModalVisible, setVacuumModalVisible] = useState(false);
  const [analyzeModalVisible, setAnalyzeModalVisible] = useState(false);
  const [reindexModalVisible, setReindexModalVisible] = useState(false);

  const getHealthStatusColor = (score) => {
    if (score >= 90) return '#52c41a';
    if (score >= 75) return '#faad14';
    return '#f5222e';
  };

  // 缓冲区命中率图表配置
  const bufferHitRatioChartConfig = {
    data: dashboardData?.time_series_data?.metrics || [],
    xField: 'timestamp',
    yField: 'buffer_hit_ratio',
    smooth: true,
    color: '#1890ff',
    xAxis: {
      title: { text: '时间' },
      label: {
        formatter: (text) => new Date(text).toLocaleTimeString()
      }
    },
    yAxis: {
      title: { text: '缓冲区命中率 (%)' },
      min: 0,
      max: 100
    }
  };

  return (
    <div>
      {/* PostgreSQL 核心指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={8}>
          <Card>
            <Statistic
              title="PostgreSQL性能评分"
              value={postgresInsights?.performance_score || 0}
              suffix="/100"
              valueStyle={{ color: getHealthStatusColor(postgresInsights?.performance_score || 0) }}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card>
            <Statistic
              title="缓冲区命中率"
              value={dashboardData?.current_stats?.buffer_hit_ratio || 0}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{
                color: (dashboardData?.current_stats?.buffer_hit_ratio || 0) >= 90 ? '#52c41a' : '#faad14'
              }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card>
            <Statistic
              title="表膨胀比率"
              value={postgresInsights?.health_status?.table_bloat_ratio || 0}
              suffix="倍"
              prefix={<TableOutlined />}
              valueStyle={{
                color: (postgresInsights?.health_status?.table_bloat_ratio || 0) <= 1.5 ? '#52c41a' : '#f5222e'
              }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="1">
        <TabPane tab="PostgreSQL指标" key="1">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="缓冲区命中率趋势">
                <Line {...bufferHitRatioChartConfig} />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="PostgreSQL特有指标">
                {dashboardData?.current_stats && (
                  <Row gutter={[16, 16]}>
                    <Col xs={12}>
                      <Statistic
                        title="WAL缓冲区写入"
                        value={dashboardData.current_stats.wal_buffers_written || 0}
                        suffix="blocks/sec"
                        valueStyle={{ fontSize: '14px' }}
                      />
                    </Col>
                    <Col xs={12}>
                      <Statistic
                        title="活跃锁数量"
                        value={dashboardData.current_stats.active_locks || 0}
                        valueStyle={{ fontSize: '14px' }}
                      />
                    </Col>
                    <Col xs={12}>
                      <Statistic
                        title="临时文件创建"
                        value={dashboardData.current_stats.temp_files_created || 0}
                        suffix="files/hour"
                        valueStyle={{ fontSize: '14px' }}
                      />
                    </Col>
                    <Col xs={12}>
                      <Statistic
                        title="AutoVacuum工作进程"
                        value={dashboardData.current_stats.autovacuum_workers || 0}
                        valueStyle={{ fontSize: '14px' }}
                      />
                    </Col>
                  </Row>
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="表健康分析" key="2">
          <Card
            title="表健康状况"
            extra={
              <Space>
                <Button
                  type="primary"
                  icon={<ToolOutlined />}
                  onClick={() => setVacuumModalVisible(true)}
                >
                  创建VACUUM任务
                </Button>
                <Button
                  icon={<SettingOutlined />}
                  onClick={() => setAnalyzeModalVisible(true)}
                >
                  创建ANALYZE任务
                </Button>
              </Space>
            }
          >
            {tableHealth?.recommendations ? (
              <Table
                columns={[
                  { title: '表名', dataIndex: 'table', key: 'table' },
                  { title: '优先级', dataIndex: 'priority', key: 'priority', render: (priority) => <Tag color={priority === 'critical' ? 'red' : 'orange'}>{priority}</Tag> },
                  { title: '建议操作', dataIndex: 'action', key: 'action', render: (action) => <Tag color="geekblue">{action}</Tag> },
                  { title: '原因', dataIndex: 'reason', key: 'reason', ellipsis: true }
                ]}
                dataSource={tableHealth.recommendations}
                pagination={false}
                size="small"
                rowKey={(record, index) => index}
              />
            ) : (
              <Empty description="暂无表健康分析数据" />
            )}
          </Card>
        </TabPane>

        <TabPane tab="VACUUM策略" key="3">
          <Card title="VACUUM维护策略">
            {vacuumStrategy ? (
              <Row gutter={[16, 16]}>
                <Col xs={24} md={8}>
                  <Card size="small" title="紧急维护任务">
                    <Badge count={vacuumStrategy.immediate_actions?.length || 0} color="red">
                      <span>需要立即处理的表</span>
                    </Badge>
                    {vacuumStrategy.immediate_actions?.map((action, index) => (
                      <div key={index} style={{ marginTop: 8 }}>
                        <Tag color="red">{action.action}</Tag>
                        <span style={{ marginLeft: 8 }}>{action.table}</span>
                      </div>
                    ))}
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card size="small" title="定期维护任务">
                    <Badge count={vacuumStrategy.scheduled_maintenance?.length || 0} color="orange">
                      <span>定期维护的表</span>
                    </Badge>
                    {vacuumStrategy.scheduled_maintenance?.map((task, index) => (
                      <div key={index} style={{ marginTop: 8 }}>
                        <Tag color="orange">{task.action}</Tag>
                        <span style={{ marginLeft: 8 }}>{task.table}</span>
                      </div>
                    ))}
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card size="small" title="AutoVacuum配置">
                    <div style={{ fontSize: '12px' }}>
                      {vacuumStrategy.autovacuum_tuning && Object.entries(vacuumStrategy.autovacuum_tuning).map(([key, value]) => (
                        <div key={key} style={{ marginBottom: 4 }}>
                          <strong>{key}:</strong> {value}
                        </div>
                      ))}
                    </div>
                  </Card>
                </Col>
              </Row>
            ) : (
              <Empty description="暂无VACUUM策略数据" />
            )}
          </Card>
        </TabPane>

        <TabPane tab="配置优化" key="4">
          <Card title="PostgreSQL配置优化建议">
            {configAnalysis?.recommendations ? (
              <div>
                <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                  <Col xs={24} md={8}>
                    <Statistic
                      title="配置优化评分"
                      value={configAnalysis.optimization_score}
                      suffix="/100"
                      valueStyle={{
                        color: configAnalysis.optimization_score >= 80 ? '#52c41a' : '#faad14'
                      }}
                    />
                  </Col>
                  <Col xs={24} md={8}>
                    <Statistic
                      title="建议数量"
                      value={configAnalysis.recommendations.length}
                      prefix={<SettingOutlined />}
                    />
                  </Col>
                  <Col xs={24} md={8}>
                    <Statistic
                      title="高优先级建议"
                      value={configAnalysis.recommendations.filter(r => r.impact === 'high').length}
                      valueStyle={{ color: '#f5222e' }}
                    />
                  </Col>
                </Row>
                <Table
                  columns={[
                    { title: '参数', dataIndex: 'parameter', key: 'parameter' },
                    { title: '当前值', dataIndex: 'current_value', key: 'current_value' },
                    { title: '建议值', dataIndex: 'recommended_value', key: 'recommended_value', render: (text) => <Tag color="green">{text}</Tag> },
                    { title: '影响程度', dataIndex: 'impact', key: 'impact', render: (impact) => <Tag color={impact === 'high' ? 'red' : 'orange'}>{impact}</Tag> },
                    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true }
                  ]}
                  dataSource={configAnalysis.recommendations}
                  pagination={false}
                  size="small"
                  rowKey="parameter"
                />
              </div>
            ) : (
              <Empty description="暂无配置优化建议" />
            )}
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

// MySQL 特性组件
const MySQLMetrics = ({ database, dashboardData }) => {
  return (
    <div>
      <Alert
        message="MySQL 特性监控"
        description="MySQL特有的监控指标和功能即将推出，包括InnoDB缓冲池、主从延迟监控等。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="InnoDB缓冲池命中率"
              value={95.6}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="主从延迟"
              value={0.12}
              suffix="秒"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="表锁等待"
              value={0}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

// Oracle 特性组件
const OracleMetrics = ({ database, dashboardData }) => {
  return (
    <div>
      <Alert
        message="Oracle 特性监控"
        description="Oracle特有的监控指标和功能即将推出，包括SGA/PGA监控、AWR报告分析等。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="SGA命中率"
              value={98.2}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="PGA使用率"
              value={76.5}
              suffix="%"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="等待事件"
              value={3}
              prefix={<AlertOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

// SQL Server 特性组件
const SQLServerMetrics = ({ database, dashboardData }) => {
  return (
    <div>
      <Alert
        message="SQL Server 特性监控"
        description="SQL Server特有的监控指标和功能即将推出，包括缓冲区管理、索引碎片分析等。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="缓冲区命中率"
              value={94.8}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="锁等待时间"
              value={45}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card>
            <Statistic
              title="索引碎片率"
              value={12.3}
              suffix="%"
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

// 主组件
const DatabaseSpecificMetrics = ({ 
  database, 
  dashboardData,
  // PostgreSQL 特有数据
  postgresInsights,
  tableHealth,
  vacuumStrategy,
  configAnalysis
}) => {
  if (!database) {
    return (
      <Card>
        <Empty 
          description="请先选择一个数据库实例"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  const renderSpecificMetrics = () => {
    switch (database.type) {
      case 'postgresql':
        return (
          <PostgreSQLMetrics
            database={database}
            dashboardData={dashboardData}
            postgresInsights={postgresInsights}
            tableHealth={tableHealth}
            vacuumStrategy={vacuumStrategy}
            configAnalysis={configAnalysis}
          />
        );
      case 'mysql':
        return <MySQLMetrics database={database} dashboardData={dashboardData} />;
      case 'oracle':
        return <OracleMetrics database={database} dashboardData={dashboardData} />;
      case 'sqlserver':
        return <SQLServerMetrics database={database} dashboardData={dashboardData} />;
      default:
        return (
          <Card>
            <Alert
              message={`${database.type ? database.type.toUpperCase() : '未知类型'} 数据库监控`}
              description={`${database.type ? database.type.toUpperCase() : '未知类型'} 数据库的特有监控功能正在开发中，敬请期待。`}
              type="info"
              showIcon
            />
          </Card>
        );
    }
  };

  return (
    <div>
      <Card 
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <DatabaseOutlined />
            <span>{database.type ? database.type.toUpperCase() : '未知类型'} 特性监控</span>
            <Tag color="blue">{database.name}</Tag>
          </div>
        }
        style={{ marginTop: 16 }}
      >
        {renderSpecificMetrics()}
      </Card>
    </div>
  );
};

export default DatabaseSpecificMetrics;
