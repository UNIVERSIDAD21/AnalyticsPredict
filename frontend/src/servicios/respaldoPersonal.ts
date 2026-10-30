import { CLAVE_CUADERNO, leerCuaderno, validarCuaderno, type EntradaCuaderno } from './cuadernoLocal';
import { CLAVE_FAVORITOS, identidadFavorito, leerFavoritos, validarFavoritos, type FavoritoLocal } from './favoritosLocales';
import { aplicarPreferencias, CLAVE_VISUAL, leerAparienciaGuardada, validarPreferencias, type PreferenciasVisualesLocal } from './preferenciasVisuales';

export const LIMITE_ARCHIVO_RESPALDO = 12_000_000;
const CLAVES = [CLAVE_CUADERNO, CLAVE_FAVORITOS, CLAVE_VISUAL] as const;
interface DatosPersonales { cuaderno: EntradaCuaderno[]; favoritos: FavoritoLocal[]; apariencia: PreferenciasVisualesLocal | null }
export interface RespaldoPersonal { formato: 'analyticspredict-respaldo-personal'; version: 1; creadoEn: string; datos: DatosPersonales }
export interface PlanRestauracion {
  base: string;
  origen: string;
  creadoEn: string | null;
  siguientes: DatosPersonales;
  nuevas: number;
  repetidas: number;
  conflictos: number;
  favoritosNuevos: number;
  aplicarApariencia: boolean;
}
const objeto = (v: unknown): v is Record<string, unknown> => v !== null && typeof v === 'object' && !Array.isArray(v);
function estadoActual(): string { return JSON.stringify(CLAVES.map(k => localStorage.getItem(k))); }
export function crearRespaldo(): RespaldoPersonal {
  return { formato: 'analyticspredict-respaldo-personal', version: 1, creadoEn: new Date().toISOString(),
    datos: { cuaderno: leerCuaderno(), favoritos: leerFavoritos(), apariencia: leerAparienciaGuardada() } };
}
/** Rescate literal de las tres claves personales, incluso si alguna está dañada. */
export function crearCopiaRecuperacion() {
  return { formato: 'analyticspredict-recuperacion-personal', version: 1, creadoEn: new Date().toISOString(),
    originales: Object.fromEntries(CLAVES.map(k => [k, localStorage.getItem(k)])) };
}
function canonico(valor: unknown): string {
  if (Array.isArray(valor)) return '[' + valor.map(canonico).join(',') + ']';
  if (objeto(valor)) return '{' + Object.keys(valor).sort().map(k => JSON.stringify(k) + ':' + canonico(valor[k])).join(',') + '}';
  return JSON.stringify(valor);
}
function validarProfundidad(valor: unknown) {
  const pendientes: [unknown, number][] = [[valor, 0]];
  while (pendientes.length) {
    const [v, nivel] = pendientes.pop()!;
    if (nivel > 60) throw new Error('El archivo tiene una estructura demasiado profunda. No se importó.');
    if (v && typeof v === 'object') for (const hijo of Object.values(v)) pendientes.push([hijo, nivel + 1]);
  }
}
export function prepararRestauracion(texto: string, aplicarApariencia = false): PlanRestauracion {
  if (texto.length > LIMITE_ARCHIVO_RESPALDO) throw new Error('El respaldo supera el tamaño permitido de 12 MB.');
  let parsed: unknown;
  try { parsed = JSON.parse(texto.replace(/^\uFEFF/, '')); }
  catch { throw new Error('No se pudo leer el archivo JSON. Tus datos actuales se conservan.'); }
  validarProfundidad(parsed);
  const base = estadoActual();
  const actual = crearRespaldo().datos;
  let recibidos: DatosPersonales, origen: string, creadoEn: string | null = null;
  if (Array.isArray(parsed)) {
    recibidos = { cuaderno: validarCuaderno(parsed), favoritos: [], apariencia: null };
    origen = 'Cuaderno anterior · solo consultas';
  } else {
    if (!objeto(parsed) || parsed.formato !== 'analyticspredict-respaldo-personal' || parsed.version !== 1 || !objeto(parsed.datos) ||
      typeof parsed.creadoEn !== 'string' || !Number.isFinite(Date.parse(parsed.creadoEn))) {
      throw new Error('Este archivo no es un respaldo personal compatible (versión 1) ni un cuaderno anterior.');
    }
    recibidos = { cuaderno: validarCuaderno(parsed.datos.cuaderno), favoritos: validarFavoritos(parsed.datos.favoritos),
      apariencia: parsed.datos.apariencia === null ? null : validarPreferencias(parsed.datos.apariencia) };
    origen = 'Respaldo personal completo'; creadoEn = parsed.creadoEn;
  }
  const porId = new Map(actual.cuaderno.map(e => [e.id, e]));
  let repetidas = 0, conflictos = 0;
  const nuevas = recibidos.cuaderno.filter(e => {
    const local = porId.get(e.id);
    if (!local) return true;
    if (canonico(local) === canonico(e)) repetidas++; else conflictos++;
    return false;
  });
  const idsFavoritos = new Set(actual.favoritos.map(identidadFavorito));
  const favoritosNuevos = recibidos.favoritos.filter(f => !idsFavoritos.has(identidadFavorito(f)));
  const siguientes: DatosPersonales = {
    cuaderno: validarCuaderno([...nuevas, ...actual.cuaderno].sort((a, b) => Date.parse(b.guardadoEn) - Date.parse(a.guardadoEn))),
    favoritos: validarFavoritos([...actual.favoritos, ...favoritosNuevos]),
    apariencia: aplicarApariencia && recibidos.apariencia ? recibidos.apariencia : actual.apariencia,
  };
  if (estadoActual() !== base) throw new Error('Tus datos cambiaron mientras se preparaba el respaldo. Vuelve a leer el archivo.');
  return { base, origen, creadoEn, siguientes, nuevas: nuevas.length, repetidas, conflictos,
    favoritosNuevos: favoritosNuevos.length, aplicarApariencia: Boolean(aplicarApariencia && recibidos.apariencia) };
}
/** Mezcla conservadora: un ID existente conserva siempre su versión local. */
export function aplicarRestauracion(plan: PlanRestauracion) {
  if (estadoActual() !== plan.base) throw new Error('Tus datos cambiaron después de la vista previa. Vuelve a leer el archivo antes de restaurar.');
  validarCuaderno(plan.siguientes.cuaderno); validarFavoritos(plan.siguientes.favoritos);
  if (plan.siguientes.apariencia) validarPreferencias(plan.siguientes.apariencia);
  const valores = [JSON.stringify(plan.siguientes.cuaderno), JSON.stringify({ version: 1, elementos: plan.siguientes.favoritos }),
    plan.siguientes.apariencia ? JSON.stringify(plan.siguientes.apariencia) : null];
  const anteriores = CLAVES.map(k => localStorage.getItem(k)), escritos: number[] = [];
  try {
    CLAVES.forEach((clave, i) => {
      if (valores[i] === anteriores[i]) return;
      if (valores[i] === null) localStorage.removeItem(clave); else localStorage.setItem(clave, valores[i]!);
      escritos.push(i);
    });
  } catch {
    let revertido = true;
    for (const i of escritos.reverse()) {
      try { if (anteriores[i] === null) localStorage.removeItem(CLAVES[i]); else localStorage.setItem(CLAVES[i], anteriores[i]!); }
      catch { revertido = false; }
    }
    throw new Error(revertido ? 'No hubo espacio para restaurar. Se recuperaron los datos anteriores; puedes liberar espacio y volver a intentarlo.' :
      'El navegador impidió completar la recuperación. Conserva la copia de seguridad descargada antes de restaurar y vuelve a abrir el cuaderno.');
  }
  if (plan.aplicarApariencia && plan.siguientes.apariencia) aplicarPreferencias(plan.siguientes.apariencia);
  for (const evento of ['cuaderno-actualizado', 'favoritos-actualizados', 'preferencias-visuales-actualizadas']) window.dispatchEvent(new Event(evento));
}
