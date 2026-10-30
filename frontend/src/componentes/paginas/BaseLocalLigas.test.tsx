import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { PaginaBaseLocal } from './PaginaBaseLocal';
import { PaginaCuaderno } from './PaginaCuaderno';
import { catalogoLocal, consultarLocal, type ConsultaLocal } from '../../servicios/consultaLocal';

vi.mock('../organismos/Encabezado', () => ({ Encabezado: () => <header>AnalyticsPredict</header> }));
vi.mock('../../servicios/consultaLocal', async importOriginal => ({
  ...await importOriginal<typeof import('../../servicios/consultaLocal')>(),
  catalogoLocal: vi.fn(), consultarLocal: vi.fn(),
}));
const metadata = { modelo_version: 'sintetico', corte_modelo: '2026-01-01', modelo_generado_en: '2026-01-02', dataset_hash: 'sintetico', muestra_entrenamiento: 70, incluye_ot: false as const };
const catalogo = { equipos: [{ clave: 'a', nombre: 'Equipo A', disponible: true }, { clave: 'b', nombre: 'Equipo B', disponible: true }, { clave: 'c', nombre: 'Sin muestra', disponible: false }], metadata };
afterEach(cleanup);
beforeEach(() => {
  localStorage.clear(); vi.resetAllMocks();
  vi.mocked(catalogoLocal).mockResolvedValue(catalogo);
  vi.mocked(consultarLocal).mockImplementation(async (p, _signal, liga = 'nba') => ({
    formato: 'consulta-local-v2', analisis_id: 'sintetico', liga, equipo_local: 'Equipo A', equipo_visitante: 'Equipo B',
    equipo_local_id: 'a', equipo_visitante_id: 'b', periodo: p.periodo, linea: p.linea, modo: 'BASE_LOCAL', generado_en: '2026-01-02T00:00:00Z', metadata,
    distribucion: { media: 160, desviacion: 10, familia: 'normal_discretizada', origen: 'artefacto_publicado', probabilidad_tipo: 'RAW' },
    probabilidad_over: .48, probabilidad_under: .48, probabilidad_push: .04, motivo_nd: null, advertencias: ['Datos sintéticos de prueba.'],
  }));
});

it.each(['euroliga', 'wnba'] as const)('consulta %s y reabre el snapshot con su liga y push sin otro POST', async liga => {
  const vista = render(<MemoryRouter><PaginaBaseLocal /></MemoryRouter>);
  await screen.findByRole('button', { name: 'Consultar artefacto' });
  fireEvent.change(screen.getByLabelText('Liga'), { target: { value: liga } });
  await waitFor(() => expect(catalogoLocal).toHaveBeenLastCalledWith(expect.any(AbortSignal), liga));
  await screen.findByRole('button', { name: 'Consultar artefacto' });
  expect((screen.getAllByRole('option', { name: /Sin muestra/ })[0] as HTMLOptionElement).disabled).toBe(true);
  fireEvent.change(screen.getByLabelText('Local'), { target: { value: 'a' } });
  fireEvent.change(screen.getByLabelText('Visitante'), { target: { value: 'b' } });
  fireEvent.change(screen.getByLabelText('Línea de puntos'), { target: { value: '160' } });
  fireEvent.click(screen.getByRole('button', { name: 'Consultar artefacto' }));
  await screen.findByText('4.00%');
  expect(screen.getByText(/40 min sin OT/)).toHaveTextContent(liga === 'wnba' ? 'WNBA' : 'Euroliga');
  expect(consultarLocal).toHaveBeenLastCalledWith({ equipo_local: 'a', equipo_visitante: 'b', periodo: 'TOTAL', linea: 160 }, expect.any(AbortSignal), liga);
  fireEvent.change(screen.getByLabelText('Línea entera o terminada en .5'), { target: { value: '165' } });
  expect(consultarLocal).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole('button', { name: 'Guardar consulta' }));
  await screen.findByText(/Copia guardada en Mis análisis/);
  vista.unmount(); render(<MemoryRouter><PaginaCuaderno /></MemoryRouter>);
  fireEvent.click(screen.getByRole('button', { name: 'Abrir' }));
  fireEvent.click(screen.getByRole('button', { name: 'Ver resultado original' }));
  await screen.findByText('4.00%');
  expect(screen.getByText(/40 min sin OT/)).toHaveTextContent(liga === 'wnba' ? 'WNBA' : 'Euroliga');
  expect(consultarLocal).toHaveBeenCalledTimes(1);
});

it('cambiar liga cancela la consulta anterior y descarta su respuesta tardía', async () => {
  let resolver!: (r: ConsultaLocal) => void;
  vi.mocked(consultarLocal).mockImplementationOnce(() => new Promise(resolve => { resolver = resolve; }));
  render(<MemoryRouter><PaginaBaseLocal /></MemoryRouter>);
  await screen.findByRole('button', { name: 'Consultar artefacto' });
  fireEvent.change(screen.getByLabelText('Local'), { target: { value: 'a' } });
  fireEvent.change(screen.getByLabelText('Visitante'), { target: { value: 'b' } });
  fireEvent.click(screen.getByRole('button', { name: 'Consultar artefacto' }));
  const signal = vi.mocked(consultarLocal).mock.calls[0][1]!;
  fireEvent.change(screen.getByLabelText('Liga'), { target: { value: 'wnba' } });
  expect(signal.aborted).toBe(true);
  resolver({ analisis_id: 'viejo', equipo_local: 'Respuesta tardía' } as ConsultaLocal);
  await screen.findByRole('button', { name: 'Consultar artefacto' });
  expect(screen.queryByText('Respuesta tardía')).not.toBeInTheDocument();
  expect(screen.getByLabelText('Local')).toHaveValue('');
});

it('artefacto ausente permite reintentar la misma liga sin usar otro catálogo', async () => {
  vi.mocked(catalogoLocal).mockRejectedValueOnce(new Error('Artefacto no disponible'));
  render(<MemoryRouter><PaginaBaseLocal /></MemoryRouter>);
  await screen.findByRole('alert');
  fireEvent.click(screen.getByRole('button', { name: 'Reintentar catálogo local' }));
  await screen.findByRole('button', { name: 'Consultar artefacto' });
  expect(catalogoLocal).toHaveBeenCalledTimes(2);
  expect(vi.mocked(catalogoLocal).mock.calls.every(c => c[1] === 'nba')).toBe(true);
  expect(consultarLocal).not.toHaveBeenCalled();
});
