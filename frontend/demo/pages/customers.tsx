import type { NextPage } from 'next'
import Head from 'next/head'
import { useState } from 'react'
import DashboardLayout from '../strategic-dashboard/DashboardLayout'
import { 
  BuildingOffice2Icon,
  UserIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  CalendarDaysIcon,
  ArrowTrendingUpIcon,
  PhoneIcon,
  EnvelopeIcon,
  MapPinIcon
} from '@heroicons/react/24/outline'

interface AgencyProfile {
  id: string
  name: string
  abbreviation: string
  totalBudget: number
  cyberSecurityBudget: number
  yourAddressableMarket: number
  averageContractSize: number
  preferredVendorProfile: string
  relationshipStrength: 'strong' | 'moderate' | 'developing' | 'none'
  recentActivity: string[]
  strategicPriorities: string[]
  keyDecisionMakers: DecisionMaker[]
  recentContracts: Contract[]
}

interface DecisionMaker {
  name: string
  title: string
  background: string
  influence: 'high' | 'medium' | 'low'
  contactHistory: string
  preferredApproach: string
  email?: string
  phone?: string
}

interface Contract {
  title: string
  value: number
  winner: string
  status: 'your_win' | 'competitor_win' | 'upcoming'
  date: Date
  keyFactors: string[]
}

