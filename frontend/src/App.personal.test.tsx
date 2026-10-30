import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { RutasAplicacion } from './App';
import { NavegacionPersonal } from './componentes/moleculas/NavegacionPersonal';

const montajes = vi.hoisted(() => ({ analisis: vi.fn(), seguimiento: vi.fn() }));
vi.mock('./componentes/paginas/PaginaCuaderno', () => ({ PaginaCuaderno: () => { montajes.analisis(); return <h1>Mis análisis</h1>; } }));
vi.mock('./componentes/paginas/PaginaBitacora', () => ({ PaginaBitacora: () => { montajes.seguimiento(); return <h1>Seguimiento</h1>; } }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
function Ubicacion() { const l = useLocation(); return <output data-testid="ubicacion">{l.pathname}{l.search}{l.hash}</output>; }

it.each(['/cuaderno', '/mi-espacio'])('conserva la entrada y fragmento del enlace anterior %s sin montar Seguimiento', async ruta => {
  render(<MemoryRouter initialEntries={[`${ruta}?entrada=original%2F42#notas`]}><RutasAplicacion /><Ubicacion /></MemoryRouter>);
  await screen.findByRole('heading', { name: 'Mis análisis' });
  expect(screen.getByTestId('ubicacion')).toHaveTextContent('/mis-analisis?entrada=original%2F42#notas');
  expect(montajes.seguimiento).not.toHaveBeenCalled();
});
it.each(['/bitacora', '/futbol/bitacora'])('mantiene el marcador anterior %s y monta solamente Seguimiento', async ruta => {
  render(<MemoryRouter initialEntries={[`${ruta}?desde=2026-10-01#registros`]}><RutasAplicacion /><Ubicacion /></MemoryRouter>);
  await screen.findByRole('heading', { name: 'Seguimiento' });
  expect(screen.getByTestId('ubicacion')).toHaveTextContent('/seguimiento?desde=2026-10-01#registros');
  expect(montajes.analisis).not.toHaveBeenCalled();
});
it.each([['/mis-analisis', 'Mis análisis'], ['/seguimiento', 'Seguimiento']])('identifica la sección activa en %s', (ruta, nombre) => {
  render(<MemoryRouter initialEntries={[ruta]}><NavegacionPersonal /></MemoryRouter>);
  expect(screen.getByRole('link', { name: nombre })).toHaveAttribute('aria-current', 'page');
  expect(screen.getAllByRole('link')).toHaveLength(2);
});
