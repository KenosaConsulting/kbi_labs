const API_BASE_URL = 'http://localhost:8001/api/v1';

class APIService {
  async getCompanies(page = 1, limit = 20, search = '') {
    try {
      const offset = (page - 1) * limit;
      const url = `${API_BASE_URL}/companies?offset=${offset}&limit=${limit}${search ? `&search=${search}` : ''}`;
      
      console.log('🔄 Fetching companies from:', url);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        mode: 'cors'
      });
      
      console.log('📡 Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('📊 Companies data received:', data);
      return data;
    } catch (error) {
      console.error('❌ Error fetching companies:', error);
      throw error;
    }
  }

  async getCompanyDetails(id) {
    try {
      const response = await fetch(`${API_BASE_URL}/companies/${id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching company details:', error);
      throw error;
    }
  }

  async getAnalytics() {
    try {
      console.log('🔄 Fetching analytics from:', `${API_BASE_URL}/analytics`);
      const response = await fetch(`${API_BASE_URL}/analytics`);
      console.log('📡 Analytics response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('📊 Analytics data received:', data);
      return data;
    } catch (error) {
      console.error('❌ Error fetching analytics:', error);
      throw error;
    }
  }

  async getKPIs() {
    try {
      const response = await fetch(`${API_BASE_URL}/kpis`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching KPIs:', error);
      return {
        totalCompanies: 0,
        totalRevenue: 0,
        avgKBIScore: 0,
        activeDeals: 0
      };
    }
  }

  async getMarketIntelligence() {
    try {
      const response = await fetch(`${API_BASE_URL}/market-intelligence`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching market intelligence:', error);
      // Return null to trigger mock data
      return null;
    }
  }

  async getGovernmentContractorData() {
    try {
      const response = await fetch(`${API_BASE_URL}/government-contractor`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching government contractor data:', error);
      // Return null to use default data in component
      return null;
    }
  }
}

export default new APIService();
