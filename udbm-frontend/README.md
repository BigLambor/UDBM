# UDBM - 统一数据库管理平台 (前端)

## 项目概述

UDBM前端是基于React 18 + Ant Design 5开发的现代化Web应用，为统一数据库管理平台提供直观易用的用户界面。支持数据库管理、性能监控、智能调优等功能的可视化操作。

## 技术栈

- **React**: 18.2+ - 现代化用户界面框架
- **Ant Design**: 5.12+ - 企业级UI组件库
- **React Router**: 6.20+ - 单页应用路由管理
- **Axios**: 1.6+ - HTTP客户端库
- **Ant Design Charts**: 1.4+ - 数据可视化组件
- **React Hooks**: 状态管理和副作用处理
- **CSS3**: 现代化样式和动画效果

## 功能特性

### 🚀 核心功能
- ✅ **数据库实例管理**: 添加、编辑、删除、查看数据库实例
- ✅ **多数据库支持**: PostgreSQL、MySQL、MongoDB、Redis
- ✅ **连接测试**: 实时测试数据库连接状态
- ✅ **响应式设计**: 适配桌面、平板、移动设备
- ✅ **现代化UI**: 基于Ant Design的企业级界面

### 🔧 性能调优功能
- ✅ **性能监控面板**: 实时显示数据库性能指标
- ✅ **慢查询分析**: 可视化慢查询分析和优化建议
- ✅ **执行计划分析**: SQL执行计划的图形化展示
- ✅ **索引优化**: 索引使用情况分析和优化建议
- ✅ **系统诊断**: 数据库健康状态和系统资源监控
- ✅ **配置优化**: 数据库配置参数优化建议

### 🎨 用户体验功能
- ✅ **主题切换**: 支持亮色/暗色主题
- ✅ **动画效果**: 流畅的页面切换和交互动画
- ✅ **数据可视化**: 丰富的图表和指标展示
- ✅ **实时更新**: 自动刷新数据和状态
- ✅ **操作反馈**: 及时的成功/错误提示

### 🔄 开发中功能
- 🔄 用户认证和权限管理界面
- 🔄 告警管理和通知中心
- 🔄 备份恢复管理界面
- 🔄 数据库迁移工具界面
- 🔄 批量操作功能

## 项目结构

```
udbm-frontend/
├── public/
│   ├── index.html              # HTML模板
│   └── favicon.ico             # 网站图标
├── src/
│   ├── components/             # 通用组件
│   │   ├── DatabaseSelector.js           # 数据库选择器
│   │   ├── PerformanceMetricCard.js      # 性能指标卡片
│   │   ├── DatabaseSpecificMetrics.js    # 数据库特定指标
│   │   └── DataSourceIndicator.js        # 数据源指示器
│   ├── pages/                  # 页面组件
│   │   ├── Dashboard.js                  # 主仪表板
│   │   ├── DatabaseList.js               # 数据库列表
│   │   ├── DatabaseDetail.js             # 数据库详情
│   │   ├── PerformanceDashboard.js       # 性能监控面板
│   │   ├── SlowQueryAnalysis.js          # 慢查询分析
│   │   ├── IndexOptimization.js          # 索引优化
│   │   ├── ExecutionPlanAnalysis.js      # 执行计划分析
│   │   ├── SystemDiagnosis.js            # 系统诊断
│   │   └── DataSourceDemo.js             # 数据源演示
│   ├── services/               # API服务层
│   │   └── api.js              # API接口封装
│   ├── App.js                  # 主应用组件
│   ├── App.css                 # 应用样式
│   ├── animations.css          # 动画样式
│   ├── index.js                # 应用入口
│   └── index.css               # 全局样式
├── package.json                # 项目依赖配置
├── package-lock.json           # 依赖锁定文件
├── Dockerfile                  # Docker镜像配置
└── README.md                   # 项目文档
```

## 快速开始

### 1. 环境准备

确保安装了Node.js和npm：

```bash
# 检查Node.js版本 (需要 14.0+)
node --version

# 检查npm版本
npm --version
```

