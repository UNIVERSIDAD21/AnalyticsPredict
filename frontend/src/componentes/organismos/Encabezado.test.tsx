import '@testing-library/jest-dom/vitest';
import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { ProveedorDeporte } from '../../contextos/DeporteContext';
import { Encabezado } from './Encabezado';

afterEach(cleanup);
function Ruta() { return <output data-testid="ruta">{useLocation().pathname}</output>; }

describe('navegación deportiva', () => {
  it('sincroniza el deporte al navegar sin reemplazar rutas de detalle', async () => {
    render(<ProveedorDeporte><MemoryRouter initialEntries={['/futbol/partidos/partido-1']}>
      <Encabezado /><Ruta />
    </MemoryRouter></ProveedorDeporte>);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Cambiar a FÚTBOL' })).toHaveAttribute('aria-pressed', 'true'));
    expect(screen.getByTestId('ruta')).toHaveTextContent('/futbol/partidos/partido-1');
    fireEvent.click(screen.getByRole('button', { name: 'NBA' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Cambiar a NBA' })).toHaveAttribute('aria-pressed', 'true'));
    expect(screen.getByTestId('ruta')).toHaveTextContent('/app');
    fireEvent.click(screen.getByRole('button', { name: 'Fútbol' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Cambiar a FÚTBOL' })).toHaveAttribute('aria-pressed', 'true'));
    expect(screen.getByTestId('ruta')).toHaveTextContent('/futbol');
  });
});
