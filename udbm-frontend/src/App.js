import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { Layout, Menu, Breadcrumb, Button } from 'antd';
import {
  DesktopOutlined,
  PieChartOutlined,
  FileOutlined,
  TeamOutlined,
  UserOutlined,
  DatabaseOutlined,
  SettingOutlined,
  ThunderboltOutlined,
  BarChartOutlined,
  SearchOutlined,
  SecurityScanOutlined,
  MenuOutlined,
  BookOutlined
} from '@ant-design/icons';

import './App.css';
import './animations.css';
import Dashboard from './pages/Dashboard';
import DatabaseList from './pages/DatabaseList';
import DatabaseDetail from './pages/DatabaseDetail';
import PerformanceDashboard from './pages/PerformanceDashboard';
import SlowQueryAnalysis from './pages/SlowQueryAnalysis';
import IndexOptimization from './pages/IndexOptimization';
import SystemDiagnosis from './pages/SystemDiagnosis';
import ExecutionPlanAnalysis from './pages/ExecutionPlanAnalysis';
import LockAnalysisPageAntd from './pages/LockAnalysisPageAntd';
import HelpCenter from './pages/HelpCenter';
import FloatingHelpButton from './components/FloatingHelpButton';


const { Header, Content, Footer, Sider } = Layout;
const { SubMenu } = Menu;

// 动态面包屑组件
const DynamicBreadcrumb = () => {
  const location = useLocation();
  
  const getBreadcrumbItems = (pathname) => {
    const pathMap = {
      '/': [{ title: 'UDBM' }, { title: '仪表板' }],
      '/databases': [{ title: 'UDBM' }, { title: '数据库管理' }, { title: '数据库实例' }],
      '/performance/dashboard': [{ title: 'UDBM' }, { title: '性能调优' }, { title: '性能监控' }],
      '/performance/slow-queries': [{ title: 'UDBM' }, { title: '性能调优' }, { title: '慢查询分析' }],
      '/performance/index-optimization': [{ title: 'UDBM' }, { title: '性能调优' }, { title: '索引优化' }],
      '/performance/execution-plan-analysis': [{ title: 'UDBM' }, { title: '性能调优' }, { title: '执行计划分析' }],
      '/performance/system-diagnosis': [{ title: 'UDBM' }, { title: '性能调优' }, { title: '系统诊断' }],
      '/performance/lock-analysis': [{ title: 'UDBM' }, { title: '性能调优' }, { title: '锁分析' }],
      '/help-center': [{ title: 'UDBM' }, { title: '帮助中心' }],
      '/monitoring': [{ title: 'UDBM' }, { title: '监控告警' }],
      '/backup': [{ title: 'UDBM' }, { title: '备份恢复' }],
      '/admin': [{ title: 'UDBM' }, { title: '系统管理' }],
    };
    
    // 处理数据库详情页面
    if (pathname.startsWith('/databases/') && pathname !== '/databases') {
      return [{ title: 'UDBM' }, { title: '数据库管理' }, { title: '数据库详情' }];
    }
    
    return pathMap[pathname] || [{ title: 'UDBM' }, { title: '数据库管理' }];
  };
  
  const breadcrumbItems = getBreadcrumbItems(location.pathname);
  
  return (
    <Breadcrumb style={{ margin: '16px 0' }}>
      {breadcrumbItems.map((item, index) => (
        <Breadcrumb.Item key={index}>{item.title}</Breadcrumb.Item>
      ))}
    </Breadcrumb>
  );
};

