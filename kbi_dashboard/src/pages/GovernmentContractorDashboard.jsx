import React, { useState, useEffect } from 'react';
import { 
  Shield, AlertTriangle, CheckCircle, Clock, TrendingUp, 
  FileText, Users, DollarSign, Award, Building2, Globe,
  Target, BarChart3, Brain, Calendar, AlertCircle, Search,
  ExternalLink, Star, Filter
} from 'lucide-react';
import api from '../services/api';
// Temporarily commented out charts to test data loading
// import { 
//   NAICSBreakdownChart, 
//   StateBreakdownChart, 
//   BusinessGradeChart, 
//   ComplianceScoreChart,
//   ContractPipelineChart 
// } from '../components/Charts';

const OpportunitiesTab = ({ naics }) => {
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchKeywords, setSearchKeywords] = useState('');
  const [filteredNaics, setFilteredNaics] = useState(naics);

  useEffect(() => {
    fetchOpportunities();
  }, [filteredNaics]);

  const fetchOpportunities = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8001/api/v1/government-contractor/opportunities?naics=${filteredNaics}&keywords=${searchKeywords}&limit=20`);
      const data = await response.json();
      setOpportunities(data.opportunities || []);
    } catch (error) {
      console.error('Error fetching opportunities:', error);
      // Set mock data on error
      setOpportunities([
        {
          id: "SP060025Q0801",
          title: "IT Support Services - Cybersecurity Implementation",
          agency: "Department of Defense",
          naics: "541511",
          setAside: "8(a) Small Business",
          responseDeadline: "2025-03-15",
          matchScore: 92,
          requirements: ["CMMC Level 2 Required", "Security Clearance: Secret"],
          estimatedValue: "$500,000 - $2,000,000",
          competitionLevel: "Low"
        },
        {
          id: "IN12568",
          title: "Cybersecurity Consulting and Risk Assessment",
          agency: "Department of Homeland Security",
          naics: "541512",
          setAside: "Service-Disabled Veteran-Owned Small Business",
          responseDeadline: "2025-04-01",
          matchScore: 88,
          requirements: ["CMMC Level 2 Required", "FedRAMP Experience Preferred"],
          estimatedValue: "$1,000,000 - $5,000,000",
          competitionLevel: "Medium"
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getMatchScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getCompetitionColor = (level) => {
    if (level === 'Low') return 'text-green-600 bg-green-100';
    if (level === 'Medium') return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <input
                type="text"
                placeholder="Search opportunities by keywords..."
                value={searchKeywords}
                onChange={(e) => setSearchKeywords(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
          </div>
          <button
            onClick={fetchOpportunities}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Search
          </button>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-600">NAICS:</span>
            <select
              value={filteredNaics}
              onChange={(e) => setFilteredNaics(e.target.value)}
              className="border border-gray-300 rounded px-3 py-1 text-sm"
            >
              <option value="541511">541511 - Custom Computer Programming</option>
              <option value="541512">541512 - Computer Systems Design</option>
              <option value="541519">541519 - Other Computer Services</option>
              <option value="">All NAICS</option>
            </select>
          </div>
        </div>
      </div>

      {/* Opportunities List */}
      <div className="space-y-4">
        {opportunities.map((opp) => (
          <div key={opp.id} className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">{opp.title}</h3>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${getMatchScoreColor(opp.matchScore)}`}>
                    {opp.matchScore}% Match
                  </div>
                </div>
                <p className="text-gray-600 mb-2">{opp.agency}</p>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>NAICS: {opp.naics}</span>
                  <span>•</span>
                  <span>Due: {opp.responseDeadline}</span>
                  <span>•</span>
                  <span>{opp.estimatedValue}</span>
                </div>
              </div>
              <button className="p-2 text-gray-400 hover:text-gray-600">
                <ExternalLink className="h-5 w-5" />
              </button>
            </div>

            <div className="flex items-center gap-2 mb-4">
              <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                {opp.setAside}
              </span>
              <span className={`px-3 py-1 rounded-full text-sm ${getCompetitionColor(opp.competitionLevel)}`}>
                {opp.competitionLevel} Competition
              </span>
            </div>

            {opp.requirements && opp.requirements.length > 0 && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Key Requirements:</p>
                <div className="flex flex-wrap gap-2">
                  {opp.requirements.map((req, index) => (
                    <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm">
                      {req}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {opportunities.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
          <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Opportunities Found</h3>
          <p className="text-gray-500">Try adjusting your search criteria or NAICS code filter.</p>
        </div>
      )}
    </div>
  );
};

const GovernmentContractorDashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    complianceStatus: {
      cmmc: { level: 'Level 2', status: 'In Progress', score: 75, nextAssessment: '2025-09-15' },
      dfars: { status: 'Compliant', score: 90, lastAudit: '2024-12-01' },
      fedramp: { status: 'Not Required', cloudProvider: 'AWS GovCloud', authorized: true }
    },
    contractPipeline: {
      active: 12,
      pending: 8,
      totalValue: 2850000,
      winRate: 68
    },
    naicsAnalysis: {
      primary: '541511',
      secondary: ['541512', '541330', '541519'],
      opportunities: 45,
      competition: 'Medium'
    },
    performance: {
      cpars: 4.2,
      pastPerformance: 'Excellent',
      onTimeDelivery: 94,
      qualityScore: 4.6
    },
    realData: {
      totalCompanies: 0,
      avgInvestmentScore: 0,
      naicsBreakdown: {},
      stateBreakdown: {},
      gradeBreakdown: {}
    }
  });
  
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchGovConData();
  }, []);

  const fetchGovConData = async () => {
    console.log('🔄 Fetching government contractor data...');
    try {
      // Fetch from our real API
      const response = await fetch('http://localhost:8001/api/v1/government-contractor/');
      console.log('📡 API Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('📊 Full API data received:', data);
      console.log('🎯 Real data section:', data.realData);
      
      if (data) {
        setDashboardData(prev => {
          const newData = { ...prev, ...data };
          console.log('💾 Updated dashboard data:', newData);
          return newData;
        });
        console.log('✅ Data loaded successfully!');
      }
    } catch (error) {
      console.error('❌ Error fetching government contractor data:', error);
      console.error('❌ Error details:', error.message);
      // Fallback to default data
    } finally {
      setLoading(false);
      console.log('🏁 Loading completed');
    }
  };

  const ComplianceCard = ({ title, status, score, details, icon: Icon, color }) => (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${color}`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
          <h3 className="font-semibold text-gray-900">{title}</h3>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          status === 'Compliant' ? 'bg-green-100 text-green-700' :
          status === 'In Progress' ? 'bg-yellow-100 text-yellow-700' :
          'bg-red-100 text-red-700'
        }`}>
          {status}
        </span>
      </div>
      
      {score && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
            <span>Compliance Score</span>
            <span>{score}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${
                score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${score}%` }}
            ></div>
          </div>
        </div>
      )}
      
      <div className="space-y-2 text-sm text-gray-600">
        {Object.entries(details).map(([key, value]) => (
          <div key={key} className="flex justify-between">
            <span className="capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}:</span>
            <span className="font-medium">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );

  const MetricCard = ({ title, value, change, icon: Icon, color, subtitle }) => (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900 mt-2">{value}</p>
          {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
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

  const NAICSCard = () => (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">NAICS Code Analysis</h3>
      
      <div className="space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Primary NAICS</span>
            <span className="text-lg font-semibold text-gray-900">{dashboardData.naicsAnalysis.primary}</span>
          </div>
          <p className="text-sm text-gray-500">Custom Computer Programming Services</p>
        </div>
        
        <div>
          <span className="text-sm font-medium text-gray-600 block mb-2">Secondary NAICS</span>
          <div className="flex flex-wrap gap-2">
            {dashboardData.naicsAnalysis.secondary.map((naics) => (
              <span key={naics} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                {naics}
              </span>
            ))}
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div>
            <p className="text-sm text-gray-600">Open Opportunities</p>
            <p className="text-xl font-semibold text-green-600">{dashboardData.naicsAnalysis.opportunities}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Competition Level</p>
            <p className="text-xl font-semibold text-yellow-600">{dashboardData.naicsAnalysis.competition}</p>
          </div>
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
        <h1 className="text-2xl font-bold text-gray-900 mb-2">🚀 DEBUG MODE - Government Contractor Dashboard - v2.0 {new Date().toLocaleTimeString()}</h1>
        <p className="text-gray-600">📊 Real Data Status: {dashboardData.realData?.totalCompanies || 0} Companies | Loading: {loading.toString()} | Debug: Active</p>
        <div className="mb-4 p-3 bg-yellow-100 border border-yellow-300 rounded-lg">
          <p className="text-sm text-yellow-800">🔍 DEBUG: Check browser console for API call logs. Expected: 50 companies</p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: BarChart3 },
            { id: 'compliance', label: 'Compliance', icon: Shield },
            { id: 'opportunities', label: 'Opportunities', icon: Target },
            { id: 'performance', label: 'Performance', icon: Award }
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 px-4 py-2 border-b-2 font-medium text-sm ${
                activeTab === id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Total Companies"
              value={dashboardData.realData.totalCompanies}
              icon={Building2}
              color="bg-blue-500"
              subtitle="In Database"
            />
            <MetricCard
              title="Avg Investment Score"
              value={dashboardData.realData.avgInvestmentScore}
              icon={TrendingUp}
              color="bg-green-500"
              subtitle="Out of 100"
            />
            <MetricCard
              title="Win Rate"
              value={`${dashboardData.contractPipeline.winRate}%`}
              change={8.2}
              icon={Target}
              color="bg-purple-500"
            />
            <MetricCard
              title="CPARS Rating"
              value={dashboardData.performance.cpars}
              icon={Award}
              color="bg-indigo-500"
              subtitle="Excellent"
            />
          </div>

          {/* Charts Section - Temporarily disabled for testing */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">NAICS Breakdown</h3>
              <pre className="text-sm bg-gray-100 p-4 rounded">
                {JSON.stringify(dashboardData.realData.naicsBreakdown, null, 2)}
              </pre>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">State Breakdown</h3>
              <pre className="text-sm bg-gray-100 p-4 rounded">
                {JSON.stringify(dashboardData.realData.stateBreakdown, null, 2)}
              </pre>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Business Grades</h3>
              <pre className="text-sm bg-gray-100 p-4 rounded">
                {JSON.stringify(dashboardData.realData.gradeBreakdown, null, 2)}
              </pre>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Contract Pipeline</h3>
              <p>Active: {dashboardData.contractPipeline.active}</p>
              <p>Pending: {dashboardData.contractPipeline.pending}</p>
              <p>Total Value: ${(dashboardData.contractPipeline.totalValue / 1000000).toFixed(1)}M</p>
            </div>
          </div>

          {/* NAICS Analysis */}
          <NAICSCard />
        </div>
      )}

      {/* Compliance Tab */}
      {activeTab === 'compliance' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <ComplianceCard
              title="CMMC 2.0"
              status={dashboardData.complianceStatus.cmmc.status}
              score={dashboardData.complianceStatus.cmmc.score}
              details={{
                level: dashboardData.complianceStatus.cmmc.level,
                nextAssessment: dashboardData.complianceStatus.cmmc.nextAssessment
              }}
              icon={Shield}
              color="bg-blue-500"
            />
            
            <ComplianceCard
              title="DFARS"
              status={dashboardData.complianceStatus.dfars.status}
              score={dashboardData.complianceStatus.dfars.score}
              details={{
                lastAudit: dashboardData.complianceStatus.dfars.lastAudit,
                nistCompliant: 'Yes'
              }}
              icon={FileText}
              color="bg-green-500"
            />
            
            <ComplianceCard
              title="FedRAMP"
              status={dashboardData.complianceStatus.fedramp.status}
              details={{
                cloudProvider: dashboardData.complianceStatus.fedramp.cloudProvider,
                authorized: dashboardData.complianceStatus.fedramp.authorized ? 'Yes' : 'No'
              }}
              icon={Globe}
              color="bg-purple-500"
            />
          </div>

          {/* Compliance Score Chart - Temporarily disabled */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Compliance Scores</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">{dashboardData.complianceStatus.cmmc.score}%</p>
                <p className="text-sm text-gray-600">CMMC 2.0</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{dashboardData.complianceStatus.dfars.score}%</p>
                <p className="text-sm text-gray-600">DFARS</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-600">{dashboardData.complianceStatus.fedramp.authorized ? '100%' : '0%'}</p>
                <p className="text-sm text-gray-600">FedRAMP</p>
              </div>
            </div>
          </div>

          {/* Compliance Actions */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Required Actions</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                <div>
                  <p className="font-medium text-gray-900">CMMC Level 2 Assessment Due</p>
                  <p className="text-sm text-gray-600">Schedule third-party assessment by September 2025</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                <Clock className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="font-medium text-gray-900">Update System Security Plan</p>
                  <p className="text-sm text-gray-600">Annual SSP review and updates required</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Opportunities Tab */}
      {activeTab === 'opportunities' && (
        <OpportunitiesTab naics={dashboardData.naicsAnalysis.primary} />
      )}

      {/* Performance Tab */}
      {activeTab === 'performance' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Past Performance</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">CPARS Rating</span>
                  <span className="text-2xl font-semibold text-green-600">{dashboardData.performance.cpars}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">On-Time Delivery</span>
                  <span className="text-xl font-semibold text-blue-600">{dashboardData.performance.onTimeDelivery}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Quality Score</span>
                  <span className="text-xl font-semibold text-purple-600">{dashboardData.performance.qualityScore}</span>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Contract Performance</h3>
              <div className="text-center py-8">
                <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Performance analytics coming soon</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GovernmentContractorDashboard;