import { useState, useEffect } from 'react';
import useSWR from 'swr';
import api from '../services/api';
import config from '../config';

export function useCompanies(filters = {}) {
  const key = `/companies?${new URLSearchParams(filters).toString()}`;
  
  const { data, error, mutate, isLoading } = useSWR(
    key,
    () => api.getCompanies(filters),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      dedupingInterval: config.cache.durations.companies,
      refreshInterval: config.features.realTimeUpdates ? 30000 : 0
    }
  );

  return {
    companies: data?.companies || [],
    totalCount: data?.totalCount || 0,
    isLoading,
    isError: error,
    refresh: mutate
  };
}

export function useAnalytics() {
  const { data, error, isLoading } = useSWR(
    '/analytics',
    () => api.getAnalytics(),
    {
      revalidateOnFocus: false,
      dedupingInterval: 60000 // 1 minute
    }
  );

  return {
    analytics: data || {
      totalCompanies: 0,
      totalRevenue: "$0M",
      totalContracts: 0,
      stateCount: 0
    },
    isLoading,
    isError: error
  };
}

export function useCompany(id) {
  const { data, error, mutate, isLoading } = useSWR(
    id ? `/companies/${id}` : null,
    () => api.getCompany(id),
    {
      revalidateOnFocus: false,
      dedupingInterval: config.cache.durations.companies
    }
  );

  const enrichCompany = async () => {
    try {
      const enrichedData = await api.enrichCompany(id);
      mutate(enrichedData, false);
      return enrichedData;
    } catch (error) {
      console.error('Failed to enrich company:', error);
      throw error;
    }
  };

  return {
    company: data,
    isLoading,
    isError: error,
    refresh: mutate,
    enrichCompany
  };
}

export function useCompanySearch(query, options = {}) {
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (!query || query.length < 2) {
      setResults([]);
      return;
    }

    const searchTimeout = setTimeout(async () => {
      setIsSearching(true);
      try {
        const data = await api.search(query, {
          type: 'company',
          ...options
        });
        setResults(data.results || []);
      } catch (error) {
        console.error('Search failed:', error);
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300); // Debounce search

    return () => clearTimeout(searchTimeout);
  }, [query, options]);

  return { results, isSearching };
}
