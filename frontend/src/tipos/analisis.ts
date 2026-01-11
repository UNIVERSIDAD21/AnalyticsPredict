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
 * Overrides de sizing enviados al backend.
 * caps en formato decimal (0.02 = 2%).
 */
export interface ConfiguracionSizingPeticion {
  cap_por_apuesta?: number;
  cap_diario?: number;
  stake_minimo?: number;
}

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

  /** Override de bankroll para sizing */
  bankroll?: number;

  /** Override del perfil de riesgo para sizing */
  perfil_riesgo?: PerfilRiesgo;

  /** Overrides de caps/stake mínimo para sizing */
  config_sizing?: ConfiguracionSizingPeticion;
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
  cuota_over?: number;
  cuota_under?: number;
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

  // ════════════════════════════════════════════════════════════
  // Campos adicionales que vienen en la respuesta
  // ════════════════════════════════════════════════════════════

  probabilidad_over?: number | null;
  probabilidad_under?: number | null;
  linea_analizada?: number | null;

  // ════════════════════════════════════════════════════════════
  // Campos avanzados Fase 2 (opcionales, backend puede o no enviarlos)
  // ════════════════════════════════════════════════════════════

  /** Detalle completo de la mejor apuesta con de-vig, score, sizing */
  mejor_apuesta_detalle?: MejorApuestaDetalle | null;

  /** Mensaje descriptivo de la apuesta recomendada */
  mensaje_apuesta?: string | null;

  /** Lista de candidatos evaluados con información extendida */
  candidatos?: CandidatoApuestaExtendido[];
}

/**
 * Respuesta del endpoint POST /api/analizar
 */
export interface RespuestaAnalisis {
  exito: boolean;
  datos: ResultadoAnalisis;
  advertencias?: string[];
}

// ══════════════════════════════════════════════════════════════
// TIPOS AVANZADOS DE-VIG, SCORE Y SIZING (Fase 2)
// ══════════════════════════════════════════════════════════════

/**
 * Método de de-vig utilizado para calcular probabilidades justas.
 *
 * - 'exacto': Se usaron ambas cuotas (over y under), cálculo preciso de overround
 * - 'estimado': Solo una cuota disponible, se usa vig estimado (4.5%)
 * - 'no_aplicado': No hay información suficiente para de-vig
 */
export type MetodoDeVig = 'exacto' | 'estimado' | 'no_aplicado';

/**
 * Datos del proceso de de-vig.
 * Muestra cómo se eliminó el margen de la casa para obtener probabilidades justas.
 */
export interface DatosDeVig {
  /** Método utilizado: exacto, estimado o no_aplicado */
  devig_metodo: MetodoDeVig;

  /** Overround (suma de probabilidades crudas). null si metodo=no_aplicado */
  devig_overround: number | null;

  /** Probabilidad cruda del mercado (1/cuota) */
  devig_p_mkt_raw: number;

  /** Probabilidad justa después de eliminar vig */
  devig_p_mkt_fair: number;

  /** Advertencias del proceso de de-vig */
  devig_advertencias: string[];

  /** Edge crudo: p_raw - p_mkt_raw (antes de calibración) */
  edge_raw: number | null;
}

/**
 * Componentes que forman el score total de la apuesta.
 */
export interface ComponentesScore {
  /** Componente por valor esperado (EV * 50) */
  ev: number;

  /** Componente por edge real (edge_real * 30) */
  edge_real: number;

  /** Valor de riesgo/volatilidad raw */
  riesgo_valor: number;

  /** Referencia de riesgo (umbral: 6.0) */
  riesgo_referencia: number;

  /** Riesgo normalizado: riesgo_valor / riesgo_referencia */
  riesgo_normalizado: number;

  /** Penalización por riesgo alto (-20 si riesgo > 6.0) */
  penalizacion_riesgo: number;

  /** Penalización por método de de-vig (-10 estimado, -20 no_aplicado) */
  penalizacion_devig: number;
}

/**
 * Score profesional de la apuesta.
 * Determina si la apuesta es apta y con qué nivel de confianza.
 */
export interface ScoreApuesta {
  /**
   * Score total. Si gates_pasados=false, será -1000.
   * Composición: ev + edge_real + penalizacion_riesgo + penalizacion_devig
   */
  score_total: number;

  /** Desglose de componentes del score */
  score_componentes: ComponentesScore;

  /** Explicación legible del score */
  score_explicacion: string;

  /** Lista de penalizaciones aplicadas: RIESGO_ALTO, DEVIG_ESTIMADO, SIN_DEVIG */
  score_penalizaciones: string[];
}

/**
 * Penalizaciones de sizing aplicadas como multiplicadores.
 */
export interface PenalizacionesSizing {
  /** Multiplicador por de-vig estimado (0.5) */
  devig_estimado?: number;

  /** Multiplicador por de-vig no aplicado (0.3) */
  devig_no_aplicado?: number;

  /** Multiplicador por riesgo alto (0.7) */
  riesgo_alto?: number;

  /** Penalización por kelly negativo (1.0) */
  kelly_negativo?: number;
}

/**
 * Perfil de riesgo del usuario para sizing.
 */
export type PerfilRiesgo = 'CONSERVADOR' | 'MEDIO' | 'AGRESIVO';

/**
 * Resultado del cálculo de sizing (Kelly criterion).
 * Determina cuánto apostar según bankroll y perfil de riesgo.
 */
export interface ResultadoSizing {
  /** Kelly completo: (b*p - q) / b */
  kelly_full: number | null;

  /** Kelly fraccional después de aplicar perfil y penalizaciones */
  kelly_fraccional: number | null;

