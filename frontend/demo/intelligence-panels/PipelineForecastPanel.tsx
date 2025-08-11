import { useState } from 'react'
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  CalendarDaysIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  UserGroupIcon,
  BuildingOffice2Icon
} from '@heroicons/react/24/outline'

interface PipelineOpportunity {
  id: string
  title: string
  agency: string
  value: number
  probability: number
  stage: 'identified' | 'qualified' | 'proposal' | 'negotiation'
  expectedAward: Date
  riskFactors: string[]
  keyRequirements: string[]
}

interface ForecastData {
  period: string
  highProbability: number
  mediumProbability: number
  lowProbability: number
  total: number
}

interface ResourceRequirement {
  role: string
  currentCapacity: number
  projectedNeed: number
  gap: number
  priority: 'high' | 'medium' | 'low'
}

const mockPipeline: PipelineOpportunity[] = [
  {
    id: '1',
    title: 'DOD Zero Trust Implementation IDIQ',
    agency: 'Department of Defense - DISA',
    value: 15000000,
    probability: 0.75,
    stage: 'proposal',
    expectedAward: new Date('2024-03-15'),
    riskFactors: ['CyberSecure Corp new hire advantage', 'Large team requirements'],
    keyRequirements: ['Zero Trust Architecture', 'Cloud Security', 'DOD Secret Clearance']
  },
  {
    id: '2',
    title: 'Grid Modernization Security Assessment',
    agency: 'Department of Energy',
    value: 3200000,
    probability: 0.85,
    stage: 'negotiation',
    expectedAward: new Date('2024-02-28'),
    riskFactors: ['Budget approval timing'],
    keyRequirements: ['NERC CIP Expertise', 'OT Security', 'Grid Modernization']
  },
  {
    id: '3',
    title: 'Critical Infrastructure Assessment',
    agency: 'DHS - CISA',
    value: 4500000,
    probability: 0.65,
    stage: 'qualified',
    expectedAward: new Date('2024-04-30'),
    riskFactors: ['Multiple strong competitors', 'Technical complexity'],
    keyRequirements: ['Critical Infrastructure', 'Risk Assessment', 'DHS Experience']
  },
  {
    id: '4',
    title: 'Financial Systems Cybersecurity',
    agency: 'Department of Treasury',
    value: 2100000,
    probability: 0.45,
    stage: 'identified',
    expectedAward: new Date('2024-06-15'),
    riskFactors: ['Limited Treasury experience', 'Compliance requirements'],
    keyRequirements: ['Financial Systems', 'FedRAMP', 'Compliance']
  },
  {
    id: '5',
    title: 'AI Security Framework Implementation',
    agency: 'Department of Defense - CIO',
    value: 8900000,
    probability: 0.70,
    stage: 'proposal',
    expectedAward: new Date('2024-05-01'),
    riskFactors: ['AI expertise requirements', 'Prototype demonstration needed'],
    keyRequirements: ['AI/ML Security', 'Machine Learning', 'DOD Standards']
  }
]

const mockForecastData: ForecastData[] = [
  {
    period: 'Next 90 Days',
    highProbability: 5300000,
    mediumProbability: 2100000,
    lowProbability: 0,
    total: 7400000
  },
  {
    period: 'Next 6 Months',
    highProbability: 8500000,
    mediumProbability: 8900000,
    lowProbability: 2100000,
    total: 19500000
  },
  {
    period: 'Next 12 Months',
    highProbability: 8500000,
    mediumProbability: 17400000,
    lowProbability: 8200000,
    total: 34100000
  }
]

const mockResourceRequirements: ResourceRequirement[] = [
  {
    role: 'Senior Cybersecurity Engineers',
    currentCapacity: 8,
    projectedNeed: 12,
    gap: 4,
    priority: 'high'
  },
  {
    role: 'AI/ML Security Specialists',
    currentCapacity: 2,
    projectedNeed: 5,
    gap: 3,
    priority: 'high'
  },
  {
    role: 'Project Managers (Cleared)',
    currentCapacity: 3,
    projectedNeed: 5,
    gap: 2,
    priority: 'medium'
  },
  {
    role: 'Compliance Specialists',
    currentCapacity: 2,
    projectedNeed: 4,
    gap: 2,
    priority: 'medium'
  }
]

const stageConfig = {
  identified: {
    color: 'text-stark-400',
    bgColor: 'bg-stark-600/20',
    label: 'Identified'
  },
  qualified: {
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-400/20',
    label: 'Qualified'
  },
  proposal: {
    color: 'text-jarvis-400',
    bgColor: 'bg-jarvis-500/20',
    label: 'Proposal'
  },
  negotiation: {
    color: 'text-green-400',
    bgColor: 'bg-green-400/20',
    label: 'Negotiation'
  }
}

