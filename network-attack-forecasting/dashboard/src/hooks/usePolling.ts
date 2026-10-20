import { useEffect, useRef, useState, useCallback } from 'react';

export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number = 10000,
  enabled: boolean = true
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const timerRef = useRef<number | null>(null);

  const executeFetch = useCallback(
    async (isManual: boolean = false) => {
      if (isManual) {
        setIsRefreshing(true);
      }
      try {
        const result = await fetcher();
        setData(result);
        setError(null);
        setLastUpdated(new Date());
      } catch (err: any) {
        setError(err?.message || 'Failed to fetch telemetry data');
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [fetcher]
  );

  useEffect(() => {
    executeFetch(false);

    if (enabled && intervalMs > 0) {
      timerRef.current = window.setInterval(() => {
        executeFetch(false);
      }, intervalMs);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [executeFetch, intervalMs, enabled]);

  const refresh = useCallback(() => {
    return executeFetch(true);
  }, [executeFetch]);

  return { data, isLoading, isRefreshing, error, lastUpdated, refresh, setData };
}
