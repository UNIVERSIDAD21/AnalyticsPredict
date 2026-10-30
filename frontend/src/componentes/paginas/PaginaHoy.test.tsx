import { beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { PaginaHoy } from './PaginaHoy';
import { consultarAgendaBaloncesto, type PartidoAgendaBaloncesto, type AgendaBaloncesto } from '../../servicios/agendaBaloncesto';
import { listarAgenda, type AgendaFutbol } from '../../servicios/futbol/catalogo';
import { cambiarFavorito, favoritoEquipo, favoritoLiga } from '../../servicios/favoritosLocales';
import { guardarConsulta } from '../../servicios/cuadernoLocal';
const partido = (id: string, cambios: Partial<PartidoAgendaBaloncesto> = {}): PartidoAgendaBaloncesto => ({
  id, liga: 'nba', competicion_nombre: 'NBA', fecha_partido: '2026-10-30', inicio_utc: null,
  equipo_local_id: id, equipo_visitante_id: 'visita', equipo_local_nombre: id, equipo_visitante_nombre: 'Atlanta',
  temporada_id: 't', temporada_nombre: '2026-2027', tipo_partido: 'REG', estado: 'PROGRAMADO',
  precision_fecha: 'DIA', local_total: null, visitante_total: null, finalizado: false, analizable: true, reconstruccion: true, ...cambios,
});
const agenda = (partidos: PartidoAgendaBaloncesto[] = [], total = partidos.length, pagina = 1): AgendaBaloncesto => ({
  fecha: '2026-10-30', total, pagina, tamano: 2, consultado_en: '2026-10-30T12:00:00Z', datos_actualizados_en: null, competiciones: ['nba', 'wnba'], partidos,
});
const futbolVacio: AgendaFutbol = { fecha: '2026-10-30', total: 0, consultadoEn: '', datosActualizadosEn: null, partidos: [] };
const abrir = () => render(<MemoryRouter><PaginaHoy /></MemoryRouter>);
vi.mock('../organismos/Encabezado', () => ({ Encabezado: () => <header>AnalyticsPredict</header> }));
vi.mock('../../servicios/agendaBaloncesto', () => ({ consultarAgendaBaloncesto: vi.fn() }));
vi.mock('../../servicios/futbol/catalogo', () => ({ listarAgenda: vi.fn() }));
beforeEach(() => { cleanup(); localStorage.clear(); vi.resetAllMocks(); vi.mocked(consultarAgendaBaloncesto).mockResolvedValue(agenda()); vi.mocked(listarAgenda).mockResolvedValue(futbolVacio); });
it('conserva el dominio disponible y no transforma un error en cero partidos', async () => {
  vi.mocked(consultarAgendaBaloncesto).mockRejectedValue(new Error('BD no disponible'));
  vi.mocked(listarAgenda).mockResolvedValue({ fecha: '2026-01-01', total: 0, consultadoEn: '2026-01-01T00:00:00Z', datosActualizadosEn: null, partidos: [] });
  render(<MemoryRouter><PaginaHoy /></MemoryRouter>);
  await screen.findByText('Partidos: N/D. BD no disponible');
  expect(screen.getByText(/0 registrados · Fuente actualizada: N\/D/)).toBeInTheDocument();
  expect(screen.queryByText(/0 partidos registrados/)).toBeNull();
  fireEvent.change(screen.getByLabelText('Liga'), { target: { value: 'wnba' } });
  await waitFor(() => expect(consultarAgendaBaloncesto).toHaveBeenLastCalledWith(expect.objectContaining({ liga: 'wnba' }), expect.any(AbortSignal)));
});
it('encuentra un favorito en la segunda página y conserva liga, filtro y página en su enlace', async () => {
  vi.mocked(consultarAgendaBaloncesto).mockImplementation(async p => p.pagina === 1 ? agenda([
    partido('NBA-1', { equipo_local_id: '42', equipo_local_nombre: 'Boston' }), partido('WNBA-1', { liga: 'wnba', equipo_local_nombre: 'Seattle' }),
  ], 3) : agenda([partido('WNBA-2', { liga: 'wnba', equipo_local_id: '42', equipo_local_nombre: 'Boston' })], 3, 2));
  vi.mocked(listarAgenda).mockResolvedValue({ fecha: '2026-01-01', total: 0, consultadoEn: '', datosActualizadosEn: null, partidos: [] });
  cambiarFavorito(favoritoEquipo('wnba', '42', 'Boston'));
  render(<MemoryRouter><PaginaHoy /></MemoryRouter>);
  await screen.findByText(/3 registrados/);
  fireEvent.click(screen.getByLabelText('Solo equipos, competiciones o ligas favoritos'));
  await screen.findByText(/1 favoritos encontrados · 3 de 3 registros consultados/);
  expect(screen.getAllByRole('link', { name: /Boston — Atlanta/ })).toHaveLength(1);
  expect(screen.getByRole('link', { name: /Boston — Atlanta/ })).toHaveAttribute('href', expect.stringContaining('liga=wnba'));
  expect(screen.getByRole('link', { name: /Boston — Atlanta/ })).toHaveAttribute('href', expect.stringContaining('paginaAgenda=2'));
  expect(consultarAgendaBaloncesto).toHaveBeenCalledTimes(2);
});
it('consulta únicamente el dominio seleccionado y reintenta un fallo sin releer el otro', async () => {
  abrir(); await waitFor(() => expect(screen.getAllByText(/0 de 0 registros consultados/)).toHaveLength(2));
  await waitFor(() => expect(listarAgenda).toHaveBeenCalledTimes(1));
  vi.mocked(consultarAgendaBaloncesto).mockClear(); vi.mocked(listarAgenda).mockClear();
  fireEvent.change(screen.getByLabelText('Liga'), { target: { value: 'wnba' } });
  await waitFor(() => expect(consultarAgendaBaloncesto).toHaveBeenCalledTimes(1));
  expect(listarAgenda).not.toHaveBeenCalled();
  vi.mocked(consultarAgendaBaloncesto).mockClear();
  fireEvent.change(screen.getByLabelText('Liga'), { target: { value: 'futbol' } });
  await waitFor(() => expect(listarAgenda).toHaveBeenCalledTimes(1)); expect(consultarAgendaBaloncesto).not.toHaveBeenCalled();
});
it('un fallo de página posterior conserva lo leído y permite reintentar esa misma página', async () => {
  vi.mocked(consultarAgendaBaloncesto).mockResolvedValueOnce(agenda([partido('Primero')], 2)).mockRejectedValueOnce(new Error('Sin conexión'))
    .mockResolvedValueOnce(agenda([partido('Segundo')], 2, 2));
  abrir(); await screen.findByRole('link', { name: /Primero — Atlanta/ });
  fireEvent.click(screen.getByRole('button', { name: 'Cargar más partidos de baloncesto' }));
  await screen.findByText(/Sin conexión/); expect(screen.getByRole('link', { name: /Primero — Atlanta/ })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Cargar más partidos de baloncesto' }));
  await screen.findByRole('link', { name: /Segundo — Atlanta/ });
  expect(vi.mocked(consultarAgendaBaloncesto).mock.calls.map(([p]) => p.pagina)).toEqual([1, 2, 2]);
  expect(listarAgenda).toHaveBeenCalledTimes(1);
});
it('descarta una página tardía cuando cambia la fecha', async () => {
  let resolver!: (d: AgendaBaloncesto) => void;
  vi.mocked(consultarAgendaBaloncesto).mockImplementation(async p => p.pagina === 2 ? new Promise(r => { resolver = r; }) :
    p.fecha === '2099-01-02' ? agenda([partido('Fecha nueva')]) : agenda([partido('Fecha vieja')], 2));
  abrir(); await screen.findByRole('link', { name: /Fecha vieja — Atlanta/ });
  fireEvent.click(screen.getByRole('button', { name: 'Cargar más partidos de baloncesto' }));
  await waitFor(() => expect(consultarAgendaBaloncesto).toHaveBeenCalledTimes(2));
  fireEvent.change(screen.getByLabelText('Fecha · Colombia'), { target: { value: '2099-01-02' } });
  await screen.findByRole('link', { name: /Fecha nueva — Atlanta/ });
  await act(async () => resolver(agenda([partido('Respuesta tardía')], 2, 2)));
  expect(screen.queryByRole('link', { name: /Respuesta tardía/ })).toBeNull(); expect(screen.queryByRole('link', { name: /Fecha vieja/ })).toBeNull();
});
it('detiene la búsqueda, conserva lo leído y no incorpora una respuesta cancelada', async () => {
  let resolver!: (d: AgendaBaloncesto) => void;
  vi.mocked(consultarAgendaBaloncesto).mockResolvedValueOnce(agenda([partido('Primero')], 2)).mockImplementationOnce(async () => new Promise(r => { resolver = r; }));
  abrir(); await screen.findByRole('link', { name: /Primero — Atlanta/ });
  fireEvent.click(screen.getByRole('button', { name: 'Cargar más partidos de baloncesto' }));
  fireEvent.click(await screen.findByRole('button', { name: 'Detener búsqueda de baloncesto' }));
  await act(async () => resolver(agenda([partido('Cancelado')], 2, 2)));
  expect(screen.queryByRole('link', { name: /Cancelado/ })).toBeNull();
  expect(screen.getByRole('link', { name: /Primero — Atlanta/ })).toBeInTheDocument();
});
it('acota la búsqueda de favoritos y permite continuar hasta recibir todas las páginas', async () => {
  cambiarFavorito(favoritoLiga('nba'));
  vi.mocked(consultarAgendaBaloncesto).mockImplementation(async p => agenda([partido(`Equipo ${p.pagina}`)], 13, p.pagina));
  abrir(); await screen.findByRole('link', { name: /Equipo 1 — Atlanta/ });
  fireEvent.click(screen.getByLabelText('Solo equipos, competiciones o ligas favoritos'));
  await screen.findByText(/11 favoritos encontrados · 11 de 13 registros consultados/);
  expect(consultarAgendaBaloncesto).toHaveBeenCalledTimes(11);
  fireEvent.click(screen.getByRole('button', { name: 'Buscar más favoritos de baloncesto' }));
  await screen.findByText(/13 favoritos encontrados · 13 de 13 registros consultados/);
  expect(consultarAgendaBaloncesto).toHaveBeenCalledTimes(13);
});
it('no descarga otras páginas para buscar favoritos cuando no existen preferencias', async () => {
  vi.mocked(consultarAgendaBaloncesto).mockResolvedValue(agenda([partido('Primero')], 3));
  abrir(); await screen.findByRole('link', { name: /Primero — Atlanta/ });
  fireEvent.click(screen.getByLabelText('Solo equipos, competiciones o ligas favoritos'));
  expect(screen.getByText(/Todavía no tienes equipos/)).toBeInTheDocument(); expect(consultarAgendaBaloncesto).toHaveBeenCalledTimes(1);
});
it('detecta páginas repetidas y cambios de fuente sin sumarlos como cobertura completa', async () => {
  vi.mocked(consultarAgendaBaloncesto).mockResolvedValueOnce(agenda([partido('Primero')], 3))
    .mockResolvedValueOnce(agenda([partido('Primero')], 3, 2)).mockResolvedValueOnce(agenda([partido('Nuevo')], 4, 2));
  abrir(); await screen.findByRole('link', { name: /Primero — Atlanta/ });
  fireEvent.click(screen.getByRole('button', { name: 'Cargar más partidos de baloncesto' })); await screen.findByText(/repitió encuentros/);
  fireEvent.click(screen.getByRole('button', { name: 'Cargar más partidos de baloncesto' })); await screen.findByText(/cambió entre páginas/);
  expect(screen.queryByRole('link', { name: /Nuevo — Atlanta/ })).toBeNull(); expect(screen.getByText(/1 de 3 registros consultados/)).toBeInTheDocument();
});
it('enlaza directamente a la consulta reciente y refleja nuevas copias sin recargar', async () => {
  const e = guardarConsulta({ titulo: 'Consulta anterior', liga: 'nba', tipo: 'base', snapshot: {} });
  abrir(); expect(screen.getByRole('link', { name: 'Consulta anterior' })).toHaveAttribute('href', `/mis-analisis?entrada=${e.id}`);
  act(() => { guardarConsulta({ titulo: 'Consulta nueva', liga: 'wnba', tipo: 'resultado', snapshot: {} }); });
  await screen.findByRole('link', { name: 'Consulta nueva' });
});
it('encuentra competiciones favoritas de fútbol en páginas posteriores', async () => {
  const p = (id: string, competicion: string): AgendaFutbol['partidos'][number] => ({ id, competicion, competicionNombre: competicion,
    temporadaId: 't', fechaPartido: '2026-10-30T18:00:00Z', precisionFecha: 'DIA', fechaFuente: '2026-10-30',
    equipoLocal: id, equipoLocalNombre: id, equipoVisitante: 'visitante', equipoVisitanteNombre: 'Visitante',
    estado: 'PROGRAMADO', pais: 'Colombia', estadoAgenda: 'PROXIMO', analizable: true });
  cambiarFavorito({ liga: 'futbol', tipo: 'competicion', id: 'Colombia', nombre: 'Colombia' });
  vi.mocked(listarAgenda).mockImplementation(async f => ({ ...futbolVacio, total: 2,
    partidos: f.pagina === 1 ? [p('No favorito', 'Otra liga')] : [p('Favorito encontrado', 'Colombia')] }));
  abrir(); await screen.findByRole('link', { name: /No favorito — Visitante/ });
  fireEvent.change(screen.getByLabelText('Liga'), { target: { value: 'futbol' } });
  fireEvent.click(screen.getByLabelText('Solo equipos, competiciones o ligas favoritos'));
  const enlace = await screen.findByRole('link', { name: /Favorito encontrado — Visitante/ });
  expect(enlace).toHaveAttribute('href', expect.stringContaining('partidoId=Favorito+encontrado'));
  expect(screen.getByText(/1 favoritos encontrados · 2 de 2 registros consultados/)).toBeInTheDocument();
  expect(listarAgenda).toHaveBeenCalledTimes(2);
});
it('reintenta solo el dominio que falló, sin releer la agenda disponible', async () => {
  vi.mocked(consultarAgendaBaloncesto).mockRejectedValueOnce(new Error('Fallo temporal')).mockResolvedValueOnce(agenda([partido('Recuperado')]));
  abrir(); await screen.findByText(/Partidos: N\/D. Fallo temporal/);
  fireEvent.click(screen.getByRole('button', { name: 'Reintentar baloncesto' }));
  await screen.findByRole('link', { name: /Recuperado — Atlanta/ });
  expect(listarAgenda).toHaveBeenCalledTimes(1);
});
it('una página vacía inesperada no convierte una lectura incompleta en cero partidos', async () => {
  vi.mocked(consultarAgendaBaloncesto).mockResolvedValueOnce(agenda([partido('Conservado')], 2)).mockResolvedValueOnce(agenda([], 2, 2));
  abrir(); await screen.findByRole('link', { name: /Conservado — Atlanta/ });
  fireEvent.click(screen.getByRole('button', { name: 'Cargar más partidos de baloncesto' }));
  await screen.findByText(/página vacía antes de completar/);
  expect(screen.getByText(/1 de 2 registros consultados/)).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Conservado — Atlanta/ })).toBeInTheDocument();
});
