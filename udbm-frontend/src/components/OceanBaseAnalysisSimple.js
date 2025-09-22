import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

const OceanBaseAnalysisSimple = ({ databaseId }) => {
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
      const response = await api.get(`/performance-tuning/oceanbase/sql-analysis/${databaseId}`);
      setSqlAnalysis(response.data);
    } catch (err) {
      console.error('Failed to load SQL analysis:', err);
    }
  };

  const loadSqlTrends = async () => {
    try {
      const response = await api.get(`/performance-tuning/oceanbase/sql-trends/${databaseId}`);
      setSqlTrends(response.data);
    } catch (err) {
      console.error('Failed to load SQL trends:', err);
    }
  };

  const loadPartitionAnalysis = async () => {
    try {
      const response = await api.get(`/performance-tuning/oceanbase/partition-analysis/${databaseId}`);
      setPartitionAnalysis(response.data);
    } catch (err) {
      console.error('Failed to load partition analysis:', err);
    }
  };

  const loadHotspotAnalysis = async () => {
    try {
      const response = await api.get(`/performance-tuning/oceanbase/partition-hotspots/${databaseId}`);
      setHotspotAnalysis(response.data);
    } catch (err) {
      console.error('Failed to load hotspot analysis:', err);
    }
  };

  const analyzeExecutionPlan = async () => {
    if (!sqlText.trim()) return;
    
    try {
      const response = await api.post('/performance-tuning/oceanbase/execution-plan', {
        sql_text: sqlText
      });
      setExecutionPlan(response.data);
    } catch (err) {
      console.error('Failed to analyze execution plan:', err);
    }
  };

  const analyzePartitionPruning = async () => {
    try {
      const response = await api.post('/performance-tuning/oceanbase/partition-pruning', {
        database_id: databaseId,
        sql_queries: testQueries
      });
      setPruningAnalysis(response.data);
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

      const response = await api.post(`/performance-tuning/oceanbase/generate-${scriptType}-optimization-script`, {
        analysis_results: analysisData
      });
      setGeneratedScript(response.data.script);
    } catch (err) {
      console.error('Failed to generate script:', err);
    }
  };

  const renderSqlAnalysis = () => {
    if (!sqlAnalysis) return <div>加载中...</div>;

    return (
      <div className="space-y-6">
        {/* 慢查询摘要 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">慢查询分析摘要</h3>
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
        </div>

        {/* 优化建议 */}
        {sqlAnalysis.optimization_suggestions && sqlAnalysis.optimization_suggestions.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">优化建议</h3>
            <div className="space-y-4">
              {sqlAnalysis.optimization_suggestions.map((suggestion, index) => (
                <div key={index} className={`p-4 rounded-lg border ${
                  suggestion.priority === 'high' ? 'border-red-200 bg-red-50' : 'border-yellow-200 bg-yellow-50'
                }`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">{suggestion.title}</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      suggestion.priority === 'high' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {suggestion.priority}
                    </span>
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
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 慢查询列表 */}
        {sqlAnalysis.top_slow_queries && sqlAnalysis.top_slow_queries.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Top 慢查询</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SQL ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">执行时间</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">CPU时间</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">物理读</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">优化潜力</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {sqlAnalysis.top_slow_queries.slice(0, 10).map((query, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">{query.sql_id}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">{query.elapsed_time.toFixed(3)}s</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">{query.cpu_time.toFixed(3)}s</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">{query.physical_reads.toLocaleString()}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 py-1 rounded text-xs ${
                          query.optimization_potential === 'high' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {query.optimization_potential}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderExecutionPlan = () => {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">执行计划分析</h3>
          <div className="space-y-4">
            <textarea
              placeholder="输入SQL语句进行分析..."
              value={sqlText}
              onChange={(e) => setSqlText(e.target.value)}
              className="w-full h-24 p-3 border border-gray-300 rounded-md resize-none"
            />
            <button
              onClick={analyzeExecutionPlan}
              disabled={!sqlText.trim()}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-300"
            >
              分析执行计划
            </button>
          </div>
        </div>

        {executionPlan && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">分析结果</h3>
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
                    <div key={index} className="p-3 bg-blue-50 border border-blue-200 rounded">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{suggestion.description}</span>
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                          {suggestion.expected_improvement}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderPartitionAnalysis = () => {
    if (!partitionAnalysis) return <div>加载中...</div>;

    return (
      <div className="space-y-6">
        {/* 分区摘要 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">分区表分析摘要</h3>
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
        </div>

        {/* 分区表详情 */}
        {partitionAnalysis.table_analysis && partitionAnalysis.table_analysis.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">分区表详情</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">表名</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">分区类型</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">分区数</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">热点分区</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">优化评分</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {partitionAnalysis.table_analysis.map((table, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">{table.table_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">{table.partition_type}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">{table.total_partitions}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 py-1 rounded text-xs ${
                          table.hot_partitions > 0 ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {table.hot_partitions}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="flex items-center space-x-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-500 h-2 rounded-full" 
                              style={{ width: `${table.optimization_score}%` }}
                            ></div>
                          </div>
                          <span className="text-sm">{table.optimization_score.toFixed(1)}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 py-1 rounded text-xs ${
                          table.optimization_score > 80 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {table.optimization_score > 80 ? '良好' : '需优化'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderHotspotAnalysis = () => {
    if (!hotspotAnalysis) return <div>加载中...</div>;

    return (
      <div className="space-y-6">
        {/* 热点摘要 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">分区热点分析</h3>
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
        </div>

        {/* 热点分区列表 */}
        {hotspotAnalysis.hot_partitions && hotspotAnalysis.hot_partitions.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">热点分区详情</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">表名</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">分区名</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">访问频率</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">数据大小</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">热点原因</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {hotspotAnalysis.hot_partitions.slice(0, 10).map((partition, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">{partition.table_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">{partition.partition_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">{partition.access_frequency.toLocaleString()}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">{partition.data_size_mb.toFixed(1)} MB</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs">
                          {partition.hotspot_reason}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderScriptGenerator = () => {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">优化脚本生成器</h3>
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <select
                value={scriptType}
                onChange={(e) => setScriptType(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="sql">SQL优化脚本</option>
                <option value="partition">分区优化脚本</option>
              </select>
              <button
                onClick={generateOptimizationScript}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
              >
                生成脚本
              </button>
            </div>

            {generatedScript && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold">生成的优化脚本:</h4>
                  <button
                    onClick={() => navigator.clipboard.writeText(generatedScript)}
                    className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600"
                  >
                    复制脚本
                  </button>
                </div>
                <textarea
                  value={generatedScript}
                  readOnly
                  className="w-full h-64 p-3 border border-gray-300 rounded-md font-mono text-sm resize-none"
                />
              </div>
            )}
          </div>
        </div>
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
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="text-red-800">
          加载数据时发生错误: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'sql-analysis', name: 'SQL分析' },
            { id: 'execution-plan', name: '执行计划' },
            { id: 'partition-analysis', name: '分区分析' },
            { id: 'hotspot-analysis', name: '热点分析' },
            { id: 'script-generator', name: '脚本生成' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'sql-analysis' && renderSqlAnalysis()}
      {activeTab === 'execution-plan' && renderExecutionPlan()}
      {activeTab === 'partition-analysis' && renderPartitionAnalysis()}
      {activeTab === 'hotspot-analysis' && renderHotspotAnalysis()}
      {activeTab === 'script-generator' && renderScriptGenerator()}
    </div>
  );
};

export default OceanBaseAnalysisSimple;

