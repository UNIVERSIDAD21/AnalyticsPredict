import type { ResultadoEuro } from '../../servicios/euroliga';

function numero(n: number | null | undefined, decimales = 2): string {
  return typeof n === 'number' && Number.isFinite(n) ? n.toFixed(decimales) : 'N/D';
}

export function PanelDiagnosticoEuroliga({ resultado }: { resultado: ResultadoEuro }) {
  const d = resultado.diagnostico_modelo;
  const v = resultado.validacion_historica;
  const evaluacion = v?.evaluacion;
  const mercados = ['Q1', 'Q2', 'Q3', 'Q4', 'COMPLETO'];

  return <details className="tarjeta p-4 text-sm text-texto-secundario">
    <summary className="cursor-pointer font-semibold text-texto-principal">Método, historial de validación y trazabilidad</summary>
    <div className="mt-3 space-y-4">
      <section className="space-y-1">
        <h4 className="font-semibold text-neon-cyan">Modelo y corte</h4>
        <p>Ridge Euroliga · α={numero(d?.alpha_ridge)} · refit servido con {d?.partidos_entrenamiento ?? 'N/D'} finales, {d?.fecha_min ?? 'N/D'} a {d?.fecha_max ?? resultado.corte_datos}. Datos disponibles estrictamente antes del fixture: {resultado.contexto.corte_exclusivo ?? resultado.fecha_partido ?? 'N/D'}.</p>
        <p>Separación temporal de evaluación del candidato: TRAIN {v?.train_n ?? 'N/D'} · CAL {v?.cal_n ?? 'N/D'} ({v?.cal_util_n ?? 'N/D'} útiles) · EVAL {evaluacion?.partidos ?? 'N/D'} ({evaluacion?.evaluados ?? 'N/D'} evaluados, {evaluacion?.abstenciones ?? 'N/D'} abstenciones). Cobertura EVAL {evaluacion?.cobertura == null ? 'N/D' : `${(evaluacion.cobertura * 100).toFixed(1)}%`}.</p>
        <p>Validación {v?.tipo ?? 'N/D'}; prospectiva independiente registrada: {v?.prospectiva_n ?? 0}. CAL estima dispersión y no es un calibrador. {v?.limitacion ?? 'No hay limitación de validación disponible.'}</p>
      </section>
      <section className="space-y-2">
        <h4 className="font-semibold text-neon-cyan">EVAL retrospectiva por periodo</h4>
        {resultado.analisis_integral && <p className="text-xs">Esta evaluación no valida los nuevos ajustes de forma y descanso del escenario contextual.</p>}
        <p className="text-xs">Mide el candidato congelado en TRAIN, no este refit final. Comparación descriptiva frente a media de liga; no demuestra superioridad, eficacia prospectiva ni calibración. Línea de referencia fijada desde TRAIN, no la línea elegida para este análisis.</p>
        <div className="overflow-x-auto"><table className="w-full min-w-[650px] text-xs text-left"><thead><tr className="border-b border-neon-cyan/20 text-texto-terciario"><th className="p-2">Periodo</th><th className="p-2">n</th><th className="p-2">MAE modelo</th><th className="p-2">MAE media liga</th><th className="p-2">Brier RAW / 0,25</th><th className="p-2">Cobertura intervalo 80%</th></tr></thead>
          <tbody>{mercados.map((mercado) => { const m = evaluacion?.mercados?.[mercado]; return <tr key={mercado} className="border-b border-futurista-medio/40"><th className="p-2">{mercado}</th><td className="p-2">{m?.n ?? 'N/D'}</td><td className="p-2">{numero(m?.mae, 3)}</td><td className="p-2">{numero(m?.mae_media_liga, 3)}</td><td className="p-2">{numero(m?.brier_raw, 4)} / {numero(m?.brier_referencia_50, 2)}</td><td className="p-2">{m?.cobertura_intervalo_80 == null ? 'N/D' : `${(m.cobertura_intervalo_80 * 100).toFixed(1)}%`}</td></tr>; })}</tbody>
        </table></div>
      </section>
      <section className="space-y-1">
        <h4 className="font-semibold text-neon-cyan">Lectura y procedencia</h4>
        <p>Las probabilidades usan una aproximación gaussiana discreta RAW; no hay calibrador y se informa push cuando corresponde. Proyección de 40 minutos de regulación, sin OT. No son picks, stakes ni una recomendación de apuesta.</p>
        <p>Equipo local temporada {resultado.temporada_reciente}: {resultado.muestras_temporada.local} finales · visitante: {resultado.muestras_temporada.visitante}. Ejecución {resultado.fecha_analisis}; versión {resultado.modelo_version}; análisis {resultado.analisis_id}.</p>
        <p className="break-all">SHA-256 del dataset: {resultado.dataset_sha256}</p>
        <p>Registro original conservado en el journal Euroliga · ID {resultado.analisis_id}. {resultado.prospectiva_acreditada_por_fecha ? 'La fecha de captura es anterior a la fecha del fixture.' : 'No se acredita que la captura preceda al kickoff.'}</p>
      </section>
    </div>
  </details>;
}
