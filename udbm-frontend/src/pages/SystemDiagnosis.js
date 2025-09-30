import React, { useState, useEffect } from 'react';
import {
  Card, Button, Select, Space, Progress, Alert, Spin,
  Tooltip, Statistic, Row, Col, Tabs, Descriptions,
  Typography, Tag, Divider, List
} from 'antd';
import {
  DatabaseOutlined, BarChartOutlined, WarningOutlined,
  CheckCircleOutlined, ReloadOutlined, ThunderboltOutlined,
  ClockCircleOutlined, SettingOutlined, SecurityScanOutlined,
  MedicineBoxOutlined, TrophyOutlined, AlertOutlined
} from '@ant-design/icons';

import { performanceAPI } from '../services/api';
import DatabaseSelector from '../components/DatabaseSelector';

const { Option } = Select;
const { TabPane } = Tabs;
const { Title, Text, Paragraph } = Typography;

const SystemDiagnosis = () => {
  const [loading, setLoading] = useState(false);
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [selectedDatabaseType, setSelectedDatabaseType] = useState('all');
  const [currentDiagnosis, setCurrentDiagnosis] = useState(null);
  const [diagnosisHistory, setDiagnosisHistory] = useState([]);
  const [databases, setDatabases] = useState([]);
  const [diagnosing, setDiagnosing] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // 获取数据库列表
  useEffect(() => {
    fetchDatabases();
  }, []);

  // 获取诊断数据
  useEffect(() => {
    if (selectedDatabase) {
      fetchDiagnosisHistory();
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

  const fetchDiagnosisHistory = async () => {
    try {
      const response = await performanceAPI.getSystemDiagnoses(selectedDatabase.id);
      setDiagnosisHistory(response || []);
      if (response && response.length > 0) {
        setCurrentDiagnosis(response[0]); // 最新的诊断结果
      }
    } catch (error) {
      console.error('获取诊断历史失败:', error);
    }
  };

  const handlePerformDiagnosis = async () => {
    setDiagnosing(true);
    try {
      const response = await performanceAPI.performSystemDiagnosis(selectedDatabase.id);
      setCurrentDiagnosis(response);
      await fetchDiagnosisHistory();
    } catch (error) {
      console.error('执行系统诊断失败:', error);
    } finally {
      setDiagnosing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDiagnosisHistory();
    setRefreshing(false);
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#52c41a';
    if (score >= 60) return '#faad14';
    return '#f5222e';
  };

  const getScoreStatus = (score) => {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    return 'poor';
  };

  const getStatusIcon = (status) => {
    if (status === 'healthy') return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
    if (status === 'warning') return <WarningOutlined style={{ color: '#faad14' }} />;
    return <AlertOutlined style={{ color: '#f5222e' }} />;
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

  const renderDiagnosisResult = (diagnosis) => {
    if (!diagnosis || !diagnosis.diagnosis_result) return null;

    const result = typeof diagnosis.diagnosis_result === 'string'
      ? JSON.parse(diagnosis.diagnosis_result)
      : diagnosis.diagnosis_result;

    return (
      <div>
        {/* CPU分析 */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <BarChartOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              <Title level={5} style={{ margin: 0 }}>CPU使用情况</Title>
            </div>
            {getStatusIcon(result.cpu_analysis?.status)}
          </div>
          <Divider style={{ margin: '12px 0' }} />
          <Row gutter={[16, 16]}>
            <Col xs={12}>
              <Statistic
                title="CPU使用率"
                value={result.cpu_analysis?.usage_percent || 0}
                suffix="%"
                valueStyle={{ color: getScoreColor(100 - (result.cpu_analysis?.usage_percent || 0)) }}
              />
            </Col>
            <Col xs={12}>
              <Text>{result.cpu_analysis?.recommendations?.[0] || 'CPU运行正常'}</Text>
            </Col>
          </Row>
        </Card>

        {/* 内存分析 */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <ThunderboltOutlined style={{ marginRight: 8, color: '#722ed1' }} />
              <Title level={5} style={{ margin: 0 }}>内存使用情况</Title>
            </div>
            {getStatusIcon(result.memory_analysis?.status)}
          </div>
          <Divider style={{ margin: '12px 0' }} />
          <Row gutter={[16, 16]}>
            <Col xs={12}>
              <Statistic
                title="内存使用率"
                value={result.memory_analysis?.usage_percent || 0}
                suffix="%"
                valueStyle={{ color: getScoreColor(100 - (result.memory_analysis?.usage_percent || 0)) }}
              />
            </Col>
            <Col xs={12}>
              <Text>{result.memory_analysis?.recommendations?.[0] || '内存使用正常'}</Text>
            </Col>
          </Row>
        </Card>

        {/* IO分析 */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <ClockCircleOutlined style={{ marginRight: 8, color: '#fa8c16' }} />
              <Title level={5} style={{ margin: 0 }}>磁盘IO性能</Title>
            </div>
            {getStatusIcon(result.io_analysis?.status)}
          </div>
          <Divider style={{ margin: '12px 0' }} />
          <Row gutter={[16, 16]}>
            <Col xs={12}>
              <Statistic
                title="读取IOPS"
                value={result.io_analysis?.read_iops || 0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col xs={12}>
              <Statistic
                title="写入IOPS"
                value={result.io_analysis?.write_iops || 0}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
          </Row>
          <div style={{ marginTop: 8 }}>
            <Text>{result.io_analysis?.recommendations?.[0] || 'IO性能正常'}</Text>
          </div>
        </Card>

        {/* 连接池分析 */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <DatabaseOutlined style={{ marginRight: 8, color: '#13c2c2' }} />
              <Title level={5} style={{ margin: 0 }}>连接池状态</Title>
            </div>
            {getStatusIcon(result.connection_analysis?.status)}
          </div>
          <Divider style={{ margin: '12px 0' }} />
          <Row gutter={[16, 16]}>
            <Col xs={12}>
              <Statistic
                title="活跃连接数"
                value={result.connection_analysis?.active_connections || 0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col xs={12}>
              <Statistic
                title="最大连接数"
                value={result.connection_analysis?.max_connections || 100}
                valueStyle={{ color: '#666' }}
              />
            </Col>
          </Row>
          <div style={{ marginTop: 8 }}>
            <Text>{result.connection_analysis?.recommendations?.[0] || '连接数正常'}</Text>
          </div>
        </Card>

        {/* 瓶颈分析 */}
        {result.bottlenecks && result.bottlenecks.length > 0 && (
          <Card size="small">
            <Title level={5} style={{ color: '#f5222e', marginBottom: 16 }}>
              <AlertOutlined style={{ marginRight: 8 }} />
              发现的性能瓶颈
            </Title>
            <List
              dataSource={result.bottlenecks}
              renderItem={(bottleneck) => (
                <List.Item>
                  <Alert
                    message={
                      <div>
                        <Text strong>{bottleneck.type ? bottleneck.type.toUpperCase() : '未知类型'} 瓶颈</Text>
                        <br />
                        <Text>{bottleneck.description}</Text>
                      </div>
                    }
                    description={
                      <div>
                        <Text>建议解决方案: {bottleneck.solution}</Text>
                        <br />
                        <Text type="success">预期改善: {bottleneck.estimated_improvement}</Text>
                      </div>
                    }
                    type={bottleneck.severity === 'critical' ? 'error' : 'warning'}
                    showIcon
                  />
                </List.Item>
              )}
            />
          </Card>
        )}
      </div>
    );
  };

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0 }}>
            <SecurityScanOutlined style={{ marginRight: 8 }} />
            系统诊断
          </h2>
          <p style={{ margin: '8px 0', color: '#666' }}>
            全面诊断数据库系统性能状态，提供优化建议
          </p>
        </div>
        <Space>
          <Button
            type="primary"
            icon={<MedicineBoxOutlined />}
            onClick={handlePerformDiagnosis}
            loading={diagnosing}
            disabled={!selectedDatabase}
          >
            执行诊断
          </Button>
          <Button
            icon={<ReloadOutlined spin={refreshing} />}
            onClick={handleRefresh}
            loading={refreshing}
            disabled={!selectedDatabase}
          >
            刷新
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

      {currentDiagnosis && (
        <div>
          {/* 整体健康评分 */}
          <Card style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <Title level={4} style={{ margin: 0 }}>系统健康评分</Title>
                <p style={{ margin: '8px 0', color: '#666' }}>
                  基于CPU、内存、IO、连接池等关键指标的综合评分
                </p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{
                  fontSize: '48px',
                  fontWeight: 'bold',
                  color: getScoreColor(currentDiagnosis.overall_score),
                  marginBottom: '8px'
                }}>
                  {(currentDiagnosis.overall_score || 0).toFixed(1)}
                </div>
                <Tag color={getScoreColor(currentDiagnosis.overall_score)} style={{ fontSize: '14px' }}>
                  {currentDiagnosis.overall_score >= 80 ? '健康' :
                   currentDiagnosis.overall_score >= 60 ? '一般' : '异常'}
                </Tag>
              </div>
            </div>
            <Progress
              percent={currentDiagnosis.overall_score}
              strokeColor={getScoreColor(currentDiagnosis.overall_score)}
              status={currentDiagnosis.overall_score >= 60 ? 'active' : 'exception'}
              showInfo={false}
            />
            <div style={{ marginTop: 16, fontSize: '12px', color: '#666' }}>
              诊断时间: {new Date(currentDiagnosis.timestamp).toLocaleString()}
            </div>
          </Card>

          {/* 各维度评分 */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} md={6}>
              <Card size="small">
                <Statistic
                  title="性能评分"
                  value={currentDiagnosis.performance_score}
                  suffix="/100"
                  valueStyle={{ color: getScoreColor(currentDiagnosis.performance_score) }}
                  prefix={<BarChartOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card size="small">
                <Statistic
                  title="安全评分"
                  value={currentDiagnosis.security_score}
                  suffix="/100"
                  valueStyle={{ color: getScoreColor(currentDiagnosis.security_score) }}
                  prefix={<SettingOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card size="small">
                <Statistic
                  title="维护评分"
                  value={currentDiagnosis.maintenance_score}
                  suffix="/100"
                  valueStyle={{ color: getScoreColor(currentDiagnosis.maintenance_score) }}
                  prefix={<ThunderboltOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card size="small">
                <Statistic
                  title="诊断次数"
                  value={diagnosisHistory.length}
                  prefix={<ClockCircleOutlined />}
                />
              </Card>
            </Col>
          </Row>

          <Tabs defaultActiveKey="1">
            <TabPane tab="详细诊断结果" key="1">
              {renderDiagnosisResult(currentDiagnosis)}
            </TabPane>

            <TabPane tab="诊断历史" key="2">
              <Card>
                <List
                  dataSource={diagnosisHistory}
                  renderItem={(diagnosis) => (
                    <List.Item
                      actions={[
                        <Button
                          type="link"
                          onClick={() => setCurrentDiagnosis(diagnosis)}
                        >
                          查看详情
                        </Button>
                      ]}
                    >
                      <List.Item.Meta
                        title={
                          <div>
                            <Text strong>诊断时间: {new Date(diagnosis.timestamp).toLocaleString()}</Text>
                            <Tag
                              color={getScoreColor(diagnosis.overall_score)}
                              style={{ marginLeft: 8 }}
                            >
                              评分: {(diagnosis.overall_score || 0).toFixed(1)}
                            </Tag>
                          </div>
                        }
                        description={
                          <div>
                            <Text>性能: {diagnosis.performance_score} | 安全: {diagnosis.security_score} | 维护: {diagnosis.maintenance_score}</Text>
                          </div>
                        }
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </TabPane>
          </Tabs>
        </div>
      )}

      {!currentDiagnosis && !loading && (
        <Card style={{ textAlign: 'center', padding: '50px' }}>
          <MedicineBoxOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: '16px' }} />
          <Title level={4}>暂无诊断结果</Title>
          <Paragraph type="secondary">
            点击"执行诊断"按钮开始对数据库进行全面的性能诊断
          </Paragraph>
          <Button
            type="primary"
            size="large"
            icon={<MedicineBoxOutlined />}
            onClick={handlePerformDiagnosis}
            loading={diagnosing}
          >
            开始诊断
          </Button>
        </Card>
      )}
    </div>
  );
};

export default SystemDiagnosis;
