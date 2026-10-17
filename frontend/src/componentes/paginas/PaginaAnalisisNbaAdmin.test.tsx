import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { PaginaAnalisisNbaAdmin } from './PaginaAnalisisNbaAdmin';
import { generarAnalisisNba } from '../../servicios/nbaMatchAnalysis';

vi.mock('../organismos/Encabezado', () => ({ Encabezado: () => <nav>AnalyticsPredict</nav> }));
vi.mock('../../servicios/nbaMatchAnalysis', () => ({ generarAnalisisNba: vi.fn() }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });

it('no presenta una fecha, cuotas ni fuente de mercado de ejemplo como datos reales', () => {
  render(<PaginaAnalisisNbaAdmin />);
  for (const nombre of ['Equipo local','Equipo visitante','Fecha','line','over_odds','under_odds','source','source_url opcional']) {
    expect((screen.getByLabelText(nombre) as HTMLInputElement).value).toBe('');
  }
  fireEvent.click(screen.getByRole('button', { name: 'Generar análisis' }));
  expect(generarAnalisisNba).not.toHaveBeenCalled();
  expect(screen.getByText(/No genera picks, no calcula stake/)).toBeTruthy();
});
