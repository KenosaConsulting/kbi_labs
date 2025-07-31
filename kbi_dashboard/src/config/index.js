// KBI Labs Frontend Configuration
export const config = {
  // API Configuration
  api: {
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:3001/api',
    wsURL: import.meta.env.VITE_WS_URL || 'ws://localhost:3001',
    timeout: 30000,
    retryAttempts: 3,
    retryDelay: 1000
  },

  // Feature Flags
  features: {
    aiInsights: import.meta.env.VITE_ENABLE_AI_INSIGHTS === 'true',
    realTimeUpdates: import.meta.env.VITE_ENABLE_REAL_TIME === 'true',
    scenarioPlanning: true,
    bulkOperations: true,
    naturalLanguageSearch: true,
    advancedAnalytics: true
  },

  // Cache Configuration
  cache: {
    enabled: true,
    defaultTTL: 300000, // 5 minutes
    maxSize: 100,
    strategy: 'LRU',
    durations: {
      companies: 600000, // 10 minutes
      kpis: 60000, // 1 minute
      marketData: 300000, // 5 minutes
      aiInsights: 30000 // 30 seconds
    }
  },

  // UI Configuration
  ui: {
    theme: {
      colors: {
        primary: '#2563eb',
        secondary: '#7c3aed',
        success: '#16a34a',
        warning: '#f59e0b',
        error: '#dc2626',
        ai: '#a855f7'
      },
      animations: {
        enabled: true,
        duration: 300
      }
    },
    table: {
      defaultPageSize: 20,
      pageSizeOptions: [10, 20, 50, 100]
    },
    chart: {
      defaultHeight: 300,
      colors: ['#2563eb', '#7c3aed', '#16a34a', '#f59e0b', '#dc2626']
    }
  },

  // User Segments
  segments: {
    PE_INVESTOR: 'pe_investor',
    SMB_OWNER: 'smb_owner',
    CONSULTANT: 'consultant'
  },

  // Data Sources
  dataSources: {
    clearbit: {
      enabled: true,
      rateLimit: 600 // per minute
    },
    fullContact: {
      enabled: true,
      rateLimit: 300
    },
    pitchbook: {
      enabled: true,
      rateLimit: 100
    },
    linkedin: {
      enabled: true,
      rateLimit: 100
    }
  }
};

export default config;
