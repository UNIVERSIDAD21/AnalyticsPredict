import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { ListaBitacoraUnificada } from './ListaBitacoraUnificada';
import type { RegistroBitacoraUnificada } from '../../tipos';

afterEach(() => { cleanup(); vi.unstubAllEnvs(); });
describe('fechas del seguimiento', () => {
  it('conserva el día de una fecha sin hora en Bogotá y no inventa importes ausentes', () => {
    vi.stubEnv('TZ', 'America/Bogota');
    const registro = {
      id: 'registro', deporte: 'futbol', tipo_apuesta: 'SIMPLE', fecha_partido: '2026-10-17',
      creado_en: '2026-10-18T01:00:00Z', resultado: 'PENDIENTE',
      equipo_local: 'Local', equipo_visitante: 'Visitante', mercado: 'GOLES_FT', lado: 'OVER', linea: 2.5,
      stake: null, cuota: null, ganancia: null, probabilidad_sistema: null,
    } as unknown as RegistroBitacoraUnificada;
    render(<ListaBitacoraUnificada apuestas={[registro]} estado="exito" mensajeVacio="Vacío"
      onResolver={vi.fn()} onEliminar={vi.fn()} />);
    expect(screen.getByText('17/10/26')).toBeTruthy();
    expect(screen.queryByText('16/10/26')).toBeNull();
    expect(screen.queryByText('$0.00')).toBeNull();
  });

  it('distingue una apuesta Euroliga guardada en la tabla de baloncesto', () => {
    const registro = {
      id: 'registro-euro', deporte: 'baloncesto', competicion_nombre: 'Euroliga',
      tipo_apuesta: 'SIMPLE', fecha_partido: '2026-10-22', resultado: 'PENDIENTE',
      equipo_local: 'Real Madrid', equipo_visitante: 'Maccabi', mercado: 'COMPLETO',
      lado: 'UNDER', linea: 170.5, stake: 25, cuota: 1.91, ganancia: 0,
      probabilidad_sistema: 0.7, confianza_sistema: null,
    } as unknown as RegistroBitacoraUnificada;
    render(<ListaBitacoraUnificada apuestas={[registro]} estado="exito" mensajeVacio="Vacío"
      onResolver={vi.fn()} onEliminar={vi.fn()} />);
    expect(screen.getByText('EURO')).toBeTruthy();
    expect(screen.getByText('REAL MADRID')).toBeTruthy();
    expect(screen.getByText('MACCABI')).toBeTruthy();
    expect(screen.getByText('1.91')).toBeTruthy();
    expect(screen.getByText('70.0%')).toBeTruthy();
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });
});
