import type { EntradaCuaderno } from './cuadernoLocal';
export interface FiltrosCuaderno {
  buscar: string; liga: string; favorito: boolean; etiqueta: string; desde: string; hasta: string;
  orden: 'recientes' | 'antiguas' | 'titulo' | 'favoritos';
}
export const FILTROS_INICIALES: FiltrosCuaderno = { buscar: '', liga: '', favorito: false, etiqueta: '', desde: '', hasta: '', orden: 'recientes' };
const normalizar = (s: string) => s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLocaleLowerCase('es-CO').trim();
export function fechaColombiaGuardada(timestamp: string) {
  const partes = new Intl.DateTimeFormat('en', { timeZone: 'America/Bogota', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date(timestamp));
  const parte = (tipo: string) => partes.find(p => p.type === tipo)?.value;
  return `${parte('year')}-${parte('month')}-${parte('day')}`;
}
export function organizarCuaderno(entradas: EntradaCuaderno[], filtros: FiltrosCuaderno) {
  const palabras = normalizar(filtros.buscar).split(/\s+/).filter(Boolean);
  return entradas.filter(e => {
    const texto = normalizar(`${e.titulo} ${e.notas} ${e.etiquetas.join(' ')}`);
    const fecha = fechaColombiaGuardada(e.guardadoEn);
    return (!filtros.liga || e.liga === filtros.liga) && (!filtros.favorito || e.favorito) &&
      (!filtros.etiqueta || e.etiquetas.some(t => normalizar(t) === normalizar(filtros.etiqueta))) &&
      (!filtros.desde || fecha >= filtros.desde) && (!filtros.hasta || fecha <= filtros.hasta) && palabras.every(p => texto.includes(p));
  }).sort((a, b) => {
    if (filtros.orden === 'titulo') return a.titulo.localeCompare(b.titulo, 'es') || a.id.localeCompare(b.id);
    if (filtros.orden === 'favoritos' && a.favorito !== b.favorito) return a.favorito ? -1 : 1;
    const delta = Date.parse(b.guardadoEn) - Date.parse(a.guardadoEn);
    return (filtros.orden === 'antiguas' ? -delta : delta) || a.id.localeCompare(b.id);
  });
}
