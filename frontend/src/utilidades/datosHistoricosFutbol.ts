import type { PartidoFutbolEstadistico } from '../tipos/futbol';

/** Valores observados; nunca usar FT como sustituto de una mitad ausente. */
export function valorHistoricoFutbol(p: PartidoFutbolEstadistico, mercado: string, lado: 'LOCAL' | 'VISITANTE'): number | null {
  const m = mercado.toUpperCase();
  const sufijo = lado === 'LOCAL' ? 'Local' : 'Visitante';
  const periodo = m.endsWith('_1T') ? '1t' : m.endsWith('_2T') ? '2t' : '';
  if (m.startsWith('DISPAROS') && periodo) return null;
  const clave = m.startsWith('CORNERS') ? `corners${sufijo}${periodo}`
    : m.startsWith('GOLES') ? `goles${sufijo}${periodo}`
    : m.includes('ARCO') ? `disparosArco${sufijo}` : `disparos${sufijo}`;
  const v = (p as unknown as Record<string, unknown>)[clave];
  return typeof v === 'number' && Number.isFinite(v) && v >= 0 ? v : null;
}

export function sumarObservados(a: number | null, b: number | null): number | null {
  return a !== null && b !== null ? a + b : null;
}
