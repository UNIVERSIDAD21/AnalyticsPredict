import { beforeEach, afterEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { PaginaCuaderno } from './PaginaCuaderno';
import { CLAVE_CUADERNO, guardarConsulta, leerCuaderno } from '../../servicios/cuadernoLocal';
import { instalarAlmacenPersonalSimulado } from '../../test/almacenPersonalSimulado';
import { olvidarCachePersonal } from '../../servicios/personalCache';
import * as cuaderno from '../../servicios/cuadernoLocal';
import { crearRespaldo } from '../../servicios/respaldoPersonal';
vi.mock('../organismos/Encabezado', () => ({ Encabezado: () => <header>AnalyticsPredict</header> }));
const abrir = (ruta = '/mis-analisis') => render(<MemoryRouter initialEntries={[ruta]}><PaginaCuaderno /></MemoryRouter>);
let almacen: ReturnType<typeof instalarAlmacenPersonalSimulado>;
beforeEach(() => { localStorage.clear(); almacen = instalarAlmacenPersonalSimulado(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); olvidarCachePersonal(); });
it('abre una consulta por enlace y guarda notas sin tocar el resultado ni su fecha', async () => {
  const e = guardarConsulta({ titulo: 'Bogotá — Peña', liga: 'futbol', tipo: 'resultado', snapshot: { media: 0, probabilidad: null } });
  abrir(`/mis-analisis?entrada=${e.id}`);
  fireEvent.change(screen.getByLabelText('Mis notas'), { target: { value: 'Comparar mañana' } });
  fireEvent.click(screen.getByRole('button', { name: 'Guardar notas' }));
  await screen.findByText('Notas guardadas y verificadas en este PC.');
  expect(leerCuaderno()[0]).toEqual({ ...e, notas: 'Comparar mañana' });
});
it('filtra sin tildes y limpia filtros sin borrar entradas', () => {
  guardarConsulta({ titulo: 'Bogotá — Peña', liga: 'futbol', tipo: 'resultado', snapshot: {} });
  guardarConsulta({ titulo: 'Boston — Atlanta', liga: 'nba', tipo: 'base', snapshot: {} });
  abrir(); fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'bogota pena' } });
  expect(screen.getByRole('button', { name: 'Bogotá — Peña' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Boston — Atlanta' })).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Limpiar filtros' }));
  expect(screen.getByRole('button', { name: 'Boston — Atlanta' })).toBeInTheDocument(); expect(leerCuaderno()).toHaveLength(2);
});
it('restaura desde archivo con vista previa y descarga una copia anterior antes de escribir', async () => {
  guardarConsulta({ titulo: 'Consulta importada', liga: 'wnba', tipo: 'resultado', snapshot: { probabilidad: null } });
  const texto = JSON.stringify(crearRespaldo()); localStorage.clear();
  const descarga = vi.spyOn(cuaderno, 'descargar').mockImplementation(() => { expect(leerCuaderno()).toHaveLength(0); });
  abrir();
  fireEvent.change(screen.getByLabelText('Archivo de respaldo personal'), { target: { files: [{ size: texto.length, text: async () => texto }] } });
  await screen.findByRole('button', { name: 'Incorporar respaldo' }); expect(leerCuaderno()).toHaveLength(0);
  fireEvent.click(screen.getByRole('button', { name: 'Incorporar respaldo' }));
  expect(descarga).toHaveBeenCalledOnce();
  await screen.findByRole('button', { name: 'Consulta importada' }); expect(leerCuaderno()).toHaveLength(1);
});
it('refleja una revisión recibida del almacén sin repetir consultas deportivas', async () => {
  const e = guardarConsulta({ titulo: 'Consulta', liga: 'nba', tipo: 'base', snapshot: {} });
  abrir(); await screen.findByText(/Aún no hay consultas en el almacén/);
  act(() => almacen.recibir(state => { state.datos.cuaderno = [{ ...e, notas: 'Actualizada', favorito: true }]; }));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Quitar favorito: Consulta' })).toHaveAttribute('aria-pressed', 'true'));
});
it('un cuaderno dañado muestra N/D y permite descargar recuperación sin reemplazarlo', async () => {
  localStorage.setItem(CLAVE_CUADERNO, '{dañado');
  const descarga = vi.spyOn(cuaderno, 'descargar').mockImplementation(() => {});
  abrir(); fireEvent.click(screen.getByRole('button', { name: 'Crear respaldo' }));
  fireEvent.click(await screen.findByRole('button', { name: 'Guardar copia de recuperación de mis datos actuales' }));
  expect(descarga).toHaveBeenCalledOnce(); expect(localStorage.getItem(CLAVE_CUADERNO)).toBe('{dañado');
  expect(screen.getAllByText('N/D')).toHaveLength(4);
});
