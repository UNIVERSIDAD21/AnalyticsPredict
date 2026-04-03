import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TarjetaCalidadDatosFutbol } from './TarjetaCalidadDatosFutbol';

describe('TarjetaCalidadDatosFutbol', () => {
  it('renderiza flags y penalizaciones con honestidad', () => {
    render(
      <TarjetaCalidadDatosFutbol
        calidad={{
          muestras: { h2h: 3, localHome: 12, visitanteAway: 9, localGlobal: 50, visitanteGlobal: 45, liga: 100 },
          rangoTemporal: { fechaMin: '2024-01-01', fechaMax: '2026-03-30' },
          temporadasIncluidas: ['2025-26', '2024-25'],
          competicionesIncluidas: ['laliga'],
          muestraInsuficiente: true,
          datosIncompletos: true,
          penalizacionesAplicadas: ['muestra_insuficiente', 'estado_mercados_vacio'],
        }}
      />,
    );

    expect(screen.getByTestId('tarjeta-calidad-datos-futbol')).toBeTruthy();
    expect(screen.getByText('MUESTRA INSUFICIENTE')).toBeTruthy();
    expect(screen.getByText('DATOS INCOMPLETOS')).toBeTruthy();
    expect(screen.getByText(/Penalizaciones:/).textContent).toContain('muestra_insuficiente');
  });
});
