import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { EstadoSincronizacionAgenda } from './EstadoSincronizacionAgenda';
import { clienteAPI } from '../../servicios/api';
import type { EstadoActualizacion } from '../../tipos/actualizacionLigas';

vi.mock('../../servicios/api', () => ({ clienteAPI: { get: vi.fn(), post: vi.fn() }, extraerMensajeError: () => 'Servicio no disponible' }));
afterEach(() => { cleanup(); vi.useRealTimers(); });
beforeEach(() => { vi.resetAllMocks(); vi.mocked(clienteAPI.get).mockResolvedValue({ data: { estado: 'PARCIAL' } }); });

function datos(): EstadoActualizacion {
  const resultado = { deporte: 'futbol', estado: 'PARCIAL', desde: '2026-11-06', hasta: '2026-11-13',
    finales_fuente: 2, insertados: 0, resultados_actualizados: 0, estadisticas_actualizadas: 0,
    campos_completados: 0, campos_escritos: 0, campos_acreditados: 0, campos_no_acreditados: 0,
    incidencias: [{ motivo: 'ESTADISTICAS_AUSENTES' }] };
  return { estado: 'PARCIAL', fuentes_verificadas_en: '2026-11-13T12:24:09Z', terminado_en: '2026-11-13T12:24:09Z',
    cobertura_operativa: { competiciones_diarias: 22, competiciones_diarias_con_incidencias: 4, competiciones_archivadas: 2,
      consultas_agenda_pendientes: 0, consultas_agenda_error: 0, eventos_agenda_pendientes: 133,
      campos_estadisticas_ausentes_ventana: 6, partidos_estadisticas_pendientes_ventana: 1 },
    ligas_resultado: [
      { ...resultado, codigo: 'FRA_COUPE', nombre: 'Coupe de France', afecta_cobertura_diaria: true,
        estadisticas_ventana: { campos_estadisticas_ausentes: 6, partidos_estadisticas_pendientes: 1 },
        pendientes_cola: { resultados: 0, eventos_agenda: 64, campos_estadisticas: 12, partidos_estadisticas: 2,
          campos_estadisticas_elegibles: 0, proximo_reintento_en: '2026-11-13T19:16:34Z' } },
      { ...resultado, codigo: 'COL_COPA', nombre: 'Copa BetPlay', afecta_cobertura_diaria: true,
        estadisticas_ventana: { campos_estadisticas_ausentes: 0, partidos_estadisticas_pendientes: 0 },
        pendientes_cola: { resultados: 0, eventos_agenda: 0, campos_estadisticas: 6, partidos_estadisticas: 1,
          campos_estadisticas_elegibles: 0, proximo_reintento_en: null } },
      { ...resultado, codigo: 'ARG_MARADONA', nombre: 'Copa Maradona', afecta_cobertura_diaria: false, estado: 'SIN_ADAPTADOR' },
    ],
    agenda_multiliga: { desde: '2026-11-12', hasta: '2027-01-12', operaciones: 0, ligas: [
      { codigo: 'nba', nombre: 'NBA', estado: 'PARCIAL', consultas_observadas: 63, consultas_pendientes: 0,
        consultas_error: 0, eventos_enumerados: 403, horas_confirmadas: 397, ultima_fecha_publicada: '2027-01-12', eventos_pendientes_cola: 6 },
      { codigo: 'wnba', nombre: 'WNBA', estado: 'SIN_EVENTOS_PUBLICADOS', consultas_observadas: 63, consultas_pendientes: 0,
        consultas_error: 0, eventos_enumerados: 0, horas_confirmadas: 0, ultima_fecha_publicada: null },
    ] },
    modelos: [{ nombre: 'NBA candidato', version: 2191, corte: '2026-11-05', finales_posteriores: 51, necesita_actualizacion: true }],
    actualizacion_ligas: { ultima_completa_en: null, ultimo_ciclo_integral: { terminado_en: '2026-11-13T12:24:09Z', estado: 'PARCIAL' }, ultimo_ciclo_agendas: null,
      ligas: [{ codigo: 'nba', nombre: 'NBA', deporte: 'baloncesto', cambio_en: null, resultados_hasta: '2026-11-12', estadisticas_hasta: '2026-11-12', verificacion_agenda_en: null, estado_agenda: 'PARCIAL', estadisticas: { estado: 'COMPLETA_EN_VENTANA' } }] },
  };
}
async function abrirTablero(d = datos()) {
  vi.mocked(clienteAPI.get).mockResolvedValue({ data: d }); render(<EstadoSincronizacionAgenda vista="tablero" />);
  await screen.findByText(/Ejecución terminada/);
}
function abrirLiga(nombre: string) {
  fireEvent.click(screen.getByText(`Ver detalle de ${nombre}`));
  return screen.getByText(`Ver detalle de ${nombre}`).closest('details')!;
}

