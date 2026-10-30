import { useState } from 'react';
import type { ResultadoEuro } from '../../servicios/euroliga';
import { compararNormalDiscreta } from '../../servicios/consultaLocal';
export function ComparadorEuroliga({ fuente }: { fuente: ResultadoEuro }) {
  const [linea, setLinea] = useState(String(fuente.linea));
  const p = fuente.predicciones[fuente.mercado];
  const r = p && compararNormalDiscreta(p.media_total, p.desviacion_total, linea.trim() ? Number(linea) : Number.NaN);
  const porcentaje = (v: number) => `${(100 * v).toFixed(2)}%`;
  return <details className="my-4 border-t border-white/10 pt-3"><summary className="cursor-pointer text-sm text-neon-cyan">Comparar líneas · misma distribución Euroliga</summary><div className="space-y-3 pt-3 text-sm">
    <p>{fuente.mercado} · {fuente.modo} · 40 minutos sin OT. Se conservan los parámetros de esta corrida, incluido su escenario contextual cuando se aplicó.</p>
    <label className="block">Nueva línea entera o .5<input type="number" className="input-base mt-2 max-w-48 block" min="0" max="600" step="0.5" value={linea} onChange={e => setLinea(e.target.value)} /></label>
    <p>{r ? `Over ≈ ${porcentaje(r.over)} · Under ≈ ${porcentaje(r.under)} · Push ≈ ${porcentaje(r.push)}` : 'N/D: parámetros o línea no compatibles.'}</p>
    <p className="text-texto-secundario">Normal discretizada con corrección de continuidad. CDF aproximada; no es una nueva salida API, no ajusta, registra ni recalibra el modelo. El resultado original permanece arriba.</p>
  </div></details>;
}
