import '@testing-library/jest-dom/vitest';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { FormularioAnalisis } from './FormularioAnalisis';
import { obtenerTemporadasEquipos } from '../../servicios';
import type { Equipo, PartidoResumen } from '../../tipos';

vi.mock('../../servicios', async (original) => ({
  ...await original<typeof import('../../servicios')>(),
  obtenerTemporadasEquipos: vi.fn().mockResolvedValue([]),
}));
afterEach(() => { cleanup(); vi.clearAllMocks(); });

const equipos: Equipo[] = ['Everton', 'Chelsea', 'Betis', 'Barcelona'].map((nombre, i) => ({
  id: `club-${i}`, nombre, nombre_corto: nombre, abreviatura: nombre.slice(0, 3),
}));
const partido: PartidoResumen = {
  id: 'partido-segundo', fecha_partido: '2026-10-20', tipo_partido: 'REG',
  equipo_local_id: 'club-2', equipo_local_nombre: 'Betis',
  equipo_visitante_id: 'club-3', equipo_visitante_nombre: 'Barcelona',
  temporada_id: 'temporada-futbol', temporada_nombre: 'Liga',
  local_total: null, visitante_total: null, finalizado: false,
};

describe('formulario por dominio', () => {
  it('acepta un partido distinto del primero sin pedir temporadas NBA y conserva sus IDs', async () => {
    const analizar = vi.fn();
    render(<FormularioAnalisis equipos={equipos} deporte="FUTBOL" partidoActual={partido}
      partidosDisponibles={[partido]} onAnalizar={analizar} />);
    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Equipo Local' })).toHaveValue('betis'));
    expect(screen.getByRole('combobox', { name: 'Equipo Visitante' })).toHaveValue('barcelona');
    expect(obtenerTemporadasEquipos).not.toHaveBeenCalled();
    expect(screen.queryByText('Temporadas para el análisis')).toBeNull();
    fireEvent.change(screen.getByRole('combobox', { name: 'Mercado' }), { target: { value: 'COMPLETO' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Línea del análisis' }), { target: { value: '2.5' } });
    fireEvent.click(screen.getByRole('button', { name: 'Analizar Partido' }));
    expect(analizar).toHaveBeenCalledWith(expect.objectContaining({
      partido_id: 'partido-segundo', equipo_local_id: 'club-2', equipo_visitante_id: 'club-3', linea: 2.5,
    }), 'OVER');
  });

  it('NBA conserva la consulta de temporadas y limpiar notifica la selección controlada', async () => {
    const seleccionar = vi.fn();
    render(<FormularioAnalisis equipos={equipos} partidoActual={partido} partidosDisponibles={[partido]}
      onAnalizar={vi.fn()} onSeleccionarPartido={seleccionar} />);
    await waitFor(() => expect(obtenerTemporadasEquipos).toHaveBeenCalledWith(['club-2', 'club-3']));
    fireEvent.click(screen.getByRole('button', { name: 'Limpiar' }));
    expect(seleccionar).toHaveBeenCalledWith(null);
  });
});
