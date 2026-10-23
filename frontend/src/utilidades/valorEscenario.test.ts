import { describe, expect, it } from 'vitest';
import { evaluarEscenario } from './valorEscenario';

describe('retorno de escenario deportivo', () => {
  it('conserva push y distingue fallo de uno menos probabilidad', () => {
    const r = evaluarEscenario(.4,.3,.3,2);
    expect(r?.ev).toBeCloseTo(.1);
    expect(r?.cuotaEquilibrio).toBeCloseTo(1.75);
    expect(r?.desviacionRetorno).toBeCloseTo(Math.sqrt(.7-.01));
  });
  it('no complementa la probabilidad de un underdog ni recomienda stake', () => {
    expect(evaluarEscenario(.2,.8,0,3)?.ev).toBeCloseTo(-.4);
    expect(evaluarEscenario(.6,.4,0,2)?.ev).toBeCloseTo(.2);
  });
  it('rechaza cuotas invalidas, distribución incompleta y NaN', () => {
    for (const c of [null, 1, NaN, 1001]) expect(evaluarEscenario(.5,.5,0,c)).toBeNull();
    expect(evaluarEscenario(.6,.6,0,2)).toBeNull();
    expect(evaluarEscenario(null,.5,0,2)).toBeNull();
  });
});
