const KEY_VISITOR_ID = 'public.visitor.id';
const KEY_VISITOR_METRICS = 'public.visitor.metrics';

export interface MetricasVisitante {
  visitorId: string;
  vistasLanding: number;
  ingresosCentro: number;
  ultimoAccesoIso: string;
}

function generarIdVisitante(): string {
  return `visit_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

export function obtenerVisitorId(): string {
  if (typeof window === 'undefined') return 'visit_server';
  const existente = window.localStorage.getItem(KEY_VISITOR_ID);
  if (existente) return existente;
  const id = generarIdVisitante();
  window.localStorage.setItem(KEY_VISITOR_ID, id);
  return id;
}

export function obtenerMetricasVisitante(): MetricasVisitante {
  const visitorId = obtenerVisitorId();
  if (typeof window === 'undefined') {
    return { visitorId, vistasLanding: 0, ingresosCentro: 0, ultimoAccesoIso: new Date().toISOString() };
  }

  const raw = window.localStorage.getItem(KEY_VISITOR_METRICS);
  if (!raw) {
    return { visitorId, vistasLanding: 0, ingresosCentro: 0, ultimoAccesoIso: new Date().toISOString() };
  }

  try {
    const parsed = JSON.parse(raw) as Omit<MetricasVisitante, 'visitorId'>;
    return {
      visitorId,
      vistasLanding: Number(parsed.vistasLanding ?? 0),
      ingresosCentro: Number(parsed.ingresosCentro ?? 0),
      ultimoAccesoIso: String(parsed.ultimoAccesoIso ?? new Date().toISOString()),
    };
  } catch {
    return { visitorId, vistasLanding: 0, ingresosCentro: 0, ultimoAccesoIso: new Date().toISOString() };
  }
}

function guardar(metricas: Omit<MetricasVisitante, 'visitorId'>): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(KEY_VISITOR_METRICS, JSON.stringify(metricas));
}

export function registrarVistaLanding(): MetricasVisitante {
  const m = obtenerMetricasVisitante();
  const nuevo = {
    vistasLanding: m.vistasLanding + 1,
    ingresosCentro: m.ingresosCentro,
    ultimoAccesoIso: new Date().toISOString(),
  };
  guardar(nuevo);
  return { ...nuevo, visitorId: m.visitorId };
}

export function registrarIngresoCentro(): MetricasVisitante {
  const m = obtenerMetricasVisitante();
  const nuevo = {
    vistasLanding: m.vistasLanding,
    ingresosCentro: m.ingresosCentro + 1,
    ultimoAccesoIso: new Date().toISOString(),
  };
  guardar(nuevo);
  return { ...nuevo, visitorId: m.visitorId };
}
