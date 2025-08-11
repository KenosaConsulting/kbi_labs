import { ReactNode } from 'react'
import { 
  ChartBarIcon, 
  ShieldCheckIcon, 
  ArrowTrendingUpIcon,
  BellIcon,
  CogIcon,
  HomeIcon,
  UsersIcon,
  DocumentChartBarIcon
} from '@heroicons/react/24/outline'

interface DashboardLayoutProps {
  children: ReactNode
}

const navigation = [
  { name: 'Strategic Dashboard', href: '/', icon: HomeIcon, current: true },
  { name: 'Market Intelligence', href: '/market-intelligence', icon: ChartBarIcon, current: false },
  { name: 'Competitive Intel', href: '/competitive-intelligence', icon: ShieldCheckIcon, current: false },
  { name: 'Pipeline Forecast', href: '/pipeline-forecast', icon: ArrowTrendingUpIcon, current: false },
  { name: 'Customer Intelligence', href: '/customers', icon: UsersIcon, current: false },
  { name: 'Reports & Analytics', href: '/reports', icon: DocumentChartBarIcon, current: false },
]

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-stark-900">
      {/* Navigation Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-stark-800/50 backdrop-blur-sm border-r border-stark-700/50">
        {/* Logo/Header */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-stark-700/50">
          <div className="flex items-center space-x-3">
            {/* KBI Labs Icon */}
            <div className="w-8 h-8 bg-gradient-to-br from-jarvis-500 to-arc-reactor rounded-lg flex items-center justify-center">
              <div className="w-4 h-4 bg-stark-900 rounded-full flex items-center justify-center">
                <div className="w-2 h-2 bg-jarvis-500 rounded-full"></div>
              </div>
            </div>
            <div>
              <h1 className="text-lg font-bold gradient-text">KBI Labs</h1>
              <p className="text-xs text-stark-400">Strategic Intelligence</p>
            </div>
          </div>
          
          {/* Notification Bell */}
          <button className="p-2 text-stark-400 hover:text-jarvis-500 rounded-lg hover:bg-stark-700/50 transition-colors">
            <BellIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Menu */}
        <nav className="mt-6 px-3">
          <div className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon
              return (
                <a
                  key={item.name}
                  href={item.href}
                  className={`
                    group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors
                    ${item.current
                      ? 'bg-jarvis-500/20 text-jarvis-400 border-r-2 border-jarvis-500'
                      : 'text-stark-300 hover:text-stark-100 hover:bg-stark-700/50'
                    }
                  `}
                >
                  <Icon className="mr-3 h-5 w-5 flex-shrink-0" />
                  {item.name}
                </a>
              )
            })}
          </div>
        </nav>

        {/* System Status */}
        <div className="absolute bottom-6 left-3 right-3">
          <div className="jarvis-panel p-4 space-y-3">
            <h3 className="text-sm font-semibold text-stark-300">System Status</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-stark-400">Government APIs</span>
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span className="text-green-400">Online</span>
                </div>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-stark-400">AI Analysis</span>
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span className="text-green-400">Active</span>
                </div>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-stark-400">Data Freshness</span>
                <span className="text-stark-300">&lt; 5 min</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="pl-64">
        {/* Top Header */}
        <header className="h-16 bg-stark-800/30 backdrop-blur-sm border-b border-stark-700/50 flex items-center justify-between px-6">
          <div>
            <h1 className="text-xl font-semibold text-stark-100">Strategic Intelligence Dashboard</h1>
            <p className="text-sm text-stark-400">Real-time government contracting intelligence</p>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Current Time */}
            <div className="text-right">
              <div className="text-sm font-medium text-stark-100">
                {new Date().toLocaleTimeString('en-US', { 
                  hour: '2-digit', 
                  minute: '2-digit',
                  timeZoneName: 'short'
                })}
              </div>
              <div className="text-xs text-stark-400">
                {new Date().toLocaleDateString('en-US', { 
                  weekday: 'long',
                  month: 'short',
                  day: 'numeric'
                })}
              </div>
            </div>

            {/* User Profile */}
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-jarvis-500 to-arc-reactor rounded-full flex items-center justify-center text-stark-900 text-sm font-bold">
                SK
              </div>
              <div>
                <div className="text-sm font-medium text-stark-100">Sarah Kim</div>
                <div className="text-xs text-stark-400">CEO, CyberSecure Solutions</div>
              </div>
            </div>

            {/* Settings */}
            <button className="p-2 text-stark-400 hover:text-jarvis-500 rounded-lg hover:bg-stark-700/50 transition-colors">
              <CogIcon className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Main Content */}
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  )
}