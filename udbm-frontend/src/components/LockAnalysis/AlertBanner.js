/**
 * 告警Banner组件
 * 
 * 用于在页面顶部显示关键告警信息
 * - 支持多种严重级别
 * - 可操作按钮
 * - 可折叠/展开
 */

import React, { useState } from 'react';
import {
  Alert,
  AlertTitle,
  Button,
  Stack,
  Link,
  Collapse,
  IconButton,
  Box,
  Chip
} from '@mui/material';
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  Close as CloseIcon
} from '@mui/icons-material';

const AlertBanner = ({ alerts = [], onActionClick, onClose }) => {
  const [dismissed, setDismissed] = useState(new Set());
  const [expanded, setExpanded] = useState(false);
  
  // 过滤已关闭的告警
  const activeAlerts = alerts.filter(alert => !dismissed.has(alert.id));
  
  // 按严重程度排序
  const sortedAlerts = [...activeAlerts].sort((a, b) => {
    const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    return severityOrder[a.severity] - severityOrder[b.severity];
  });
  
  // 如果没有告警，不显示
  if (sortedAlerts.length === 0) {
    return null;
  }
  
  // 获取最严重的告警
  const primaryAlert = sortedAlerts[0];
  const additionalCount = sortedAlerts.length - 1;
  
  // 严重级别配置
  const severityConfig = {
    critical: {
      severity: 'error',
      icon: <ErrorIcon />,
      color: 'error'
    },
    high: {
      severity: 'error',
      icon: <ErrorIcon />,
      color: 'error'
    },
    medium: {
      severity: 'warning',
      icon: <WarningIcon />,
      color: 'warning'
    },
    low: {
      severity: 'info',
      icon: <InfoIcon />,
      color: 'info'
    }
  };
  
  const config = severityConfig[primaryAlert.severity] || severityConfig.medium;
  
  // 处理操作点击
  const handleActionClick = (action) => {
    if (onActionClick) {
      onActionClick(action, primaryAlert);
    }
  };
  
  // 关闭告警
  const handleDismiss = (alertId) => {
    setDismissed(new Set([...dismissed, alertId]));
    if (onClose) {
      onClose(alertId);
    }
  };
  
  // 格式化时间
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // 秒
    
    if (diff < 60) return `${diff}秒前`;
    if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`;
    return `${Math.floor(diff / 86400)}天前`;
  };
  
  return (
    <Box sx={{ mb: 2 }}>
      {/* 主告警 */}
      <Alert
        severity={config.severity}
        icon={config.icon}
        sx={{
          borderRadius: 1,
          '& .MuiAlert-message': {
            width: '100%'
          }
        }}
        action={
          <IconButton
            size="small"
            onClick={() => handleDismiss(primaryAlert.id)}
            sx={{ ml: 1 }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        }
      >
        <Stack spacing={1}>
          {/* 标题和时间 */}
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <AlertTitle sx={{ mb: 0 }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <span>{primaryAlert.title}</span>
                <Chip
                  label={primaryAlert.severity.toUpperCase()}
                  size="small"
                  color={config.color}
                  sx={{ height: 20, fontSize: '0.7rem' }}
                />
              </Stack>
            </AlertTitle>
            <Chip
              label={formatTime(primaryAlert.timestamp)}
              size="small"
              variant="outlined"
              sx={{ height: 20, fontSize: '0.7rem' }}
            />
          </Stack>
          
          {/* 消息 */}
          <Box>{primaryAlert.message}</Box>
          
          {/* 影响对象（如果有）*/}
          {primaryAlert.affected_objects && primaryAlert.affected_objects.length > 0 && (
            <Box>
              <strong>影响对象: </strong>
              {primaryAlert.affected_objects.slice(0, 3).join(', ')}
              {primaryAlert.affected_objects.length > 3 && ` +${primaryAlert.affected_objects.length - 3}个`}
            </Box>
          )}
          
          {/* 操作按钮 */}
          {primaryAlert.recommended_actions && primaryAlert.recommended_actions.length > 0 && (
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {primaryAlert.recommended_actions.map((action) => (
                <Button
                  key={action.id}
                  size="small"
                  variant="outlined"
                  color="inherit"
                  onClick={() => handleActionClick(action)}
                >
                  {action.label}
                </Button>
              ))}
            </Stack>
          )}
          
          {/* 更多告警提示 */}
          {additionalCount > 0 && (
            <Stack direction="row" alignItems="center" spacing={1}>
              <Link
                component="button"
                underline="always"
                onClick={() => setExpanded(!expanded)}
                sx={{ cursor: 'pointer', fontSize: '0.875rem' }}
              >
                {expanded ? '收起' : `查看全部 ${additionalCount + 1} 个告警`}
              </Link>
              <IconButton
                size="small"
                onClick={() => setExpanded(!expanded)}
                sx={{
                  transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.3s'
                }}
              >
                <ExpandMoreIcon fontSize="small" />
              </IconButton>
            </Stack>
          )}
        </Stack>
      </Alert>
      
      {/* 其他告警（折叠）*/}
      {additionalCount > 0 && (
        <Collapse in={expanded}>
          <Stack spacing={1} mt={1}>
            {sortedAlerts.slice(1).map((alert) => (
              <Alert
                key={alert.id}
                severity={severityConfig[alert.severity]?.severity || 'info'}
                onClose={() => handleDismiss(alert.id)}
                sx={{ borderRadius: 1 }}
              >
                <AlertTitle>{alert.title}</AlertTitle>
                {alert.message}
              </Alert>
            ))}
          </Stack>
        </Collapse>
      )}
    </Box>
  );
};

export default AlertBanner;