it('separa contadores de ventana, cola, consultas y archivadas', async () => {
  await abrirTablero();
  expect(screen.getByLabelText('Incidencias diarias')).toHaveTextContent('4 / 22');
  expect(screen.getByLabelText('Eventos de agenda pendientes')).toHaveTextContent('133');
  expect(screen.getByLabelText('Estadísticas ausentes en ventana')).toHaveTextContent('1 partido guardado');
  const france = abrirLiga('Coupe de France');
  expect(france).toHaveTextContent('12 campos estadísticos en 2 partidos');
  expect(france).toHaveTextContent('En la ventana: 6 campos ausentes en 1 partidos guardados');
  expect(france).toHaveTextContent('no se ejecuta automáticamente');
  expect(clienteAPI.post).not.toHaveBeenCalled();
});
it('focaliza agenda y cola aunque no haya campos ausentes en ventana', async () => {
  await abrirTablero();
  expect(screen.getByText('Ver detalle de NBA')).toBeInTheDocument();
  expect(screen.getByText('Ver detalle de Copa BetPlay')).toBeInTheDocument();
  expect(screen.queryByText('Ver detalle de WNBA')).toBeNull();
  expect(screen.getByRole('button', { name: /Con pendientes/ })).toHaveTextContent('3');
});
it('une códigos exactos sin duplicar NBA y no archiva un feed vacío', async () => {
  await abrirTablero(); fireEvent.click(screen.getByRole('button', { name: /Todas las diarias/ }));
  expect(screen.getAllByText('Ver detalle de NBA')).toHaveLength(1);
  expect(screen.getByText('Ver detalle de WNBA')).toBeInTheDocument();
  expect(screen.queryByText('Ver detalle de Copa Maradona')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: /Archivadas/ }));
  expect(screen.getByText('Ver detalle de Copa Maradona')).toBeInTheDocument();
  expect(screen.queryByText('Ver detalle de WNBA')).toBeNull();
  expect(screen.getByText(/Torneos archivados: fuera del contador diario/)).toBeInTheDocument();
});
it('filtra por búsqueda y deporte sin disparar solicitudes de red', async () => {
  await abrirTablero();
  fireEvent.change(screen.getByLabelText('Buscar competición'), { target: { value: 'coupe' } });
  expect(screen.queryByText('Ver detalle de NBA')).toBeNull();
  fireEvent.change(screen.getByLabelText('Deporte'), { target: { value: 'baloncesto' } });
  expect(screen.getByText('No hay competiciones para estos filtros.')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Limpiar búsqueda y deporte' }));
  expect(screen.getByText('Ver detalle de NBA')).toBeInTheDocument();
  expect(clienteAPI.get).toHaveBeenCalledTimes(1); expect(clienteAPI.post).not.toHaveBeenCalled();
});
it('conserva los cortes y motivos sin prometer reentrenamiento', async () => {
  await abrirTablero(); expect(abrirLiga('NBA')).toHaveTextContent('Resultados hasta: 2026-11-12');
  abrirLiga('Copa BetPlay'); expect(screen.getAllByText(/Todavía faltan estadísticas publicadas/).length).toBeGreaterThan(0);
  fireEvent.click(screen.getByText('Modelos y cortes de entrenamiento'));
  expect(screen.getByText('51 finales guardados posteriores.')).toBeInTheDocument();
  expect(screen.getByText(/Preparar un candidato es una operación separada/)).toBeInTheDocument();
  expect(screen.getByLabelText('Última actualización completa de todas las ligas')).toHaveTextContent('Sin acreditar');
});
it('ofrece un resumen compacto con enlace al tablero en las agendas', async () => {
  vi.mocked(clienteAPI.get).mockResolvedValue({ data: datos() }); render(<EstadoSincronizacionAgenda />);
  expect(await screen.findByRole('link', { name: /Abrir tablero de actualización/ })).toHaveAttribute('href', '/actualizaciones');
  expect(screen.queryByLabelText('Buscar competición')).toBeNull(); expect(clienteAPI.post).not.toHaveBeenCalled();
});
it('solo el botón manual solicita una actualización y bloquea el doble clic', async () => {
  let resolver!: (r: { data: EstadoActualizacion }) => void;
  vi.mocked(clienteAPI.post).mockImplementation(() => new Promise(resolve => { resolver = resolve; }));
  await abrirTablero(); const boton = screen.getByRole('button', { name: 'Actualizar todas las ligas' });
  fireEvent.click(boton); fireEvent.click(boton);
  expect(clienteAPI.post).toHaveBeenCalledTimes(1); expect(clienteAPI.post).toHaveBeenCalledWith('/api/agendas/sincronizar');
  expect(screen.getByRole('button', { name: 'Solicitando actualización…' })).toBeDisabled();
  resolver({ data: { estado: 'SOLICITADA', detalle: 'Verificación solicitada, todavía no terminada' } });
  expect(await screen.findByRole('status')).toHaveTextContent('todavía no terminada');
  expect(screen.getByRole('button', { name: 'Actualizar todas las ligas' })).toBeDisabled();
});
it('consultar estado hace GET y nunca POST', async () => {
  await abrirTablero(); fireEvent.click(screen.getByRole('button', { name: 'Consultar estado' }));
  await waitFor(() => expect(clienteAPI.get).toHaveBeenCalledTimes(2)); expect(clienteAPI.post).not.toHaveBeenCalled();
});
it('no presenta una lectura fallida como cero pendientes o datos frescos', async () => {
  vi.mocked(clienteAPI.get).mockRejectedValue(new Error('offline')); render(<EstadoSincronizacionAgenda vista="tablero" />);
  expect(await screen.findByRole('alert')).toHaveTextContent('Servicio no disponible');
  expect(screen.getByLabelText('Eventos de agenda pendientes')).toHaveTextContent('N/D');
  expect(screen.getByRole('button', { name: 'Actualizar todas las ligas' })).toBeDisabled();
});
it('conserva el estado anterior con aviso si el refresco falla', async () => {
  await abrirTablero(); vi.mocked(clienteAPI.get).mockRejectedValue(new Error('offline'));
  fireEvent.click(screen.getByRole('button', { name: 'Consultar estado' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('no es una verificación nueva');
  expect(screen.getByLabelText('Eventos de agenda pendientes')).toHaveTextContent('133');
});
it('expone progreso medido y bloquea otra solicitud mientras está en curso', async () => {
  vi.mocked(clienteAPI.get).mockResolvedValue({ data: { estado: 'EN_CURSO', detalle: 'Revisando NBA', progreso: { ligas_revisadas: 8, ligas_total: 23 } } });
  render(<EstadoSincronizacionAgenda vista="tablero" />);
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('8/23 competiciones'));
  expect(screen.getByRole('progressbar')).toHaveAttribute('value', '8'); expect(screen.getByRole('progressbar')).toHaveAttribute('max', '23');
  expect(screen.getByRole('button', { name: 'Actualizar todas las ligas' })).toBeDisabled();
});
it('mantiene la pausa de calidad y distingue escrito de acreditado', async () => {
  const d = datos(); d.estado = 'PAUSADA_CALIDAD';
  d.correccion_calidad = { campos_escritos: 762, campos_acreditados: 642, campos_no_acreditados: 120, partidos_en_cuarentena: 20 };
  d.ligas_resultado![0].campos_escritos = 132; d.ligas_resultado![0].campos_acreditados = 12; d.ligas_resultado![0].campos_no_acreditados = 120;
  vi.mocked(clienteAPI.get).mockResolvedValue({ data: d }); render(<EstadoSincronizacionAgenda vista="tablero" />);
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('actualización está pausada'));
  expect(screen.getByRole('button', { name: 'Actualizar todas las ligas' })).toBeDisabled();
  expect(screen.getByText(/Corrección estadística/)).toHaveTextContent('120 quedaron en cuarentena en 20 partidos');
  expect(abrirLiga('Coupe de France')).toHaveTextContent('Campos escritos en el ciclo: 132. Campos que pasaron el control: 12. Campos rechazados: 120.');
});
it('un error al solicitar no afirma éxito y permite volver a consultar', async () => {
  vi.mocked(clienteAPI.post).mockRejectedValue(new Error('offline')); await abrirTablero();
  fireEvent.click(screen.getByRole('button', { name: 'Actualizar todas las ligas' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Servicio no disponible'); expect(screen.getByRole('button', { name: 'Consultar estado' })).toBeEnabled();
});
it('un informe legacy sin detalle no inventa cobertura', async () => {
  vi.mocked(clienteAPI.get).mockResolvedValue({ data: { estado: 'SIN_SINCRONIZAR', actualizacion_ligas: null, error_actualizacion: 'No se pudo consultar la última actualización de las ligas.' } });
  render(<EstadoSincronizacionAgenda vista="tablero" />);
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('No se pudo consultar'));
  expect(screen.getByLabelText('Última actualización completa de todas las ligas')).toHaveTextContent('Sin acreditar');
  expect(within(screen.getByLabelText('Resumen de cobertura')).getAllByText('N/D')).toHaveLength(3);
});
