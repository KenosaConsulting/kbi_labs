import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';

const UnifiedIntelligence = () => {
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [selectedAgency, setSelectedAgency] = useState(null);
  const [activeTab, setActiveTab] = useState('companies');

  // Fetch companies
  const { data: companies, isLoading: companiesLoading } = useQuery({
    queryKey: ['companies'],
    queryFn: async () => {
      const response = await fetch('/api/v1/companies');
      return response.json();
    }
  });

  // Fetch agencies
  const { data: agencies, isLoading: agenciesLoading } = useQuery({
    queryKey: ['agencies'],
    queryFn: async () => {
      const response = await fetch('/api/data-enrichment/agencies');
      return response.json();
    }
  });

  // Fetch intelligence report
  const { data: intelligenceReport, refetch: refetchReport } = useQuery({
    queryKey: ['intelligence-report', selectedCompany?.id],
    queryFn: async () => {
      if (!selectedCompany) return null;
      const response = await fetch(`/api/v1/companies/${selectedCompany.id}/intelligence-report`);
      return response.json();
    },
    enabled: !!selectedCompany
  });

  // Request enrichment mutation
  const enrichmentMutation = useMutation({
    mutationFn: async (agencyCode) => {
      const response = await fetch('/api/data-enrichment/enrich', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agency_code: agencyCode,
          agency_name: agencies?.agencies?.find(a => a.code === agencyCode)?.name,
          data_types: ['budget', 'personnel', 'contracts'],
          enrichment_depth: 'standard'
        })
      });
      return response.json();
    }
  });

  const CompanyCard = ({ company, isSelected, onClick }) => (
    <div 
      className={`p-4 border rounded-lg cursor-pointer transition-all ${
        isSelected 
          ? 'border-blue-500 bg-blue-50 shadow-md' 
          : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
      }`}
      onClick={() => onClick(company)}
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-lg">{company.name}</h3>
        <span className={`px-2 py-1 text-xs rounded-full ${
          company.opportunity_score >= 95 ? 'bg-green-100 text-green-800' :
          company.opportunity_score >= 90 ? 'bg-yellow-100 text-yellow-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {company.opportunity_score.toFixed(1)}% Opportunity Score
        </span>
      </div>
      
      <div className="space-y-1 text-sm text-gray-600">
        <div>NAICS: {company.naics_code}</div>
        <div>Revenue: ${(company.revenue / 1000000).toFixed(1)}M</div>
        <div>Gov Contracts: ${(company.government_contracts_value / 1000000).toFixed(1)}M</div>
      </div>
    </div>
  );

  const AgencyCard = ({ agency, onEnrich }) => (
    <div className="p-4 border rounded-lg">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-semibold">{agency.name}</h3>
          <div className="text-sm text-gray-600">Code: {agency.code}</div>
          <div className="text-xs text-gray-500 mt-1">{agency.category}</div>
        </div>
        <button
          onClick={() => onEnrich(agency.code)}
          disabled={enrichmentMutation.isPending}
          className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {enrichmentMutation.isPending ? 'Enriching...' : 'Enrich Data'}
        </button>
      </div>
    </div>
  );

  const IntelligenceReport = ({ report }) => {
    if (!report) return null;

    return (
      <div className="space-y-6">
        {/* Company Overview */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Intelligence Report: {report.company.name}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded">
              <div className="text-2xl font-bold text-blue-600">{report.opportunity_score.toFixed(1)}%</div>
              <div className="text-sm text-gray-600">Overall Opportunity Score</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded">
              <div className="text-2xl font-bold text-green-600">{report.target_agencies.length}</div>
              <div className="text-sm text-gray-600">Target Agencies</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded">
              <div className="text-2xl font-bold text-purple-600">
                ${((report.company.government_contracts_value || 0) / 1000000).toFixed(1)}M
              </div>
              <div className="text-sm text-gray-600">Current Gov Contracts</div>
            </div>
          </div>
        </div>

        {/* Strategic Recommendations */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">🎯 Strategic Recommendations</h3>
          <ul className="space-y-2">
            {report.strategic_recommendations.map((rec, index) => (
              <li key={index} className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span className="text-gray-700">{rec}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Target Agencies */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">🏛️ Target Agencies</h3>
          <div className="space-y-4">
            {report.target_agencies.map((agency, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="font-semibold">{agency.agency_name}</h4>
                    <div className="text-sm text-gray-600">Code: {agency.agency_code}</div>
                  </div>
                  <div className="text-right text-sm">
                    <div className="text-green-600 font-semibold">
                      ${(agency.budget_data?.annual_budget / 1000000).toFixed(0)}M Annual Budget
                    </div>
                    <div className="text-blue-600">
                      ${(agency.budget_data?.it_budget / 1000000).toFixed(0)}M IT Budget
                    </div>
                  </div>
                </div>

                {/* Key Personnel */}
                <div className="mb-3">
                  <h5 className="font-medium text-sm mb-2">👥 Key Personnel</h5>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {agency.key_personnel.map((person, pIndex) => (
                      <div key={pIndex} className="bg-gray-50 p-2 rounded text-xs">
                        <div className="font-medium">{person.name}</div>
                        <div className="text-gray-600">{person.title}</div>
                        <div className="text-blue-600">{person.email}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Upcoming Opportunities */}
                <div className="mb-3">
                  <h5 className="font-medium text-sm mb-2">💼 Upcoming Opportunities</h5>
                  <div className="space-y-2">
                    {agency.upcoming_opportunities.map((opp, oIndex) => (
                      <div key={oIndex} className="bg-yellow-50 p-2 rounded text-xs">
                        <div className="font-medium">{opp.title}</div>
                        <div className="flex justify-between text-gray-600">
                          <span>Value: ${(opp.value / 1000000).toFixed(1)}M</span>
                          <span>Due: {opp.due_date}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Agency Recommendations */}
                <div>
                  <h5 className="font-medium text-sm mb-2">📋 Agency-Specific Strategy</h5>
                  <ul className="text-xs space-y-1">
                    {agency.strategic_recommendations.map((rec, rIndex) => (
                      <li key={rIndex} className="text-gray-600">• {rec}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          🚀 KBI Labs Unified Intelligence Platform
        </h1>
        <p className="text-gray-600">
          Comprehensive SMB and Government Contractor Intelligence System
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white shadow-sm rounded-lg">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {[
              { id: 'companies', label: '🏢 Company Intelligence', count: companies?.total },
              { id: 'agencies', label: '🏛️ Agency Intelligence', count: agencies?.total_count },
              { id: 'report', label: '📊 Intelligence Report' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
                {tab.count && (
                  <span className="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-xs">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Companies Tab */}
          {activeTab === 'companies' && (
            <div>
              <div className="mb-4">
                <h2 className="text-lg font-semibold">Company Intelligence Dashboard</h2>
                <p className="text-gray-600 text-sm">Select a company to view detailed intelligence and agency recommendations</p>
              </div>
              
              {companiesLoading ? (
                <div className="text-center py-8">Loading companies...</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {companies?.companies?.map((company) => (
                    <CompanyCard
                      key={company.id}
                      company={company}
                      isSelected={selectedCompany?.id === company.id}
                      onClick={setSelectedCompany}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Agencies Tab */}
          {activeTab === 'agencies' && (
            <div>
              <div className="mb-4">
                <h2 className="text-lg font-semibold">Government Agency Intelligence</h2>
                <p className="text-gray-600 text-sm">Enrich agency data to get detailed intelligence for strategic targeting</p>
              </div>
              
              {agenciesLoading ? (
                <div className="text-center py-8">Loading agencies...</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {agencies?.agencies?.map((agency) => (
                    <AgencyCard
                      key={agency.code}
                      agency={agency}
                      onEnrich={(code) => enrichmentMutation.mutate(code)}
                    />
                  ))}
                </div>
              )}

              {/* Enrichment Results */}
              {enrichmentMutation.data && (
                <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <h3 className="font-semibold text-green-800 mb-2">✅ Enrichment Successful</h3>
                  <div className="text-sm text-green-700">
                    <div>Job ID: {enrichmentMutation.data.job_id}</div>
                    <div>Status: {enrichmentMutation.data.status}</div>
                    <div>Message: {enrichmentMutation.data.message}</div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Intelligence Report Tab */}
          {activeTab === 'report' && (
            <div>
              {!selectedCompany ? (
                <div className="text-center py-12">
                  <div className="text-gray-400 text-6xl mb-4">📊</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Company Selected</h3>
                  <p className="text-gray-600">
                    Go to the Company Intelligence tab and select a company to generate a comprehensive intelligence report.
                  </p>
                </div>
              ) : intelligenceReport ? (
                <IntelligenceReport report={intelligenceReport} />
              ) : (
                <div className="text-center py-8">
                  Loading intelligence report for {selectedCompany.name}...
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UnifiedIntelligence;