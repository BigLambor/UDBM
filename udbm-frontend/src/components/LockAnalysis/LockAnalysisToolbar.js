/**
 * 锁分析工具栏组件
 * 
 * 顶部紧凑工具栏，包含：
 * - 数据库选择
 * - 时间范围选择
 * - 实时模式开关
 * - 刷新按钮
 * - 设置和帮助
 */

import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Box,
  Stack,
  Chip,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  Lock as LockIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Help as HelpIcon,
  FiberManualRecord as LiveIcon,
  Pause as PauseIcon,
  Storage as DatabaseIcon
} from '@mui/icons-material';

// 时间范围选项
const TIME_RANGE_OPTIONS = [
  { value: '5m', label: '过去5分钟' },
  { value: '15m', label: '过去15分钟' },
  { value: '1h', label: '过去1小时' },
  { value: '6h', label: '过去6小时' },
  { value: '24h', label: '过去24小时' },
  { value: '7d', label: '过去7天' }
];

const LockAnalysisToolbar = ({
  databaseId,
  databases = [],
  timeRange = '1h',
  isLive = true,
  lastUpdate,
  refreshing = false,
  onDatabaseChange,
  onTimeRangeChange,
  onRefresh,
  onToggleLive,
  onSettings,
  onHelp
}) => {
  // 格式化相对时间
  const formatRelativeTime = (date) => {
    if (!date) return '';
    
    const now = new Date();
    const diff = Math.floor((now - new Date(date)) / 1000); // 秒
    
    if (diff < 10) return '刚刚';
    if (diff < 60) return `${diff}秒前`;
    if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`;
    return `${Math.floor(diff / 86400)}天前`;
  };
  
  // 获取数据库类型图标颜色
  const getDatabaseTypeColor = (type) => {
    const colors = {
      mysql: '#4479A1',
      postgresql: '#336791',
      oceanbase: '#FF6B35',
      oracle: '#F80000',
      sqlserver: '#CC2927'
    };
    return colors[type?.toLowerCase()] || '#666';
  };
  
  return (
    <AppBar 
      position="static" 
      color="default" 
      elevation={1}
      sx={{ 
        bgcolor: 'background.paper',
        borderBottom: 1,
        borderColor: 'divider'
      }}
    >
      <Toolbar variant="dense" sx={{ minHeight: 48, px: 2 }}>
        {/* Logo和标题 */}
        <Stack direction="row" spacing={1} alignItems="center" mr={3}>
          <LockIcon color="primary" />
          <Typography variant="h6" component="div" noWrap>
            锁分析
          </Typography>
        </Stack>
        
        {/* 数据库选择 */}
        <FormControl size="small" sx={{ minWidth: 240, mr: 2 }}>
          <Select
            value={databaseId}
            onChange={(e) => onDatabaseChange?.(e.target.value)}
            displayEmpty
            sx={{ 
              '& .MuiSelect-select': { 
                py: 0.75,
                display: 'flex',
                alignItems: 'center'
              }
            }}
          >
            {databases.map((db) => (
              <MenuItem key={db.id} value={db.id}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <DatabaseIcon 
                    fontSize="small" 
                    sx={{ color: getDatabaseTypeColor(db.type) }}
                  />
                  <Typography>{db.name}</Typography>
                  <Chip 
                    label={db.type} 
                    size="small" 
                    sx={{ 
                      height: 20, 
                      fontSize: '0.7rem',
                      backgroundColor: getDatabaseTypeColor(db.type) + '20',
                      color: getDatabaseTypeColor(db.type)
                    }} 
                  />
                </Stack>
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        
        {/* 时间范围选择 */}
        <FormControl size="small" sx={{ minWidth: 140, mr: 2 }}>
          <Select
            value={timeRange}
            onChange={(e) => onTimeRangeChange?.(e.target.value)}
            sx={{ '& .MuiSelect-select': { py: 0.75 } }}
          >
            {TIME_RANGE_OPTIONS.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        
        {/* 实时模式切换 */}
        <Tooltip title={isLive ? '实时更新已开启 (30秒)' : '点击开启实时更新'}>
          <Chip
            icon={isLive ? <LiveIcon sx={{ fontSize: 12 }} /> : <PauseIcon />}
            label={isLive ? 'Live' : 'Paused'}
            onClick={onToggleLive}
            size="small"
            color={isLive ? 'success' : 'default'}
            sx={{
              height: 28,
              fontWeight: 600,
              cursor: 'pointer',
              mr: 2,
              '& .MuiChip-icon': {
                animation: isLive ? 'pulse 2s infinite' : 'none'
              },
              '@keyframes pulse': {
                '0%': { opacity: 1 },
                '50%': { opacity: 0.5 },
                '100%': { opacity: 1 }
              }
            }}
          />
        </Tooltip>
        
        {/* 弹性空间 */}
        <Box sx={{ flexGrow: 1 }} />
        
        {/* 最后更新时间 */}
        {lastUpdate && (
          <Tooltip title={`最后更新: ${new Date(lastUpdate).toLocaleString()}`}>
            <Typography 
              variant="caption" 
              color="textSecondary" 
              sx={{ mr: 2, minWidth: 60 }}
            >
              更新于 {formatRelativeTime(lastUpdate)}
            </Typography>
          </Tooltip>
        )}
        
        {/* 刷新按钮 */}
        <Tooltip title="刷新数据 (F5)">
          <IconButton 
            size="small" 
            onClick={onRefresh}
            disabled={refreshing}
            sx={{
              animation: refreshing ? 'spin 1s linear infinite' : 'none',
              '@keyframes spin': {
                '0%': { transform: 'rotate(0deg)' },
                '100%': { transform: 'rotate(360deg)' }
              }
            }}
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>
        
        {/* 设置按钮 */}
        <Tooltip title="监控设置">
          <IconButton size="small" onClick={onSettings}>
            <SettingsIcon />
          </IconButton>
        </Tooltip>
        
        {/* 帮助按钮 */}
        <Tooltip title="帮助文档">
          <IconButton size="small" onClick={onHelp}>
            <HelpIcon />
          </IconButton>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
};

export default LockAnalysisToolbar;
