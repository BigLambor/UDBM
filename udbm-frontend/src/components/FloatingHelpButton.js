import React from 'react';
import { Button, Tooltip } from 'antd';
import { QuestionCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

/**
 * 浮动帮助按钮组件
 * 固定在页面右下角，提供快速访问帮助中心的入口
 * 符合现代 SaaS 应用的 UX 最佳实践
 */
const FloatingHelpButton = () => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate('/help-center');
  };

  return (
    <Tooltip title="帮助中心" placement="left">
      <Button
        type="primary"
        shape="circle"
        size="large"
        icon={<QuestionCircleOutlined style={{ fontSize: '24px' }} />}
        onClick={handleClick}
        style={{
          position: 'fixed',
          right: '24px',
          bottom: '24px',
          width: '56px',
          height: '56px',
          zIndex: 1000,
          boxShadow: '0 4px 12px rgba(24, 144, 255, 0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      />
    </Tooltip>
  );
};

export default FloatingHelpButton;
