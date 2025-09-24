import React from 'react';
import { Alert, Card, Typography, List, Tag, Space } from 'antd';
import { InfoCircleOutlined, QuestionCircleOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

const LockAnalysisHelper = ({ databaseType }) => {
  const getDatabaseSpecificInfo = () => {
    switch (databaseType?.toLowerCase()) {
      case 'postgresql':
        return {
          title: 'PostgreSQL 锁分析说明',
          features: [
            '支持多种锁类型：表锁、行锁、页锁、Advisory锁等',
            '提供详细的等待链分析和死锁检测',
            'VACUUM操作对锁的影响监控',
            '事务级别的锁分析和优化建议'
          ],
          tips: [
            '使用pg_locks视图查看当前锁状态',
            '通过pg_stat_activity监控阻塞会话',
            '合理设置lock_timeout和deadlock_timeout',
            '定期执行VACUUM避免锁升级'
          ],
          lockTypes: [
            { name: 'AccessShareLock', desc: '读锁，SELECT操作' },
            { name: 'RowShareLock', desc: 'SELECT FOR UPDATE' },
            { name: 'RowExclusiveLock', desc: 'UPDATE/DELETE/INSERT' },
            { name: 'ShareUpdateExclusiveLock', desc: 'VACUUM/ANALYZE' },
            { name: 'AccessExclusiveLock', desc: 'ALTER TABLE/DROP TABLE' }
          ]
        };
      
      case 'mysql':
        return {
          title: 'MySQL InnoDB 锁分析说明',
          features: [
            'InnoDB行级锁：共享锁(S)和排他锁(X)',
            '间隙锁(Gap Lock)和临键锁(Next-Key Lock)',
            '意向锁(Intention Lock)机制',
            '死锁自动检测和回滚'
          ],
          tips: [
            '使用INFORMATION_SCHEMA.INNODB_LOCKS查看锁信息',
            '通过SHOW ENGINE INNODB STATUS查看锁等待',
            '合理设置innodb_lock_wait_timeout',
            '使用READ COMMITTED减少间隙锁'
          ],
          lockTypes: [
            { name: 'Record Lock', desc: '行锁，锁定索引记录' },
            { name: 'Gap Lock', desc: '间隙锁，锁定索引间隙' },
            { name: 'Next-Key Lock', desc: '临键锁，行锁+间隙锁' },
            { name: 'Insert Intention Lock', desc: '插入意向锁' },
            { name: 'AUTO-INC Lock', desc: '自增锁' }
          ]
        };
      
      case 'oceanbase':
        return {
          title: 'OceanBase 锁分析说明',
          features: [
            '分布式锁管理，支持跨节点锁协调',
            '租户级锁隔离和资源管理',
            '分区表的锁优化',
            '全局索引锁管理'
          ],
          tips: [
            '监控跨分区事务的锁开销',
            '合理设计分区键减少分布式锁',
            '使用租户资源隔离避免锁竞争',
            '优化全局索引减少锁冲突'
          ],
          lockTypes: [
            { name: 'Local Lock', desc: '本地锁，单节点内锁' },
            { name: 'Distributed Lock', desc: '分布式锁，跨节点锁' },
            { name: 'Partition Lock', desc: '分区锁' },
            { name: 'Tenant Lock', desc: '租户级锁' },
            { name: 'Global Index Lock', desc: '全局索引锁' }
          ]
        };
      
      default:
        return {
          title: '锁分析功能说明',
          features: [
            '实时监控数据库锁状态',
            '分析锁等待链和死锁',
            '提供锁优化建议',
            '历史锁数据趋势分析'
          ],
          tips: [
            '定期监控锁等待时间',
            '识别热点对象和锁竞争',
            '优化长事务减少锁持有时间',
            '合理设置锁超时参数'
          ],
          lockTypes: []
        };
    }
  };

  const info = getDatabaseSpecificInfo();

  return (
    <Card size="small" style={{ marginBottom: 16 }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <div>
          <InfoCircleOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          <Text strong>{info.title}</Text>
        </div>
        
        <div>
          <Text type="secondary">功能特性：</Text>
          <List
            size="small"
            dataSource={info.features}
            renderItem={item => (
              <List.Item style={{ padding: '4px 0', border: 'none' }}>
                <Text>• {item}</Text>
              </List.Item>
            )}
          />
        </div>

        <div>
          <Text type="secondary">优化建议：</Text>
          <List
            size="small"
            dataSource={info.tips}
            renderItem={item => (
              <List.Item style={{ padding: '4px 0', border: 'none' }}>
                <Text>• {item}</Text>
              </List.Item>
            )}
          />
        </div>

        {info.lockTypes.length > 0 && (
          <div>
            <Text type="secondary">锁类型说明：</Text>
            <div style={{ marginTop: 8 }}>
              {info.lockTypes.map((lock, index) => (
                <div key={index} style={{ marginBottom: 4 }}>
                  <Tag color="blue">{lock.name}</Tag>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {lock.desc}
                  </Text>
                </div>
              ))}
            </div>
          </div>
        )}

        <Alert
          message="提示"
          description={`锁分析数据每30秒自动刷新，您也可以手动刷新获取最新数据。${
            databaseType?.toLowerCase() === 'oceanbase' 
              ? '对于OceanBase，建议关注跨分区事务的锁开销。' 
              : databaseType?.toLowerCase() === 'mysql'
              ? '对于MySQL，注意间隙锁可能导致的并发问题。'
              : databaseType?.toLowerCase() === 'postgresql'
              ? '对于PostgreSQL，注意VACUUM操作对锁的影响。'
              : ''
          }`}
          type="info"
          showIcon
          icon={<QuestionCircleOutlined />}
        />
      </Space>
    </Card>
  );
};

export default LockAnalysisHelper;