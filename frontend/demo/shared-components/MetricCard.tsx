import { ReactNode } from 'react'
import { 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon,
  MinusIcon
} from '@heroicons/react/24/outline'

interface MetricCardProps {
  title: string
  value: string | number
  change?: {
    value: number
    type: 'percentage' | 'absolute'
    period?: string
  }
  trend?: 'up' | 'down' | 'stable'
  icon?: ReactNode
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'jarvis'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  className?: string
  onClick?: () => void
}

const variantConfig = {
  default: {
    bg: 'bg-stark-800/50',
    border: 'border-stark-700/50',
    text: 'text-stark-100',
    subtext: 'text-stark-400',
    accent: 'text-jarvis-400'
  },
  success: {
    bg: 'bg-green-900/20',
    border: 'border-green-500/30',
    text: 'text-green-400',
    subtext: 'text-green-300/60',
    accent: 'text-green-400'
  },
  warning: {
    bg: 'bg-amber-900/20',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
    subtext: 'text-amber-300/60',
    accent: 'text-amber-400'
  },
  danger: {
    bg: 'bg-red-900/20',
    border: 'border-red-500/30',
    text: 'text-red-400',
    subtext: 'text-red-300/60',
    accent: 'text-red-400'
  },
  jarvis: {
    bg: 'bg-jarvis-900/20',
    border: 'border-jarvis-500/30',
    text: 'text-jarvis-400',
    subtext: 'text-jarvis-300/60',
    accent: 'text-jarvis-400'
  }
}

const sizeConfig = {
  sm: {
    padding: 'p-3',
    titleSize: 'text-xs',
    valueSize: 'text-lg',
    iconSize: 'w-4 h-4',
    changeSize: 'text-xs'
  },
  md: {
    padding: 'p-4',
    titleSize: 'text-sm',
    valueSize: 'text-2xl',
    iconSize: 'w-5 h-5',
    changeSize: 'text-sm'
  },
  lg: {
    padding: 'p-6',
    titleSize: 'text-base',
    valueSize: 'text-3xl',
    iconSize: 'w-6 h-6',
    changeSize: 'text-base'
  }
}

const formatValue = (value: string | number): string => {
  if (typeof value === 'number') {
    if (Math.abs(value) >= 1000000000) {
      return `${(value / 1000000000).toFixed(1)}B`
    } else if (Math.abs(value) >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`
    } else if (Math.abs(value) >= 1000) {
      return `${(value / 1000).toFixed(0)}K`
    }
    return value.toLocaleString()
  }
  return value
}

const formatChange = (change: MetricCardProps['change']): string => {
  if (!change) return ''
  
  const { value, type } = change
  const prefix = value > 0 ? '+' : ''
  
  if (type === 'percentage') {
    return `${prefix}${value.toFixed(1)}%`
  }
  return `${prefix}${formatValue(value)}`
}

const getTrendIcon = (trend?: 'up' | 'down' | 'stable', change?: MetricCardProps['change']) => {
  let trendDirection = trend
  
  // Auto-detect trend from change if not explicitly provided
  if (!trendDirection && change) {
    if (change.value > 0) trendDirection = 'up'
    else if (change.value < 0) trendDirection = 'down'
    else trendDirection = 'stable'
  }
  
  switch (trendDirection) {
    case 'up':
      return <ArrowTrendingUpIcon className="w-3 h-3" />
    case 'down':
      return <ArrowTrendingDownIcon className="w-3 h-3" />
    case 'stable':
      return <MinusIcon className="w-3 h-3" />
    default:
      return null
  }
}

const getTrendColor = (trend?: 'up' | 'down' | 'stable', change?: MetricCardProps['change']) => {
  let trendDirection = trend
  
  // Auto-detect trend from change if not explicitly provided
  if (!trendDirection && change) {
    if (change.value > 0) trendDirection = 'up'
    else if (change.value < 0) trendDirection = 'down'
    else trendDirection = 'stable'
  }
  
  switch (trendDirection) {
    case 'up':
      return 'text-green-400'
    case 'down':
      return 'text-red-400'
    case 'stable':
      return 'text-stark-400'
    default:
      return 'text-stark-400'
  }
}

export default function MetricCard({
  title,
  value,
  change,
  trend,
  icon,
  variant = 'default',
  size = 'md',
  loading = false,
  className = '',
  onClick
}: MetricCardProps) {
  const config = variantConfig[variant]
  const sizeConf = sizeConfig[size]
  
  const cardClasses = `
    ${config.bg} ${config.border} border rounded-lg transition-all duration-200
    ${onClick ? 'cursor-pointer hover:shadow-lg hover:border-jarvis-500/50' : ''}
    ${className}
  `
  
  if (loading) {
    return (
      <div className={cardClasses}>
        <div className={sizeConf.padding}>
          <div className="animate-pulse space-y-2">
            <div className="h-4 bg-stark-700 rounded w-3/4"></div>
            <div className="h-8 bg-stark-700 rounded w-1/2"></div>
            <div className="h-3 bg-stark-700 rounded w-1/3"></div>
          </div>
        </div>
      </div>
    )
  }
  
  return (
    <div className={cardClasses} onClick={onClick}>
      <div className={sizeConf.padding}>
        {/* Header with title and icon */}
        <div className="flex items-center justify-between mb-2">
          <h3 className={`font-medium ${config.subtext} ${sizeConf.titleSize}`}>
            {title}
          </h3>
          {icon && (
            <div className={`${config.accent} ${sizeConf.iconSize}`}>
              {icon}
            </div>
          )}
        </div>
        
        {/* Main value */}
        <div className={`font-bold ${config.text} ${sizeConf.valueSize} mb-1`}>
          {formatValue(value)}
        </div>
        
        {/* Change indicator */}
        {change && (
          <div className={`flex items-center space-x-1 ${sizeConf.changeSize}`}>
            <span className={getTrendColor(trend, change)}>
              {getTrendIcon(trend, change)}
            </span>
            <span className={getTrendColor(trend, change)}>
              {formatChange(change)}
            </span>
            {change.period && (
              <span className={config.subtext}>
                {change.period}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}