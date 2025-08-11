import { useState, useEffect } from 'react'
import { 
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  ShieldExclamationIcon,
  LightBulbIcon,
  ChevronRightIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'

interface CriticalAlert {
  id: string
  type: 'budget_shift' | 'policy_change' | 'competitive_threat' | 'market_opportunity'
  title: string
  message: string
  urgency: 'high' | 'medium' | 'low'
  actionRequired: boolean
  timestamp: Date
}

const mockAlerts: CriticalAlert[] = [
  {
    id: '1',
    type: 'budget_shift',
    title: 'DOD Budget Increase',
    message: 'DOD increased cybersecurity budget by $200M - 3 opportunities in your pipeline',
    urgency: 'high',
    actionRequired: true,
    timestamp: new Date(Date.now() - 1000 * 60 * 15) // 15 minutes ago
  },
  {
    id: '2',
    type: 'policy_change',
    title: 'Zero Trust Mandate',
    message: 'New Zero Trust mandate affects 85% of your target agencies',
    urgency: 'high',
    actionRequired: true,
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2) // 2 hours ago
  },
  {
    id: '3',
    type: 'competitive_threat',
    title: 'Competitor Movement',
    message: 'CyberSecure Corp hired key DISA program manager - ENCORE III impact',
    urgency: 'medium',
    actionRequired: true,
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 6) // 6 hours ago
  },
  {
    id: '4',
    type: 'market_opportunity',
    title: 'AI/ML Requirements Surge',
    message: 'AI/ML requirements up 156% - your certification provides advantage',
    urgency: 'medium',
    actionRequired: false,
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 12) // 12 hours ago
  }
]

const alertConfig = {
  budget_shift: {
    icon: ArrowTrendingUpIcon,
    bgColor: 'bg-opportunity/20',
    borderColor: 'border-l-opportunity',
    textColor: 'text-opportunity',
    iconBg: 'bg-opportunity/20'
  },
  policy_change: {
    icon: ExclamationTriangleIcon,
    bgColor: 'bg-warning/20',
    borderColor: 'border-l-warning',
    textColor: 'text-warning',
    iconBg: 'bg-warning/20'
  },
  competitive_threat: {
    icon: ShieldExclamationIcon,
    bgColor: 'bg-critical-alert/20',
    borderColor: 'border-l-critical-alert',
    textColor: 'text-critical-alert',
    iconBg: 'bg-critical-alert/20'
  },
  market_opportunity: {
    icon: LightBulbIcon,
    bgColor: 'bg-jarvis-500/20',
    borderColor: 'border-l-jarvis-500',
    textColor: 'text-jarvis-400',
    iconBg: 'bg-jarvis-500/20'
  }
}

