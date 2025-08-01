import React, { useState, useEffect } from 'react';

const SimpleTest = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('Fetching from API...');
        const response = await fetch('http://localhost:8001/api/v1/government-contractor/');
        console.log('Response status:', response.status);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Data received:', result);
        setData(result);
      } catch (err) {
        console.error('Error:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div className="p-8">Loading...</div>;
  if (error) return <div className="p-8 text-red-600">Error: {error}</div>;

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">API Connection Test - {new Date().toLocaleTimeString()}</h1>
      
      <div className="bg-green-100 p-4 rounded mb-4">
        <h2 className="font-semibold">✅ API Connected Successfully!</h2>
        <p>Companies loaded: {data?.realData?.totalCompanies || 'N/A'}</p>
        <p>Average investment score: {data?.realData?.avgInvestmentScore || 'N/A'}</p>
      </div>

      <div className="bg-gray-100 p-4 rounded">
        <h3 className="font-semibold mb-2">Raw API Response:</h3>
        <pre className="text-xs overflow-auto max-h-96">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </div>
  );
};

export default SimpleTest;