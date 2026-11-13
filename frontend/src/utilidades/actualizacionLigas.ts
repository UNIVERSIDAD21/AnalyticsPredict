import type { EstadoActualizacion } from '../tipos/actualizacionLigas';

export type LigaResultado = NonNullable<EstadoActualizacion['ligas_resultado']>[number];
export type LigaAgenda = NonNullable<EstadoActualizacion['agenda_multiliga']>['ligas'][number];
export type LigaFrescura = NonNullable<EstadoActualizacion['actualizacion_ligas']>['ligas'][number];
export interface LigaActualizacion {
  codigo: string;
  nombre: string;
  deporte?: string;
  resultado?: LigaResultado;
  agenda?: LigaAgenda;
  frescura?: LigaFrescura;
  archivada: boolean;
}

export function fechaActualizacion(valor?: string | null): string {
  if (!valor) return 'sin acreditar';
  const date = new Date(valor);
  return Number.isNaN(date.getTime()) ? 'N/D' : date.toLocaleString('es-CO', { timeZone: 'America/Bogota' }) + ' COT';
}

export function corteActualizacion(valor?: string | null): string {
  return !valor ? 'N/D' : /^\d{4}-\d{2}-\d{2}$/.test(valor) ? valor : fechaActualizacion(valor);
}

export function estadoActualizacionLegible(valor?: string): string {
  const nombres: Record<string, string> = {
    PARCIAL: 'Con pendientes', COMPLETO: 'Revisión terminada', COMPLETA_EN_VENTANA: 'Revisada en esta ventana',
    SIN_FINALES_EN_VENTANA: 'Sin finales en ventana', SIN_ADAPTADOR: 'Sin fuente configurada',
    SIN_EVENTOS_PUBLICADOS: 'Sin eventos publicados', OBSERVADA_EN_FUENTE: 'Observada en fuente',
    EN_CURSO: 'En curso', SOLICITADA: 'Solicitada', PAUSADA_CALIDAD: 'Pausada por calidad',
    SIN_SINCRONIZAR: 'Sin revisión acreditada', INTERRUMPIDA: 'Interrumpida', ERROR: 'Error de actualización',
    PLAN_SIN_APLICAR: 'Revisión sin guardar', SIN_ACREDITAR: 'Sin acreditar',
  };
  return valor ? nombres[valor] ?? valor.replace(/_/g, ' ') : 'Sin revisión';
}

export function motivoActualizacionLegible(valor: string): string {
  if (valor.startsWith('SIN_ADAPTADOR')) return 'Esta competición no tiene una fuente vigente configurada. Su histórico se conserva.';
  if (valor === 'FINAL_LOCAL_NO_CONTRASTADO_CON_FUENTE') return 'Hay un resultado guardado que no pudo contrastarse con la fuente en esta revisión.';
  if (valor === 'ESTADISTICAS_LOCALES_PENDIENTES' || valor === 'ESTADISTICAS_AUSENTES') return 'Todavía faltan estadísticas publicadas o vinculadas para este partido.';
  if (valor.startsWith('PRESUPUESTO_ESTADISTICAS')) return 'Este partido queda pendiente del siguiente ciclo por el límite de consultas.';
  return valor;
}

/** Unión por código exacto de competición, nunca por nombres parecidos. */
export function unirLigasActualizacion(estado: EstadoActualizacion | null): LigaActualizacion[] {
  const ligas = new Map<string, LigaActualizacion>();
  const obtener = (codigo: string, nombre: string) => {
    if (!ligas.has(codigo)) ligas.set(codigo, { codigo, nombre, archivada: false });
    return ligas.get(codigo)!;
  };
  estado?.actualizacion_ligas?.ligas.forEach(frescura => {
    Object.assign(obtener(frescura.codigo, frescura.nombre), { frescura, deporte: frescura.deporte });
  });
  estado?.agenda_multiliga?.ligas.forEach(agenda => {
    obtener(agenda.codigo, agenda.nombre).agenda = agenda;
  });
  estado?.ligas_resultado?.forEach(resultado => {
    Object.assign(obtener(resultado.codigo, resultado.nombre), {
      resultado, nombre: resultado.nombre, deporte: resultado.deporte,
      archivada: resultado.afecta_cobertura_diaria === false,
    });
  });
  return [...ligas.values()].sort((a, b) => Number(tienePendientesActualizacion(b)) - Number(tienePendientesActualizacion(a)) || a.nombre.localeCompare(b.nombre, 'es'));
}

export function eventosPendientesActualizacion(liga: LigaActualizacion): number | undefined {
  return liga.agenda?.eventos_pendientes_cola ?? liga.resultado?.pendientes_cola?.eventos_agenda;
}

export function tienePendientesActualizacion(liga: LigaActualizacion): boolean {
  const { resultado: r, agenda: a } = liga;
  return (r?.incidencias?.length ?? 0) > 0 || ['PARCIAL', 'ERROR', 'SIN_ADAPTADOR', 'INTERRUMPIDA'].includes(r?.estado ?? '')
    || (eventosPendientesActualizacion(liga) ?? 0) > 0
    || (a?.consultas_pendientes ?? 0) > 0 || (a?.consultas_error ?? 0) > 0
    || (r?.estadisticas_ventana?.campos_estadisticas_ausentes ?? 0) > 0
    || (r?.pendientes_cola?.campos_estadisticas ?? 0) > 0 || (r?.pendientes_cola?.resultados ?? 0) > 0;
}
