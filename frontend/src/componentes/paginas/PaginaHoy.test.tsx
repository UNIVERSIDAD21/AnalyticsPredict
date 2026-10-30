import { beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { PaginaHoy } from './PaginaHoy';
import { consultarAgendaBaloncesto } from '../../servicios/agendaBaloncesto';
import { listarAgenda } from '../../servicios/futbol/catalogo';
import { cambiarFavorito, favoritoEquipo } from '../../servicios/favoritosLocales';
vi.mock('../organismos/Encabezado', () => ({ Encabezado: () => <header>AnalyticsPredict</header> }));
vi.mock('../../servicios/agendaBaloncesto', () => ({ consultarAgendaBaloncesto: vi.fn() }));
vi.mock('../../servicios/futbol/catalogo', () => ({ listarAgenda: vi.fn() }));
beforeEach(() => { cleanup(); localStorage.clear(); vi.clearAllMocks(); });
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
it('filtra favoritos por identidad sin volver a consultar ni confundir la página con el total', async () => {
  vi.mocked(consultarAgendaBaloncesto).mockResolvedValue({ fecha: '2026-01-01', total: 54, pagina: 1, tamano: 50, competiciones: ['nba', 'wnba'], consultado_en: '2026-01-01', datos_actualizados_en: null,
    partidos: [
      { id: 'NBA-1', liga: 'nba', equipo_local_id: '42', equipo_local_nombre: 'Boston', equipo_visitante_id: '44', equipo_visitante_nombre: 'Atlanta' },
      { id: 'WNBA-1', liga: 'wnba', equipo_local_id: '42', equipo_local_nombre: 'Boston', equipo_visitante_id: '44', equipo_visitante_nombre: 'Atlanta' },
    ] } as Awaited<ReturnType<typeof consultarAgendaBaloncesto>>);
  vi.mocked(listarAgenda).mockResolvedValue({ fecha: '2026-01-01', total: 0, consultadoEn: '', datosActualizadosEn: null, partidos: [] });
  cambiarFavorito(favoritoEquipo('wnba', '42', 'Boston'));
  render(<MemoryRouter><PaginaHoy /></MemoryRouter>);
  await screen.findByText(/54 registrados/);
  fireEvent.click(screen.getByLabelText('Solo equipos, competiciones o ligas favoritos'));
  expect(screen.getByText('1 favoritos visibles de 2 partidos recibidos. El filtro no consulta otras páginas.')).toBeInTheDocument();
  expect(screen.getAllByRole('link', { name: /Boston — Atlanta/ })).toHaveLength(1);
  expect(screen.getByRole('link', { name: /Boston — Atlanta/ })).toHaveAttribute('href', expect.stringContaining('liga=wnba'));
  expect(consultarAgendaBaloncesto).toHaveBeenCalledTimes(1);
});