推荐版本：
- Node.js: 18.0+ (LTS)
- npm: 9.0+

### 2. 安装依赖

```bash
cd udbm-frontend

# 安装依赖
npm install

# 或使用yarn
yarn install
```

### 3. 启动开发服务器

```bash
# 启动开发服务器
npm start

# 或使用yarn
yarn start
```

应用将在 http://localhost:3000 启动，并自动打开浏览器。

### 4. 构建生产版本

```bash
# 构建生产版本
npm run build

# 构建的文件将保存在 build/ 目录中
```

### 5. 代码检查和格式化

```bash
# 运行ESLint检查
npm run lint

# 自动修复ESLint问题
npm run lint:fix

# 运行测试
npm test
```

## 页面功能详解

### 主仪表板 (`/`)
- **功能**: 项目总览和快速导航
- **特性**: 
  - 数据库实例统计
  - 性能指标概览
  - 快速操作入口
  - 系统状态监控

### 数据库管理

#### 数据库列表页面 (`/databases`)
- **功能**: 管理所有数据库实例
- **特性**:
  - 数据库实例列表展示
  - 支持添加、编辑、删除操作
  - 实时连接状态显示
  - 批量操作支持
  - 搜索和筛选功能

#### 数据库详情页面 (`/databases/:id`)
- **功能**: 查看单个数据库实例详情
- **特性**:
  - 连接信息展示
  - 配置参数查看
  - 连接测试功能
  - 性能指标预览
  - 操作历史记录

### 性能调优功能

#### 性能监控面板 (`/performance/dashboard`)
- **功能**: 实时性能监控和可视化
- **特性**:
  - 实时性能指标图表
  - 多维度数据展示
  - 自定义时间范围
  - 性能趋势分析
  - 告警状态显示

#### 慢查询分析 (`/performance/slow-queries`)
- **功能**: 慢查询识别和优化建议
- **特性**:
  - 慢查询列表展示
  - 查询执行统计
  - 优化建议展示
  - 查询性能对比
  - 历史趋势分析

#### 索引优化 (`/performance/index-optimization`)
- **功能**: 索引使用分析和优化建议
- **特性**:
  - 索引使用情况统计
  - 缺失索引检测
  - 重复索引识别
  - 索引优化建议
  - 索引性能影响分析

#### 执行计划分析 (`/performance/execution-plan-analysis`)
- **功能**: SQL执行计划可视化分析
- **特性**:
  - 执行计划树形展示
  - 性能瓶颈识别
  - 成本分析
  - 优化建议生成
  - 计划对比功能

#### 系统诊断 (`/performance/system-diagnosis`)
- **功能**: 数据库系统健康诊断
- **特性**:
  - 系统资源监控
  - 数据库健康评估
  - 性能瓶颈诊断
  - 配置问题检测
  - 优化建议汇总

## 组件库

### 通用组件

#### DatabaseSelector
```javascript
import DatabaseSelector from '../components/DatabaseSelector';

<DatabaseSelector
  value={selectedDatabase}
  onChange={handleDatabaseChange}
  showAll={true}
  filterByType="postgresql"
/>
```

#### PerformanceMetricCard
```javascript
import PerformanceMetricCard from '../components/PerformanceMetricCard';

<PerformanceMetricCard
  title="CPU使用率"
  value={75}
  unit="%"
  trend="up"
  color="#1890ff"
/>
```

#### DatabaseSpecificMetrics
```javascript
import DatabaseSpecificMetrics from '../components/DatabaseSpecificMetrics';

<DatabaseSpecificMetrics
  databaseId={1}
  databaseType="postgresql"
  refreshInterval={30000}
/>
```

## API集成

前端通过RESTful API与后端通信：

### 数据库管理API

```javascript
import { databaseAPI } from '../services/api';

// 获取数据库列表
const databases = await databaseAPI.getDatabases();

// 创建数据库实例
const newDatabase = await databaseAPI.createDatabase({
  name: "生产数据库",
  type_id: 1,
  host: "localhost",
  port: 5432,
  database_name: "myapp_prod",
  environment: "production"
});

// 测试数据库连接
const result = await databaseAPI.testConnection(databaseId);
```

