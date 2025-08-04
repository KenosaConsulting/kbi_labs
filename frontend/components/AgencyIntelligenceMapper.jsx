import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent 
} from '@/components/ui/card';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  RefreshCw, 
  Download, 
  Eye, 
  AlertCircle, 
  CheckCircle, 
  Clock,
  Users,
  DollarSign,
  FileText,
  Building
} from 'lucide-react';

import EnrichmentProgressModal from './EnrichmentProgressModal';
import DataQualityIndicator from './DataQualityIndicator';
import AgencyDataVisualization from './AgencyDataVisualization';
import { useEnrichmentWebSocket } from '../hooks/useEnrichmentWebSocket';
import { enrichmentApi } from '../services/enrichmentApi';
import { formatCurrency, formatDate, formatPercentage } from '../utils/formatters';

const AgencyIntelligenceMapper = () => {
  // State management
  const [selectedAgency, setSelectedAgency] = useState('');
  const [agencies, setAgencies] = useState([]);
  const [enrichmentStatus, setEnrichmentStatus] = useState('idle'); // idle, loading, completed, error
  const [currentJobId, setCurrentJobId] = useState(null);
  const [agencyData, setAgencyData] = useState(null);
  const [enrichmentSummary, setEnrichmentSummary] = useState(null);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [error, setError] = useState(null);
  const [dataTypes, setDataTypes] = useState(['budget', 'personnel', 'contracts', 'organizational']);
  const [enrichmentDepth, setEnrichmentDepth] = useState('standard');
  
  // WebSocket for real-time updates
  const { 
    progress, 
    status: wsStatus, 
    error: wsError,
    connect: connectWebSocket,
    disconnect: disconnectWebSocket 
  } = useEnrichmentWebSocket();

  // Load supported agencies on component mount
  useEffect(() => {
    loadSupportedAgencies();
  }, []);

  // Handle WebSocket status updates
  useEffect(() => {
    if (wsStatus) {
      setEnrichmentStatus(wsStatus);
      
      if (wsStatus === 'completed') {
        setShowProgressModal(false);
        loadAgencyData(selectedAgency);
        loadAgencySummary(selectedAgency);
      } else if (wsStatus === 'failed') {
        setError(wsError || 'Enrichment failed');
        setShowProgressModal(false);
      }
    }
  }, [wsStatus, wsError, selectedAgency]);

  // API Functions
  const loadSupportedAgencies = async () => {
    try {
      const response = await enrichmentApi.getSupportedAgencies();
      setAgencies(response.agencies);
    } catch (err) {
      console.error('Failed to load agencies:', err);
      setError('Failed to load supported agencies');
    }
  };

  const loadAgencyData = async (agencyCode) => {
    if (!agencyCode) return;

    try {
      const response = await enrichmentApi.getAgencyData(agencyCode, {
        dataTypes: dataTypes,
        includeMetadata: true
      });
      
      setAgencyData(response);
      setError(null);
    } catch (err) {
      console.error('Failed to load agency data:', err);
      // Don't set error here - might just be no data available yet
    }
  };

  const loadAgencySummary = async (agencyCode) => {
    if (!agencyCode) return;

    try {
      const response = await enrichmentApi.getAgencySummary(agencyCode);
      setEnrichmentSummary(response);
    } catch (err) {
      console.error('Failed to load agency summary:', err);
    }
  };

  // Event Handlers
  const handleAgencySelect = useCallback(async (agencyCode) => {
    setSelectedAgency(agencyCode);
    setError(null);
    
    // Load existing data and summary
    await Promise.all([
      loadAgencyData(agencyCode),
      loadAgencySummary(agencyCode)
    ]);
  }, [dataTypes]);

  const handleEnrichmentRequest = async () => {
    if (!selectedAgency) return;

    try {
      setError(null);
      setEnrichmentStatus('loading');

      const response = await enrichmentApi.requestEnrichment({
        agency_code: selectedAgency,
        agency_name: agencies.find(a => a.code === selectedAgency)?.name,
        data_types: dataTypes,
        enrichment_depth: enrichmentDepth,
        priority: 'normal'
      });

      if (response.cache_hit) {
        // Data was available from cache
        setEnrichmentStatus('completed');
        setAgencyData(response.data);
      } else if (response.job_id) {
        // Job was queued - show progress modal and connect WebSocket
        setCurrentJobId(response.job_id);
        setShowProgressModal(true);
        connectWebSocket(response.job_id);
      }

    } catch (err) {
      console.error('Enrichment request failed:', err);
      setError(err.message || 'Failed to request enrichment');
      setEnrichmentStatus('error');
    }
  };

  const handleDataTypeToggle = (dataType) => {
    setDataTypes(prev => 
      prev.includes(dataType) 
        ? prev.filter(dt => dt !== dataType)
        : [...prev, dataType]
    );
  };

  const handleRefreshData = () => {
    if (selectedAgency) {
      loadAgencyData(selectedAgency);
      loadAgencySummary(selectedAgency);
    }
  };

  const handleInvalidateCache = async () => {
    if (!selectedAgency) return;

    try {
      await enrichmentApi.invalidateCache(selectedAgency, dataTypes);
      setAgencyData(null);
      setEnrichmentSummary(null);
    } catch (err) {
      console.error('Failed to invalidate cache:', err);
      setError('Failed to invalidate cache');
    }
  };

  // Helper functions
  const getStatusBadgeVariant = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'warning';
      case 'failed': return 'destructive';
      case 'queued': return 'secondary';
      default: return 'outline';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4" />;
      case 'running': return <RefreshCw className="h-4 w-4 animate-spin" />;
      case 'failed': return <AlertCircle className="h-4 w-4" />;
      case 'queued': return <Clock className="h-4 w-4" />;
      default: return null;
    }
  };

  const calculateDataFreshness = (lastUpdated) => {
    if (!lastUpdated) return 'Unknown';
    
    const now = new Date();
    const updated = new Date(lastUpdated);
    const diffHours = Math.floor((now - updated) / (1000 * 60 * 60));
    
    if (diffHours < 1) return 'Fresh';
    if (diffHours < 24) return `${diffHours} hours old`;
    if (diffHours < 168) return `${Math.floor(diffHours / 24)} days old`;
    return 'Stale';
  };

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Building className="h-6 w-6" />
              Agency Intelligence Mapper
            </span>
            {selectedAgency && (
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={handleRefreshData}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh
                </Button>
                <Button variant="outline" size="sm" onClick={handleInvalidateCache}>
                  Clear Cache
                </Button>
              </div>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Agency Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Select Agency</label>
              <Select value={selectedAgency} onValueChange={handleAgencySelect}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose an agency..." />
                </SelectTrigger>
                <SelectContent>
                  {agencies.map((agency) => (
                    <SelectItem key={agency.code} value={agency.code}>
                      {agency.name} ({agency.code})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Enrichment Depth</label>
              <Select value={enrichmentDepth} onValueChange={setEnrichmentDepth}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="basic">Basic (Fast)</SelectItem>
                  <SelectItem value="standard">Standard</SelectItem>
                  <SelectItem value="comprehensive">Comprehensive (Detailed)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="col-span-2">
              <label className="text-sm font-medium mb-2 block">Data Types</label>
              <div className="flex flex-wrap gap-2">
                {[
                  { key: 'budget', label: 'Budget', icon: DollarSign },
                  { key: 'personnel', label: 'Personnel', icon: Users },
                  { key: 'contracts', label: 'Contracts', icon: FileText },
                  { key: 'organizational', label: 'Org Structure', icon: Building }
                ].map(({ key, label, icon: Icon }) => (
                  <Badge
                    key={key}
                    variant={dataTypes.includes(key) ? 'default' : 'outline'}
                    className="cursor-pointer hover:bg-primary/10"
                    onClick={() => handleDataTypeToggle(key)}
                  >
                    <Icon className="h-3 w-3 mr-1" />
                    {label}
                  </Badge>
                ))}
              </div>
            </div>
          </div>

          {/* Action Button */}
          <div className="flex justify-between items-center">
            <Button 
              onClick={handleEnrichmentRequest}
              disabled={!selectedAgency || enrichmentStatus === 'loading'}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {enrichmentStatus === 'loading' ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              {enrichmentStatus === 'loading' ? 'Processing...' : 'Enrich Agency Data'}
            </Button>

            {enrichmentSummary && (
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span>Last enriched: {formatDate(enrichmentSummary.last_successful_enrichment)}</span>
                <Badge variant={getStatusBadgeVariant(enrichmentSummary.current_status)}>
                  {getStatusIcon(enrichmentSummary.current_status)}
                  {enrichmentSummary.current_status || 'Unknown'}
                </Badge>
              </div>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Agency Summary Card */}
      {enrichmentSummary && (
        <Card>
          <CardHeader>
            <CardTitle>Agency Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {enrichmentSummary.available_data_types}
                </div>
                <div className="text-sm text-muted-foreground">Data Types Available</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {formatPercentage(enrichmentSummary.average_quality_score)}
                </div>
                <div className="text-sm text-muted-foreground">Average Quality</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {enrichmentSummary.total_access_count}
                </div>
                <div className="text-sm text-muted-foreground">Total Accesses</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {calculateDataFreshness(enrichmentSummary.last_successful_enrichment)}
                </div>
                <div className="text-sm text-muted-foreground">Data Freshness</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Data Quality Indicators */}
      {agencyData && agencyData.data && (
        <Card>
          <CardHeader>
            <CardTitle>Data Quality Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(agencyData.data).map(([dataType, typeData]) => {
                const metadata = typeData._metadata;
                return (
                  <DataQualityIndicator
                    key={dataType}
                    dataType={dataType}
                    qualityScore={metadata?.quality_score || 0}
                    lastUpdated={metadata?.last_updated}
                    accessCount={metadata?.access_count || 0}
                  />
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Data Visualization */}
      {agencyData && agencyData.data_available && (
        <AgencyDataVisualization 
          agencyCode={selectedAgency}
          agencyData={agencyData.data}
          enrichmentSummary={enrichmentSummary}
        />
      )}

      {/* No Data State */}
      {selectedAgency && !agencyData?.data_available && enrichmentStatus !== 'loading' && (
        <Card>
          <CardContent className="text-center py-12">
            <Building className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Data Available</h3>
            <p className="text-muted-foreground mb-4">
              No enriched data found for this agency. Click "Enrich Agency Data" to collect and process government data.
            </p>
            <Button onClick={handleEnrichmentRequest} disabled={enrichmentStatus === 'loading'}>
              <Download className="h-4 w-4 mr-2" />
              Start Data Enrichment
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Progress Modal */}
      <EnrichmentProgressModal
        open={showProgressModal}
        onClose={() => {
          setShowProgressModal(false);
          disconnectWebSocket();
        }}
        jobId={currentJobId}
        agencyCode={selectedAgency}
        agencyName={agencies.find(a => a.code === selectedAgency)?.name}
        dataTypes={dataTypes}
        progress={progress}
        status={wsStatus}
        error={wsError}
      />
    </div>
  );
};

export default AgencyIntelligenceMapper;