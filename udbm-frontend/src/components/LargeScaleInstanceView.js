import React, { useState, useMemo } from 'react';
import { 
  Card, 
  Input, 
  Select, 
  Button, 
  Space, 
  Table, 
  Tag, 
  Badge, 
  Tooltip, 
  Pagination,
  Row,
  Col,
  Statistic,
  Progress,
  Empty,
  Spin
} from 'antd';
import { 
  SearchOutlined, 
  FilterOutlined, 
  ReloadOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  BarChartOutlined,
  SettingOutlined
} from '@ant-design/icons';

const { Option } = Select;
const { Search } = Input;

// 数据库类型配置
const DATABASE_TYPE_CONFIG = {
  postgresql: { icon: '🐘', color: '#336791', name: 'PostgreSQL' },
  mysql: { icon: '🐬', color: '#4479A1', name: 'MySQL' },
  mongodb: { icon: '🍃', color: '#47A248', name: 'MongoDB' },
  redis: { icon: '⚡', color: '#DC382D', name: 'Redis' },
  oracle: { icon: '🔶', color: '#F80000', name: 'Oracle' },
  sqlserver: { icon: '🏢', color: '#CC2927', name: 'SQL Server' }
};

// 环境配置
const ENVIRONMENT_CONFIG = {
  production: { color: '#f5222d', icon: '🔴', name: '生产环境' },
  staging: { color: '#faad14', icon: '🟡', name: '测试环境' },
  development: { color: '#52c41a', icon: '🟢', name: '开发环境' }
};

