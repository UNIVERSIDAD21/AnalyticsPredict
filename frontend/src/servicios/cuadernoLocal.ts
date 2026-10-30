/** Copias de consulta personales, no apuestas ni registros analíticos oficiales. */
export type LigaCuaderno = 'nba' | 'wnba' | 'euroliga' | 'futbol';
export interface EntradaCuaderno {
  id: string; titulo: string; liga: LigaCuaderno; guardadoEn: string;
  tipo: 'base' | 'resultado'; snapshot: unknown; notas: string; etiquetas: string[]; favorito: boolean;
}
export const CLAVE_CUADERNO = 'analyticspredict-cuaderno-v1';
export const LIMITE_CONSULTAS = 100;
export const LIMITE_CUADERNO = 4_000_000;
export function validarCuaderno(parsed: unknown): EntradaCuaderno[] {
  if (!Array.isArray(parsed) || parsed.length > LIMITE_CONSULTAS || !parsed.every(e => e && typeof e === 'object' &&
    typeof e.id === 'string' && e.id.length > 0 && e.id.length <= 300 && typeof e.titulo === 'string' && e.titulo.length <= 1000 &&
    ['nba', 'wnba', 'euroliga', 'futbol'].includes(e.liga) && ['base', 'resultado'].includes(e.tipo) &&
    typeof e.guardadoEn === 'string' && Number.isFinite(Date.parse(e.guardadoEn)) && typeof e.notas === 'string' && e.notas.length <= 5000 && typeof e.favorito === 'boolean' &&
    Array.isArray(e.etiquetas) && e.etiquetas.length <= 12 && e.etiquetas.every((t: unknown) => typeof t === 'string' && t.length <= 300) && 'snapshot' in e) ||
    new Set(parsed.map(e => e.id)).size !== parsed.length || JSON.stringify(parsed).length > LIMITE_CUADERNO) {
    throw new Error('El cuaderno local no tiene un formato válido o supera su capacidad. No se sobrescribió.');
  }
  return parsed as EntradaCuaderno[];
}
export function leerCuaderno(): EntradaCuaderno[] {
  const raw = localStorage.getItem(CLAVE_CUADERNO);
  if (!raw) return [];
  const parsed: unknown = JSON.parse(raw);
  return validarCuaderno(parsed);
}
function persistir(entradas: EntradaCuaderno[]) {
  const json = JSON.stringify(entradas);
  if (json.length > LIMITE_CUADERNO || entradas.length > LIMITE_CONSULTAS) throw new Error('El cuaderno alcanzó su límite local. Exporta una copia antes de quitar entradas.');
  try { localStorage.setItem(CLAVE_CUADERNO, json); }
  catch { throw new Error('No se pudo guardar: almacenamiento del navegador lleno o no disponible. Exporta JSON para conservar la consulta.'); }
  window.dispatchEvent(new Event('cuaderno-actualizado'));
}
export function guardarConsulta(datos: Pick<EntradaCuaderno, 'titulo' | 'liga' | 'snapshot' | 'tipo'>) {
  const e: EntradaCuaderno = { ...datos, snapshot: JSON.parse(JSON.stringify(datos.snapshot)), id: crypto.randomUUID(),
    guardadoEn: new Date().toISOString(), notas: '', etiquetas: [], favorito: false };
  persistir([e, ...leerCuaderno()]);
  return e;
}
export function editarEntrada(id: string, cambios: Pick<EntradaCuaderno, 'notas' | 'etiquetas' | 'favorito'>) {
  // La edición del cuaderno nunca cambia la salida original ni su timestamp.
  persistir(leerCuaderno().map(e => e.id === id ? { ...e, ...cambios, etiquetas: cambios.etiquetas.slice(0, 12), notas: cambios.notas.slice(0, 5000) } : e));
}
export function quitarEntrada(id: string) { persistir(leerCuaderno().filter(e => e.id !== id)); }
export function descargar(nombre: string, contenido: string, tipo = 'application/json') {
  const url = URL.createObjectURL(new Blob([contenido], { type: `${tipo};charset=utf-8` }));
  const a = document.createElement('a'); a.href = url; a.download = nombre; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function csvSnapshot(snapshot: unknown): string {
  const filas: [string, unknown][] = [];
  function recorrer(v: unknown, clave: string) {
    if (v !== null && typeof v === 'object') Object.entries(v).forEach(([k, valor]) => recorrer(valor, clave ? `${clave}.${k}` : k));
    else filas.push([clave, v]);
  }
  recorrer(snapshot, '');
  const celda = (v: unknown) => {
    let s = v == null ? 'N/D' : String(v);
    if (/^[\s]*[=+@-]/.test(s) && typeof v === 'string') s = `'${s}`;
    return `"${s.replace(/"/g, '""')}"`;
  };
  return '\uFEFFcampo,valor\r\n' + filas.map(f => f.map(celda).join(',')).join('\r\n');
}
