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
  it('la ficha fútbol oculta equipos redundantes sin perder los IDs ni la localía al enviar', () => {
    const analizar = vi.fn();
    render(<FormularioAnalisis equipos={equipos} deporte="FUTBOL" partidoActual={partido} ocultarSelectorPartido
      partidosDisponibles={[partido]} onAnalizar={analizar} />);
    expect(screen.queryByRole('combobox', { name: 'Equipo Local' })).toBeNull();
    expect(screen.queryByRole('combobox', { name: 'Equipo Visitante' })).toBeNull();
    fireEvent.change(screen.getByRole('combobox', { name: 'Mercado' }), { target: { value: 'COMPLETO' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Línea del análisis' }), { target: { value: '2.5' } });
    fireEvent.click(screen.getByRole('button', { name: 'Analizar Partido' }));
    expect(analizar).toHaveBeenCalledWith(expect.objectContaining({ partido_id: partido.id,
      equipo_local_id: 'club-2', equipo_visitante_id: 'club-3', equipo_local: 'Betis', equipo_visitante: 'Barcelona' }), 'OVER');
  });
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

  it('NBA PRE no consulta temporadas ni solicita ajuste y limpiar notifica la selección controlada', async () => {
    const seleccionar = vi.fn(), analizar = vi.fn();
    render(<FormularioAnalisis equipos={equipos} partidoActual={partido} partidosDisponibles={[partido]}
      onAnalizar={analizar} onSeleccionarPartido={seleccionar} />);
    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Equipo Local' })).toHaveValue('betis'));
    expect(obtenerTemporadasEquipos).not.toHaveBeenCalled();
    expect(screen.queryByText('Temporadas para el análisis')).toBeNull();
    fireEvent.change(screen.getByRole('combobox', { name: 'Mercado' }), { target: { value: 'COMPLETO' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Línea del análisis' }), { target: { value: '220.5' } });
    fireEvent.click(screen.getByRole('button', { name: 'Analizar Partido' }));
    expect(analizar).toHaveBeenCalledWith(expect.objectContaining({ temporadas: undefined, partido_id: partido.id }), 'OVER');
    fireEvent.click(screen.getByRole('button', { name: 'Limpiar' }));
    expect(seleccionar).toHaveBeenCalledWith(null);
  });
  it('NBA conserva la consulta de temporadas solo para reconstrucción histórica', async () => {
    render(<FormularioAnalisis equipos={equipos} partidoActual={partido} partidosDisponibles={[partido]} consultaHistorica onAnalizar={vi.fn()} />);
    await waitFor(() => expect(obtenerTemporadasEquipos).toHaveBeenCalledWith(['club-2', 'club-3'], expect.any(AbortSignal)));
  });
  it('NBA envía solo cuartos completos a la petición live y vuelve limpiamente a prepartido', async () => {
    const analizar=vi.fn(), invalidar=vi.fn();
    render(<FormularioAnalisis equipos={equipos} partidoActual={partido} partidosDisponibles={[partido]} onAnalizar={analizar} onCambiarParametros={invalidar} />);
    await waitFor(() => expect(screen.getByRole('combobox', { name:'Equipo Local' })).toHaveValue('betis'));
    fireEvent.change(screen.getByRole('combobox',{name:'Mercado'}),{target:{value:'COMPLETO'}});
    fireEvent.change(screen.getByRole('spinbutton',{name:'Línea del análisis'}),{target:{value:'220.5'}});
    fireEvent.change(screen.getByRole('combobox',{name:'Modo de análisis'}),{target:{value:'2'}});
    expect(screen.queryByText('Temporadas para el análisis')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Analizar Partido'}));
    expect(analizar).not.toHaveBeenCalled();
    for (const [label,value] of [['Q1 local','28'],['Q1 visitante','30'],['Q2 local','25'],['Q2 visitante','24']]) fireEvent.change(screen.getByRole('spinbutton',{name:label}),{target:{value}});
    fireEvent.click(screen.getByRole('button',{name:'Analizar Partido'}));
    expect(analizar).toHaveBeenLastCalledWith(expect.objectContaining({marcador_q1:'28-30',marcador_q2:'25-24',linea:220.5,partido_id:partido.id,temporadas:undefined,cuota_over:undefined}), 'OVER');
    expect(analizar.mock.calls[0][0]).not.toHaveProperty('marcador_q3');
    fireEvent.change(screen.getByRole('combobox',{name:'Modo de análisis'}),{target:{value:'0'}});
    expect(screen.queryByRole('spinbutton',{name:'Q1 local'})).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Analizar Partido'}));
    expect(analizar.mock.calls[1][0]).not.toHaveProperty('marcador_q1');
    expect(invalidar).toHaveBeenCalled();
  });

});