  /** Fracción aplicada: kelly_fraccional / kelly_full */
  fraccion_kelly: number | null;

  /** Stake en moneda (bankroll * kelly_fraccional) */
  stake: number | null;

  /** Porcentaje del bankroll a apostar */
  stake_porcentaje: number | null;

  /** Bankroll usado para el cálculo */
  bankroll_momento: number | null;

  /** Perfil de riesgo utilizado */
  perfil_riesgo_usado: PerfilRiesgo;

  /** Advertencias del sizing */
  sizing_advertencias: string[];

  /** Multiplicadores/penalizaciones aplicados */
  sizing_penalizaciones: PenalizacionesSizing;

  /** Indica si se aplicó algún cap */
  aplicaron_caps: boolean;
}

/**
 * Datos de calibración de probabilidades.
 * Muestra la diferencia entre probabilidad cruda y calibrada.
 */
export interface DatosCalibracion {
  /** Probabilidad cruda del modelo antes de calibración */
  p_raw: number | null;

  /** Probabilidad calibrada después de aplicar calibrador */
  p_calibrada: number | null;

  /** Nombre del calibrador usado (platt, isotonic, none) */
  calibrador_usado: string | null;
}

/**
 * Detalle completo de la mejor apuesta recomendada.
 * Incluye de-vig, score, sizing y calibración.
 */
export interface MejorApuestaDetalle {
  // ════════════════════════════════════════════════════════════
  // Información básica de la apuesta
  // ════════════════════════════════════════════════════════════

  /** Mercado: Q1, Q2, Q3, Q4 o COMPLETO */
  mercado: string;

  /** Lado: OVER o UNDER */
  lado: LadoApuesta;

  /** Línea de la apuesta */
  linea: number;

  /** Cuota del lado seleccionado */
  cuota: number;

  /** Cuota over (si disponible) */
  cuota_over: number | null;

  /** Cuota under (si disponible) */
  cuota_under: number | null;

  // ════════════════════════════════════════════════════════════
  // Probabilidades y valor
  // ════════════════════════════════════════════════════════════

  /** Probabilidad calculada por el sistema */
  probabilidad_sistema: number;

  /** Edge real: p_calibrada - p_mkt_fair */
  edge_real: number | null;

  /** Valor esperado: (p * cuota) - 1 */
  valor_esperado: number | null;

  /** Media de la predicción */
  prediccion_media: number;

  /** Desviación estándar de la predicción */
  prediccion_desviacion: number;

  /** Distancia Z desde la línea */
  distancia_z: number;

  // ════════════════════════════════════════════════════════════
  // Calibración
  // ════════════════════════════════════════════════════════════

  /** Probabilidad cruda antes de calibración */
  p_raw: number | null;

  /** Probabilidad después de calibración */
  p_calibrada: number | null;

  /** Calibrador usado */
  calibrador_usado: string | null;

  // ════════════════════════════════════════════════════════════
  // De-Vig
  // ════════════════════════════════════════════════════════════

  /** Método de de-vig: exacto, estimado, no_aplicado */
  devig_metodo: MetodoDeVig;

  /** Overround calculado */
  devig_overround: number | null;

  /** Probabilidad cruda del mercado */
  devig_p_mkt_raw: number;

  /** Probabilidad justa del mercado */
  devig_p_mkt_fair: number;

  /** Advertencias de de-vig */
  devig_advertencias: string[];

  /** Edge crudo (antes de calibración) */
  edge_raw: number | null;

  // ════════════════════════════════════════════════════════════
  // Score
  // ════════════════════════════════════════════════════════════

  /** Score total (-1000 si gates fallan) */
  score_total: number;

  /** Componentes del score */
  score_componentes: ComponentesScore;

  /** Explicación del score */
  score_explicacion: string;

  /** Penalizaciones del score */
  score_penalizaciones: string[];

  // ════════════════════════════════════════════════════════════
  // Sizing
  // ════════════════════════════════════════════════════════════

  /** Kelly completo */
  kelly_full: number | null;

  /** Kelly fraccional */
  kelly_fraccional: number | null;

  /** Fracción de kelly aplicada */
  fraccion_kelly: number | null;

  /** Stake recomendado en moneda */
  stake: number | null;

  /** Stake como porcentaje del bankroll */
  stake_porcentaje: number | null;

  /** Bankroll en el momento del cálculo */
  bankroll_momento: number | null;

  /** Perfil de riesgo usado */
  perfil_riesgo_usado: PerfilRiesgo;

  /** Advertencias de sizing */
  sizing_advertencias: string[];

  /** Penalizaciones de sizing */
  sizing_penalizaciones: PenalizacionesSizing;

  /** Indica si se aplicó algún cap */
  aplicaron_caps: boolean;
}

/**
 * Candidato de apuesta con información extendida.
 * Versión resumida para la lista de candidatos.
 */
export interface CandidatoApuestaExtendido extends CandidatoApuesta {
  /** Cuota del lado */
  cuota?: number;

  /** Probabilidad calculada */
  probabilidad_sistema?: number;

  /** Edge real */
  edge_real?: number | null;

  /** Valor esperado */
  valor_esperado?: number | null;

  /** Método de de-vig */
  devig_metodo?: MetodoDeVig;

  /** Overround */
  devig_overround?: number | null;

  /** Probabilidad cruda del mercado */
  devig_p_mkt_raw?: number;

  /** Probabilidad justa del mercado */
  devig_p_mkt_fair?: number;

  /** Advertencias de de-vig */
  devig_advertencias?: string[];

  /** Edge crudo */
  edge_raw?: number | null;

  /** Score total */
  score_total?: number;

  /** Penalizaciones del score */
  score_penalizaciones?: string[];
}
