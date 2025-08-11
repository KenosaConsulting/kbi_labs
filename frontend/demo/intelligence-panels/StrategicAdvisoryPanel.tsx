import { useState } from 'react'
import {
  LightBulbIcon,
  CurrencyDollarIcon,
  UserGroupIcon,
  ArrowTrendingUpIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  ArrowTopRightOnSquareIcon,
  ChartBarIcon,
  BriefcaseIcon
} from '@heroicons/react/24/outline'

interface StrategicRecommendation {
  id: string
  category: 'investment' | 'partnership' | 'market_expansion' | 'capability_development'
  title: string
  recommendation: string
  rationale: string
  implementation: string
  investment: number
  expectedReturn: string | number
  timeline: string
  riskLevel: 'low' | 'medium' | 'high'
  priority: 'high' | 'medium' | 'low'
  success_probability: number
  keyBenefits: string[]
  implementation_steps: string[]
}

const mockRecommendations: StrategicRecommendation[] = [
  {
    id: '1',
    category: 'investment',
    title: 'Hire Quantum Cryptography Specialist',
    recommendation: 'Add senior quantum cryptography specialist to team within 90 days',
    rationale: 'NIST post-quantum standards driving federal adoption timeline acceleration. Early quantum expertise becoming competitive differentiator in government contracts.',
    implementation: '6-month search and onboarding process with university partnerships for talent acquisition',
    investment: 165000,
    expectedReturn: '340% ROI within 24 months',
    timeline: '90 days to hire, 6 months to full productivity',
    riskLevel: 'low',
    priority: 'high',
    success_probability: 0.78,
    keyBenefits: [
      'Access to $50M+ in quantum-resistant opportunities',
      'First-mover advantage in post-quantum government market',
      'Enhanced technical credibility with federal agencies',
      'Potential for NIST standards contribution and recognition'
    ],
    implementation_steps: [
      'Post quantum cryptography specialist position',
      'Partner with universities for quantum research talent',
      'Begin NIST post-quantum certification process',
      'Develop quantum security service offerings'
    ]
  },
  {
    id: '2',
    category: 'partnership',
    title: 'Strategic Cloud Provider Alliance',
    recommendation: 'Form exclusive partnership with major cloud infrastructure provider',
    rationale: 'Zero Trust implementations require integrated cloud + security solutions. Partnership provides access to $500M+ infrastructure opportunities while differentiating from competitors.',
    implementation: 'Formal partnership agreement with joint go-to-market strategy within 45 days',
    investment: 75000,
    expectedReturn: '$2.1M additional pipeline',
    timeline: '45 days to partnership, 3 months to first joint opportunity',
    riskLevel: 'medium',
    priority: 'high', 
    success_probability: 0.82,
    keyBenefits: [
      'Access to cloud infrastructure opportunity pipeline',
      'Joint technical solution development capabilities',
      'Enhanced credibility for large-scale implementations',
      'Shared marketing and business development costs'
    ],
    implementation_steps: [
      'Evaluate partnership opportunities (AWS, Azure, Oracle)',
      'Negotiate exclusive regional or sector partnership',
      'Develop integrated solution offerings',
      'Launch joint marketing and business development activities'
    ]
  },
  {
    id: '3',
    category: 'market_expansion',
    title: 'Water Sector Cybersecurity Entry',
    recommendation: 'Enter water sector cybersecurity market with specialized offering',
    rationale: 'Infrastructure bill allocates $150M for water systems security with limited competition. Your SCADA/OT expertise transfers directly to water infrastructure.',
    implementation: '6-month capability development program with water utility partnerships',
    investment: 95000,
    expectedReturn: '$1.8M pipeline opportunity',
    timeline: '6 months capability development, 12 months to first wins',
    riskLevel: 'medium',
    priority: 'medium',
    success_probability: 0.65,
    keyBenefits: [
      'New market with limited competition',
      'Leverages existing OT/SCADA expertise', 
      'Infrastructure bill funding provides stable demand',
      'Geographic expansion opportunities'
    ],
    implementation_steps: [
      'Research water sector regulatory requirements',
      'Develop water utility partnership relationships',
      'Create water-specific cybersecurity service offerings',
      'Pursue water sector certifications and credentials'
    ]
  },
  {
    id: '4',
    category: 'capability_development',
    title: 'AI Threat Detection Platform Development',
    recommendation: 'Develop proprietary AI threat detection platform for government clients',
    rationale: 'AI requirements in federal RFPs increasing 156%. Proprietary platform would differentiate from service-only competitors and create recurring revenue streams.',
    implementation: '12-month development timeline with phased deployment and government customer validation',
    investment: 450000,
    expectedReturn: '$5.2M annual recurring revenue potential',
    timeline: '12 months development, 6 months customer validation',
    riskLevel: 'high',
    priority: 'medium',
    success_probability: 0.58,
    keyBenefits: [
      'Product differentiation from service competitors',
      'Recurring revenue model vs. project-based',
      'Higher margin business with scalable technology',
      'Patent and IP development opportunities'
    ],
    implementation_steps: [
      'Assemble AI development team (3-4 specialists)',
      'Define minimum viable product for government validation',
      'Develop proof-of-concept with existing government customers',
      'Pursue government validation and initial deployments'
    ]
  }
]

