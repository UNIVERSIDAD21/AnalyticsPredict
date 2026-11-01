import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { EstadoSincronizacionAgenda } from './EstadoSincronizacionAgenda';
import { clienteAPI } from '../../servicios/api';
vi.mock('../../servicios/api', () => ({ clienteAPI: { get: vi.fn(), post: vi.fn() }, extraerMensajeError: () => 'Servicio no disponible' }));
afterEach(cleanup);
beforeEach(() => { vi.resetAllMocks(); vi.mocked(clienteAPI.get).mockResolvedValue({ data: { estado: 'PARCIAL' } }); });
it('leer estado no sincroniza fuentes y la solicitud no afirma éxito', async () => {
  vi.mocked(clienteAPI.post).mockResolvedValue({ data: { estado: 'SOLICITADA', detalle: 'Verificación solicitada, todavía no terminada' } });
  render(<EstadoSincronizacionAgenda />);
  await screen.findByText(/Fuentes y sincronización · PARCIAL/);
  expect(clienteAPI.post).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText(/Fuentes y sincronización/));
  fireEvent.click(screen.getByRole('button', { name: 'Sincronizar fuentes' }));
  await screen.findByText('Verificación solicitada, todavía no terminada');
  expect(clienteAPI.post).toHaveBeenCalledTimes(1);
  expect(clienteAPI.post).toHaveBeenCalledWith('/api/agendas/sincronizar');
});
it('un servicio caído conserva la posibilidad de leer la agenda', async () => {
  vi.mocked(clienteAPI.post).mockRejectedValue(new Error('no')); render(<EstadoSincronizacionAgenda />);
  fireEvent.click(screen.getByText(/Fuentes y sincronización/));
  fireEvent.click(screen.getByRole('button', { name: 'Sincronizar fuentes' }));
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