### 性能调优API

```javascript
import { performanceAPI } from '../services/api';

// 获取慢查询
const slowQueries = await performanceAPI.getSlowQueries(databaseId);

// 分析SQL查询
const analysis = await performanceAPI.analyzeQuery(databaseId, {
  query: "SELECT * FROM users WHERE created_at > '2024-01-01'"
});

// 获取执行计划
const executionPlan = await performanceAPI.getExecutionPlan(databaseId, {
  query: "SELECT u.*, p.name FROM users u JOIN profiles p ON u.id = p.user_id"
});

// 获取系统指标
const metrics = await performanceAPI.getSystemMetrics(databaseId);
```

## 开发指南

### 添加新页面

1. **创建页面组件**
   
   在 `src/pages/` 目录下创建新的页面组件：

   ```javascript
   // src/pages/NewFeature.js
   import React, { useState, useEffect } from 'react';
   import { Card, Table, Button } from 'antd';

   const NewFeature = () => {
     const [data, setData] = useState([]);

     return (
       <div>
         <Card title="新功能">
           {/* 页面内容 */}
         </Card>
       </div>
     );
   };

   export default NewFeature;
   ```

2. **添加路由配置**
   
   在 `src/App.js` 中添加路由：

   ```javascript
   import NewFeature from './pages/NewFeature';

   // 在Routes中添加
   <Route path="/new-feature" element={<NewFeature />} />
   ```

3. **添加菜单项**
   
   在 `src/App.js` 的菜单配置中添加新项：

   ```javascript
   const menuItems = [
     // ... 其他菜单项
     {
       key: 'new-feature',
       icon: <SettingOutlined />,
       label: '新功能',
       onClick: () => navigate('/new-feature')
     }
   ];
   ```

### 添加新组件

在 `src/components/` 目录下创建可复用组件：

```javascript
// src/components/CustomChart.js
import React from 'react';
import { Card } from 'antd';
import { Line } from '@ant-design/charts';

const CustomChart = ({ data, title }) => {
  const config = {
    data,
    xField: 'time',
    yField: 'value',
    smooth: true,
  };

  return (
    <Card title={title}>
      <Line {...config} />
    </Card>
  );
};

export default CustomChart;
```

### 添加API接口

在 `src/services/api.js` 中添加新的API接口：

```javascript
// 添加新的API模块
export const newFeatureAPI = {
  getData: () => api.get('/new-feature/data'),
  createItem: (data) => api.post('/new-feature/items', data),
  updateItem: (id, data) => api.put(`/new-feature/items/${id}`, data),
  deleteItem: (id) => api.delete(`/new-feature/items/${id}`)
};
```

### 状态管理

使用React Hooks进行状态管理：

```javascript
import React, { useState, useEffect, useCallback } from 'react';

const MyComponent = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 使用useCallback优化性能
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getData();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    // JSX内容
  );
};
```

## 样式和主题

### 自定义主题

在 `src/App.css` 中自定义Ant Design主题：

```css
/* 自定义主题变量 */
:root {
  --primary-color: #1890ff;
  --success-color: #52c41a;
  --warning-color: #faad14;
  --error-color: #ff4d4f;
}

/* 自定义组件样式 */
.custom-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.performance-metric {
  text-align: center;
  padding: 16px;
}
```

### 响应式设计

使用CSS媒体查询实现响应式布局：

```css
/* 桌面端 */
@media (min-width: 1200px) {
  .dashboard-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* 平板端 */
@media (min-width: 768px) and (max-width: 1199px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 移动端 */
@media (max-width: 767px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
```

### 动画效果

在 `src/animations.css` 中定义动画：

```css
/* 淡入动画 */
.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 滑入动画 */
.slide-in {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
```

## 部署

### 开发环境

```bash
# 启动开发服务器
npm start

# 应用将在 http://localhost:3000 启动
```

### 生产环境

```bash
# 构建生产版本
npm run build

# 使用静态文件服务器部署
npx serve -s build

# 或使用nginx部署
# 将build目录中的文件复制到nginx的html目录
```

