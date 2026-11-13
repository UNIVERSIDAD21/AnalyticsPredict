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

/** País por código canónico: también permite encontrar una liga por su país. */
export function paisActualizacion(codigo: string): string {
  const paises: Record<string, string> = { ARG: 'Argentina', BRA: 'Brasil', COL: 'Colombia',
    ENG: 'Inglaterra', ESP: 'España', FRA: 'Francia', GER: 'Alemania', ITA: 'Italia', USA: 'Estados Unidos' };
  return paises[codigo.split('_')[0]] ?? '';
}

export interface MotivoPendiente {
  titulo: string;
  accion: string;
  registros?: number;
  detalles: string[];
}

function explicarMotivo(motivo: string): Pick<MotivoPendiente, 'titulo' | 'accion'> {
  if (/\bTBD\b/.test(motivo)) return { titulo: 'Rival por definir en la fuente', accion: 'Esperar a que la fuente publique el equipo definitivo; no sustituirlo por uno supuesto.' };
  if (motivo.startsWith('Alta sin hora')) return { titulo: 'Horario sin confirmar en la fuente', accion: 'Esperar un horario confirmado y volver a actualizar manualmente. No se asigna una hora inventada.' };
  if (/sin equivalencia revisada|sin crosswalk exacto/.test(motivo)) return { titulo: 'Equipo o temporada sin vincular al catálogo', accion: 'Validar la identidad exacta del equipo y la temporada antes de incorporar el evento.' };
  if (/ESTADISTICAS_AUSENTES|ESTADISTICAS_LOCALES_PENDIENTES/.test(motivo)) return { titulo: 'Estadísticas ausentes', accion: 'Consultar una fuente que publique los campos del partido y validar sus valores antes de guardarlos.' };
  if (motivo === 'PENDIENTES_COLA_SQL') return { titulo: 'Pendientes acumulados de ciclos anteriores', accion: 'Consultar el desglose de la cola: puede incluir campos estadísticos fuera de la ventana actual.' };
  if (/prorroga|prórroga/.test(motivo)) return { titulo: 'Estadísticas sin separar los 90 minutos y la prórroga', accion: 'Conseguir un desglose de tiempo reglamentario. No mezclar estadísticas de prórroga con las de 90 minutos.' };
  if (/Cifra inferior a goles/.test(motivo)) return { titulo: 'Estadísticas que no superan el control de coherencia', accion: 'Contrastar el dato y los posibles autogoles con evidencia del partido; conservar el campo vacío mientras no se resuelva.' };
  if (/Conflicto /.test(motivo)) return { titulo: 'Fuentes con valores contradictorios', accion: 'Resolver la discrepancia con evidencia verificable; no elegir un valor por conveniencia.' };
  if (/no publica campo/.test(motivo)) return { titulo: 'La fuente consultada no publica el campo', accion: 'Buscar otra fuente verificable; si no existe, el campo permanece vacío.' };
  if (/No localizado en resultados/.test(motivo)) return { titulo: 'Partido no localizado en la fuente consultada', accion: 'Verificar el evento exacto en otra fuente antes de completar estadísticas.' };
  if (/Resultado final distinto/.test(motivo)) return { titulo: 'Marcador de la fuente sin conciliar', accion: 'Conciliar la identidad y el resultado del partido antes de aceptar sus estadísticas.' };
  if (/Horario del final canónico protegido/.test(motivo)) return { titulo: 'La fuente contradice el horario de un partido finalizado', accion: 'Se conservó el horario guardado. Contrastar el horario con evidencia oficial antes de modificarlo.' };
  if (motivo === 'FINAL_LOCAL_NO_CONTRASTADO_CON_FUENTE') return { titulo: 'Resultado guardado sin contraste en esta revisión', accion: 'Verificar el resultado en la fuente exacta; esta incidencia no demuestra que falte el marcador.' };
  if (motivo.startsWith('PRESUPUESTO_ESTADISTICAS')) return { titulo: 'Se alcanzó el límite de consultas del ciclo', accion: 'Continuar en una actualización manual posterior; no se ejecuta automáticamente.' };
  if (motivo.startsWith('SIN_ADAPTADOR')) return { titulo: 'Sin fuente vigente configurada', accion: 'El histórico se conserva. Incorporar una fuente compatible requiere un trabajo separado.' };
  return { titulo: motivo.replace(/_/g, ' '), accion: 'Contrastar el motivo registrado antes de modificar los datos; no hay una resolución automática acreditada.' };
}

/** Conserva todos los motivos originales. Registros de cola no equivale a partidos únicos. */
export function motivosPendientesActualizacion(liga: LigaActualizacion): MotivoPendiente[] {
  const grupos = new Map<string, MotivoPendiente>();
  for (const entrada of liga.resultado?.pendientes_cola?.motivos ?? []) {
    const explicacion = explicarMotivo(entrada.motivo);
    const grupo = grupos.get(explicacion.titulo) ?? { ...explicacion, registros: 0, detalles: [] };
    grupo.registros = (grupo.registros ?? 0) + entrada.obligaciones;
    grupo.detalles.push(entrada.motivo);
    grupos.set(grupo.titulo, grupo);
  }
  // La incidencia genérica de cola no duplica sus motivos específicos.
  for (const incidencia of liga.resultado?.incidencias ?? []) {
    if (incidencia.motivo === 'PENDIENTES_COLA_SQL' && grupos.size) continue;
    const explicacion = explicarMotivo(incidencia.motivo);
    const grupo = grupos.get(explicacion.titulo);
    if (grupo) {
      if (!grupo.detalles.includes(incidencia.motivo)) grupo.detalles.push(incidencia.motivo);
    } else grupos.set(explicacion.titulo, { ...explicacion, detalles: [incidencia.motivo] });
  }
  const a = liga.agenda;
  if ((a?.consultas_pendientes ?? 0) > 0) grupos.set('consultas', { titulo: `${a!.consultas_pendientes} consultas de agenda sin terminar`, accion: 'Continuar la revisión en una actualización manual; una consulta no equivale a un partido ausente.', detalles: [] });
  if ((a?.consultas_error ?? 0) > 0) grupos.set('errores', { titulo: `${a!.consultas_error} consultas de agenda con error`, accion: 'Comprobar la disponibilidad de la fuente y el error antes de reintentar manualmente.', detalles: [] });
  if (!grupos.size && tienePendientesActualizacion(liga)) grupos.set('sin-desglose', {
    titulo: 'Pendiente informado sin motivo desglosado', accion: 'El informe disponible no explica la causa. Consultar el recibo del ciclo; no se presupone que falte un partido.', detalles: [],
  });
  return [...grupos.values()];
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
    || (r?.pendientes_cola?.campos_estadisticas ?? 0) > 0 || (r?.pendientes_cola?.resultados ?? 0) > 0
    || (r?.pendientes_cola?.consultas_resultados ?? 0) > 0;
}
