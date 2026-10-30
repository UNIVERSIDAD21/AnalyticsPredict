import type { PartidoFutbolResumen } from '../tipos/futbol';

export function fechaColombia(instante = new Date()): string {
  const partes = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(instante);
  return ['year', 'month', 'day'].map(tipo => partes.find(p => p.type === tipo)?.value).join('-');
}
export function sumarDias(fecha: string, cantidad: number): string {
  const dia = new Date(`${fecha}T12:00:00Z`);
  dia.setUTCDate(dia.getUTCDate() + cantidad);
  return dia.toISOString().slice(0, 10);
}
export function puedeAnalizarPartido(partido: PartidoFutbolResumen, ahora = Date.now()): boolean {
  const inicio = Date.parse(partido.fechaPartido);
  return Number.isFinite(inicio) && (inicio <= ahora || partido.estado === 'PROGRAMADO');
}

export function requiereReconstruccion(partido: PartidoFutbolResumen, ahora = Date.now()): boolean {
  return partido.precisionFecha === 'DIA' || partido.reconstruccion === true || Date.parse(partido.fechaPartido) <= ahora;
}
export function fechaVisiblePartido(partido: Pick<PartidoFutbolResumen, 'fechaPartido' | 'precisionFecha' | 'fechaFuente'>): string {
  if (partido.precisionFecha === 'DIA') {
    const nominal = partido.fechaFuente;
    if (!nominal || !/^\d{4}-\d{2}-\d{2}$/.test(nominal)) return 'Fecha nominal N/D · Hora por confirmar';
    const d = new Date(`${nominal}T12:00:00Z`);
    if (!Number.isFinite(d.getTime()) || d.toISOString().slice(0,10) !== nominal) return 'Fecha nominal N/D · Hora por confirmar';
    return `${d.toLocaleDateString('es-CO', { timeZone: 'UTC', dateStyle: 'medium' })} · Día nominal de fuente · Hora por confirmar`;
  }
  const d = new Date(partido.fechaPartido);
  return Number.isFinite(d.getTime()) ? `${d.toLocaleString('es-CO', { timeZone: 'America/Bogota', dateStyle: 'medium', timeStyle: 'short' })} COT` : 'Fecha y hora N/D';
}
