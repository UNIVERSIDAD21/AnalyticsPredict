/** Copias de consulta personales, no apuestas ni registros analíticos oficiales. */
export type LigaCuaderno = 'nba' | 'wnba' | 'euroliga' | 'futbol';
export interface EntradaCuaderno {
  id: string; titulo: string; liga: LigaCuaderno; guardadoEn: string;
  tipo: 'base' | 'resultado'; snapshot: unknown; notas: string; etiquetas: string[]; favorito: boolean;
}
const CLAVE = 'analyticspredict-cuaderno-v1';
export function leerCuaderno(): EntradaCuaderno[] {
  const raw = localStorage.getItem(CLAVE);
  if (!raw) return [];
  const parsed: unknown = JSON.parse(raw);
  if (!Array.isArray(parsed) || !parsed.every(e => e && typeof e.id === 'string' && typeof e.titulo === 'string' &&
    ['nba', 'wnba', 'euroliga', 'futbol'].includes(e.liga) && ['base', 'resultado'].includes(e.tipo) &&
    typeof e.guardadoEn === 'string' && typeof e.notas === 'string' && typeof e.favorito === 'boolean' &&
    Array.isArray(e.etiquetas) && e.etiquetas.every((t: unknown) => typeof t === 'string') && 'snapshot' in e)) {
    throw new Error('El cuaderno local no tiene un formato válido. No se sobrescribió.');
  }
  return parsed as EntradaCuaderno[];
}
function persistir(entradas: EntradaCuaderno[]) {
  const json = JSON.stringify(entradas);
  if (json.length > 4_000_000 || entradas.length > 100) throw new Error('El cuaderno alcanzó su límite local. Exporta una copia antes de quitar entradas.');
  try { localStorage.setItem(CLAVE, json); }
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
