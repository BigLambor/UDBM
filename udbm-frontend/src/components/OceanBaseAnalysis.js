import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Button,
  Badge,
  Progress,
  Alert,
  AlertDescription,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Textarea,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui';
import api from '../services/api';

const OceanBaseAnalysis = ({ databaseId }) => {
  const [activeTab, setActiveTab] = useState('sql-analysis');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // SQL分析状态
  const [sqlAnalysis, setSqlAnalysis] = useState(null);
  const [sqlTrends, setSqlTrends] = useState(null);
  const [executionPlan, setExecutionPlan] = useState(null);
  const [sqlText, setSqlText] = useState('');
  
  // 分区分析状态
  const [partitionAnalysis, setPartitionAnalysis] = useState(null);
  const [hotspotAnalysis, setHotspotAnalysis] = useState(null);
  const [pruningAnalysis, setPruningAnalysis] = useState(null);
  const [testQueries, setTestQueries] = useState([
    "SELECT * FROM orders WHERE order_date > '2025-01-01'",
    "SELECT * FROM users WHERE user_id = 12345",
    "SELECT * FROM products WHERE category = 'electronics'"
  ]);
  
  // 脚本生成状态
  const [generatedScript, setGeneratedScript] = useState('');
  const [scriptType, setScriptType] = useState('sql');

  useEffect(() => {
    if (databaseId) {
      loadInitialData();
    }
  }, [databaseId]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadSqlAnalysis(),
        loadPartitionAnalysis(),
        loadHotspotAnalysis()
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadSqlAnalysis = async () => {
    try {
      const response = await api.get(`/performance/oceanbase/sql-analysis/${databaseId}`);
      setSqlAnalysis(response);
    } catch (err) {
      console.error('Failed to load SQL analysis:', err);
    }
  };

  const loadSqlTrends = async () => {
    try {
      const response = await api.get(`/performance/oceanbase/sql-trends/${databaseId}`);
      setSqlTrends(response);
    } catch (err) {
      console.error('Failed to load SQL trends:', err);
    }
  };

  const loadPartitionAnalysis = async () => {
    try {
      const response = await api.get(`/performance/oceanbase/partition-analysis/${databaseId}`);
      setPartitionAnalysis(response);
    } catch (err) {
      console.error('Failed to load partition analysis:', err);
    }
  };

  const loadHotspotAnalysis = async () => {
    try {
      const response = await api.get(`/performance/oceanbase/partition-hotspots/${databaseId}`);
      setHotspotAnalysis(response);
    } catch (err) {
      console.error('Failed to load hotspot analysis:', err);
    }
  };

  const analyzeExecutionPlan = async () => {
    if (!sqlText.trim()) return;
    
    try {
      const response = await api.post('/performance/oceanbase/execution-plan', {
        sql_text: sqlText
      });
      setExecutionPlan(response);
    } catch (err) {
      console.error('Failed to analyze execution plan:', err);
    }
  };

  const analyzePartitionPruning = async () => {
    try {
      const response = await api.post('/performance/oceanbase/partition-pruning', {
        database_id: databaseId,
        sql_queries: testQueries
      });
      setPruningAnalysis(response);
    } catch (err) {
      console.error('Failed to analyze partition pruning:', err);
    }
  };

  const generateOptimizationScript = async () => {
    try {
      let analysisData;
      if (scriptType === 'sql') {
        analysisData = sqlAnalysis;
      } else {
        analysisData = partitionAnalysis;
      }

      const response = await api.post(`/performance/oceanbase/generate-${scriptType}-optimization-script`, {
        analysis_results: analysisData
      });
      setGeneratedScript(response.script);
    } catch (err) {
      console.error('Failed to generate script:', err);
    }
  };

  const renderSqlAnalysis = () => {
    if (!sqlAnalysis) return <div>加载中...</div>;

    return (
      <div className="space-y-6">
        {/* 慢查询摘要 */}
        <Card>
          <CardHeader>
            <CardTitle>慢查询分析摘要</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {sqlAnalysis.summary?.total_slow_queries || 0}
                </div>
                <div className="text-sm text-gray-600">慢查询总数</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {sqlAnalysis.summary?.avg_elapsed_time?.toFixed(3) || 0}秒
                </div>
                <div className="text-sm text-gray-600">平均执行时间</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {sqlAnalysis.summary?.slow_query_percentage?.toFixed(1) || 0}%
                </div>
                <div className="text-sm text-gray-600">慢查询比例</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {sqlAnalysis.optimization_suggestions?.length || 0}
                </div>
                <div className="text-sm text-gray-600">优化建议</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 优化建议 */}
        {sqlAnalysis.optimization_suggestions && sqlAnalysis.optimization_suggestions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>优化建议</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {sqlAnalysis.optimization_suggestions.map((suggestion, index) => (
                  <Alert key={index} className={suggestion.priority === 'high' ? 'border-red-200 bg-red-50' : 'border-yellow-200 bg-yellow-50'}>
                    <AlertDescription>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold">{suggestion.title}</span>
                        <Badge variant={suggestion.priority === 'high' ? 'destructive' : 'secondary'}>
                          {suggestion.priority}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{suggestion.description}</p>
                      <ul className="text-sm space-y-1">
                        {suggestion.actions?.map((action, actionIndex) => (
                          <li key={actionIndex} className="flex items-center">
                            <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                            {action}
                          </li>
                        ))}
                      </ul>
                    </AlertDescription>
                  </Alert>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* 慢查询列表 */}
        {sqlAnalysis.top_slow_queries && sqlAnalysis.top_slow_queries.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Top 慢查询</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>SQL ID</TableHead>
                    <TableHead>执行时间</TableHead>
                    <TableHead>CPU时间</TableHead>
                    <TableHead>物理读</TableHead>
                    <TableHead>优化潜力</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sqlAnalysis.top_slow_queries.slice(0, 10).map((query, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-mono text-sm">{query.sql_id}</TableCell>
                      <TableCell>{query.elapsed_time.toFixed(3)}s</TableCell>
                      <TableCell>{query.cpu_time.toFixed(3)}s</TableCell>
                      <TableCell>{query.physical_reads.toLocaleString()}</TableCell>
                      <TableCell>
                        <Badge variant={query.optimization_potential === 'high' ? 'destructive' : 'secondary'}>
                          {query.optimization_potential}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderExecutionPlan = () => {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>执行计划分析</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Textarea
                placeholder="输入SQL语句进行分析..."
                value={sqlText}
                onChange={(e) => setSqlText(e.target.value)}
                className="min-h-[100px]"
              />
              <Button onClick={analyzeExecutionPlan} disabled={!sqlText.trim()}>
                分析执行计划
              </Button>
            </div>
          </CardContent>
        </Card>

        {executionPlan && (
          <Card>
            <CardHeader>
              <CardTitle>分析结果</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="text-center">
                  <div className="text-lg font-semibold">{executionPlan.estimated_cost}</div>
                  <div className="text-sm text-gray-600">预估成本</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold">{executionPlan.estimated_rows?.toLocaleString()}</div>
                  <div className="text-sm text-gray-600">预估行数</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold">{executionPlan.execution_plan?.length || 0}</div>
                  <div className="text-sm text-gray-600">执行步骤</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold">{executionPlan.optimization_suggestions?.length || 0}</div>
                  <div className="text-sm text-gray-600">优化建议</div>
                </div>
              </div>

              {executionPlan.execution_plan && executionPlan.execution_plan.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-semibold">执行计划步骤:</h4>
                  <div className="space-y-1">
                    {executionPlan.execution_plan.map((step, index) => (
                      <div key={index} className="flex items-center space-x-4 p-2 bg-gray-50 rounded">
                        <span className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm">
                          {step.id}
                        </span>
                        <div className="flex-1">
                          <div className="font-medium">{step.operation}</div>
                          <div className="text-sm text-gray-600">{step.object_name}</div>
                        </div>
                        <div className="text-sm text-gray-500">
                          成本: {step.cost} | 行数: {step.rows}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {executionPlan.optimization_suggestions && executionPlan.optimization_suggestions.length > 0 && (
                <div className="mt-4">
                  <h4 className="font-semibold mb-2">优化建议:</h4>
                  <div className="space-y-2">
                    {executionPlan.optimization_suggestions.map((suggestion, index) => (
                      <Alert key={index}>
                        <AlertDescription>
                          <div className="flex items-center justify-between">
                            <span className="font-medium">{suggestion.description}</span>
                            <Badge variant="secondary">{suggestion.expected_improvement}</Badge>
                          </div>
                        </AlertDescription>
                      </Alert>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderPartitionAnalysis = () => {
    if (!partitionAnalysis) return <div>加载中...</div>;

    return (
      <div className="space-y-6">
        {/* 分区摘要 */}
        <Card>
          <CardHeader>
            <CardTitle>分区表分析摘要</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {partitionAnalysis.summary?.total_partition_tables || 0}
                </div>
                <div className="text-sm text-gray-600">分区表总数</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {partitionAnalysis.summary?.total_partitions || 0}
                </div>
                <div className="text-sm text-gray-600">总分区数</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {partitionAnalysis.summary?.total_rows?.toLocaleString() || 0}
                </div>
                <div className="text-sm text-gray-600">总行数</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {partitionAnalysis.summary?.total_size_mb?.toFixed(1) || 0} MB
                </div>
                <div className="text-sm text-gray-600">总大小</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 分区表详情 */}
        {partitionAnalysis.table_analysis && partitionAnalysis.table_analysis.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>分区表详情</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>表名</TableHead>
                    <TableHead>分区类型</TableHead>
                    <TableHead>分区数</TableHead>
                    <TableHead>热点分区</TableHead>
                    <TableHead>优化评分</TableHead>
                    <TableHead>状态</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {partitionAnalysis.table_analysis.map((table, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{table.table_name}</TableCell>
                      <TableCell>{table.partition_type}</TableCell>
                      <TableCell>{table.total_partitions}</TableCell>
                      <TableCell>
                        <Badge variant={table.hot_partitions > 0 ? 'destructive' : 'secondary'}>
                          {table.hot_partitions}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Progress value={table.optimization_score} className="w-16" />
                          <span className="text-sm">{table.optimization_score.toFixed(1)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={table.optimization_score > 80 ? 'default' : 'destructive'}>
                          {table.optimization_score > 80 ? '良好' : '需优化'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderHotspotAnalysis = () => {
    if (!hotspotAnalysis) return <div>加载中...</div>;

    return (
      <div className="space-y-6">
        {/* 热点摘要 */}
        <Card>
          <CardHeader>
            <CardTitle>分区热点分析</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {hotspotAnalysis.hot_partitions?.length || 0}
                </div>
                <div className="text-sm text-gray-600">热点分区</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {hotspotAnalysis.cold_partitions?.length || 0}
                </div>
                <div className="text-sm text-gray-600">冷分区</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {hotspotAnalysis.hot_partition_ratio?.toFixed(1) || 0}%
                </div>
                <div className="text-sm text-gray-600">热点比例</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 热点分区列表 */}
        {hotspotAnalysis.hot_partitions && hotspotAnalysis.hot_partitions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>热点分区详情</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>表名</TableHead>
                    <TableHead>分区名</TableHead>
                    <TableHead>访问频率</TableHead>
                    <TableHead>数据大小</TableHead>
                    <TableHead>热点原因</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {hotspotAnalysis.hot_partitions.slice(0, 10).map((partition, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{partition.table_name}</TableCell>
                      <TableCell className="font-mono text-sm">{partition.partition_name}</TableCell>
                      <TableCell>{partition.access_frequency.toLocaleString()}</TableCell>
                      <TableCell>{partition.data_size_mb.toFixed(1)} MB</TableCell>
                      <TableCell>
                        <Badge variant="destructive">{partition.hotspot_reason}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderScriptGenerator = () => {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>优化脚本生成器</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                <Select value={scriptType} onValueChange={setScriptType}>
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sql">SQL优化脚本</SelectItem>
                    <SelectItem value="partition">分区优化脚本</SelectItem>
                  </SelectContent>
                </Select>
                <Button onClick={generateOptimizationScript}>
                  生成脚本
                </Button>
              </div>

              {generatedScript && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">生成的优化脚本:</h4>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigator.clipboard.writeText(generatedScript)}
                    >
                      复制脚本
                    </Button>
                  </div>
                  <Textarea
                    value={generatedScript}
                    readOnly
                    className="min-h-[300px] font-mono text-sm"
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <div>加载OceanBase分析数据...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          加载数据时发生错误: {error}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="sql-analysis">SQL分析</TabsTrigger>
          <TabsTrigger value="execution-plan">执行计划</TabsTrigger>
          <TabsTrigger value="partition-analysis">分区分析</TabsTrigger>
          <TabsTrigger value="hotspot-analysis">热点分析</TabsTrigger>
          <TabsTrigger value="script-generator">脚本生成</TabsTrigger>
        </TabsList>

        <TabsContent value="sql-analysis">
          {renderSqlAnalysis()}
        </TabsContent>

        <TabsContent value="execution-plan">
          {renderExecutionPlan()}
        </TabsContent>

        <TabsContent value="partition-analysis">
          {renderPartitionAnalysis()}
        </TabsContent>

        <TabsContent value="hotspot-analysis">
          {renderHotspotAnalysis()}
        </TabsContent>

        <TabsContent value="script-generator">
          {renderScriptGenerator()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default OceanBaseAnalysis;

