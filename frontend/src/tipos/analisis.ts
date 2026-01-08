// hace parte del diseño de analisis
/**
 * analisis.ts — Tipos relacionados con el análisis de partidos
 */

// ══════════════════════════════════════════════════════════════
// ENUMERACIONES
// ══════════════════════════════════════════════════════════════

/**
 * Mercados disponibles para análisis
 */
export type Mercado = 'Q1' | 'Q2' | 'Q3' | 'Q4' | 'COMPLETO';

/**
 * Niveles de confianza del sistema
 */
export type NivelConfianza = 'ALTA' | 'MEDIA' | 'BAJA';

/**
 * Tipos de recomendación
 */
export type TipoRecomendacion = 'VALOR' | 'JUSTO' | 'EVITAR';

/**
 * Lado de la apuesta
 */
export type LadoApuesta = 'OVER' | 'UNDER';

// ══════════════════════════════════════════════════════════════
// PETICIONES
// ══════════════════════════════════════════════════════════════

/**
 * Datos para solicitar un análisis
 */
export interface PeticionAnalisis {
  equipo_local: string;
  equipo_visitante: string;
  mercado: Mercado;
  linea: number;
  cuota?: number;
  temporadas?: string[];
}

/**
 * Datos para solicitar análisis en vivo
 */
export interface PeticionAnalisisEnVivo extends PeticionAnalisis {
  marcador_q1?: string;
  marcador_q2?: string;
  marcador_q3?: string;
  peso_en_vivo?: number;
}

// ══════════════════════════════════════════════════════════════
// RESPUESTAS
// ══════════════════════════════════════════════════════════════

/**
 * Razón que explica una predicción
 */
export interface RazonPrediccion {
  factor: string;
  direccion: 'sube' | 'baja';
  impacto: number;
  descripcion: string;
}

/**
 * Predicción para un cuarto específico
 */
export interface PrediccionCuarto {
  cuarto: string;
  media_equipo: number;
  desviacion_equipo: number;
  rango_equipo: [number, number];
  media_rival: number;
  desviacion_rival: number;
  rango_rival: [number, number];
  media_total: number;
  desviacion_total: number;
  rango_total: [number, number];
  linea_analizada: number | null;
  probabilidad_over: number | null;
  probabilidad_under: number | null;
  ganador_probable: string;
  probabilidad_ganador: number;
}

/**
 * Factores que determinan la confianza
 */
export interface FactoresConfianza {
  tamano_muestra: string;
  volatilidad: string;
  frescura_datos: string;
  puntaje_total: number;
}

/**
 * Análisis del valor de mercado
 */
export interface AnalisisMercado {
  cuota: number;
  probabilidad_implicita: number;
  edge: number;
  valor_esperado: number;
  recomendacion: TipoRecomendacion;
}

/**
 * Candidato de apuesta evaluado
 */
export interface CandidatoApuesta {
  cuarto: string;
  mercado: string;
  lado: LadoApuesta;
  linea: number;
  probabilidad: number;
  media: number;
  desviacion: number;
  distancia_z: number;
}

/**
 * Resultado completo del análisis
 */
export interface ResultadoAnalisis {
  equipo: string;
  equipo_nombre_completo: string;
  rival: string;
  rival_nombre_completo: string;
  ubicacion: 'LOCAL' | 'VISITANTE';
  fecha_analisis: string;
  predicciones: Record<string, PrediccionCuarto>;
  prediccion_juego_completo: PrediccionCuarto | null;
  razones: RazonPrediccion[];
  nivel_confianza: NivelConfianza;
  factores_confianza: FactoresConfianza;
  analisis_mercado: AnalisisMercado | null;
  mejor_apuesta: CandidatoApuesta | null;
  es_en_vivo: boolean;
  cuartos_reales: Record<string, [number, number]>;
  metadata: Record<string, unknown>;
  // Campos adicionales que vienen en la respuesta
  probabilidad_over?: number | null;
  probabilidad_under?: number | null;
  linea_analizada?: number | null;
}

/**
 * Respuesta del endpoint POST /api/analizar
 */
export interface RespuestaAnalisis {
  exito: boolean;
  datos: ResultadoAnalisis;
  advertencias?: string[];
}
