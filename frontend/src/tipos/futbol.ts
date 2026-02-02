/**
 * futbol.ts — Interfaces TypeScript para el módulo de fútbol
 */

// ══════════════════════════════════════════════════════════════
// TIPOS BASE
// ══════════════════════════════════════════════════════════════

/**
 * Competición de fútbol
 */
export interface Competicion {
  id: string;
  codigo: string;
  nombre: string;
  pais: string;
  tipo: 'liga' | 'copa_nacional' | 'continental';
  prioridad: number;
  activa: boolean;
  logoUrl?: string;
}

/**
 * Filtros para competiciones
 */
export interface FiltrosCompeticion {
  pais?: string;
  tipo?: 'liga' | 'copa_nacional' | 'continental';
  activa?: boolean;
}

/**
 * Equipo de fútbol
 */
export interface EquipoFutbol {
  id: string;
  nombre: string;
  nombreCorto: string;
  pais: string;
  competicionPrincipal: string;
  logoUrl?: string;
}

/**
 * Estadísticas de equipo de fútbol
 */
export interface EstadisticasEquipoFutbol {
  partidosJugados: number;
  victorias: number;
  empates: number;
  derrotas: number;
  golesFavor: number;
  golesContra: number;
  cornersFavor: number;
  cornersContra: number;
  disparosTotal: number;
  disparosArco: number;
  // Promedios
  promedioGolesFavor: number;
  promedioGolesContra: number;
  promedioCornersFavor: number;
  promedioCornersContra: number;
  promedioDisparos: number;
  // Por ubicación
  promedioGolesFavorLocal: number;
  promedioGolesFavorVisitante: number;
  promedioCornersFavorLocal: number;
  promedioCornersFavorVisitante: number;
}

// ══════════════════════════════════════════════════════════════
// TIPOS DE PARTIDO
// ══════════════════════════════════════════════════════════════

/**
 * Estado del partido
 */
export type EstadoPartido =
  | 'PROGRAMADO'
  | 'EN_VIVO'
  | 'ENTRETIEMPO'
  | 'FINALIZADO'
  | 'SUSPENDIDO'
  | 'APLAZADO'
  | 'CANCELADO';

/**
 * Partido resumen (para listas)
 */
export interface PartidoFutbolResumen {
  id: string;
  competicion: string;
  competicionNombre: string;
  fechaPartido: string; // ISO datetime
  equipoLocal: string;
  equipoLocalNombre: string;
  equipoLocalLogo?: string;
  equipoVisitante: string;
  equipoVisitanteNombre: string;
  equipoVisitanteLogo?: string;
  estado: EstadoPartido;
  jornada?: number;
  // Resultado (si finalizado)
  golesLocal?: number;
  golesVisitante?: number;
}

/**
 * Filtros para partidos
 */
export interface FiltrosPartidos {
  competicion?: string;
  dias?: number;
  estado?: EstadoPartido;
  equipo?: string;
  limite?: number;
}

/**
 * Partido detalle (para análisis)
 */
export interface PartidoFutbolDetalle extends PartidoFutbolResumen {
  // Goles por tiempo
  localGoles1t?: number;
  localGoles2t?: number;
  localGolesTotal?: number;
  visitanteGoles1t?: number;
  visitanteGoles2t?: number;
  visitanteGolesTotal?: number;
  equipoLocalId?: string;
  equipoVisitanteId?: string;
  // Corners por tiempo
  localCorners1t?: number;
  localCorners2t?: number;
  localCornersTotal?: number;
  visitanteCorners1t?: number;
  visitanteCorners2t?: number;
  visitanteCornersTotal?: number;
  // Disparos
  localDisparosTotal?: number;
  localDisparosArco?: number;
  visitanteDisparosTotal?: number;
  visitanteDisparosArco?: number;
  // Estadísticas de equipos
  estadisticasLocal?: EstadisticasEquipoFutbol;
  estadisticasVisitante?: EstadisticasEquipoFutbol;
}

/**
 * Partido con estadísticas completas para análisis contextual
 */
export interface PartidoFutbolEstadistico {
  id: string;
  fechaPartido: string;
  equipoLocalId: string;
  equipoVisitanteId: string;
  equipoLocalNombre: string;
  equipoVisitanteNombre: string;
  golesLocal: number;
  golesVisitante: number;
  cornersLocal: number;
  cornersVisitante: number;
  cornersLocal1t?: number;
  cornersLocal2t?: number;
  cornersVisitante1t?: number;
  cornersVisitante2t?: number;
  disparosLocal: number;
  disparosVisitante: number;
  disparosArcoLocal: number;
  disparosArcoVisitante: number;
}

