import type { NextPage } from 'next'
import Head from 'next/head'
import DashboardLayout from '../strategic-dashboard/DashboardLayout'
import PipelineForecastPanel from '../intelligence-panels/PipelineForecastPanel'

const PipelineForecast: NextPage = () => {
  return (
    <>
      <Head>
        <title>Pipeline Forecast - KBI Labs</title>
        <meta name="description" content="Revenue pipeline forecasting and opportunity analysis" />
      </Head>
      
      <DashboardLayout>
        {/* Page Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-stark-100">Pipeline Forecast</h1>
          <p className="text-stark-400">Revenue forecasting and opportunity pipeline analysis</p>
        </div>

        {/* Full Pipeline Forecast Panel */}
        <div className="max-w-none">
          <PipelineForecastPanel />
        </div>
      </DashboardLayout>
    </>
  )
}

export default PipelineForecast