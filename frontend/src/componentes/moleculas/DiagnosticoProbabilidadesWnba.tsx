import { useState } from 'react';
interface Bin { desde: number; hasta: number; n: number; probabilidad_media: number | null; frecuencia_observada: number | null }
interface Medida { n: number; linea: number; linea_entera: number; brier_multiclase: number; brier_referencia?: number;
  log_loss: number; brier_con_push: number; push_observados: number; cobertura_intervalo80: number; calibracion_bins: Bin[] }
interface Validacion { candidato_version?: string; evaluacion?: { partidos?: number; analizados?: number; abstenciones?: number; desde?: string; hasta?: string; mercados?: Record<string, Medida> } }
const numero = (n: unknown, porcentaje = false) => typeof n === 'number' && Number.isFinite(n) ? `${(n*(porcentaje ? 100 : 1)).toFixed(porcentaje ? 2 : 4)}${porcentaje ? '%' : ''}` : 'N/D';
export function DiagnosticoProbabilidadesWnba({ datos }: { datos: unknown }) {
  const [seleccion, setSeleccion] = useState('COMPLETO');
  const v = datos && typeof datos === 'object' ? datos as Validacion : {};
  const mercados = Object.entries(v.evaluacion?.mercados ?? {}).filter(([,m]) => Array.isArray(m.calibracion_bins));
  const mercado = mercados.find(([k]) => k === seleccion) ?? mercados[0];
  const m = mercado?.[1];
  return <details className="space-y-3"><summary className="cursor-pointer text-neon-cyan">Fiabilidad declarada WNBA · candidato original</summary>
    <p className="text-xs text-texto-secundario">Retrospectiva ya observada, regulación sin OT. No es la evaluación del refit final ni de otras temporadas seleccionadas. No hay calibrador activado ni evidencia prospectiva en esta tabla.</p>
    <p className="text-xs break-all">Candidato: {v.candidato_version ?? 'N/D'}. Ventana: {v.evaluacion?.desde ?? 'N/D'} → {v.evaluacion?.hasta ?? 'N/D'}.</p>
    <p className="text-sm">Analizados / elegibles: {v.evaluacion?.analizados ?? 'N/D'} / {v.evaluacion?.partidos ?? 'N/D'} · Abstenciones: {v.evaluacion?.abstenciones ?? 'N/D'}.</p>
    {!m ? <p>Bins conservados: N/D. No se reconstruyen desde parámetros del refit.</p> : <>
      <label className="block text-sm">Mercado diagnóstico WNBA<select className="input-base block mt-2" value={mercado[0]} onChange={e => setSeleccion(e.target.value)}>{mercados.map(([k]) => <option key={k} value={k}>{k === 'COMPLETO' ? 'Total regulación · sin OT' : k}</option>)}</select></label>
      <p className="text-sm">Muestra {m.n} · Línea original {m.linea} · Brier suma de clases {numero(m.brier_multiclase)} · Referencia {numero(m.brier_referencia)} · Log loss {numero(m.log_loss)}.</p>
      <p className="text-xs text-texto-secundario">Brier = suma de errores cuadrados Over/Under/Push (rango0–2); en línea .5 es el doble del Brier binario. Menor es mejor, pero no certifica calibración. Las líneas originales no son cuotas de mercado.</p>
      <p className="text-sm">Intervalo RAW nominal80%: cobertura observada {numero(m.cobertura_intervalo80, true)} en la cohorte. Línea entera {m.linea_entera}: {m.push_observados} push observados · Brier con push {numero(m.brier_con_push)}.</p>
      <div className="overflow-x-auto"><table className="text-xs w-full text-left"><caption className="text-left mb-2">Bins originales de probabilidad Over · frecuencia observada, no pronóstico futuro</caption><thead><tr><th className="p-2">Rango</th><th className="p-2">n</th><th className="p-2">Probabilidad media</th><th className="p-2">Frecuencia observada</th></tr></thead><tbody>{m.calibracion_bins.map((b,i) => <tr key={i} className="border-t border-white/10"><th className="p-2">{Math.round(b.desde*100)}–{Math.round(b.hasta*100)}%</th><td className="p-2">{b.n}</td><td className="p-2">{numero(b.probabilidad_media, true)}</td><td className="p-2">{numero(b.frecuencia_observada, true)}</td></tr>)}</tbody></table></div>
      <p className="text-xs text-texto-secundario">Vacíos: N/D, no frecuencia cero. Los intervalos son [desde,hasta), salvo el último que incluye100%. Bins pequeños y partidos de un mismo día no sustentan conclusiones firmes; no se eligen ajustes mirando esta evaluación.</p>
    </>}
  </details>;
}