// ══════════════════════════════════════════════════════════════
// TIPOS DE MERCADO Y PREDICCIÓN
// ══════════════════════════════════════════════════════════════

/**
 * Tipos de mercado de fútbol
 */
export type TipoMercadoFutbol =
  // Corners (9)
  | 'CORNERS_1T'
  | 'CORNERS_2T'
  | 'CORNERS_FT'
  | 'CORNERS_LOCAL_1T'
  | 'CORNERS_LOCAL_2T'
  | 'CORNERS_LOCAL_FT'
  | 'CORNERS_VISITANTE_1T'
  | 'CORNERS_VISITANTE_2T'
  | 'CORNERS_VISITANTE_FT'
  // Goles (9)
  | 'GOLES_1T'
  | 'GOLES_2T'
  | 'GOLES_FT'
  | 'GOLES_LOCAL_1T'
  | 'GOLES_LOCAL_2T'
  | 'GOLES_LOCAL_FT'
  | 'GOLES_VISITANTE_1T'
  | 'GOLES_VISITANTE_2T'
  | 'GOLES_VISITANTE_FT'
  // Disparos (6)
  | 'DISPAROS_FT'
  | 'DISPAROS_ARCO_FT'
  | 'DISPAROS_LOCAL_FT'
  | 'DISPAROS_LOCAL_ARCO_FT'
  | 'DISPAROS_VISITANTE_FT'
  | 'DISPAROS_VISITANTE_ARCO_FT';

/**
 * Categoría de mercado
 */
export type CategoriaMercado = 'corners' | 'goles' | 'disparos';

/**
 * Nivel de confianza
 */
export type NivelConfianza = 'MUY_ALTA' | 'ALTA' | 'MEDIA' | 'BAJA' | 'MUY_BAJA';

/**
 * Probabilidad por línea
 */
export interface RazonAnalisisFutbol {
  factor: string;
  direccion: 'sube' | 'baja' | 'neutral';
  impacto: number;
  descripcion: string;
}

export interface ProbabilidadLinea {
  linea: number;
  overRaw: number;
  overCalibrada: number;
  underRaw: number;
  underCalibrada: number;
  razones?: RazonAnalisisFutbol[];
}

/**
 * Predicción de mercado
 */
export interface PrediccionMercadoFutbol {
  mercado: TipoMercadoFutbol;
  media: number;
  std: number;
  probabilidades: ProbabilidadLinea[];
  confianza: NivelConfianza;
}

/**
 * Recomendación de apuesta
 */
export interface RecomendacionApuesta {
  mercado: TipoMercadoFutbol;
  lado: 'OVER' | 'UNDER';
  linea: number;
  probabilidad: number;
  confianza: NivelConfianza;
  valorEsperado?: number;
  razon: string;
}

// ══════════════════════════════════════════════════════════════
// TIPOS DE ANÁLISIS
// ══════════════════════════════════════════════════════════════

/**
 * Request de análisis
 */
export interface AnalisisFutbolRequest {
  partidoId: string;
  lineasCorners?: number[]; // Default: [8.5, 9.5, 10.5, 11.5]
  lineasGoles?: number[]; // Default: [1.5, 2.5, 3.5]
  lineasDisparos?: number[]; // Default: [22.5, 24.5, 26.5]
  h2hLimite?: number;
}

/**
 * Response de análisis
 */
export interface AnalisisFutbolResponse {
  exito: boolean;
  partido: PartidoFutbolResumen;
  timestampAnalisis: string;
  // Mercados agrupados por categoría
  mercadosCorners: Record<string, PrediccionMercadoFutbol>;
  mercadosGoles: Record<string, PrediccionMercadoFutbol>;
  mercadosDisparos: Record<string, PrediccionMercadoFutbol>;
  // Recomendaciones ordenadas por confianza
  recomendaciones: RecomendacionApuesta[];
  // Metadata
  modeloVersion: string;
  calibradoresActivos: number;
}

// ══════════════════════════════════════════════════════════════
// TIPOS DE APUESTA
// ══════════════════════════════════════════════════════════════

/**
 * Estado de apuesta
 */
export type EstadoApuesta = 'PENDIENTE' | 'GANADA' | 'PERDIDA' | 'PUSH' | 'CANCELADA' | 'VOID';

/**
 * Request para crear apuesta
 */
export interface ApuestaFutbolRequest {
  partidoId: string;
  mercado: TipoMercadoFutbol;
  lado: 'OVER' | 'UNDER';
  linea: number;
  cuota: number;
  stake: number;
  casaApuestas?: string;
  notas?: string;
}

