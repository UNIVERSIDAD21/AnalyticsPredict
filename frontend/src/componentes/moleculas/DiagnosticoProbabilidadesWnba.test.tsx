import { afterEach, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { DiagnosticoProbabilidadesWnba } from './DiagnosticoProbabilidadesWnba';
afterEach(cleanup);
it('conserva N/D sin métricas guardadas y no lo sustituye por otra evaluación', () => {
  render(<DiagnosticoProbabilidadesWnba datos={null} />);
  expect(screen.getByText(/Bins conservados: N\/D/)).toBeInTheDocument();
  expect(screen.queryByRole('table', { hidden: true })).toBeNull();
});
it('presenta cohorte y definición Brier originales, bins vacíos N/D y cambia solo el mercado visible', () => {
  const medida = { n: 2, linea: 160.5, linea_entera: 160, brier_multiclase: .4, brier_referencia: .5, log_loss: .6, brier_con_push: .42, push_observados: 1, cobertura_intervalo80: .75,
    calibracion_bins: [{ desde: 0, hasta: .1, n: 0, probabilidad_media: null, frecuencia_observada: null }, { desde: .5, hasta: .6, n: 2, probabilidad_media: .55, frecuencia_observada: .5 }] };
  const datos = { candidato_version: 'sintetico', evaluacion: { partidos: 3, analizados: 2, abstenciones: 1, mercados: { COMPLETO: medida, Q1: { ...medida, linea: 40.5 } } } };
  const antes = JSON.stringify(datos); render(<DiagnosticoProbabilidadesWnba datos={datos} />);
  fireEvent.click(screen.getByText('Fiabilidad declarada WNBA · candidato original'));
  expect(screen.getByText(/Analizados \/ elegibles: 2 \/ 3 · Abstenciones: 1/)).toBeInTheDocument();
  expect(screen.getByText(/Brier suma de clases 0.4000 · Referencia 0.5000/)).toBeInTheDocument();
  const vacia = within(screen.getByRole('table')).getAllByRole('row')[1];
  expect(within(vacia).getAllByText('N/D')).toHaveLength(2);
  expect(screen.getByText(/cobertura observada 75.00%/)).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Mercado diagnóstico WNBA'), { target: { value: 'Q1' } });
  expect(screen.getByText(/Línea original 40.5/)).toBeInTheDocument();
  expect(JSON.stringify(datos)).toBe(antes);
});
