import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import {
  Users,
  DollarSign,
  FileText,
  Building,
  TrendingUp,
  ExternalLink,
  Download,
  Eye,
  Filter,
  BarChart3,
  PieChart,
  MapPin,
  Phone,
  Mail,
  Calendar,
  Award,
  Target
} from 'lucide-react';
import { formatCurrency, formatDate, formatPercentage } from '../utils/formatters';

const AgencyDataVisualization = ({
  agencyCode,
  agencyData = {},
  enrichmentSummary = null
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedDataType, setSelectedDataType] = useState('all');

  const getDataTypeIcon = (type) => {
    switch (type) {
      case 'budget':
        return <DollarSign className="h-5 w-5" />;
      case 'personnel':
        return <Users className="h-5 w-5" />;
      case 'contracts':
        return <FileText className="h-5 w-5" />;
      case 'organizational':
        return <Building className="h-5 w-5" />;
      case 'strategic':
        return <TrendingUp className="h-5 w-5" />;
      default:
        return <FileText className="h-5 w-5" />;
    }
  };

  const renderOverview = () => {
    const dataTypes = Object.keys(agencyData);
    const totalRecords = dataTypes.reduce((sum, type) => {
      const typeData = agencyData[type];
      if (typeData?.summary?.total_records) {
        return sum + typeData.summary.total_records;
      }
      return sum;
    }, 0);

    return (
      <div className="space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Data Types
                  </p>
                  <p className="text-2xl font-bold">{dataTypes.length}</p>
                </div>
                <BarChart3 className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Total Records
                  </p>
                  <p className="text-2xl font-bold">{totalRecords.toLocaleString()}</p>
                </div>
                <FileText className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Avg Quality
                  </p>
                  <p className="text-2xl font-bold">
                    {enrichmentSummary?.average_quality_score ? 
                      formatPercentage(enrichmentSummary.average_quality_score) : 'N/A'}
                  </p>
                </div>
                <Award className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Last Updated
                  </p>
                  <p className="text-sm font-bold">
                    {enrichmentSummary?.last_successful_enrichment ? 
                      formatDate(enrichmentSummary.last_successful_enrichment) : 'Never'}
                  </p>
                </div>
                <Calendar className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Data Type Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Data Type Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dataTypes.map((dataType) => {
                const typeData = agencyData[dataType];
                const metadata = typeData?._metadata || {};
                
                return (
                  <div key={dataType} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getDataTypeIcon(dataType)}
                      <div>
                        <h4 className="font-medium capitalize">{dataType} Data</h4>
                        <p className="text-sm text-muted-foreground">
                          {typeData?.summary?.total_records || 0} records
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge variant="outline">
                        Quality: {formatPercentage(metadata.quality_score || 0)}
                      </Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setActiveTab(dataType)}
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        View Details
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderBudgetData = () => {
    const budgetData = agencyData.budget;
    if (!budgetData) return <div>No budget data available</div>;

    const analysis = budgetData.budget_analysis;
    const summary = budgetData.summary;

    return (
      <div className="space-y-6">
        {/* Budget Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Total Budget Authority
                  </p>
                  <p className="text-xl font-bold">
                    {formatCurrency(summary?.total_budget_authority || 0)}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Total Outlays
                  </p>
                  <p className="text-xl font-bold">
                    {formatCurrency(summary?.total_outlays || 0)}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Execution Rate
                  </p>
                  <p className="text-xl font-bold">
                    {formatPercentage(summary?.execution_rate || 0)}
                  </p>
                </div>
                <Target className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Budget Line Items */}
        {analysis?.budget_line_items && (
          <Card>
            <CardHeader>
              <CardTitle>Budget Line Items</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analysis.budget_line_items.slice(0, 10).map((item, index) => (
                  <div key={index} className="flex justify-between items-center p-3 border rounded">
                    <div>
                      <h4 className="font-medium">{item.program_name || `Program ${index + 1}`}</h4>
                      <p className="text-sm text-muted-foreground">
                        {item.account_code || 'N/A'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">
                        {formatCurrency(item.budget_authority || 0)}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        FY {item.fiscal_year || '2024'}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderPersonnelData = () => {
    const personnelData = agencyData.personnel;
    if (!personnelData) return <div>No personnel data available</div>;

    const records = personnelData.personnel_records || [];
    const summary = personnelData.summary || {};

    return (
      <div className="space-y-6">
        {/* Personnel Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Total Personnel
                  </p>
                  <p className="text-2xl font-bold">{summary.total_personnel || 0}</p>
                </div>
                <Users className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Avg Confidence
                  </p>
                  <p className="text-2xl font-bold">
                    {formatPercentage(summary.average_confidence || 0)}
                  </p>
                </div>
                <Award className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Data Sources
                  </p>
                  <p className="text-2xl font-bold">
                    {summary.data_sources?.length || 0}
                  </p>
                </div>
                <FileText className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Personnel Records */}
        <Card>
          <CardHeader>
            <CardTitle>Key Personnel</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {records.slice(0, 10).map((person, index) => (
                <div key={index} className="flex items-start justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium">{person.name || 'Name Not Available'}</h4>
                    <p className="text-sm text-muted-foreground mb-2">
                      {person.title || 'Title Not Available'}
                    </p>
                    {person.office && (
                      <Badge variant="outline" className="mr-2">
                        <Building className="h-3 w-3 mr-1" />
                        {person.office}
                      </Badge>
                    )}
                    <Badge variant="outline">
                      Confidence: {formatPercentage(person.confidence_score || 0)}
                    </Badge>
                  </div>
                  <div className="text-right text-sm text-muted-foreground">
                    {person.contact_info?.email && (
                      <div className="flex items-center gap-1 mb-1">
                        <Mail className="h-3 w-3" />
                        <span>{person.contact_info.email}</span>
                      </div>
                    )}
                    {person.contact_info?.phone && (
                      <div className="flex items-center gap-1">
                        <Phone className="h-3 w-3" />
                        <span>{person.contact_info.phone}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderOrganizationalData = () => {
    const orgData = agencyData.organizational;
    if (!orgData) return <div>No organizational data available</div>;

    const chart = orgData.organizational_chart || {};
    const summary = orgData.summary || {};

    return (
      <div className="space-y-6">
        {/* Organizational Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Total Units
                  </p>
                  <p className="text-2xl font-bold">{summary.total_units || 0}</p>
                </div>
                <Building className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Personnel Count
                  </p>
                  <p className="text-2xl font-bold">{summary.total_personnel || 0}</p>
                </div>
                <Users className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Org Depth
                  </p>
                  <p className="text-2xl font-bold">{summary.organizational_depth || 0}</p>
                </div>
                <BarChart3 className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Organizational Units */}
        {chart.organizational_units && (
          <Card>
            <CardHeader>
              <CardTitle>Organizational Units</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {chart.organizational_units.slice(0, 10).map((unit, index) => (
                  <div key={index} className="flex justify-between items-center p-3 border rounded">
                    <div>
                      <h4 className="font-medium">{unit.name || `Unit ${index + 1}`}</h4>
                      <p className="text-sm text-muted-foreground">
                        {unit.type || 'Department'} • Level {unit.level || 1}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge variant="outline">
                        {unit.personnel_count || 0} staff
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderContractsData = () => {
    const contractsData = agencyData.contracts;
    if (!contractsData) return <div>No contracts data available</div>;

    return (
      <Card>
        <CardHeader>
          <CardTitle>Contract Data</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Contract data visualization will be implemented based on the specific structure of your contract data.
          </p>
        </CardContent>
      </Card>
    );
  };

  const renderStrategicData = () => {
    const strategicData = agencyData.strategic;
    if (!strategicData) return <div>No strategic data available</div>;

    return (
      <Card>
        <CardHeader>
          <CardTitle>Strategic Data</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Strategic data visualization will be implemented based on the specific structure of your strategic planning data.
          </p>
        </CardContent>
      </Card>
    );
  };

  const availableTabs = ['overview', ...Object.keys(agencyData)];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Agency Data Visualization
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export Data
            </Button>
            <Button variant="outline" size="sm">
              <ExternalLink className="h-4 w-4 mr-2" />
              Full Report
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2 lg:grid-cols-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            {Object.keys(agencyData).map((dataType) => (
              <TabsTrigger key={dataType} value={dataType} className="capitalize">
                {dataType}
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            {renderOverview()}
          </TabsContent>

          <TabsContent value="budget" className="mt-6">
            {renderBudgetData()}
          </TabsContent>

          <TabsContent value="personnel" className="mt-6">
            {renderPersonnelData()}
          </TabsContent>

          <TabsContent value="organizational" className="mt-6">
            {renderOrganizationalData()}
          </TabsContent>

          <TabsContent value="contracts" className="mt-6">
            {renderContractsData()}
          </TabsContent>

          <TabsContent value="strategic" className="mt-6">
            {renderStrategicData()}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default AgencyDataVisualization;