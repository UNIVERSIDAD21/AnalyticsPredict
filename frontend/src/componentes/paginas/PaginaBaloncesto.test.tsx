import '@testing-library/jest-dom/vitest';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, useLocation, useNavigate } from 'react-router-dom';
import { RutasAplicacion } from '../../App';
import { consultarAgendaBaloncesto, type PartidoAgendaBaloncesto } from '../../servicios/agendaBaloncesto';
import { fechaColombia } from '../../utilidades/agendaFutbol';
import { ProveedorDeporte } from '../../contextos/DeporteContext';

// Motores sustituidos en esta prueba de navegación. El formulario real se prueba
// por separado: aquí interesa que nunca compartan selección/salida al cambiar liga.
vi.mock('../../servicios/agendaBaloncesto', () => ({ consultarAgendaBaloncesto: vi.fn(async () => ({ fecha:'2026-10-26',total:0,pagina:1,tamano:50,partidos:[],competiciones:[] })) }));
vi.mock('./PaginaPrincipal', () => ({ PaginaPrincipal: ({partidoAgenda}: {partidoAgenda?: {id:string}|null}) => <div>Motor NBA<output>{partidoAgenda?.id}</output><input aria-label="Selección NBA" /></div> }));
vi.mock('./PaginaEuroliga', () => ({ ModuloEuroliga: ({partidoAgenda}: {partidoAgenda?: {id:string}|null}) => <div>Motor Euroliga<output>{partidoAgenda?.id}</output><input aria-label="Selección Euroliga" /></div> }));
vi.mock('./PaginaWnba', () => ({ ModuloWnba: () => <div>Motor WNBA<input aria-label="Selección WNBA" /></div> }));
afterEach(cleanup);
beforeEach(() => { vi.mocked(consultarAgendaBaloncesto).mockResolvedValue({fecha:fechaColombia(),total:0,pagina:1,tamano:50,partidos:[],competiciones:[],consultado_en:new Date().toISOString(),datos_actualizados_en:null}); });

function Ubicacion() {
  const l = useLocation(); const navegar = useNavigate();
  return <><output data-testid="ruta">{l.pathname}{l.search}{l.hash}</output>
    <button onClick={() => navegar(-1)}>Atrás navegador</button><button onClick={() => navegar(1)}>Adelante navegador</button></>;
}
function preparar(ruta: string) {
  render(<ProveedorDeporte><MemoryRouter initialEntries={[ruta]}><RutasAplicacion /><Ubicacion /></MemoryRouter></ProveedorDeporte>);
}

