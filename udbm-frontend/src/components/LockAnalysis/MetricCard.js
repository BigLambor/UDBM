/**
 * 指标卡片组件
 * 
 * 用于展示单个KPI指标，支持：
 * - 数值展示
 * - 状态颜色编码
 * - Sparkline趋势图
 * - 变化百分比
 * - 点击交互
 */

import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Stack,
  Chip,
  useTheme
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { Sparklines, SparklinesLine } from 'react-sparklines';

const MetricCard = ({
  title,
  value,
  unit,
  trend = [],
  status = 'normal',
  changePercent,
  threshold,
  onClick,
  loading = false
}) => {
  const theme = useTheme();
  
  // 状态颜色映射
  const statusConfig = {
    good: {
      color: theme.palette.success.main,
      icon: <CheckCircleIcon fontSize="small" />,
      label: 'Good'
    },
    normal: {
      color: theme.palette.info.main,
      icon: null,
      label: 'Normal'
    },
    warning: {
      color: theme.palette.warning.main,
      icon: <WarningIcon fontSize="small" />,
      label: 'Warning'
    },
    critical: {
      color: theme.palette.error.main,
      icon: <ErrorIcon fontSize="small" />,
      label: 'Critical'
    }
  };
  
  const config = statusConfig[status] || statusConfig.normal;
  
  // 格式化数值
  const formatValue = (val) => {
    if (typeof val === 'number') {
      if (val >= 1000000) {
        return (val / 1000000).toFixed(1) + 'M';
      } else if (val >= 1000) {
        return (val / 1000).toFixed(1) + 'K';
      }
      return val.toLocaleString();
    }
    return val;
  };
  
  return (
    <Card
      sx={{
        height: 140,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.3s',
        '&:hover': onClick ? {
          boxShadow: 4,
          transform: 'translateY(-2px)'
        } : {},
        border: status === 'critical' ? `2px solid ${config.color}` : 'none'
      }}
      onClick={onClick}
      elevation={status === 'critical' ? 3 : 1}
    >
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        {/* 标题行 */}
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
          <Typography 
            variant="caption" 
            color="textSecondary"
            sx={{ fontWeight: 500, textTransform: 'uppercase' }}
          >
            {title}
          </Typography>
          {config.icon && (
            <Box sx={{ color: config.color }}>
              {config.icon}
            </Box>
          )}
        </Stack>
        
        {/* 主值 */}
        <Stack direction="row" alignItems="baseline" spacing={0.5} mb={1.5}>
          <Typography
            variant="h3"
            component="div"
            sx={{
              color: config.color,
              fontWeight: 600,
              lineHeight: 1
            }}
          >
            {loading ? '-' : formatValue(value)}
          </Typography>
          {unit && (
            <Typography variant="body2" color="textSecondary">
              {unit}
            </Typography>
          )}
        </Stack>
        
        {/* 底部信息 */}
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          {/* 变化百分比 */}
          {changePercent !== undefined && changePercent !== null && (
            <Chip
              icon={changePercent >= 0 ? <TrendingUpIcon /> : <TrendingDownIcon />}
              label={`${changePercent > 0 ? '+' : ''}${changePercent.toFixed(1)}%`}
              size="small"
              sx={{
                height: 20,
                fontSize: '0.7rem',
                fontWeight: 600,
                color: changePercent > 0 ? theme.palette.error.main : theme.palette.success.main,
                backgroundColor: changePercent > 0 
                  ? theme.palette.error.light + '20' 
                  : theme.palette.success.light + '20',
                '& .MuiChip-icon': {
                  fontSize: '0.9rem'
                }
              }}
            />
          )}
          
          {/* Sparkline趋势图 */}
          {trend && trend.length > 0 && (
            <Box sx={{ width: 80, height: 24 }}>
              <Sparklines data={trend} width={80} height={24} margin={0}>
                <SparklinesLine
                  color={config.color}
                  style={{ strokeWidth: 2, fill: 'none' }}
                />
              </Sparklines>
            </Box>
          )}
          
          {/* 状态标签（无trend和change时显示）*/}
          {!changePercent && !trend?.length && (
            <Chip
              label={config.label}
              size="small"
              sx={{
                height: 20,
                fontSize: '0.7rem',
                fontWeight: 600,
                backgroundColor: config.color + '20',
                color: config.color
              }}
            />
          )}
        </Stack>
        
        {/* 阈值指示 */}
        {threshold !== undefined && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" color="textSecondary">
              阈值: {threshold}{unit}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default MetricCard;
