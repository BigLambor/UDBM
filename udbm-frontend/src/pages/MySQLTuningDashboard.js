import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Statistic, Progress, Alert, Tabs, Table, Tag,
  Button, Space, Modal, Form, Input, Select, message, Spin,
  Descriptions, Tooltip, Badge, Empty, Divider, Typography,
  Collapse, Steps
} from 'antd';
import {
  DatabaseOutlined, BarChartOutlined, ThunderboltOutlined,
  ToolOutlined, SettingOutlined, TableOutlined, ClockCircleOutlined,
  CheckCircleOutlined, WarningOutlined, AlertOutlined, SecurityScanOutlined,
  CloudServerOutlined, HddOutlined, SafetyOutlined, BackupOutlined,
  PartitionOutlined, ReloadOutlined, CopyOutlined, RocketOutlined,
  TrophyOutlined, FireOutlined, SyncOutlined
} from '@ant-design/icons';
import { Line, Bar, Pie } from '@ant-design/charts';

import { performanceAPI, databaseAPI } from '../services/api';
import DatabaseSelector from '../components/DatabaseSelector';

const { TabPane } = Tabs;
const { Option } = Select;
const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;
const { Step } = Steps;

const MySQLTuningDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [databases, setDatabases] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  
  // 分析数据状态
  const [configAnalysis, setConfigAnalysis] = useState(null);
  const [storageAnalysis, setStorageAnalysis] = useState(null);
  const [hardwareAnalysis, setHardwareAnalysis] = useState(null);
  const [securityAnalysis, setSecurityAnalysis] = useState(null);
  const [replicationAnalysis, setReplicationAnalysis] = useState(null);
  const [partitionAnalysis, setPartitionAnalysis] = useState(null);
  const [backupAnalysis, setBackupAnalysis] = useState(null);
  const [optimizationSummary, setOptimizationSummary] = useState(null);
  const [performanceInsights, setPerformanceInsights] = useState(null);
  
  // UI状态
  const [tuningScript, setTuningScript] = useState('');
  const [scriptModalVisible, setScriptModalVisible] = useState(false);
  const [comprehensiveModalVisible, setComprehensiveModalVisible] = useState(false);

  // 加载数据库列表
  const loadDatabases = async () => {
    try {
      const data = await databaseAPI.getDatabases();
      const mysqlDatabases = data.filter(db => db.db_type === 'mysql');
      setDatabases(mysqlDatabases);
      if (mysqlDatabases.length > 0 && !selectedDatabase) {
        setSelectedDatabase(mysqlDatabases[0]);
      }
    } catch (error) {
      console.error('加载数据库列表失败:', error);
    }
  };

  // 加载所有分析数据
  const loadAllAnalysis = async () => {
    if (!selectedDatabase?.id) return;
    
    setLoading(true);
    try {
      // 并行加载所有分析
      const [
        config, storage, hardware, security, replication, 
        partition, backup, summary, insights
      ] = await Promise.all([
        performanceAPI.analyzeMySQLConfig(selectedDatabase.id).catch(() => null),
        performanceAPI.analyzeMySQLStorageEngine(selectedDatabase.id).catch(() => null),
        performanceAPI.analyzeMySQLHardware(selectedDatabase.id).catch(() => null),
        performanceAPI.analyzeMySQLSecurity(selectedDatabase.id).catch(() => null),
        performanceAPI.analyzeMySQLReplication(selectedDatabase.id).catch(() => null),
        performanceAPI.analyzeMySQLPartition(selectedDatabase.id).catch(() => null),
        performanceAPI.analyzeMySQLBackup(selectedDatabase.id).catch(() => null),
        performanceAPI.getMySQLOptimizationSummary(selectedDatabase.id).catch(() => null),
        performanceAPI.getMySQLPerformanceInsights(selectedDatabase.id).catch(() => null)
      ]);

      setConfigAnalysis(config);
      setStorageAnalysis(storage);
      setHardwareAnalysis(hardware);
      setSecurityAnalysis(security);
      setReplicationAnalysis(replication);
      setPartitionAnalysis(partition);
      setBackupAnalysis(backup);
      setOptimizationSummary(summary);
      setPerformanceInsights(insights);

    } catch (error) {
      console.error('加载分析数据失败:', error);
      message.error('加载分析数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 生成调优脚本
  const generateTuningScript = async (areas = ['config', 'storage', 'security']) => {
    if (!selectedDatabase?.id) return;
    
    try {
      setLoading(true);
      const scriptData = await performanceAPI.generateMySQLTuningScript(selectedDatabase.id, areas);
      setTuningScript(scriptData.tuning_script || '');
      setScriptModalVisible(true);
      message.success('调优脚本生成成功');
    } catch (error) {
      console.error('生成调优脚本失败:', error);
      message.error('生成调优脚本失败');
    } finally {
      setLoading(false);
    }
  };

  // 快速优化
  const performQuickOptimization = async (focusArea = 'performance') => {
    if (!selectedDatabase?.id) return;
    
    try {
      setLoading(true);
      const result = await performanceAPI.quickMySQLOptimization(selectedDatabase.id, focusArea);
      
      const focusAreaNames = {
        'performance': '性能',
        'security': '安全',
        'reliability': '可靠性'
      };
      
      Modal.info({
        title: `MySQL ${focusAreaNames[focusArea] || focusArea} 优化建议`,
        width: 800,
        content: (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>重点优化区域: </Text>
              <Tag color="blue">{result.focus_area}</Tag>
            </div>
            
            {result.quick_recommendations?.length > 0 ? (
              <div>
                <Title level={5}>快速建议:</Title>
                {result.quick_recommendations.map((rec, index) => (
                  <Card key={index} size="small" style={{ marginBottom: 8 }}>
                    <div style={{ marginBottom: 8 }}>
                      <Tag color={rec.impact === 'critical' ? 'red' : rec.impact === 'high' ? 'orange' : 'blue'}>
                        {rec.impact}
                      </Tag>
                      <Text strong>{rec.category}</Text>
                    </div>
                    <Paragraph>{rec.action}</Paragraph>
                    {rec.sql && (
                      <div style={{ 
                        fontFamily: 'monospace', 
                        backgroundColor: '#f5f5f5', 
                        padding: 8, 
                        borderRadius: 4,
                        fontSize: '12px'
                      }}>
                        {rec.sql}
                      </div>
                    )}
                    {rec.estimated_improvement && (
                      <div style={{ marginTop: 8, color: '#52c41a' }}>
                        <Text type="success">预期改善: {rec.estimated_improvement}</Text>
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            ) : (
              <Empty description="暂无快速建议" />
            )}
            
            {result.next_steps && (
              <div style={{ marginTop: 16 }}>
                <Title level={5}>后续步骤:</Title>
                <ul>
                  {result.next_steps.map((step, index) => (
                    <li key={index}>{step}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )
      });
    } catch (error) {
      console.error('快速优化失败:', error);
      message.error('快速优化失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDatabases();
  }, []);

  useEffect(() => {
    if (selectedDatabase) {
      loadAllAnalysis();
    }
  }, [selectedDatabase]);

  const getHealthStatusColor = (score) => {
    if (score >= 90) return '#52c41a';
    if (score >= 75) return '#faad14';
    return '#f5222e';
  };

  const getHealthStatusIcon = (status) => {
    switch (status) {
      case 'excellent': return <TrophyOutlined style={{ color: '#52c41a' }} />;
      case 'good': return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'fair': return <WarningOutlined style={{ color: '#faad14' }} />;
      case 'poor': return <AlertOutlined style={{ color: '#f5222e' }} />;
      case 'critical': return <FireOutlined style={{ color: '#f5222e' }} />;
      default: return <DatabaseOutlined />;
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>
        <DatabaseOutlined /> MySQL 性能调优中心
      </Title>
      
      {/* 数据库选择器 */}
      <Card style={{ marginBottom: 24 }}>
        <Row align="middle" gutter={16}>
          <Col>
            <Text strong>选择MySQL数据库:</Text>
          </Col>
          <Col flex="auto">
            <DatabaseSelector
              databases={databases}
              selectedDatabase={selectedDatabase}
              onDatabaseChange={setSelectedDatabase}
              databaseType="mysql"
            />
          </Col>
          <Col>
            <Button 
              type="primary" 
              icon={<SyncOutlined />} 
              onClick={loadAllAnalysis}
              loading={loading}
            >
              全面分析
            </Button>
          </Col>
        </Row>
      </Card>

      {!selectedDatabase ? (
        <Card>
          <Empty description="请选择一个MySQL数据库实例开始分析" />
        </Card>
      ) : (
        <Spin spinning={loading}>
          {/* 核心指标概览 */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} lg={6}>
              <Card>
                <Statistic
                  title="整体健康评分"
                  value={optimizationSummary?.overall_health_score || 0}
                  suffix="/100"
                  valueStyle={{ 
                    color: getHealthStatusColor(optimizationSummary?.overall_health_score || 0) 
                  }}
                  prefix={getHealthStatusIcon(performanceInsights?.health_status?.status)}
                />
              </Card>
            </Col>
            <Col xs={24} lg={6}>
              <Card>
                <Statistic
                  title="优化建议总数"
                  value={optimizationSummary?.optimization_statistics?.total_recommendations || 0}
                  suffix="条"
                  prefix={<ToolOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} lg={6}>
              <Card>
                <Statistic
                  title="高影响建议"
                  value={optimizationSummary?.optimization_statistics?.high_impact_recommendations || 0}
                  suffix="条"
                  prefix={<RocketOutlined />}
                  valueStyle={{ color: '#ff7a45' }}
                />
              </Card>
            </Col>
            <Col xs={24} lg={6}>
              <Card>
                <Statistic
                  title="安全问题"
                  value={optimizationSummary?.optimization_statistics?.critical_security_issues || 0}
                  suffix="个"
                  prefix={<SecurityScanOutlined />}
                  valueStyle={{ color: optimizationSummary?.optimization_statistics?.critical_security_issues > 0 ? '#f5222e' : '#52c41a' }}
                />
              </Card>
            </Col>
          </Row>

          {/* 快速操作按钮 */}
          <Card style={{ marginBottom: 24 }}>
            <Title level={4}>快速操作</Title>
            <Space wrap>
              <Button 
                type="primary" 
                icon={<ThunderboltOutlined />} 
                onClick={() => performQuickOptimization('performance')}
                loading={loading}
              >
                性能优化
              </Button>
              <Button 
                icon={<SecurityScanOutlined />} 
                onClick={() => performQuickOptimization('security')}
                loading={loading}
              >
                安全加固
              </Button>
              <Button 
                icon={<SafetyOutlined />} 
                onClick={() => performQuickOptimization('reliability')}
                loading={loading}
              >
                可靠性提升
              </Button>
              <Button 
                icon={<SettingOutlined />} 
                onClick={() => generateTuningScript()}
                loading={loading}
              >
                生成调优脚本
              </Button>
              <Button 
                icon={<SettingOutlined />} 
                onClick={() => generateTuningScript(['config', 'storage', 'security', 'replication'])}
                loading={loading}
              >
                完整调优脚本
              </Button>
            </Space>
          </Card>

          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            {/* 概览 */}
            <TabPane tab="概览" key="overview">
              <Row gutter={[16, 16]}>
                {/* 健康状态 */}
                <Col xs={24} lg={8}>
                  <Card title="系统健康状态">
                    {performanceInsights?.health_status ? (
                      <div>
                        <div style={{ textAlign: 'center', marginBottom: 16 }}>
                          {getHealthStatusIcon(performanceInsights.health_status.status)}
                          <div style={{ marginTop: 8 }}>
                            <Text strong>{performanceInsights.health_status.description}</Text>
                          </div>
                        </div>
                        <Progress 
                          percent={Math.round(performanceInsights.health_status.health_score)} 
                          strokeColor={getHealthStatusColor(performanceInsights.health_status.health_score)}
                          format={(percent) => `${percent}分`}
                        />
                        {performanceInsights.health_status.critical_issues > 0 && (
                          <Alert
                            message={`发现 ${performanceInsights.health_status.critical_issues} 个严重问题`}
                            type="error"
                            style={{ marginTop: 16 }}
                          />
                        )}
                      </div>
                    ) : (
                      <Empty description="暂无健康状态数据" />
                    )}
                  </Card>
                </Col>

                {/* 性能瓶颈 */}
                <Col xs={24} lg={8}>
                  <Card title="性能瓶颈">
                    {performanceInsights?.bottlenecks?.length > 0 ? (
                      <div>
                        {performanceInsights.bottlenecks.map((bottleneck, index) => (
                          <div key={index} style={{ marginBottom: 12 }}>
                            <div>
                              <Tag color={bottleneck.severity === 'high' ? 'red' : 'orange'}>
                                {bottleneck.severity}
                              </Tag>
                              <Text strong>{bottleneck.type}</Text>
                            </div>
                            <Paragraph style={{ marginTop: 4, marginBottom: 4 }}>
                              {bottleneck.description}
                            </Paragraph>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              影响: {bottleneck.impact}
                            </Text>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <Empty description="未发现明显瓶颈" />
                    )}
                  </Card>
                </Col>

                {/* 优化机会 */}
                <Col xs={24} lg={8}>
                  <Card title="优化机会">
                    {performanceInsights?.optimization_opportunities?.length > 0 ? (
                      <div>
                        {performanceInsights.optimization_opportunities.map((opportunity, index) => (
                          <div key={index} style={{ marginBottom: 12 }}>
                            <div>
                              <Tag color="green">{opportunity.type}</Tag>
                              <Text strong>{opportunity.title}</Text>
                            </div>
                            <Paragraph style={{ marginTop: 4, marginBottom: 4 }}>
                              {opportunity.description}
                            </Paragraph>
                            <div>
                              <Text type="success">收益: {opportunity.estimated_benefit}</Text>
                              <Text type="secondary" style={{ marginLeft: 16 }}>
                                难度: {opportunity.effort}
                              </Text>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <Empty description="暂无优化机会" />
                    )}
                  </Card>
                </Col>
              </Row>

              {/* 优化路线图 */}
              {optimizationSummary?.optimization_roadmap && (
                <Card title="优化路线图" style={{ marginTop: 16 }}>
                  <Steps direction="vertical" size="small">
                    <Step
                      title="即时行动"
                      status="process"
                      description={
                        <ul>
                          {optimizationSummary.optimization_roadmap.immediate_actions?.map((action, index) => (
                            <li key={index}>{action}</li>
                          ))}
                        </ul>
                      }
                    />
                    <Step
                      title="短期目标"
                      status="wait"
                      description={
                        <ul>
                          {optimizationSummary.optimization_roadmap.short_term_goals?.map((goal, index) => (
                            <li key={index}>{goal}</li>
                          ))}
                        </ul>
                      }
                    />
                    <Step
                      title="长期目标"
                      status="wait"
                      description={
                        <ul>
                          {optimizationSummary.optimization_roadmap.long_term_goals?.map((goal, index) => (
                            <li key={index}>{goal}</li>
                          ))}
                        </ul>
                      }
                    />
                  </Steps>
                </Card>
              )}
            </TabPane>

            {/* 配置优化 */}
            <TabPane tab="配置优化" key="config">
              <Card title="配置分析" extra={
                <Tag color={configAnalysis?.data_source === 'real_data' ? 'green' : 'blue'}>
                  {configAnalysis?.data_source === 'real_data' ? '真实数据' : '演示数据'}
                </Tag>
              }>
                {configAnalysis?.recommendations?.length > 0 ? (
                  <Table
                    dataSource={configAnalysis.recommendations}
                    columns={[
                      {
                        title: '参数',
                        dataIndex: 'parameter',
                        key: 'parameter',
                        render: (text) => <Text code>{text}</Text>
                      },
                      {
                        title: '当前值',
                        dataIndex: 'current_value',
                        key: 'current_value'
                      },
                      {
                        title: '建议值',
                        dataIndex: 'recommended_value',
                        key: 'recommended_value',
                        render: (text) => <Text strong style={{ color: '#1890ff' }}>{text}</Text>
                      },
                      {
                        title: '影响',
                        dataIndex: 'impact',
                        key: 'impact',
                        render: (impact) => (
                          <Tag color={impact === 'high' ? 'red' : impact === 'medium' ? 'orange' : 'blue'}>
                            {impact}
                          </Tag>
                        )
                      },
                      {
                        title: '描述',
                        dataIndex: 'description',
                        key: 'description',
                        ellipsis: true
                      }
                    ]}
                    pagination={false}
                    size="middle"
                    rowKey={(record, index) => index}
                  />
                ) : (
                  <Empty description="暂无配置建议" />
                )}
              </Card>
            </TabPane>

            {/* 存储引擎优化 */}
            <TabPane tab="存储引擎" key="storage">
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="InnoDB 优化">
                    {storageAnalysis?.innodb_optimization?.recommendations?.length > 0 ? (
                      <div>
                        {storageAnalysis.innodb_optimization.recommendations.map((rec, index) => (
                          <Card key={index} size="small" style={{ marginBottom: 8 }}>
                            <div>
                              <Tag color={rec.impact === 'high' ? 'red' : 'orange'}>{rec.impact}</Tag>
                              <Text strong>{rec.parameter}</Text>
                            </div>
                            <div style={{ marginTop: 8 }}>{rec.description}</div>
                            <div style={{ marginTop: 4, fontSize: '12px', color: '#666' }}>
                              {rec.current_value} → {rec.recommended_value}
                            </div>
                            {rec.estimated_improvement && (
                              <div style={{ marginTop: 4, color: '#52c41a' }}>
                                {rec.estimated_improvement}
                              </div>
                            )}
                          </Card>
                        ))}
                      </div>
                    ) : (
                      <Empty description="暂无InnoDB优化建议" />
                    )}
                  </Card>
                </Col>
                
                <Col xs={24} lg={12}>
                  <Card title="存储引擎建议">
                    {storageAnalysis?.engine_recommendations?.length > 0 ? (
                      <div>
                        {storageAnalysis.engine_recommendations.map((rec, index) => (
                          <Card key={index} size="small" style={{ marginBottom: 8 }}>
                            <div>
                              <Text strong>{rec.table_pattern}</Text>
                            </div>
                            <div style={{ marginTop: 8 }}>
                              <Tag color="blue">{rec.current_engine}</Tag>
                              <span> → </span>
                              <Tag color="green">{rec.recommended_engine}</Tag>
                            </div>
                            <div style={{ marginTop: 8, color: '#666' }}>
                              {rec.reason}
                            </div>
                            <div style={{ marginTop: 4, fontSize: '12px', color: '#999' }}>
                              迁移复杂度: {rec.migration_complexity}
                            </div>
                          </Card>
                        ))}
                      </div>
                    ) : (
                      <Empty description="暂无引擎迁移建议" />
                    )}
                  </Card>
                </Col>
              </Row>
            </TabPane>

            {/* 安全配置 */}
            <TabPane tab="安全配置" key="security">
              <Row gutter={[16, 16]}>
                {securityAnalysis && Object.entries(securityAnalysis).map(([category, data]) => (
                  <Col xs={24} lg={8} key={category}>
                    <Card title={category === 'user_security' ? '用户安全' : category === 'network_security' ? '网络安全' : '审计安全'}>
                      {data.recommendations?.length > 0 ? (
                        <div>
                          {data.recommendations.map((rec, index) => (
                            <Alert
                              key={index}
                              message={rec.issue}
                              description={
                                <div>
                                  <div>{rec.solution}</div>
                                  {rec.sql && (
                                    <div style={{ 
                                      marginTop: 8, 
                                      fontFamily: 'monospace', 
                                      backgroundColor: '#f5f5f5', 
                                      padding: 4, 
                                      borderRadius: 2,
                                      fontSize: '11px'
                                    }}>
                                      {rec.sql}
                                    </div>
                                  )}
                                </div>
                              }
                              type={rec.severity === 'high' ? 'error' : 'warning'}
                              style={{ marginBottom: 8 }}
                            />
                          ))}
                        </div>
                      ) : (
                        <Empty description="暂无安全建议" />
                      )}
                    </Card>
                  </Col>
                ))}
              </Row>
            </TabPane>

            {/* 分区表优化 */}
            <TabPane tab="分区优化" key="partition">
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="分区候选表">
                    {partitionAnalysis?.partition_candidates?.length > 0 ? (
                      <div>
                        {partitionAnalysis.partition_candidates.map((candidate, index) => (
                          <Card key={index} size="small" style={{ marginBottom: 8 }}>
                            <div>
                              <Text strong>{candidate.table_name}</Text>
                              <Tag color="blue" style={{ marginLeft: 8 }}>
                                {candidate.current_size_gb}GB
                              </Tag>
                            </div>
                            <div style={{ marginTop: 8 }}>
                              <Text>建议分区类型: </Text>
                              <Tag color="green">{candidate.recommended_partition_type}</Tag>
                            </div>
                            <div style={{ marginTop: 8 }}>
                              <Text>分区键: </Text>
                              <Text code>{candidate.recommended_partition_key}</Text>
                            </div>
                            <div style={{ marginTop: 8, color: '#666' }}>
                              {candidate.reason}
                            </div>
                            <div style={{ marginTop: 4, color: '#52c41a' }}>
                              {candidate.estimated_improvement}
                            </div>
                          </Card>
                        ))}
                      </div>
                    ) : (
                      <Empty description="暂无分区候选表" />
                    )}
                  </Card>
                </Col>
                
                <Col xs={24} lg={12}>
                  <Card title="分区维护">
                    {partitionAnalysis?.partition_maintenance?.recommendations?.length > 0 ? (
                      <div>
                        {partitionAnalysis.partition_maintenance.recommendations.map((rec, index) => (
                          <Card key={index} size="small" style={{ marginBottom: 8 }}>
                            <div>
                              <Text strong>{rec.table}</Text>
                              <Tag color="blue" style={{ marginLeft: 8 }}>{rec.action}</Tag>
                            </div>
                            <div style={{ marginTop: 8, fontFamily: 'monospace', fontSize: '11px' }}>
                              {rec.sql}
                            </div>
                            <div style={{ marginTop: 8, fontSize: '12px', color: '#999' }}>
                              频率: {rec.frequency}
                            </div>
                          </Card>
                        ))}
                      </div>
                    ) : (
                      <Empty description="暂无分区维护建议" />
                    )}
                  </Card>
                </Col>
              </Row>
            </TabPane>

            {/* 备份策略 */}
            <TabPane tab="备份策略" key="backup">
              <Card title="备份优化建议">
                {backupAnalysis?.optimization_recommendations?.length > 0 ? (
                  <Collapse>
                    {backupAnalysis.optimization_recommendations.map((rec, index) => (
                      <Panel 
                        header={
                          <div>
                            <Tag color={rec.severity === 'high' ? 'red' : 'orange'}>{rec.severity}</Tag>
                            <Text strong>{rec.category}</Text>
                          </div>
                        } 
                        key={index}
                      >
                        <div>
                          <Paragraph><Text strong>问题:</Text> {rec.issue}</Paragraph>
                          <Paragraph><Text strong>解决方案:</Text> {rec.solution}</Paragraph>
                          {rec.benefits && (
                            <div>
                              <Text strong>收益:</Text>
                              <ul>
                                {rec.benefits.map((benefit, idx) => (
                                  <li key={idx}>{benefit}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {rec.implementation && (
                            <Paragraph><Text strong>实施:</Text> {rec.implementation}</Paragraph>
                          )}
                        </div>
                      </Panel>
                    ))}
                  </Collapse>
                ) : (
                  <Empty description="暂无备份优化建议" />
                )}
              </Card>
            </TabPane>
          </Tabs>

          {/* 调优脚本模态框 */}
          <Modal
            title="MySQL 调优脚本"
            visible={scriptModalVisible}
            onCancel={() => setScriptModalVisible(false)}
            width={900}
            footer={[
              <Button key="close" onClick={() => setScriptModalVisible(false)}>
                关闭
              </Button>,
              <Button 
                key="copy" 
                type="primary"
                icon={<CopyOutlined />}
                onClick={() => {
                  navigator.clipboard.writeText(tuningScript);
                  message.success('脚本已复制到剪贴板');
                }}
              >
                复制脚本
              </Button>
            ]}
          >
            <Alert
              message="重要提醒"
              description="执行调优脚本前请务必备份数据库配置和数据！建议在测试环境中先验证脚本效果。"
              type="warning"
              style={{ marginBottom: 16 }}
              showIcon
            />
            <div style={{ 
              fontFamily: 'monospace', 
              fontSize: '12px', 
              backgroundColor: '#f5f5f5', 
              padding: 16, 
              borderRadius: 4,
              maxHeight: '500px',
              overflowY: 'auto',
              border: '1px solid #d9d9d9'
            }}>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{tuningScript}</pre>
            </div>
          </Modal>
        </Spin>
      )}
    </div>
  );
};

export default MySQLTuningDashboard;