import type { ResultadoWnba as Resultado } from "../../servicios/wnba";

const n = (x: number | null | undefined) => (x == null ? "N/D" : x.toFixed(2));
const pct = (x: number) => `${(100 * x).toFixed(2)} %`;

export function ResultadoWnba({
  r,
  onGuardar,
}: {
  r: Resultado;
  onGuardar?: () => void;
}) {
  return (
    <section
      className="tarjeta p-4 sm:p-6 space-y-6 min-w-0"
      aria-label="Resultado WNBA"
    >
      <header className="space-y-2">
        <p className="text-neon-cyan text-sm">
          WNBA · Predictor propio · SIN CALIBRAR
        </p>
        <h2 className="text-xl font-futurista">
          {r.equipo_local} — {r.equipo_visitante}
        </h2>
        <p>
          {r.mercado} · línea {r.linea} · {r.modo}
          {r.es_prueba ? " · ANÁLISIS DE PRUEBA" : ""}
        </p>
        <p className="text-sm text-texto-secundario">
          Regulación de 40 minutos, sin prórroga. No es moneyline con OT.{" "}
          {r.fixture_fuente
            ? `Partido ESPN ${r.fixture_fuente}`
            : "Simulación manual: sin partido oficial asociado."}
        </p>
      </header>
      <div
        className="grid grid-cols-1 sm:grid-cols-3 gap-3"
        aria-label="Probabilidades WNBA"
      >
        {(["over", "under", "push"] as const).map((k) => (
          <div
            key={k}
            className="p-4 rounded-xl bg-futurista-oscuro border border-neon-cyan/20"
          >
            <p className="uppercase text-sm">{k}</p>
            <p className="text-2xl font-mono text-neon-cyan">
              {pct(r.probabilidades[k])}
            </p>
            <p className="text-xs text-texto-secundario">
              Estimación sin calibrar
            </p>
          </div>
        ))}
      </div>
      <section>
        <h3 className="font-semibold mb-2">
          Proyección e incertidumbre · puntos
        </h3>
        <p className="sm:hidden text-xs text-texto-secundario mb-2">
          Desliza la tabla horizontalmente para ver todas las columnas.
        </p>
        <div className="overflow-x-auto">
          <table className="min-w-[540px] w-full text-sm [&_th]:px-2 [&_td]:px-2">
            <thead>
              <tr>
                <th>Periodo</th>
                <th>Local</th>
                <th>Visitante</th>
                <th>Total</th>
                <th>σ total</th>
                <th>Intervalo 80 % RAW</th>
              </tr>
            </thead>
            <tbody>
              {["Q1", "Q2", "Q3", "Q4", "COMPLETO"]
                .map((k) => [k, r.predicciones[k]] as const)
                .map(([k, p]) => (
                  <tr key={k} className="border-t border-neon-cyan/10">
                    <th className="py-2">{k}</th>
                    <td>{n(p.media_local)}</td>
                    <td>{n(p.media_visitante)}</td>
                    <td>{n(p.media_total)}</td>
                    <td>{n(p.desviacion_total)}</td>
                    <td>
                      {n(p.intervalo_80_raw[0])}–{n(p.intervalo_80_raw[1])}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-texto-secundario mt-2">
          La dispersión agregada incluye covarianzas entre equipos y cuartos; no
          es la suma de desviaciones. Intervalos no calibrados.
        </p>
      </section>
      <section>
        <h3 className="font-semibold">Ganador de regulación · admite empate</h3>
        <p className="text-sm">
          {r.equipo_local}: {pct(r.ganador_regulacion.local)} · Empate:{" "}
          {pct(r.ganador_regulacion.empate)} · {r.equipo_visitante}:{" "}
          {pct(r.ganador_regulacion.visitante)}
        </p>
      </section>
      <section>
        <h3 className="font-semibold">Muestra y alcance efectivos</h3>
        <p className="text-sm">
          {r.muestras.partidos} partidos. Local: {r.muestras.local} (
          {n(r.muestras.efectivas_local)} efectivos); visitante:{" "}
          {r.muestras.visitante} ({n(r.muestras.efectivas_visitante)}{" "}
          efectivos). Mismo soporte Q1–Q4.
        </p>
        <p className="text-sm">
          Temporadas utilizadas: {r.temporadas_utilizadas.join(", ")} · fases:{" "}
          {r.fases_utilizadas.join(", ")} · recencia:{" "}
          {r.semivida_dias ? `semivida ${r.semivida_dias} días` : "uniforme"}.
        </p>
        <p className="text-sm">
          Confianza certificada: N/D. Calibrador: ninguno.
        </p>
      </section>
      <section>
        <h3 className="font-semibold">
          Valor con cuotas manuales · escenario RAW
        </h3>
        {(["over", "under"] as const).map((k) => (
          <p key={k} className="text-sm">
            {k.toUpperCase()}: cuota {n(r.valor[k].cuota)} · EV{" "}
            {r.valor[k].ev_sin_calibrar == null
              ? "N/D"
              : pct(r.valor[k].ev_sin_calibrar!)}
          </p>
        ))}
        <p className="text-xs text-texto-secundario">
          Incluye push. No es recomendación, stake ni rentabilidad acreditada.
        </p>
      </section>
      <details>
        <summary className="cursor-pointer font-semibold">
          Forma, H2H e historial real del alcance
        </summary>
        <p className="text-xs my-3 text-texto-secundario">{r.contexto.uso}</p>
        {[
          [r.equipo_local_id, r.equipo_local],
          [r.equipo_visitante_id, r.equipo_visitante],
        ].map(([id, nombre]) => (
          <div key={id} className="my-4">
            <h4>
              {nombre} · {r.contexto.equipos[id].n} partidos · media regulación{" "}
              {n(r.contexto.equipos[id].media_regulacion)}
            </h4>
            <p className="sm:hidden text-xs text-texto-secundario mb-2">
              Desliza la tabla horizontalmente para ver todas las columnas.
            </p>
            <div className="overflow-x-auto">
              <table className="min-w-[600px] w-full text-xs [&_th]:px-2 [&_td]:px-2">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Rival/sede</th>
                    <th>Q1–Q4 propios</th>
                    <th>Regulación</th>
                    <th>OT</th>
                    <th>FT</th>
                    <th>V/E/D reg.</th>
                  </tr>
                </thead>
                <tbody>
                  {r.contexto.equipos[id].recientes.map((p) => (
                    <tr key={p.id} className="border-t border-neon-cyan/10">
                      <td className="py-2 whitespace-nowrap">{p.fecha}</td>
                      <td>
                        {p.rival} ({p.como_local ? "L" : "V"})
                      </td>
                      <td className="whitespace-nowrap">
                        {p.cuartos.join(" / ")}
                      </td>
                      <td>
                        {p.regulacion}–{p.regulacion_rival}
                      </td>
                      <td>{p.ot}</td>
                      <td>{p.final}</td>
                      <td>{p.resultado}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
        <h4>Últimos enfrentamientos directos</h4>
        {r.contexto.h2h.length ? (
          r.contexto.h2h.map((p) => (
            <p key={p.id} className="text-xs my-2">
              {p.fecha}: {p.local} {p.y.slice(0, 4).reduce((a, b) => a + b, 0)}{" "}
              — {p.y.slice(4).reduce((a, b) => a + b, 0)} {p.visitante}{" "}
              (regulación)
            </p>
          ))
        ) : (
          <p className="text-sm">Sin enfrentamientos previos en el alcance.</p>
        )}
      </details>
      <details>
        <summary className="cursor-pointer font-semibold">
          Trazabilidad del análisis
        </summary>
        <dl className="text-xs space-y-2 mt-3 break-words">
          <dt>Fecha/hora</dt>
          <dd>{r.fecha_analisis}</dd>
          <dt>Corte exclusivo</dt>
          <dd>
            {r.corte_exclusivo} · {r.politica_corte}
          </dd>
          <dt>Temporadas solicitadas</dt>
          <dd>{r.temporadas_solicitadas.map((t) => t.nombre).join(", ")}</dd>
          <dt>Último final BD / último dato utilizado</dt>
          <dd>
            {r.ultimo_final_bd ?? "N/D"} / {r.ultimo_dato_utilizado}
          </dd>
          <dt>Ajuste propio / publicación</dt>
          <dd className="break-all">
            {r.modelo_version}
            <br />
            {r.publicacion_version}
          </dd>
          <dt>Huella del alcance</dt>
          <dd className="break-all">{r.dataset_sha256}</dd>
          <dt>Dispersión</dt>
          <dd>
            {r.dispersion.origen}; {r.dispersion.dispersión_n} residuos desde{" "}
            {r.dispersion.desde}.
          </dd>
          <dt>ID del análisis</dt>
          <dd>{r.analisis_id}</dd>
        </dl>
      </details>
      <section className="text-sm text-texto-secundario">
        <h3 className="font-semibold">Límites y advertencias</h3>
        <ul className="list-disc pl-5 space-y-1">
          {r.advertencias.map((x) => (
            <li key={x}>{x}</li>
          ))}
        </ul>
      </section>
      {r.guardar_bitacora_habilitado && onGuardar ? (
        <button type="button" onClick={onGuardar} className="boton-primario">
          Guardar selección en Bitácora
        </button>
      ) : (
        <p className="text-xs text-texto-secundario">
          Bitácora: {r.motivo_bitacora}
        </p>
      )}
    </section>
  );
}
