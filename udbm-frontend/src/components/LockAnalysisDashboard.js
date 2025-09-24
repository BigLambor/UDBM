import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Grid,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Lock as LockIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { performanceAPI } from '../services/api';

const LockAnalysisDashboard = ({ databaseId }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [optimizationDialogOpen, setOptimizationDialogOpen] = useState(false);
  const [selectedOptimization, setSelectedOptimization] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // 30秒刷新一次
    return () => clearInterval(interval);
  }, [databaseId]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await performanceAPI.get(`/performance-tuning/lock-analysis/dashboard/${databaseId}`);
      setDashboardData(response.data);
      setError(null);
    } catch (err) {
      setError('获取锁分析数据失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleOptimizationClick = (optimization) => {
    setSelectedOptimization(optimization);
    setOptimizationDialogOpen(true);
  };

  const getHealthScoreColor = (score) => {
    if (score >= 90) return '#4caf50';
    if (score >= 70) return '#ff9800';
    if (score >= 50) return '#ff5722';
    return '#f44336';
  };

  const getSeverityColor = (severity) => {
    const colors = {
      low: '#4caf50',
      medium: '#ff9800',
      high: '#ff5722',
      critical: '#f44336'
    };
    return colors[severity] || '#757575';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <LinearProgress style={{ width: '100%' }} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={fetchDashboardData}>
          重试
        </Button>
      }>
        {error}
      </Alert>
    );
  }

  if (!dashboardData) {
    return (
      <Alert severity="info">
        暂无锁分析数据
      </Alert>
    );
  }

  const {
    overall_health_score,
    lock_efficiency_score,
    contention_severity,
    current_locks,
    waiting_locks,
    deadlock_count_today,
    timeout_count_today,
    hot_objects,
    active_wait_chains,
    top_contentions,
    optimization_suggestions,
    lock_trends
  } = dashboardData;

  const trendData = lock_trends?.wait_time?.map((point, index) => ({
    time: new Date(point.timestamp).toLocaleTimeString(),
    waitTime: point.value,
    contentionCount: lock_trends.contention_count?.[index]?.value || 0
  })) || [];

  const lockTypeData = [
    { name: '表锁', value: current_locks - waiting_locks, color: '#8884d8' },
    { name: '行锁', value: waiting_locks, color: '#82ca9d' },
    { name: '页锁', value: Math.floor(current_locks * 0.3), color: '#ffc658' }
  ];

  return (
    <Box>
      {/* 头部操作栏 */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          <LockIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          数据库锁分析
        </Typography>
        <Box>
          <Tooltip title="刷新数据">
            <IconButton onClick={fetchDashboardData} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="生成报告">
            <IconButton color="primary">
              <DownloadIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="监控设置">
            <IconButton color="primary">
              <SettingsIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* 关键指标卡片 */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    整体健康评分
                  </Typography>
                  <Typography variant="h4" style={{ color: getHealthScoreColor(overall_health_score) }}>
                    {overall_health_score.toFixed(1)}
                  </Typography>
                </Box>
                <CheckCircleIcon style={{ color: getHealthScoreColor(overall_health_score), fontSize: 40 }} />
              </Box>
              <LinearProgress
                variant="determinate"
                value={overall_health_score}
                style={{ marginTop: 8 }}
                sx={{
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: getHealthScoreColor(overall_health_score)
                  }
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    当前锁数量
                  </Typography>
                  <Typography variant="h4" color="primary">
                    {current_locks}
                  </Typography>
                </Box>
                <LockIcon color="primary" style={{ fontSize: 40 }} />
              </Box>
              <Typography variant="body2" color="textSecondary">
                等待中: {waiting_locks}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    今日死锁
                  </Typography>
                  <Typography variant="h4" color={deadlock_count_today > 0 ? 'error' : 'success'}>
                    {deadlock_count_today}
                  </Typography>
                </Box>
                {deadlock_count_today > 0 ? <ErrorIcon color="error" style={{ fontSize: 40 }} /> : <CheckCircleIcon color="success" style={{ fontSize: 40 }} />}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    竞争严重程度
                  </Typography>
                  <Chip
                    label={contention_severity}
                    color={contention_severity === 'low' ? 'success' : contention_severity === 'medium' ? 'warning' : 'error'}
                    size="small"
                  />
                </Box>
                <WarningIcon style={{ color: getSeverityColor(contention_severity), fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 标签页内容 */}
      <Card>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab icon={<TimelineIcon />} label="趋势分析" />
          <Tab icon={<AssessmentIcon />} label="竞争分析" />
          <Tab icon={<LockIcon />} label="等待链" />
          <Tab icon={<SettingsIcon />} label="优化建议" />
        </Tabs>

        <CardContent>
          {/* 趋势分析标签页 */}
          {activeTab === 0 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <Typography variant="h6" gutterBottom>
                  锁等待时间趋势
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <RechartsTooltip />
                    <Line type="monotone" dataKey="waitTime" stroke="#8884d8" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </Grid>

              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>
                  锁类型分布
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={lockTypeData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {lockTypeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Grid>
            </Grid>
          )}

          {/* 竞争分析标签页 */}
          {activeTab === 1 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                热点对象竞争分析
              </Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>对象名称</TableCell>
                      <TableCell align="right">竞争次数</TableCell>
                      <TableCell align="right">总等待时间(s)</TableCell>
                      <TableCell align="right">平均等待时间(s)</TableCell>
                      <TableCell align="center">优先级</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {hot_objects?.map((obj, index) => (
                      <TableRow key={index}>
                        <TableCell>{obj.object_name}</TableCell>
                        <TableCell align="right">{obj.contention_count}</TableCell>
                        <TableCell align="right">{obj.total_wait_time?.toFixed(2)}</TableCell>
                        <TableCell align="right">{obj.avg_wait_time?.toFixed(2)}</TableCell>
                        <TableCell align="center">
                          <Chip
                            label={obj.priority_level || 'medium'}
                            color={obj.priority_level === 'high' ? 'error' : obj.priority_level === 'medium' ? 'warning' : 'default'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {/* 等待链标签页 */}
          {activeTab === 2 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                活跃等待链
              </Typography>
              {active_wait_chains?.length > 0 ? (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>链ID</TableCell>
                        <TableCell align="right">链长度</TableCell>
                        <TableCell align="right">总等待时间(s)</TableCell>
                        <TableCell align="center">严重程度</TableCell>
                        <TableCell>头会话</TableCell>
                        <TableCell>尾会话</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {active_wait_chains.map((chain, index) => (
                        <TableRow key={index}>
                          <TableCell>{chain.chain_id}</TableCell>
                          <TableCell align="right">{chain.chain_length}</TableCell>
                          <TableCell align="right">{chain.total_wait_time?.toFixed(2)}</TableCell>
                          <TableCell align="center">
                            <Chip
                              label={chain.severity_level}
                              color={chain.severity_level === 'critical' ? 'error' : chain.severity_level === 'high' ? 'warning' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{chain.head_session_id}</TableCell>
                          <TableCell>{chain.tail_session_id}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info">当前无活跃等待链</Alert>
              )}
            </Box>
          )}

          {/* 优化建议标签页 */}
          {activeTab === 3 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                锁优化建议
              </Typography>
              {optimization_suggestions?.map((suggestion, index) => (
                <Card key={index} sx={{ mb: 2 }}>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                      <Box flex={1}>
                        <Typography variant="h6" color="primary">
                          {suggestion.title}
                        </Typography>
                        <Typography variant="body2" color="textSecondary" paragraph>
                          {suggestion.description}
                        </Typography>
                        <Box>
                          <Typography variant="subtitle2" gutterBottom>
                            建议操作:
                          </Typography>
                          <ul>
                            {suggestion.actions?.map((action, actionIndex) => (
                              <li key={actionIndex}>
                                <Typography variant="body2">{action}</Typography>
                              </li>
                            ))}
                          </ul>
                        </Box>
                      </Box>
                      <Box ml={2}>
                        <Chip
                          label={suggestion.priority}
                          color={suggestion.priority === 'high' ? 'error' : suggestion.priority === 'medium' ? 'warning' : 'default'}
                          size="small"
                        />
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => handleOptimizationClick(suggestion)}
                          sx={{ mt: 1, display: 'block' }}
                        >
                          查看详情
                        </Button>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* 优化详情对话框 */}
      <Dialog
        open={optimizationDialogOpen}
        onClose={() => setOptimizationDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          锁优化详情
        </DialogTitle>
        <DialogContent>
          {selectedOptimization && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedOptimization.title}
              </Typography>
              <Typography variant="body1" paragraph>
                {selectedOptimization.description}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                优化类型: {selectedOptimization.type}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                优先级: 
                <Chip
                  label={selectedOptimization.priority}
                  color={selectedOptimization.priority === 'high' ? 'error' : 'warning'}
                  size="small"
                  sx={{ ml: 1 }}
                />
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                建议操作:
              </Typography>
              <ul>
                {selectedOptimization.actions?.map((action, index) => (
                  <li key={index}>
                    <Typography variant="body2">{action}</Typography>
                  </li>
                ))}
              </ul>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOptimizationDialogOpen(false)}>
            关闭
          </Button>
          <Button variant="contained" color="primary">
            应用优化
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LockAnalysisDashboard;
