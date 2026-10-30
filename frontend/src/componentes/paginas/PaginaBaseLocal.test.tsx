import { beforeEach, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { PaginaBaseLocal } from './PaginaBaseLocal';
import { PaginaCuaderno } from './PaginaCuaderno';
import { consultarLocal } from '../../servicios/consultaLocal';
vi.mock('../organismos/Encabezado', () => ({ Encabezado: () => <header>AnalyticsPredict</header> }));
vi.mock('../../servicios/consultaLocal', async importOriginal => ({
  ...await importOriginal<typeof import('../../servicios/consultaLocal')>(),
  catalogoLocal: vi.fn().mockResolvedValue({ equipos: ['Local', 'Visita'], metadata: { modelo_version: 17, corte_modelo: '2026-01-01' } }),
  consultarLocal: vi.fn().mockResolvedValue({ formato: 'consulta-local-v1', analisis_id: 'sintetico', liga: 'nba', equipo_local: 'Local', equipo_visitante: 'Visita',
    periodo: 'TOTAL', linea: 220.5, modo: 'BASE_LOCAL', generado_en: '2026-01-02T00:00:00Z',
    metadata: { modelo_version: 17, corte_modelo: '2026-01-01', modelo_generado_en: '2026-01-02', dataset_hash: 'sintetico', muestra_entrenamiento: null },
    distribucion: { media: 220, desviacion: 10, familia: 'normal_continua' }, probabilidad_over: .4800611942, probabilidad_under: .5199388058, motivo_nd: null, advertencias: ['Datos sintéticos de prueba.'] }),
}));
beforeEach(() => { localStorage.clear(); vi.clearAllMocks(); });
it('consulta una vez, compara sin POST y reabre exactamente la copia guardada', async () => {
  const vista = render(<MemoryRouter><PaginaBaseLocal /></MemoryRouter>);
  await screen.findByRole('button', { name: 'Consultar artefacto' });
  fireEvent.change(screen.getByLabelText('Local'), { target: { value: 'Local' } });
  fireEvent.change(screen.getByLabelText('Visitante'), { target: { value: 'Visita' } });
  fireEvent.click(screen.getByRole('button', { name: 'Consultar artefacto' }));
  await screen.findByText('48.01%'); expect(consultarLocal).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByText('Comparar otra línea · misma distribución'));
  fireEvent.change(screen.getByLabelText('Línea terminada en .5'), { target: { value: '230.5' } });
  expect(consultarLocal).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole('button', { name: 'Guardar consulta' }));
  await screen.findByText(/Copia guardada en Mis análisis/);
  vista.unmount();
  render(<MemoryRouter><PaginaCuaderno /></MemoryRouter>);
  fireEvent.click(screen.getByRole('button', { name: 'Abrir' }));
  fireEvent.click(screen.getByRole('button', { name: 'Ver resultado original' }));
  await waitFor(() => expect(screen.getByText('48.01%')).toBeInTheDocument());
  expect(screen.getByText(/Corte: 2026-01-01/)).toBeInTheDocument();
  expect(consultarLocal).toHaveBeenCalledTimes(1);
});
