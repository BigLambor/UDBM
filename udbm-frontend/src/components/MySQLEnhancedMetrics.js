import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Statistic, Progress, Alert, Tabs, Table, Tag,
  Button, Space, Modal, Form, Input, Select as AntSelect, message,
  Descriptions, Tooltip, Badge, Empty, Spin
} from 'antd';
import {
  DatabaseOutlined, BarChartOutlined, ThunderboltOutlined,
  ToolOutlined, SettingOutlined, TableOutlined, ClockCircleOutlined,
  CheckCircleOutlined, WarningOutlined, AlertOutlined, SecurityScanOutlined,
  CloudServerOutlined, HddOutlined, SafetyOutlined, BackupOutlined,
  PartitionOutlined, ReloadOutlined, CopyOutlined
} from '@ant-design/icons';
import { Line, Bar, Pie } from '@ant-design/charts';

import { performanceAPI } from '../services/api';

const { TabPane } = Tabs;
const { Option } = AntSelect;

// MySQL 增强特性组件
const MySQLEnhancedMetrics = ({ database, dashboardData, onRefresh }) => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [analysisData, setAnalysisData] = useState(null);
  const [optimizationSummary, setOptimizationSummary] = useState(null);
  const [tuningScript, setTuningScript] = useState('');
  const [scriptModalVisible, setScriptModalVisible] = useState(false);
  const [comprehensiveData, setComprehensiveData] = useState(null);
  
  // 加载MySQL分析数据
  const loadMySQLAnalysis = async () => {
    if (!database?.id) return;
    
    setLoading(true);
    try {
      // 并行加载多个分析结果
      const [configAnalysis, optimizationSummary, performanceInsights] = await Promise.all([
        performanceAPI.analyzeMySQLConfig(database.id).catch(() => null),
        performanceAPI.getMySQLOptimizationSummary(database.id).catch(() => null),
        performanceAPI.getMySQLPerformanceInsights(database.id).catch(() => null)
      ]);
      
      setAnalysisData({
        config: configAnalysis,
        insights: performanceInsights
      });
      setOptimizationSummary(optimizationSummary);
      
      if (onRefresh) {
        onRefresh();
      }
    } catch (error) {
      console.error('加载MySQL分析数据失败:', error);
      message.error('加载MySQL分析数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载综合分析数据
  const loadComprehensiveAnalysis = async () => {
    if (!database?.id) return;
    
    setLoading(true);
    try {
      const data = await performanceAPI.comprehensiveMySQLAnalysis(
        database.id, 
        ['config', 'storage', 'security', 'replication']
      );
      setComprehensiveData(data);
    } catch (error) {
      console.error('加载综合分析失败:', error);
      message.error('加载综合分析失败');
    } finally {
      setLoading(false);
    }
  };

  // 生成调优脚本
  const generateTuningScript = async (areas = ['config', 'storage', 'security']) => {
    try {
      setLoading(true);
      const scriptData = await performanceAPI.generateMySQLTuningScript(database.id, areas);
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
    try {
      setLoading(true);
      const result = await performanceAPI.quickMySQLOptimization(database.id, focusArea);
      
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
            <p>重点优化区域: <Tag color="blue">{result.focus_area}</Tag></p>
            <div style={{ marginTop: 16 }}>
              <h4>快速建议:</h4>
              {result.quick_recommendations?.length > 0 ? (
                result.quick_recommendations.map((rec, index) => (
                  <Card key={index} size="small" style={{ marginBottom: 8 }}>
                    <div>
                      <Tag color={rec.impact === 'critical' ? 'red' : rec.impact === 'high' ? 'orange' : 'blue'}>
                        {rec.impact}
                      </Tag>
                      <strong>{rec.category}</strong>
                    </div>
                    <div style={{ marginTop: 8 }}>{rec.action}</div>
                    {rec.sql && (
                      <div style={{ marginTop: 8, fontFamily: 'monospace', backgroundColor: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                        {rec.sql}
                      </div>
                    )}
                    {rec.estimated_improvement && (
                      <div style={{ marginTop: 8, color: '#52c41a' }}>
                        预期改善: {rec.estimated_improvement}
                      </div>
                    )}
                  </Card>
                ))
              ) : (
                <Empty description="暂无快速建议" />
              )}
              {result.next_steps && (
                <div style={{ marginTop: 16 }}>
                  <h4>后续步骤:</h4>
                  <ul>
                    {result.next_steps.map((step, index) => (
                      <li key={index}>{step}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
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
    loadMySQLAnalysis();
  }, [database?.id]);

  const getHealthStatusColor = (score) => {
    if (score >= 90) return '#52c41a';
    if (score >= 75) return '#faad14';
    return '#f5222e';
  };

  const getHealthStatusText = (status) => {
    const statusMap = {
      'excellent': '优秀',
      'good': '良好',
      'fair': '一般',
      'poor': '较差',
      'critical': '严重'
    };
    return statusMap[status] || status;
  };

  return (
    <Spin spinning={loading}>
      <div>
        {/* MySQL 核心指标 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} lg={6}>
            <Card>
              <Statistic
                title="MySQL健康评分"
                value={analysisData?.insights?.performance_score || optimizationSummary?.overall_health_score || 0}
                suffix="/100"
                valueStyle={{ 
                  color: getHealthStatusColor(analysisData?.insights?.performance_score || optimizationSummary?.overall_health_score || 0) 
                }}
                prefix={<DatabaseOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} lg={6}>
            <Card>
              <Statistic
                title="活跃连接"
                value={analysisData?.insights?.key_metrics?.active_connections || dashboardData?.current_stats?.active_connections || 0}
                prefix={<DatabaseOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} lg={6}>
            <Card>
              <Statistic
                title="QPS"
                value={analysisData?.insights?.key_metrics?.qps || dashboardData?.current_stats?.qps || 0}
                suffix="/s"
                prefix={<ThunderboltOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} lg={6}>
            <Card>
              <Statistic
                title="优化建议"
                value={optimizationSummary?.optimization_statistics?.total_recommendations || 0}
                suffix="条"
                prefix={<ToolOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 操作按钮 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col>
            <Space wrap>
              <Button 
                type="primary" 
                icon={<ReloadOutlined />} 
                onClick={loadMySQLAnalysis}
                loading={loading}
              >
                刷新分析
              </Button>
              <Button 
                icon={<SettingOutlined />} 
                onClick={() => generateTuningScript()}
                loading={loading}
              >
                生成调优脚本
              </Button>
              <Button 
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
                icon={<BarChartOutlined />} 
                onClick={loadComprehensiveAnalysis}
                loading={loading}
              >
                综合分析
              </Button>
            </Space>
          </Col>
        </Row>

        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="概览" key="overview">
            <Row gutter={[16, 16]}>
              {/* 健康状态 */}
              <Col xs={24} lg={12}>
                <Card title="系统健康状态">
                  {analysisData?.insights?.health_status ? (
                    <div>
                      <div style={{ marginBottom: 16 }}>
                        <Badge 
                          status={
                            analysisData.insights.health_status.status === 'excellent' ? 'success' :
                            analysisData.insights.health_status.status === 'good' ? 'processing' :
                            analysisData.insights.health_status.status === 'fair' ? 'warning' : 'error'
                          }
                          text={analysisData.insights.health_status.description}
                        />
                      </div>
                      <Progress 
                        percent={Math.round(analysisData.insights.health_status.health_score)} 
                        strokeColor={getHealthStatusColor(analysisData.insights.health_status.health_score)}
                      />
                      {analysisData.insights.health_status.critical_issues > 0 && (
                        <Alert
                          message={`发现 ${analysisData.insights.health_status.critical_issues} 个严重问题`}
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
              <Col xs={24} lg={12}>
                <Card title="性能瓶颈">
                  {analysisData?.insights?.bottlenecks?.length > 0 ? (
                    <div>
                      {analysisData.insights.bottlenecks.map((bottleneck, index) => (
                        <div key={index} style={{ marginBottom: 12 }}>
                          <div>
                            <Tag color={bottleneck.severity === 'high' ? 'red' : 'orange'}>
                              {bottleneck.severity}
                            </Tag>
                            <strong>{bottleneck.type}</strong>
                          </div>
                          <div style={{ marginTop: 4, color: '#666' }}>
                            {bottleneck.description}
                          </div>
                          <div style={{ marginTop: 4, fontSize: '12px', color: '#999' }}>
                            影响: {bottleneck.impact}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <Empty description="未发现明显瓶颈" />
                  )}
                </Card>
              </Col>

              {/* 配置分析 */}
              <Col xs={24}>
                <Card title="配置分析">
                  {analysisData?.config ? (
                    <Descriptions bordered column={3}>
                      <Descriptions.Item label="数据源">
                        <Tag color={analysisData.config.data_source === 'real_data' ? 'green' : 'blue'}>
                          {analysisData.config.data_source === 'real_data' ? '真实数据' : '演示数据'}
                        </Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="优化评分">
                        <span style={{ color: getHealthStatusColor(analysisData.config.optimization_score) }}>
                          {analysisData.config.optimization_score}/100
                        </span>
                      </Descriptions.Item>
                      <Descriptions.Item label="分析时间">
                        {new Date(analysisData.config.analysis_timestamp).toLocaleString()}
                      </Descriptions.Item>
                      <Descriptions.Item label="配置建议" span={3}>
                        {analysisData.config.recommendations?.length || 0} 条建议
                      </Descriptions.Item>
                    </Descriptions>
                  ) : (
                    <Empty description="暂无配置数据" />
                  )}
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="优化建议" key="recommendations">
            <Card title="优化建议">
              {optimizationSummary?.priority_recommendations?.length > 0 ? (
                <Table
                  dataSource={optimizationSummary.priority_recommendations}
                  columns={[
                    {
                      title: '类别',
                      dataIndex: 'category',
                      key: 'category',
                      render: (text) => <Tag color="blue">{text}</Tag>
                    },
                    {
                      title: '标题',
                      dataIndex: 'title',
                      key: 'title'
                    },
                    {
                      title: '影响程度',
                      dataIndex: 'impact',
                      key: 'impact',
                      render: (impact) => (
                        <Tag color={
                          impact === 'critical' ? 'red' :
                          impact === 'high' ? 'orange' :
                          impact === 'medium' ? 'blue' : 'default'
                        }>
                          {impact}
                        </Tag>
                      )
                    },
                    {
                      title: '预期改善',
                      dataIndex: 'estimated_improvement',
                      key: 'estimated_improvement'
                    },
                    {
                      title: '描述',
                      dataIndex: 'description',
                      key: 'description',
                      ellipsis: true
                    }
                  ]}
                  pagination={{ pageSize: 10 }}
                  size="middle"
                  rowKey={(record, index) => index}
                />
              ) : (
                <Empty description="暂无优化建议" />
              )}
            </Card>
          </TabPane>

          <TabPane tab="优化机会" key="opportunities">
            <Card title="优化机会">
              {analysisData?.insights?.optimization_opportunities?.length > 0 ? (
                <Row gutter={[16, 16]}>
                  {analysisData.insights.optimization_opportunities.map((opportunity, index) => (
                    <Col xs={24} lg={12} key={index}>
                      <Card size="small">
                        <div>
                          <Tag color="green">{opportunity.type}</Tag>
                          <strong>{opportunity.title}</strong>
                        </div>
                        <div style={{ marginTop: 8, color: '#666' }}>
                          {opportunity.description}
                        </div>
                        <div style={{ marginTop: 8 }}>
                          <span style={{ color: '#1890ff' }}>预期收益: {opportunity.estimated_benefit}</span>
                          <span style={{ marginLeft: 16, color: '#999' }}>
                            实施难度: {opportunity.effort}
                          </span>
                        </div>
                      </Card>
                    </Col>
                  ))}
                </Row>
              ) : (
                <Empty description="暂无优化机会" />
              )}
            </Card>
          </TabPane>

          <TabPane tab="综合分析" key="comprehensive">
            <Card 
              title="综合分析结果" 
              extra={
                <Button 
                  icon={<ReloadOutlined />} 
                  onClick={loadComprehensiveAnalysis}
                  loading={loading}
                  size="small"
                >
                  刷新
                </Button>
              }
            >
              {comprehensiveData ? (
                <div>
                  <Descriptions bordered style={{ marginBottom: 16 }}>
                    <Descriptions.Item label="分析时间">
                      {new Date(comprehensiveData.analysis_timestamp).toLocaleString()}
                    </Descriptions.Item>
                    <Descriptions.Item label="分析维度">
                      {comprehensiveData.included_areas?.join(', ')}
                    </Descriptions.Item>
                    <Descriptions.Item label="整体评分">
                      <span style={{ color: getHealthStatusColor(comprehensiveData.summary?.overall_health_score || 0) }}>
                        {comprehensiveData.summary?.overall_health_score || 0}/100
                      </span>
                    </Descriptions.Item>
                  </Descriptions>

                  {/* 各维度分析结果 */}
                  <Tabs type="card">
                    {Object.entries(comprehensiveData.analysis_results || {}).map(([key, result]) => (
                      <TabPane tab={key.toUpperCase()} key={key}>
                        <div style={{ padding: 16 }}>
                          {key === 'config' && result.recommendations && (
                            <div>
                              <h4>配置建议 ({result.recommendations.length} 条)</h4>
                              {result.recommendations.map((rec, index) => (
                                <Card key={index} size="small" style={{ marginBottom: 8 }}>
                                  <Tag color={rec.impact === 'high' ? 'red' : 'blue'}>{rec.impact}</Tag>
                                  <strong>{rec.parameter}</strong>
                                  <div style={{ marginTop: 4 }}>{rec.description}</div>
                                  <div style={{ marginTop: 4, fontSize: '12px', color: '#999' }}>
                                    当前值: {rec.current_value} → 建议值: {rec.recommended_value}
                                  </div>
                                </Card>
                              ))}
                            </div>
                          )}
                          {key === 'security' && (
                            <div>
                              <h4>安全分析</h4>
                              {Object.entries(result).map(([category, data]) => (
                                <div key={category} style={{ marginBottom: 16 }}>
                                  <h5>{category}</h5>
                                  {data.recommendations?.map((rec, index) => (
                                    <Alert
                                      key={index}
                                      message={rec.issue}
                                      description={rec.solution}
                                      type={rec.severity === 'high' ? 'error' : 'warning'}
                                      style={{ marginBottom: 8 }}
                                    />
                                  ))}
                                </div>
                              ))}
                            </div>
                          )}
                          {/* 其他维度的展示可以根据需要添加 */}
                        </div>
                      </TabPane>
                    ))}
                  </Tabs>
                </div>
              ) : (
                <Empty description="点击刷新按钮加载综合分析数据" />
              )}
            </Card>
          </TabPane>
        </Tabs>

        {/* 调优脚本模态框 */}
        <Modal
          title="MySQL 调优脚本"
          visible={scriptModalVisible}
          onCancel={() => setScriptModalVisible(false)}
          width={800}
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
            message="注意"
            description="执行调优脚本前请务必备份数据库配置和数据！建议在测试环境中先验证脚本效果。"
            type="warning"
            style={{ marginBottom: 16 }}
          />
          <div style={{ 
            fontFamily: 'monospace', 
            fontSize: '12px', 
            backgroundColor: '#f5f5f5', 
            padding: 16, 
            borderRadius: 4,
            maxHeight: '400px',
            overflowY: 'auto',
            border: '1px solid #d9d9d9'
          }}>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{tuningScript}</pre>
          </div>
        </Modal>
      </div>
    </Spin>
  );
};

export default MySQLEnhancedMetrics;