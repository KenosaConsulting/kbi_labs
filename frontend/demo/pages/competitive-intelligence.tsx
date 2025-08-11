import type { NextPage } from 'next'
import Head from 'next/head'
import DashboardLayout from '../strategic-dashboard/DashboardLayout'
import CompetitiveIntelPanel from '../intelligence-panels/CompetitiveIntelPanel'

const CompetitiveIntelligence: NextPage = () => {
  return (
    <>
      <Head>
        <title>Competitive Intelligence - KBI Labs</title>
        <meta name="description" content="Competitor analysis and threat assessment" />
      </Head>
      
      <DashboardLayout>
        {/* Page Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-stark-100">Competitive Intelligence</h1>
          <p className="text-stark-400">Real-time competitor analysis and threat assessment</p>
        </div>

        {/* Full Competitive Intelligence Panel */}
        <div className="max-w-none">
          <CompetitiveIntelPanel />
        </div>
      </DashboardLayout>
    </>
  )
}

export default CompetitiveIntelligence