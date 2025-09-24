import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Tabs,
  Tab,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import {
  Lock as LockIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Add as AddIcon,
  Visibility as ViewIcon
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import LockAnalysisDashboard from '../components/LockAnalysisDashboard';
import { performanceAPI } from '../services/api';

const LockAnalysisPage = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [databaseId, setDatabaseId] = useState(1); // 默认数据库ID
  const [databases, setDatabases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 分析相关状态
  const [analysisDialogOpen, setAnalysisDialogOpen] = useState(false);
  const [analysisType, setAnalysisType] = useState('realtime');
  const [timeRange, setTimeRange] = useState(24);
  const [analysisResult, setAnalysisResult] = useState(null);
  
  // 监控相关状态
  const [monitoringStatus, setMonitoringStatus] = useState(null);
  const [monitoringDialogOpen, setMonitoringDialogOpen] = useState(false);
  const [collectionInterval, setCollectionInterval] = useState(60);
  
  // 报告相关状态
  const [reports, setReports] = useState([]);
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [reportType, setReportType] = useState('custom');
  const [reportDays, setReportDays] = useState(7);

  useEffect(() => {
    fetchDatabases();
    fetchMonitoringStatus();
    fetchReports();
  }, []);

  const fetchDatabases = async () => {
    try {
      const response = await performanceAPI.getDatabases();
      setDatabases(response);
    } catch (err) {
      console.error('获取数据库列表失败:', err);
    }
  };

  const fetchMonitoringStatus = async () => {
    try {
      const response = await performanceAPI.getLockMonitoringStatus(databaseId);
      setMonitoringStatus(response);
    } catch (err) {
      console.error('获取监控状态失败:', err);
    }
  };

  const fetchReports = async () => {
    try {
      const response = await performanceAPI.getLockAnalysisReports(databaseId);
      setReports(response);
    } catch (err) {
      console.error('获取报告列表失败:', err);
    }
  };

  const handleAnalysis = async () => {
    try {
      setLoading(true);
      const response = await performanceAPI.analyzeLocks(databaseId, {
        database_id: databaseId,
        analysis_type: analysisType,
        time_range_hours: timeRange,
        include_wait_chains: true,
        include_contention: true,
        min_wait_time: 0.1
      });
      setAnalysisResult(response);
      setAnalysisDialogOpen(false);
    } catch (err) {
      setError('分析失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleStartMonitoring = async () => {
    try {
      await performanceAPI.startLockMonitoring(databaseId, collectionInterval);
      setMonitoringDialogOpen(false);
      fetchMonitoringStatus();
    } catch (err) {
      setError('启动监控失败: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleStopMonitoring = async () => {
    try {
      await performanceAPI.stopLockMonitoring(databaseId);
      fetchMonitoringStatus();
    } catch (err) {
      setError('停止监控失败: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleGenerateReport = async () => {
    try {
      setLoading(true);
      await performanceAPI.generateLockAnalysisReport(databaseId, reportType, reportDays);
      setReportDialogOpen(false);
      fetchReports();
    } catch (err) {
      setError('生成报告失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const getMonitoringStatusColor = (status) => {
    switch (status) {
      case 'running': return 'success';
      case 'stopped': return 'error';
      case 'paused': return 'warning';
      default: return 'default';
    }
  };

  const getMonitoringStatusText = (status) => {
    switch (status) {
      case 'running': return '运行中';
      case 'stopped': return '已停止';
      case 'paused': return '已暂停';
      default: return '未知';
    }
  };

  return (
    <Container maxWidth="xl">
      <Box py={3}>
        {/* 页面标题和操作栏 */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1">
            <LockIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            数据库锁分析
          </Typography>
          <Box>
            <Button
              variant="outlined"
              startIcon={<PlayIcon />}
              onClick={() => setAnalysisDialogOpen(true)}
              sx={{ mr: 1 }}
            >
              执行分析
            </Button>
            <Button
              variant="outlined"
              startIcon={<SettingsIcon />}
              onClick={() => setMonitoringDialogOpen(true)}
              sx={{ mr: 1 }}
            >
              监控设置
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => setReportDialogOpen(true)}
            >
              生成报告
            </Button>
          </Box>
        </Box>

        {/* 数据库选择 */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth>
                  <InputLabel>选择数据库</InputLabel>
                  <Select
                    value={databaseId}
                    onChange={(e) => setDatabaseId(e.target.value)}
                    label="选择数据库"
                  >
                    {databases.map((db) => (
                      <MenuItem key={db.id} value={db.id}>
                        {db.name} ({db.type})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Chip
                  label={`监控状态: ${getMonitoringStatusText(monitoringStatus?.status)}`}
                  color={getMonitoringStatusColor(monitoringStatus?.status)}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Chip
                  label={`收集间隔: ${monitoringStatus?.collection_interval || 60}秒`}
                  color="primary"
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Chip
                  label={`已收集事件: ${monitoringStatus?.total_events_collected || 0}`}
                  color="info"
                  variant="outlined"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* 错误提示 */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* 加载指示器 */}
        {loading && <LinearProgress sx={{ mb: 3 }} />}

        {/* 主要内容标签页 */}
        <Card>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab icon={<TimelineIcon />} label="实时监控" />
            <Tab icon={<AssessmentIcon />} label="历史分析" />
            <Tab icon={<SettingsIcon />} label="优化任务" />
            <Tab icon={<DownloadIcon />} label="分析报告" />
          </Tabs>

          <CardContent>
            {/* 实时监控标签页 */}
            {activeTab === 0 && (
              <LockAnalysisDashboard databaseId={databaseId} />
            )}

            {/* 历史分析标签页 */}
            {activeTab === 1 && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  历史锁分析
                </Typography>
                {analysisResult ? (
                  <Box>
                    <Alert severity="success" sx={{ mb: 2 }}>
                      分析完成 - {analysisResult.analysis_timestamp}
                    </Alert>
                    <Grid container spacing={3}>
                      <Grid item xs={12} md={6}>
                        <Card>
                          <CardHeader title="分析结果概览" />
                          <CardContent>
                            <Typography variant="body2" paragraph>
                              分析类型: {analysisResult.analysis_type}
                            </Typography>
                            <Typography variant="body2" paragraph>
                              数据库ID: {analysisResult.database_id}
                            </Typography>
                            <Typography variant="body2">
                              分析时间: {new Date(analysisResult.analysis_timestamp).toLocaleString()}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Card>
                          <CardHeader title="关键指标" />
                          <CardContent>
                            <Typography variant="body2" paragraph>
                              健康评分: {analysisResult.result?.health_score?.toFixed(1) || 'N/A'}
                            </Typography>
                            <Typography variant="body2" paragraph>
                              当前锁数: {analysisResult.result?.current_locks?.length || 0}
                            </Typography>
                            <Typography variant="body2">
                              等待链数: {analysisResult.result?.wait_chains?.length || 0}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>
                  </Box>
                ) : (
                  <Alert severity="info">
                    请先执行锁分析
                  </Alert>
                )}
              </Box>
            )}

            {/* 优化任务标签页 */}
            {activeTab === 2 && (
              <Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    锁优化任务
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => {/* 打开创建任务对话框 */}}
                  >
                    创建任务
                  </Button>
                </Box>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>任务名称</TableCell>
                        <TableCell>任务类型</TableCell>
                        <TableCell>状态</TableCell>
                        <TableCell>优先级</TableCell>
                        <TableCell>创建时间</TableCell>
                        <TableCell>操作</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell colSpan={6}>
                          <Alert severity="info">
                            暂无优化任务
                          </Alert>
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}

            {/* 分析报告标签页 */}
            {activeTab === 3 && (
              <Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    锁分析报告
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<DownloadIcon />}
                    onClick={() => setReportDialogOpen(true)}
                  >
                    生成报告
                  </Button>
                </Box>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>报告类型</TableCell>
                        <TableCell>分析周期</TableCell>
                        <TableCell>健康评分</TableCell>
                        <TableCell>竞争严重程度</TableCell>
                        <TableCell>创建时间</TableCell>
                        <TableCell>操作</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {reports.length > 0 ? (
                        reports.map((report, index) => (
                          <TableRow key={index}>
                            <TableCell>{report.report_type}</TableCell>
                            <TableCell>
                              {new Date(report.analysis_period_start).toLocaleDateString()} - 
                              {new Date(report.analysis_period_end).toLocaleDateString()}
                            </TableCell>
                            <TableCell>{report.overall_health_score?.toFixed(1)}</TableCell>
                            <TableCell>
                              <Chip
                                label={report.contention_severity}
                                color={report.contention_severity === 'low' ? 'success' : 'warning'}
                                size="small"
                              />
                            </TableCell>
                            <TableCell>{new Date(report.created_at).toLocaleString()}</TableCell>
                            <TableCell>
                              <Tooltip title="查看详情">
                                <IconButton size="small">
                                  <ViewIcon />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="下载报告">
                                <IconButton size="small">
                                  <DownloadIcon />
                                </IconButton>
                              </Tooltip>
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={6}>
                            <Alert severity="info">
                              暂无分析报告
                            </Alert>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* 分析对话框 */}
        <Dialog open={analysisDialogOpen} onClose={() => setAnalysisDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>执行锁分析</DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2 }}>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>分析类型</InputLabel>
                <Select
                  value={analysisType}
                  onChange={(e) => setAnalysisType(e.target.value)}
                  label="分析类型"
                >
                  <MenuItem value="realtime">实时分析</MenuItem>
                  <MenuItem value="historical">历史分析</MenuItem>
                  <MenuItem value="comprehensive">综合分析</MenuItem>
                </Select>
              </FormControl>
              <TextField
                fullWidth
                label="时间范围(小时)"
                type="number"
                value={timeRange}
                onChange={(e) => setTimeRange(parseInt(e.target.value))}
                sx={{ mb: 2 }}
                inputProps={{ min: 1, max: 168 }}
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setAnalysisDialogOpen(false)}>取消</Button>
            <Button variant="contained" onClick={handleAnalysis} disabled={loading}>
              {loading ? '分析中...' : '开始分析'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* 监控设置对话框 */}
        <Dialog open={monitoringDialogOpen} onClose={() => setMonitoringDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>锁监控设置</DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2 }}>
              <TextField
                fullWidth
                label="收集间隔(秒)"
                type="number"
                value={collectionInterval}
                onChange={(e) => setCollectionInterval(parseInt(e.target.value))}
                sx={{ mb: 2 }}
                inputProps={{ min: 10, max: 3600 }}
                helperText="建议设置60-300秒之间的值"
              />
              <Alert severity="info" sx={{ mb: 2 }}>
                监控将自动收集锁事件数据，用于后续分析
              </Alert>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setMonitoringDialogOpen(false)}>取消</Button>
            <Button variant="contained" onClick={handleStartMonitoring}>
              启动监控
            </Button>
          </DialogActions>
        </Dialog>

        {/* 报告生成对话框 */}
        <Dialog open={reportDialogOpen} onClose={() => setReportDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>生成锁分析报告</DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2 }}>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>报告类型</InputLabel>
                <Select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  label="报告类型"
                >
                  <MenuItem value="daily">日报</MenuItem>
                  <MenuItem value="weekly">周报</MenuItem>
                  <MenuItem value="monthly">月报</MenuItem>
                  <MenuItem value="custom">自定义</MenuItem>
                </Select>
              </FormControl>
              <TextField
                fullWidth
                label="分析天数"
                type="number"
                value={reportDays}
                onChange={(e) => setReportDays(parseInt(e.target.value))}
                sx={{ mb: 2 }}
                inputProps={{ min: 1, max: 30 }}
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setReportDialogOpen(false)}>取消</Button>
            <Button variant="contained" onClick={handleGenerateReport} disabled={loading}>
              {loading ? '生成中...' : '生成报告'}
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Container>
  );
};

export default LockAnalysisPage;
