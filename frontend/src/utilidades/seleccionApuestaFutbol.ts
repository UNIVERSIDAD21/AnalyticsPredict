import type {
  AnalisisFutbolResponse,
  NivelConfianza,
  TipoMercadoFutbol,
} from '../tipos/futbol';

export interface SeleccionRegistrableFutbol {
  mercado: TipoMercadoFutbol;
  lado: 'OVER' | 'UNDER';
  linea: number;
  cuotas: { over?: number; under?: number };
  trazabilidad: { idSeleccion: string };
}

export interface ApuestaGuardableFutbol {
  mercado: TipoMercadoFutbol;
  lado: 'OVER' | 'UNDER';
  linea: number;
  cuota: number;
  probabilidad: number | null;
  confianza: NivelConfianza | null;
  valorEsperado: number | null;
  trazabilidad: string;
  tieneRecomendacion: boolean;
}

function probabilidadValida(valor: unknown): number | null {
  return typeof valor === 'number' && Number.isFinite(valor) && valor >= 0 && valor <= 1
    ? valor
    : null;
}

/**
 * Prepara el registro de la selección del usuario, aunque no haya una
 * recomendación apta para esa línea. Los campos analíticos no disponibles se
 * conservan como N/D; nunca se sustituyen por valores inventados.
 */
export function prepararApuestaGuardableFutbol(
  analisis: Pick<AnalisisFutbolResponse, 'objetivo' | 'recomendaciones'>,
  seleccion: SeleccionRegistrableFutbol,
): ApuestaGuardableFutbol {
  const recomendacion = analisis.recomendaciones.find((item) => (
    item.mercado === seleccion.mercado
    && item.lado === seleccion.lado
    && Math.abs(item.linea - seleccion.linea) < 1e-9
  )) ?? null;

  const objetivoCoincide = analisis.objetivo.mercado === seleccion.mercado
    && analisis.objetivo.lado === seleccion.lado
    && Math.abs(analisis.objetivo.linea - seleccion.linea) < 1e-9;
  const probabilidadObjetivo = objetivoCoincide
    ? analisis.objetivo.probabilidadesObjetivo[seleccion.lado === 'OVER' ? 'over' : 'under']
    : null;
  const cuotaSeleccionada = seleccion.lado === 'OVER'
    ? seleccion.cuotas.over
    : seleccion.cuotas.under;
  const cuotaRecomendada = seleccion.lado === 'OVER'
    ? recomendacion?.cuotaOver
    : recomendacion?.cuotaUnder;

  return {
    mercado: seleccion.mercado,
    lado: seleccion.lado,
    linea: seleccion.linea,
    cuota: cuotaSeleccionada ?? recomendacion?.cuota ?? cuotaRecomendada ?? 0,
    probabilidad: probabilidadValida(probabilidadObjetivo) ?? probabilidadValida(recomendacion?.probabilidad),
    confianza: recomendacion?.confianza ?? null,
    valorEsperado: recomendacion?.valorEsperado ?? null,
    trazabilidad: seleccion.trazabilidad.idSeleccion,
    tieneRecomendacion: recomendacion !== null,
  };
}
