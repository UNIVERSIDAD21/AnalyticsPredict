import '@testing-library/jest-dom/vitest';
import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { TarjetaProbabilidad } from './TarjetaProbabilidad';

afterEach(cleanup);
describe('probabilidades compartidas de baloncesto', () => {
  it('mantiene tres probabilidades sin convertir el push en Under', () => {
    render(<TarjetaProbabilidad linea={170} probabilidadOver={0.4} probabilidadUnder={0.58} probabilidadPush={0.02} decimales={2} mediaTotal={171} desviacion={17} />);
    expect(screen.getByText('40.00%')).toBeInTheDocument();
    expect(screen.getByText('58.00%')).toBeInTheDocument();
    expect(screen.getByText('2.00%')).toBeInTheDocument();
    expect(screen.queryByText('60.00%')).toBeNull();
    expect(screen.getByRole('img')).toHaveAccessibleName('Over 40.00%, Under 58.00%, Push 2.00%');
    expect(screen.getByTestId('barra-push')).toHaveStyle({ width: '2%', left: '40%' });
  });

  it('conserva el formato NBA de dos lados y no redondea una línea distinta', () => {
    render(<TarjetaProbabilidad linea={170.55} probabilidadOver={0.65} probabilidadUnder={0.35} mediaTotal={175} desviacion={17} />);
    expect(screen.getByText('65.0%')).toBeInTheDocument();
    expect(screen.getByText('35.0%')).toBeInTheDocument();
    expect(screen.getByText('Over 170.55')).toBeInTheDocument();
    expect(screen.queryByText(/push/i)).toBeNull();
  });
});
