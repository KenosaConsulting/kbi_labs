import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  TrendingUp,
  Users,
  DollarSign,
  FileText,
  Building
} from 'lucide-react';
import { formatDate, formatPercentage } from '../utils/formatters';

const DataQualityIndicator = ({
  dataType,
  qualityScore = 0,
  lastUpdated = null,
  accessCount = 0,
  className = ""
}) => {
  const getDataTypeIcon = (type) => {
    switch (type) {
      case 'budget':
        return <DollarSign className="h-4 w-4" />;
      case 'personnel':
        return <Users className="h-4 w-4" />;
      case 'contracts':
        return <FileText className="h-4 w-4" />;
      case 'organizational':
        return <Building className="h-4 w-4" />;
      case 'strategic':
        return <TrendingUp className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getDataTypeLabel = (type) => {
    const labels = {
      budget: 'Budget Data',
      personnel: 'Personnel',
      contracts: 'Contracts',
      organizational: 'Organization',
      strategic: 'Strategic'
    };
    return labels[type] || type;
  };

  const getQualityBadge = (score) => {
    if (score >= 0.9) {
      return {
        variant: 'default',
        className: 'bg-green-100 text-green-800 border-green-200',
        icon: <CheckCircle className="h-3 w-3" />,
        label: 'Excellent'
      };
    } else if (score >= 0.7) {
      return {
        variant: 'default',
        className: 'bg-blue-100 text-blue-800 border-blue-200',
        icon: <CheckCircle className="h-3 w-3" />,
        label: 'Good'
      };
    } else if (score >= 0.5) {
      return {
        variant: 'default',
        className: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        icon: <AlertTriangle className="h-3 w-3" />,
        label: 'Fair'
      };
    } else if (score > 0) {
      return {
        variant: 'default',
        className: 'bg-orange-100 text-orange-800 border-orange-200',
        icon: <AlertTriangle className="h-3 w-3" />,
        label: 'Poor'
      };
    } else {
      return {
        variant: 'default',
        className: 'bg-red-100 text-red-800 border-red-200',
        icon: <XCircle className="h-3 w-3" />,
        label: 'No Data'
      };
    }
  };

  const getProgressColor = (score) => {
    if (score >= 0.9) return 'bg-green-500';
    if (score >= 0.7) return 'bg-blue-500';
    if (score >= 0.5) return 'bg-yellow-500';
    if (score > 0) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getFreshnessStatus = (lastUpdatedDate) => {
    if (!lastUpdatedDate) {
      return {
        text: 'Never updated',
        className: 'text-red-600',
        icon: <XCircle className="h-3 w-3" />
      };
    }

    const now = new Date();
    const updated = new Date(lastUpdatedDate);
    const diffHours = Math.floor((now - updated) / (1000 * 60 * 60));

    if (diffHours < 1) {
      return {
        text: 'Just updated',
        className: 'text-green-600',
        icon: <CheckCircle className="h-3 w-3" />
      };
    } else if (diffHours < 24) {
      return {
        text: `${diffHours}h ago`,
        className: 'text-green-600',
        icon: <CheckCircle className="h-3 w-3" />
      };
    } else if (diffHours < 168) { // 7 days
      const days = Math.floor(diffHours / 24);
      return {
        text: `${days}d ago`,
        className: 'text-yellow-600',
        icon: <Clock className="h-3 w-3" />
      };
    } else {
      const days = Math.floor(diffHours / 24);
      return {
        text: `${days}d ago`,
        className: 'text-red-600',
        icon: <AlertTriangle className="h-3 w-3" />
      };
    }
  };

  const qualityBadge = getQualityBadge(qualityScore);
  const freshnessStatus = getFreshnessStatus(lastUpdated);
  const progressColor = getProgressColor(qualityScore);

  return (
    <Card className={`hover:shadow-md transition-shadow ${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            {getDataTypeIcon(dataType)}
            <span>{getDataTypeLabel(dataType)}</span>
          </div>
          <Badge className={qualityBadge.className}>
            {qualityBadge.icon}
            <span className="ml-1">{qualityBadge.label}</span>
          </Badge>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Quality Score */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-medium text-muted-foreground">
              Quality Score
            </span>
            <span className="text-sm font-semibold">
              {formatPercentage(qualityScore)}
            </span>
          </div>
          <Progress 
            value={qualityScore * 100} 
            className="h-2"
            indicatorClassName={progressColor}
          />
        </div>

        {/* Data Freshness */}
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground">
            Last Updated
          </span>
          <div className={`flex items-center gap-1 text-xs ${freshnessStatus.className}`}>
            {freshnessStatus.icon}
            <span>{freshnessStatus.text}</span>
          </div>
        </div>

        {/* Access Count */}
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground">
            Access Count
          </span>
          <span className="text-xs font-medium">
            {accessCount.toLocaleString()} times
          </span>
        </div>

        {/* Additional Details */}
        {lastUpdated && (
          <div className="pt-2 border-t border-gray-100">
            <div className="text-xs text-muted-foreground">
              Updated: {formatDate(lastUpdated)}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DataQualityIndicator;