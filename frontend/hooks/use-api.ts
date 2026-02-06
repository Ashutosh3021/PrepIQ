import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';

interface UseApiOptions<T> {
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  loadingMessage?: string;
  errorMessage?: string;
}

interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  execute: () => Promise<void>;
  setData: (data: T | null) => void;
  setError: (error: Error | null) => void;
  setLoading: (loading: boolean) => void;
}

export function useApi<T>(
  apiCall: () => Promise<T>,
  options: UseApiOptions<T> = {}
): UseApiReturn<T> {
  const {
    immediate = true,
    onSuccess,
    onError,
    loadingMessage = 'Loading...',
    errorMessage = 'Failed to load data'
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await apiCall();
      setData(result);
      
      if (onSuccess) {
        onSuccess(result);
      }
    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error('An unknown error occurred');
      setError(errorObj);
      
      if (onError) {
        onError(errorObj);
      } else {
        toast.error(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }, [apiCall, onSuccess, onError, errorMessage]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return {
    data,
    loading,
    error,
    execute,
    setData,
    setError,
    setLoading
  };
}

// Specialized hooks for common operations
export function useApiMutation<T, P = void>(
  apiCall: (params: P) => Promise<T>,
  options: Omit<UseApiOptions<T>, 'immediate'> = {}
) {
  return useApi<T>(() => apiCall(undefined as P), { ...options, immediate: false });
}

export function usePaginatedApi<T>(
  apiCall: (page: number, limit: number) => Promise<T[]>,
  initialPage = 1,
  limit = 10
) {
  const [page, setPage] = useState(initialPage);
  const [hasMore, setHasMore] = useState(true);
  const [allData, setAllData] = useState<T[]>([]);

  const { data, loading, error, execute, setData } = useApi<T[]>(
    () => apiCall(page, limit),
    {
      immediate: false,
      onSuccess: (newData) => {
        if (newData.length < limit) {
          setHasMore(false);
        }
        setAllData(prev => page === 1 ? newData : [...prev, ...newData]);
      }
    }
  );

  const loadMore = useCallback(() => {
    if (hasMore && !loading) {
      setPage(prev => prev + 1);
    }
  }, [hasMore, loading]);

  const refresh = useCallback(() => {
    setPage(1);
    setHasMore(true);
    setAllData([]);
    execute();
  }, [execute]);

  useEffect(() => {
    if (page > 1) {
      execute();
    }
  }, [page, execute]);

  return {
    data: allData,
    loading,
    error,
    hasMore,
    loadMore,
    refresh,
    page,
    setData
  };
}

export default useApi;