import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FormularioAnalisis } from "../organismos/FormularioAnalisis";
import {
  EstadoVacio,
  PanelesAnalisisBaloncesto,
} from "../organismos/PanelesAnalisisBaloncesto";
import { ResultadoWnba } from "../organismos/ResultadoWnba";
import {
  analizarWnba,
  cargarWnba,
  type FormularioWnba,
  type ResultadoWnba as Resultado,
} from "../../servicios/wnba";
import { crearApuesta } from "../../servicios/bitacora";
import { extraerMensajeError } from "../../servicios/api";
import type { Equipo, LadoApuesta, PartidoResumen } from "../../tipos";

const hoy = () =>
  new Intl.DateTimeFormat("en-CA", { timeZone: "America/Bogota" }).format(
    new Date(),
  );
const mercados = [
  { valor: "Q1" as const, etiqueta: "Primer Cuarto (Q1)" },
  { valor: "Q2" as const, etiqueta: "Segundo Cuarto (Q2)" },
  { valor: "Q3" as const, etiqueta: "Tercer Cuarto (Q3)" },
  { valor: "Q4" as const, etiqueta: "Cuarto Cuarto (Q4)" },
  {
    valor: "COMPLETO" as const,
    etiqueta: "Total de regulación (40 min, sin OT)",
  },
];

