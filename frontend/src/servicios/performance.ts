export interface ResumenRendimientoCliente {
  domContentLoadedMs: number | null;
  loadEventMs: number | null;
  transferKb: number | null;
  registradoEn: string;
}

const KEY_PERF = 'perf.dashboard.resumen';

export function capturarRendimientoCliente(): ResumenRendimientoCliente | null {
  if (typeof window === 'undefined' || !('performance' in window)) return null;

  const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
  if (!nav) return null;

  const resumen: ResumenRendimientoCliente = {
    domContentLoadedMs: Number.isFinite(nav.domContentLoadedEventEnd)
      ? Math.round(nav.domContentLoadedEventEnd)
      : null,
    loadEventMs: Number.isFinite(nav.loadEventEnd) ? Math.round(nav.loadEventEnd) : null,
    transferKb: Number.isFinite(nav.transferSize) ? Math.round(nav.transferSize / 1024) : null,
    registradoEn: new Date().toISOString(),
  };

  window.sessionStorage.setItem(KEY_PERF, JSON.stringify(resumen));
  return resumen;
}

export function leerRendimientoCliente(): ResumenRendimientoCliente | null {
  if (typeof window === 'undefined') return null;
  const raw = window.sessionStorage.getItem(KEY_PERF);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as ResumenRendimientoCliente;
  } catch {
    return null;
  }
}
