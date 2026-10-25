/** Contrato de presentación: lo no estimado puede faltar, nunca se inventa. */
import type { ResultadoAnalisis, PrediccionCuarto, NivelConfianza, FactoresConfianza, ContextoForma, ContextoH2H, MejorApuestaDetalle, PrediccionAjustada, ResultadoAjustes, AjusteIndividual, ComponentesScore } from './analisis';
export type PrediccionVista = Pick<PrediccionCuarto, 'media_equipo' | 'media_rival' | 'media_total' | 'desviacion_total' | 'probabilidad_over' | 'probabilidad_under'>
  & Partial<Pick<PrediccionCuarto, 'ganador_probable' | 'probabilidad_ganador'>>
  & { ganador_tres_vias?: { local: number; empate: number; visitante: number } };
export type ResultadoVista = Omit<ResultadoAnalisis, 'predicciones' | 'prediccion_juego_completo' | 'nivel_confianza' | 'factores_confianza' | 'contexto' | 'prediccion_ajustada' | 'ajustes'> & {
  predicciones: Record<string, PrediccionVista>; prediccion_juego_completo: PrediccionVista | null;
  contexto?: (Omit<NonNullable<ResultadoAnalisis['contexto']>, 'descanso_equipo' | 'descanso_rival' | 'forma_equipo' | 'forma_rival'> & {
    descanso_equipo: NonNullable<ResultadoAnalisis['contexto']>['descanso_equipo'] | null;
    descanso_rival: NonNullable<ResultadoAnalisis['contexto']>['descanso_rival'] | null;
    forma_equipo: FormaVista; forma_rival: FormaVista;
  }) | null;
  nivel_confianza: NivelConfianza | null; factores_confianza: FactoresConfianza | null;
  prediccion_ajustada?: (Omit<PrediccionAjustada,'confianza_base'|'confianza_ajustada'|'ajustes_aplicados'> & { confianza_base: NivelConfianza | null; confianza_ajustada: NivelConfianza | null; ajustes_aplicados: AjustesVista }) | null;
  ajustes?: AjustesVista | null;
  detalle_descriptivo?: Omit<{ [K in keyof MejorApuestaDetalle]?: MejorApuestaDetalle[K] | null }, 'score_componentes'> & {score_componentes?:ComponentesScoreVista|null};
};
export type FormaVista = Pick<ContextoForma, 'ultimos_n' | 'victorias' | 'derrotas' | 'racha' | 'ppg' | 'opp_ppg' | 'net_rating'>
  & Partial<Pick<ContextoForma, 'ppg_temporada' | 'diferencia_vs_temporada' | 'tendencia'>> & { empates?: number };

export type H2HVista = Omit<ContextoH2H, 'tendencia_over'>;

export type AjustesVista = Omit<ResultadoAjustes,"ajustes"|"confianza_delta"> & { confianza_delta:number|null; ajustes:(Omit<AjusteIndividual,"confianza_ajuste"> & {confianza_ajuste:number|null})[] };

export type ComponentesScoreVista = {[K in keyof ComponentesScore]:number|null};
