import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { clienteAPI } from '../../servicios/api';
import { PaginaOperacion } from './PaginaOperacion';

vi.mock('../organismos/Encabezado', () => ({ Encabezado: () => <nav>Estado</nav> }));
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe('Estado operativo', () => {
  it('no desplaza fechas sin hora y conserva N/D del seguimiento ausente', async () => {
    vi.spyOn(clienteAPI, 'get').mockResolvedValue({ data: {
      observado_en: '2026-10-16T01:00:00Z',
      nba: { n: 30, ultimo_final: '2026-10-15' }, futbol: { n: 200, ultimo_final: null },
      modelo_nba: { estado: 'DISPONIBLE', version: 2123, equipos: 30 },
      capturas_futbol: { lotes: 10, observado_en: null },
      prospectiva: { congeladas: null, resueltas: null, estado: 'ALMACEN_NO_INSTALADO' }, notas: [],
    } });
    render(<PaginaOperacion />);
    expect(await screen.findByText(/último final: 2026-10-15/)).toBeTruthy();
    expect(screen.getByText(/N\/D predicciones congeladas/)).toBeTruthy();
    expect(screen.getByText('Seguimiento aún no instalado')).toBeTruthy();
  });
  it('no inventa ceros al fallar la carga y permite reintentar', async () => {
    const get = vi.spyOn(clienteAPI, 'get').mockRejectedValue(new Error('sin conexión'));
    render(<PaginaOperacion />);
    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.queryByText(/0 partidos/)).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar estado' }));
    await waitFor(() => expect(get).toHaveBeenCalledTimes(2));
  });
});