// 主要应用内容组件
const AppContent = ({ collapsed, onCollapse, handleMenuClick }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileView, setMobileView] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // 检查是否为移动端视图
  useEffect(() => {
    const checkMobileView = () => {
      const isMobile = window.innerWidth < 768;
      setMobileView(isMobile);

      // 移动端默认折叠侧边栏
      if (isMobile) {
        setSidebarCollapsed(true);
      } else {
        setSidebarCollapsed(false);
      }
    };

    checkMobileView();
    window.addEventListener('resize', checkMobileView);

    return () => {
      window.removeEventListener('resize', checkMobileView);
    };
  }, []);

  // 处理菜单点击，自动关闭移动端侧边栏
  const handleMenuItemClick = ({ key }) => {
    const pathMap = {
      '1': '/',
      '2': '/databases',
      '3': '/databases',
      '4': '/databases',
      '5': '/performance/dashboard',
      '6': '/performance/slow-queries',
      '7': '/performance/index-optimization',
      '8': '/performance/execution-plan-analysis',
      '9': '/performance/system-diagnosis',
      '10': '/performance/lock-analysis',
      '11': '/monitoring',
      '12': '/monitoring',
      '13': '/monitoring',
      '14': '/backup',
      '15': '/backup',
      '16': '/backup',
      '17': '/admin',
      '18': '/admin',
      '19': '/admin',
      '20': '/help-center',
    };

    const path = pathMap[key];
    if (path && location.pathname !== path) {
      navigate(path);

      // 在移动端，点击菜单项后自动关闭侧边栏
      if (mobileView) {
        setSidebarCollapsed(true);
        onCollapse(true);
      }
    }
  };

  // 根据路径获取当前选中的菜单项
  const getSelectedKeys = (pathname) => {
    const keyMap = {
      '/': ['1'],
      '/databases': ['2'],
      '/performance/dashboard': ['5'],
      '/performance/slow-queries': ['6'],
      '/performance/index-optimization': ['7'],
      '/performance/execution-plan-analysis': ['8'],
      '/performance/system-diagnosis': ['9'],
      '/performance/lock-analysis': ['10'],
      '/help-center': ['20'],
      '/monitoring': ['11'],
      '/backup': ['14'],
      '/admin': ['17'],
    };

    // 处理数据库详情页面
    if (pathname.startsWith('/databases/') && pathname !== '/databases') {
      return ['2'];
    }

    return keyMap[pathname] || ['1'];
  };

  const selectedKeys = getSelectedKeys(location.pathname);
  
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={mobileView ? sidebarCollapsed : collapsed}
        onCollapse={(collapsed) => {
          if (mobileView) {
            setSidebarCollapsed(collapsed);
          }
          onCollapse(collapsed);
        }}
        width={250}
        collapsedWidth={mobileView ? 0 : 80}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: mobileView ? 'absolute' : 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: mobileView ? 1000 : 'auto',
          transition: 'all 0.3s ease',
          boxShadow: mobileView && !sidebarCollapsed ? '2px 0 8px rgba(0,0,0,0.15)' : 'none',
        }}
      >
        <div className="logo" style={{ 
          height: '64px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: 'white',
          fontSize: '18px',
          fontWeight: 'bold',
          background: 'linear-gradient(135deg, #1f1f1f 0%, #2c2c2c 100%)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
          transition: 'all 0.3s ease'
        }}>
          {collapsed ? 'U' : 'UDBM'}
        </div>
        <Menu
          theme="dark"
          selectedKeys={selectedKeys}
          defaultOpenKeys={['sub2']}
          mode="inline"
          onClick={handleMenuItemClick}
          style={{ borderRight: 0 }}
        >
          <Menu.Item key="1" icon={<DesktopOutlined />}>
            仪表板
          </Menu.Item>
          <SubMenu key="sub1" icon={<DatabaseOutlined />} title="数据库管理">
            <Menu.Item key="2">数据库实例</Menu.Item>
            <Menu.Item key="3">数据库分组</Menu.Item>
            <Menu.Item key="4">连接测试</Menu.Item>
          </SubMenu>
          <SubMenu key="sub2" icon={<ThunderboltOutlined />} title="性能调优">
            <Menu.Item key="5" icon={<BarChartOutlined />}>性能监控</Menu.Item>
            <Menu.Item key="6" icon={<SearchOutlined />}>慢查询分析</Menu.Item>
            <Menu.Item key="7" icon={<DatabaseOutlined />}>索引优化</Menu.Item>
            <Menu.Item key="10" icon={<DatabaseOutlined />}>锁分析</Menu.Item>
            <Menu.Item key="8" icon={<DatabaseOutlined />}>执行计划分析</Menu.Item>
            <Menu.Item key="9" icon={<SecurityScanOutlined />}>系统诊断</Menu.Item>         
          </SubMenu>
          <SubMenu key="sub3" icon={<PieChartOutlined />} title="监控告警">
            <Menu.Item key="11">监控面板</Menu.Item>
            <Menu.Item key="12">告警规则</Menu.Item>
            <Menu.Item key="13">告警历史</Menu.Item>
          </SubMenu>
          <SubMenu key="sub4" icon={<FileOutlined />} title="备份恢复">
            <Menu.Item key="14">备份策略</Menu.Item>
            <Menu.Item key="15">备份任务</Menu.Item>
            <Menu.Item key="16">恢复记录</Menu.Item>
          </SubMenu>
          <SubMenu key="sub5" icon={<SettingOutlined />} title="系统管理">
            <Menu.Item key="17">用户管理</Menu.Item>
            <Menu.Item key="18">角色权限</Menu.Item>
            <Menu.Item key="19">系统设置</Menu.Item>
          </SubMenu>
          <Menu.Item key="20" icon={<BookOutlined />}>
            帮助中心
          </Menu.Item>
        </Menu>
      </Sider>

      {/* 移动端遮罩层 */}
      {mobileView && !sidebarCollapsed && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 999,
            transition: 'all 0.3s ease'
          }}
          onClick={() => {
            setSidebarCollapsed(true);
            onCollapse(true);
          }}
        />
      )}
      
      <Layout style={{
        marginLeft: mobileView ? 0 : (collapsed ? 80 : 250),
        transition: 'all 0.3s ease',
        position: 'relative'
      }}>
        <Header
          className="site-layout-background"
          style={{
            padding: '0',
            background: '#fff',
            boxShadow: '0 1px 4px rgba(0,21,41,.08)',
            zIndex: 10,
            position: 'relative',
            height: mobileView ? '64px' : '0px',
            minHeight: mobileView ? '64px' : '0px',
            display: mobileView ? 'flex' : 'none',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: mobileView ? '0 16px' : '0'
          }}
        >
          {mobileView && (
            <>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <Button
                  type="text"
                  icon={<MenuOutlined />}
                  onClick={() => {
                    const newCollapsed = !sidebarCollapsed;
                    setSidebarCollapsed(newCollapsed);
                    onCollapse(newCollapsed);
                  }}
                  style={{ marginRight: 16 }}
                />
                <div className="logo" style={{
                  height: '32px',
                  margin: 0,
                  background: 'linear-gradient(135deg, #1f1f1f 0%, #2c2c2c 100%)',
                  borderRadius: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  color: 'white',
                  padding: '0 12px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
                  transition: 'all 0.3s ease'
                }}>
                  UDBM
                </div>
              </div>
              <Button
                type="text"
                icon={<BookOutlined />}
                onClick={() => navigate('/help-center')}
                style={{ fontSize: '18px' }}
              />
            </>
          )}
        </Header>
        
        <Content style={{
          margin: 0,
          padding: mobileView ? '8px 16px' : '16px 24px',
          background: '#f0f2f5',
          minHeight: mobileView ? 'calc(100vh - 134px)' : 'calc(100vh - 70px)', // 减去Header和Footer的高度
          overflow: 'auto',
          transition: 'all 0.3s ease'
        }}>
          <DynamicBreadcrumb />
          <div
            className="site-layout-background"
            style={{
              padding: mobileView ? '16px' : '24px',
              background: '#fff',
              borderRadius: mobileView ? '6px' : '8px',
              boxShadow: '0 1px 3px rgba(0,21,41,.08)',
              minHeight: mobileView ? 'calc(100vh - 134px - 32px - 16px)' : 'calc(100vh - 70px - 32px - 47px)', // 减去各种边距和面包屑高度
              transition: 'all 0.3s ease'
            }}
          >
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/databases" element={<DatabaseList />} />
              <Route path="/databases/:id" element={<DatabaseDetail />} />
              <Route path="/performance/dashboard" element={<PerformanceDashboard />} />
              <Route path="/performance/slow-queries" element={<SlowQueryAnalysis />} />
              <Route path="/performance/index-optimization" element={<IndexOptimization />} />
              <Route path="/performance/execution-plan-analysis" element={<ExecutionPlanAnalysis />} />
              <Route path="/performance/system-diagnosis" element={<SystemDiagnosis />} />
              <Route path="/performance/lock-analysis" element={<LockAnalysisPageAntd />} />
              <Route path="/help-center" element={<HelpCenter />} />
            </Routes>
          </div>
        </Content>
        
        {/* 桌面端浮动帮助按钮 */}
        {!mobileView && location.pathname !== '/help-center' && <FloatingHelpButton />}
        
        <Footer style={{ 
          textAlign: 'center',
          background: '#fff',
          borderTop: '1px solid #f0f0f0',
          padding: '12px 24px',
          fontSize: '12px',
          color: '#666'
        }}>
          UDBM 统一数据库管理平台
        </Footer>
      </Layout>
    </Layout>
  );
};

class App extends React.Component {
  state = {
    collapsed: false,
  };

  onCollapse = collapsed => {
    this.setState({ collapsed });
  };

  // 注意：这个函数现在被AppContent组件内部的handleMenuItemClick替代
  // 保留是为了向后兼容，但实际上不会被调用
  handleMenuClick = ({ key }) => {
    // 这个函数不再使用，由AppContent内部处理
    console.log('handleMenuClick called with key:', key);
  };

  render() {
    const { collapsed } = this.state;
    
    return (
      <Router>
        <AppContent collapsed={collapsed} onCollapse={this.onCollapse} handleMenuClick={this.handleMenuClick} />
      </Router>
    );
  }
}

export default App;
