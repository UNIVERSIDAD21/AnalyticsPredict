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
// TIPOS DE DE-VIG
// ══════════════════════════════════════════════════════════════

/**
 * Modo de de-vig para el cálculo de probabilidades justas.
 *
 * - 'estricto': Requiere ambas cuotas (over y under) para calcular overround exacto
 * - 'estimado': Solo una cuota disponible, aplica penalización por vig estimado
 */
export type ModoDevig = 'estricto' | 'estimado';

// ══════════════════════════════════════════════════════════════
// PETICIONES
// ══════════════════════════════════════════════════════════════

/**
 * Datos para solicitar un análisis
 *
 * IMPORTANTE: Para que las predicciones se registren en la BD,
 * es necesario enviar el contexto del partido (partido_id o al menos
 * equipo_local + equipo_visitante + fecha_partido para que el backend
 * pueda hacer lookup).
 *
 * CONTRATO DE CUOTAS:
 * - Sin cuotas: análisis solo probabilidades (sin EV)
 * - Una cuota (del lado seleccionado): de-vig estimado (modo_devig='estimado')
 * - Ambas cuotas: de-vig exacto con overround real (modo_devig='estricto')
 */
export interface PeticionAnalisis {
  /** Nombre del equipo local (requerido) */
  equipo_local: string;

  /** Nombre del equipo visitante (requerido) */
  equipo_visitante: string;

  /** Mercado a analizar: Q1, Q2, Q3, Q4 o COMPLETO (requerido) */
  mercado: Mercado;

  /** Línea de puntos a analizar (requerido) */
  linea: number;

  /**
   * @deprecated Usar cuota_over y cuota_under en su lugar.
   * Campo legacy mantenido por compatibilidad con versiones anteriores.
   * Si se envía, representa la cuota del lado seleccionado.
   */
  cuota?: number;

  /**
   * Cuota decimal para el OVER (ej: 1.85).
   * Con ambas cuotas se activa de-vig exacto.
   */
  cuota_over?: number;

  /**
   * Cuota decimal para el UNDER (ej: 1.95).
   * Con ambas cuotas se activa de-vig exacto.
   */
  cuota_under?: number;

  /**
   * Lado de la apuesta: 'OVER' o 'UNDER'.
   * IMPORTANTE: Debe enviarse siempre que se incluyan cuotas.
   * El backend valida coherencia entre lado y cuotas.
   */
  lado?: LadoApuesta;

  /**
   * Modo de de-vig calculado por el frontend:
   * - 'estricto': ambas cuotas presentes
   * - 'estimado': solo una cuota presente
   * Si no se envía, el backend lo determina automáticamente.
   */
  modo_devig?: ModoDevig;

  /** IDs de temporadas a incluir en el análisis */
  temporadas?: string[];

  // ══════════════════════════════════════════════════════════════
  // Campos para registro de predicciones (opcionales pero recomendados)
  // Si se envían, permiten el registro idempotente de predicciones
  // ══════════════════════════════════════════════════════════════

  /** ID único del partido (si se seleccionó desde el selector) */
  partido_id?: string;

  /** ID de la temporada actual */
  temporada_id?: string;

  /** ID del equipo local */
  equipo_local_id?: string;

  /** ID del equipo visitante */
  equipo_visitante_id?: string;

  /** Fecha del partido en formato YYYY-MM-DD */
  fecha_partido?: string;

  /** Tipo de partido: PRE (pretemporada), REG (regular), POST (playoffs) */
  tipo_partido?: 'PRE' | 'REG' | 'POST';
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