export default function CriticalIntelligenceBar() {
  const [currentAlertIndex, setCurrentAlertIndex] = useState(0)
  const [dismissedAlerts, setDismissedAlerts] = useState<string[]>([])
  const [isExpanded, setIsExpanded] = useState(false)

  const activeAlerts = mockAlerts.filter(alert => !dismissedAlerts.includes(alert.id))

  useEffect(() => {
    // Auto-rotate through alerts every 8 seconds
    if (activeAlerts.length > 1) {
      const interval = setInterval(() => {
        setCurrentAlertIndex((prev) => (prev + 1) % activeAlerts.length)
      }, 8000)
      
      return () => clearInterval(interval)
    }
  }, [activeAlerts.length])

  const handleDismissAlert = (alertId: string) => {
    setDismissedAlerts(prev => [...prev, alertId])
    if (currentAlertIndex >= activeAlerts.length - 1) {
      setCurrentAlertIndex(0)
    }
  }

  const formatTimeAgo = (timestamp: Date) => {
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - timestamp.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 60) {
      return `${diffInMinutes}m ago`
    } else if (diffInMinutes < 1440) {
      return `${Math.floor(diffInMinutes / 60)}h ago`
    } else {
      return `${Math.floor(diffInMinutes / 1440)}d ago`
    }
  }

  if (activeAlerts.length === 0) {
    return (
      <div className="jarvis-panel p-4">
        <div className="flex items-center justify-center text-stark-400">
          <LightBulbIcon className="w-5 h-5 mr-2" />
          <span>All critical intelligence reviewed</span>
        </div>
      </div>
    )
  }

  const currentAlert = activeAlerts[currentAlertIndex]
  const config = alertConfig[currentAlert.type]
  const Icon = config.icon

  return (
    <div className="space-y-4">
      {/* Main Critical Alert Display */}
      <div className={`
        ${config.bgColor} ${config.borderColor} border-l-4 p-4 rounded-lg
        transition-all duration-500 ease-in-out
      `}>
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1">
            {/* Alert Icon */}
            <div className={`${config.iconBg} p-2 rounded-lg`}>
              <Icon className={`w-5 h-5 ${config.textColor}`} />
            </div>
            
            {/* Alert Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <h3 className={`font-semibold ${config.textColor}`}>
                  {currentAlert.title}
                </h3>
                {currentAlert.urgency === 'high' && (
                  <span className="px-2 py-1 text-xs font-medium bg-critical-alert/20 text-critical-alert rounded-full">
                    HIGH PRIORITY
                  </span>
                )}
                <span className="text-xs text-stark-400">
                  {formatTimeAgo(currentAlert.timestamp)}
                </span>
              </div>
              
              <p className="text-stark-200 text-sm mb-2">
                {currentAlert.message}
              </p>
              
              {currentAlert.actionRequired && (
                <button className="btn-jarvis text-xs px-3 py-1">
                  Review Action Items
                  <ChevronRightIcon className="w-3 h-3 ml-1 inline" />
                </button>
              )}
            </div>
          </div>
          
          {/* Alert Controls */}
          <div className="flex items-center space-x-2 ml-4">
            {/* Alert Counter */}
            {activeAlerts.length > 1 && (
              <div className="flex items-center space-x-1">
                {activeAlerts.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentAlertIndex(index)}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      index === currentAlertIndex ? config.textColor.replace('text-', 'bg-') : 'bg-stark-600'
                    }`}
                  />
                ))}
              </div>
            )}
            
            {/* Expand/Collapse Button */}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 text-stark-400 hover:text-stark-200 rounded"
            >
              <ChevronRightIcon className={`w-4 h-4 transform transition-transform ${
                isExpanded ? 'rotate-90' : ''
              }`} />
            </button>
            
            {/* Dismiss Button */}
            <button
              onClick={() => handleDismissAlert(currentAlert.id)}
              className="p-1 text-stark-400 hover:text-stark-200 rounded"
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Expanded Alert List */}
      {isExpanded && (
        <div className="jarvis-panel p-4 space-y-3">
          <h4 className="font-semibold text-stark-200 text-sm">All Critical Intelligence</h4>
          <div className="space-y-2">
            {activeAlerts.map((alert, index) => {
              const config = alertConfig[alert.type]
              const AlertIcon = config.icon
              
              return (
                <div
                  key={alert.id}
                  className={`
                    p-3 rounded-lg cursor-pointer transition-all duration-200
                    ${index === currentAlertIndex 
                      ? `${config.bgColor} border border-opacity-50 ${config.textColor.replace('text-', 'border-')}` 
                      : 'bg-stark-800/50 hover:bg-stark-700/50'
                    }
                  `}
                  onClick={() => setCurrentAlertIndex(index)}
                >
                  <div className="flex items-center space-x-3">
                    <AlertIcon className={`w-4 h-4 ${
                      index === currentAlertIndex ? config.textColor : 'text-stark-400'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h5 className={`font-medium text-sm ${
                          index === currentAlertIndex ? config.textColor : 'text-stark-200'
                        }`}>
                          {alert.title}
                        </h5>
                        <span className="text-xs text-stark-400">
                          {formatTimeAgo(alert.timestamp)}
                        </span>
                      </div>
                      <p className="text-xs text-stark-400 truncate">
                        {alert.message}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDismissAlert(alert.id)
                      }}
                      className="p-1 text-stark-500 hover:text-stark-300 rounded"
                    >
                      <XMarkIcon className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}