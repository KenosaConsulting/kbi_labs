import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import { SWRConfig } from 'swr';
import { Toaster } from 'react-hot-toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Components
import Dashboard from './pages/Dashboard';
import Companies from './pages/Companies';
import CompanyDetails from './pages/CompanyDetails';
import Analytics from './pages/Analytics';
import MarketIntelligence from './pages/MarketIntelligence';
import GovernmentContractorDashboard from './pages/GovernmentContractorDashboard';
import SimpleTest from './pages/SimpleTest';

// Styles
import './index.css';

const queryClient = new QueryClient();

const Navigation = () => {
  const navigate = useNavigate();
  const [currentView, setCurrentView] = useState('dashboard');

  const handleNavigation = (view, path) => {
    setCurrentView(view);
    navigate(path);
  };

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-indigo-600">KBI Labs</h1>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <button
                onClick={() => handleNavigation('dashboard', '/')}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  currentView === 'dashboard'
                    ? 'border-indigo-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => handleNavigation('companies', '/companies')}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  currentView === 'companies'
                    ? 'border-indigo-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                Companies
              </button>
              <button
                onClick={() => handleNavigation('analytics', '/analytics')}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  currentView === 'analytics'
                    ? 'border-indigo-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                Analytics
              </button>
              <button
                onClick={() => handleNavigation('market', '/market')}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  currentView === 'market'
                    ? 'border-indigo-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                Market Intelligence
              </button>
              <button
                onClick={() => handleNavigation('govcon', '/government-contractor')}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  currentView === 'govcon'
                    ? 'border-indigo-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                GovCon Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SWRConfig value={{ revalidateOnFocus: false }}>
        <Router>
          <div className="min-h-screen bg-gray-50">
            <Toaster position="top-right" />
            <Navigation />
            
            <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/companies" element={<Companies />} />
                <Route path="/companies/:id" element={<CompanyDetails />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/market" element={<MarketIntelligence />} />
                <Route path="/government-contractor" element={<GovernmentContractorDashboard />} />
                <Route path="/test" element={<SimpleTest />} />
              </Routes>
            </main>
          </div>
        </Router>
      </SWRConfig>
    </QueryClientProvider>
  );
}

export default App;
