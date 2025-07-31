import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, AlertTriangle, Lightbulb, Target, Globe, 
  DollarSign, Users, BarChart3, Activity, ChevronRight,
  Calendar, Award, Eye, BrainCircuit, Building2
} from 'lucide-react';
import { 
  AreaChart, Area, BarChart, Bar, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import api from '../services/api';

const MarketIntelligence = () => {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchMarketIntelligence();
  }, []);

  const fetchMarketIntelligence = async () => {
    try {
      setLoading(true);
      const data = await api.getMarketIntelligence();
      setMarketData(data);
    } catch (error) {
      console.error('Error fetching market intelligence:', error);
      // Use mock data if API fails
      setMarketData(getMockData());
    } finally {
      setLoading(false);
    }
  };

  const getMockData = () => ({
    market_trends: [
      { industry: "Technology", growth_rate: 23.5, market_size: 15200000, company_count: 3, trend: "up", forecast_growth: 28.2 },
      { industry: "Healthcare", growth_rate: 18.3, market_size: 7100000, company_count: 1, trend: "up", forecast_growth: 22.0 },
      { industry: "Energy", growth_rate: 15.2, market_size: 3800000, company_count: 1, trend: "stable", forecast_growth: 18.2 },
      { industry: "Manufacturing", growth_rate: 8.7, market_size: 4200000, company_count: 1, trend: "stable", forecast_growth: 10.4 },
      { industry: "Construction", growth_rate: 12.1, market_size: 2500000, company_count: 1, trend: "stable", forecast_growth: 14.5 }
    ],
    geographic_insights: {
      top_states: [
        { state: "CA", company_count: 2, total_revenue: 10400000, avg_revenue: 5200000 },
        { state: "VA", company_count: 1, total_revenue: 6800000, avg_revenue: 6800000 },
        { state: "MA", company_count: 1, total_revenue: 7100000, avg_revenue: 7100000 },
        { state: "TX", company_count: 2, total_revenue: 6300000, avg_revenue: 3150000 },
        { state: "MI", company_count: 1, total_revenue: 4200000, avg_revenue: 4200000 }
      ],
      emerging_markets: ["Texas", "Florida", "Colorado"],
      declining_markets: ["Illinois", "Michigan"]
    },
    ai_insights: [
      {
        id: 1,
        type: "opportunity",
        title: "Technology Sector Expansion",
        description: "Federal technology contracts have grown 23% YoY. Companies with AI/ML capabilities are winning 3x more contracts.",
        impact: "high",
        confidence: 92,
        affected_industries: ["Technology", "Healthcare"],
        action: "Consider partnerships with AI-focused vendors"
      },
      {
        id: 2,
        type: "risk",
        title: "Supply Chain Disruptions",
        description: "Manufacturing sector seeing 15% delays in contract fulfillment due to supply chain issues.",
        impact: "medium",
        confidence: 85,
        affected_industries: ["Manufacturing", "Construction"],
        action: "Diversify supplier base and increase inventory buffers"
      },
      {
        id: 3,
        type: "trend",
        title: "Cybersecurity Requirements Increasing",
        description: "82% of new federal contracts now require enhanced cybersecurity certifications.",
        impact: "high",
        confidence: 95,
        affected_industries: ["All"],
        action: "Prioritize CMMC certification for competitive advantage"
      }
    ],
    competitor_updates: [
      {
        company: "TechCorp Solutions",
        event: "Won $2.5M DoD contract for AI development",
        date: "2024-03-10",
        impact: "Strengthens position in defense sector"
      },
      {
        company: "CyberShield Security",
        event: "Acquired SmallSec Inc for $1.2M",
        date: "2024-03-08",
        impact: "Expands cybersecurity capabilities"
      }
    ],
    opportunities: [
      {
        title: "Upcoming VA Hospital Modernization",
        value: "$15M - $20M",
        probability: 75,
        timeline: "Q3 2024",
        requirements: ["Healthcare IT", "CMMC Level 2", "Past Performance"],
        competition: "Medium (5-8 competitors expected)",
        kbi_match_score: 92
      },
      {
        title: "DoE Renewable Energy Research",
        value: "$8M - $12M",
        probability: 60,
        timeline: "Q4 2024",
        requirements: ["Energy sector experience", "Research capabilities", "University partnerships"],
        competition: "High (10+ competitors expected)",
        kbi_match_score: 78
      }
    ],
    market_summary: {
      total_market_size: 32800000,
      avg_growth_rate: 18.5,
      top_growing_sector: "Technology",
      risk_level: "Medium",
      opportunity_score: 82
    }
  });
  const getInsightIcon = (type) => {
    switch (type) {
      case 'opportunity': return <Lightbulb className="h-5 w-5 text-green-500" />;
      case 'risk': return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'trend': return <TrendingUp className="h-5 w-5 text-blue-500" />;
      default: return <Activity className="h-5 w-5 text-gray-500" />;
    }
  };

  const getImpactColor = (impact) => {
    switch (impact) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const data = marketData || getMockData();

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Market Intelligence</h1>
        <p className="text-gray-600">AI-powered insights and market analysis</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center justify-between mb-2">
            <DollarSign className="h-8 w-8 text-gray-400" />
            <span className="text-xs text-green-600 font-medium">+15.3%</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            ${(data.market_summary.total_market_size / 1000000).toFixed(1)}M
          </p>
          <p className="text-sm text-gray-600">Total Market Size</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className="h-8 w-8 text-gray-400" />
            <span className="text-xs text-green-600 font-medium">↑</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{data.market_summary.avg_growth_rate}%</p>
          <p className="text-sm text-gray-600">Avg Growth Rate</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center justify-between mb-2">
            <Target className="h-8 w-8 text-gray-400" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{data.opportunities.length}</p>
          <p className="text-sm text-gray-600">Active Opportunities</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center justify-between mb-2">
            <Activity className="h-8 w-8 text-gray-400" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{data.market_summary.opportunity_score}</p>
          <p className="text-sm text-gray-600">Opportunity Score</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex items-center justify-between mb-2">
            <AlertTriangle className="h-8 w-8 text-gray-400" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{data.market_summary.risk_level}</p>
          <p className="text-sm text-gray-600">Risk Level</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border mb-6">
        <div className="border-b">
          <nav className="flex -mb-px">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-6 py-3 border-b-2 font-medium text-sm ${
                activeTab === 'overview'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Market Overview
            </button>
            <button
              onClick={() => setActiveTab('insights')}
              className={`px-6 py-3 border-b-2 font-medium text-sm ${
                activeTab === 'insights'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              AI Insights
            </button>
            <button
              onClick={() => setActiveTab('opportunities')}
              className={`px-6 py-3 border-b-2 font-medium text-sm ${
                activeTab === 'opportunities'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Opportunities
            </button>
            <button
              onClick={() => setActiveTab('competitors')}
              className={`px-6 py-3 border-b-2 font-medium text-sm ${
                activeTab === 'competitors'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Competitor Activity
            </button>
          </nav>
        </div>

        <div className="p-6">
          {/* Market Overview Tab */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Industry Growth Rates */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Industry Growth Rates</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={data.market_trends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="industry" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="growth_rate" fill="#6366f1" name="Current Growth %" />
                    <Bar dataKey="forecast_growth" fill="#8b5cf6" name="Forecast Growth %" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Market Size by Industry */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Market Size by Industry</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={data.market_trends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="industry" />
                    <YAxis />
                    <Tooltip formatter={(value) => `$${(value/1000000).toFixed(1)}M`} />
                    <Area type="monotone" dataKey="market_size" stroke="#6366f1" fill="#6366f1" fillOpacity={0.6} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* AI Insights Tab */}
          {activeTab === 'insights' && (
            <div className="space-y-4">
              <div className="flex items-center mb-4">
                <BrainCircuit className="h-5 w-5 text-indigo-600 mr-2" />
                <h3 className="text-lg font-semibold text-gray-900">AI-Generated Market Insights</h3>
              </div>
              
              {data.ai_insights.map((insight) => (
                <div key={insight.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-start">
                      {getInsightIcon(insight.type)}
                      <div className="ml-3">
                        <h4 className="font-medium text-gray-900">{insight.title}</h4>
                        <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getImpactColor(insight.impact)}`}>
                        {insight.impact} impact
                      </span>
                      <div className="text-right">
                        <p className="text-xs text-gray-500">Confidence</p>
                        <p className="text-sm font-semibold">{insight.confidence}%</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-3 pt-3 border-t">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500">Affects:</span>
                        {insight.affected_industries.map((ind, idx) => (
                          <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                            {ind}
                          </span>
                        ))}
                      </div>
                    </div>
                    {insight.action && (
                      <div className="mt-2 p-2 bg-indigo-50 rounded text-sm text-indigo-700">
                        <strong>Recommended Action:</strong> {insight.action}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Opportunities Tab */}
          {activeTab === 'opportunities' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Matched Opportunities</h3>
              
              {data.opportunities.map((opp, idx) => (
                <div key={idx} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-gray-900">{opp.title}</h4>
                      <div className="flex items-center gap-4 mt-1">
                        <span className="text-sm text-gray-600">
                          <DollarSign className="h-4 w-4 inline mr-1" />
                          {opp.value}
                        </span>
                        <span className="text-sm text-gray-600">
                          <Calendar className="h-4 w-4 inline mr-1" />
                          {opp.timeline}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-indigo-600">{opp.kbi_match_score}</div>
                      <p className="text-xs text-gray-500">Match Score</p>
                    </div>
                  </div>
                  
                  <div className="mt-3">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-indigo-600 h-2 rounded-full" 
                        style={{width: `${opp.probability}%`}}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-500">{opp.probability}% probability</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Competitor Activity Tab */}
          {activeTab === 'competitors' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Competitor Activity</h3>
              
              {data.competitor_updates.map((update, idx) => (
                <div key={idx} className="flex items-start p-4 border rounded-lg hover:bg-gray-50">
                  <div className="flex-shrink-0 w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                    <Building2 className="h-5 w-5 text-indigo-600" />
                  </div>
                  <div className="ml-4 flex-1">
                    <h4 className="font-medium text-gray-900">{update.company}</h4>
                    <p className="text-sm text-gray-600 mt-1">{update.event}</p>
                    <p className="text-xs text-gray-500 mt-2">Impact: {update.impact}</p>
                    <p className="text-xs text-gray-500">{new Date(update.date).toLocaleDateString()}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MarketIntelligence;
