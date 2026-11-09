import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../services/api";

const DEFAULT_INTERVAL_MS = 5000;

/**
 * Carga datos y los refresca solos. Sin `intervalMs` (0) solo carga al cambiar `deps`.
 * Si una respuesta llega después de que cambiaron los filtros, se descarta.
 */
export function usePolling<T>(fetcher: () => Promise<T>, deps: unknown[] = [], intervalMs = DEFAULT_INTERVAL_MS) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;
  const requestId = useRef(0);

  const reload = useCallback(async () => {
    const id = ++requestId.current;
    try {
      const result = await fetcherRef.current();
      if (id !== requestId.current) return;
      setData(result);
      setError(null);
    } catch (err) {
      if (id !== requestId.current) return;
      setError(err instanceof ApiError ? err.message : "No se pudo conectar con el servidor");
    } finally {
      if (id === requestId.current) setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    setIsLoading(true);
    void reload();
    if (!intervalMs) return;

    const timer = setInterval(() => {
      if (!document.hidden) void reload();
    }, intervalMs);
    return () => clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, intervalMs]);

  return { data, error, isLoading, reload };
}