### Docker部署

```bash
# 构建Docker镜像
docker build -t udbm-frontend:latest .

# 运行容器
docker run -p 3000:80 udbm-frontend:latest

# 或使用docker-compose
docker-compose up -d frontend
```

### Nginx配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /usr/share/nginx/html;
    index index.html;

    # 处理React Router
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 性能优化

### 代码分割

使用React.lazy进行代码分割：

```javascript
import React, { Suspense } from 'react';
import { Spin } from 'antd';

// 懒加载组件
const PerformanceDashboard = React.lazy(() => import('./pages/PerformanceDashboard'));

const App = () => {
  return (
    <Suspense fallback={<Spin size="large" />}>
      <PerformanceDashboard />
    </Suspense>
  );
};
```

### 组件优化

使用React.memo优化组件渲染：

```javascript
import React, { memo } from 'react';

const PerformanceMetricCard = memo(({ title, value, unit }) => {
  return (
    <Card>
      <div>{title}</div>
      <div>{value}{unit}</div>
    </Card>
  );
});

export default PerformanceMetricCard;
```

### 数据获取优化

```javascript
// 使用防抖优化搜索
import { debounce } from 'lodash';

const SearchComponent = () => {
  const debouncedSearch = useCallback(
    debounce((searchTerm) => {
      // 执行搜索
    }, 300),
    []
  );

  return (
    <Input
      placeholder="搜索..."
      onChange={(e) => debouncedSearch(e.target.value)}
    />
  );
};
```

## 浏览器支持

- **Chrome**: 90+ (推荐)
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+
- **移动端**: iOS Safari 14+, Android Chrome 90+

## 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 使用其他端口启动
   PORT=3001 npm start
   ```

2. **API连接失败**
   ```bash
   # 检查后端服务状态
   curl http://localhost:8000/api/v1/health/
   
   # 检查代理配置
   # 确保package.json中的proxy配置正确
   ```

3. **依赖安装失败**
   ```bash
   # 清除缓存后重新安装
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **构建失败**
   ```bash
   # 检查内存使用
   export NODE_OPTIONS="--max-old-space-size=4096"
   npm run build
   ```

### 调试技巧

1. **使用React Developer Tools**
2. **启用详细日志**：在开发环境中设置 `REACT_APP_LOG_LEVEL=debug`
3. **网络请求调试**：在浏览器开发者工具中查看Network面板
4. **性能分析**：使用React Profiler分析组件性能

## 贡献指南

### 代码规范

- 使用ESLint和Prettier进行代码格式化
- 遵循React Hooks最佳实践
- 编写有意义的组件和函数名
- 添加适当的PropTypes或TypeScript类型
- 编写单元测试

```bash
# 代码格式化
npm run lint:fix

# 运行测试
npm test

# 类型检查 (如果使用TypeScript)
npm run type-check
```

### 提交规范

使用约定式提交格式：

```
feat: 添加新的性能监控图表
fix: 修复数据库连接测试问题
docs: 更新API文档
style: 调整按钮样式
refactor: 重构数据获取逻辑
test: 添加组件单元测试
```

### Pull Request流程

1. Fork项目到自己的仓库
2. 创建特性分支 (`git checkout -b feature/new-feature`)
3. 提交更改 (`git commit -m 'feat: add new feature'`)
4. 推送到分支 (`git push origin feature/new-feature`)
5. 创建Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 更新日志

### v1.2.0 (2024-12)
- 添加完整的性能调优功能界面
- 新增慢查询分析页面
- 实现执行计划可视化
- 添加系统诊断和监控面板
- 优化响应式设计和用户体验

### v1.1.0 (2024-11)
- 添加多数据库类型支持界面
- 改进数据库列表和详情页面
- 增强连接测试功能
- 添加数据可视化图表
- 优化移动端适配

### v1.0.0 (2024-10)
- 初始版本发布
- 基础数据库管理界面
- React + Ant Design架构
- 响应式设计实现

---

*最后更新: 2024年*