/**
 * Apuesta registrada
 */
export interface ApuestaFutbol {
  id: string;
  partidoId: string;
  partido: PartidoFutbolResumen;
  mercado: TipoMercadoFutbol;
  lado: 'OVER' | 'UNDER';
  linea: number;
  cuota: number;
  stake: number;
  estado: EstadoApuesta;
  // Análisis del sistema
  probabilidadSistema: number;
  confianza: NivelConfianza;
  valorEsperado: number;
  gananciasPotenciales: number;
  // Resultado (si resuelto)
  resultadoReal?: number;
  gananciasReales?: number;
  // Metadata
  casaApuestas?: string;
  notas?: string;
  fechaCreacion: string;
  fechaResolucion?: string;
}

/**
 * Filtros para apuestas
 */
export interface FiltrosApuestas {
  estado?: EstadoApuesta;
  mercado?: TipoMercadoFutbol;
  confianza?: NivelConfianza;
  desde?: string;
  hasta?: string;
  busqueda?: string;
  limite?: number;
  offset?: number;
}

/**
 * Resumen de apuestas
 */
export interface ResumenApuestasFutbol {
  total: number;
  pendientes: number;
  ganadas: number;
  perdidas: number;
  push: number;
  roi: number | null;
  winRate: number | null;
  stakeTotal: number;
  gananciaNeta: number;
}

/**
 * Resumen de resolución de apuestas
 */
export interface ResumenResolucion {
  procesadas: number;
  ganadas: number;
  perdidas: number;
  push: number;
  errores: number;
}

/**
 * Filtros para estadísticas
 */
export interface FiltrosEstadisticas {
  mercado?: TipoMercadoFutbol;
  desde?: string;
  hasta?: string;
}

// ══════════════════════════════════════════════════════════════
// TIPOS DE MÉTRICAS
// ══════════════════════════════════════════════════════════════

/**
 * Métricas de calibración
 */
export interface MetricasCalibracionFutbol {
  mercado: TipoMercadoFutbol;
  brierScore: number;
  ece: number;
  logLoss: number;
  nPredicciones: number;
  calibradorActivo: boolean;
  metodoCalibrador?: string;
  mejoraBrier?: number;
}

/**
 * Métricas de rendimiento
 */
export interface MetricasRendimientoFutbol {
  mercado: TipoMercadoFutbol;
  nApuestas: number;
  ganadas: number;
  perdidas: number;
  roi: number;
  winRate: number;
  stakeTotal: number;
  gananciaNeta: number;
}

/**
 * Estado del modelo
 */
export interface EstadoModeloFutbol {
  tipoModelo: 'CORNERS' | 'GOLES' | 'DISPAROS';
  version: string;
  fechaEntrenamiento: string;
  mae: number;
  rmse: number;
  r2: number;
  nPartidosEntrenamiento: number;
  nEquipos: number;
}

/**
 * Resumen del sistema
 */
export interface ResumenSistema {
  modelos: EstadoModeloFutbol[];
  calibradores: MetricasCalibracionFutbol[];
  rendimiento: MetricasRendimientoFutbol[];
  ultimaActualizacion: string;
  estadoGeneral: 'saludable' | 'degradado' | 'error';
}

// ══════════════════════════════════════════════════════════════
// TIPOS DE CONFIGURACIÓN Y UI
// ══════════════════════════════════════════════════════════════

/**
 * Configuración de mercados
 */
export const MERCADOS_CORNERS: TipoMercadoFutbol[] = [
  'CORNERS_FT',
  'CORNERS_1T',
  'CORNERS_2T',
  'CORNERS_LOCAL_FT',
  'CORNERS_LOCAL_1T',
  'CORNERS_LOCAL_2T',
  'CORNERS_VISITANTE_FT',
  'CORNERS_VISITANTE_1T',
  'CORNERS_VISITANTE_2T',
];

export const MERCADOS_GOLES: TipoMercadoFutbol[] = [
  'GOLES_FT',
  'GOLES_1T',
  'GOLES_2T',
  'GOLES_LOCAL_FT',
  'GOLES_LOCAL_1T',
  'GOLES_LOCAL_2T',
  'GOLES_VISITANTE_FT',
  'GOLES_VISITANTE_1T',
  'GOLES_VISITANTE_2T',
];

export const MERCADOS_DISPAROS: TipoMercadoFutbol[] = [
  'DISPAROS_FT',
  'DISPAROS_ARCO_FT',
  'DISPAROS_LOCAL_FT',
  'DISPAROS_LOCAL_ARCO_FT',
  'DISPAROS_VISITANTE_FT',
  'DISPAROS_VISITANTE_ARCO_FT',
];

