import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Building2, MapPin, Phone, Globe, Calendar, Shield, 
  TrendingUp, DollarSign, Users, Award, AlertCircle,
  ArrowLeft, Edit, Download, RefreshCw
} from 'lucide-react';
import api from '../services/api';

const CompanyDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCompanyDetails();
  }, [id]);

  const fetchCompanyDetails = async () => {
    try {
      setLoading(true);
      const data = await api.getCompanyDetails(id);
      setCompany(data);
    } catch (err) {
      setError('Failed to load company details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getRiskColor = (score) => {
    if (score <= 20) return 'text-green-600 bg-green-50';
    if (score <= 40) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error || !company) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-600 mb-4">{error || 'Company not found'}</p>
        <button
          onClick={() => navigate('/companies')}
          className="text-indigo-600 hover:text-indigo-700"
        >
          Back to Companies
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/companies')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Companies
        </button>
        
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{company.name}</h1>
            {company.dba_name && (
              <p className="text-gray-600">DBA: {company.dba_name}</p>
            )}
            <p className="text-lg text-gray-600 mt-1">{company.industry}</p>
          </div>
          
          <div className="flex gap-2">
            <button className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2">
              <Edit className="h-4 w-4" />
              Edit
            </button>
            <button className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2">
              <Download className="h-4 w-4" />
              Export
            </button>
            <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2">
              <RefreshCw className="h-4 w-4" />
              Refresh Data
            </button>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600">KBI Score</p>
            <TrendingUp className="h-5 w-5 text-gray-400" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{company.metrics.kbi_score}</p>
          <span className={`inline-block mt-2 px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(company.metrics.kbi_score)}`}>
            {company.metrics.kbi_score >= 80 ? 'Excellent' : company.metrics.kbi_score >= 60 ? 'Good' : 'Needs Attention'}
          </span>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600">Risk Score</p>
            <Shield className="h-5 w-5 text-gray-400" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{company.metrics.risk_score}</p>
          <span className={`inline-block mt-2 px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(company.metrics.risk_score)}`}>
            {company.metrics.risk_score <= 20 ? 'Low Risk' : company.metrics.risk_score <= 40 ? 'Medium Risk' : 'High Risk'}
          </span>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600">Revenue</p>
            <DollarSign className="h-5 w-5 text-gray-400" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{company.financials.revenue}</p>
          <p className="text-sm text-gray-500 mt-2">{company.financials.contracts_count} contracts</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-600">Employees</p>
            <Users className="h-5 w-5 text-gray-400" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{company.metrics.employee_count || 'N/A'}</p>
          <p className="text-sm text-gray-500 mt-2">In business {company.metrics.business_age}</p>
        </div>
      </div>

      {/* Detailed Information Tabs */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="border-b">
          <nav className="flex -mb-px">
            <button className="px-6 py-3 border-b-2 border-indigo-500 text-indigo-600 font-medium">
              Overview
            </button>
            <button className="px-6 py-3 border-b-2 border-transparent text-gray-500 hover:text-gray-700">
              Financials
            </button>
            <button className="px-6 py-3 border-b-2 border-transparent text-gray-500 hover:text-gray-700">
              Certifications
            </button>
            <button className="px-6 py-3 border-b-2 border-transparent text-gray-500 hover:text-gray-700">
              Risk Analysis
            </button>
          </nav>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Contact Information */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h3>
              <div className="space-y-3">
                <div className="flex items-start">
                  <MapPin className="h-5 w-5 text-gray-400 mt-0.5 mr-3" />
                  <div>
                    <p className="text-gray-900">{company.address.line1}</p>
                    {company.address.line2 && <p className="text-gray-900">{company.address.line2}</p>}
                    <p className="text-gray-900">{company.address.city}, {company.address.state} {company.address.zipcode}</p>
                  </div>
                </div>
                
                {company.contact.phone && (
                  <div className="flex items-center">
                    <Phone className="h-5 w-5 text-gray-400 mr-3" />
                    <p className="text-gray-900">{company.contact.phone}</p>
                  </div>
                )}
                
                {company.contact.website && (
                  <div className="flex items-center">
                    <Globe className="h-5 w-5 text-gray-400 mr-3" />
                    <a href={company.contact.website} target="_blank" rel="noopener noreferrer" 
                       className="text-indigo-600 hover:text-indigo-700">
                      {company.contact.website}
                    </a>
                  </div>
                )}
              </div>
            </div>

            {/* Business Information */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Business Information</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-600">NAICS Code</p>
                  <p className="text-gray-900">{company.naics_code}</p>
                </div>
                
                <div>
                  <p className="text-sm text-gray-600">CAGE Code</p>
                  <p className="text-gray-900">{company.certifications.cage_code || 'N/A'}</p>
                </div>
                
                <div>
                  <p className="text-sm text-gray-600">SAM Registration</p>
                  <p className="text-gray-900">
                    <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                      company.certifications.sam_status === 'Active' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {company.certifications.sam_status || 'Not Registered'}
                    </span>
                  </p>
                </div>
                
                {company.certifications.clearance_level && (
                  <div>
                    <p className="text-sm text-gray-600">Clearance Level</p>
                    <p className="text-gray-900">{company.certifications.clearance_level}</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Socioeconomic Certifications */}
          {company.certifications.socioeconomic && company.certifications.socioeconomic.length > 0 && (
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Certifications</h3>
              <div className="flex flex-wrap gap-2">
                {company.certifications.socioeconomic.map((cert, index) => (
                  <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                    {cert}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Enrichment Status */}
          <div className="mt-8 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Data Enrichment Status</p>
                <p className="text-gray-900">
                  Last updated: {company.enrichment.last_updated ? 
                    new Date(company.enrichment.last_updated).toLocaleDateString() : 
                    'Never'}
                </p>
              </div>
              <button className="text-indigo-600 hover:text-indigo-700 text-sm font-medium">
                View Details →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompanyDetails;
