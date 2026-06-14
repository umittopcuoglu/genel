'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, ApiRequestError } from './api';

interface UseApiDataOptions<T> {
  path: string;
  fallback?: T;
  enabled?: boolean;
  responseKey?: string; // For nested responses like { data: [...] }
}

interface UseApiDataResult<T> {
  data: T;
  loading: boolean;
  error: string | null;
  usingFallback: boolean;
  refetch: () => void;
}

/**
 * Generic hook for API data fetching with fallback to mock data.
 *
 * Usage:
 *   const { data, loading, error, usingFallback } = useApiData({
 *     path: '/api/v1/reservations',
 *     fallback: MOCK_RESERVATIONS,
 *     responseKey: 'data', // for paginated responses
 *   });
 */
export function useApiData<T>({
  path,
  fallback,
  enabled = true,
  responseKey,
}: UseApiDataOptions<T>): UseApiDataResult<T> {
  const [data, setData] = useState<T>(fallback as T);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);
  const [usingFallback, setUsingFallback] = useState(false);

  const fetchData = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api<any>(path);
      const result = responseKey ? response[responseKey] : response;
      setData(result);
      setUsingFallback(false);
    } catch (err) {
      console.warn(`API call to ${path} failed:`, err);
      if (fallback !== undefined) {
        setData(fallback);
        setUsingFallback(true);
      }
      if (err instanceof ApiRequestError && err.status !== 0) {
        setError(`API hatası (${err.status}): ${err.message}`);
      } else {
        // 0 status = network/connection error → silently use fallback
        setError(null);
      }
    } finally {
      setLoading(false);
    }
  }, [path, responseKey, enabled, fallback]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    usingFallback,
    refetch: fetchData,
  };
}
