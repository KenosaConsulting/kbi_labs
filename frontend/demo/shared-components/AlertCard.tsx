import { ReactNode, useState } from 'react'
import {
  XMarkIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  BoltIcon
} from '@heroicons/react/24/outline'

interface AlertCardProps {
  type?: 'info' | 'success' | 'warning' | 'error' | 'jarvis'
  title: string
  message: string | ReactNode
  actions?: {
    label: string
    onClick: () => void
    variant?: 'primary' | 'secondary'
  }[]
  dismissible?: boolean
  onDismiss?: () => void
  className?: string
}

const alertConfig = {
  info: {
    bg: 'bg-blue-950/50',
    border: 'border-blue-500/30',
    icon: InformationCircleIcon,
    iconColor: 'text-blue-400',
    titleColor: 'text-blue-300',
    messageColor: 'text-blue-100'
  },
  success: {
    bg: 'bg-green-950/50',
    border: 'border-green-500/30',
    icon: CheckCircleIcon,
    iconColor: 'text-green-400',
    titleColor: 'text-green-300',
    messageColor: 'text-green-100'
  },
  warning: {
    bg: 'bg-amber-950/50',
    border: 'border-amber-500/30',
    icon: ExclamationTriangleIcon,
    iconColor: 'text-amber-400',
    titleColor: 'text-amber-300',
    messageColor: 'text-amber-100'
  },
  error: {
    bg: 'bg-red-950/50',
    border: 'border-red-500/30',
    icon: XCircleIcon,
    iconColor: 'text-red-400',
    titleColor: 'text-red-300',
    messageColor: 'text-red-100'
  },
  jarvis: {
    bg: 'bg-jarvis-950/50',
    border: 'border-jarvis-500/30',
    icon: BoltIcon,
    iconColor: 'text-jarvis-400',
    titleColor: 'text-jarvis-300',
    messageColor: 'text-jarvis-100'
  }
}

export default function AlertCard({
  type = 'info',
  title,
  message,
  actions,
  dismissible = false,
  onDismiss,
  className = ''
}: AlertCardProps) {
  const [dismissed, setDismissed] = useState(false)
  const config = alertConfig[type]
  const Icon = config.icon

  const handleDismiss = () => {
    setDismissed(true)
    onDismiss?.()
  }

  if (dismissed) {
    return null
  }

  return (
    <div
      className={`
        ${config.bg} ${config.border} border rounded-lg p-4
        transition-all duration-300 ease-in-out
        ${className}
      `}
    >
      <div className="flex items-start space-x-3">
        {/* Icon */}
        <div className="flex-shrink-0">
          <Icon className={`w-6 h-6 ${config.iconColor}`} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className={`font-semibold text-sm ${config.titleColor} mb-1`}>
                {title}
              </h3>
              <div className={`text-sm ${config.messageColor}`}>
                {typeof message === 'string' ? (
                  <p>{message}</p>
                ) : (
                  message
                )}
              </div>
            </div>

            {/* Dismiss button */}
            {dismissible && (
              <button
                onClick={handleDismiss}
                className={`
                  flex-shrink-0 ml-4 p-1 rounded-md transition-colors duration-200
                  hover:bg-white/10 ${config.iconColor}
                `}
              >
                <XMarkIcon className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Actions */}
          {actions && actions.length > 0 && (
            <div className="flex items-center space-x-3 mt-4">
              {actions.map((action, index) => (
                <button
                  key={index}
                  onClick={action.onClick}
                  className={`
                    px-3 py-1.5 rounded-md text-xs font-medium transition-colors duration-200
                    ${action.variant === 'primary'
                      ? `${config.iconColor} bg-white/10 hover:bg-white/20`
                      : 'text-stark-300 hover:text-stark-100 hover:bg-white/5'
                    }
                  `}
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Specialized alert components
export function CriticalAlert({
  title,
  message,
  actions,
  onDismiss
}: Omit<AlertCardProps, 'type'>) {
  return (
    <AlertCard
      type="error"
      title={title}
      message={message}
      actions={actions}
      dismissible
      onDismiss={onDismiss}
      className="animate-pulse"
    />
  )
}

export function JarvisAlert({
  title,
  message,
  actions,
  dismissible = true,
  onDismiss
}: Omit<AlertCardProps, 'type'>) {
  return (
    <AlertCard
      type="jarvis"
      title={title}
      message={message}
      actions={actions}
      dismissible={dismissible}
      onDismiss={onDismiss}
    />
  )
}

export function SuccessAlert({
  title,
  message,
  actions,
  onDismiss
}: Omit<AlertCardProps, 'type'>) {
  return (
    <AlertCard
      type="success"
      title={title}
      message={message}
      actions={actions}
      dismissible
      onDismiss={onDismiss}
    />
  )
}