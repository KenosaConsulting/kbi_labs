import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, Users, DollarSign, Brain, Building2, FileText, BarChart3 } from 'lucide-react';
import api from '../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalCompanies: 0,
    totalContracts: 110,
    aiInsights: 156,
    portfolioValue: 0
  });
  const [recentCompanies, setRecentCompanies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch companies
      const companiesData = await api.getCompanies(1, 5);
      console.log('Companies data:', companiesData);
      
      setRecentCompanies(companiesData.companies || []);
      
      // Fetch KPIs
      const kpisData = await api.getKPIs();
      console.log('KPIs data:', kpisData);
      
      // Update stats with proper data
      const totalCompanies = companiesData.total || companiesData.totalCount || 0;
      const totalRevenue = kpisData.totalRevenue || 0;
      const activeDeals = kpisData.activeDeals || 110;
      
      setStats({
        totalCompanies: totalCompanies,
        totalContracts: activeDeals,
        aiInsights: 156,
        portfolioValue: totalRevenue
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}K`;
    }
    return `$${value}`;
  };

  const MetricCard = ({ title, value, change, icon: Icon, color }) => (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900 mt-2">{value}</p>
          {change && (
            <p className={`text-sm mt-2 ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {change > 0 ? '+' : ''}{change}%
            </p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-gray-600">Welcome to KBI Labs Intelligence Platform</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total Companies"
          value={stats.totalCompanies}
          icon={Building2}
          color="bg-blue-500"
        />
        <MetricCard
          title="Total Contracts"
          value={stats.totalContracts}
          change={12.5}
          icon={FileText}
          color="bg-purple-500"
        />
        <MetricCard
          title="AI Insights"
          value={stats.aiInsights}
          change={8.2}
          icon={Brain}
          color="bg-indigo-500"
        />
        <MetricCard
          title="Portfolio Value"
          value={formatValue(stats.portfolioValue)}
          change={15.3}
          icon={DollarSign}
          color="bg-green-500"
        />
      </div>

      {/* Recent Companies */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Companies</h2>
          
          {recentCompanies.length > 0 ? (
            <div className="space-y-4">
              {recentCompanies.map((company) => (
                <div key={company.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                      <Building2 className="h-5 w-5 text-indigo-600" />
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">{company.name}</h4>
                      <p className="text-sm text-gray-500">{company.industry} • {company.location}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-gray-900">{company.revenue}</p>
                    <p className="text-sm text-gray-500">KBI Score: {company.kbi_score}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Building2 className="h-8 w-8 text-gray-400" />
              </div>
              <p className="text-gray-500 mb-4">No companies found</p>
              <button className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
                Add Your First Company
              </button>
            </div>
          )}
        </div>
      </div>

      {/* AI Insights */}
      <div className="mt-8 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg shadow-lg text-white p-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">AI-Powered Insights</h2>
            <p className="text-purple-100">Get intelligent recommendations and predictions powered by advanced AI</p>
            <button className="mt-4 px-6 py-2 bg-white text-purple-600 rounded-lg hover:bg-gray-100 transition-colors font-medium">
              Explore AI Features
            </button>
          </div>
          <Brain className="h-24 w-24 text-purple-200 opacity-50" />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