/**
 * Etiquetas legibles para mercados
 */
export const ETIQUETAS_MERCADOS: Record<TipoMercadoFutbol, string> = {
  // Corners
  CORNERS_1T: 'Corners 1T',
  CORNERS_2T: 'Corners 2T',
  CORNERS_FT: 'Corners FT',
  CORNERS_LOCAL_1T: 'Corners Local 1T',
  CORNERS_LOCAL_2T: 'Corners Local 2T',
  CORNERS_LOCAL_FT: 'Corners Local FT',
  CORNERS_VISITANTE_1T: 'Corners Visitante 1T',
  CORNERS_VISITANTE_2T: 'Corners Visitante 2T',
  CORNERS_VISITANTE_FT: 'Corners Visitante FT',
  // Goles
  GOLES_1T: 'Goles 1T',
  GOLES_2T: 'Goles 2T',
  GOLES_FT: 'Goles FT',
  GOLES_LOCAL_1T: 'Goles Local 1T',
  GOLES_LOCAL_2T: 'Goles Local 2T',
  GOLES_LOCAL_FT: 'Goles Local FT',
  GOLES_VISITANTE_1T: 'Goles Visitante 1T',
  GOLES_VISITANTE_2T: 'Goles Visitante 2T',
  GOLES_VISITANTE_FT: 'Goles Visitante FT',
  // Disparos
  DISPAROS_FT: 'Disparos FT',
  DISPAROS_ARCO_FT: 'Disparos a Puerta FT',
  DISPAROS_LOCAL_FT: 'Disparos Local FT',
  DISPAROS_LOCAL_ARCO_FT: 'Disparos Local a Puerta FT',
  DISPAROS_VISITANTE_FT: 'Disparos Visitante FT',
  DISPAROS_VISITANTE_ARCO_FT: 'Disparos Visitante a Puerta FT',
};

/**
 * Configuración de colores por nivel de confianza
 */
export const COLORES_CONFIANZA: Record<
  NivelConfianza,
  { bg: string; border: string; text: string }
> = {
  MUY_ALTA: {
    bg: 'bg-neon-verde/20',
    border: 'border-neon-verde/50',
    text: 'text-neon-verde',
  },
  ALTA: {
    bg: 'bg-neon-verde/10',
    border: 'border-neon-verde/30',
    text: 'text-neon-verde',
  },
  MEDIA: {
    bg: 'bg-advertencia-50',
    border: 'border-advertencia-500/30',
    text: 'text-advertencia-500',
  },
  BAJA: {
    bg: 'bg-neon-rojo/10',
    border: 'border-neon-rojo/30',
    text: 'text-neon-rojo',
  },
  MUY_BAJA: {
    bg: 'bg-neon-rojo/20',
    border: 'border-neon-rojo/50',
    text: 'text-neon-rojo',
  },
};

/**
 * Configuración de colores por estado de apuesta
 */
export const COLORES_ESTADO_APUESTA: Record<
  EstadoApuesta,
  { bg: string; text: string; icono: string }
> = {
  PENDIENTE: {
    bg: 'bg-advertencia-50',
    text: 'text-advertencia-500',
    icono: '🟡',
  },
  GANADA: {
    bg: 'bg-exito-50',
    text: 'text-exito-500',
    icono: '🟢',
  },
  PERDIDA: {
    bg: 'bg-error-50',
    text: 'text-error-500',
    icono: '🔴',
  },
  PUSH: {
    bg: 'bg-futurista-medio/50',
    text: 'text-texto-secundario',
    icono: '⚪',
  },
  CANCELADA: {
    bg: 'bg-futurista-medio/50',
    text: 'text-texto-terciario line-through',
    icono: '❌',
  },
  VOID: {
    bg: 'bg-futurista-medio/50',
    text: 'text-texto-terciario',
    icono: '⚫',
  },
};

/**
 * Líneas por defecto para cada categoría
 */
export const LINEAS_DEFAULT = {
  corners: [8.5, 9.5, 10.5, 11.5],
  goles: [1.5, 2.5, 3.5],
  disparos: [22.5, 24.5, 26.5],
};

/**
 * Casas de apuestas disponibles
 */
export const CASAS_APUESTAS = [
  'Bet365',
  'Betway',
  'Betfair',
  'William Hill',
  'Pinnacle',
  '1xBet',
  'Unibet',
  'Bwin',
  'Codere',
  'Otra',
];
