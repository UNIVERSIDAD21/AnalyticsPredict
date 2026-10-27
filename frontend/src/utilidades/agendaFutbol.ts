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
  return partido.estado === 'FINALIZADO' || (partido.estado === 'PROGRAMADO' && Date.parse(partido.fechaPartido) > ahora);
}
