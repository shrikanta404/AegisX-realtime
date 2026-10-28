import { useEffect, useRef } from "react";

export function usePolling(
  callback: () => void | Promise<void>,
  intervalMs: number,
  enabled = true,
): void {
  const callbackRef = useRef(callback);
  const runningRef = useRef(false);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled) return;

    const tick = async () => {
      if (runningRef.current) return;
      runningRef.current = true;
      try {
        await callbackRef.current();
      } finally {
        runningRef.current = false;
      }
    };

    const timer = window.setInterval(() => void tick(), intervalMs);
    return () => window.clearInterval(timer);
  }, [intervalMs, enabled]);
}
