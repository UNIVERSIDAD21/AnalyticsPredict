/**
 * fechasFutbol.ts — Helpers de fecha/hora para módulo fútbol
 */

const ZONA_HORARIA_COLOMBIA = 'America/Bogota';

const RE_TIENE_ZONA = /([zZ]|[+\-]\d{2}:\d{2})$/;

/**
 * Si la fecha viene sin zona horaria, se asume UTC para evitar desfases.
 */
export function parsearFechaPartidoFutbol(fechaISO: string): Date {
  const normalizada = RE_TIENE_ZONA.test(fechaISO) ? fechaISO : `${fechaISO}Z`;
  return new Date(normalizada);
}

export function formatearHoraPartidoBogota(fechaISO: string): string {
  return parsearFechaPartidoFutbol(fechaISO).toLocaleTimeString('es-CO', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: ZONA_HORARIA_COLOMBIA,
  });
}

export function formatearFechaPartidoBogota(
  fechaISO: string,
  opciones?: Intl.DateTimeFormatOptions
): string {
  return parsearFechaPartidoFutbol(fechaISO).toLocaleDateString('es-CO', {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
    timeZone: ZONA_HORARIA_COLOMBIA,
    ...opciones,
  });
}

export function obtenerFechaISOBogota(fechaISO: string): string {
  const partes = new Intl.DateTimeFormat('en-CA', {
    timeZone: ZONA_HORARIA_COLOMBIA,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(parsearFechaPartidoFutbol(fechaISO));

  const year = partes.find((p) => p.type === 'year')?.value ?? '0000';
  const month = partes.find((p) => p.type === 'month')?.value ?? '00';
  const day = partes.find((p) => p.type === 'day')?.value ?? '00';
  return `${year}-${month}-${day}`;
}

export function obtenerHoyISOBogota(): string {
  const partes = new Intl.DateTimeFormat('en-CA', {
    timeZone: ZONA_HORARIA_COLOMBIA,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date());

  const year = partes.find((p) => p.type === 'year')?.value ?? '0000';
  const month = partes.find((p) => p.type === 'month')?.value ?? '00';
  const day = partes.find((p) => p.type === 'day')?.value ?? '00';
  return `${year}-${month}-${day}`;
}

