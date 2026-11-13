/** Contrato de lectura del actualizador; contadores de distintos alcances no se suman. */
export interface EstadoActualizacion {
  estado: string;
  etapa?: string;
  terminado_en?: string;
  ejecucion_id?: string;
  cobertura_operativa?: {
    desde?: string; hasta?: string;
    competiciones_diarias: number; competiciones_diarias_con_incidencias: number;
    competiciones_archivadas: number; consultas_agenda_pendientes: number;
    consultas_agenda_error: number; eventos_agenda_pendientes: number;
    campos_estadisticas_ausentes_ventana: number; partidos_estadisticas_pendientes_ventana: number;
  };
  agenda_multiliga?: {
    desde: string; hasta: string; operaciones: number;
    ejecucion_lotes?: { lotes?: { lote: string; turnos: number; consultas: number }[];
      turnos_consumidos?: number; limite_turnos?: number; motivo_parada?: string };
    ligas: { codigo: string; nombre: string; estado: string; consultas_observadas: number;
      consultas_pendientes: number; consultas_error: number; eventos_enumerados: number;
      horas_confirmadas: number; ultima_fecha_publicada: string | null; eventos_pendientes_cola?: number }[];
  };
  fuentes_verificadas_en?: string | null;
  cambio_guardado_en?: string | null;
  detalle?: string;
  error_actualizacion?: string;
  iniciado_en?: string;
  progreso?: { ligas_revisadas: number; ligas_total: number };
  ligas_resultado?: { codigo: string; nombre: string; deporte: string; estado: string;
    desde: string; hasta: string; finales_fuente: number; insertados: number;
    resultados_actualizados: number; estadisticas_actualizadas: number; campos_completados: number;
    campos_escritos?: number; campos_acreditados?: number; campos_no_acreditados?: number;
    ambito?: string; afecta_cobertura_diaria?: boolean;
    pendientes_cola?: { resultados: number; eventos_agenda: number; campos_estadisticas: number;
      partidos_estadisticas: number; campos_estadisticas_elegibles: number; proximo_reintento_en: string | null;
      consultas_resultados?: number; motivos?: { motivo: string; obligaciones: number }[] };
    estadisticas_ventana?: { partidos_estadisticas_pendientes: number; campos_estadisticas_ausentes: number } | null;
    incidencias: { motivo: string }[] }[];
  correccion_calidad?: { campos_escritos: number; campos_acreditados: number;
    campos_no_acreditados: number; partidos_en_cuarentena: number };
  modelos?: { nombre: string; version?: number | string; corte: string | null;
    finales_posteriores?: number; necesita_actualizacion?: boolean }[];
  actualizacion_ligas?: {
    ultimo_ciclo_agendas: { terminado_en: string; estado: string } | null;
    ultimo_ciclo_integral: { terminado_en: string; estado: string } | null;
    ultima_completa_en: string | null;
    ligas: { codigo: string; nombre: string; deporte: string; cambio_en: string | null;
      resultados_hasta: string | null; estadisticas_hasta: string | null;
      verificacion_agenda_en: string | null; estado_agenda: string;
      estadisticas: { estado: string; verificado_en?: string; detalle?: string } }[];
  } | null;
  cobertura?: { competicion: string; hasta_solicitado: string; futuros_con_hora: number; ultimo_inicio_publicado: string | null; incidencias: number }[];
}
