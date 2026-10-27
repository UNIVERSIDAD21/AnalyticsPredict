import { describe, expect, it } from 'vitest';
import { valorHistoricoFutbol, sumarObservados } from './datosHistoricosFutbol';
import { transformarPartidoEstadistico } from '../servicios/futbol/partidos';

describe('Datos históricos sin imputación', () => {
  it('preserva NULL y ceros por lado y no sustituye 1T por FT', () => {
    const p=transformarPartidoEstadistico({ goles_local: 2, goles_visitante: 0, corners_local: null, corners_visitante: 0, goles_local_2t: -1 });
    expect(p.cornersLocal).toBeNull();expect(p.cornersVisitante).toBe(0);
    expect(p.golesLocal2t).toBeNull();
    expect(valorHistoricoFutbol(p,'GOLES_1T','LOCAL')).toBeNull();
    expect(valorHistoricoFutbol(p,'GOLES_FT','VISITANTE')).toBe(0);
    expect(sumarObservados(p.cornersLocal,p.cornersVisitante)).toBeNull();
  });
  it('no trata tiros FT como observaciones por mitad', () => {
    const p=transformarPartidoEstadistico({ disparos_arco_local: 4 });
    expect(valorHistoricoFutbol(p,'DISPAROS_ARCO_1T','LOCAL')).toBeNull();
    expect(valorHistoricoFutbol(p,'DISPAROS_ARCO_FT','LOCAL')).toBe(4);
  });
});