describe('una sola sección Baloncesto', () => {
  it('la agenda selecciona la liga y el partido sin arrastrar el motor anterior', async () => {
    const base: PartidoAgendaBaloncesto = {id:'partido-nba',liga:'nba',competicion_nombre:'NBA',fecha_partido:fechaColombia(),inicio_utc:null,
      equipo_local_id:'l',equipo_visitante_id:'v',equipo_local_nombre:'Celtics',equipo_visitante_nombre:'Bulls',
      temporada_id:'t',temporada_nombre:'2026',tipo_partido:'REG',local_total:null,visitante_total:null,finalizado:false,analizable:true,reconstruccion:true};
    vi.mocked(consultarAgendaBaloncesto).mockResolvedValue({fecha:fechaColombia(),total:2,pagina:1,tamano:50,competiciones:['NBA','Euroliga'],consultado_en:new Date().toISOString(),datos_actualizados_en:null,
      partidos:[base,{...base,id:'partido-euro',liga:'euroliga',competicion_nombre:'Euroliga',equipo_local_nombre:'Madrid'}]});
    preparar('/baloncesto');
    await screen.findByRole('button',{name:'Analizar Celtics vs Bulls'}, {timeout:5000});
    expect(screen.queryByText('Motor NBA')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Analizar Celtics vs Bulls'}));
    await screen.findByText('Motor NBA');expect(screen.getByText('partido-nba')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:'Analizar Madrid vs Bulls'}));
    await screen.findByText('Motor Euroliga');expect(screen.getByText('partido-euro')).toBeInTheDocument();
    expect(screen.queryByText('Motor NBA')).toBeNull();
    expect(screen.getByTestId('ruta')).toHaveTextContent('liga=euroliga');
    fireEvent.click(screen.getByRole('button',{name:'Atrás navegador'}));
    await screen.findByText('partido-nba');
    fireEvent.click(screen.getByRole('button',{name:'Adelante navegador'}));
    await screen.findByText('partido-euro');
  });

  it('WNBA conserva URL y se desmonta al cambiar de liga sin arrastrar selección', async () => {
    preparar('/baloncesto?liga=wnba');
    const liga=await screen.findByRole('combobox',{name:'Liga'});
    expect(liga).toHaveValue('wnba');await screen.findByText('Motor WNBA');
    fireEvent.change(screen.getByLabelText('Selección WNBA'),{target:{value:'Liberty'}});
    fireEvent.change(liga,{target:{value:'nba'}});await screen.findByText('Motor NBA');
    expect(screen.queryByText('Motor WNBA')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Atrás navegador'}));await screen.findByText('Motor WNBA');
    expect(screen.getByLabelText('Selección WNBA')).toHaveValue('');
    expect(screen.getByTestId('ruta')).toHaveTextContent('liga=wnba');
  });
  it('retira la referencia al journal y lado al cambiar de competición', async () => {
    preparar('/baloncesto?liga=wnba&analisis=journal-wnba&lado=UNDER&prueba=1');
    await screen.findByText('Motor WNBA');
    fireEvent.change(screen.getByRole('combobox',{name:'Liga'}),{target:{value:'nba'}});
    await screen.findByText('Motor NBA');
    expect(screen.getByTestId('ruta')).toHaveTextContent('/baloncesto?liga=nba&prueba=1');
    expect(screen.getByTestId('ruta')).not.toHaveTextContent('analisis=');
    expect(screen.getByTestId('ruta')).not.toHaveTextContent('lado=');
  });
  it('cambia de motor en la misma pantalla y limpia las selecciones de la otra liga', async () => {
    preparar('/baloncesto?liga=nba');
    const liga = await screen.findByRole('combobox', { name: 'Liga' });
    await screen.findByText('Motor NBA');
    fireEvent.change(screen.getByLabelText('Selección NBA'), { target: { value: 'Lakers' } });
    fireEvent.change(liga, { target: { value: 'euroliga' } });
    await screen.findByText('Motor Euroliga');
    expect(screen.getByTestId('ruta')).toHaveTextContent('/baloncesto?liga=euroliga');
    expect(screen.queryByLabelText('Selección NBA')).toBeNull();
    expect(screen.getByRole('button', { name: 'Baloncesto' })).toHaveAttribute('aria-current', 'page');
    expect(screen.queryByRole('button', { name: 'Euroliga' })).toBeNull();
    expect(screen.getAllByRole('heading', { name: 'Partidos' })).toHaveLength(1);
    expect(screen.getAllByRole('banner')).toHaveLength(1);
    fireEvent.change(screen.getByLabelText('Selección Euroliga'), { target: { value: 'Madrid' } });
    fireEvent.change(liga, { target: { value: 'nba' } });
    await screen.findByText('Motor NBA');
    expect(screen.getByLabelText('Selección NBA')).toHaveValue('');
    expect(screen.queryByLabelText('Selección Euroliga')).toBeNull();
  });

  it.each([
    ['/app?tab=estadisticas&equipo=equipo-id#tabla', 'nba'],
    ['/euroliga', 'euroliga'],
  ])('conserva los enlaces antiguos %s sin una segunda pantalla', async (ruta, liga) => {
    preparar(ruta);
    expect(await screen.findByRole('combobox', { name: 'Liga' })).toHaveValue(liga);
    const destino = screen.getByTestId('ruta').textContent!;
    expect(destino).toContain('/baloncesto?');
    expect(destino).toContain(`liga=${liga}`);
    if (ruta.startsWith('/app')) {
      expect(destino).toContain('tab=estadisticas'); expect(destino).toContain('equipo=equipo-id'); expect(destino).toContain('#tabla');
    }
  });

  it('recarga directa, atrás y adelante respetan la liga de la URL', async () => {
    preparar('/baloncesto?liga=euroliga');
    const liga = await screen.findByRole('combobox', { name: 'Liga' });
    expect(liga).toHaveValue('euroliga');
    await screen.findByText('Motor Euroliga');
    expect(screen.queryByText('Motor NBA')).toBeNull();
    fireEvent.change(liga, { target: { value: 'nba' } });
    await screen.findByText('Motor NBA');
    fireEvent.click(screen.getByRole('button', { name: 'Atrás navegador' }));
    await screen.findByText('Motor Euroliga');
    expect(liga).toHaveValue('euroliga');
    fireEvent.click(screen.getByRole('button', { name: 'Adelante navegador' }));
    await screen.findByText('Motor NBA');
    expect(liga).toHaveValue('nba');
  });
});
