import React, { useState, useEffect } from 'react';
import {
  Layout, Menu, Input, Card, Typography, Breadcrumb, Button, 
  Anchor, Spin, Empty, Tag, Space, Tooltip, Switch, Affix, Alert
} from 'antd';
import {
  FileTextOutlined, SearchOutlined, BookOutlined,
  HomeOutlined, DatabaseOutlined, PrinterOutlined,
  DownloadOutlined, HeartOutlined, ShareAltOutlined,
  SunOutlined, MoonOutlined, BulbOutlined
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import './HelpCenter.css';

const { Header, Sider, Content } = Layout;
const { Title, Paragraph, Text } = Typography;
const { Search } = Input;

// 文档目录结构
const documentStructure = [
  {
    key: 'home',
    icon: <HomeOutlined />,
    label: '首页',
    path: null
  },
  {
    key: 'health-score',
    icon: <HeartOutlined />,
    label: '健康度指标体系',
    path: '/docs/health-score-system.md',
    description: '了解数据库健康度的计算模型和优化策略'
  },
  {
    key: 'mysql',
    icon: <DatabaseOutlined />,
    label: 'MySQL 性能指标',
    path: '/docs/mysql-performance-metrics.md',
    description: 'MySQL核心指标、优化建议和最佳实践'
  },
  {
    key: 'postgresql',
    icon: <DatabaseOutlined />,
    label: 'PostgreSQL 性能指标',
    path: '/docs/postgresql-performance-metrics.md',
    description: 'PostgreSQL特有指标和VACUUM策略'
  },
  {
    key: 'oceanbase',
    icon: <DatabaseOutlined />,
    label: 'OceanBase 性能指标',
    path: '/docs/oceanbase-performance-metrics.md',
    description: 'OceanBase分布式架构和合并策略'
  }
];

const HelpCenter = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState('home');
  const [markdownContent, setMarkdownContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [darkMode, setDarkMode] = useState(false);
  const [favorites, setFavorites] = useState([]);

  // 加载文档内容
  useEffect(() => {
    if (selectedDoc === 'home') {
      setMarkdownContent(getHomeContent());
      return;
    }

    const doc = documentStructure.find(d => d.key === selectedDoc);
    if (doc && doc.path) {
      loadMarkdownFile(doc.path);
    }
  }, [selectedDoc]);

  // 加载Markdown文件
  const loadMarkdownFile = async (path) => {
    setLoading(true);
    try {
      const response = await fetch(path);
      if (response.ok) {
        const text = await response.text();
        setMarkdownContent(text);
      } else {
        setMarkdownContent('# 文档加载失败\n\n无法加载该文档，请稍后重试。');
      }
    } catch (error) {
      console.error('加载文档失败:', error);
      setMarkdownContent('# 文档加载失败\n\n' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 首页内容
  const getHomeContent = () => {
    return `# 欢迎使用数据库性能监控帮助中心

## 📚 文档导航

本帮助中心提供全面的数据库性能指标说明和优化指南，帮助您：
- 理解各项性能指标的含义和计算方法
- 掌握数据来源和获取方式
- 学习业界最佳实践
- 快速定位和解决性能问题

### 🎯 核心文档

#### 1. 健康度指标体系 ⭐
**最重要的文档** - 详细介绍健康度的计算模型、维度权重和优化策略。

**适用场景**：
- 想要了解系统整体健康状况
- 需要快速定位性能瓶颈
- 制定优化优先级

**关键内容**：
- 健康度计算公式和维度体系
- MySQL/PostgreSQL/OceanBase各自的健康度模型
- 影响因素矩阵和阈值标准
- 优化实战案例

#### 2. MySQL 性能指标
MySQL是全球最流行的开源数据库，本文档涵盖：
- CPU、内存、连接池等核心指标
- InnoDB存储引擎特有指标
- 主从复制监控
- 配置优化建议

#### 3. PostgreSQL 性能指标
PostgreSQL以其ACID兼容和丰富特性著称，重点关注：
- 缓冲区命中率优化
- **表膨胀问题**（PostgreSQL独有）
- AutoVacuum策略配置
- WAL性能调优

#### 4. OceanBase 性能指标
OceanBase是原生分布式数据库，需要了解：
- 计划缓存命中率
- MemStore冻结机制
- 合并（Compaction）策略
- 分布式架构特性

---

## 🚀 快速开始

### 新手指南
1. **先阅读"健康度指标体系"** - 建立整体认知
2. **根据使用的数据库类型** - 深入学习对应章节
3. **关注健康度影响因素矩阵** - 了解优化优先级
4. **参考优化实战案例** - 学习实际操作

### 进阶使用
- 使用搜索功能快速查找特定指标
- 收藏常用章节以便快速访问
- 导出文档进行离线学习
- 在Dashboard中点击指标旁的"?"图标跳转到对应说明

---

## 💡 使用技巧

### 文档导航
- **左侧菜单**：选择要查看的文档
- **右侧锚点**：快速跳转到文档中的特定章节
- **面包屑导航**：了解当前位置
- **搜索功能**：在文档中查找关键词

### 交互功能
- **深色/浅色模式切换**：适应不同环境
- **收藏功能**：标记常用文档
- **打印/导出**：离线学习和分享
- **代码高亮**：SQL语句清晰易读

---

## 📊 指标查询速查表

| 数据库 | 最关键指标 | 正常阈值 | 危险阈值 |
|--------|-----------|----------|----------|
| MySQL | InnoDB Buffer Pool命中率 | ≥ 99% | < 95% |
| MySQL | 慢查询比率 | < 0.5% | > 5% |
| PostgreSQL | 缓冲区命中率 | ≥ 99% | < 95% |
| PostgreSQL | 死元组比率 | < 5% | > 20% |
| OceanBase | 计划缓存命中率 | ≥ 98% | < 90% |
| OceanBase | MemStore使用率 | < 60% | > 90% |

---

## 🔗 相关资源

- [官方文档](https://www.mysql.com)
- [性能优化工具](/)
- [问题排查流程](/)
- [联系技术支持](/)

---

## ❓ 常见问题

### Q: 如何快速提升数据库健康度？
A: 参考"健康度指标体系"文档中的"快速提升健康度 - 行动清单"章节。

### Q: 不同数据库的监控重点有什么不同？
A: 
- MySQL: 关注Buffer Pool和死锁
- PostgreSQL: 关注表膨胀和VACUUM
- OceanBase: 关注合并策略和MemStore

### Q: 如何设置合理的告警阈值？
A: 每个数据库文档都包含"监控告警阈值"章节，提供详细的建议。

---

**开始探索吧！** 从左侧菜单选择您需要的文档 👈
`;
  };

  // 搜索过滤
  const filterContent = (content) => {
    if (!searchTerm) return content;
    
    // 简单的高亮实现
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    return content.replace(regex, '**$1**');
  };

  // Markdown自定义渲染
  const markdownComponents = {
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <SyntaxHighlighter
          style={darkMode ? vscDarkPlus : vs}
          language={match[1]}
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code className={className} {...props}>
          {children}
        </code>
      );
    },
    table({ children }) {
      return (
        <div style={{ overflowX: 'auto', marginBottom: '16px' }}>
          <table className="markdown-table">{children}</table>
        </div>
      );
    }
  };

  // 导出为PDF
  const handleExport = () => {
    window.print();
  };

  // 收藏功能
  const toggleFavorite = (docKey) => {
    if (favorites.includes(docKey)) {
      setFavorites(favorites.filter(f => f !== docKey));
    } else {
      setFavorites([...favorites, docKey]);
    }
  };

  return (
    <Layout className={`help-center ${darkMode ? 'dark-mode' : ''}`} style={{ minHeight: '100vh' }}>
      {/* 顶部Header */}
      <Header className="help-header" style={{ 
        background: darkMode ? '#1f1f1f' : '#fff', 
        padding: '0 24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <BookOutlined style={{ fontSize: '24px', marginRight: '12px', color: '#1890ff' }} />
          <Title level={3} style={{ margin: 0, color: darkMode ? '#fff' : '#000' }}>
            数据库性能监控 - 帮助中心
          </Title>
        </div>
        
        <Space size="middle">
          {/* 搜索框 */}
          <Search
            placeholder="搜索文档内容..."
            allowClear
            style={{ width: 300 }}
            onSearch={setSearchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          
          {/* 深色模式切换 */}
          <Tooltip title={darkMode ? '切换到浅色模式' : '切换到深色模式'}>
            <Switch
              checked={darkMode}
              onChange={setDarkMode}
              checkedChildren={<MoonOutlined />}
              unCheckedChildren={<SunOutlined />}
            />
          </Tooltip>
          
          {/* 导出按钮 */}
          <Tooltip title="导出PDF">
            <Button 
              icon={<DownloadOutlined />} 
              onClick={handleExport}
            >
              导出
            </Button>
          </Tooltip>
        </Space>
      </Header>

      <Layout>
        {/* 左侧导航 */}
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          width={280}
          style={{
            background: darkMode ? '#1f1f1f' : '#fff',
            borderRight: `1px solid ${darkMode ? '#333' : '#f0f0f0'}`
          }}
        >
          <div style={{ padding: '16px' }}>
            {!collapsed && (
              <Alert
                message={
                  <Space>
                    <BulbOutlined />
                    <span>提示</span>
                  </Space>
                }
                description="点击左侧文档开始学习，使用搜索快速查找内容。"
                type="info"
                showIcon={false}
                style={{ marginBottom: '16px' }}
              />
            )}
          </div>
          
          <Menu
            mode="inline"
            selectedKeys={[selectedDoc]}
            onClick={({ key }) => setSelectedDoc(key)}
            style={{ borderRight: 0, background: 'transparent' }}
            items={documentStructure.map(doc => ({
              key: doc.key,
              icon: doc.icon,
              label: (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{doc.label}</span>
                  {!collapsed && favorites.includes(doc.key) && (
                    <HeartOutlined style={{ color: '#ff4d4f' }} />
                  )}
                </div>
              )
            }))}
          />
        </Sider>

        {/* 主内容区 */}
        <Layout style={{ padding: '0 24px 24px' }}>
          {/* 面包屑 */}
          <Breadcrumb style={{ margin: '16px 0' }}>
            <Breadcrumb.Item href="/">
              <HomeOutlined />
              <span>首页</span>
            </Breadcrumb.Item>
            <Breadcrumb.Item>
              <BookOutlined />
              <span>帮助中心</span>
            </Breadcrumb.Item>
            <Breadcrumb.Item>
              {documentStructure.find(d => d.key === selectedDoc)?.label || '文档'}
            </Breadcrumb.Item>
          </Breadcrumb>

          <Content
            style={{
              background: darkMode ? '#1f1f1f' : '#fff',
              padding: 24,
              margin: 0,
              minHeight: 280,
            }}
          >
            {/* 文档操作栏 */}
            {selectedDoc !== 'home' && (
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                marginBottom: '24px',
                padding: '12px 0',
                borderBottom: `1px solid ${darkMode ? '#333' : '#f0f0f0'}`
              }}>
                <Space>
                  <Tag color="blue" icon={<FileTextOutlined />}>
                    {documentStructure.find(d => d.key === selectedDoc)?.label}
                  </Tag>
                  {documentStructure.find(d => d.key === selectedDoc)?.description && (
                    <Text type="secondary">
                      {documentStructure.find(d => d.key === selectedDoc)?.description}
                    </Text>
                  )}
                </Space>
                
                <Space>
                  <Tooltip title={favorites.includes(selectedDoc) ? '取消收藏' : '收藏文档'}>
                    <Button
                      type={favorites.includes(selectedDoc) ? 'primary' : 'default'}
                      icon={<HeartOutlined />}
                      onClick={() => toggleFavorite(selectedDoc)}
                      size="small"
                    >
                      {favorites.includes(selectedDoc) ? '已收藏' : '收藏'}
                    </Button>
                  </Tooltip>
                  
                  <Tooltip title="打印文档">
                    <Button
                      icon={<PrinterOutlined />}
                      onClick={() => window.print()}
                      size="small"
                    >
                      打印
                    </Button>
                  </Tooltip>
                </Space>
              </div>
            )}

            {/* 文档内容 */}
            {loading ? (
              <div style={{ textAlign: 'center', padding: '50px 0' }}>
                <Spin size="large" tip="正在加载文档..." />
              </div>
            ) : markdownContent ? (
              <div className="markdown-content">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={markdownComponents}
                >
                  {filterContent(markdownContent)}
                </ReactMarkdown>
              </div>
            ) : (
              <Empty description="暂无文档内容" />
            )}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default HelpCenter;
