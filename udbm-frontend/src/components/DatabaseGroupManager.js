import React, { useState, useEffect } from 'react';
import {
  Card, Tree, Button, Modal, Form, Input, Select, Space, message,
  Popconfirm, Tooltip, Badge, Tag, Row, Col, Statistic, Empty,
  Dropdown, Menu, Divider
} from 'antd';
import {
  FolderOutlined, FolderOpenOutlined, DatabaseOutlined,
  PlusOutlined, EditOutlined, DeleteOutlined, MoreOutlined,
  DragOutlined, GroupOutlined, SettingOutlined, FilterOutlined
} from '@ant-design/icons';

const { Option } = Select;
const { TextArea } = Input;

const DatabaseGroupManager = ({ databases = [], onGroupChange }) => {
  const [loading, setLoading] = useState(false);
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingGroup, setEditingGroup] = useState(null);
  const [form] = Form.useForm();
  const [expandedKeys, setExpandedKeys] = useState([]);
  const [selectedKeys, setSelectedKeys] = useState([]);

  useEffect(() => {
    fetchGroups();
  }, []);

  // 模拟获取分组数据
  const fetchGroups = async () => {
    setLoading(true);
    try {
      // 模拟分组数据
      const mockGroups = [
        {
          id: 1,
          name: '生产环境',
          description: '生产环境数据库实例',
          parent_id: null,
          level: 1,
          path: '/生产环境',
          children: [
            {
              id: 2,
              name: '核心业务',
              description: '核心业务系统数据库',
              parent_id: 1,
              level: 2,
              path: '/生产环境/核心业务',
              databases: ['prod-postgres-01', 'prod-postgres-02', 'prod-mysql-01']
            },
            {
              id: 3,
              name: '辅助系统',
              description: '辅助系统数据库',
              parent_id: 1,
              level: 2,
              path: '/生产环境/辅助系统',
              databases: ['prod-redis-01', 'prod-mongo-01']
            }
          ]
        },
        {
          id: 4,
          name: '测试环境',
          description: '测试环境数据库实例',
          parent_id: null,
          level: 1,
          path: '/测试环境',
          children: [
            {
              id: 5,
              name: '集成测试',
              description: '集成测试数据库',
              parent_id: 4,
              level: 2,
              path: '/测试环境/集成测试',
              databases: ['test-postgres-01', 'test-mysql-01']
            }
          ]
        },
        {
          id: 6,
          name: '开发环境',
          description: '开发环境数据库实例',
          parent_id: null,
          level: 1,
          path: '/开发环境',
          databases: ['dev-postgres-01', 'dev-mysql-01', 'dev-mongo-01']
        }
      ];
      
      setGroups(mockGroups);
      setExpandedKeys(['1', '4', '6']);
    } catch (error) {
      message.error('获取分组数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 转换为Tree组件所需的数据格式
  const convertToTreeData = (groups) => {
    return groups.map(group => ({
      key: group.id.toString(),
      title: renderGroupTitle(group),
      icon: group.children ? <FolderOutlined /> : <GroupOutlined />,
      children: group.children ? convertToTreeData(group.children) : undefined,
      group: group
    }));
  };

  // 渲染分组标题
  const renderGroupTitle = (group) => {
    const databaseCount = group.databases ? group.databases.length : 
      (group.children ? group.children.reduce((sum, child) => 
        sum + (child.databases ? child.databases.length : 0), 0) : 0);
    
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ marginRight: 8, fontWeight: 500 }}>
            {group.name}
          </span>
          <Badge count={databaseCount} size="small" />
        </div>
        <div onClick={(e) => e.stopPropagation()}>
          <Dropdown
            overlay={
              <Menu>
                <Menu.Item key="edit" icon={<EditOutlined />} onClick={() => editGroup(group)}>
                  编辑分组
                </Menu.Item>
                <Menu.Item key="addChild" icon={<PlusOutlined />} onClick={() => addChildGroup(group)}>
                  添加子分组
                </Menu.Item>
                <Menu.Divider />
                <Menu.Item key="delete" icon={<DeleteOutlined />} danger onClick={() => deleteGroup(group)}>
                  删除分组
                </Menu.Item>
              </Menu>
            }
            trigger={['click']}
          >
            <Button type="text" size="small" icon={<MoreOutlined />} />
          </Dropdown>
        </div>
      </div>
    );
  };

  // 打开创建/编辑分组模态框
  const openGroupModal = (group = null, parentGroup = null) => {
    setEditingGroup(group);
    if (group) {
      form.setFieldsValue({
        name: group.name,
        description: group.description,
        parent_id: group.parent_id
      });
    } else {
      form.resetFields();
      if (parentGroup) {
        form.setFieldsValue({ parent_id: parentGroup.id });
      }
    }
    setModalVisible(true);
  };

  // 编辑分组
  const editGroup = (group) => {
    openGroupModal(group);
  };

  // 添加子分组
  const addChildGroup = (parentGroup) => {
    openGroupModal(null, parentGroup);
  };

  // 删除分组
  const deleteGroup = (group) => {
    Modal.confirm({
      title: '确认删除分组',
      content: `确定要删除分组 "${group.name}" 吗？此操作不可撤销。`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          // 这里应该调用API删除分组
          message.success('分组删除成功');
          fetchGroups();
        } catch (error) {
          message.error('删除分组失败');
        }
      }
    });
  };

  // 关闭模态框
  const closeModal = () => {
    setModalVisible(false);
    setEditingGroup(null);
    form.resetFields();
  };

  // 提交分组表单
  const handleSubmit = async (values) => {
    try {
      if (editingGroup) {
        // 更新分组
        message.success('分组更新成功');
      } else {
        // 创建分组
        message.success('分组创建成功');
      }
      closeModal();
      fetchGroups();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 选择分组
  const handleSelect = (selectedKeys, info) => {
    setSelectedKeys(selectedKeys);
    if (selectedKeys.length > 0) {
      const selectedNode = info.node;
      setSelectedGroup(selectedNode.group);
      onGroupChange?.(selectedNode.group);
    } else {
      setSelectedGroup(null);
      onGroupChange?.(null);
    }
  };

  // 展开/收起分组
  const handleExpand = (expandedKeys) => {
    setExpandedKeys(expandedKeys);
  };

  // 获取分组中的数据库列表
  const getGroupDatabases = (group) => {
    if (!group) return [];
    
    let groupDatabases = group.databases || [];
    
    // 如果有子分组，递归获取子分组中的数据库
    if (group.children) {
      group.children.forEach(child => {
        groupDatabases = [...groupDatabases, ...getGroupDatabases(child)];
      });
    }
    
    // 根据数据库名称匹配实际的数据库对象
    return databases.filter(db => groupDatabases.includes(db.name));
  };

  const treeData = convertToTreeData(groups);
  const selectedGroupDatabases = selectedGroup ? getGroupDatabases(selectedGroup) : [];

  return (
    <Row gutter={[16, 16]}>
      {/* 左侧分组树 */}
      <Col xs={24} lg={8}>
        <Card
          title={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span>
                <GroupOutlined style={{ marginRight: 8 }} />
                数据库分组
              </span>
              <Button
                type="primary"
                size="small"
                icon={<PlusOutlined />}
                onClick={() => openGroupModal()}
              >
                新建分组
              </Button>
            </div>
          }
          bodyStyle={{ padding: '16px 0' }}
          style={{ height: '600px' }}
        >
          {treeData.length > 0 ? (
            <Tree
              showIcon
              expandedKeys={expandedKeys}
              selectedKeys={selectedKeys}
              treeData={treeData}
              onSelect={handleSelect}
              onExpand={handleExpand}
              style={{ padding: '0 16px' }}
            />
          ) : (
            <Empty
              description="暂无分组"
              style={{ marginTop: 50 }}
            >
              <Button type="primary" onClick={() => openGroupModal()}>
                创建第一个分组
              </Button>
            </Empty>
          )}
        </Card>
      </Col>

      {/* 右侧分组详情 */}
      <Col xs={24} lg={16}>
        {selectedGroup ? (
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>
                  <FolderOutlined style={{ marginRight: 8 }} />
                  {selectedGroup.name}
                </span>
                <Space>
                  <Button
                    icon={<EditOutlined />}
                    onClick={() => editGroup(selectedGroup)}
                  >
                    编辑
                  </Button>
                  <Button
                    icon={<PlusOutlined />}
                    onClick={() => addChildGroup(selectedGroup)}
                  >
                    添加子分组
                  </Button>
                </Space>
              </div>
            }
          >
            {/* 分组信息 */}
            <div style={{ marginBottom: 24 }}>
              <Row gutter={[16, 16]}>
                <Col span={8}>
                  <Statistic
                    title="数据库实例"
                    value={selectedGroupDatabases.length}
                    suffix="个"
                    prefix={<DatabaseOutlined />}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="健康实例"
                    value={selectedGroupDatabases.filter(db => db.health_status === 'healthy').length}
                    suffix={`/ ${selectedGroupDatabases.length}`}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="分组层级"
                    value={selectedGroup.level}
                    suffix="级"
                  />
                </Col>
              </Row>
              
              {selectedGroup.description && (
                <div style={{ marginTop: 16 }}>
                  <strong>描述：</strong>
                  <span style={{ color: '#666' }}>{selectedGroup.description}</span>
                </div>
              )}
              
              <div style={{ marginTop: 8 }}>
                <strong>路径：</strong>
                <Tag>{selectedGroup.path}</Tag>
              </div>
            </div>

            <Divider />

            {/* 分组中的数据库列表 */}
            <div>
              <h4 style={{ marginBottom: 16 }}>数据库实例 ({selectedGroupDatabases.length})</h4>
              {selectedGroupDatabases.length > 0 ? (
                <Row gutter={[16, 16]}>
                  {selectedGroupDatabases.map(db => (
                    <Col xs={24} sm={12} md={8} key={db.id}>
                      <Card size="small" hoverable>
                        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                          <DatabaseOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                          <strong>{db.name}</strong>
                          <Badge 
                            status={db.health_status === 'healthy' ? 'success' : 'warning'} 
                            style={{ marginLeft: 'auto' }}
                          />
                        </div>
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          {db.host}:{db.port}
                        </div>
                        <div style={{ marginTop: 8 }}>
                          <Tag size="small" color="blue">{db.environment}</Tag>
                          <Tag size="small">{db.type}</Tag>
                        </div>
                      </Card>
                    </Col>
                  ))}
                </Row>
              ) : (
                <Empty description="该分组中暂无数据库实例" />
              )}
            </div>
          </Card>
        ) : (
          <Card style={{ height: '600px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Empty
              description="请选择左侧分组查看详情"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          </Card>
        )}
      </Col>

      {/* 创建/编辑分组模态框 */}
      <Modal
        title={editingGroup ? "编辑分组" : "创建分组"}
        open={modalVisible}
        onCancel={closeModal}
        footer={null}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="分组名称"
            rules={[{ required: true, message: '请输入分组名称' }]}
          >
            <Input placeholder="例如: 生产环境核心业务" />
          </Form.Item>

          <Form.Item
            name="description"
            label="分组描述"
          >
            <TextArea
              rows={3}
              placeholder="简要描述该分组的用途和包含的数据库类型"
            />
          </Form.Item>

          <Form.Item
            name="parent_id"
            label="父分组"
          >
            <Select placeholder="选择父分组（可选）" allowClear>
              {groups.map(group => (
                <Option key={group.id} value={group.id}>
                  {group.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item style={{ textAlign: 'right', marginBottom: 0, marginTop: 24 }}>
            <Space>
              <Button onClick={closeModal}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingGroup ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Row>
  );
};

export default DatabaseGroupManager;