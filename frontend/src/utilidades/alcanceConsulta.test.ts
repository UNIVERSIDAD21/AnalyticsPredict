import { expect, it } from 'vitest';
import { alcanceConsulta } from './alcanceConsulta';
it('no atribuye OT a un cuarto WNBA ni regulación NBA a otra liga', () => {
  expect(alcanceConsulta({ liga: 'wnba', incluye_ot: true }, 'Q1')).toContain('Cuarto de 10 minutos, sin OT');
  expect(alcanceConsulta({ liga: 'wnba', incluye_ot: true }, 'COMPLETO')).toContain('más OT');
  expect(alcanceConsulta({ liga: 'wnba', incluye_ot: false }, 'COMPLETO')).toContain('regulación, sin OT');
  expect(alcanceConsulta({ liga: 'euroliga' }, 'COMPLETO')).toContain('40 minutos');
  expect(alcanceConsulta({ deporte: 'futbol' }, 'GOLES_FT')).toContain('sin prórroga ni penales');
});
