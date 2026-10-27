import '@testing-library/jest-dom/vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CatalogoFutbol } from './CatalogoFutbol';
import { listarCatalogo, listarCompeticiones, listarTemporadas, resolverPartidoCatalogo } from '../../servicios/futbol/catalogo';

vi.mock('../../servicios/futbol/catalogo', () => ({ listarCatalogo: vi.fn(), listarCompeticiones: vi.fn(), listarTemporadas: vi.fn(), resolverPartidoCatalogo: vi.fn() }));
afterEach(() => { cleanup(); window.history.replaceState({}, '', '/'); });
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(listarCompeticiones).mockResolvedValue([
    { id: 'mls', nombre: 'MLS', codigo: 'USA_MLS', pais: 'Estados Unidos', tipo: 'liga', prioridad: 1, activa: true },
    { id: 'copa', nombre: 'Copa LPF', codigo: 'ARG_COPA_LPF', pais: 'Argentina', tipo: 'copa_nacional', prioridad: 2, activa: true },
  ]);
  vi.mocked(listarTemporadas).mockImplementation(async id => [{ id: `${id}-2026`, nombre: '2026', anio_inicio: 2026, finales: 60 }]);
  vi.mocked(listarCatalogo).mockResolvedValue({ total: 80, partidos: [] });
});

const props = () => ({ revision: 0, onInicio: vi.fn(), onCargando: vi.fn(), onError: vi.fn(), onDatos: vi.fn(), onTemporadas: vi.fn() });

describe('catálogo fútbol con datos por dominio', () => {
  it('consulta competición, temporada, histórico y página; no es solo un filtro visual', async () => {
    const p = props(); render(<CatalogoFutbol {...p} />);
    await screen.findByRole('option', { name: '2026 · 60 finales' });
    fireEvent.change(screen.getByRole('combobox', { name: 'Competición' }), { target: { value: 'copa' } });
    await waitFor(() => expect(listarTemporadas).toHaveBeenLastCalledWith('copa', expect.any(AbortSignal)));
    await screen.findByRole('option', { name: '2026 · 60 finales' });
    fireEvent.change(screen.getByRole('combobox', { name: 'Tipo de partidos' }), { target: { value: 'historicos' } });
    fireEvent.change(screen.getByRole('combobox', { name: 'Temporada de fútbol' }), { target: { value: 'copa-2026' } });
    await waitFor(() => expect(listarCatalogo).toHaveBeenLastCalledWith({ competicionId: 'copa', temporadaId: 'copa-2026', modo: 'historicos', pagina: 1 }, expect.any(AbortSignal)));
    expect(p.onTemporadas).toHaveBeenLastCalledWith(['copa-2026']);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Siguiente' })).toBeEnabled());
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    await waitFor(() => expect(listarCatalogo).toHaveBeenLastCalledWith(expect.objectContaining({ competicionId: 'copa', pagina: 2 }), expect.any(AbortSignal)));
    expect(screen.getByText(/No es un pronóstico emitido entonces/)).toBeInTheDocument();
  });

  it('descarta una respuesta tardía de otra liga y conserva el aviso de calendario vacío', async () => {
    let resolver: (value: { total: number; partidos: [] }) => void = () => {};
    vi.mocked(listarCatalogo).mockImplementation(async ambito => ambito.competicionId === 'mls'
      ? new Promise(resolve => { resolver = resolve; }) : { total: 0, partidos: [] });
    const p = props(); render(<CatalogoFutbol {...p} />);
    await waitFor(() => expect(listarCatalogo).toHaveBeenCalled());
    fireEvent.change(screen.getByRole('combobox', { name: 'Competición' }), { target: { value: 'copa' } });
    await screen.findByText(/calendario vacío no certifica/);
    await act(async () => resolver({ total: 999, partidos: [] }));
    expect(screen.queryByText(/999 partidos/)).not.toBeInTheDocument();
    expect(p.onInicio).toHaveBeenCalled();
  });

  it('permite reintentar un error del catálogo inicial', async () => {
    vi.mocked(listarCompeticiones).mockRejectedValueOnce(new Error('Sin conexión'));
    const p = props(); render(<CatalogoFutbol {...p} />);
    await waitFor(() => expect(p.onError).toHaveBeenCalledWith('Sin conexión'));
    expect(p.onCargando).toHaveBeenCalledWith(false);
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar carga' }));
    await screen.findByRole('option', { name: 'MLS · Estados Unidos' });
    expect(listarCompeticiones).toHaveBeenCalledTimes(2);
  });

  it('un partido guardado abre su propia copa y temporada, no las de la primera liga', async () => {
    const pid = '00000000-0000-0000-0000-000000000001';
    window.history.replaceState({}, '', `/?partidoId=${pid}`);
    vi.mocked(resolverPartidoCatalogo).mockResolvedValue({ competicionId: 'copa', temporadaId: 'copa-2026', estado: 'FINALIZADO' });
    render(<CatalogoFutbol {...props()} />);
    await waitFor(() => expect(listarCatalogo).toHaveBeenLastCalledWith({ competicionId: 'copa', temporadaId: 'copa-2026', modo: 'historicos', pagina: 1 }, expect.any(AbortSignal)));
    expect(screen.getByRole('combobox', { name: 'Competición' })).toHaveValue('copa');
    fireEvent.change(screen.getByRole('combobox', { name: 'Competición' }), { target: { value: 'mls' } });
    expect(window.location.search).not.toContain('partidoId');
    expect(window.location.search).toContain('competicionId=mls');
  });
});
