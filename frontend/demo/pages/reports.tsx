import type { NextPage } from 'next'
import Head from 'next/head'
import { useState } from 'react'
import DashboardLayout from '../strategic-dashboard/DashboardLayout'
import { Chart, MetricCard, Badge } from '../shared-components'
import PolicyImpactAnalyzer from '../intelligence-panels/PolicyImpactAnalyzer'
import StrategicAdvisoryPanel from '../intelligence-panels/StrategicAdvisoryPanel'
import { 
  DocumentChartBarIcon,
  ArrowDownTrayIcon,
  CalendarDaysIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline'

const Reports: NextPage = () => {
  const [reportPeriod, setReportPeriod] = useState<'week' | 'month' | 'quarter'>('month')
  
  // Mock report data
  const reportMetrics = {
    week: {
      opportunities: 47,
      pipelineValue: 12400000,
      winRate: 68.5,
      averageDeal: 890000
    },
    month: {
      opportunities: 187,
      pipelineValue: 45600000,
      winRate: 71.2,
      averageDeal: 1200000
    },
    quarter: {
      opportunities: 542,
      pipelineValue: 157800000,
      winRate: 69.8,
      averageDeal: 1150000
    }
  }

  const currentMetrics = reportMetrics[reportPeriod]

  const performanceData = [
    { label: 'Q1 2024', value: currentMetrics.pipelineValue * 0.8, color: '#00D4FF' },
    { label: 'Q2 2024', value: currentMetrics.pipelineValue * 0.9, color: '#22C55E' },
    { label: 'Q3 2024', value: currentMetrics.pipelineValue, color: '#F59E0B' },
    { label: 'Q4 2024', value: currentMetrics.pipelineValue * 1.2, color: '#EF4444' }
  ]

  const winRateData = [
    { label: 'Jan', value: 65, color: '#00D4FF' },
    { label: 'Feb', value: 71, color: '#22C55E' },
    { label: 'Mar', value: 68, color: '#F59E0B' },
    { label: 'Apr', value: 73, color: '#EF4444' },
    { label: 'May', value: 69, color: '#8B5CF6' },
    { label: 'Jun', value: 75, color: '#06B6D4' }
  ]

  return (
    <>
      <Head>
        <title>Reports & Analytics - KBI Labs</title>
        <meta name="description" content="Business intelligence reports and performance analytics" />
      </Head>
      
      <DashboardLayout>
        {/* Page Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-stark-100">Reports & Analytics</h1>
              <p className="text-stark-400">Business intelligence reports and performance metrics</p>
            </div>
            <div className="flex items-center space-x-3">
              {/* Period Selector */}
              <div className="flex items-center space-x-2">
                <CalendarDaysIcon className="w-4 h-4 text-stark-400" />
                <select
                  value={reportPeriod}
                  onChange={(e) => setReportPeriod(e.target.value as 'week' | 'month' | 'quarter')}
                  className="bg-stark-800 border border-stark-600 rounded-lg px-3 py-2 text-sm text-stark-200 focus:border-jarvis-500 focus:outline-none"
                >
                  <option value="week">This Week</option>
                  <option value="month">This Month</option>
                  <option value="quarter">This Quarter</option>
                </select>
              </div>
              {/* Export Button */}
              <button className="btn-jarvis text-sm px-4 py-2 flex items-center space-x-2">
                <ArrowDownTrayIcon className="w-4 h-4" />
                <span>Export Report</span>
              </button>
            </div>
          </div>
        </div>

        {/* Executive Summary Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <MetricCard
            title="Active Opportunities"
            value={currentMetrics.opportunities}
            change={{ value: 15.2, type: 'percentage', period: `vs last ${reportPeriod}` }}
            trend="up"
            icon={<ChartBarIcon className="w-5 h-5" />}
            variant="jarvis"
          />
          <MetricCard
            title="Pipeline Value"
            value={currentMetrics.pipelineValue}
            change={{ value: 22.8, type: 'percentage', period: `vs last ${reportPeriod}` }}
            trend="up"
            icon={<CurrencyDollarIcon className="w-5 h-5" />}
            variant="success"
          />
          <MetricCard
            title="Win Rate"
            value={`${currentMetrics.winRate}%`}
            change={{ value: 3.2, type: 'absolute', period: 'percentage points' }}
            trend="up"
            icon={<ArrowTrendingUpIcon className="w-5 h-5" />}
            variant="success"
          />
          <MetricCard
            title="Average Deal Size"
            value={currentMetrics.averageDeal}
            change={{ value: 8.5, type: 'percentage', period: `vs last ${reportPeriod}` }}
            trend="up"
            icon={<CurrencyDollarIcon className="w-5 h-5" />}
            variant="default"
          />
        </div>

        {/* Performance Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="intelligence-card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-stark-100">Pipeline Performance</h2>
              <Badge variant="jarvis" size="sm">Quarterly View</Badge>
            </div>
            <Chart
              type="bar"
              data={performanceData}
              height={300}
              showGrid
              animate
            />
          </div>

          <div className="intelligence-card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-stark-100">Win Rate Trends</h2>
              <Badge variant="success" size="sm">6-Month Trend</Badge>
            </div>
            <Chart
              type="line"
              data={winRateData}
              height={300}
              showGrid
              animate
            />
          </div>
        </div>

        {/* Detailed Reports */}
        <div className="space-y-8">
          {/* Report Categories */}
          <div className="intelligence-card">
            <h2 className="text-lg font-semibold text-stark-100 mb-6">Available Reports</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                {
                  title: 'Executive Summary',
                  description: 'High-level business performance overview',
                  lastGenerated: '2 hours ago',
                  format: 'PDF'
                },
                {
                  title: 'Pipeline Analysis',
                  description: 'Detailed opportunity and forecast analysis',
                  lastGenerated: '1 day ago',
                  format: 'Excel'
                },
                {
                  title: 'Competitive Intelligence Report',
                  description: 'Market positioning and competitor analysis',
                  lastGenerated: '3 days ago',
                  format: 'PDF'
                },
                {
                  title: 'Customer Relationship Analysis',
                  description: 'Government agency engagement metrics',
                  lastGenerated: '1 week ago',
                  format: 'PDF'
                },
                {
                  title: 'Market Intelligence Briefing',
                  description: 'Federal market trends and opportunities',
                  lastGenerated: '2 days ago',
                  format: 'PowerPoint'
                },
                {
                  title: 'Strategic Advisory Summary',
                  description: 'Board-level strategic recommendations',
                  lastGenerated: '1 week ago',
                  format: 'PDF'
                }
              ].map((report, index) => (
                <div key={index} className="jarvis-panel p-4 hover:bg-stark-700/30 transition-colors duration-200">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-medium text-stark-100 text-sm">{report.title}</h3>
                    <Badge variant="outline" size="sm">{report.format}</Badge>
                  </div>
                  <p className="text-stark-400 text-xs mb-3">{report.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-stark-500">Updated {report.lastGenerated}</span>
                    <button className="text-xs text-jarvis-400 hover:text-jarvis-300 font-medium">
                      Generate
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Strategic Analysis */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div>
              <h2 className="text-lg font-semibold text-stark-100 mb-4">Strategic Advisory Analysis</h2>
              <StrategicAdvisoryPanel />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-stark-100 mb-4">Policy Impact Analysis</h2>
              <PolicyImpactAnalyzer />
            </div>
          </div>
        </div>
      </DashboardLayout>
    </>
  )
}

export default Reports