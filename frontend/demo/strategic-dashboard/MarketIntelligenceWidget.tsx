import { useState } from 'react'
import { 
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ArrowTopRightOnSquareIcon
} from '@heroicons/react/24/outline'

interface MarketTrend {
  agency: string
  category: string
  currentSpending: number
  projectedSpending: number
  growth: number
  confidence: number
  opportunities: number
}

interface PolicyImpact {
  policy: string
  impact: 'positive' | 'negative' | 'neutral'
  description: string
  businessEffect: string
  timeline: string
}

const mockMarketTrends: MarketTrend[] = [
  {
    agency: 'Department of Energy',
    category: 'Grid Cybersecurity',
    currentSpending: 340000000,
    projectedSpending: 580000000,
    growth: 70.6,
    confidence: 0.94,
    opportunities: 23
  },
  {
    agency: 'Department of Defense',
    category: 'Zero Trust Implementation',
    currentSpending: 1200000000,
    projectedSpending: 1560000000,
    growth: 30.0,
    confidence: 0.89,
    opportunities: 45
  },
  {
    agency: 'DHS/CISA',
    category: 'Critical Infrastructure',
    currentSpending: 890000000,
    projectedSpending: 1100000000,
    growth: 23.6,
    confidence: 0.82,
    opportunities: 31
  },
  {
    agency: 'Treasury',
    category: 'Financial Systems Security',
    currentSpending: 450000000,
    projectedSpending: 520000000,
    growth: 15.6,
    confidence: 0.75,
    opportunities: 12
  }
]

const mockPolicyImpacts: PolicyImpact[] = [
  {
    policy: 'Infrastructure Investment Act',
    impact: 'positive',
    description: '$1.2B allocated for critical infrastructure cybersecurity',
    businessEffect: '+68% addressable market in grid security',
    timeline: '24 months'
  },
  {
    policy: 'Zero Trust Executive Order',
    impact: 'positive', 
    description: 'Mandates Zero Trust architecture across federal agencies',
    businessEffect: '+156% in Zero Trust opportunities',
    timeline: '18 months'
  },
  {
    policy: 'NIST Post-Quantum Standards',
    impact: 'neutral',
    description: 'New cryptographic standards creating transition period',
    businessEffect: 'Early investment opportunity in quantum-resistant security',
    timeline: '36 months'
  }
]

const formatCurrency = (amount: number) => {
  if (amount >= 1000000000) {
    return `$${(amount / 1000000000).toFixed(1)}B`
  } else if (amount >= 1000000) {
    return `$${(amount / 1000000).toFixed(0)}M`
  } else {
    return `$${(amount / 1000).toFixed(0)}K`
  }
}

