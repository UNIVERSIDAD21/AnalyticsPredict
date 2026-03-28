import { clienteAPI } from './api';

interface EventoProducto {
  nombre: string;
  timestamp: string;
  payload?: Record<string, unknown>;
}

const KEY = 'analytics.product.events';
const MAX_ITEMS = 300;

function leerEventos(): EventoProducto[] {
  if (typeof window === 'undefined') return [];
  const raw = window.localStorage.getItem(KEY);
  if (!raw) return [];
  try {
    const data = JSON.parse(raw) as EventoProducto[];
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

function guardarEventos(eventos: EventoProducto[]) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(KEY, JSON.stringify(eventos.slice(-MAX_ITEMS)));
}

export function registrarEventoProducto(nombre: string, payload?: Record<string, unknown>) {
  const evento: EventoProducto = {
    nombre,
    timestamp: new Date().toISOString(),
    payload,
  };

  const eventos = leerEventos();
  eventos.push(evento);
  guardarEventos(eventos);

  void clienteAPI.post('/api/product-analytics/events', {
    name: nombre,
    payload: {
      ...payload,
      ts_client: evento.timestamp,
    },
  }).catch(() => {
    // Best-effort: no romper UX por fallas de telemetría.
  });
}
