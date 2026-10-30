import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { PaginaOperacion } from './PaginaOperacion';
import { clienteAPI } from '../../servicios/api';
import { leerEstadoLocal, type EstadoLocal } from '../../servicios/estadoLocal';
import { descargar } from '../../servicios/cuadernoLocal';

vi.mock('../organismos/Encabezado', () => ({ Encabezado: () => <nav>Estado</nav> }));
vi.mock('../../servicios/estadoLocal', () => ({ leerEstadoLocal: vi.fn() }));
vi.mock('../../servicios/cuadernoLocal', () => ({ descargar: vi.fn() }));
const diagnostico: EstadoLocal = {
  formato: 'diagnostico-local-v1', observado_en: '2026-10-30T20:00:00Z', modo: 'BASE_LOCAL',
  bd: { deshabilitada: true, conexion_comprobada: false, estado: 'DESHABILITADA_POR_MODO' },
  modelos: { nba: { disponible: false, motivo: 'Artefacto ausente' }, euroliga: { disponible: false },
    wnba: { disponible: true, modelo_version: 'wnba-sintetico', equipos_disponibles: 2, muestra_entrenamiento: 70, corte_modelo: '2026-01-01' } },
  limites: ['No acredita migración ni rendimiento predictivo.'],
};
beforeEach(() => { vi.resetAllMocks(); vi.mocked(leerEstadoLocal).mockResolvedValue(diagnostico); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it('muestra capacidades sin consultar BD y descarga solo el diagnóstico recibido', async () => {
  const get = vi.spyOn(clienteAPI, 'get').mockRejectedValue(new Error('No debe consultar BD'));
  render(<PaginaOperacion />);
  await screen.findByText(/BD está deshabilitada/);
  expect(get).not.toHaveBeenCalled();
  expect(screen.getByText(/2 equipos con soporte/)).toBeInTheDocument();
  expect(screen.queryByText(/0 partidos/)).not.toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Abrir Mis análisis' })).toHaveAttribute('href', '/mis-analisis');
  fireEvent.click(screen.getByRole('button', { name: 'Descargar diagnóstico local' }));
  expect(descargar).toHaveBeenCalledWith('diagnostico-local-2026-10-30.json', JSON.stringify(diagnostico, null, 2));
  fireEvent.click(screen.getByRole('button', { name: 'Actualizar estado' }));
  await waitFor(() => expect(leerEstadoLocal).toHaveBeenCalledTimes(2));
  expect(get).not.toHaveBeenCalled();
});

it('conserva el diagnóstico anterior al fallar la actualización sin probar otra conexión', async () => {
  const get = vi.spyOn(clienteAPI, 'get').mockRejectedValue(new Error('No debe consultar BD'));
  vi.mocked(leerEstadoLocal).mockResolvedValueOnce(diagnostico).mockRejectedValueOnce(new Error('Sin respuesta'));
  render(<PaginaOperacion />);
  await screen.findByText(/BD está deshabilitada/);
  fireEvent.click(screen.getByRole('button', { name: 'Actualizar estado' }));
  await screen.findByRole('alert');
  expect(screen.getByText(/Versión: wnba-sintetico/)).toBeInTheDocument();
  expect(screen.getByText(/Última respuesta recibida/)).toBeInTheDocument();
  expect(get).not.toHaveBeenCalled();
});
