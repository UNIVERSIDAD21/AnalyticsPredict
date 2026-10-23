/** Contrato de presentación: lo no estimado puede faltar, nunca se inventa. */
import type { ResultadoAnalisis, PrediccionCuarto, NivelConfianza, FactoresConfianza, ContextoForma, ContextoH2H } from './analisis';
export type PrediccionVista = Pick<PrediccionCuarto, 'media_equipo' | 'media_rival' | 'media_total' | 'desviacion_total' | 'probabilidad_over' | 'probabilidad_under'>
  & Partial<Pick<PrediccionCuarto, 'ganador_probable' | 'probabilidad_ganador'>>;
export type ResultadoVista = Omit<ResultadoAnalisis, 'predicciones' | 'prediccion_juego_completo' | 'nivel_confianza' | 'factores_confianza' | 'contexto'> & {
  predicciones: Record<string, PrediccionVista>; prediccion_juego_completo: PrediccionVista | null;
  contexto?: (Omit<NonNullable<ResultadoAnalisis['contexto']>, 'descanso_equipo' | 'descanso_rival' | 'forma_equipo' | 'forma_rival'> & {
    descanso_equipo: NonNullable<ResultadoAnalisis['contexto']>['descanso_equipo'] | null;
    descanso_rival: NonNullable<ResultadoAnalisis['contexto']>['descanso_rival'] | null;
    forma_equipo: FormaVista; forma_rival: FormaVista;
  }) | null;
  nivel_confianza: NivelConfianza | null; factores_confianza: FactoresConfianza | null;
};
export type FormaVista = Pick<ContextoForma, 'ultimos_n' | 'victorias' | 'derrotas' | 'racha' | 'ppg' | 'opp_ppg' | 'net_rating'>
  & Partial<Pick<ContextoForma, 'ppg_temporada' | 'diferencia_vs_temporada' | 'tendencia'>> & { empates?: number };

export type H2HVista = Omit<ContextoH2H, 'tendencia_over'>;
