import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1', '#d084d0'];

export const NAICSBreakdownChart = ({ data }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No NAICS data available</p>
      </div>
    );
  }

  const chartData = Object.entries(data)
    .slice(0, 8) // Top 8 NAICS codes
    .map(([naics, count]) => ({
      naics: naics.substring(0, 6), // Truncate for display
      count,
      fullNaics: naics
    }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">NAICS Code Distribution</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="naics" angle={-45} textAnchor="end" height={60} />
          <YAxis />
          <Tooltip 
            formatter={(value, name) => [value, 'Companies']}
            labelFormatter={(label) => `NAICS: ${label}`}
          />
          <Bar dataKey="count" fill="#8884d8" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export const StateBreakdownChart = ({ data }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No state data available</p>
      </div>
    );
  }

  const chartData = Object.entries(data)
    .slice(0, 10) // Top 10 states
    .map(([state, count]) => ({
      state,
      count
    }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Geographic Distribution</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} layout="horizontal">
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis dataKey="state" type="category" width={80} />
          <Tooltip />
          <Bar dataKey="count" fill="#82ca9d" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export const BusinessGradeChart = ({ data }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No grade data available</p>
      </div>
    );
  }

  const chartData = Object.entries(data).map(([grade, count]) => ({
    grade,
    count
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Business Health Grades</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ grade, count, percent }) => `${grade}: ${count} (${(percent * 100).toFixed(0)}%)`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="count"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export const ComplianceScoreChart = ({ cmmcScore, dfarsScore, fedrampAuthorized }) => {
  const data = [
    { name: 'CMMC 2.0', score: cmmcScore, target: 100 },
    { name: 'DFARS', score: dfarsScore, target: 100 },
    { name: 'FedRAMP', score: fedrampAuthorized ? 100 : 0, target: 100 }
  ];

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Compliance Scores</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis domain={[0, 100]} />
          <Tooltip formatter={(value) => [`${value}%`, 'Score']} />
          <Bar dataKey="score" fill="#4f46e5" />
          <Bar dataKey="target" fill="#e5e7eb" opacity={0.3} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export const ContractPipelineChart = ({ data }) => {
  const pipelineData = [
    { stage: 'Active', count: data?.active || 0, color: '#10b981' },
    { stage: 'Pending', count: data?.pending || 0, color: '#f59e0b' },
    { stage: 'Won', count: Math.floor((data?.active || 0) * 1.2), color: '#8b5cf6' }
  ];

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Contract Pipeline</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={pipelineData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="stage" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill="#8884d8" />
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-4 text-center">
        <p className="text-sm text-gray-600">
          Total Pipeline Value: <span className="font-semibold text-green-600">
            ${((data?.totalValue || 0) / 1000000).toFixed(1)}M
          </span>
        </p>
        <p className="text-sm text-gray-600">
          Win Rate: <span className="font-semibold text-blue-600">{data?.winRate || 0}%</span>
        </p>
      </div>
    </div>
  );
};