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
