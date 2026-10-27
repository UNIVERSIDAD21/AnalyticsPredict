import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { HistoricoAnalisisFutbol } from './HistoricoAnalisisFutbol';
import { listarTemporadas } from '../../servicios/futbol/catalogo';
import type { PartidoFutbolResumen } from '../../tipos/futbol';
vi.mock('../../servicios/futbol/catalogo', () => ({ listarTemporadas: vi.fn() }));
afterEach(cleanup);
it('las temporadas pertenecen al partido seleccionado, no a la agenda global', async () => {
  vi.mocked(listarTemporadas).mockResolvedValue([{ id: 't1', nombre: '2025', anio_inicio: 2025, finales: 100 }, { id: 't2', nombre: '2027', anio_inicio: 2027, finales: 0 }]);
  const partido = { id: 'p', competicion: 'bra', competicionNombre: 'Brasileirão', estado: 'FINALIZADO', fechaPartido: '2026-10-20T20:00:00Z' } as PartidoFutbolResumen;
  const onCambiar = vi.fn(); render(<HistoricoAnalisisFutbol partido={partido} seleccion={[]} onCambiar={onCambiar} />);
  fireEvent.click(screen.getByText('Histórico para calcular'));
  const checkbox = await screen.findByRole('checkbox'); fireEvent.click(checkbox);
  expect(listarTemporadas).toHaveBeenCalledWith('bra', expect.any(AbortSignal));
  expect(onCambiar).toHaveBeenCalledWith('bra', ['t1']); expect(screen.queryByText('2027')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Usar selección automática' })); expect(onCambiar).toHaveBeenLastCalledWith('bra', []);
});
