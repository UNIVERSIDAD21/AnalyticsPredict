import '@testing-library/jest-dom/vitest';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, useLocation, useNavigate } from 'react-router-dom';
import { RutasAplicacion } from '../../App';
import { ProveedorDeporte } from '../../contextos/DeporteContext';

// Motores sustituidos en esta prueba de navegación. El formulario real se prueba
// por separado: aquí interesa que nunca compartan selección/salida al cambiar liga.
vi.mock('./PaginaPrincipal', () => ({ PaginaPrincipal: () => <div>Motor NBA<input aria-label="Selección NBA" /></div> }));
vi.mock('./PaginaEuroliga', () => ({ ModuloEuroliga: () => <div>Motor Euroliga<input aria-label="Selección Euroliga" /></div> }));
vi.mock('./PaginaWnba', () => ({ ModuloWnba: () => <div>Motor WNBA<input aria-label="Selección WNBA" /></div> }));
afterEach(cleanup);

function Ubicacion() {
  const l = useLocation(); const navegar = useNavigate();
  return <><output data-testid="ruta">{l.pathname}{l.search}{l.hash}</output>
    <button onClick={() => navegar(-1)}>Atrás navegador</button><button onClick={() => navegar(1)}>Adelante navegador</button></>;
}
function preparar(ruta: string) {
  render(<ProveedorDeporte><MemoryRouter initialEntries={[ruta]}><RutasAplicacion /><Ubicacion /></MemoryRouter></ProveedorDeporte>);
}

describe('una sola sección Baloncesto', () => {
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
    expect(screen.getAllByRole('heading', { name: 'Baloncesto' })).toHaveLength(1);
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
