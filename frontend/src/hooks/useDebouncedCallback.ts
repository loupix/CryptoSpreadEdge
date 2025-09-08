import { useRef, useCallback, useEffect } from 'react';

export function useDebouncedCallback<T extends (...args: any[]) => void>(fn: T, delayMs: number) {
  const timeoutRef = useRef<number | null>(null);
  const fnRef = useRef<T>(fn);
  fnRef.current = fn;

  const cancel = useCallback(() => {
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  useEffect(() => cancel, [cancel]);

  const debounced = useCallback((...args: Parameters<T>) => {
    cancel();
    timeoutRef.current = window.setTimeout(() => {
      fnRef.current(...args);
    }, delayMs);
  }, [delayMs, cancel]);

  return { debounced, cancel } as const;
}