export function ModuloWnba() {
  const [datos, setDatos] = useState<Awaited<
    ReturnType<typeof cargarWnba>
  > | null>(null);
  const [temporadas, setTemporadas] = useState<string[] | null>(null);
  const [corte, setCorte] = useState(hoy);
  const [post, setPost] = useState(false);
  const [prueba, setPrueba] = useState(false);
  const [fixture, setFixture] = useState<PartidoResumen | null>(null);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [revision, setRevision] = useState(0);
  const [tab, setTab] = useState<"analisis" | "historial" | "estadisticas">(
    "analisis",
  );
  const [lado, setLado] = useState<LadoApuesta>("OVER");
  const [guardar, setGuardar] = useState(false);
  const [cuota, setCuota] = useState("");
  const [stake, setStake] = useState("");
  const montado = useRef(true);
  const generacion = useRef(0);
  const peticion = useRef<AbortController | null>(null);
  const cancelar = useCallback(() => {
    generacion.current++;
    peticion.current?.abort();
  }, []);
  useEffect(() => {
    montado.current = true;
    return () => {
      montado.current = false;
      cancelar();
    };
  }, [cancelar]);
  useEffect(() => {
    const controller = new AbortController();
    cargarWnba(controller.signal)
      .then((d) => {
        if (controller.signal.aborted) return;
        setDatos(d);
        setError(null);
        setTemporadas((prev) =>
          prev === null
            ? d.catalogo.temporadas.map((t) => t.id)
            : prev.filter((id) =>
                d.catalogo.temporadas.some((t) => t.id === id),
              ),
        );
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(extraerMensajeError(e));
      });
    return () => controller.abort();
  }, [revision]);
  const invalidar = useCallback(() => {
    generacion.current++;
    peticion.current?.abort();
    setCargando(false);
    setResultado(null);
    setError(null);
    setGuardar(false);
  }, []);
  const equipos = useMemo<Equipo[]>(
    () =>
      datos?.catalogo.equipos.map((t) => ({
        ...t,
        nombre_corto: t.nombre,
        abreviatura: "",
      })) ?? [],
    [datos],
  );
  const seleccionar = useCallback(
    (p: PartidoResumen | null) => {
      invalidar();
      setFixture(p);
      if (p) {
        setCorte(
          new Intl.DateTimeFormat("en-CA", {
            timeZone: "America/Bogota",
          }).format(new Date(p.fecha_partido)),
        );
        if (p.tipo_partido === "POST") setPost(true);
      }
    },
    [invalidar],
  );
  const enviar = async (p: FormularioWnba, seleccion?: LadoApuesta) => {
    if (!datos?.catalogo.modelo.disponible) {
      setError("Modelo WNBA no disponible.");
      return;
    }
    if (!temporadas?.length) {
      setError("Selecciona al menos una temporada WNBA.");
      return;
    }
    const id = ++generacion.current;
    peticion.current?.abort();
    const controller = new AbortController();
    peticion.current = controller;
    setCargando(true);
    setError(null);
    setResultado(null);
    setGuardar(false);
    setLado(seleccion ?? "OVER");
    try {
      const r = await analizarWnba(
        {
          ...p,
          temporadas,
          corte,
          fases: post ? ["REG", "POST"] : ["REG"],
          es_prueba: prueba,
        },
        controller.signal,
      );
      if (!montado.current || id !== generacion.current) return;
      setResultado(r);
      setDatos((d) =>
        d ? { ...d, historial: [r, ...d.historial].slice(0, 20) } : d,
      );
    } catch (e) {
      if (
        montado.current &&
        id === generacion.current &&
        !controller.signal.aborted
      )
        setError(extraerMensajeError(e));
    } finally {
      if (montado.current && id === generacion.current) setCargando(false);
    }
  };
  const guardarSeleccion = async () => {
    if (!resultado?.guardar_bitacora_habilitado) return;
    const q = Number(cuota),
      s = Number(stake);
    if (
      !Number.isFinite(q) ||
      q <= 1 ||
      q > 1000 ||
      !Number.isFinite(s) ||
      s <= 0
    ) {
      setError("Introduce cuota decimal >1 y stake positivo.");
      return;
    }
    setCargando(true);
    try {
      const r = resultado;
      const p = r.predicciones[r.mercado];
      await crearApuesta({
        competicion_codigo: "wnba",
        partido_id: r.partido_id,
        equipo_local: r.equipo_local,
        equipo_visitante: r.equipo_visitante,
        fecha_partido: r.fecha_partido
          ? new Intl.DateTimeFormat("en-CA", {
              timeZone: "America/Bogota",
            }).format(new Date(r.fecha_partido))
          : undefined,
        mercado: r.mercado,
        lado,
        linea: r.linea,
        cuota: q,
        stake: s,
        probabilidad_sistema:
          r.probabilidades[lado === "OVER" ? "over" : "under"],
        confianza_sistema: null,
        prediccion_media: p.media_total,
        prediccion_desviacion: p.desviacion_total,
        razones: [
          {
            tipo: "trazabilidad_wnba",
            analisis_id: r.analisis_id,
            calibracion: "SIN_CALIBRAR",
            incluye_ot: false,
          },
        ],
      });
      setGuardar(false);
    } catch (e) {
      setError(extraerMensajeError(e));
    } finally {
      if (montado.current) setCargando(false);
    }
  };
  const validacion = datos?.catalogo.modelo.validacion;
  return (
    <div aria-label="Analizador WNBA" className="min-w-0">
      <section className="tarjeta p-4 mb-6 space-y-2">
        <h1 className="text-xl font-futurista text-neon-cyan">
          WNBA · Predictor propio
        </h1>
        <p className="text-sm">
          Datos reales de la BD · cuatro cuartos de 10 minutos · regulación sin
          OT · estimaciones SIN CALIBRAR.
        </p>
        {datos && (
          <p className="text-xs text-texto-secundario">
            {datos.catalogo.finales_n} finales en BD;{" "}
            {datos.catalogo.elegibles_n} REG/POST elegibles por estructura;{" "}
            {datos.catalogo.equipos.length} equipos de liga. Último final:{" "}
            {datos.catalogo.ultimo_final_bd ?? "N/D"}.{" "}
            {datos.catalogo.cobertura}
          </p>
        )}
        {datos?.catalogo.modelo.desactualizado && (
          <p role="alert" className="text-sm text-amber-300">
            La BD tiene resultados nuevos o corregidos que no están en la
            publicación WNBA. Actualiza su modelo; el análisis informa el corte
            realmente utilizado.
          </p>
        )}
        <button
          type="button"
          className="text-sm text-neon-cyan"
          disabled={cargando}
          onClick={() => {
            invalidar();
            setRevision((x) => x + 1);
          }}
        >
          Actualizar estado y calendario WNBA
        </button>
      </section>
      {error && (
        <p role="alert" className="tarjeta p-4 mb-4 text-red-300 break-words">
          WNBA: {error}
        </p>
      )}
      {!datos && <p role="status">Cargando catálogo WNBA…</p>}
      {datos && (
        <>
          {!datos.catalogo.modelo.disponible && (
            <p role="alert" className="mb-4">
              Modelo WNBA no disponible. Publicar su artefacto y actualizar
              estado; NBA y Euroliga siguen independientes.
            </p>
          )}
          <nav
            className="flex flex-wrap gap-3 mb-4"
            aria-label="Apartados WNBA"
          >
            {(["analisis", "estadisticas", "historial"] as const).map((t) => (
              <button
                type="button"
                key={t}
                aria-pressed={tab === t}
                onClick={() => setTab(t)}
                className="px-3 py-2 border border-neon-cyan/30 rounded"
              >
                {t === "analisis"
                  ? "Análisis"
                  : t === "historial"
                    ? `Historial WNBA (${datos.historial.length})`
                    : "Estadísticas y validación"}
              </button>
            ))}
          </nav>
          {tab === "analisis" && (
            <PanelesAnalisisBaloncesto
              formulario={
                <div className="space-y-4">
                  <section
                    className="tarjeta p-4 space-y-4"
                    aria-label="Alcance WNBA"
                  >
                    <label className="block text-sm">
                      Corte exclusivo de datos (Colombia)
                      <input
                        aria-label="Corte WNBA"
                        type="date"
                        max={hoy()}
                        value={corte}
                        disabled={cargando}
                        onChange={(e) => {
                          invalidar();
                          setCorte(e.target.value);
                        }}
                        className="input-base w-full mt-1"
                      />
                    </label>
                    <p className="text-xs text-texto-secundario">
                      Solo partidos de días anteriores al corte. Se excluye el
                      día completo porque no hay hora de publicación del
                      resultado final.
                    </p>
                    <fieldset>
                      <legend className="text-sm mb-2">
                        Temporadas WNBA para el cálculo
                      </legend>
                      <div className="flex flex-wrap gap-3">
                        {datos.catalogo.temporadas.map((t) => (
                          <label key={t.id} className="text-sm">
                            <input
                              type="checkbox"
                              checked={temporadas?.includes(t.id) ?? false}
                              disabled={cargando}
                              onChange={(e) => {
                                invalidar();
                                setTemporadas((prev) =>
                                  e.target.checked
                                    ? [...(prev ?? []), t.id]
                                    : (prev ?? []).filter((id) => id !== t.id),
                                );
                              }}
                            />{" "}
                            {t.nombre} ({t.fases.REG ?? 0} REG)
                          </label>
                        ))}
                      </div>
                    </fieldset>
                    <label className="block text-sm">
                      <input
                        type="checkbox"
                        checked={post}
                        disabled={cargando}
                        onChange={(e) => {
                          invalidar();
                          setPost(e.target.checked);
                        }}
                      />{" "}
                      Incluir playoffs (POST), además de REG
                    </label>
                    <p className="text-xs text-texto-secundario">
                      PRE, invitados, All-Star y Copa excluidos. Añadir POST
                      cambia el ajuste; la validación global corresponde a REG.
                    </p>
                    <label className="block text-sm">
                      Encuentro histórico oficial (opcional)
                      <select
                        aria-label="Partido histórico WNBA"
                        className="input-base w-full mt-1"
                        value={fixture?.id ?? ""}
                        disabled={cargando}
                        onChange={(e) =>
                          seleccionar(
                            datos.pasados.find(
                              (p) => p.id === e.target.value,
                            ) ?? null,
                          )
                        }
                      >
                        <option value="">
                          Simulación manual / calendario próximo
                        </option>
                        {datos.pasados.map((p) => (
                          <option key={p.id} value={p.id}>
                            {new Intl.DateTimeFormat("en-CA", {
                              timeZone: "America/Bogota",
                            }).format(new Date(p.fecha_partido))}{" "}
                            · {p.equipo_local_nombre} —{" "}
                            {p.equipo_visitante_nombre}
                          </option>
                        ))}
                      </select>
                    </label>
                    {!datos.proximos.length && (
                      <p className="text-xs text-texto-secundario">
                        No hay próximos encuentros WNBA disponibles en la BD.
                        Puedes analizar manualmente sin inventar un partido
                        oficial.
                      </p>
                    )}
                    <label className="block text-xs">
                      <input
                        type="checkbox"
                        checked={prueba}
                        disabled={cargando}
                        onChange={(e) => {
                          invalidar();
                          setPrueba(e.target.checked);
                        }}
                      />{" "}
                      Identificar como análisis de prueba, no prospectivo
                    </label>
                    <p className="text-xs text-texto-secundario">
                      En vivo desactivado: no se analizan posesiones, reloj ni
                      parciales observados en esta versión.
                    </p>
                  </section>
                  <fieldset
                    disabled={!datos.catalogo.modelo.disponible}
                    className="min-w-0"
                  >
                    <FormularioAnalisis
                      deporte="WNBA"
                      equipos={equipos}
                      opcionesMercado={mercados}
                      partidosDisponibles={datos.proximos}
                      textoAyudaMercado="Q1–Q4 y total de 40 minutos. Todas las líneas SIN OT."
                      partidoActual={fixture}
                      onSeleccionarPartido={seleccionar}
                      onCambiarParametros={invalidar}
                      cargando={cargando}
                      onAnalizar={enviar}
                    />
                  </fieldset>
                </div>
              }
            >
              {cargando ? (
                <div role="status" className="tarjeta p-8">
                  Calculando con el histórico WNBA seleccionado…
                </div>
              ) : resultado ? (
                <ResultadoWnba
                  r={resultado}
                  onGuardar={() => setGuardar(true)}
                />
              ) : (
                <div className="tarjeta">
                  <EstadoVacio />
                </div>
              )}
            </PanelesAnalisisBaloncesto>
          )}
          {guardar && resultado && (
            <section
              className="tarjeta p-4 mt-4 space-y-3"
              aria-label="Guardar selección WNBA"
            >
              <h2>Guardar selección {lado} · solo registro manual</h2>
              <label className="block">
                Cuota decimal
                <input
                  aria-label="Cuota WNBA"
                  value={cuota}
                  onChange={(e) => setCuota(e.target.value)}
                  type="number"
                  step="0.01"
                  className="input-base w-full"
                />
              </label>
              <label className="block">
                Stake elegido por ti
                <input
                  aria-label="Stake WNBA"
                  value={stake}
                  onChange={(e) => setStake(e.target.value)}
                  type="number"
                  step="0.01"
                  className="input-base w-full"
                />
              </label>
              <button
                type="button"
                onClick={guardarSeleccion}
                disabled={cargando}
              >
                Confirmar guardado
              </button>
              <button
                type="button"
                className="ml-4"
                onClick={() => setGuardar(false)}
              >
                Cancelar
              </button>
            </section>
          )}
          {tab === "historial" && (
            <section className="space-y-4" aria-label="Historial WNBA">
              {!datos.historial.length && (
                <p>Aún no hay análisis WNBA registrados.</p>
              )}
              {datos.historial.map((r) => (
                <details key={r.analisis_id} className="tarjeta p-4">
                  <summary>
                    {new Date(r.fecha_analisis).toLocaleString()} ·{" "}
                    {r.equipo_local} — {r.equipo_visitante} · {r.mercado}{" "}
                    {r.linea} · {r.es_prueba ? "PRUEBA" : r.modo}
                  </summary>
                  <div className="mt-4">
                    <ResultadoWnba r={r} />
                  </div>
                </details>
              ))}
            </section>
          )}
          {tab === "estadisticas" && (
            <section
              className="tarjeta p-4 space-y-4"
              aria-label="Validación WNBA"
            >
              <h2 className="text-xl">
                Validación temporal · candidato congelado REG
              </h2>
              <p className="text-sm">
                No son métricas del refit actual ni de cada selección
                personalizada de temporadas. Calibración probabilística: no
                acreditada.
              </p>
              <p className="text-sm">
                La mejora del total frente a la referencia es pequeña y varios
                cuartos no la superan. No hay superioridad general acreditada;
                los intervalos RAW tampoco tienen cobertura nominal garantizada.
              </p>
              {validacion && (
                <>
                  <p className="text-sm">
                    TRAIN {validacion.train.n} ({validacion.train.desde}–
                    {validacion.train.hasta}); CAL selección{" "}
                    {validacion.cal_seleccion.n}; CAL dispersión{" "}
                    {validacion.cal_dispersion.n}.
                  </p>
                  <p className="text-sm">
                    EVAL {validacion.evaluacion.desde}–
                    {validacion.evaluacion.hasta}:{" "}
                    {validacion.evaluacion.analizados}/
                    {validacion.evaluacion.partidos} analizados,{" "}
                    {validacion.evaluacion.abstenciones} abstenciones, cobertura{" "}
                    {(100 * validacion.evaluacion.cobertura).toFixed(1)} %.
                  </p>
                  <p className="text-xs break-all">
                    {validacion.candidato_version} · {validacion.limitacion}
                  </p>
                  <div className="overflow-x-auto">
                    <table className="min-w-[600px] text-sm w-full [&_th]:px-2 [&_td]:px-2">
                      <thead>
                        <tr>
                          <th>Periodo</th>
                          <th>MAE</th>
                          <th>MAE media TRAIN</th>
                          <th>Brier</th>
                          <th>Brier referencia</th>
                          <th>Log loss</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(validacion.evaluacion.mercados).map(
                          ([key, x]) => (
                            <tr
                              key={key}
                              className="border-t border-neon-cyan/10"
                            >
                              <th className="py-2">{key}</th>
                              <td>{x.mae.toFixed(2)}</td>
                              <td>{x.mae_referencia.toFixed(2)}</td>
                              <td>{x.brier_multiclase.toFixed(3)}</td>
                              <td>{x.brier_referencia.toFixed(3)}</td>
                              <td>{x.log_loss.toFixed(3)}</td>
                            </tr>
                          ),
                        )}
                      </tbody>
                    </table>
                  </div>
                  <details>
                    <summary>
                      Frecuencias por intervalos de probabilidad (Over total)
                    </summary>
                    <p className="text-xs mt-2">
                      Diagnóstico retrospectivo del candidato, no calibrador ni
                      precisión garantizada.
                    </p>
                    <div className="overflow-x-auto">
                      <table className="min-w-[600px] text-sm w-full [&_th]:px-2 [&_td]:px-2">
                        <thead>
                          <tr>
                            <th>Intervalo</th>
                            <th>N</th>
                            <th>Prob. media</th>
                            <th>Frecuencia real</th>
                          </tr>
                        </thead>
                        <tbody>
                          {validacion.evaluacion.mercados.COMPLETO.calibracion_bins.map(
                            (b) => (
                              <tr key={b.desde}>
                                <td>
                                  {Math.round(100 * b.desde)}–
                                  {Math.round(100 * b.hasta)} %
                                </td>
                                <td>{b.n}</td>
                                <td>
                                  {b.probabilidad_media == null
                                    ? "N/D"
                                    : (100 * b.probabilidad_media).toFixed(1) +
                                      " %"}
                                </td>
                                <td>
                                  {b.frecuencia_observada == null
                                    ? "N/D"
                                    : (100 * b.frecuencia_observada).toFixed(
                                        1,
                                      ) + " %"}
                                </td>
                              </tr>
                            ),
                          )}
                        </tbody>
                      </table>
                    </div>
                  </details>
                </>
              )}
              <h3>Participantes elegibles de liga · muestra REG/POST en BD</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th>Equipo</th>
                      <th>Partidos</th>
                    </tr>
                  </thead>
                  <tbody>
                    {datos.catalogo.equipos.map((t) => (
                      <tr key={t.id}>
                        <th className="py-1">{t.nombre}</th>
                        <td>{t.muestras}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
