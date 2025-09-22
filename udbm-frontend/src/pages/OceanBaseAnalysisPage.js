import React, { useState } from 'react';
import OceanBaseAnalysisSimple from '../components/OceanBaseAnalysisSimple';

const OceanBaseAnalysisPage = () => {
  const [databaseId, setDatabaseId] = useState(1);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900">OceanBase 性能分析</h1>
            <p className="mt-2 text-gray-600">
              基于GV$SQL_AUDIT视图的SQL性能分析和分区表优化
            </p>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              数据库ID
            </label>
            <input
              type="number"
              value={databaseId}
              onChange={(e) => setDatabaseId(parseInt(e.target.value) || 1)}
              className="px-3 py-2 border border-gray-300 rounded-md w-32"
              min="1"
            />
          </div>

          <OceanBaseAnalysisSimple databaseId={databaseId} />
        </div>
      </div>
    </div>
  );
};

export default OceanBaseAnalysisPage;