const mockAgencies: AgencyProfile[] = [
  {
    id: 'doe',
    name: 'Department of Energy',
    abbreviation: 'DOE',
    totalBudget: 2100000000,
    cyberSecurityBudget: 450000000,
    yourAddressableMarket: 340000000,
    averageContractSize: 1200000,
    preferredVendorProfile: 'NERC CIP experience, OT security focus, energy sector understanding',
    relationshipStrength: 'strong',
    recentActivity: [
      'Increased grid modernization budget by 40%',
      'New cybersecurity division under Dr. Sarah Chen',
      'Focus on renewable energy integration security'
    ],
    strategicPriorities: [
      'Grid resilience against cyber threats',
      'Integration of renewable energy security',
      'Legacy system modernization',
      'Supply chain risk management'
    ],
    keyDecisionMakers: [
      {
        name: 'Dr. Sarah Chen',
        title: 'Director, Cybersecurity Division',
        background: 'Former NERC executive, 15 years in energy sector cybersecurity, PhD in electrical engineering',
        influence: 'high',
        contactHistory: 'Met at NERC conference 2023, quarterly technical briefings since May 2023',
        preferredApproach: 'Technical deep-dives, quarterly business reviews, grid security trend analysis',
        email: 'sarah.chen@energy.gov',
        phone: '(202) 555-0143'
      },
      {
        name: 'Michael Rodriguez',
        title: 'Deputy Assistant Secretary for Cybersecurity',
        background: 'Former utility CISO, expertise in SCADA and industrial control systems',
        influence: 'high',
        contactHistory: 'Initial meeting through Dr. Chen, positive response to OT security proposal',
        preferredApproach: 'Executive briefings, industry trend reports, strategic partnership discussions'
      }
    ],
    recentContracts: [
      {
        title: 'Grid Modernization Security Assessment',
        value: 3200000,
        winner: 'Your Company',
        status: 'your_win',
        date: new Date('2023-09-15'),
        keyFactors: ['NERC CIP expertise', 'Past performance', 'Technical approach', 'Competitive pricing']
      },
      {
        title: 'Renewable Energy Integration Security',
        value: 1800000,
        winner: 'EnergySecure Corp',
        status: 'competitor_win',
        date: new Date('2023-11-30'),
        keyFactors: ['Renewable energy focus', 'Lower cost', 'Faster timeline']
      },
      {
        title: 'SCADA Security Framework Implementation',
        value: 2100000,
        winner: 'TBD',
        status: 'upcoming',
        date: new Date('2024-03-01'),
        keyFactors: ['SCADA expertise required', 'Multi-site deployment', 'Training component']
      }
    ]
  },
  {
    id: 'dod',
    name: 'Department of Defense',
    abbreviation: 'DOD',
    totalBudget: 15600000000,
    cyberSecurityBudget: 3400000000,
    yourAddressableMarket: 890000000,
    averageContractSize: 2800000,
    preferredVendorProfile: 'Security clearances, DOD experience, zero trust expertise, cloud security focus',
    relationshipStrength: 'moderate',
    recentActivity: [
      'Zero Trust acceleration initiative launched',
      'AI/ML security requirements in all new RFPs',
      'Cloud-first security architecture mandate'
    ],
    strategicPriorities: [
      'Zero Trust architecture implementation',
      'AI/ML security integration',
      'Cloud security standardization',
      'Supply chain security enhancement'
    ],
    keyDecisionMakers: [
      {
        name: 'Colonel Jennifer Park',
        title: 'Chief Information Security Officer',
        background: 'Former DISA program manager, 20+ years military IT, expert in enterprise security',
        influence: 'high',
        contactHistory: 'Recently hired by CyberSecure Corp - competitive threat',
        preferredApproach: 'Military briefing format, technical demonstrations, past performance emphasis'
      },
      {
        name: 'Dr. James Liu',
        title: 'Director of Cyber Operations',
        background: 'Academic background, focus on AI security and advanced persistent threats',
        influence: 'medium',
        contactHistory: 'No direct relationship - opportunity for engagement',
        preferredApproach: 'Technical whitepapers, AI security thought leadership, research collaboration'
      }
    ],
    recentContracts: [
      {
        title: 'Enterprise Security Assessment',
        value: 1900000,
        winner: 'SecureFed LLC',
        status: 'competitor_win',
        date: new Date('2023-08-20'),
        keyFactors: ['Lower cost', 'DOD relationships', 'Faster delivery']
      },
      {
        title: 'Zero Trust Implementation IDIQ',
        value: 15000000,
        winner: 'TBD',
        status: 'upcoming',
        date: new Date('2024-02-15'),
        keyFactors: ['Zero Trust expertise', 'Large team capacity', 'Cloud integration']
      }
    ]
  },
  {
    id: 'dhs',
    name: 'Department of Homeland Security',
    abbreviation: 'DHS',
    totalBudget: 1890000000,
    cyberSecurityBudget: 890000000,
    yourAddressableMarket: 234000000,
    averageContractSize: 850000,
    preferredVendorProfile: 'Critical infrastructure expertise, incident response, risk assessment focus',
    relationshipStrength: 'developing',
    recentActivity: [
      'Critical infrastructure protection emphasis',
      'Public-private partnership expansion',
      'Incident response capability enhancement'
    ],
    strategicPriorities: [
      'Critical infrastructure protection',
      'Incident response and recovery',
      'Threat intelligence sharing',
      'Public-private collaboration'
    ],
    keyDecisionMakers: [
      {
        name: 'Maria Gonzalez',
        title: 'Assistant Director, Cybersecurity Division',
        background: 'Former private sector CISO, expertise in critical infrastructure protection',
        influence: 'high',
        contactHistory: 'Initial meeting scheduled for January 2024',
        preferredApproach: 'Industry case studies, critical infrastructure focus, partnership opportunities'
      }
    ],
    recentContracts: [
      {
        title: 'Critical Infrastructure Risk Assessment',
        value: 1200000,
        winner: 'TBD',
        status: 'upcoming',
        date: new Date('2024-04-30'),
        keyFactors: ['Critical infrastructure expertise', 'Risk assessment methodology', 'Multi-sector experience']
      }
    ]
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

const relationshipConfig = {
  strong: { color: 'text-green-400', bgColor: 'bg-green-400/20', label: 'Strong Partnership' },
  moderate: { color: 'text-yellow-400', bgColor: 'bg-yellow-400/20', label: 'Active Relationship' },
  developing: { color: 'text-blue-400', bgColor: 'bg-blue-400/20', label: 'Developing Relationship' },
  none: { color: 'text-stark-400', bgColor: 'bg-stark-600/20', label: 'No Relationship' }
}

const CustomerIntelligence: NextPage = () => {
  const [selectedAgency, setSelectedAgency] = useState<string>('doe')
  const [activeTab, setActiveTab] = useState<'overview' | 'contacts' | 'contracts'>('overview')

  const currentAgency = mockAgencies.find(agency => agency.id === selectedAgency)
  if (!currentAgency) return null

  const relationshipConf = relationshipConfig[currentAgency.relationshipStrength]

  return (
    <>
      <Head>
        <title>Government Customer Intelligence - KBI Labs</title>
        <meta name="description" content="Deep agency profiles and decision maker intelligence" />
      </Head>
      
      <DashboardLayout>
        {/* Page Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-stark-100">Government Customer Intelligence</h1>
          <p className="text-stark-400">Deep agency profiles and decision maker relationships</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Agency Selector */}
          <div className="lg:col-span-1">
            <div className="intelligence-card">
              <h2 className="text-lg font-semibold text-stark-100 mb-4">Target Agencies</h2>
              <div className="space-y-2">
                {mockAgencies.map((agency) => {
                  const relConf = relationshipConfig[agency.relationshipStrength]
                  return (
                    <button
                      key={agency.id}
                      onClick={() => setSelectedAgency(agency.id)}
                      className={`
                        w-full text-left p-3 rounded-lg transition-all duration-200
                        ${selectedAgency === agency.id
                          ? 'bg-jarvis-500/20 border border-jarvis-500/50'
                          : 'bg-stark-800/50 hover:bg-stark-700/50'
                        }
                      `}
                    >
                      <div className="flex items-center space-x-2 mb-2">
                        <BuildingOffice2Icon className="w-5 h-5 text-jarvis-400" />
                        <span className="font-medium text-stark-100 text-sm">
                          {agency.abbreviation}
                        </span>
                      </div>
                      <div className="text-xs text-stark-400 mb-2">
                        {formatCurrency(agency.yourAddressableMarket)} addressable
                      </div>
                      <div className={`
                        inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
                        ${relConf.bgColor} ${relConf.color}
                      `}>
                        {relConf.label}
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {/* Agency Header */}
            <div className="intelligence-card mb-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-2xl font-bold text-stark-100">{currentAgency.name}</h1>
                  <p className="text-stark-400">{currentAgency.abbreviation}</p>
                </div>
                <div className={`
                  inline-flex items-center px-3 py-2 rounded-lg text-sm font-medium
                  ${relationshipConf.bgColor} ${relationshipConf.color}
                `}>
                  {relationshipConf.label}
                </div>
              </div>

              {/* Key Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="jarvis-panel p-3">
                  <div className="text-center">
                    <div className="text-lg font-bold text-green-400">
                      {formatCurrency(currentAgency.yourAddressableMarket)}
                    </div>
                    <div className="text-xs text-stark-400">Your Market</div>
                  </div>
                </div>
                <div className="jarvis-panel p-3">
                  <div className="text-center">
                    <div className="text-lg font-bold text-jarvis-400">
                      {formatCurrency(currentAgency.cyberSecurityBudget)}
                    </div>
                    <div className="text-xs text-stark-400">Cyber Budget</div>
                  </div>
                </div>
                <div className="jarvis-panel p-3">
                  <div className="text-center">
                    <div className="text-lg font-bold text-stark-300">
                      {formatCurrency(currentAgency.averageContractSize)}
                    </div>
                    <div className="text-xs text-stark-400">Avg Contract</div>
                  </div>
                </div>
                <div className="jarvis-panel p-3">
                  <div className="text-center">
                    <div className="text-lg font-bold text-warning">
                      {currentAgency.keyDecisionMakers.length}
                    </div>
                    <div className="text-xs text-stark-400">Key Contacts</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="mb-6">
              <div className="flex space-x-1 bg-stark-800/50 rounded-lg p-1">
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`
                    flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all duration-200
                    ${activeTab === 'overview'
                      ? 'bg-jarvis-500/20 text-jarvis-400'
                      : 'text-stark-400 hover:text-stark-200'
                    }
                  `}
                >
                  Agency Overview
                </button>
                <button
                  onClick={() => setActiveTab('contacts')}
                  className={`
                    flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all duration-200
                    ${activeTab === 'contacts'
                      ? 'bg-jarvis-500/20 text-jarvis-400'
                      : 'text-stark-400 hover:text-stark-200'
                    }
                  `}
                >
                  Decision Makers
                </button>
                <button
                  onClick={() => setActiveTab('contracts')}
                  className={`
                    flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all duration-200
                    ${activeTab === 'contracts'
                      ? 'bg-jarvis-500/20 text-jarvis-400'
                      : 'text-stark-400 hover:text-stark-200'
                    }
                  `}
                >
                  Contract History
                </button>
              </div>
            </div>

            {/* Tab Content */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Strategic Priorities */}
                <div className="intelligence-card">
                  <h3 className="font-semibold text-stark-100 mb-4">Strategic Priorities</h3>
                  <div className="space-y-3">
                    {currentAgency.strategicPriorities.map((priority, index) => (
                      <div key={index} className="flex items-start space-x-3">
                        <div className="w-6 h-6 bg-jarvis-500/20 text-jarvis-400 rounded-full flex items-center justify-center text-xs font-bold">
                          {index + 1}
                        </div>
                        <span className="text-stark-300">{priority}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recent Activity */}
                <div className="intelligence-card">
                  <h3 className="font-semibold text-stark-100 mb-4">Recent Activity</h3>
                  <div className="space-y-3">
                    {currentAgency.recentActivity.map((activity, index) => (
                      <div key={index} className="flex items-start space-x-3">
                        <ArrowTrendingUpIcon className="w-4 h-4 text-green-400 mt-1" />
                        <span className="text-stark-300 text-sm">{activity}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Preferred Vendor Profile */}
                <div className="intelligence-card">
                  <h3 className="font-semibold text-stark-100 mb-4">Preferred Vendor Profile</h3>
                  <p className="text-stark-300">{currentAgency.preferredVendorProfile}</p>
                </div>
              </div>
            )}

            {activeTab === 'contacts' && (
              <div className="space-y-4">
                {currentAgency.keyDecisionMakers.map((contact, index) => (
                  <div key={index} className="intelligence-card">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-semibold text-stark-100">{contact.name}</h3>
                        <p className="text-stark-400">{contact.title}</p>
                      </div>
                      <div className={`
                        inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
                        ${contact.influence === 'high' 
                          ? 'bg-red-400/20 text-red-400'
                          : contact.influence === 'medium'
                          ? 'bg-yellow-400/20 text-yellow-400'
                          : 'bg-green-400/20 text-green-400'
                        }
                      `}>
                        {contact.influence.toUpperCase()} INFLUENCE
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <h4 className="font-medium text-stark-200 text-sm mb-2">Background</h4>
                        <p className="text-stark-300 text-sm">{contact.background}</p>
                      </div>

                      <div>
                        <h4 className="font-medium text-stark-200 text-sm mb-2">Engagement History</h4>
                        <p className="text-stark-300 text-sm">{contact.contactHistory}</p>
                      </div>

                      <div>
                        <h4 className="font-medium text-stark-200 text-sm mb-2">Preferred Approach</h4>
                        <p className="text-stark-300 text-sm">{contact.preferredApproach}</p>
                      </div>

                      {(contact.email || contact.phone) && (
                        <div className="flex items-center space-x-4 pt-2 border-t border-stark-700/50">
                          {contact.email && (
                            <div className="flex items-center space-x-2 text-sm text-stark-400">
                              <EnvelopeIcon className="w-4 h-4" />
                              <span>{contact.email}</span>
                            </div>
                          )}
                          {contact.phone && (
                            <div className="flex items-center space-x-2 text-sm text-stark-400">
                              <PhoneIcon className="w-4 h-4" />
                              <span>{contact.phone}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'contracts' && (
              <div className="space-y-4">
                {currentAgency.recentContracts.map((contract, index) => (
                  <div key={index} className="intelligence-card">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-semibold text-stark-100">{contract.title}</h3>
                        <p className="text-stark-400">{formatCurrency(contract.value)}</p>
                      </div>
                      <div className="text-right">
                        <div className={`
                          inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mb-2
                          ${contract.status === 'your_win'
                            ? 'bg-green-400/20 text-green-400'
                            : contract.status === 'competitor_win'
                            ? 'bg-red-400/20 text-red-400'
                            : 'bg-blue-400/20 text-blue-400'
                          }
                        `}>
                          {contract.status === 'your_win' ? 'YOUR WIN' :
                           contract.status === 'competitor_win' ? 'COMPETITOR WIN' : 'UPCOMING'
                          }
                        </div>
                        <div className="text-sm text-stark-400">
                          {contract.date.toLocaleDateString()}
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium text-stark-200 text-sm mb-2">
                        {contract.status === 'upcoming' ? 'Key Requirements' : 'Success Factors'}
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {contract.keyFactors.map((factor, factorIndex) => (
                          <span
                            key={factorIndex}
                            className="px-2 py-1 text-xs bg-stark-700/50 text-stark-300 rounded"
                          >
                            {factor}
                          </span>
                        ))}
                      </div>
                    </div>

                    {contract.winner !== 'TBD' && (
                      <div className="mt-3 pt-3 border-t border-stark-700/50">
                        <div className="text-sm">
                          <span className="text-stark-400">Winner: </span>
                          <span className={`
                            font-medium
                            ${contract.winner === 'Your Company' ? 'text-green-400' : 'text-red-400'}
                          `}>
                            {contract.winner}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </DashboardLayout>
    </>
  )
}

export default CustomerIntelligence