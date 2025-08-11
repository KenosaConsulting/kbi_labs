import { useState } from 'react'
import {
  ShieldExclamationIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  UserGroupIcon,
  BuildingOfficeIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

interface Competitor {
  id: string
  name: string
  threatLevel: 'high' | 'medium' | 'low'
  recentActivity: string
  strategicImplications: string
  recommendedResponse: string
  marketShare: number
  recentWins: number
  capabilities: string[]
  strengths: string[]
  vulnerabilities: string[]
}

interface MarketPosition {
  yourPosition: string
  competitiveAdvantages: string[]
  vulnerabilities: string[]
  marketShare: number
  winRate: number
  averageDealSize: number
}

const mockCompetitors: Competitor[] = [
  {
    id: '1',
    name: 'CyberSecure Corp',
    threatLevel: 'high',
    recentActivity: 'Hired key DISA program manager (Dr. Jennifer Park) and opened DC office',
    strategicImplications: 'Significantly stronger position for DOD cyber opportunities, especially DISA contracts',
    recommendedResponse: 'Accelerate DISA relationship building, consider teaming opportunities, emphasize past performance advantages',
    marketShare: 18.5,
    recentWins: 7,
    capabilities: ['Zero Trust Architecture', 'Cloud Security', 'DISA Relations'],
    strengths: ['Strong DOD relationships', 'Large team capacity', 'Recent funding'],
    vulnerabilities: ['New to critical infrastructure', 'Limited NERC experience', 'Higher overhead']
  },
  {
    id: '2', 
    name: 'TechDefense Solutions',
    threatLevel: 'medium',
    recentActivity: 'Acquired AI security startup (SecureML) for $12M',
    strategicImplications: 'Enhanced AI/ML security capabilities may compete directly with your recent certifications',
    recommendedResponse: 'Differentiate on implementation experience vs. theoretical capabilities, emphasize real-world deployments',
    marketShare: 12.3,
    recentWins: 4,
    capabilities: ['AI/ML Security', 'Threat Detection', 'Incident Response'],
    strengths: ['AI expertise', 'Fast-growing', 'Innovative solutions'],
    vulnerabilities: ['Limited government experience', 'Integration challenges', 'Unproven at scale']
  },
  {
    id: '3',
    name: 'SecureFed LLC',
    threatLevel: 'medium',
    recentActivity: 'Expanded into water sector cybersecurity with new partnership',
    strategicImplications: 'Direct competition in emerging water infrastructure security market',
    recommendedResponse: 'Accelerate water sector capability development, leverage superior NERC experience as differentiator',
    marketShare: 8.7,
    recentWins: 3,
    capabilities: ['Water Systems', 'SCADA Security', 'Compliance'],
    strengths: ['Niche specialization', 'Strong partnerships', 'Compliance focus'],
    vulnerabilities: ['Limited technical depth', 'Small team', 'Geographic constraints']
  },
  {
    id: '4',
    name: 'Federal CyberGuard',
    threatLevel: 'low',
    recentActivity: 'Lost two senior engineers to competitors, restructuring leadership',
    strategicImplications: 'Weakened position may create opportunities to capture their clients or talent',
    recommendedResponse: 'Target their key clients with relationship-building activities, consider recruiting their talent',
    marketShare: 6.2,
    recentWins: 1,
    capabilities: ['Basic Cybersecurity', 'Compliance', 'Risk Assessment'],
    strengths: ['Established relationships', 'Cost-effective', 'Stable processes'],
    vulnerabilities: ['Losing talent', 'Limited innovation', 'Aging capabilities']
  }
]

const mockMarketPosition: MarketPosition = {
  yourPosition: 'Strong in NERC/Critical Infrastructure, Growing in AI Security',
  competitiveAdvantages: [
    'FedRAMP Authorization (only 2 competitors have this)',
    'NERC CIP Deep Expertise (market leading)',
    'Clean Security Record (zero incidents)',
    'Agile Team Structure (faster than large competitors)',
    'Government Relationships (15+ years history)'
  ],
  vulnerabilities: [
    'Limited AI/ML Staff (only 2 specialists)',
    'Geographic Concentration (70% revenue from East Coast)', 
    'Small Business Constraints (team size limitations)',
    'Limited Marketing (competitors have stronger brand presence)',
    'Funding Constraints (limited R&D budget)'
  ],
  marketShare: 14.2,
  winRate: 34.5,
  averageDealSize: 1850000
}

const threatLevelConfig = {
  high: {
    color: 'text-critical-alert',
    bgColor: 'bg-critical-alert/20',
    borderColor: 'border-critical-alert',
    icon: ExclamationTriangleIcon
  },
  medium: {
    color: 'text-warning',
    bgColor: 'bg-warning/20', 
    borderColor: 'border-warning',
    icon: InformationCircleIcon
  },
  low: {
    color: 'text-green-400',
    bgColor: 'bg-green-400/20',
    borderColor: 'border-green-400',
    icon: CheckCircleIcon
  }
}

export default function CompetitiveIntelPanel() {
  const [activeTab, setActiveTab] = useState<'competitors' | 'position'>('competitors')
  const [selectedCompetitor, setSelectedCompetitor] = useState<string | null>(null)

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`
    } else {
      return `$${(amount / 1000).toFixed(0)}K`
    }
  }

  return (
    <div className="intelligence-card h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-stark-100">Competitive Intelligence</h2>
          <p className="text-sm text-stark-400">Battlefield awareness and strategic positioning</p>
        </div>
        <div className="flex items-center space-x-2">
          <ShieldExclamationIcon className="w-5 h-5 text-jarvis-400" />
          <span className="text-xs text-jarvis-400">Active Monitoring</span>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 mb-4 bg-stark-800/50 rounded-lg p-1">
        <button
          onClick={() => setActiveTab('competitors')}
          className={`
            flex-1 px-3 py-2 text-sm font-medium rounded-md transition-all duration-200
            ${activeTab === 'competitors'
              ? 'bg-jarvis-500/20 text-jarvis-400'
              : 'text-stark-400 hover:text-stark-200'
            }
          `}
        >
          Threat Assessment
        </button>
        <button
          onClick={() => setActiveTab('position')}
          className={`
            flex-1 px-3 py-2 text-sm font-medium rounded-md transition-all duration-200
            ${activeTab === 'position'
              ? 'bg-jarvis-500/20 text-jarvis-400'
              : 'text-stark-400 hover:text-stark-200'
            }
          `}
        >
          Your Position
        </button>
      </div>

      {/* Content */}
      <div className="space-y-3 max-h-80 overflow-y-auto">
        {activeTab === 'competitors' && (
          <>
            {mockCompetitors.map((competitor) => {
              const config = threatLevelConfig[competitor.threatLevel]
              const Icon = config.icon
              const isSelected = selectedCompetitor === competitor.id

              return (
                <div
                  key={competitor.id}
                  className={`
                    ${config.bgColor} border rounded-lg cursor-pointer transition-all duration-200
                    ${isSelected 
                      ? `${config.borderColor} border-2 shadow-lg` 
                      : 'border-stark-700/50 hover:border-stark-600/50'
                    }
                  `}
                  onClick={() => setSelectedCompetitor(isSelected ? null : competitor.id)}
                >
                  {/* Competitor Header */}
                  <div className="p-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3 flex-1">
                        <div className={`${config.bgColor} p-2 rounded-lg`}>
                          <Icon className={`w-4 h-4 ${config.color}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <h3 className="font-semibold text-stark-100 text-sm">
                              {competitor.name}
                            </h3>
                            <span className={`
                              px-2 py-1 text-xs font-medium rounded-full
                              ${config.bgColor} ${config.color}
                            `}>
                              {competitor.threatLevel.toUpperCase()} THREAT
                            </span>
                          </div>
                          
                          <p className="text-stark-300 text-xs mb-2">
                            {competitor.recentActivity}
                          </p>
                          
                          <div className="flex items-center space-x-4 text-xs text-stark-400">
                            <div className="flex items-center space-x-1">
                              <ChartBarIcon className="w-3 h-3" />
                              <span>{competitor.marketShare}% market share</span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <ArrowTrendingUpIcon className="w-3 h-3" />
                              <span>{competitor.recentWins} recent wins</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {isSelected && (
                    <div className="px-3 pb-3 border-t border-stark-700/50">
                      <div className="pt-3 space-y-3">
                        {/* Strategic Implications */}
                        <div>
                          <h4 className="font-medium text-stark-200 text-xs mb-1">Strategic Implications</h4>
                          <p className="text-stark-300 text-xs">{competitor.strategicImplications}</p>
                        </div>

                        {/* Recommended Response */}
                        <div>
                          <h4 className="font-medium text-stark-200 text-xs mb-1">Recommended Response</h4>
                          <p className="text-stark-300 text-xs">{competitor.recommendedResponse}</p>
                        </div>

                        {/* Strengths and Vulnerabilities */}
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <h4 className="font-medium text-green-400 text-xs mb-1">Strengths</h4>
                            <div className="space-y-1">
                              {competitor.strengths.map((strength, index) => (
                                <div key={index} className="flex items-start space-x-1">
                                  <CheckCircleIcon className="w-3 h-3 text-green-400 mt-0.5 flex-shrink-0" />
                                  <span className="text-xs text-stark-300">{strength}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                          <div>
                            <h4 className="font-medium text-red-400 text-xs mb-1">Vulnerabilities</h4>
                            <div className="space-y-1">
                              {competitor.vulnerabilities.map((vulnerability, index) => (
                                <div key={index} className="flex items-start space-x-1">
                                  <XCircleIcon className="w-3 h-3 text-red-400 mt-0.5 flex-shrink-0" />
                                  <span className="text-xs text-stark-300">{vulnerability}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </>
        )}

        {activeTab === 'position' && (
          <div className="space-y-4">
            {/* Market Position Overview */}
            <div className="jarvis-panel p-4">
              <h3 className="font-semibold text-stark-200 mb-3">Market Position</h3>
              <p className="text-stark-300 text-sm mb-4">{mockMarketPosition.yourPosition}</p>
              
              {/* Key Metrics */}
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-lg font-bold text-jarvis-400">
                    {mockMarketPosition.marketShare}%
                  </div>
                  <div className="text-xs text-stark-400">Market Share</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-green-400">
                    {mockMarketPosition.winRate}%
                  </div>
                  <div className="text-xs text-stark-400">Win Rate</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-stark-300">
                    {formatCurrency(mockMarketPosition.averageDealSize)}
                  </div>
                  <div className="text-xs text-stark-400">Avg Deal Size</div>
                </div>
              </div>
            </div>

            {/* Competitive Advantages */}
            <div className="bg-green-400/10 rounded-lg p-4">
              <h4 className="font-semibold text-green-400 mb-3 flex items-center space-x-2">
                <CheckCircleIcon className="w-4 h-4" />
                <span>Competitive Advantages</span>
              </h4>
              <div className="space-y-2">
                {mockMarketPosition.competitiveAdvantages.map((advantage, index) => (
                  <div key={index} className="flex items-start space-x-2">
                    <div className="w-1.5 h-1.5 bg-green-400 rounded-full mt-2 flex-shrink-0"></div>
                    <span className="text-stark-300 text-sm">{advantage}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Vulnerabilities */}
            <div className="bg-red-400/10 rounded-lg p-4">
              <h4 className="font-semibold text-red-400 mb-3 flex items-center space-x-2">
                <ExclamationTriangleIcon className="w-4 h-4" />
                <span>Areas for Improvement</span>
              </h4>
              <div className="space-y-2">
                {mockMarketPosition.vulnerabilities.map((vulnerability, index) => (
                  <div key={index} className="flex items-start space-x-2">
                    <div className="w-1.5 h-1.5 bg-red-400 rounded-full mt-2 flex-shrink-0"></div>
                    <span className="text-stark-300 text-sm">{vulnerability}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mt-4 pt-4 border-t border-stark-700/50">
        <div className="flex items-center space-x-2">
          <button className="btn-jarvis text-xs px-3 py-1.5">
            Generate Competitive Report
          </button>
          <button className="btn-ghost text-xs px-3 py-1.5">
            Update Intelligence
          </button>
        </div>
      </div>
    </div>
  )
}