const categoryConfig = {
  investment: {
    icon: CurrencyDollarIcon,
    color: 'text-green-400',
    bgColor: 'bg-green-400/20',
    borderColor: 'border-green-400/50'
  },
  partnership: {
    icon: UserGroupIcon,
    color: 'text-jarvis-400',
    bgColor: 'bg-jarvis-500/20',
    borderColor: 'border-jarvis-500/50'
  },
  market_expansion: {
    icon: ArrowTrendingUpIcon,
    color: 'text-opportunity',
    bgColor: 'bg-opportunity/20',
    borderColor: 'border-opportunity/50'
  },
  capability_development: {
    icon: BriefcaseIcon,
    color: 'text-warning',
    bgColor: 'bg-warning/20',
    borderColor: 'border-warning/50'
  }
}

const riskConfig = {
  low: { color: 'text-green-400', bgColor: 'bg-green-400/20' },
  medium: { color: 'text-yellow-400', bgColor: 'bg-yellow-400/20' },
  high: { color: 'text-red-400', bgColor: 'bg-red-400/20' }
}

export default function StrategicAdvisoryPanel() {
  const [expandedRecommendations, setExpandedRecommendations] = useState<string[]>(['1'])
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  const toggleRecommendationExpansion = (recommendationId: string) => {
    setExpandedRecommendations(prev => 
      prev.includes(recommendationId) 
        ? prev.filter(id => id !== recommendationId)
        : [...prev, recommendationId]
    )
  }

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`
    } else {
      return `$${(amount / 1000).toFixed(0)}K`
    }
  }

  const filteredRecommendations = selectedCategory === 'all' 
    ? mockRecommendations 
    : mockRecommendations.filter(rec => rec.category === selectedCategory)

  const totalInvestment = mockRecommendations.reduce((sum, rec) => sum + rec.investment, 0)
  const highPriorityCount = mockRecommendations.filter(rec => rec.priority === 'high').length

  return (
    <div className="intelligence-card h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-stark-100">Strategic Advisory</h2>
          <p className="text-sm text-stark-400">AI-powered business strategy recommendations</p>
        </div>
        <div className="flex items-center space-x-2">
          <LightBulbIcon className="w-5 h-5 text-jarvis-400" />
          <span className="text-xs text-jarvis-400">Board of Directors AI</span>
        </div>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="jarvis-panel p-3">
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />
            <span className="text-sm text-stark-400">High Priority</span>
          </div>
          <div className="mt-1">
            <div className="text-lg font-bold text-red-400">
              {highPriorityCount}
            </div>
            <div className="text-xs text-stark-400">
              Recommendations
            </div>
          </div>
        </div>
        
        <div className="jarvis-panel p-3">
          <div className="flex items-center space-x-2">
            <CurrencyDollarIcon className="w-5 h-5 text-green-400" />
            <span className="text-sm text-stark-400">Total Investment</span>
          </div>
          <div className="mt-1">
            <div className="text-lg font-bold text-green-400">
              {formatCurrency(totalInvestment)}
            </div>
            <div className="text-xs text-stark-400">
              Strategic initiatives
            </div>
          </div>
        </div>
      </div>

      {/* Category Filter */}
      <div className="mb-4">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`
              px-3 py-1 rounded-full text-xs font-medium transition-all duration-200
              ${selectedCategory === 'all'
                ? 'bg-jarvis-500/20 text-jarvis-400 border border-jarvis-500/50'
                : 'bg-stark-700/50 text-stark-400 hover:bg-stark-600/50 hover:text-stark-200'
              }
            `}
          >
            All ({mockRecommendations.length})
          </button>
          {Object.entries(categoryConfig).map(([category, config]) => {
            const count = mockRecommendations.filter(rec => rec.category === category).length
            return (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`
                  px-3 py-1 rounded-full text-xs font-medium transition-all duration-200
                  ${selectedCategory === category
                    ? `${config.bgColor} ${config.color} border ${config.borderColor}`
                    : 'bg-stark-700/50 text-stark-400 hover:bg-stark-600/50 hover:text-stark-200'
                  }
                `}
              >
                {category.replace('_', ' ')} ({count})
              </button>
            )
          })}
        </div>
      </div>

      {/* Recommendations List */}
      <div className="space-y-4 max-h-80 overflow-y-auto">
        {filteredRecommendations.map((recommendation) => {
          const config = categoryConfig[recommendation.category]
          const riskConf = riskConfig[recommendation.riskLevel]
          const Icon = config.icon
          const isExpanded = expandedRecommendations.includes(recommendation.id)

          return (
            <div
              key={recommendation.id}
              className={`
                border rounded-lg transition-all duration-300
                ${config.bgColor} ${config.borderColor} border-l-4
                ${isExpanded ? 'shadow-lg' : 'shadow-sm hover:shadow-md'}
              `}
            >
              {/* Recommendation Header */}
              <div
                className="p-4 cursor-pointer"
                onClick={() => toggleRecommendationExpansion(recommendation.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <div className={`${config.bgColor} p-2 rounded-lg`}>
                      <Icon className={`w-5 h-5 ${config.color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="font-semibold text-stark-100 text-sm">
                          {recommendation.title}
                        </h3>
                        {recommendation.priority === 'high' && (
                          <span className="px-2 py-1 text-xs font-medium bg-critical-alert/20 text-critical-alert rounded-full">
                            HIGH PRIORITY
                          </span>
                        )}
                      </div>
                      
                      {/* Key Metrics */}
                      <div className="flex items-center space-x-4 mb-2 text-xs">
                        <div className="flex items-center space-x-1">
                          <CurrencyDollarIcon className="w-3 h-3 text-green-400" />
                          <span className="text-stark-300">
                            {formatCurrency(recommendation.investment)} investment
                          </span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <CheckCircleIcon className="w-3 h-3 text-jarvis-400" />
                          <span className="text-stark-300">
                            {Math.round(recommendation.success_probability * 100)}% success rate
                          </span>
                        </div>
                        <div className={`
                          flex items-center space-x-1 px-2 py-1 rounded-full
                          ${riskConf.bgColor} ${riskConf.color}
                        `}>
                          <span className="text-xs font-medium">
                            {recommendation.riskLevel.toUpperCase()} RISK
                          </span>
                        </div>
                      </div>

                      <p className="text-stark-300 text-sm line-clamp-2">
                        {recommendation.recommendation}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-stark-700/50">
                  <div className="pt-4 space-y-4">
                    {/* Strategic Rationale */}
                    <div>
                      <h4 className="font-medium text-stark-200 text-sm mb-2">Strategic Rationale</h4>
                      <p className="text-stark-300 text-sm">{recommendation.rationale}</p>
                    </div>

                    {/* Implementation & ROI */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium text-stark-200 text-sm mb-2">Expected Return</h4>
                        <div className="text-lg font-bold text-green-400">
                          {typeof recommendation.expectedReturn === 'number' 
                            ? formatCurrency(recommendation.expectedReturn)
                            : recommendation.expectedReturn
                          }
                        </div>
                        <div className="text-xs text-stark-400">
                          Timeline: {recommendation.timeline}
                        </div>
                      </div>
                      <div>
                        <h4 className="font-medium text-stark-200 text-sm mb-2">Implementation</h4>
                        <p className="text-stark-300 text-sm">{recommendation.implementation}</p>
                      </div>
                    </div>

                    {/* Key Benefits */}
                    <div>
                      <h4 className="font-medium text-stark-200 text-sm mb-2">Key Benefits</h4>
                      <div className="space-y-1">
                        {recommendation.keyBenefits.map((benefit, index) => (
                          <div key={index} className="flex items-start space-x-2">
                            <div className="w-1.5 h-1.5 bg-green-400 rounded-full mt-2 flex-shrink-0"></div>
                            <span className="text-stark-300 text-sm">{benefit}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Implementation Steps */}
                    <div>
                      <h4 className="font-medium text-stark-200 text-sm mb-2">Implementation Steps</h4>
                      <div className="space-y-2">
                        {recommendation.implementation_steps.map((step, index) => (
                          <div key={index} className="flex items-start space-x-3">
                            <div className={`
                              w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
                              ${config.bgColor} ${config.color}
                            `}>
                              {index + 1}
                            </div>
                            <span className="text-stark-300 text-sm">{step}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center space-x-3 pt-2">
                      <button className="btn-jarvis text-xs px-3 py-1.5">
                        Approve & Plan Implementation
                      </button>
                      <button className="btn-ghost text-xs px-3 py-1.5">
                        View Detailed Analysis
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

      {/* Advisory Summary */}
      <div className="mt-4 pt-4 border-t border-stark-700/50">
        <div className="jarvis-panel p-3">
          <div className="flex items-center space-x-2 mb-2">
            <ChartBarIcon className="w-4 h-4 text-jarvis-400" />
            <h4 className="font-medium text-stark-200 text-sm">Strategic Outlook</h4>
          </div>
          <p className="text-stark-300 text-xs">
            Implementing high-priority recommendations could generate {formatCurrency(5200000)} in additional revenue 
            over 24 months with {formatCurrency(785000)} total investment. 
            Focus on quantum expertise and cloud partnerships for maximum impact.
          </p>
        </div>
      </div>
    </div>
  )
}