/**
 * PaginaMetricas.tsx — Dashboard de métricas de calibración
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, BarChart3, Calendar, RotateCw } from 'lucide-react';
import { Encabezado, GraficoCurvaCalibracion } from '../organismos';
import { Boton, Spinner } from '../atomos';
import { AlertasCalibracion, MensajeError } from '../moleculas';
import { obtenerCurvaCalibracion, obtenerMetricasCalibracion } from '../../servicios/metricas';
import type {
  MercadoMetricas,
  MetricaMercado,
  OrigenMetricas,
  RespuestaCurvaCalibracion,
  RespuestaMetricasCalibracion,
} from '../../tipos';

type PeriodoSeleccion = '7' | '30' | '90' | 'rango';
type TipoBins = 'fijos' | 'cuantiles';

const MERCADOS_TABLA: Array<MetricaMercado['mercado']> = ['Q1', 'Q2', 'Q3', 'Q4'];
const MERCADOS_CURVA: MercadoMetricas[] = ['Q1', 'Q2', 'Q3', 'Q4', 'COMPLETO'];

const navegar = (ruta: string) => {
  if (window.location.pathname === ruta) return;
  window.history.pushState({}, '', ruta);
  window.dispatchEvent(new PopStateEvent('popstate'));
};

function formatearFechaISO(fecha: Date): string {
  return fecha.toISOString().slice(0, 10);
}

function formatearNumero(valor: number | null, decimales = 3): string {
  if (valor === null || !isFinite(valor)) return '—';
  return valor.toFixed(decimales);
}

function formatearEntero(valor: number | null): string {
  if (valor === null || !isFinite(valor)) return '—';
  return Math.round(valor).toLocaleString('es-ES');
}

function obtenerEstadoCalibracion(metrica?: MetricaMercado) {
  if (!metrica || !metrica.suficiente_data || metrica.ece === null) {
    return { texto: 'Sin datos', clase: 'text-texto-terciario border-neon-cyan/20' };
  }
  if (metrica.ece <= 0.02) {
    return { texto: 'Bueno', clase: 'text-neon-verde border-neon-verde/40' };
  }
  if (metrica.ece <= 0.05) {
    return { texto: 'Aceptable', clase: 'text-advertencia-500 border-advertencia-500/40' };
  }
  return { texto: 'Regular', clase: 'text-neon-rojo border-neon-rojo/40' };
}

export function PaginaMetricas() {
  const [origen, setOrigen] = useState<OrigenMetricas>('API_USUARIO');
  const [periodo, setPeriodo] = useState<PeriodoSeleccion>('30');
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const [estado, setEstado] = useState<'idle' | 'cargando' | 'exito' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [metricas, setMetricas] = useState<RespuestaMetricasCalibracion | null>(null);
  const [mercadoCurva, setMercadoCurva] = useState<MercadoMetricas>('Q1');
  const [tipoBins, setTipoBins] = useState<TipoBins>('fijos');
  const [nBins, setNBins] = useState(10);
  const [estadoCurva, setEstadoCurva] = useState<'idle' | 'cargando' | 'exito' | 'error'>('idle');
  const [errorCurva, setErrorCurva] = useState<string | null>(null);
  const [curva, setCurva] = useState<RespuestaCurvaCalibracion | null>(null);

  const rangoValido = periodo !== 'rango' || (Boolean(desde) && Boolean(hasta));

  const parametrosPeriodo = useMemo(() => {
    if (periodo === 'rango') {
      return {
        desde: desde || undefined,
        hasta: hasta || undefined,
      };
    }

    const dias = Number(periodo);
    const hoy = new Date();
    const inicio = new Date();
    inicio.setDate(hoy.getDate() - dias);

    return {
      desde: formatearFechaISO(inicio),
      hasta: formatearFechaISO(hoy),
    };
  }, [periodo, desde, hasta]);

  const cargarMetricas = useCallback(async () => {
    if (!rangoValido) {
      return;
    }
    setEstado('cargando');
    setError(null);
    try {
      const data = await obtenerMetricasCalibracion({
        origen,
        desde: parametrosPeriodo.desde,
        hasta: parametrosPeriodo.hasta,
      });
      setMetricas(data);
      setEstado('exito');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudieron cargar las métricas.');
      setEstado('error');
    }
  }, [origen, parametrosPeriodo, rangoValido]);

  const cargarCurva = useCallback(async () => {
    if (!rangoValido) {
      return;
    }
    setEstadoCurva('cargando');
    setErrorCurva(null);
    try {
      const data = await obtenerCurvaCalibracion({
        mercado: mercadoCurva,
        origen,
        tipo_bins: tipoBins,
        n_bins: nBins,
        desde: parametrosPeriodo.desde,
        hasta: parametrosPeriodo.hasta,
      });
      setCurva(data);
      setEstadoCurva('exito');
    } catch (err) {
      setErrorCurva(err instanceof Error ? err.message : 'No se pudo cargar la curva.');
      setEstadoCurva('error');
    }
  }, [mercadoCurva, nBins, origen, parametrosPeriodo, rangoValido, tipoBins]);

  useEffect(() => {
    void cargarMetricas();
  }, [cargarMetricas]);

  useEffect(() => {
    void cargarCurva();
  }, [cargarCurva]);

  const metricasPorMercado = metricas?.metricas_por_mercado ?? [];
  const resumenGlobal = metricasPorMercado.find((item) => item.mercado === 'COMPLETO');
  const resumenDisponible = Boolean(resumenGlobal?.suficiente_data);

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-futurista text-texto-principal flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-neon-cyan" />
              Métricas de calibración
            </h2>
            <p className="text-sm text-texto-secundario">
              Audita la calidad probabilística (Brier, ECE, LogLoss) por mercado.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Boton variante="secundario" iconoInicio={<RotateCw size={16} />} onClick={cargarMetricas}>
              Actualizar
            </Boton>
            <Boton variante="primario" onClick={() => navegar('/')}>
              Volver al análisis
            </Boton>
          </div>
        </div>

        <div className="tarjeta p-4 flex flex-wrap items-end gap-4">
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-widest text-texto-secundario">Origen</label>
            <select
              value={origen}
              onChange={(event) => setOrigen(event.target.value as OrigenMetricas)}
              className="w-52 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20 text-texto-principal"
            >
              <option value="API_USUARIO">API_USUARIO</option>
              <option value="BACKTEST_SINTETICO">BACKTEST_SINTETICO</option>
              <option value="BACKTEST_BATCH">BACKTEST_BATCH</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-widest text-texto-secundario">Periodo</label>
            <select
              value={periodo}
              onChange={(event) => setPeriodo(event.target.value as PeriodoSeleccion)}
              className="w-40 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20 text-texto-principal"
            >
              <option value="7">Últimos 7 días</option>
              <option value="30">Últimos 30 días</option>
              <option value="90">Últimos 90 días</option>
              <option value="rango">Rango</option>
            </select>
          </div>

          {periodo === 'rango' && (
            <div className="flex flex-wrap items-center gap-3">
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-widest text-texto-secundario">Desde</label>
                <div className="flex items-center gap-2 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20">
                  <Calendar className="w-4 h-4 text-neon-cyan" />
                  <input
                    type="date"
                    value={desde}
                    onChange={(event) => setDesde(event.target.value)}
                    className="bg-transparent text-sm text-texto-principal focus:outline-none"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-widest text-texto-secundario">Hasta</label>
                <div className="flex items-center gap-2 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20">
                  <Calendar className="w-4 h-4 text-neon-cyan" />
                  <input
                    type="date"
                    value={hasta}
                    onChange={(event) => setHasta(event.target.value)}
                    className="bg-transparent text-sm text-texto-principal focus:outline-none"
                  />
                </div>
              </div>
            </div>
          )}

          {!rangoValido && (
            <div className="flex items-center gap-2 text-xs text-advertencia-500">
              <AlertTriangle className="w-4 h-4" />
              Selecciona ambas fechas para cargar métricas.
            </div>
          )}
        </div>

        {estado === 'error' && error && (
          <MensajeError titulo="Error al cargar métricas" mensaje={error} onCerrar={() => setError(null)} />
        )}

        {estado === 'cargando' && (
          <div className="tarjeta flex items-center justify-center min-h-[240px]">
            <Spinner tamano="lg" texto="Cargando métricas..." centrado />
          </div>
        )}

        {estado === 'exito' && metricas && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
              <div className="tarjeta p-4 space-y-2">
                <p className="text-xs uppercase tracking-widest text-texto-secundario">Predicciones</p>
                <p className="text-2xl font-mono text-neon-cyan">
                  {resumenDisponible ? formatearEntero(resumenGlobal?.n_predicciones ?? null) : '—'}
                </p>
                <p className="text-[11px] text-texto-terciario">
                  {resumenDisponible ? 'Mercado completo' : 'Sin datos suficientes'}
                </p>
              </div>
              <div className="tarjeta p-4 space-y-2">
                <p className="text-xs uppercase tracking-widest text-texto-secundario">Brier</p>
                <p className="text-2xl font-mono text-neon-verde">
                  {resumenDisponible ? formatearNumero(resumenGlobal?.brier_score ?? null) : '—'}
                </p>
                <p className="text-[11px] text-texto-terciario">
                  Menor es mejor
                </p>
              </div>
              <div className="tarjeta p-4 space-y-2">
                <p className="text-xs uppercase tracking-widest text-texto-secundario">ECE</p>
                <p className="text-2xl font-mono text-neon-magenta">
                  {resumenDisponible ? formatearNumero(resumenGlobal?.ece ?? null) : '—'}
                </p>
                <p className="text-[11px] text-texto-terciario">
                  Desviación de calibración
                </p>
              </div>
              <div className="tarjeta p-4 space-y-2">
                <p className="text-xs uppercase tracking-widest text-texto-secundario">LogLoss</p>
                <p className="text-2xl font-mono text-neon-cyan">
                  {resumenDisponible ? formatearNumero(resumenGlobal?.log_loss ?? null) : '—'}
                </p>
                <p className="text-[11px] text-texto-terciario">
                  Penaliza sobreconfianza
                </p>
              </div>
            </div>

            <div className="tarjeta p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-neon-cyan">
                  Métricas por mercado
                </h3>
                <div className="text-xs text-texto-terciario">
                  Periodo: {metricas.periodo.inicio} → {metricas.periodo.fin}
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="text-xs uppercase tracking-wider text-texto-terciario">
                    <tr className="border-b border-neon-cyan/20">
                      <th className="py-2 text-left">Mercado</th>
                      <th className="py-2 text-right">N</th>
                      <th className="py-2 text-right">Brier</th>
                      <th className="py-2 text-right">ECE</th>
                      <th className="py-2 text-right">LogLoss</th>
                      <th className="py-2 text-right">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {MERCADOS_TABLA.map((mercado) => {
                      const metrica = metricasPorMercado.find((item) => item.mercado === mercado);
                      const estadoCalibracion = obtenerEstadoCalibracion(metrica);
                      return (
                        <tr key={mercado} className="border-b border-neon-cyan/10">
                          <td className="py-2 font-semibold text-texto-principal">{mercado}</td>
                          <td className="py-2 text-right text-texto-secundario">
                            {metrica?.suficiente_data ? formatearEntero(metrica.n_predicciones) : '—'}
                          </td>
                          <td className="py-2 text-right text-texto-secundario">
                            {metrica?.suficiente_data ? formatearNumero(metrica.brier_score) : '—'}
                          </td>
                          <td className="py-2 text-right text-texto-secundario">
                            {metrica?.suficiente_data ? formatearNumero(metrica.ece) : '—'}
                          </td>
                          <td className="py-2 text-right text-texto-secundario">
                            {metrica?.suficiente_data ? formatearNumero(metrica.log_loss) : '—'}
                          </td>
                          <td className="py-2 text-right">
                            <span className={`px-2 py-1 rounded-full text-[10px] uppercase border ${estadoCalibracion.clase}`}>
                              {estadoCalibracion.texto}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="tarjeta p-4 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-neon-cyan">
                    Curva de calibración
                  </h3>
                  <p className="text-xs text-texto-terciario">
                    Visualiza la confiabilidad del sistema por bins.
                  </p>
                </div>
                <div className="text-xs text-texto-terciario">
                  Periodo: {metricas.periodo.inicio} → {metricas.periodo.fin}
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] uppercase tracking-widest text-texto-terciario">
                    Mercado
                  </label>
                  <select
                    value={mercadoCurva}
                    onChange={(event) => setMercadoCurva(event.target.value as MercadoMetricas)}
                    className="w-36 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20 text-texto-principal text-sm"
                  >
                    {MERCADOS_CURVA.map((mercado) => (
                      <option key={mercado} value={mercado}>
                        {mercado}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] uppercase tracking-widest text-texto-terciario">
                    Tipo de bins
                  </label>
                  <select
                    value={tipoBins}
                    onChange={(event) => setTipoBins(event.target.value as TipoBins)}
                    className="w-36 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20 text-texto-principal text-sm"
                  >
                    <option value="fijos">Fijos</option>
                    <option value="cuantiles">Cuantiles</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] uppercase tracking-widest text-texto-terciario">
                    N bins
                  </label>
                  <input
                    type="number"
                    min={5}
                    max={20}
                    value={nBins}
                    onChange={(event) => {
                      const valor = Number(event.target.value);
                      if (Number.isNaN(valor)) {
                        setNBins(10);
                        return;
                      }
                      setNBins(Math.min(20, Math.max(5, valor)));
                    }}
                    className="w-24 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20 text-texto-principal text-sm"
                  />
                </div>

                <div className="flex items-end">
                  <Boton variante="secundario" tamano="sm" onClick={cargarCurva}>
                    Recalcular curva
                  </Boton>
                </div>
              </div>

              {estadoCurva === 'cargando' && (
                <div className="flex items-center justify-center min-h-[220px]">
                  <Spinner tamano="lg" texto="Cargando curva..." centrado />
                </div>
              )}

              {estadoCurva === 'error' && errorCurva && (
                <div className="space-y-3">
                  <MensajeError titulo="Error al cargar curva" mensaje={errorCurva} />
                  <Boton variante="secundario" tamano="sm" onClick={cargarCurva}>
                    Reintentar
                  </Boton>
                </div>
              )}

              {estadoCurva === 'exito' && curva && (
                <GraficoCurvaCalibracion datos={curva} />
              )}
            </div>

            {metricas.alertas_activas.length > 0 && (
              <div className="tarjeta p-4 space-y-3">
                <div className="flex items-center gap-2 text-neon-rojo">
                  <AlertTriangle className="w-4 h-4" />
                  <h3 className="text-sm font-futurista font-bold uppercase tracking-wider">
                    Alertas activas
                  </h3>
                </div>
                <AlertasCalibracion alertas={metricas.alertas_activas} onAccionCompletada={cargarMetricas} />
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
