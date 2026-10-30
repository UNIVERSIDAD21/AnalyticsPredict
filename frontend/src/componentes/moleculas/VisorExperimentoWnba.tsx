import { useRef, useState } from 'react';
import { validarInformeExperimento, type InformeExperimento } from '../../servicios/informeExperimento';
export function VisorExperimentoWnba() {
  const [r, setR] = useState<InformeExperimento | null>(null), [error, setError] = useState('');
  const secuencia = useRef(0);
  const cargar = async (f?: File) => {
    const actual = ++secuencia.current;
    setR(null); setError(''); if (!f) return;
    if (f.size > 8_000_000) { setError('El archivo supera el límite de 8 MB.'); return; }
    try { const dato = validarInformeExperimento(JSON.parse(await f.text())); if (actual === secuencia.current) setR(dato); }
    catch (e) { if (actual === secuencia.current) setError(e instanceof Error ? e.message : 'No se pudo leer la evaluación.'); }
  };
  return <section className="tarjeta space-y-4"><h2 className="text-lg font-semibold">Evaluaciones guardadas</h2>
    <p className="text-sm text-texto-secundario">Abre el JSON del experimento offline WNBA para revisar sus resultados. Se lee solo en esta página: no sube el archivo, consulta fuentes, entrena ni cambia el modelo activo.</p>
    <label className="block text-sm">Abrir evaluación WNBA guardada<input type="file" className="block mt-2 max-w-full" accept="application/json,.json" onChange={e => { void cargar(e.target.files?.[0]); }} /></label>
    {error && <p role="alert">{error}</p>}
    {r && <><p className="text-sm">Solo retrospectiva exploratoria · 0 prospectivos · No activado · Sin refit final</p><p className="text-sm text-texto-secundario">{r.limitacion}</p>
      <p className="text-sm">Predicciones experimentales {r.cobertura.experimento}/{r.cobertura.denominador} · Original {r.cobertura.original}/{r.cobertura.denominador} · Comparación común {r.cobertura.comunes}</p>
      <p className="text-sm">Selección en CAL: k={r.seleccion.elegida.k} · semivida={r.seleccion.elegida.semivida_dias ?? 'uniforme'}. La mayor cobertura no demuestra mayor precisión.</p>
      <div className="overflow-x-auto"><table className="text-sm w-full text-left"><caption className="text-left mb-3">Mismos encuentros: experimento / original / media de liga</caption><thead><tr><th className="p-2">Objetivo</th><th className="p-2">MAE</th><th className="p-2">Brier binario</th><th className="p-2">Cobertura intervalo 80% RAW</th></tr></thead><tbody>{Object.keys(r.tabla_comun.experimento).map(key => <tr key={key} className="border-t border-white/10"><th className="p-2">{key}</th>{(['mae', 'brier_binario', 'cobertura_intervalo80_raw'] as const).map(campo => <td className="p-2" key={campo}>{[r.tabla_comun.experimento, r.tabla_comun.original, r.tabla_comun.media_liga].map(t => t[key][campo].toFixed(3)).join(' / ')}</td>)}</tr>)}</tbody></table></div>
      <details><summary>Evaluación de cobertura ampliada · denominador distinto</summary><pre className="text-xs whitespace-pre-wrap break-all mt-3">{JSON.stringify(r.tabla_ampliada, null, 2)}</pre></details>
      <details><summary>Identidad declarada en el archivo</summary><p className="text-xs break-all mt-3">Publicación {r.snapshot.publicacion} · corte {r.snapshot.corte_exclusivo} · dataset {r.snapshot.dataset_sha256}. Archivo local: esta vista no acredita autenticidad de su origen ni certifica sus métricas.</p></details>
    </>}
  </section>;
}
