import { useState } from 'react'
import { 
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  ArrowTopRightOnSquareIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ClockIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'

interface StrategicInsight {
  id: string
  category: 'market_opportunity' | 'competitive_intelligence' | 'policy_impact' | 'investment_guidance'
  title: string
  insight: string
  businessImpact: string
  actionRequired: string
  timeframe: string
  confidence: number
  priority: 'high' | 'medium' | 'low'
  tags: string[]
  metrics?: {
    label: string
    value: string
    trend: 'up' | 'down' | 'neutral'
  }[]
  recommendedActions: string[]
}

const mockInsights: StrategicInsight[] = [
  {
    id: '1',
    category: 'market_opportunity',
    title: 'AI/ML Requirements Accelerating in Federal Cybersecurity',
    insight: 'AI/ML requirements appearing in 40% more cybersecurity RFPs compared to last quarter. Government agencies are prioritizing intelligent threat detection and automated response capabilities.',
    businessImpact: 'Your recent AI security certification positions you as early-mover for $12M+ in emerging opportunities over next 18 months.',
    actionRequired: 'Update capability statements to emphasize AI/ML security expertise and target 5 AI-focused opportunities in pipeline.',
    timeframe: 'Act within 30 days for first-mover advantage',
    confidence: 0.87,
    priority: 'high',
    tags: ['AI/ML', 'Cybersecurity', 'DOD', 'DHS'],
    metrics: [
      { label: 'AI Requirements Growth', value: '+156%', trend: 'up' },
      { label: 'Addressable Pipeline', value: '$12.3M', trend: 'up' },
      { label: 'Competition Level', value: 'Low', trend: 'neutral' }
    ],
    recommendedActions: [
      'Highlight AI security certification in all proposal responses',
      'Schedule briefings with DISA and CISA on AI threat detection',
      'Partner with ML platform vendors for enhanced capabilities',
      'Develop AI security case studies from recent projects'
    ]
  },
  {
    id: '2',
    category: 'competitive_intelligence',
    title: 'Market Consolidation Risk in Mid-Tier Contracts',
    insight: '3 competitors in your size range acquired by large primes in Q4. Market showing consolidation pressure in the $1-5M contract space where you compete most actively.',
    businessImpact: 'Increased competition from well-resourced competitors may reduce win rates by 15-20% unless strategic positioning adjusted.',
    actionRequired: 'Consider strategic partnerships, niche specialization, or capability expansion to differentiate from larger competitors.',
    timeframe: 'Strategic planning needed within 60 days',
    confidence: 0.92,
    priority: 'high',
    tags: ['Competition', 'M&A', 'Strategic Planning'],
    metrics: [
      { label: 'Market Consolidation', value: '3 Acquisitions', trend: 'up' },
      { label: 'Win Rate Impact', value: '-15%', trend: 'down' },
      { label: 'Strategic Response Time', value: '60 days', trend: 'neutral' }
    ],
    recommendedActions: [
      'Evaluate potential teaming agreements with complementary SMBs',
      'Develop specialized niche in quantum-resistant cryptography',
      'Expand geographic footprint to reduce regional competition',
      'Consider acquiring smaller firms with unique capabilities'
    ]
  },
  {
    id: '3',
    category: 'policy_impact',
    title: 'Infrastructure Bill Creating Cybersecurity Opportunities',
    insight: 'New infrastructure legislation allocates $1.2B specifically for critical infrastructure cybersecurity over 24 months. Focus on grid modernization and OT security.',
    businessImpact: 'Your NERC CIP expertise addresses 68% of new infrastructure funding. Estimated $340M addressable market in your specialty areas.',
    actionRequired: 'Immediately engage with DOE Office of Cybersecurity and state energy agencies for early positioning.',
    timeframe: '90-day window for optimal positioning',
    confidence: 0.94,
    priority: 'high',
    tags: ['Infrastructure Bill', 'DOE', 'Grid Security', 'NERC CIP'],
    metrics: [
      { label: 'Available Funding', value: '$1.2B', trend: 'up' },
      { label: 'Your Market Share', value: '68%', trend: 'up' },
      { label: 'Competition Timeline', value: '90 days', trend: 'neutral' }
    ],
    recommendedActions: [
      'Schedule meetings with DOE cybersecurity leadership',
      'Update past performance to highlight grid modernization work',
      'Develop partnerships with utility companies',
      'Create thought leadership content on OT security'
    ]
  },
  {
    id: '4',
    category: 'investment_guidance',
    title: 'Quantum Cryptography Specialist Hiring Recommendation',
    insight: 'NIST post-quantum cryptography standards driving federal adoption timeline acceleration. Early quantum expertise becoming competitive differentiator.',
    businessImpact: 'Quantum-resistant security requirements appearing in $50M+ worth of upcoming opportunities. Investment ROI projected at 340% within 24 months.',
    actionRequired: 'Hire senior quantum cryptography specialist within 90 days to capture early opportunities.',
    timeframe: 'Hire within 90 days for optimal ROI',
    confidence: 0.78,
    priority: 'medium',
    tags: ['Quantum', 'NIST', 'Investment', 'Personnel'],
    metrics: [
      { label: 'Investment Required', value: '$165K', trend: 'neutral' },
      { label: 'Projected ROI', value: '340%', trend: 'up' },
      { label: 'Market Readiness', value: '24 months', trend: 'neutral' }
    ],
    recommendedActions: [
      'Post quantum cryptography specialist job opening',
      'Partner with universities for quantum research talent',
      'Begin NIST post-quantum certification process',
      'Develop quantum security service offerings'
    ]
  }
]

const categoryConfig = {
  market_opportunity: {
    icon: ArrowTrendingUpIcon,
    color: 'text-opportunity',
    bgColor: 'bg-opportunity/20',
    borderColor: 'border-opportunity/50'
  },
  competitive_intelligence: {
    icon: ExclamationTriangleIcon,
    color: 'text-critical-alert',
    bgColor: 'bg-critical-alert/20',
    borderColor: 'border-critical-alert/50'
  },
  policy_impact: {
    icon: ChartBarIcon,
    color: 'text-warning',
    bgColor: 'bg-warning/20',
    borderColor: 'border-warning/50'
  },
  investment_guidance: {
    icon: LightBulbIcon,
    color: 'text-jarvis-400',
    bgColor: 'bg-jarvis-500/20',
    borderColor: 'border-jarvis-500/50'
  }
}

export default function StrategicInsightCard() {
  const [expandedInsights, setExpandedInsights] = useState<string[]>(['1']) // First insight expanded by default
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  const toggleInsightExpansion = (insightId: string) => {
    setExpandedInsights(prev => 
      prev.includes(insightId) 
        ? prev.filter(id => id !== insightId)
        : [...prev, insightId]
    )
  }

  const filteredInsights = selectedCategory === 'all' 
    ? mockInsights 
    : mockInsights.filter(insight => insight.category === selectedCategory)

  const categories = [
    { value: 'all', label: 'All Insights', count: mockInsights.length },
    { value: 'market_opportunity', label: 'Market Opportunities', count: mockInsights.filter(i => i.category === 'market_opportunity').length },
    { value: 'competitive_intelligence', label: 'Competitive Intel', count: mockInsights.filter(i => i.category === 'competitive_intelligence').length },
    { value: 'policy_impact', label: 'Policy Impact', count: mockInsights.filter(i => i.category === 'policy_impact').length },
    { value: 'investment_guidance', label: 'Investment Guidance', count: mockInsights.filter(i => i.category === 'investment_guidance').length }
  ]

  return (
    <div className="intelligence-card h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-stark-100">Strategic Insights</h2>
          <p className="text-sm text-stark-400">AI-powered business intelligence and recommendations</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
          <span className="text-xs text-green-400">Live Analysis</span>
        </div>
      </div>

      {/* Category Filter */}
      <div className="mb-4">
        <div className="flex flex-wrap gap-2">
          {categories.map((category) => (
            <button
              key={category.value}
              onClick={() => setSelectedCategory(category.value)}
              className={`
                px-3 py-1 rounded-full text-xs font-medium transition-all duration-200
                ${selectedCategory === category.value
                  ? 'bg-jarvis-500/20 text-jarvis-400 border border-jarvis-500/50'
                  : 'bg-stark-700/50 text-stark-400 hover:bg-stark-600/50 hover:text-stark-200'
                }
              `}
            >
              {category.label} ({category.count})
            </button>
          ))}
        </div>
      </div>

      {/* Insights List */}
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {filteredInsights.map((insight) => {
          const config = categoryConfig[insight.category]
          const Icon = config.icon
          const isExpanded = expandedInsights.includes(insight.id)

          return (
            <div
              key={insight.id}
              className={`
                border rounded-lg transition-all duration-300
                ${config.bgColor} ${config.borderColor} border-l-4
                ${isExpanded ? 'shadow-lg' : 'shadow-sm hover:shadow-md'}
              `}
            >
              {/* Insight Header */}
              <div
                className="p-4 cursor-pointer"
                onClick={() => toggleInsightExpansion(insight.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <div className={`${config.bgColor} p-2 rounded-lg`}>
                      <Icon className={`w-5 h-5 ${config.color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="font-semibold text-stark-100 text-sm">
                          {insight.title}
                        </h3>
                        {insight.priority === 'high' && (
                          <span className="px-2 py-1 text-xs font-medium bg-critical-alert/20 text-critical-alert rounded-full">
                            HIGH PRIORITY
                          </span>
                        )}
                      </div>
                      
                      {/* Confidence and Timeframe */}
                      <div className="flex items-center space-x-4 mb-2">
                        <div className="flex items-center space-x-1">
                          <CheckCircleIcon className="w-4 h-4 text-green-400" />
                          <span className="text-xs text-stark-300">
                            {Math.round(insight.confidence * 100)}% Confidence
                          </span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <ClockIcon className="w-4 h-4 text-stark-400" />
                          <span className="text-xs text-stark-300">
                            {insight.timeframe}
                          </span>
                        </div>
                      </div>

                      <p className="text-stark-300 text-sm line-clamp-2">
                        {insight.insight}
                      </p>

                      {/* Tags */}
                      <div className="flex flex-wrap gap-1 mt-2">
                        {insight.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-1 text-xs bg-stark-700/50 text-stark-400 rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  <button className="p-1 text-stark-400 hover:text-stark-200 rounded">
                    {isExpanded ? (
                      <ChevronUpIcon className="w-5 h-5" />
                    ) : (
                      <ChevronDownIcon className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-stark-700/50">
                  <div className="pt-4 space-y-4">
                    {/* Business Impact */}
                    <div>
                      <h4 className="font-medium text-stark-200 text-sm mb-2">Business Impact</h4>
                      <p className="text-stark-300 text-sm">{insight.businessImpact}</p>
                    </div>

                    {/* Metrics */}
                    {insight.metrics && (
                      <div>
                        <h4 className="font-medium text-stark-200 text-sm mb-2">Key Metrics</h4>
                        <div className="grid grid-cols-3 gap-4">
                          {insight.metrics.map((metric, index) => (
                            <div key={index} className="text-center">
                              <div className={`
                                text-lg font-bold
                                ${metric.trend === 'up' ? 'text-green-400' : 
                                  metric.trend === 'down' ? 'text-red-400' : 'text-stark-300'}
                              `}>
                                {metric.value}
                              </div>
                              <div className="text-xs text-stark-400">{metric.label}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Recommended Actions */}
                    <div>
                      <h4 className="font-medium text-stark-200 text-sm mb-2">Recommended Actions</h4>
                      <div className="space-y-2">
                        {insight.recommendedActions.map((action, index) => (
                          <div key={index} className="flex items-start space-x-2">
                            <div className="w-1.5 h-1.5 bg-jarvis-500 rounded-full mt-2 flex-shrink-0"></div>
                            <span className="text-stark-300 text-sm">{action}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center space-x-3 pt-2">
                      <button className="btn-jarvis text-xs px-3 py-1.5">
                        Create Action Plan
                      </button>
                      <button className="btn-ghost text-xs px-3 py-1.5">
                        View Full Analysis
                        <ArrowTopRightOnSquareIcon className="w-3 h-3 ml-1 inline" />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}