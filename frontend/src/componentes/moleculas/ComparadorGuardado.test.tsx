import { afterEach, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { ComparadorGuardado } from './ComparadorGuardado';
afterEach(cleanup);
it('conserva la selección original al comparar masa WNBA y muestra enteros con push', () => {
  const datos = { formato: 'pmf-wnba-sobol-v1', mercado: 'COMPLETO', incluye_ot: true, simulaciones: 8,
    valores: [160,161,180], frecuencias: [2,4,2], probabilidad_tipo: 'SIN_CALIBRAR', sha256: 'sintetico' };
  render(<ComparadorGuardado datos={datos} mercado="COMPLETO" original={160.5} />);
  fireEvent.click(screen.getByText('Comparar líneas · misma corrida guardada'));
  fireEvent.change(screen.getByLabelText('Otra línea entera o .5'), { target: { value: '161' } });
  expect(screen.getByText('Over 25.0000% · Under 25.0000% · Push 50.0000%')).toBeInTheDocument();
  expect(screen.getByText(/Incluye OT.*8 puntos/)).toBeInTheDocument();
  expect(datos.frecuencias).toEqual([2,4,2]);
  fireEvent.change(screen.getByLabelText('Otra línea entera o .5'), { target: { value: '' } });
  expect(screen.getByText('N/D para esa línea en esta copia.')).toBeInTheDocument();
});
it('fútbol solo permite las líneas conservadas y no complementa ausencias', () => {
  render(<ComparadorGuardado mercado="GOLES_FT" original={2} datos={{ formato: 'lineas-originales-futbol-v1', mercado: 'GOLES_FT',
    lineas: [{ linea: 2, over: .4, under: null, push: null, fuente: 'RAW', calibrador: null }] }} />);
  fireEvent.click(screen.getByText('Comparar líneas · misma corrida guardada'));
  expect(screen.getByText('Over N/D · Under N/D · Push N/D')).toBeInTheDocument();
  expect(screen.getByText(/porcentajes legacy.*no separan el push/)).toBeInTheDocument();
  expect(screen.getAllByRole('option')).toHaveLength(2);
});
