import '@testing-library/jest-dom/vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AgendaBaloncesto } from './AgendaBaloncesto';
import { consultarAgendaBaloncesto, type PartidoAgendaBaloncesto, type AgendaBaloncesto as Datos } from '../../servicios/agendaBaloncesto';
import { fechaColombia, sumarDias } from '../../utilidades/agendaFutbol';
vi.mock('../../servicios/agendaBaloncesto', () => ({ consultarAgendaBaloncesto: vi.fn() }));
const partido = (cambios: Partial<PartidoAgendaBaloncesto> = {}): PartidoAgendaBaloncesto => ({
  id:'nba1', liga:'nba', competicion_nombre:'NBA', fecha_partido:fechaColombia(), inicio_utc:null,
  equipo_local_id:'local',equipo_visitante_id:'visita',equipo_local_nombre:'Celtics',equipo_visitante_nombre:'Bulls',
  temporada_id:'t',temporada_nombre:'2026-2027',tipo_partido:'REG',estado:'PROGRAMADO',
  precision_fecha:'DIA',local_total:null,visitante_total:null,finalizado:false,analizable:true,reconstruccion:true,...cambios,
});
const agenda = (partidos=[partido()]): Datos => ({fecha:fechaColombia(),total:partidos.length,pagina:1,tamano:50,consultado_en:new Date().toISOString(),datos_actualizados_en:null,competiciones:[...new Set(partidos.map(p=>p.competicion_nombre))],partidos});
function preparar(ruta='/baloncesto?liga=wnba') {
  const seleccionar=vi.fn(), cambiar=vi.fn();
  render(<MemoryRouter initialEntries={[ruta]}><AgendaBaloncesto seleccionado={null} onSeleccionar={seleccionar} onCambiar={cambiar}/></MemoryRouter>);
  return {seleccionar,cambiar};
}
afterEach(cleanup);
beforeEach(()=>{vi.resetAllMocks();vi.mocked(consultarAgendaBaloncesto).mockResolvedValue(agenda());});
describe('agenda global de baloncesto',()=>{
  it('abre desde Hoy la página y el filtro explícitos del encuentro',async()=>{
    vi.mocked(consultarAgendaBaloncesto).mockResolvedValue({...agenda([partido({id:'segundo',liga:'wnba'})]),pagina:2,total:60});
    const p=preparar('/baloncesto?liga=wnba&ligaAgenda=wnba&paginaAgenda=2&partidoId=segundo');
    await waitFor(()=>expect(p.seleccionar).toHaveBeenCalledWith(expect.objectContaining({id:'segundo',liga:'wnba'})));
    expect(consultarAgendaBaloncesto).toHaveBeenCalledWith(expect.objectContaining({liga:'wnba',pagina:2}),expect.any(AbortSignal));
    expect(screen.getByLabelText('Filtrar por liga')).toHaveValue('wnba');
  });
  it('rechaza una página de enlace inválida sin alterar la liga del motor',async()=>{
    preparar('/baloncesto?liga=wnba&ligaAgenda=desconocida&paginaAgenda=-7');
    await waitFor(()=>expect(consultarAgendaBaloncesto).toHaveBeenCalledWith(expect.objectContaining({liga:'',pagina:1}),expect.any(AbortSignal)));
  });
  it('ignora la liga del motor como filtro y mezcla las competiciones',async()=>{
    vi.mocked(consultarAgendaBaloncesto).mockResolvedValue(agenda([partido(),partido({id:'e1',liga:'euroliga',competicion_nombre:'Euroliga',equipo_local_nombre:'Real Madrid'})]));
    const p=preparar();await screen.findByText('Real Madrid');
    expect(consultarAgendaBaloncesto).toHaveBeenLastCalledWith(expect.objectContaining({liga:'',fecha:fechaColombia()}),expect.any(AbortSignal));
    fireEvent.click(screen.getByRole('button',{name:'Analizar Real Madrid vs Bulls'}));
    expect(p.seleccionar).toHaveBeenCalledWith(expect.objectContaining({id:'e1',liga:'euroliga'}));
    expect(screen.getAllByText('Hora por confirmar')).toHaveLength(2);
  });
  it('permite abrir un final y conserva el resultado real',async()=>{
    vi.mocked(consultarAgendaBaloncesto).mockResolvedValue(agenda([partido({finalizado:true,estado:'FINALIZADO',local_total:100,visitante_total:99})]));
    const p=preparar();await screen.findByText('Celtics · 100');
    fireEvent.click(screen.getByRole('button',{name:'Analizar Celtics vs Bulls'}));
    expect(p.seleccionar).toHaveBeenCalledWith(expect.objectContaining({finalizado:true}));
  });
  it('Mañana descarta respuestas antiguas y consulta el día correcto',async()=>{
    let resolver!: (x:Datos)=>void;
    vi.mocked(consultarAgendaBaloncesto).mockImplementation(async p=>p.fecha===fechaColombia()?new Promise(r=>{resolver=r;}):agenda([]));
    preparar();await waitFor(()=>expect(consultarAgendaBaloncesto).toHaveBeenCalled());
    fireEvent.click(screen.getByRole('button',{name:'Mañana'}));
    await screen.findByText(/No hay partidos registrados/);
    await act(async()=>resolver(agenda([partido({equipo_local_nombre:'Respuesta vieja'})])));
    expect(screen.queryByText('Respuesta vieja')).toBeNull();
    expect(consultarAgendaBaloncesto).toHaveBeenLastCalledWith(expect.objectContaining({fecha:sumarDias(fechaColombia(),1)}),expect.any(AbortSignal));
  });
  it('aplica filtros visibles y los limpia incluyendo la búsqueda',async()=>{
    preparar();await screen.findByText('Celtics');
    fireEvent.change(screen.getByLabelText('Filtrar por liga'),{target:{value:'wnba'}});
    fireEvent.change(screen.getByRole('searchbox'),{target:{value:'Liberty'}});
    await waitFor(()=>expect(consultarAgendaBaloncesto).toHaveBeenLastCalledWith(expect.objectContaining({liga:'wnba',buscar:'Liberty'}),expect.any(AbortSignal)));
    fireEvent.click(screen.getByRole('button',{name:/Quitar filtros/}));
    await waitFor(()=>expect(consultarAgendaBaloncesto).toHaveBeenLastCalledWith(expect.objectContaining({liga:'',buscar:'',estado:'todos'}),expect.any(AbortSignal)));
  });
  it('muestra errores y recupera con reintento',async()=>{
    vi.mocked(consultarAgendaBaloncesto).mockRejectedValueOnce(new Error('Sin conexión'));
    preparar();await screen.findByRole('alert');fireEvent.click(screen.getByRole('button',{name:'Reintentar carga'}));
    await screen.findByText('Celtics');expect(screen.queryByRole('alert')).toBeNull();
  });
});
