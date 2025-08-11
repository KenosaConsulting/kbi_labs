import type { NextPage } from 'next'
import Head from 'next/head'
import { useState } from 'react'
import DashboardLayout from '../strategic-dashboard/DashboardLayout'
import { Chart, MetricCard, Badge } from '../shared-components'
import { 
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CurrencyDollarIcon,
  BuildingLibraryIcon,
  BanknotesIcon,
  ChartBarIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'

interface MarketTrend {
  category: string
  current_value: number
  growth_rate: number
  forecast: number[]
  key_drivers: string[]
  risk_factors: string[]
}

interface AgencySpending {
  agency: string
  total_budget: number
  cyber_budget: number
  growth: number
  key_programs: string[]
  addressable_market: number
}

const mockMarketTrends: MarketTrend[] = [
  {
    category: 'Zero Trust Architecture',
    current_value: 2800000000,
    growth_rate: 34.5,
    forecast: [2800000000, 3200000000, 4100000000, 5200000000],
    key_drivers: [
      'Federal Zero Trust mandate deadline FY 2026',
      'Executive Order 14028 implementation',
      'CISA Zero Trust maturity model adoption',
      'Legacy system modernization requirements'
    ],
    risk_factors: [
      'Budget cuts due to fiscal constraints',
      'Implementation complexity delays',
      'Skills shortage for Zero Trust expertise'
    ]
  },
  {
    category: 'Cloud Security',
    current_value: 1900000000,
    growth_rate: 28.2,
    key_drivers: [
      'Cloud-first mandate expansion',
      'FedRAMP modernization requirements',
      'Multi-cloud security needs',
      'Container and serverless adoption'
    ],
    forecast: [1900000000, 2200000000, 2800000000, 3400000000],
    risk_factors: [
      'Vendor consolidation reducing competition',
      'Compliance complexity increases costs',
      'Skills gap in cloud security'
    ]
  },
  {
    category: 'AI/ML Security',
    current_value: 650000000,
    growth_rate: 67.8,
    forecast: [650000000, 950000000, 1450000000, 2100000000],
    key_drivers: [
      'AI Executive Order implementation',
      'DOD AI strategy requirements',
      'Responsible AI framework adoption',
      'AI supply chain security needs'
    ],
    risk_factors: [
      'Regulatory uncertainty',
      'Rapidly evolving threat landscape',
      'Limited proven solutions in market'
    ]
  },
  {
    category: 'Critical Infrastructure Protection',
    current_value: 1250000000,
    growth_rate: 22.1,
    forecast: [1250000000, 1420000000, 1650000000, 1950000000],
    key_drivers: [
      'Infrastructure Investment and Jobs Act funding',
      'State and local government initiatives',
      'Public-private partnership expansion',
      'Supply chain security focus'
    ],
    risk_factors: [
      'State budget constraints',
      'Complex multi-stakeholder coordination',
      'Long procurement cycles'
    ]
  }
]

const mockAgencySpending: AgencySpending[] = [
  {
    agency: 'Department of Defense',
    total_budget: 15600000000,
    cyber_budget: 3400000000,
    growth: 18.5,
    key_programs: ['Zero Trust Implementation', 'AI/ML Security', 'Cloud Security'],
    addressable_market: 890000000
  },
  {
    agency: 'Department of Energy',
    total_budget: 2100000000,
    cyber_budget: 450000000,
    growth: 25.2,
    key_programs: ['Grid Modernization', 'NERC CIP Compliance', 'OT Security'],
    addressable_market: 340000000
  },
  {
    agency: 'Department of Homeland Security',
    total_budget: 1890000000,
    cyber_budget: 890000000,
    growth: 15.8,
    key_programs: ['Critical Infrastructure', 'Incident Response', 'Threat Intel'],
    addressable_market: 234000000
  },
  {
    agency: 'Department of Treasury',
    total_budget: 980000000,
    cyber_budget: 180000000,
    growth: 31.4,
    key_programs: ['Financial Systems Security', 'Cloud Migration', 'Identity Management'],
    addressable_market: 145000000
  }
]

const MarketIntelligence: NextPage = () => {
  const [activeView, setActiveView] = useState<'trends' | 'agencies' | 'forecast'>('trends')
  
  const totalMarketSize = mockMarketTrends.reduce((sum, trend) => sum + trend.current_value, 0)
  const averageGrowth = mockMarketTrends.reduce((sum, trend) => sum + trend.growth_rate, 0) / mockMarketTrends.length
  const totalAddressableMarket = mockAgencySpending.reduce((sum, agency) => sum + agency.addressable_market, 0)

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000000) {
      return `$${(amount / 1000000000).toFixed(1)}B`
    } else if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(0)}M`
    } else {
      return `$${(amount / 1000).toFixed(0)}K`
    }
  }

  const renderTrendsView = () => (
    <div className="space-y-6">
      {mockMarketTrends.map((trend, index) => (
        <div key={index} className="intelligence-card">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-stark-100">{trend.category}</h3>
              <div className="flex items-center space-x-4 mt-2">
                <div className="text-2xl font-bold text-green-400">
                  {formatCurrency(trend.current_value)}
                </div>
                <div className="flex items-center space-x-1">
                  <ArrowTrendingUpIcon className="w-4 h-4 text-green-400" />
                  <span className="text-green-400 font-medium">{trend.growth_rate}% growth</span>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Forecast Chart */}
            <div>
              <h4 className="text-stark-200 font-medium mb-3">4-Year Forecast</h4>
              <Chart
                type="line"
                data={trend.forecast.map((value, i) => ({
                  label: `FY ${2024 + i}`,
                  value: value
                }))}
                height={200}
                showGrid
                animate
              />
            </div>

            {/* Key Drivers & Risks */}
            <div className="space-y-4">
              <div>
                <h4 className="text-stark-200 font-medium mb-2">Growth Drivers</h4>
                <div className="space-y-2">
                  {trend.key_drivers.map((driver, i) => (
                    <div key={i} className="flex items-start space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full mt-2 flex-shrink-0"></div>
                      <span className="text-stark-300 text-sm">{driver}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-stark-200 font-medium mb-2">Risk Factors</h4>
                <div className="space-y-2">
                  {trend.risk_factors.map((risk, i) => (
                    <div key={i} className="flex items-start space-x-2">
                      <div className="w-2 h-2 bg-amber-400 rounded-full mt-2 flex-shrink-0"></div>
                      <span className="text-stark-300 text-sm">{risk}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )

  const renderAgenciesView = () => (
    <div className="space-y-4">
      {mockAgencySpending.map((agency, index) => (
        <div key={index} className="intelligence-card">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-stark-100">{agency.agency}</h3>
              <div className="flex items-center space-x-4 mt-2">
                <div className="text-lg font-bold text-jarvis-400">
                  {formatCurrency(agency.cyber_budget)} cyber budget
                </div>
                <Badge variant="success">
                  +{agency.growth}% growth
                </Badge>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-stark-400">Your Addressable Market</div>
              <div className="text-xl font-bold text-green-400">
                {formatCurrency(agency.addressable_market)}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="jarvis-panel p-3">
              <div className="text-center">
                <div className="text-lg font-bold text-stark-200">
                  {formatCurrency(agency.total_budget)}
                </div>
                <div className="text-xs text-stark-400">Total IT Budget</div>
              </div>
            </div>
            <div className="jarvis-panel p-3">
              <div className="text-center">
                <div className="text-lg font-bold text-jarvis-400">
                  {Math.round((agency.cyber_budget / agency.total_budget) * 100)}%
                </div>
                <div className="text-xs text-stark-400">Cyber Share</div>
              </div>
            </div>
            <div className="jarvis-panel p-3">
              <div className="text-center">
                <div className="text-lg font-bold text-green-400">
                  {Math.round((agency.addressable_market / agency.cyber_budget) * 100)}%
                </div>
                <div className="text-xs text-stark-400">Market Share Potential</div>
              </div>
            </div>
          </div>

          <div className="mt-4">
            <h4 className="text-stark-200 font-medium mb-2">Key Programs</h4>
            <div className="flex flex-wrap gap-2">
              {agency.key_programs.map((program, i) => (
                <Badge key={i} variant="jarvis" size="sm">
                  {program}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  )

  const renderForecastView = () => (
    <div className="space-y-6">
      <div className="intelligence-card">
        <h3 className="text-lg font-semibold text-stark-100 mb-4">Market Size Evolution</h3>
        <Chart
          type="area"
          data={[
            { label: 'FY 2024', value: totalMarketSize, color: '#00D4FF' },
            { label: 'FY 2025', value: totalMarketSize * 1.25, color: '#22C55E' },
            { label: 'FY 2026', value: totalMarketSize * 1.55, color: '#F59E0B' },
            { label: 'FY 2027', value: totalMarketSize * 1.89, color: '#EF4444' }
          ]}
          height={300}
          showGrid
          animate
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="intelligence-card">
          <h3 className="text-lg font-semibold text-stark-100 mb-4">Growth by Category</h3>
          <Chart
            type="bar"
            data={mockMarketTrends.map(trend => ({
              label: trend.category.split(' ')[0],
              value: trend.growth_rate
            }))}
            height={250}
            showGrid={false}
            animate
          />
        </div>

        <div className="intelligence-card">
          <h3 className="text-lg font-semibold text-stark-100 mb-4">Market Insights</h3>
          <div className="space-y-4">
            <div className="jarvis-panel p-4">
              <h4 className="font-medium text-stark-200 mb-2">Fastest Growing Segment</h4>
              <div className="flex items-center space-x-2">
                <ArrowTrendingUpIcon className="w-5 h-5 text-green-400" />
                <span className="text-stark-300">AI/ML Security (+67.8%)</span>
              </div>
              <p className="text-xs text-stark-400 mt-2">
                Driven by AI Executive Order and DOD AI strategy requirements
              </p>
            </div>
            
            <div className="jarvis-panel p-4">
              <h4 className="font-medium text-stark-200 mb-2">Largest Market</h4>
              <div className="flex items-center space-x-2">
                <CurrencyDollarIcon className="w-5 h-5 text-jarvis-400" />
                <span className="text-stark-300">Zero Trust ({formatCurrency(2800000000)})</span>
              </div>
              <p className="text-xs text-stark-400 mt-2">
                Federal mandate creates sustained demand through FY 2026
              </p>
            </div>
            
            <div className="jarvis-panel p-4">
              <h4 className="font-medium text-stark-200 mb-2">Key Opportunity</h4>
              <div className="flex items-center space-x-2">
                <InformationCircleIcon className="w-5 h-5 text-blue-400" />
                <span className="text-stark-300">State & Local Funding</span>
              </div>
              <p className="text-xs text-stark-400 mt-2">
                Infrastructure bill creates $1.9B in new opportunities
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <>
      <Head>
        <title>Market Intelligence - KBI Labs</title>
        <meta name="description" content="Federal cybersecurity market intelligence and analysis" />
      </Head>
      
      <DashboardLayout>
        {/* Page Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-stark-100">Market Intelligence</h1>
          <p className="text-stark-400">Federal cybersecurity market analysis and forecasting</p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <MetricCard
            title="Total Market Size"
            value={totalMarketSize}
            change={{ value: averageGrowth, type: 'percentage', period: 'average growth' }}
            trend="up"
            icon={<CurrencyDollarIcon className="w-5 h-5" />}
            variant="success"
          />
          <MetricCard
            title="Addressable Market"
            value={totalAddressableMarket}
            change={{ value: 22.5, type: 'percentage', period: 'estimated growth' }}
            trend="up"
            icon={<BanknotesIcon className="w-5 h-5" />}
            variant="jarvis"
          />
          <MetricCard
            title="Monitored Agencies"
            value={mockAgencySpending.length}
            trend="stable"
            icon={<BuildingLibraryIcon className="w-5 h-5" />}
            variant="default"
          />
        </div>

        {/* Navigation Tabs */}
        <div className="mb-6">
          <div className="flex space-x-1 bg-stark-800/50 rounded-lg p-1">
            <button
              onClick={() => setActiveView('trends')}
              className={`
                flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all duration-200
                ${activeView === 'trends'
                  ? 'bg-jarvis-500/20 text-jarvis-400'
                  : 'text-stark-400 hover:text-stark-200'
                }
              `}
            >
              Market Trends
            </button>
            <button
              onClick={() => setActiveView('agencies')}
              className={`
                flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all duration-200
                ${activeView === 'agencies'
                  ? 'bg-jarvis-500/20 text-jarvis-400'
                  : 'text-stark-400 hover:text-stark-200'
                }
              `}
            >
              Agency Spending
            </button>
            <button
              onClick={() => setActiveView('forecast')}
              className={`
                flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all duration-200
                ${activeView === 'forecast'
                  ? 'bg-jarvis-500/20 text-jarvis-400'
                  : 'text-stark-400 hover:text-stark-200'
                }
              `}
            >
              Market Forecast
            </button>
          </div>
        </div>

        {/* Dynamic Content */}
        {activeView === 'trends' && renderTrendsView()}
        {activeView === 'agencies' && renderAgenciesView()}
        {activeView === 'forecast' && renderForecastView()}
      </DashboardLayout>
    </>
  )
}

export default MarketIntelligence