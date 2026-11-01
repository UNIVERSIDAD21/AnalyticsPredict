import type { LadoApuesta, Mercado } from '../tipos';
import type { UbicacionHistorialEquipo } from '../tipos/futbol';

export interface BorradorFormularioAnalisis {
  mercado: Mercado | '';
  linea: string;
  ladoApuesta: LadoApuesta;
  cuotaOver: string;
  cuotaUnder: string;
}

export interface ConfiguracionAnalisisFutbol {
  categoria: 'GOLES' | 'CORNERS' | 'TIROS_AL_ARCO';
  alcance: 'TOTAL' | 'LOCAL' | 'VISITANTE';
  competicionId: string;
  temporadas: string[];
  limiteH2h: number;
  limiteLocal: number;
  limiteVisitante: number;
  ubicacionLocal: UbicacionHistorialEquipo;
  ubicacionVisitante: UbicacionHistorialEquipo;
  formulario?: BorradorFormularioAnalisis;
}

const CLAVE = 'ap:futbol:configuraciones:v1';
const MAX_PARTIDOS = 50;
let respaldo = new Map<string, ConfiguracionAnalisisFutbol>();
let escrituraPendiente = false;
const texto = (v: unknown) => typeof v === 'string' ? v.slice(0, 200) : '';
const limite = (v: unknown) => typeof v === 'number' && Number.isInteger(v) && v >= 1 && v <= 100 ? v : 10;
const ubicacion = (v: unknown): UbicacionHistorialEquipo => v === 'local' || v === 'visitante' ? v : 'todos';

function normalizar(valor: unknown): ConfiguracionAnalisisFutbol {
  const v = valor && typeof valor === 'object' ? valor as Record<string, unknown> : {};
  const f = v.formulario && typeof v.formulario === 'object' ? v.formulario as Record<string, unknown> : null;
  return {
    categoria: v.categoria === 'GOLES' || v.categoria === 'TIROS_AL_ARCO' ? v.categoria : 'CORNERS',
    alcance: v.alcance === 'LOCAL' || v.alcance === 'VISITANTE' ? v.alcance : 'TOTAL',
    competicionId: texto(v.competicionId),
    temporadas: Array.isArray(v.temporadas) ? v.temporadas.filter((t): t is string => typeof t === 'string').slice(0, 100) : [],
    limiteH2h: limite(v.limiteH2h), limiteLocal: limite(v.limiteLocal), limiteVisitante: limite(v.limiteVisitante),
    ubicacionLocal: ubicacion(v.ubicacionLocal), ubicacionVisitante: ubicacion(v.ubicacionVisitante),
    formulario: f ? {
      mercado: ['Q1', 'Q2', 'COMPLETO'].includes(String(f.mercado)) ? f.mercado as Mercado : '',
      linea: texto(f.linea), ladoApuesta: f.ladoApuesta === 'UNDER' ? 'UNDER' : 'OVER',
      cuotaOver: texto(f.cuotaOver), cuotaUnder: texto(f.cuotaUnder),
    } : undefined,
  };
}

function leerTodas(): Map<string, ConfiguracionAnalisisFutbol> {
  try {
    const raw: unknown = JSON.parse(window.sessionStorage.getItem(CLAVE) ?? '[]');
    if (!Array.isArray(raw)) return new Map();
    const guardadas = new Map<string, ConfiguracionAnalisisFutbol>(raw.slice(-MAX_PARTIDOS).filter(e => Array.isArray(e) && typeof e[0] === 'string')
      .map(([id, valor]) => [id, normalizar(valor)]));
    return escrituraPendiente ? new Map([...guardadas, ...respaldo]) : guardadas;
  } catch { return new Map(respaldo); }
}

function escribir(todas: Map<string, ConfiguracionAnalisisFutbol>) {
  respaldo = new Map([...todas].slice(-MAX_PARTIDOS));
  try { window.sessionStorage.setItem(CLAVE, JSON.stringify([...respaldo])); escrituraPendiente = false; }
  catch { escrituraPendiente = true; /* Conservar el borrador en memoria aunque las lecturas aún funcionen. */ }
}

export function leerConfiguracionFutbol(partidoId: string): ConfiguracionAnalisisFutbol {
  return leerTodas().get(partidoId) ?? normalizar(null);
}

export function recordarConfiguracionFutbol(partidoId: string, cambio: Partial<ConfiguracionAnalisisFutbol>) {
  if (!partidoId) return;
  const todas = leerTodas();
  const anterior = todas.get(partidoId);
  todas.delete(partidoId);
  todas.set(partidoId, normalizar({ ...anterior, ...cambio }));
  escribir(todas);
}

export function olvidarConfiguracionFutbol(partidoId: string) {
  const todas = leerTodas();
  todas.delete(partidoId);
  escribir(todas);
}
