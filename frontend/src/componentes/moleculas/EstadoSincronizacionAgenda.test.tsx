import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { EstadoSincronizacionAgenda } from './EstadoSincronizacionAgenda';
import { clienteAPI } from '../../servicios/api';
vi.mock('../../servicios/api', () => ({ clienteAPI: { get: vi.fn(), post: vi.fn() }, extraerMensajeError: () => 'Servicio no disponible' }));
afterEach(cleanup);
beforeEach(() => { vi.resetAllMocks(); vi.mocked(clienteAPI.get).mockResolvedValue({ data: { estado: 'PARCIAL' } }); });
it('separa campos, partidos, agenda y torneos archivados sin ocultar sus incidencias', async () => {
  const base = { deporte: 'futbol', estado:'PARCIAL', desde: '2026-11-05', hasta: '2026-11-12',
    finales_fuente: 2, insertados: 0, resultados_actualizados: 0, estadisticas_actualizadas: 0,
    campos_completados: 0, incidencias: [{ motivo: 'ESTADISTICAS_AUSENTES' }] };
  vi.mocked(clienteAPI.get).mockResolvedValue({ data: { estado: 'PARCIAL',
    cobertura_operativa: { competiciones_diarias: 22, competiciones_diarias_con_incidencias: 1,
      competiciones_archivadas: 2, consultas_agenda_pendientes: 0, consultas_agenda_error: 0,
      eventos_agenda_pendientes: 12, campos_estadisticas_ausentes_ventana: 6,
      partidos_estadisticas_pendientes_ventana: 1 },
    ligas_resultado: [
      { ...base, codigo:'COL_COPA', nombre:'Copa BetPlay', afecta_cobertura_diaria:true,
        estadisticas_ventana:{campos_estadisticas_ausentes:6,partidos_estadisticas_pendientes:1},
        pendientes_cola:{resultados:0,eventos_agenda:0,campos_estadisticas:6,partidos_estadisticas:1,
          campos_estadisticas_elegibles:0,proximo_reintento_en:'2026-11-12T18:16:00Z'} },
      { ...base, codigo:'ARG_MARADONA', nombre:'Copa Maradona', afecta_cobertura_diaria:false },
    ] } });
  render(<EstadoSincronizacionAgenda />);
  expect(await screen.findByLabelText('Pendientes de cobertura')).toHaveTextContent('6 campos ausentes en 1 partidos guardados');
  expect(screen.getByText(/Resultados de la última actualización/)).toHaveTextContent('1 competiciones con pendientes');
  expect(screen.getByText(/Torneos archivados, fuera del contador diario/)).toHaveTextContent('Copa Maradona');
  expect(screen.getByText(/Próximo reintento habilitado/)).toHaveTextContent('no se ejecuta automáticamente');
  expect(clienteAPI.post).not.toHaveBeenCalled();
});
it('leer estado no sincroniza fuentes y la solicitud no afirma éxito', async () => {
  vi.mocked(clienteAPI.post).mockResolvedValue({ data: { estado: 'SOLICITADA', detalle: 'Verificación solicitada, todavía no terminada' } });
  render(<EstadoSincronizacionAgenda />);
  await screen.findByText(/Fuentes y sincronización · PARCIAL/);
  expect(clienteAPI.post).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText(/Fuentes y sincronización/));
  fireEvent.click(screen.getByRole('button', { name: 'Actualizar todas las ligas' }));
  await screen.findByText('Verificación solicitada, todavía no terminada');
  expect(clienteAPI.post).toHaveBeenCalledTimes(1);
  expect(clienteAPI.post).toHaveBeenCalledWith('/api/agendas/sincronizar');
});
it('un servicio caído conserva la posibilidad de leer la agenda', async () => {
  vi.mocked(clienteAPI.post).mockRejectedValue(new Error('no')); render(<EstadoSincronizacionAgenda />);
  fireEvent.click(screen.getByText(/Fuentes y sincronización/));
  fireEvent.click(screen.getByRole('button', { name: 'Actualizar todas las ligas' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Servicio no disponible');
});

it('mantiene visible la actualización general parcial sin acreditar una completa', async () => {
  vi.mocked(clienteAPI.get).mockResolvedValue({ data: { estado: 'PARCIAL', actualizacion_ligas: {
    ultimo_ciclo_agendas: { terminado_en: '2026-11-01T19:00:00Z', estado: 'PARCIAL' },
    ultimo_ciclo_integral: null, ultima_completa_en: null,
    ligas: [{ codigo: 'nba', nombre: 'NBA', deporte: 'baloncesto', cambio_en: '2026-11-01T18:00:00Z',
      resultados_hasta: '2026-10-31', estadisticas_hasta: '2026-10-31',
      verificacion_agenda_en: '2026-11-01T19:00:00Z', estado_agenda: 'VERIFICADA',
      estadisticas: { estado: 'SIN_ACREDITAR' } }],
  } } });
  render(<EstadoSincronizacionAgenda />);
  const recordatorio = await screen.findByText(/Última actualización completa de todas las ligas/);
  expect(recordatorio.closest('p')).toHaveTextContent('sin acreditar');
  expect(recordatorio.closest('details')).toBeNull();
  expect(screen.getByText(/Última revisión general/)).toHaveTextContent('PARCIAL');
  fireEvent.click(screen.getByText(/Fuentes y sincronización/));
  expect(screen.getByRole('list', { name: 'Frescura por liga' })).toHaveTextContent('Resultados hasta: 2026-10-31');
  expect(screen.getByRole('list', { name: 'Frescura por liga' })).toHaveTextContent('Revisión de estadísticas: SIN ACREDITAR');
  expect(clienteAPI.post).not.toHaveBeenCalled();
});

it('un fallo de lectura muestra N/D sin afirmar frescura', async () => {
  vi.mocked(clienteAPI.get).mockResolvedValue({ data: { estado: 'SIN_SINCRONIZAR', actualizacion_ligas: null,
    error_actualizacion: 'No se pudo consultar la última actualización de las ligas.' } });
  render(<EstadoSincronizacionAgenda />);
  expect(await screen.findByRole('status')).toHaveTextContent('No se pudo consultar');
  expect(screen.getByText(/Última actualización completa/).closest('p')).toHaveTextContent('sin acreditar');
});

it('una actualización en curso bloquea otra solicitud y muestra progreso', async () => {
  vi.mocked(clienteAPI.get).mockResolvedValue({ data: { estado: 'EN_CURSO',
    detalle: 'Revisando NBA', progreso: { ligas_revisadas: 8, ligas_total: 23 } } });
  render(<EstadoSincronizacionAgenda />);
  expect(await screen.findByRole('status')).toHaveTextContent('8/23 competiciones');
  expect(screen.getByRole('button', { name: 'Actualizar todas las ligas' })).toBeDisabled();
  expect(clienteAPI.post).not.toHaveBeenCalled();
});

it('muestra campos pendientes y el corte del candidato sin prometer reentrenamiento', async () => {
  vi.mocked(clienteAPI.get).mockResolvedValue({ data: { estado: 'PARCIAL',
    ligas_resultado: [{ codigo: 'nba', nombre: 'NBA', deporte: 'baloncesto', estado: 'PARCIAL',
      desde: '2026-11-01', hasta: '2026-11-06', finales_fuente: 10, insertados: 0,
      resultados_actualizados: 2, estadisticas_actualizadas: 0, campos_completados: 0,
      incidencias: [{ motivo: 'ESTADISTICAS_LOCALES_PENDIENTES' }] }],
    modelos: [{ nombre: 'NBA candidato', version: 2191, corte: '2026-11-05',
      necesita_actualizacion: true, finales_posteriores: 2 }] } });
  render(<EstadoSincronizacionAgenda />);
  fireEvent.click(await screen.findByText(/Resultados de la última actualización/));
  expect(screen.getByRole('list', { name: 'Resultado por competición' })).toHaveTextContent('Resultados completados: 2');
  expect(screen.getByText(/Hay 2 finales guardados posteriores/)).toHaveTextContent('preparar un candidato es una operación separada');
  expect(screen.getByText(/Todavía faltan estadísticas publicadas/)).toBeInTheDocument();
  expect(clienteAPI.post).not.toHaveBeenCalled();
});

it('distingue lo escrito de lo acreditado y bloquea la ingesta durante la revisión', async () => {
  vi.mocked(clienteAPI.get).mockResolvedValue({ data: { estado: 'PAUSADA_CALIDAD',
    correccion_calidad: { campos_escritos: 762, campos_acreditados: 642,
      campos_no_acreditados: 120, partidos_en_cuarentena: 20 },
    ligas_resultado: [{ codigo: 'ESP_COPA', nombre: 'Copa del Rey', deporte: 'futbol', estado: 'PARCIAL',
      desde: '2026-10-23', hasta: '2026-11-06', finales_fuente: 40, insertados: 0,
      resultados_actualizados: 0, estadisticas_actualizadas: 2, campos_completados: 12,
      campos_escritos: 132, campos_acreditados: 12, campos_no_acreditados: 120,
      incidencias: [{ motivo: 'Córners y tiros pendientes de una fuente fiable.' }] }],
  } });
  render(<EstadoSincronizacionAgenda />);
  expect(await screen.findByRole('status')).toHaveTextContent('actualización está pausada');
  expect(screen.getByRole('button', { name: 'Actualizar todas las ligas' })).toBeDisabled();
  expect(screen.getByText(/Corrección estadística/)).toHaveTextContent('120 quedaron en cuarentena en 20 partidos');
  fireEvent.click(screen.getByText(/Resultados de la última actualización/));
  expect(screen.getByRole('list', { name: 'Resultado por competición' })).toHaveTextContent(
    'Campos escritos en el ciclo: 132. Campos que pasaron el control: 12. Campos rechazados: 120.',
  );
});
