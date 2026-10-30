import type { EntradaCuaderno, LigaCuaderno } from './cuadernoLocal';
import { LIGAS_PERSONALES, type FavoritoLocal } from './favoritosLocales';

export interface CoberturaRegistrada {
  formato: 'cobertura-registros-v1'; observado_en: string;
  ventana: { desde: string; hasta: string; dias: number; zona: string }; criterio: string;
  calendario_oficial_completo: null;
  competiciones: { competicion_id: string; codigo: string; nombre: string; liga: LigaCuaderno;
    registros: number; finales_con_marcador: number; ultimo_final: string | null; completos_por_campo: Record<string, number> }[];
}
/** Preferencias explícitas primero; copias guardadas después. No es eficacia ni frecuencia de partidos. */
export function priorizarCobertura(favoritos: FavoritoLocal[], copias: EntradaCuaderno[]) {
  return LIGAS_PERSONALES.map(liga => ({ liga, favorita: favoritos.some(f => f.liga === liga && f.tipo === 'liga'),
    entidades: favoritos.filter(f => f.liga === liga && f.tipo !== 'liga').length,
    copias: copias.filter(c => c.liga === liga).length,
  })).sort((a, b) => Number(b.favorita) - Number(a.favorita) || b.entidades - a.entidades || b.copias - a.copias);
}
