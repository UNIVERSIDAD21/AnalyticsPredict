import { expect, it } from 'vitest';
import { motivosPendientesActualizacion, tienePendientesActualizacion, type LigaActualizacion } from './actualizacionLigas';

function liga(motivos: { motivo: string; obligaciones: number }[]): LigaActualizacion {
  return { codigo: 'USA_MLS', nombre: 'MLS', archivada: false, resultado: {
    codigo: 'USA_MLS', nombre: 'MLS', deporte: 'futbol', estado: 'PARCIAL', desde: '2026-11-06', hasta: '2026-11-13',
    finales_fuente: 1, insertados: 0, resultados_actualizados: 0, estadisticas_actualizadas: 0, campos_completados: 0,
    incidencias: [{ motivo: 'PENDIENTES_COLA_SQL' }], pendientes_cola: { resultados: 0, eventos_agenda: 12,
      campos_estadisticas: 0, partidos_estadisticas: 0, campos_estadisticas_elegibles: 0, proximo_reintento_en: null, motivos },
  } };
}
it('distingue rival TBD de un equipo real sin vincular y agrupa sin duplicar la incidencia genérica', () => {
  const motivos = motivosPendientesActualizacion(liga([
    { motivo: 'Alta sin hora: no se inventa fecha canónica UTC', obligaciones: 6 },
    { motivo: "Identidad o temporada sin equivalencia revisada ('1'): Local — TBD Away", obligaciones: 2 },
    { motivo: 'Equipo sin crosswalk exacto: TBD', obligaciones: 4 },
    { motivo: "Identidad o temporada sin equivalencia revisada ('2'): Club A — Club B", obligaciones: 1 },
  ]));
  expect(motivos.map(m => [m.titulo, m.registros])).toEqual([
    ['Horario sin confirmar en la fuente', 6], ['Rival por definir en la fuente', 6], ['Equipo o temporada sin vincular al catálogo', 1],
  ]);
  expect(motivos[1].detalles).toHaveLength(2);
});
it('conserva desconocidos y no afirma recuperación automática', () => {
  const [m] = motivosPendientesActualizacion(liga([{ motivo: 'MOTIVO_NUEVO', obligaciones: 2 }]));
  expect(m.titulo).toBe('MOTIVO NUEVO'); expect(m.detalles).toEqual(['MOTIVO_NUEVO']);
  expect(m.accion).toContain('no hay una resolución automática acreditada');
});
it('conserva restricciones de coherencia, conflictos y prórroga con sus acciones', () => {
  const motivos = motivosPendientesActualizacion(liga([
    { motivo: 'Cifra inferior a goles; sin autogoles documentados que lo expliquen', obligaciones: 5 },
    { motivo: 'Conflicto ScoreMondo vs YS Scores sin origen/revision que lo resuelva', obligaciones: 4 },
    { motivo: 'No desglosa estadisticas 90min frente a prorroga', obligaciones: 42 },
  ]));
  expect(motivos).toHaveLength(3);
  expect(motivos[0].accion).toContain('conservar el campo vacío');
  expect(motivos[1].titulo).toBe('Fuentes con valores contradictorios');
  expect(motivos[2].accion).toContain('No mezclar estadísticas de prórroga');
});
it('no oculta consultas de resultados pendientes y explica la ausencia de desglose', () => {
  const l = liga([]); l.resultado!.estado = 'COMPLETA_EN_VENTANA'; l.resultado!.incidencias = [];
  l.resultado!.pendientes_cola!.eventos_agenda = 0; l.resultado!.pendientes_cola!.consultas_resultados = 2;
  expect(tienePendientesActualizacion(l)).toBe(true);
  expect(motivosPendientesActualizacion(l)[0].titulo).toBe('Pendiente informado sin motivo desglosado');
});
