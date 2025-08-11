import type { NextPage } from 'next'
import Head from 'next/head'
import { useState, useEffect } from 'react'
import DashboardLayout from '../strategic-dashboard/DashboardLayout'
import CriticalIntelligenceBar from '../strategic-dashboard/CriticalIntelligenceBar'
import StrategicInsightCard from '../strategic-dashboard/StrategicInsightCard'
import MarketIntelligenceWidget from '../strategic-dashboard/MarketIntelligenceWidget'
import CompetitiveIntelPanel from '../intelligence-panels/CompetitiveIntelPanel'
import PipelineForecastPanel from '../intelligence-panels/PipelineForecastPanel'
import StrategicAdvisoryPanel from '../intelligence-panels/StrategicAdvisoryPanel'
import PolicyImpactAnalyzer from '../intelligence-panels/PolicyImpactAnalyzer'
import { LoadingSpinner, MetricCard, Chart, JarvisAlert } from '../shared-components'
import { 
  CurrencyDollarIcon, 
  ArrowTrendingUpIcon, 
  UserGroupIcon, 
  BuildingOfficeIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

const Home: NextPage = () => {
  const [isLoading, setIsLoading] = useState(true)
  const [showWelcomeAlert, setShowWelcomeAlert] = useState(true)

  useEffect(() => {
    // Simulate initial data loading
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, 1500)
    
    return () => clearTimeout(timer)
  }, [])

  // Mock data for enhanced dashboard metrics
  const kpiData = [
    { label: 'Q1', value: 15400000, color: '#00D4FF' },
    { label: 'Q2', value: 18200000, color: '#22C55E' },
    { label: 'Q3', value: 22100000, color: '#F59E0B' },
    { label: 'Q4', value: 19800000, color: '#EF4444' }
  ]

  if (isLoading) {
    return <LoadingScreen />
  }

  return (
    <>
      <Head>
        <title>KBI Labs - Strategic Intelligence Platform</title>
        <meta name="description" content="AI-Powered Strategic Intelligence for Government Contractors - Jarvis for GovCon" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <DashboardLayout>
        {/* Welcome Alert */}
        {showWelcomeAlert && (
          <div className="mb-6">
            <JarvisAlert
              title="Strategic Intelligence System Online"
              message="Welcome to your KBI Labs command center. All intelligence systems are operational and monitoring 247 government opportunities across 15 agencies."
              actions={[
                {
                  label: 'View Today\'s Opportunities',
                  onClick: () => console.log('Navigate to opportunities'),
                  variant: 'primary'
                },
                {
                  label: 'Customize Dashboard',
                  onClick: () => console.log('Open settings'),
                  variant: 'secondary'
                }
              ]}
              onDismiss={() => setShowWelcomeAlert(false)}
            />
          </div>
        )}

        {/* Critical Intelligence Bar - Always Visible */}
        <div className="mb-6">
          <CriticalIntelligenceBar />
        </div>

        {/* Executive KPI Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <MetricCard
            title="Pipeline Value"
            value={75400000}
            change={{ value: 18.5, type: 'percentage', period: 'vs last quarter' }}
            trend="up"
            icon={<CurrencyDollarIcon className="w-5 h-5" />}
            variant="success"
          />
          <MetricCard
            title="Active Opportunities"
            value={247}
            change={{ value: 12, type: 'absolute', period: 'this week' }}
            trend="up"
            icon={<ArrowTrendingUpIcon className="w-5 h-5" />}
            variant="jarvis"
          />
          <MetricCard
            title="Key Relationships"
            value={89}
            change={{ value: 3, type: 'absolute', period: 'new contacts' }}
            trend="up"
            icon={<UserGroupIcon className="w-5 h-5" />}
            variant="default"
          />
          <MetricCard
            title="Target Agencies"
            value={15}
            change={{ value: 0, type: 'absolute', period: 'monitored' }}
            trend="stable"
            icon={<BuildingOfficeIcon className="w-5 h-5" />}
            variant="default"
          />
        </div>

        {/* Main Dashboard Grid */}
        <div className="space-y-6">
          {/* Strategic Insights Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            <div className="xl:col-span-2">
              <StrategicInsightCard />
            </div>
            <div>
              <MarketIntelligenceWidget />
            </div>
          </div>

          {/* Revenue Trend Visualization */}
          <div className="intelligence-card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-stark-100">Quarterly Revenue Pipeline</h2>
                <p className="text-sm text-stark-400">Contract value tracking by quarter</p>
              </div>
              <ChartBarIcon className="w-5 h-5 text-jarvis-400" />
            </div>
            <Chart
              type="area"
              data={kpiData}
              height={300}
              showGrid
              animate
            />
          </div>

          {/* Intelligence Panels Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            <CompetitiveIntelPanel />
            <PipelineForecastPanel />
            <StrategicAdvisoryPanel />
          </div>

          {/* Policy Impact Analysis Row */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="xl:col-span-2">
              <PolicyImpactAnalyzer />
            </div>
          </div>
        </div>
      </DashboardLayout>
    </>
  )
}

const LoadingScreen = () => {
  return (
    <div className="min-h-screen bg-stark-900 flex items-center justify-center">
      <div className="text-center space-y-6">
        {/* KBI Labs Logo/Icon */}
        <div className="w-20 h-20 mx-auto bg-gradient-to-br from-jarvis-500 to-arc-reactor rounded-lg flex items-center justify-center">
          <div className="w-10 h-10 bg-stark-900 rounded-full flex items-center justify-center">
            <div className="w-6 h-6 bg-jarvis-500 rounded-full jarvis-glow"></div>
          </div>
        </div>
        
        {/* Loading Text */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold gradient-text">KBI Labs</h1>
          <p className="text-stark-400 text-lg">Strategic Intelligence Platform</p>
          <p className="text-stark-500 text-sm">Jarvis for Government Contractors</p>
        </div>
        
        {/* Enhanced Loading Animation */}
        <div className="space-y-4">
          <LoadingSpinner size="lg" text="Initializing intelligence systems..." />
          
          {/* Loading Steps */}
          <div className="text-xs text-stark-500 space-y-1">
            <div className="flex items-center justify-center space-x-2">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
              <span>Connecting to government databases</span>
            </div>
            <div className="flex items-center justify-center space-x-2">
              <div className="w-1.5 h-1.5 bg-jarvis-500 rounded-full animate-pulse"></div>
              <span>Loading strategic intelligence modules</span>
            </div>
            <div className="flex items-center justify-center space-x-2">
              <div className="w-1.5 h-1.5 bg-stark-600 rounded-full"></div>
              <span>Preparing dashboard analytics</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home