const LargeScaleInstanceView = ({ 
  instances = [], 
  loading = false,
  onInstanceClick,
  onRefresh 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [selectedEnvironment, setSelectedEnvironment] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [viewMode, setViewMode] = useState('table'); // 'table' | 'grid' | 'compact'

  // 过滤和搜索逻辑
  const filteredInstances = useMemo(() => {
    return instances.filter(instance => {
      const matchesSearch = !searchTerm || 
        instance.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        instance.host.toLowerCase().includes(searchTerm.toLowerCase()) ||
        instance.database_name?.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesType = selectedType === 'all' || instance.type === selectedType;
      const matchesEnvironment = selectedEnvironment === 'all' || instance.environment === selectedEnvironment;
      const matchesStatus = selectedStatus === 'all' || instance.health_status === selectedStatus;
      
      return matchesSearch && matchesType && matchesEnvironment && matchesStatus;
    });
  }, [instances, searchTerm, selectedType, selectedEnvironment, selectedStatus]);

  // 分页数据
  const paginatedInstances = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    return filteredInstances.slice(start, end);
  }, [filteredInstances, currentPage, pageSize]);

  // 统计信息
  const stats = useMemo(() => {
    const total = instances.length;
    const healthy = instances.filter(i => i.health_status === 'healthy').length;
    const warning = instances.filter(i => i.health_status === 'warning').length;
    const critical = instances.filter(i => i.health_status === 'critical').length;
    
    return { total, healthy, warning, critical };
  }, [instances]);

  // 获取健康状态配置
  const getHealthConfig = (status) => {
    const configs = {
      healthy: { color: '#52c41a', icon: CheckCircleOutlined, text: '健康' },
      warning: { color: '#faad14', icon: WarningOutlined, text: '警告' },
      critical: { color: '#f5222d', icon: CloseCircleOutlined, text: '严重' },
      unknown: { color: '#8c8c8c', icon: DatabaseOutlined, text: '未知' }
    };
    return configs[status] || configs.unknown;
  };

  // 表格列定义
  const columns = [
    {
      title: '实例名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text, record) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <DatabaseOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          <div>
            <div style={{ fontWeight: 500, marginBottom: 2 }}>{text}</div>
            <div style={{ fontSize: '11px', color: '#8c8c8c', fontFamily: 'monospace' }}>
              {record.host}:{record.port}
            </div>
          </div>
        </div>
      )
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type) => {
        const config = DATABASE_TYPE_CONFIG[type] || DATABASE_TYPE_CONFIG.postgresql;
        return (
          <Tag color={config.color} style={{ margin: 0 }}>
            {config.icon} {config.name}
          </Tag>
        );
      }
    },
    {
      title: '环境',
      dataIndex: 'environment',
      key: 'environment',
      width: 100,
      render: (env) => {
        const config = ENVIRONMENT_CONFIG[env] || { color: '#666', icon: '⚪', name: env };
        return (
          <Tag color={config.color} style={{ margin: 0 }}>
            {config.icon} {config.name}
          </Tag>
        );
      }
    },
    {
      title: '健康状态',
      dataIndex: 'health_status',
      key: 'health_status',
      width: 100,
      render: (status) => {
        const config = getHealthConfig(status);
        const IconComponent = config.icon;
        return (
          <Badge
            status={status === 'healthy' ? 'success' : status === 'warning' ? 'warning' : 'error'}
            text={
              <span style={{ color: config.color, fontSize: '12px' }}>
                <IconComponent style={{ marginRight: 4 }} />
                {config.text}
              </span>
            }
          />
        );
      }
    },
    {
      title: '性能指标',
      key: 'performance',
      width: 150,
      render: (_, record) => {
        // 模拟性能数据
        const cpuUsage = Math.floor(Math.random() * 100);
        const memoryUsage = Math.floor(Math.random() * 100);
        const getColor = (value) => value > 80 ? '#f5222d' : value > 60 ? '#faad14' : '#52c41a';
        
        return (
          <div style={{ fontSize: '11px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
              <span>CPU</span>
              <span style={{ color: getColor(cpuUsage) }}>{cpuUsage}%</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>内存</span>
              <span style={{ color: getColor(memoryUsage) }}>{memoryUsage}%</span>
            </div>
          </div>
        );
      }
    },
    {
      title: '最后检查',
      dataIndex: 'last_check',
      key: 'last_check',
      width: 120,
      render: (_, record) => {
        const lastCheck = new Date(Date.now() - Math.floor(Math.random() * 60) * 60 * 1000);
        const minutes = Math.floor((Date.now() - lastCheck) / (1000 * 60));
        return (
          <span style={{ fontSize: '11px', color: '#8c8c8c' }}>
            {minutes < 60 ? `${minutes}分钟前` : `${Math.floor(minutes / 60)}小时前`}
          </span>
        );
      }
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
              icon={<EyeOutlined />}
              onClick={() => onInstanceClick?.(record)}
            />
          </Tooltip>
          <Tooltip title="性能监控">
            <Button
              type="text"
              size="small"
              icon={<BarChartOutlined />}
            />
          </Tooltip>
          <Tooltip title="配置管理">
            <Button
              type="text"
              size="small"
              icon={<SettingOutlined />}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <div>
      {/* 统计概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={6}>
          <Card size="small">
            <Statistic
              title="总实例数"
              value={stats.total}
              prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small">
            <Statistic
              title="健康实例"
              value={stats.healthy}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small">
            <Statistic
              title="警告实例"
              value={stats.warning}
              prefix={<WarningOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small">
            <Statistic
              title="严重实例"
              value={stats.critical}
              prefix={<CloseCircleOutlined style={{ color: '#f5222d' }} />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 搜索和筛选 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8}>
            <Search
              placeholder="搜索实例名称、主机或数据库名..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ width: '100%' }}
              allowClear
            />
          </Col>
          <Col xs={24} sm={4}>
            <Select
              value={selectedType}
              onChange={setSelectedType}
              style={{ width: '100%' }}
              placeholder="数据库类型"
            >
              <Option value="all">全部类型</Option>
              {Object.entries(DATABASE_TYPE_CONFIG).map(([key, config]) => (
                <Option key={key} value={key}>
                  {config.icon} {config.name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={4}>
            <Select
              value={selectedEnvironment}
              onChange={setSelectedEnvironment}
              style={{ width: '100%' }}
              placeholder="环境"
            >
              <Option value="all">全部环境</Option>
              {Object.entries(ENVIRONMENT_CONFIG).map(([key, config]) => (
                <Option key={key} value={key}>
                  {config.icon} {config.name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={4}>
            <Select
              value={selectedStatus}
              onChange={setSelectedStatus}
              style={{ width: '100%' }}
              placeholder="健康状态"
            >
              <Option value="all">全部状态</Option>
              <Option value="healthy">健康</Option>
              <Option value="warning">警告</Option>
              <Option value="critical">严重</Option>
            </Select>
          </Col>
          <Col xs={24} sm={4}>
            <Space>
              <Button
                icon={<ReloadOutlined />}
                onClick={onRefresh}
                loading={loading}
              >
                刷新
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 实例列表 */}
      <Card>
        <Table
          columns={columns}
          dataSource={paginatedInstances}
          rowKey="id"
          loading={loading}
          pagination={false}
          size="small"
          scroll={{ x: 800 }}
          rowClassName={(record) => 
            record.health_status === 'critical' ? 'critical-row' : 
            record.health_status === 'warning' ? 'warning-row' : ''
          }
        />
        
        {/* 分页 */}
        <div style={{ 
          marginTop: 16, 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center' 
        }}>
          <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
            显示 {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, filteredInstances.length)} 条，
            共 {filteredInstances.length} 条记录
          </div>
          <Pagination
            current={currentPage}
            pageSize={pageSize}
            total={filteredInstances.length}
            onChange={(page, size) => {
              setCurrentPage(page);
              setPageSize(size);
            }}
            showSizeChanger
            showQuickJumper
            showTotal={(total, range) => 
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
            }
            pageSizeOptions={['10', '20', '50', '100']}
          />
        </div>
      </Card>

      {/* 样式 */}
      <style jsx>{`
        .critical-row {
          background-color: #fff2f0 !important;
        }
        .warning-row {
          background-color: #fffbe6 !important;
        }
        .critical-row:hover {
          background-color: #ffebe6 !important;
        }
        .warning-row:hover {
          background-color: #fff7e6 !important;
        }
      `}</style>
    </div>
  );
};

export default LargeScaleInstanceView;
