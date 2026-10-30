import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Encabezado } from '../organismos/Encabezado';
import { clienteAPI, extraerMensajeError } from '../../servicios/api';
import { descargar } from '../../servicios/cuadernoLocal';
interface ModeloLaboratorio { disponible: boolean | null; modelo_version?: string | number; corte_modelo?: string | null; dataset_hash?: string; validacion?: unknown; limite: string }
interface Inventario { fuente: string; certificacion: string; modelos: Record<string, ModeloLaboratorio> }
interface Medida { mae?: number; mae_media_liga?: number; mae_referencia?: number; n?: number }
function TablaDesarrollo({ datos }: { datos: Inventario }) {
  const filas = Object.entries(datos.modelos).flatMap(([liga, m]) => {
    const v = m.validacion as { evaluacion?: { mercados?: Record<string, Medida>; partidos?: number } } | undefined;
    return Object.entries(v?.evaluacion?.mercados ?? {}).map(([objetivo, medida]) => ({ liga, objetivo, medida, total: v?.evaluacion?.partidos }));
  });
  const numero = (n?: number) => n == null ? 'N/D' : n.toFixed(3);
  return <section className="tarjeta space-y-3 overflow-x-auto"><h2 className="text-lg font-semibold">Candidato frente a referencia · desarrollo original</h2><p className="text-sm text-texto-secundario">Mismos pares dentro de cada liga/objetivo. Estas métricas retrospectivas no se atribuyen al artefacto final publicado ni certifican rendimiento futuro.</p>
    {!filas.length ? <p>Comparaciones disponibles: N/D.</p> : <table className="text-sm text-left w-full"><thead><tr><th className="p-2">Liga / objetivo</th><th className="p-2">Evaluados / elegibles</th><th className="p-2">MAE candidato</th><th className="p-2">MAE referencia</th></tr></thead><tbody>{filas.map(({ liga, objetivo, medida, total }) => <tr key={`${liga}-${objetivo}`} className="border-t border-neon-cyan/15"><th className="p-2">{liga.toUpperCase()} · {objetivo}</th><td className="p-2">{medida.n ?? 'N/D'} / {total ?? 'N/D'}</td><td className="p-2">{numero(medida.mae)}</td><td className="p-2">{numero(medida.mae_media_liga ?? medida.mae_referencia)}</td></tr>)}</tbody></table>}
  </section>;
}
export function PaginaLaboratorio() {
  const [datos, setDatos] = useState<Inventario | null>(null), [error, setError] = useState(''), [revision, setRevision] = useState(0);
  useEffect(() => {
    const c = new AbortController(); setDatos(null); setError('');
    clienteAPI.get<Inventario>('/api/local/modelos', { signal: c.signal }).then(r => { if (!c.signal.aborted) setDatos(r.data); }).catch(e => { if (!c.signal.aborted) setError(extraerMensajeError(e)); });
    return () => c.abort();
  }, [revision]);
  return <div className="min-h-screen"><Encabezado /><main id="contenido-principal" className="contenedor py-8 space-y-6">
    <div><p className="text-neon-cyan text-sm">Modelos y evidencia</p><h1 className="text-3xl font-semibold mt-2">Laboratorio</h1><p className="text-texto-secundario mt-3">Versión y corte del artefacto local, separados de la actualidad de la BD y de su eficacia.</p></div>
    {error ? <div role="alert" className="tarjeta">{error}<button className="text-neon-cyan block mt-3" onClick={() => setRevision(v => v+1)}>Reintentar inventario</button></div> : !datos ? <p role="status">Leyendo artefactos locales…</p> : <>
      <section className="tarjeta overflow-x-auto"><h2 className="font-semibold text-lg mb-4">Publicaciones encontradas · {datos.certificacion}</h2><table className="w-full text-sm text-left"><thead><tr><th className="p-3">Liga</th><th className="p-3">Artefacto</th><th className="p-3">Versión</th><th className="p-3">Corte de datos</th></tr></thead><tbody>{Object.entries(datos.modelos).map(([liga, m]) => <tr key={liga} className="border-t border-neon-cyan/15"><th className="p-3">{liga.toUpperCase()}</th><td className="p-3">{m.disponible === null ? 'No acreditado' : m.disponible ? 'Cargable' : 'No disponible'}</td><td className="p-3 break-all">{m.modelo_version ?? 'N/D'}</td><td className="p-3 whitespace-nowrap">{m.corte_modelo ?? 'N/D'}</td></tr>)}</tbody></table></section>
      <TablaDesarrollo datos={datos} />
      <div className="grid md:grid-cols-2 gap-5">{Object.entries(datos.modelos).map(([liga, m]) => <section key={liga} className="tarjeta space-y-3 min-w-0"><h2 className="font-semibold">{liga.toUpperCase()}</h2><p className="text-sm text-texto-secundario">{m.limite}</p><p className="text-sm">Calibración independiente del artefacto final: N/D.</p>{m.validacion != null ? <details><summary>Evaluación de desarrollo preservada</summary><pre className="text-xs whitespace-pre-wrap break-all mt-3">{JSON.stringify(m.validacion, null, 2)}</pre></details> : <p className="text-sm">Métricas emparejadas disponibles en este inventario: N/D.</p>}{m.dataset_hash && <details><summary>Identidad de datos</summary><p className="text-xs break-all mt-3">{m.dataset_hash}</p></details>}</section>)}</div>
      <button className="boton-secundario" onClick={() => descargar('inventario-modelos.json', JSON.stringify(datos, null, 2))}>Exportar inventario</button>
    </>}
    <section className="tarjeta space-y-3"><h2 className="font-semibold">Criterio de comparación</h2><p className="text-sm text-texto-secundario">Comparar el modelo actual, una referencia y el candidato sobre los mismos encuentros: MAE, sesgo, cobertura, probabilidades e intervalos por liga y objetivo. Conservar abstenciones y límites temporales. Un refit no hereda la evaluación del candidato.</p><p className="text-sm">No se entrena ni activa ningún modelo desde esta pantalla. Las mejoras de recencia, covarianzas y calibración necesitan snapshots y evaluación propios.</p><Link className="text-neon-cyan text-sm" to="/base-local">Consultar el artefacto NBA →</Link></section>
  </main></div>;
}
