import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  CheckCircle,
  RefreshCw,
  AlertCircle,
  Clock,
  X,
  Building,
  Users,
  DollarSign,
  FileText
} from 'lucide-react';

const EnrichmentProgressModal = ({
  open,
  onClose,
  jobId,
  agencyCode,
  agencyName,
  dataTypes = [],
  progress = 0,
  status = 'queued',
  error = null
}) => {
  const getStatusIcon = (currentStatus) => {
    switch (currentStatus) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'running':
        return <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'queued':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (currentStatus) => {
    switch (currentStatus) {
      case 'completed':
        return 'text-green-600 bg-green-50';
      case 'running':
        return 'text-blue-600 bg-blue-50';
      case 'failed':
        return 'text-red-600 bg-red-50';
      case 'queued':
        return 'text-yellow-600 bg-yellow-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusText = (currentStatus) => {
    switch (currentStatus) {
      case 'completed':
        return 'Enrichment Completed';
      case 'running':
        return 'Processing Data';
      case 'failed':
        return 'Enrichment Failed';
      case 'queued':
        return 'Queued for Processing';
      default:
        return 'Unknown Status';
    }
  };

  const getDataTypeIcon = (dataType) => {
    switch (dataType) {
      case 'budget':
        return <DollarSign className="h-4 w-4" />;
      case 'personnel':
        return <Users className="h-4 w-4" />;
      case 'contracts':
        return <FileText className="h-4 w-4" />;
      case 'organizational':
        return <Building className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const formatDataType = (dataType) => {
    const types = {
      budget: 'Budget Data',
      personnel: 'Personnel Data',
      contracts: 'Contract Data',
      organizational: 'Organizational Data',
      strategic: 'Strategic Data'
    };
    return types[dataType] || dataType;
  };

  const getProgressMessage = () => {
    if (status === 'queued') {
      return 'Your enrichment request is in the queue and will begin processing shortly.';
    }
    if (status === 'running') {
      if (progress < 25) {
        return 'Connecting to government data sources...';
      } else if (progress < 50) {
        return 'Collecting and processing data...';
      } else if (progress < 75) {
        return 'Analyzing and validating information...';
      } else if (progress < 100) {
        return 'Finalizing enrichment and caching results...';
      }
    }
    if (status === 'completed') {
      return 'All data has been successfully enriched and is ready for analysis.';
    }
    if (status === 'failed') {
      return 'An error occurred during the enrichment process.';
    }
    return 'Processing your request...';
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Building className="h-5 w-5" />
              Agency Data Enrichment
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-6 w-6 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Agency Information */}
          <div className="text-center">
            <h3 className="font-medium text-lg">
              {agencyName || `Agency ${agencyCode}`}
            </h3>
            <p className="text-sm text-muted-foreground">
              Job ID: {jobId}
            </p>
          </div>

          {/* Status Card */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  {getStatusIcon(status)}
                  <span className="font-medium">
                    {getStatusText(status)}
                  </span>
                </div>
                <Badge className={getStatusColor(status)}>
                  {status.toUpperCase()}
                </Badge>
              </div>

              {/* Progress Bar */}
              {(status === 'running' || status === 'completed') && (
                <div className="space-y-2">
                  <Progress value={progress} className="h-2" />
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>{progress}% Complete</span>
                    <span>
                      {status === 'completed' ? 'Finished' : `${Math.round((100 - progress) / 10)} min remaining`}
                    </span>
                  </div>
                </div>
              )}

              {/* Progress Message */}
              <p className="text-sm text-muted-foreground mt-4">
                {getProgressMessage()}
              </p>

              {/* Error Display */}
              {error && status === 'failed' && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-red-800">
                        Enrichment Error
                      </p>
                      <p className="text-sm text-red-600 mt-1">
                        {error}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Data Types Being Processed */}
          <div>
            <h4 className="text-sm font-medium mb-3">Data Types Being Enriched</h4>
            <div className="grid grid-cols-2 gap-2">
              {dataTypes.map((dataType) => (
                <div
                  key={dataType}
                  className="flex items-center gap-2 p-2 bg-gray-50 rounded-md"
                >
                  {getDataTypeIcon(dataType)}
                  <span className="text-sm">{formatDataType(dataType)}</span>
                  {status === 'completed' && (
                    <CheckCircle className="h-3 w-3 text-green-500 ml-auto" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-4 border-t">
            {status === 'running' && (
              <Button variant="outline" size="sm" disabled>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Processing...
              </Button>
            )}
            {status === 'completed' && (
              <Button onClick={onClose} size="sm">
                <CheckCircle className="h-4 w-4 mr-2" />
                View Results
              </Button>
            )}
            {status === 'failed' && (
              <Button variant="outline" onClick={onClose} size="sm">
                Close
              </Button>
            )}
            {status === 'queued' && (
              <Button variant="outline" onClick={onClose} size="sm">
                Continue in Background
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default EnrichmentProgressModal;