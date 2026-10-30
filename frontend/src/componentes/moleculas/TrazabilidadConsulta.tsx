import type { ResultadoVista } from '../../tipos/resultadoVista';
const texto = (v: unknown): string => v == null || v === '' ? 'N/D' : typeof v === 'boolean' ? (v ? 'Sí' : 'No') : typeof v === 'object' ? JSON.stringify(v) : String(v);
export function TrazabilidadConsulta({ resultado }: { resultado: ResultadoVista }) {
  const m = resultado.metadata ?? {};
  const filas: [string, unknown][] = [
    ['Consulta emitida', resultado.fecha_analisis], ['Identificador de consulta', m.analisis_id],
    ['Modo', m.modo_analisis ?? (resultado.es_en_vivo ? 'Corte condicionado; ver parciales' : 'Modo no informado')],
    ['Versión de cálculo', m.modelo_version], ['Dataset', m.dataset_sha256 ?? m.dataset_hash],
    ['Corte del modelo/datos', m.corte_modelo ?? m.corte_datos ?? m.ultimo_dato_utilizado],
    ['Corte exclusivo de consulta', m.corte_exclusivo ?? m.fecha_corte],
    ['Encuentro y revisión', [m.partido_id, m.fixture_revision_sha256].filter(v => v != null).join(' · ')],
    ['Tipo de probabilidad', m.probabilidad_tipo ?? (m.probabilidad_raw_no_calibrada === true ? 'RAW, sin calibración acreditada' : null)],
    ['Mercado seleccionado incluye prórroga', m.incluye_ot_mercado ?? m.incluye_ot ?? (m.regulacion_sin_ot === true ? false : null)],
  ];
  return <details className="my-4 border-t border-white/10 pt-3"><summary className="cursor-pointer text-sm text-neon-cyan">Fuente, corte y límites de esta consulta</summary>
    <dl className="grid sm:grid-cols-2 gap-3 pt-4 text-xs">{filas.map(([k, v]) => <div key={String(k)} className="min-w-0"><dt className="text-texto-secundario">{k}</dt><dd className="break-words mt-1">{texto(v)}</dd></div>)}</dl>
    <p className="text-xs text-texto-secundario mt-4">N/D significa que esta respuesta no conserva el dato. Guardar o reabrir una copia no actualiza el corte ni acredita vigencia del encuentro. Una etiqueta de confianza no certifica calibración.</p>
  </details>;
}