export default function PipelineForecastPanel() {
  const [activeTab, setActiveTab] = useState<'forecast' | 'opportunities' | 'resources'>('forecast')
  const [selectedOpportunity, setSelectedOpportunity] = useState<string | null>(null)

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`
    } else {
      return `$${(amount / 1000).toFixed(0)}K`
    }
  }

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    })
  }

  const calculateWeightedValue = (opportunity: PipelineOpportunity) => {
    return opportunity.value * opportunity.probability
  }

  const totalPipelineValue = mockPipeline.reduce((sum, opp) => sum + opp.value, 0)
  const totalWeightedValue = mockPipeline.reduce((sum, opp) => sum + calculateWeightedValue(opp), 0)
  const avgProbability = mockPipeline.reduce((sum, opp) => sum + opp.probability, 0) / mockPipeline.length

  return (
    <div className="intelligence-card h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-stark-100">Pipeline Intelligence</h2>
          <p className="text-sm text-stark-400">Revenue forecasting and resource planning</p>
        </div>
        <div className="flex items-center space-x-2">
          <ChartBarIcon className="w-5 h-5 text-jarvis-400" />
          <span className="text-xs text-jarvis-400">AI Forecasting</span>
        </div>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="jarvis-panel p-3">
          <div className="text-center">
            <div className="text-lg font-bold text-stark-300">
              {formatCurrency(totalPipelineValue)}
            </div>
            <div className="text-xs text-stark-400">Total Pipeline</div>
          </div>
        </div>
        <div className="jarvis-panel p-3">
          <div className="text-center">
            <div className="text-lg font-bold text-green-400">
              {formatCurrency(totalWeightedValue)}
            </div>
            <div className="text-xs text-stark-400">Weighted Value</div>
          </div>
        </div>
        <div className="jarvis-panel p-3">
          <div className="text-center">
            <div className="text-lg font-bold text-jarvis-400">
              {Math.round(avgProbability * 100)}%
            </div>
            <div className="text-xs text-stark-400">Avg Probability</div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 mb-4 bg-stark-800/50 rounded-lg p-1">
        <button
          onClick={() => setActiveTab('forecast')}
          className={`
            flex-1 px-2 py-1.5 text-xs font-medium rounded-md transition-all duration-200
            ${activeTab === 'forecast'
              ? 'bg-jarvis-500/20 text-jarvis-400'
              : 'text-stark-400 hover:text-stark-200'
            }
          `}
        >
          Forecast
        </button>
        <button
          onClick={() => setActiveTab('opportunities')}
          className={`
            flex-1 px-2 py-1.5 text-xs font-medium rounded-md transition-all duration-200
            ${activeTab === 'opportunities'
              ? 'bg-jarvis-500/20 text-jarvis-400'
              : 'text-stark-400 hover:text-stark-200'
            }
          `}
        >
          Opportunities
        </button>
        <button
          onClick={() => setActiveTab('resources')}
          className={`
            flex-1 px-2 py-1.5 text-xs font-medium rounded-md transition-all duration-200
            ${activeTab === 'resources'
              ? 'bg-jarvis-500/20 text-jarvis-400'
              : 'text-stark-400 hover:text-stark-200'
            }
          `}
        >
          Resources
        </button>
      </div>

      {/* Content */}
      <div className="space-y-3 max-h-64 overflow-y-auto">
        {activeTab === 'forecast' && (
          <>
            {mockForecastData.map((forecast, index) => (
              <div key={index} className="bg-stark-800/30 rounded-lg p-3">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-stark-100 text-sm">{forecast.period}</h4>
                  <div className="text-lg font-bold text-green-400">
                    {formatCurrency(forecast.total)}
                  </div>
                </div>
                
                {/* Probability Breakdown */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                      <span className="text-stark-300">High Probability (&gt;70%)</span>
                    </div>
                    <span className="text-green-400 font-medium">
                      {formatCurrency(forecast.highProbability)}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                      <span className="text-stark-300">Medium Probability (40-70%)</span>
                    </div>
                    <span className="text-yellow-400 font-medium">
                      {formatCurrency(forecast.mediumProbability)}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                      <span className="text-stark-300">Low Probability (&lt;40%)</span>
                    </div>
                    <span className="text-red-400 font-medium">
                      {formatCurrency(forecast.lowProbability)}
                    </span>
                  </div>
                </div>

                {/* Probability Bar */}
                <div className="mt-3 bg-stark-700/50 rounded-full h-2 overflow-hidden">
                  <div className="flex h-full">
                    <div 
                      className="bg-green-400"
                      style={{ width: `${(forecast.highProbability / forecast.total) * 100}%` }}
                    ></div>
                    <div 
                      className="bg-yellow-400"
                      style={{ width: `${(forecast.mediumProbability / forecast.total) * 100}%` }}
                    ></div>
                    <div 
                      className="bg-red-400"
                      style={{ width: `${(forecast.lowProbability / forecast.total) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </>
        )}

        {activeTab === 'opportunities' && (
          <>
            {mockPipeline.map((opportunity) => {
              const config = stageConfig[opportunity.stage]
              const isSelected = selectedOpportunity === opportunity.id
              const weightedValue = calculateWeightedValue(opportunity)

              return (
                <div
                  key={opportunity.id}
                  className={`
                    bg-stark-800/30 border rounded-lg cursor-pointer transition-all duration-200
                    ${isSelected 
                      ? 'border-jarvis-500/50 bg-jarvis-500/10' 
                      : 'border-stark-700/50 hover:border-stark-600/50'
                    }
                  `}
                  onClick={() => setSelectedOpportunity(isSelected ? null : opportunity.id)}
                >
                  <div className="p-3">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-stark-100 text-sm truncate">
                          {opportunity.title}
                        </h4>
                        <p className="text-xs text-stark-400 flex items-center space-x-1">
                          <BuildingOffice2Icon className="w-3 h-3" />
                          <span>{opportunity.agency}</span>
                        </p>
                      </div>
                      <div className={`
                        px-2 py-1 rounded-full text-xs font-medium
                        ${config.bgColor} ${config.color}
                      `}>
                        {config.label}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between text-xs">
                      <div className="space-y-1">
                        <div className="text-stark-300">
                          Value: {formatCurrency(opportunity.value)}
                        </div>
                        <div className="text-stark-300">
                          Weighted: {formatCurrency(weightedValue)}
                        </div>
                      </div>
                      <div className="text-right space-y-1">
                        <div className={`
                          font-medium
                          ${opportunity.probability > 0.7 
                            ? 'text-green-400' 
                            : opportunity.probability > 0.4 
                            ? 'text-yellow-400' 
                            : 'text-red-400'
                          }
                        `}>
                          {Math.round(opportunity.probability * 100)}% probability
                        </div>
                        <div className="text-stark-400 flex items-center space-x-1">
                          <CalendarDaysIcon className="w-3 h-3" />
                          <span>{formatDate(opportunity.expectedAward)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Risk Factors (when expanded) */}
                    {isSelected && opportunity.riskFactors.length > 0 && (
                      <div className="mt-3 pt-2 border-t border-stark-700/50">
                        <h5 className="text-xs font-medium text-red-400 mb-1 flex items-center space-x-1">
                          <ExclamationTriangleIcon className="w-3 h-3" />
                          <span>Risk Factors</span>
                        </h5>
                        <div className="space-y-1">
                          {opportunity.riskFactors.map((risk, index) => (
                            <div key={index} className="text-xs text-stark-300 pl-4">
                              • {risk}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </>
        )}

        {activeTab === 'resources' && (
          <>
            {mockResourceRequirements.map((resource, index) => (
              <div key={index} className="bg-stark-800/30 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-stark-100 text-sm">{resource.role}</h4>
                  <span className={`
                    px-2 py-1 text-xs font-medium rounded-full
                    ${resource.priority === 'high' 
                      ? 'bg-red-400/20 text-red-400'
                      : resource.priority === 'medium'
                      ? 'bg-yellow-400/20 text-yellow-400'
                      : 'bg-green-400/20 text-green-400'
                    }
                  `}>
                    {resource.priority.toUpperCase()} PRIORITY
                  </span>
                </div>
                
                <div className="grid grid-cols-3 gap-3 text-xs">
                  <div className="text-center">
                    <div className="font-medium text-stark-300">{resource.currentCapacity}</div>
                    <div className="text-stark-400">Current</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-jarvis-400">{resource.projectedNeed}</div>
                    <div className="text-stark-400">Projected</div>
                  </div>
                  <div className="text-center">
                    <div className={`
                      font-medium
                      ${resource.gap > 0 ? 'text-red-400' : 'text-green-400'}
                    `}>
                      {resource.gap > 0 ? `+${resource.gap}` : resource.gap}
                    </div>
                    <div className="text-stark-400">Gap</div>
                  </div>
                </div>

                {/* Capacity Bar */}
                <div className="mt-2 bg-stark-700/50 rounded-full h-2 overflow-hidden">
                  <div className="flex h-full">
                    <div 
                      className="bg-green-400"
                      style={{ width: `${(resource.currentCapacity / resource.projectedNeed) * 100}%` }}
                    ></div>
                    <div 
                      className="bg-red-400/50"
                      style={{ width: `${((resource.projectedNeed - resource.currentCapacity) / resource.projectedNeed) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mt-4 pt-4 border-t border-stark-700/50">
        <div className="flex items-center space-x-2">
          <button className="btn-jarvis text-xs px-3 py-1.5">
            Generate Forecast Report
          </button>
          <button className="btn-ghost text-xs px-3 py-1.5">
            Update Pipeline
          </button>
        </div>
      </div>
    </div>
  )
}