# UDBM - 统一数据库管理平台 (前端)

## 项目概述

UDBM前端是基于React + Ant Design开发的现代化Web界面，为统一数据库管理平台提供直观易用的用户界面。

## 技术栈

- **React**: 18.x - 用户界面框架
- **Ant Design**: 5.x - 企业级UI组件库
- **React Router**: 6.x - 路由管理
- **Axios**: HTTP客户端
- **TypeScript**: 类型安全支持

## 功能特性

### MVP版本功能
- ✅ 数据库实例管理界面
- ✅ 数据库连接测试
- ✅ 响应式设计
- ✅ 现代化的UI界面
- 🔄 监控面板 (开发中)
- 🔄 告警管理 (开发中)
- 🔄 备份恢复 (开发中)

## 项目结构

```
udbm-frontend/
├── public/
│   ├── index.html          # HTML模板
│   └── favicon.ico         # 网站图标
├── src/
│   ├── components/         # 通用组件
│   ├── pages/             # 页面组件
│   │   ├── DatabaseList.js    # 数据库列表页面
│   │   └── DatabaseDetail.js  # 数据库详情页面
│   ├── services/          # API服务层
│   │   └── api.js            # API接口封装
│   ├── App.js             # 主应用组件
│   ├── App.css            # 应用样式
│   ├── index.js           # 应用入口
│   └── index.css          # 全局样式
├── package.json           # 项目依赖配置
├── Dockerfile            # Docker镜像配置
└── README.md             # 项目文档
```

## 快速开始

### 1. 环境准备

确保安装了Node.js (版本14+)和npm或yarn。

```bash
# 检查Node.js版本
node --version
npm --version
```

### 2. 安装依赖

```bash
cd udbm-frontend
npm install
```

### 3. 启动开发服务器

```bash
npm start
```

应用将在 http://localhost:3000 启动

### 4. 构建生产版本

```bash
npm run build
```

构建的文件将保存在 `build` 目录中。

## 主要页面

### 数据库实例管理

#### 数据库列表页面 (`/databases`)
- 显示所有数据库实例的列表
- 支持添加、编辑、删除数据库实例
- 实时显示数据库状态和健康状态
- 支持数据库连接测试

#### 数据库详情页面 (`/databases/:id`)
- 显示数据库实例的详细信息
- 连接信息和配置详情
- 连接测试功能
- 监控信息预览

### 功能特性

#### 数据库实例管理
- **添加数据库**: 支持添加PostgreSQL、MySQL、MongoDB、Redis等数据库实例
- **编辑数据库**: 修改数据库连接信息和配置
- **删除数据库**: 删除不需要的数据库实例
- **连接测试**: 测试数据库连接是否正常

#### 用户界面特性
- **响应式设计**: 支持桌面和移动设备
- **现代化UI**: 使用Ant Design组件库
- **直观操作**: 简洁明了的用户界面
- **实时反馈**: 操作结果及时反馈

## API集成

前端通过RESTful API与后端通信：

```javascript
// 获取数据库列表
const databases = await databaseAPI.getDatabases();

// 创建数据库实例
const newDatabase = await databaseAPI.createDatabase({
  name: "生产数据库",
  type_id: 1,
  host: "localhost",
  port: 5432,
  // ... 其他配置
});

// 测试数据库连接
const result = await databaseAPI.testConnection(databaseId);
```

## 开发指南

### 添加新页面

1. 在 `src/pages/` 目录下创建新的页面组件
2. 在 `src/App.js` 中添加路由配置
3. 如需要，在侧边栏菜单中添加导航项

### 添加API接口

在 `src/services/api.js` 中添加新的API接口：

```javascript
export const newAPI = {
  getData: () => api.get('/endpoint'),
  createData: (data) => api.post('/endpoint', data),
  updateData: (id, data) => api.put(`/endpoint/${id}`, data),
  deleteData: (id) => api.delete(`/endpoint/${id}`)
};
```

### 组件开发

遵循以下最佳实践：

- 使用函数式组件和Hooks
- 使用TypeScript进行类型检查
- 遵循Ant Design的设计规范
- 保持组件的可复用性

## 部署

### 开发环境

```bash
npm start
```

### 生产环境

```bash
npm run build
# 将build目录中的文件部署到Web服务器
```

### Docker部署

```bash
# 构建镜像
docker build -t udbm-frontend .

# 运行容器
docker run -p 3000:80 udbm-frontend
```

## 浏览器支持

- Chrome (推荐)
- Firefox
- Safari
- Edge

## 故障排除

### 常见问题

1. **端口冲突**: 如果3000端口被占用，可以使用其他端口
   ```bash
   PORT=3001 npm start
   ```

2. **API连接失败**: 确保后端服务正在运行
   ```bash
   # 检查后端服务状态
   curl http://localhost:8000/api/v1/health/
   ```

3. **依赖安装失败**: 清除缓存后重新安装
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情
