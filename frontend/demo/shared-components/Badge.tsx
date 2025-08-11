import { ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'jarvis' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  icon?: ReactNode
  pulse?: boolean
  className?: string
}

const variantConfig = {
  default: {
    bg: 'bg-stark-700',
    text: 'text-stark-200',
    border: 'border-stark-600'
  },
  success: {
    bg: 'bg-green-500/20',
    text: 'text-green-400',
    border: 'border-green-500/30'
  },
  warning: {
    bg: 'bg-amber-500/20',
    text: 'text-amber-400',
    border: 'border-amber-500/30'
  },
  danger: {
    bg: 'bg-red-500/20',
    text: 'text-red-400',
    border: 'border-red-500/30'
  },
  info: {
    bg: 'bg-blue-500/20',
    text: 'text-blue-400',
    border: 'border-blue-500/30'
  },
  jarvis: {
    bg: 'bg-jarvis-500/20',
    text: 'text-jarvis-400',
    border: 'border-jarvis-500/30'
  },
  outline: {
    bg: 'bg-transparent',
    text: 'text-stark-300',
    border: 'border-stark-600'
  }
}

const sizeConfig = {
  sm: {
    text: 'text-xs',
    padding: 'px-2 py-0.5',
    icon: 'w-3 h-3'
  },
  md: {
    text: 'text-sm',
    padding: 'px-2.5 py-1',
    icon: 'w-4 h-4'
  },
  lg: {
    text: 'text-base',
    padding: 'px-3 py-1.5',
    icon: 'w-5 h-5'
  }
}

export default function Badge({
  children,
  variant = 'default',
  size = 'md',
  icon,
  pulse = false,
  className = ''
}: BadgeProps) {
  const config = variantConfig[variant]
  const sizeConf = sizeConfig[size]
  
  const badgeClasses = `
    inline-flex items-center space-x-1 font-medium rounded-full
    ${config.bg} ${config.text} ${config.border}
    ${variant === 'outline' ? 'border' : ''}
    ${sizeConf.text} ${sizeConf.padding}
    ${pulse ? 'animate-pulse' : ''}
    ${className}
  `
  
  return (
    <span className={badgeClasses}>
      {icon && (
        <span className={sizeConf.icon}>
          {icon}
        </span>
      )}
      <span>{children}</span>
    </span>
  )
}

// Predefined status badges for common use cases
export function StatusBadge({
  status,
  size = 'sm'
}: {
  status: 'active' | 'inactive' | 'pending' | 'completed' | 'failed' | 'critical'
  size?: 'sm' | 'md' | 'lg'
}) {
  const statusConfig = {
    active: { variant: 'success' as const, text: 'Active', pulse: false },
    inactive: { variant: 'default' as const, text: 'Inactive', pulse: false },
    pending: { variant: 'warning' as const, text: 'Pending', pulse: false },
    completed: { variant: 'success' as const, text: 'Completed', pulse: false },
    failed: { variant: 'danger' as const, text: 'Failed', pulse: false },
    critical: { variant: 'danger' as const, text: 'Critical', pulse: true }
  }
  
  const config = statusConfig[status]
  
  return (
    <Badge
      variant={config.variant}
      size={size}
      pulse={config.pulse}
    >
      {config.text}
    </Badge>
  )
}

// Priority badge
export function PriorityBadge({
  priority,
  size = 'sm'
}: {
  priority: 'low' | 'medium' | 'high' | 'critical'
  size?: 'sm' | 'md' | 'lg'
}) {
  const priorityConfig = {
    low: { variant: 'info' as const, text: 'Low', pulse: false },
    medium: { variant: 'warning' as const, text: 'Medium', pulse: false },
    high: { variant: 'danger' as const, text: 'High', pulse: false },
    critical: { variant: 'danger' as const, text: 'Critical', pulse: true }
  }
  
  const config = priorityConfig[priority]
  
  return (
    <Badge
      variant={config.variant}
      size={size}
      pulse={config.pulse}
    >
      {config.text}
    </Badge>
  )
}

// Confidence badge for showing data confidence levels
export function ConfidenceBadge({
  confidence,
  size = 'sm'
}: {
  confidence: number // 0-1
  size?: 'sm' | 'md' | 'lg'
}) {
  const percentage = Math.round(confidence * 100)
  let variant: 'danger' | 'warning' | 'success' = 'danger'
  
  if (percentage >= 80) variant = 'success'
  else if (percentage >= 60) variant = 'warning'
  
  return (
    <Badge variant={variant} size={size}>
      {percentage}% Confidence
    </Badge>
  )
}