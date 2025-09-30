/**
 * 锁分析API服务
 * 
 * 封装所有锁分析相关的API调用
 */

import axios from 'axios';

const BASE_URL = '/api/v1/performance-tuning/lock-analysis';

/**
 * 锁分析API类
 */
export class LockAnalysisAPI {
  /**
   * 获取仪表板数据 V2（优化版本）
   */
  static async getDashboardV2(databaseId, options = {}) {
    const {
      timeRange = '1h',
      forceRefresh = false,
      includeTrends = true,
      includeRecommendations = true
    } = options;
    
    try {
      const response = await axios.get(
        `${BASE_URL}/dashboard/v2/${databaseId}`,
        {
          params: {
            time_range: timeRange,
            force_refresh: forceRefresh,
            include_trends: includeTrends,
            include_recommendations: includeRecommendations
          }
        }
      );
      
      return response.data;
    } catch (error) {
      console.error('Failed to fetch dashboard V2:', error);
      throw error;
    }
  }
  
  /**
   * 获取仪表板数据 V1（兼容旧版本）
   */
  static async getDashboardV1(databaseId, forceRefresh = false) {
    try {
      const response = await axios.get(
        `${BASE_URL}/dashboard/${databaseId}`,
        {
          params: {
            force_refresh: forceRefresh,
            use_v2: true
          }
        }
      );
      
      return response.data;
    } catch (error) {
      console.error('Failed to fetch dashboard V1:', error);
      throw error;
    }
  }
  
  /**
   * 获取仪表板数据（自动降级）
   */
  static async getDashboard(databaseId, options = {}) {
    try {
      // 尝试V2 API
      return await this.getDashboardV2(databaseId, options);
    } catch (error) {
      console.warn('V2 API failed, fallback to V1:', error.message);
      // 降级到V1
      return await this.getDashboardV1(databaseId, options.forceRefresh);
    }
  }
  
  /**
   * 执行锁分析
   */
  static async analyzeLocks(databaseId, analysisRequest) {
    try {
      const response = await axios.post(
        `${BASE_URL}/analyze/${databaseId}`,
        analysisRequest
      );
      
      return response.data;
    } catch (error) {
      console.error('Failed to analyze locks:', error);
      throw error;
    }
  }
  
  /**
   * 获取等待链
   */
  static async getWaitChains(databaseId, severityFilter = null) {
    try {
      const response = await axios.get(
        `${BASE_URL}/wait-chains/${databaseId}`,
        {
          params: {
            severity_filter: severityFilter
          }
        }
      );
      
      return response.data;
    } catch (error) {
      console.error('Failed to get wait chains:', error);
      throw error;
    }
  }
  
  /**
   * 获取竞争分析
   */
  static async getContentions(databaseId, priorityFilter = null, limit = 50) {
    try {
      const response = await axios.get(
        `${BASE_URL}/contentions/${databaseId}`,
        {
          params: {
            priority_filter: priorityFilter,
            limit: limit
          }
        }
      );
      
      return response.data;
    } catch (error) {
      console.error('Failed to get contentions:', error);
      throw error;
    }
  }
  
  /**
   * 启动锁监控
   */
  static async startMonitoring(databaseId, collectionInterval = 60) {
    try {
      const response = await axios.post(
        `${BASE_URL}/monitoring/start/${databaseId}`,
        null,
        {
          params: {
            collection_interval: collectionInterval
          }
        }
      );
      
      return response.data;
    } catch (error) {
      console.error('Failed to start monitoring:', error);
      throw error;
    }
  }
  
  /**
   * 停止锁监控
   */
  static async stopMonitoring(databaseId) {
    try {
      const response = await axios.post(
        `${BASE_URL}/monitoring/stop/${databaseId}`
      );
      
      return response.data;
    } catch (error) {
      console.error('Failed to stop monitoring:', error);
      throw error;
    }
  }
  
  /**
   * 获取监控状态
   */
  static async getMonitoringStatus(databaseId) {
    try {
      const response = await axios.get(
        `${BASE_URL}/monitoring/status/${databaseId}`
      );
      
      return response.data;
    } catch (error) {
      console.error('Failed to get monitoring status:', error);
      throw error;
    }
  }
  
  /**
   * 生成分析报告
   */
  static async generateReport(databaseId, reportType = 'custom', days = 7) {
    try {
      const response = await axios.post(
        `${BASE_URL}/generate-report/${databaseId}`,
        null,
        {
          params: {
            report_type: reportType,
            days: days
          }
        }
      );
      
      return response.data;
    } catch (error) {
      console.error('Failed to generate report:', error);
      throw error;
    }
  }
  
  /**
   * 获取分析报告列表
   */
  static async getReports(databaseId, reportType = null) {
    try {
      const response = await axios.get(
        `${BASE_URL}/reports/${databaseId}`,
        {
          params: {
            report_type: reportType
          }
        }
      );
      
      return response.data;
    } catch (error) {
      console.error('Failed to get reports:', error);
      throw error;
    }
  }
  
  /**
   * 处理告警操作
   */
  static handleAlertAction(action, alert) {
    switch (action.type) {
      case 'navigate':
        // 返回导航信息，由调用者处理
        return { type: 'navigate', ...action.payload };
      
      case 'api_call':
        // 执行API调用
        return axios.post(action.payload.url, action.payload.data);
      
      case 'external_link':
        // 打开外部链接
        window.open(action.payload.url, '_blank');
        return Promise.resolve();
      
      default:
        console.warn('Unknown action type:', action.type);
        return Promise.reject(new Error(`Unknown action type: ${action.type}`));
    }
  }
}

export default LockAnalysisAPI;
