import { useState } from 'react'
import {
  DocumentTextIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  CurrencyDollarIcon,
  BanknotesIcon,
  BuildingLibraryIcon,
  ScaleIcon,
  CalendarDaysIcon,
  ArrowRightIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'

interface PolicyChange {
  id: string
  title: string
  agency: string
  category: 'budget' | 'regulation' | 'initiative' | 'mandate'
  impact_level: 'high' | 'medium' | 'low'
  impact_type: 'opportunity' | 'threat' | 'neutral'
  effective_date: Date
  confidence: number
  estimated_market_impact: number
  summary: string
  detailed_impact: string
  affected_sectors: string[]
  business_implications: string[]
  recommended_actions: string[]
  timeline_milestones: TimelineMilestone[]
  related_opportunities: RelatedOpportunity[]
}

interface TimelineMilestone {
  date: Date
  event: string
  impact: string
}

interface RelatedOpportunity {
  title: string
  value: number
  probability: number
  timeline: string
}

const mockPolicyChanges: PolicyChange[] = [
  {
    id: '1',
    title: 'Zero Trust Executive Order Implementation Guidance',
    agency: 'CISA',
    category: 'mandate',
    impact_level: 'high',
    impact_type: 'opportunity',
    effective_date: new Date('2024-03-15'),
    confidence: 0.92,
    estimated_market_impact: 2800000000,
    summary: 'CISA releases detailed implementation guidance for federal Zero Trust architecture mandates with specific timelines and compliance requirements.',
    detailed_impact: 'Federal agencies must achieve Zero Trust maturity by FY 2026, creating massive demand for identity management, network segmentation, and continuous monitoring solutions. New compliance requirements will drive modernization of legacy systems across all federal departments.',
    affected_sectors: ['Federal IT', 'Defense Contractors', 'Cloud Providers', 'Identity Management', 'Network Security'],
    business_implications: [
      'Mandatory Zero Trust implementation creates $2.8B in new federal opportunities',
      'Legacy system modernization requirements favor experienced federal contractors',
      'Identity and access management solutions become critical procurement priority',
      'Compliance consulting and implementation services in high demand'
    ],
    recommended_actions: [
      'Develop Zero Trust assessment and implementation service offerings',
      'Partner with identity management platform providers',
      'Obtain FISMA and FedRAMP certifications for Zero Trust solutions',
      'Create compliance roadmap templates for federal agencies'
    ],
    timeline_milestones: [
      {
        date: new Date('2024-03-15'),
        event: 'Implementation guidance released',
        impact: 'RFP requirements updated to include Zero Trust mandates'
      },
      {
        date: new Date('2024-06-30'),
        event: 'Agency compliance plans due',
        impact: 'Assessment and planning services opportunities peak'
      },
      {
        date: new Date('2024-12-31'),
        event: 'Phase 1 implementations required',
        impact: 'Implementation and integration services demand surge'
      },
      {
        date: new Date('2026-09-30'),
        event: 'Full Zero Trust maturity required',
        impact: 'Final implementation and certification push'
      }
    ],
    related_opportunities: [
      {
        title: 'DOD Zero Trust Implementation IDIQ',
        value: 750000000,
        probability: 0.73,
        timeline: 'Q2 2024'
      },
      {
        title: 'Treasury Zero Trust Assessment',
        value: 85000000,
        probability: 0.81,
        timeline: 'Q1 2024'
      }
    ]
  },
  {
    id: '2',
    title: 'Infrastructure Investment and Jobs Act Cybersecurity Funding',
    agency: 'DHS',
    category: 'budget',
    impact_level: 'high',
    impact_type: 'opportunity',
    effective_date: new Date('2024-02-01'),
    confidence: 0.87,
    estimated_market_impact: 1900000000,
    summary: 'DHS allocates $1.9B from Infrastructure Bill specifically for critical infrastructure cybersecurity improvements across state and local governments.',
    detailed_impact: 'State and local governments receive federal funding to upgrade cybersecurity for critical infrastructure including power grids, water systems, and transportation networks. Emphasis on public-private partnerships and information sharing platforms.',
    affected_sectors: ['State & Local Government', 'Critical Infrastructure', 'Utilities', 'Transportation', 'Public Safety'],
    business_implications: [
      'State and local government cybersecurity budgets increase significantly',
      'Critical infrastructure protection becomes funded priority',
      'Public-private partnership opportunities expand',
      'Rural and underserved area connectivity and security funding available'
    ],
    recommended_actions: [
      'Develop state and local government go-to-market strategy',
      'Create critical infrastructure security service packages',
      'Establish partnerships with state technology offices',
      'Pursue relevant state contractor certifications'
    ],
    timeline_milestones: [
      {
        date: new Date('2024-02-01'),
        event: 'Funding allocation announced',
        impact: 'Grant application processes begin'
      },
      {
        date: new Date('2024-04-30'),
        event: 'State allocation plans due',
        impact: 'State-level RFPs and procurement planning'
      },
      {
        date: new Date('2024-07-01'),
        event: 'First round of grants awarded',
        impact: 'Implementation contracts begin'
      }
    ],
    related_opportunities: [
      {
        title: 'California Critical Infrastructure Protection',
        value: 150000000,
        probability: 0.65,
        timeline: 'Q3 2024'
      },
      {
        title: 'Texas Power Grid Security Initiative',
        value: 220000000,
        probability: 0.58,
        timeline: 'Q4 2024'
      }
    ]
  },
  {
    id: '3',
    title: 'NIST Post-Quantum Cryptography Standards Finalization',
    agency: 'NIST',
    category: 'regulation',
    impact_level: 'medium',
    impact_type: 'opportunity',
    effective_date: new Date('2024-08-01'),
    confidence: 0.78,
    estimated_market_impact: 450000000,
    summary: 'NIST finalizes post-quantum cryptography standards, triggering federal agency migration requirements and procurement preference updates.',
    detailed_impact: 'Federal agencies must begin transitioning to quantum-resistant cryptographic methods. New procurement requirements will favor vendors with post-quantum cryptography expertise and certified solutions.',
    affected_sectors: ['Federal IT', 'Cryptography', 'Defense', 'Financial Services', 'Healthcare IT'],
    business_implications: [
      'Early quantum cryptography expertise becomes competitive advantage',
      'Federal RFPs begin including post-quantum requirements',
      'Legacy system cryptography upgrades required across government',
      'Certification and compliance services for post-quantum implementations needed'
    ],
    recommended_actions: [
      'Hire quantum cryptography specialists',
      'Develop post-quantum cryptography service offerings',
      'Pursue NIST post-quantum certification processes',
      'Create migration planning and implementation services'
    ],
    timeline_milestones: [
      {
        date: new Date('2024-08-01'),
        event: 'Standards finalized and published',
        impact: 'Federal agencies begin planning quantum-resistant transitions'
      },
      {
        date: new Date('2025-02-01'),
        event: 'Federal procurement preference effective',
        impact: 'RFPs begin requiring post-quantum cryptography plans'
      },
      {
        date: new Date('2027-08-01'),
        event: 'Mandatory transition deadline for new systems',
        impact: 'All new federal systems must use quantum-resistant cryptography'
      }
    ],
    related_opportunities: [
      {
        title: 'NSA Post-Quantum Migration Assessment',
        value: 125000000,
        probability: 0.42,
        timeline: 'Q1 2025'
      }
    ]
  },
  {
    id: '4',
    title: 'OMB Software Supply Chain Security Requirements',
    agency: 'OMB',
    category: 'mandate',
    impact_level: 'high',
    impact_type: 'threat',
    effective_date: new Date('2024-01-15'),
    confidence: 0.95,
    estimated_market_impact: -350000000,
    summary: 'OMB mandates enhanced software supply chain security requirements for all federal software procurements, including SBOM requirements and vendor attestations.',
    detailed_impact: 'All federal software vendors must provide Software Bill of Materials (SBOM) and undergo enhanced security vetting. Smaller vendors may struggle with compliance requirements, potentially reducing competition in federal software markets.',
    affected_sectors: ['Software Development', 'Federal IT', 'DevOps Tools', 'Security Tools', 'Compliance Services'],
    business_implications: [
      'Additional compliance costs for all federal software vendors',
      'SBOM generation and management becomes mandatory capability',
      'Enhanced vendor security vetting requirements increase barriers to entry',
      'Compliance consulting and attestation services see increased demand'
    ],
    recommended_actions: [
      'Implement SBOM generation capabilities in development processes',
      'Enhance software supply chain security practices',
      'Invest in vendor security attestation and compliance systems',
      'Consider offering supply chain security consulting services'
    ],
    timeline_milestones: [
      {
        date: new Date('2024-01-15'),
        event: 'Requirements effective for new contracts',
        impact: 'New federal software contracts must include SBOM requirements'
      },
      {
        date: new Date('2024-07-01'),
        event: 'Existing contract amendments required',
        impact: 'All existing federal software vendors must comply or face contract termination'
      }
    ],
    related_opportunities: [
      {
        title: 'Federal SBOM Management Platform',
        value: 75000000,
        probability: 0.61,
        timeline: 'Q2 2024'
      }
    ]
  }
]

const categoryConfig = {
  budget: {
    icon: BanknotesIcon,
    color: 'text-green-400',
    bgColor: 'bg-green-400/20',
    borderColor: 'border-green-400/50',
    label: 'Budget Allocation'
  },
  regulation: {
    icon: ScaleIcon,
    color: 'text-blue-400',
    bgColor: 'bg-blue-400/20',
    borderColor: 'border-blue-400/50',
    label: 'Regulatory Change'
  },
  initiative: {
    icon: ArrowTrendingUpIcon,
    color: 'text-jarvis-400',
    bgColor: 'bg-jarvis-500/20',
    borderColor: 'border-jarvis-500/50',
    label: 'Policy Initiative'
  },
  mandate: {
    icon: ExclamationTriangleIcon,
    color: 'text-warning',
    bgColor: 'bg-warning/20',
    borderColor: 'border-warning/50',
    label: 'Federal Mandate'
  }
}

const impactConfig = {
  opportunity: {
    color: 'text-green-400',
    bgColor: 'bg-green-400/20',
    icon: ArrowTrendingUpIcon,
    label: 'Market Opportunity'
  },
  threat: {
    color: 'text-red-400',
    bgColor: 'bg-red-400/20',
    icon: ArrowTrendingDownIcon,
    label: 'Market Threat'
  },
  neutral: {
    color: 'text-stark-400',
    bgColor: 'bg-stark-600/20',
    icon: InformationCircleIcon,
    label: 'Neutral Impact'
  }
}

export default function PolicyImpactAnalyzer() {
  const [expandedPolicies, setExpandedPolicies] = useState<string[]>(['1'])
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedImpact, setSelectedImpact] = useState<string>('all')

  const togglePolicyExpansion = (policyId: string) => {
    setExpandedPolicies(prev => 
      prev.includes(policyId) 
        ? prev.filter(id => id !== policyId)
        : [...prev, policyId]
    )
  }

  const formatCurrency = (amount: number) => {
    const absAmount = Math.abs(amount)
    if (absAmount >= 1000000000) {
      return `${amount < 0 ? '-' : ''}$${(absAmount / 1000000000).toFixed(1)}B`
    } else if (absAmount >= 1000000) {
      return `${amount < 0 ? '-' : ''}$${(absAmount / 1000000).toFixed(0)}M`
    } else {
      return `${amount < 0 ? '-' : ''}$${(absAmount / 1000).toFixed(0)}K`
    }
  }

  const filteredPolicies = mockPolicyChanges.filter(policy => {
    const categoryMatch = selectedCategory === 'all' || policy.category === selectedCategory
    const impactMatch = selectedImpact === 'all' || policy.impact_type === selectedImpact
    return categoryMatch && impactMatch
  })

  const totalImpact = mockPolicyChanges.reduce((sum, policy) => sum + policy.estimated_market_impact, 0)
  const opportunityCount = mockPolicyChanges.filter(policy => policy.impact_type === 'opportunity').length
  const threatCount = mockPolicyChanges.filter(policy => policy.impact_type === 'threat').length

  return (
    <div className="intelligence-card h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-stark-100">Policy Impact Analysis</h2>
          <p className="text-sm text-stark-400">Federal policy changes and market impact assessment</p>
        </div>
        <div className="flex items-center space-x-2">
          <DocumentTextIcon className="w-5 h-5 text-jarvis-400" />
          <span className="text-xs text-jarvis-400">Real-time Policy Tracking</span>
        </div>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="jarvis-panel p-3">
          <div className="flex items-center space-x-2">
            <ArrowTrendingUpIcon className="w-5 h-5 text-green-400" />
            <span className="text-sm text-stark-400">Opportunities</span>
          </div>
          <div className="mt-1">
            <div className="text-lg font-bold text-green-400">
              {opportunityCount}
            </div>
            <div className="text-xs text-stark-400">
              Active policies
            </div>
          </div>
        </div>
        
        <div className="jarvis-panel p-3">
          <div className="flex items-center space-x-2">
            <ArrowTrendingDownIcon className="w-5 h-5 text-red-400" />
            <span className="text-sm text-stark-400">Threats</span>
          </div>
          <div className="mt-1">
            <div className="text-lg font-bold text-red-400">
              {threatCount}
            </div>
            <div className="text-xs text-stark-400">
              Risk factors
            </div>
          </div>
        </div>
        
        <div className="jarvis-panel p-3">
          <div className="flex items-center space-x-2">
            <CurrencyDollarIcon className="w-5 h-5 text-jarvis-400" />
            <span className="text-sm text-stark-400">Net Impact</span>
          </div>
          <div className="mt-1">
            <div className={`text-lg font-bold ${totalImpact >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {formatCurrency(totalImpact)}
            </div>
            <div className="text-xs text-stark-400">
              Market opportunity
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-xs text-stark-400 mb-2 block">Category</label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full bg-stark-800 border border-stark-600 rounded-lg px-3 py-2 text-sm text-stark-200 focus:border-jarvis-500 focus:outline-none"
          >
            <option value="all">All Categories</option>
            <option value="budget">Budget Allocation</option>
            <option value="regulation">Regulatory Change</option>
            <option value="initiative">Policy Initiative</option>
            <option value="mandate">Federal Mandate</option>
          </select>
        </div>
        
        <div>
          <label className="text-xs text-stark-400 mb-2 block">Impact Type</label>
          <select
            value={selectedImpact}
            onChange={(e) => setSelectedImpact(e.target.value)}
            className="w-full bg-stark-800 border border-stark-600 rounded-lg px-3 py-2 text-sm text-stark-200 focus:border-jarvis-500 focus:outline-none"
          >
            <option value="all">All Impacts</option>
            <option value="opportunity">Opportunities</option>
            <option value="threat">Threats</option>
            <option value="neutral">Neutral</option>
          </select>
        </div>
      </div>

      {/* Policy Changes List */}
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {filteredPolicies.map((policy) => {
          const categoryConf = categoryConfig[policy.category]
          const impactConf = impactConfig[policy.impact_type]
          const CategoryIcon = categoryConf.icon
          const ImpactIcon = impactConf.icon
          const isExpanded = expandedPolicies.includes(policy.id)

          return (
            <div
              key={policy.id}
              className={`
                border rounded-lg transition-all duration-300
                ${impactConf.bgColor} ${policy.impact_type === 'opportunity' ? 'border-green-400/50' : policy.impact_type === 'threat' ? 'border-red-400/50' : 'border-stark-600/50'} border-l-4
                ${isExpanded ? 'shadow-lg' : 'shadow-sm hover:shadow-md'}
              `}
            >
              {/* Policy Header */}
              <div
                className="p-4 cursor-pointer"
                onClick={() => togglePolicyExpansion(policy.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <div className={`${categoryConf.bgColor} p-2 rounded-lg`}>
                      <CategoryIcon className={`w-5 h-5 ${categoryConf.color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="font-semibold text-stark-100 text-sm">
                          {policy.title}
                        </h3>
                        {policy.impact_level === 'high' && (
                          <span className="px-2 py-1 text-xs font-medium bg-critical-alert/20 text-critical-alert rounded-full">
                            HIGH IMPACT
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-4 mb-2 text-xs">
                        <div className="flex items-center space-x-1">
                          <BuildingLibraryIcon className="w-3 h-3 text-stark-400" />
                          <span className="text-stark-300">{policy.agency}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <CalendarDaysIcon className="w-3 h-3 text-stark-400" />
                          <span className="text-stark-300">
                            Effective {policy.effective_date.toLocaleDateString()}
                          </span>
                        </div>
                        <div className={`
                          flex items-center space-x-1 px-2 py-1 rounded-full
                          ${impactConf.bgColor} ${impactConf.color}
                        `}>
                          <ImpactIcon className="w-3 h-3" />
                          <span className="text-xs font-medium">
                            {formatCurrency(policy.estimated_market_impact)}
                          </span>
                        </div>
                      </div>

                      <p className="text-stark-300 text-sm line-clamp-2">
                        {policy.summary}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-stark-700/50">
                  <div className="pt-4 space-y-4">
                    {/* Detailed Impact */}
                    <div>
                      <h4 className="font-medium text-stark-200 text-sm mb-2">Detailed Impact Analysis</h4>
                      <p className="text-stark-300 text-sm">{policy.detailed_impact}</p>
                    </div>

                    {/* Affected Sectors */}
                    <div>
                      <h4 className="font-medium text-stark-200 text-sm mb-2">Affected Sectors</h4>
                      <div className="flex flex-wrap gap-2">
                        {policy.affected_sectors.map((sector, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 text-xs bg-stark-700/50 text-stark-300 rounded"
                          >
                            {sector}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Business Implications */}
                    <div>
                      <h4 className="font-medium text-stark-200 text-sm mb-2">Business Implications</h4>
                      <div className="space-y-1">
                        {policy.business_implications.map((implication, index) => (
                          <div key={index} className="flex items-start space-x-2">
                            <ArrowRightIcon className="w-3 h-3 text-jarvis-400 mt-1 flex-shrink-0" />
                            <span className="text-stark-300 text-sm">{implication}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Recommended Actions */}
                    <div>
                      <h4 className="font-medium text-stark-200 text-sm mb-2">Recommended Actions</h4>
                      <div className="space-y-2">
                        {policy.recommended_actions.map((action, index) => (
                          <div key={index} className="flex items-start space-x-3">
                            <div className={`
                              w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
                              ${categoryConf.bgColor} ${categoryConf.color}
                            `}>
                              {index + 1}
                            </div>
                            <span className="text-stark-300 text-sm">{action}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Timeline Milestones */}
                    <div>
                      <h4 className="font-medium text-stark-200 text-sm mb-2">Key Timeline Milestones</h4>
                      <div className="space-y-3">
                        {policy.timeline_milestones.map((milestone, index) => (
                          <div key={index} className="flex items-start space-x-3">
                            <div className="flex flex-col items-center">
                              <div className="w-3 h-3 bg-jarvis-400 rounded-full"></div>
                              {index < policy.timeline_milestones.length - 1 && (
                                <div className="w-0.5 h-6 bg-stark-600 mt-2"></div>
                              )}
                            </div>
                            <div className="flex-1">
                              <div className="text-sm font-medium text-stark-200">
                                {milestone.date.toLocaleDateString()} - {milestone.event}
                              </div>
                              <div className="text-xs text-stark-400 mt-1">
                                {milestone.impact}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Related Opportunities */}
                    {policy.related_opportunities.length > 0 && (
                      <div>
                        <h4 className="font-medium text-stark-200 text-sm mb-2">Related Opportunities</h4>
                        <div className="space-y-2">
                          {policy.related_opportunities.map((opp, index) => (
                            <div key={index} className="jarvis-panel p-3">
                              <div className="flex items-center justify-between">
                                <div>
                                  <div className="text-sm font-medium text-stark-200">{opp.title}</div>
                                  <div className="text-xs text-stark-400">
                                    {Math.round(opp.probability * 100)}% probability • {opp.timeline}
                                  </div>
                                </div>
                                <div className="text-lg font-bold text-green-400">
                                  {formatCurrency(opp.value)}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Confidence & Actions */}
                    <div className="flex items-center justify-between pt-2">
                      <div className="flex items-center space-x-2">
                        <div className="text-xs text-stark-400">
                          Analysis Confidence: 
                          <span className={`ml-1 font-medium ${
                            policy.confidence >= 0.8 ? 'text-green-400' : 
                            policy.confidence >= 0.6 ? 'text-yellow-400' : 'text-red-400'
                          }`}>
                            {Math.round(policy.confidence * 100)}%
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        <button className="btn-jarvis text-xs px-3 py-1.5">
                          Track Policy Changes
                        </button>
                        <button className="btn-ghost text-xs px-3 py-1.5">
                          Export Analysis
                        </button>
                      </div>
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