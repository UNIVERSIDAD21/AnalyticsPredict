import '@testing-library/jest-dom/vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CatalogoFutbol } from './CatalogoFutbol';
import { listarAgenda, listarCompeticiones, resolverPartidoCatalogo, type AgendaFutbol, type PartidoAgendaFutbol } from '../../servicios/futbol/catalogo';
import { fechaColombia, sumarDias } from '../../utilidades/agendaFutbol';
vi.mock('../../servicios/futbol/catalogo', () => ({ listarAgenda: vi.fn(), listarCompeticiones: vi.fn(), resolverPartidoCatalogo: vi.fn() }));
const partido = (cambios: Partial<PartidoAgendaFutbol> = {}): PartidoAgendaFutbol => ({
  id: 'p1', competicion: 'mls', competicionNombre: 'MLS', pais: 'Estados Unidos', temporadaId: 'mls-2026',
  fechaPartido: '2099-10-30T20:00:00Z', equipoLocal: 'l', equipoLocalNombre: 'Atlanta', equipoVisitante: 'v', equipoVisitanteNombre: 'Chicago', estado: 'PROGRAMADO', estadoAgenda: 'PROXIMO', analizable: true, ...cambios,
});
const agenda = (partidos = [partido()], total = partidos.length): AgendaFutbol => ({ fecha: fechaColombia(), total, consultadoEn: new Date().toISOString(), datosActualizadosEn: null, partidos });
const props = () => ({ revision: 0, onInicio: vi.fn(), onCargando: vi.fn(), onError: vi.fn(), onDatos: vi.fn(), onSeleccionar: vi.fn(), seleccionadoId: '', guardadosIds: new Set<string>() });
afterEach(() => { cleanup(); vi.useRealTimers(); vi.restoreAllMocks(); window.history.replaceState({}, '', '/'); });
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(listarCompeticiones).mockResolvedValue([{ id: 'mls', nombre: 'MLS', codigo: 'USA_MLS', pais: 'Estados Unidos', tipo: 'liga', prioridad: 1, activa: true }]);
  vi.mocked(listarAgenda).mockResolvedValue(agenda());
  vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => { cb(0); return 1; });
});
describe('agenda global de fútbol', () => {
  it('abre Hoy con todas las ligas, y selecciona un partido sin elegir competición', async () => {
    vi.mocked(listarAgenda).mockResolvedValue(agenda([partido(), partido({ id: 'p2', competicion: 'bra', competicionNombre: 'Brasileirão', pais: 'Brasil', equipoLocalNombre: 'Flamengo' })]));
    const p = props(); render(<CatalogoFutbol {...p} />);
    await screen.findByText('Brasileirão · Brasil');
    expect(listarAgenda).toHaveBeenLastCalledWith(expect.objectContaining({ fecha: fechaColombia(), competicionId: '', pais: '' }), expect.any(AbortSignal));
    expect(screen.queryByRole('combobox', { name: 'Filtrar por competición' })).not.toBeVisible();
    fireEvent.click(screen.getByRole('button', { name: 'Analizar Atlanta vs Chicago' }));
    expect(p.onSeleccionar).toHaveBeenCalledWith(expect.objectContaining({ id: 'p1', competicion: 'mls' }));
  });
  it('Mañana cambia la fecha real de la consulta y descarta una respuesta tardía de Hoy', async () => {
    let resolver!: (value: AgendaFutbol) => void;
    vi.mocked(listarAgenda).mockImplementation(async f => f.fecha === fechaColombia() ? new Promise(resolve => { resolver = resolve; }) : agenda([], 0));
    const p = props(); render(<CatalogoFutbol {...p} />);
    await waitFor(() => expect(listarAgenda).toHaveBeenCalled());
    fireEvent.click(screen.getByRole('button', { name: 'Mañana' }));
    await screen.findByText(/No hay partidos registrados para esta fecha/);
    await act(async () => resolver(agenda([partido({ equipoLocalNombre: 'Respuesta vieja' })], 999)));
    expect(screen.queryByText('Respuesta vieja')).toBeNull();
    expect(listarAgenda).toHaveBeenLastCalledWith(expect.objectContaining({ fecha: sumarDias(fechaColombia(), 1) }), expect.any(AbortSignal));
  });
  it('elegir fecha permite abrir históricos sin imponer una liga', async () => {
    vi.mocked(listarAgenda).mockResolvedValue(agenda([partido({ estado: 'FINALIZADO', estadoAgenda: 'FINALIZADO', fechaPartido: '2020-01-01T20:00:00Z', golesLocal: 0, golesVisitante: 1 })]));
    const p = props(); render(<CatalogoFutbol {...p} />);
    await screen.findByRole('button', { name: 'Ver histórico Atlanta vs Chicago' });
    fireEvent.change(screen.getByLabelText('Fecha de los partidos'), { target: { value: '2020-01-01' } });
    await waitFor(() => expect(listarAgenda).toHaveBeenLastCalledWith(expect.objectContaining({ fecha: '2020-01-01', competicionId: '' }), expect.any(AbortSignal)));
    fireEvent.click(screen.getByRole('button', { name: 'Ver histórico Atlanta vs Chicago' }));
    expect(p.onSeleccionar).toHaveBeenCalledWith(expect.objectContaining({ estado: 'FINALIZADO', golesLocal: 0 }));
  });
  it('un horario vencido no se puede seleccionar aunque el servidor lo marque analizable', async () => {
    vi.mocked(listarAgenda).mockResolvedValue(agenda([partido({ fechaPartido: '2000-01-01T12:00:00Z' })]));
    const p = props(); render(<CatalogoFutbol {...p} />);
    expect(await screen.findByText('Estado por verificar', { selector: 'span' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Analizar Atlanta vs Chicago' })).toBeDisabled();
    expect(p.onSeleccionar).not.toHaveBeenCalled();
  });
  it('aplica búsqueda, filtro opcional y paginación en el servidor', async () => {
    vi.mocked(listarAgenda).mockResolvedValue(agenda([partido()], 80)); render(<CatalogoFutbol {...props()} />);
    await screen.findByText('80 partidos registrados');
    fireEvent.click(screen.getByText('Filtrar'));
    fireEvent.change(screen.getByLabelText('Filtrar por competición'), { target: { value: 'mls' } });
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'Atlanta' } });
    await waitFor(() => expect(listarAgenda).toHaveBeenLastCalledWith(expect.objectContaining({ competicionId: 'mls', buscar: 'Atlanta' }), expect.any(AbortSignal)));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Página siguiente' })).toBeEnabled());
    fireEvent.click(screen.getByRole('button', { name: 'Página siguiente' }));
    await waitFor(() => expect(listarAgenda).toHaveBeenLastCalledWith(expect.objectContaining({ pagina: 2, buscar: 'Atlanta' }), expect.any(AbortSignal)));
  });
  it('recupera un fallo de agenda sin ocultarlo como una lista vacía', async () => {
    vi.mocked(listarAgenda).mockRejectedValueOnce(new Error('Sin conexión')); render(<CatalogoFutbol {...props()} />);
    await screen.findByRole('alert'); fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    await screen.findByText('Atlanta'); expect(screen.queryByRole('alert')).toBeNull();
  });
  it('el enlace de un partido resuelve su propia fecha sin imponer el primer torneo', async () => {
    window.history.replaceState({}, '', '/?partidoId=00000000-0000-0000-0000-000000000001');
    vi.mocked(resolverPartidoCatalogo).mockResolvedValue({ competicionId: 'copa', temporadaId: 'copa-2020', estado: 'FINALIZADO', fechaPartido: '2020-01-02T02:00:00Z' });
    render(<CatalogoFutbol {...props()} />);
    await waitFor(() => expect(listarAgenda).toHaveBeenLastCalledWith(expect.objectContaining({ fecha: '2020-01-01', competicionId: '' }), expect.any(AbortSignal)));
  });
  it('no envía favoritos vacíos como una consulta global sin filtro', async () => {
    render(<CatalogoFutbol {...props()} />); await screen.findByText('Atlanta');
    fireEvent.click(screen.getByText('Filtrar')); fireEvent.click(screen.getByRole('checkbox', { name: /Solo mis partidos guardados/ }));
    await screen.findByText(/No hay partidos registrados para esta fecha/);
    expect(listarAgenda).toHaveBeenCalledTimes(1);
  });
  it('cierra una tarjeta al cruzar el kickoff sin recargar la página', async () => {
    vi.useFakeTimers(); vi.setSystemTime(new Date('2026-10-26T20:00:00Z'));
    vi.mocked(listarAgenda).mockResolvedValue(agenda([partido({ fechaPartido: '2026-10-26T20:00:01Z' })]));
    render(<CatalogoFutbol {...props()} />);
    await act(async () => {});
    expect(screen.getByRole('button', { name: 'Analizar Atlanta vs Chicago' })).toBeEnabled();
    await act(async () => { vi.advanceTimersByTime(15000); });
    expect(screen.getByRole('button', { name: 'Analizar Atlanta vs Chicago' })).toBeDisabled();
    expect(screen.getByText('Estado por verificar', { selector: 'span' })).toBeInTheDocument();
  });
});