export default function MarketIntelligenceWidget() {
  const [activeTab, setActiveTab] = useState<'trends' | 'policy'>('trends')

  const totalGrowth = mockMarketTrends.reduce((sum, trend) => 
    sum + (trend.projectedSpending - trend.currentSpending), 0
  )
  
  const avgGrowthRate = mockMarketTrends.reduce((sum, trend) => sum + trend.growth, 0) / mockMarketTrends.length
  const totalOpportunities = mockMarketTrends.reduce((sum, trend) => sum + trend.opportunities, 0)

  return (
    <div className="intelligence-card h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-stark-100">Market Intelligence</h2>
          <p className="text-sm text-stark-400">Government spending trends and policy analysis</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
          <span className="text-xs text-green-400">Real-time</span>
        </div>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="jarvis-panel p-3">
          <div className="flex items-center space-x-2">
            <CurrencyDollarIcon className="w-5 h-5 text-green-400" />
            <span className="text-sm text-stark-400">Market Growth</span>
          </div>
          <div className="mt-1">
            <div className="text-lg font-bold text-green-400">
              {formatCurrency(totalGrowth)}
            </div>
            <div className="text-xs text-stark-400">
              +{avgGrowthRate.toFixed(1)}% avg growth
            </div>
          </div>
        </div>
        
        <div className="jarvis-panel p-3">
          <div className="flex items-center space-x-2">
            <ChartBarIcon className="w-5 h-5 text-jarvis-400" />
            <span className="text-sm text-stark-400">Opportunities</span>
          </div>
          <div className="mt-1">
            <div className="text-lg font-bold text-jarvis-400">
              {totalOpportunities}
            </div>
            <div className="text-xs text-stark-400">
              Active pipeline
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 mb-4 bg-stark-800/50 rounded-lg p-1">
        <button
          onClick={() => setActiveTab('trends')}
          className={`
            flex-1 px-3 py-2 text-sm font-medium rounded-md transition-all duration-200
            ${activeTab === 'trends'
              ? 'bg-jarvis-500/20 text-jarvis-400'
              : 'text-stark-400 hover:text-stark-200'
            }
          `}
        >
          Spending Trends
        </button>
        <button
          onClick={() => setActiveTab('policy')}
          className={`
            flex-1 px-3 py-2 text-sm font-medium rounded-md transition-all duration-200
            ${activeTab === 'policy'
              ? 'bg-jarvis-500/20 text-jarvis-400'
              : 'text-stark-400 hover:text-stark-200'
            }
          `}
        >
          Policy Impact
        </button>
      </div>

      {/* Content */}
      <div className="space-y-3 max-h-64 overflow-y-auto">
        {activeTab === 'trends' && (
          <>
            {mockMarketTrends.map((trend, index) => (
              <div key={index} className="bg-stark-800/30 rounded-lg p-3">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-medium text-stark-100 text-sm">
                      {trend.agency}
                    </h4>
                    <p className="text-xs text-stark-400">{trend.category}</p>
                  </div>
                  <div className={`
                    flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium
                    ${trend.growth > 30 
                      ? 'bg-green-400/20 text-green-400'
                      : trend.growth > 15
                      ? 'bg-yellow-400/20 text-yellow-400'
                      : 'bg-stark-600/20 text-stark-300'
                    }
                  `}>
                    {trend.growth > 0 ? (
                      <ArrowTrendingUpIcon className="w-3 h-3" />
                    ) : (
                      <ArrowTrendingDownIcon className="w-3 h-3" />
                    )}
                    <span>+{trend.growth.toFixed(1)}%</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-xs">
                  <div className="space-y-1">
                    <div className="text-stark-300">
                      Current: {formatCurrency(trend.currentSpending)}
                    </div>
                    <div className="text-stark-300">
                      Projected: {formatCurrency(trend.projectedSpending)}
                    </div>
                  </div>
                  <div className="text-right space-y-1">
                    <div className="text-stark-300">
                      {trend.opportunities} opportunities
                    </div>
                    <div className="text-green-400">
                      {Math.round(trend.confidence * 100)}% confidence
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </>
        )}

        {activeTab === 'policy' && (
          <>
            {mockPolicyImpacts.map((policy, index) => (
              <div key={index} className="bg-stark-800/30 rounded-lg p-3">
                <div className="flex items-start space-x-3">
                  <div className={`
                    p-1.5 rounded-lg flex-shrink-0
                    ${policy.impact === 'positive' 
                      ? 'bg-green-400/20'
                      : policy.impact === 'negative'
                      ? 'bg-red-400/20'
                      : 'bg-yellow-400/20'
                    }
                  `}>
                    {policy.impact === 'positive' ? (
                      <ArrowTrendingUpIcon className="w-4 h-4 text-green-400" />
                    ) : policy.impact === 'negative' ? (
                      <ArrowTrendingDownIcon className="w-4 h-4 text-red-400" />
                    ) : (
                      <InformationCircleIcon className="w-4 h-4 text-yellow-400" />
                    )}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-stark-100 text-sm">
                        {policy.policy}
                      </h4>
                      <span className="text-xs text-stark-400 bg-stark-700/50 px-2 py-1 rounded">
                        {policy.timeline}
                      </span>
                    </div>
                    
                    <p className="text-xs text-stark-300 mb-2">
                      {policy.description}
                    </p>
                    
                    <div className={`
                      text-xs px-2 py-1 rounded inline-block
                      ${policy.impact === 'positive' 
                        ? 'bg-green-400/20 text-green-400'
                        : policy.impact === 'negative'
                        ? 'bg-red-400/20 text-red-400'
                        : 'bg-yellow-400/20 text-yellow-400'
                      }
                    `}>
                      {policy.businessEffect}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </>
        )}
      </div>

      {/* Quick Actions */}
      <div className="mt-4 pt-4 border-t border-stark-700/50">
        <div className="flex items-center justify-between">
          <button className="btn-jarvis text-xs px-3 py-1.5">
            Generate Market Report
          </button>
          <button className="btn-ghost text-xs px-3 py-1.5">
            View Full Analysis
            <ArrowTopRightOnSquareIcon className="w-3 h-3 ml-1 inline" />
          </button>
        </div>
      </div>
    </div>
  )
}