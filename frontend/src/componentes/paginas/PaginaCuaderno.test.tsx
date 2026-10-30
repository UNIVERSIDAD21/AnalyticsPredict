import { beforeEach, afterEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { PaginaCuaderno } from './PaginaCuaderno';
import { CLAVE_CUADERNO, editarEntrada, guardarConsulta, leerCuaderno } from '../../servicios/cuadernoLocal';
import * as cuaderno from '../../servicios/cuadernoLocal';
import { crearRespaldo } from '../../servicios/respaldoPersonal';
vi.mock('../organismos/Encabezado', () => ({ Encabezado: () => <header>AnalyticsPredict</header> }));
const abrir = (ruta = '/mis-analisis') => render(<MemoryRouter initialEntries={[ruta]}><PaginaCuaderno /></MemoryRouter>);
beforeEach(() => { localStorage.clear(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
it('abre una consulta por enlace y guarda notas sin tocar el resultado ni su fecha', () => {
  const e = guardarConsulta({ titulo: 'Bogotá — Peña', liga: 'futbol', tipo: 'resultado', snapshot: { media: 0, probabilidad: null } });
  abrir(`/mis-analisis?entrada=${e.id}`);
  fireEvent.change(screen.getByLabelText('Mis notas'), { target: { value: 'Comparar mañana' } });
  fireEvent.click(screen.getByRole('button', { name: 'Guardar notas' }));
  expect(leerCuaderno()[0]).toEqual({ ...e, notas: 'Comparar mañana' });
  expect(screen.getByText('Notas guardadas.')).toBeInTheDocument();
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
it('refleja actualizaciones del cuaderno sin recargar ni hacer consultas HTTP', async () => {
  const e = guardarConsulta({ titulo: 'Consulta', liga: 'nba', tipo: 'base', snapshot: {} });
  abrir(); act(() => editarEntrada(e.id, { notas: 'Actualizada', etiquetas: [], favorito: true }));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Quitar favorito: Consulta' })).toHaveAttribute('aria-pressed', 'true'));
});
it('un cuaderno dañado muestra N/D y permite descargar recuperación sin reemplazarlo', () => {
  localStorage.setItem(CLAVE_CUADERNO, '{dañado');
  const descarga = vi.spyOn(cuaderno, 'descargar').mockImplementation(() => {});
  abrir(); fireEvent.click(screen.getByRole('button', { name: 'Crear respaldo' }));
  fireEvent.click(screen.getByRole('button', { name: 'Guardar copia de recuperación de mis datos actuales' }));
  expect(descarga).toHaveBeenCalledOnce(); expect(localStorage.getItem(CLAVE_CUADERNO)).toBe('{dañado');
  expect(screen.getAllByText('N/D')).toHaveLength(4);
});
