/**
 * AnalisisPartidoFutbol.tsx
 *
 * Mantiene compatibilidad de rutas legacy (/futbol/partidos/:id)
 * redirigiendo al flujo canónico unificado en /futbol.
 */

import { useEffect } from 'react';

function extraerPartidoIdDeURL(): string | null {
  const path = window.location.pathname;
  const match = path.match(/^\/futbol\/partidos\/([^/]+)$/);
  return match ? match[1] : null;
}

export function AnalisisPartidoFutbol() {
  useEffect(() => {
    const partidoId = extraerPartidoIdDeURL();
    const destino = partidoId ? `/futbol?partidoId=${encodeURIComponent(partidoId)}` : '/futbol';
    window.history.replaceState({}, '', destino);
    window.dispatchEvent(new PopStateEvent('popstate'));
  }, []);

  return null;
}
