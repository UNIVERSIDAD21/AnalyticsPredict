/**
 * DashboardFutbol.tsx — Dashboard de metricas del modulo de futbol
 *
 * Muestra:
 * - ROI por mercado con barras de progreso horizontales
 * - Seccion de calibracion: Brier Score, ECE, calibradores activos
 * - Estado de modelos: MAE por tipo, fecha de entrenamiento
 * - Grafico temporal: ROI acumulado ultimos 30 dias (Recharts)
 * - Componente ResumenMetricasFutbol
 */

import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArrowLeft,
  BarChart3,
  TrendingUp,
  Activity,
  Cpu,
  Calendar,
  RefreshCw,
  Target,
  Percent,
  Database,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Award,
} from 'lucide-react';
import { clsx } from 'clsx';

import { Encabezado, ResumenMetricasFutbol } from '../organismos';

const GraficoRoiTemporalFutbol = lazy(async () => ({
  default: (await import('../organismos/GraficoRoiTemporalFutbol')).GraficoRoiTemporalFutbol,
}));
import { MensajeError } from '../moleculas';
import { Boton, Spinner, Tarjeta } from '../atomos';
import {
  obtenerMetricasCalibracion,
  obtenerMetricasRendimiento,
  obtenerEstadoModelos,
  obtenerRoiTemporal,
} from '../../servicios/futbol';
import {
  obtenerObservabilidadHTTP,
  obtenerSaludBackend,
  type ObservabilidadHTTPResumen,
  type SaludBackend,
} from '../../servicios/observabilidad';
import type {
  MetricasCalibracionFutbol,
  MetricasRendimientoFutbol,
  EstadoModeloFutbol,
  CategoriaMercado,
  PuntoROITemporalFutbol,
} from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

const navegar = (ruta: string) => {
  if (window.location.pathname === ruta) return;
  window.history.pushState({}, '', ruta);
  window.dispatchEvent(new PopStateEvent('popstate'));
};

function formatearFecha(fechaISO: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function formatearPorcentaje(valor: number): string {
  const signo = valor >= 0 ? '+' : '';
  return `${signo}${(valor * 100).toFixed(1)}%`;
}


// ══════════════════════════════════════════════════════════════
// COMPONENTE TARJETA METRICA
// ══════════════════════════════════════════════════════════════

interface PropsTarjetaMetrica {
  titulo: string;
  valor: string | number;
  subtitulo?: string;
  icono: React.ReactNode;
  colorValor?: string;
  tendencia?: 'up' | 'down' | 'neutral';
}

function TarjetaMetrica({
  titulo,
  valor,
  subtitulo,
  icono,
  colorValor = 'text-texto-principal',
  tendencia,
}: PropsTarjetaMetrica) {
  return (
    <div className="p-4 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10">
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs text-texto-terciario uppercase tracking-wider">
          {titulo}
        </span>
        <div className="p-1.5 rounded-lg bg-futurista-medio/30">{icono}</div>
      </div>
      <div className="flex items-end gap-2">
        <span className={clsx('text-2xl font-mono font-bold', colorValor)}>
          {valor}
        </span>
        {tendencia && tendencia !== 'neutral' && (
          <span
            className={clsx(
              'text-xs mb-1',
              tendencia === 'up' ? 'text-neon-verde' : 'text-neon-rojo'
            )}
          >
            {tendencia === 'up' ? '↑' : '↓'}
          </span>
        )}
      </div>
      {subtitulo && (
        <p className="text-xs text-texto-terciario mt-1">{subtitulo}</p>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE BARRA ROI MERCADO
// ══════════════════════════════════════════════════════════════

interface PropsBarraROIMercado {
  nombre: string;
  roi: number;
  apuestas: number;
  maxROI: number;
}

function BarraROIMercado({ nombre, roi, apuestas, maxROI }: PropsBarraROIMercado) {
  const porcentaje = Math.min(Math.abs(roi) / maxROI, 1) * 100;
  const esPositivo = roi >= 0;

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-texto-secundario">{nombre}</span>
        <div className="flex items-center gap-3">
          <span className="text-xs text-texto-terciario">{apuestas} apuestas</span>
          <span
            className={clsx(
              'font-mono font-semibold',
              esPositivo ? 'text-neon-verde' : 'text-neon-rojo'
            )}
          >
            {formatearPorcentaje(roi)}
          </span>
        </div>
      </div>
      <div className="h-2 rounded-full bg-futurista-medio/30 overflow-hidden">
        <div
          className={clsx(
            'h-full rounded-full transition-all duration-500',
            esPositivo
              ? 'bg-gradient-to-r from-neon-verde/50 to-neon-verde'
              : 'bg-gradient-to-r from-neon-rojo/50 to-neon-rojo'
          )}
          style={{ width: `${porcentaje}%` }}
        />
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE TARJETA MODELO
// ══════════════════════════════════════════════════════════════

interface PropsTarjetaModelo {
  modelo: EstadoModeloFutbol;
}

function TarjetaModelo({ modelo }: PropsTarjetaModelo) {
  const getEstado = () => {
    if (modelo.r2 >= 0.7 && modelo.mae <= 1.5) {
      return { texto: 'Excelente', color: 'text-neon-verde', Icono: CheckCircle };
    }
    if (modelo.r2 >= 0.5 && modelo.mae <= 2) {
      return { texto: 'Bueno', color: 'text-neon-verde/80', Icono: CheckCircle };
    }
    if (modelo.r2 >= 0.3) {
      return { texto: 'Aceptable', color: 'text-neon-amarillo', Icono: AlertTriangle };
    }
    return { texto: 'Degradado', color: 'text-neon-rojo', Icono: XCircle };
  };

  const { texto, color, Icono } = getEstado();

  return (
    <div className="p-4 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Cpu size={18} className="text-neon-cyan" />
          <span className="font-semibold text-texto-principal">
            {modelo.tipoModelo}
          </span>
        </div>
        <div className={clsx('flex items-center gap-1', color)}>
          <Icono size={14} />
          <span className="text-xs uppercase">{texto}</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div className="text-center p-2 rounded bg-futurista-negro/30">
          <div className="text-xs text-texto-terciario">MAE</div>
          <div className="font-mono font-semibold text-neon-cyan">
            {modelo.mae.toFixed(3)}
          </div>
        </div>
        <div className="text-center p-2 rounded bg-futurista-negro/30">
          <div className="text-xs text-texto-terciario">RMSE</div>
          <div className="font-mono font-semibold text-neon-magenta">
            {modelo.rmse.toFixed(3)}
          </div>
        </div>
        <div className="text-center p-2 rounded bg-futurista-negro/30">
          <div className="text-xs text-texto-terciario">R2</div>
          <div
            className={clsx(
              'font-mono font-semibold',
              modelo.r2 >= 0.5 ? 'text-neon-verde' : 'text-neon-amarillo'
            )}
          >
            {modelo.r2.toFixed(3)}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-texto-terciario">
        <div className="flex items-center gap-1">
          <Database size={12} />
          <span>{modelo.nPartidosEntrenamiento.toLocaleString()} partidos</span>
        </div>
        <div className="flex items-center gap-1">
          <Calendar size={12} />
          <span>{formatearFecha(modelo.fechaEntrenamiento)}</span>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Dashboard de metricas del modulo de futbol
 */
export function DashboardFutbol() {
  // Estados
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [calibracion, setCalibracion] = useState<MetricasCalibracionFutbol[]>([]);
  const [rendimiento, setRendimiento] = useState<MetricasRendimientoFutbol[]>([]);
  const [modelos, setModelos] = useState<EstadoModeloFutbol[]>([]);
  const [saludBackend, setSaludBackend] = useState<SaludBackend | null>(null);
  const [observabilidadHTTP, setObservabilidadHTTP] = useState<ObservabilidadHTTPResumen | null>(null);
  const [datosTemporales, setDatosTemporales] = useState<PuntoROITemporalFutbol[]>([]);

  // Cargar datos
  const cargarDatos = useCallback(async (forceRefresh = false) => {
    setCargando(true);
    setError(null);

    try {
      const [calibracionData, rendimientoData, modelosData, saludData, observabilidadData, roiTemporal] = await Promise.all([
        obtenerMetricasCalibracion(),
        obtenerMetricasRendimiento(),
        obtenerEstadoModelos(),
        obtenerSaludBackend(forceRefresh),
        obtenerObservabilidadHTTP(undefined, forceRefresh),
        obtenerRoiTemporal(30),
      ]);

      setCalibracion(calibracionData);
      setRendimiento(rendimientoData);
      setModelos(modelosData);
      setSaludBackend(saludData);
      setObservabilidadHTTP(observabilidadData);
      setDatosTemporales(roiTemporal);
    } catch (err) {
      const mensaje =
        err instanceof Error ? err.message : 'Error al cargar metricas';
      setError(mensaje);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargarDatos();
  }, [cargarDatos]);

  // Calcular metricas globales
  const metricasGlobales = useMemo(() => {
    const totalApuestas = rendimiento.reduce((acc, r) => acc + r.nApuestas, 0);
    const totalGanadas = rendimiento.reduce((acc, r) => acc + r.ganadas, 0);
    const stakeTotal = rendimiento.reduce((acc, r) => acc + r.stakeTotal, 0);
    const gananciaNeta = rendimiento.reduce((acc, r) => acc + r.gananciaNeta, 0);
    const roi = stakeTotal > 0 ? gananciaNeta / stakeTotal : 0;

    const brierPromedio =
      calibracion.length > 0
        ? calibracion.reduce((acc, c) => acc + c.brierScore, 0) / calibracion.length
        : 0;
    const ecePromedio =
      calibracion.length > 0
        ? calibracion.reduce((acc, c) => acc + c.ece, 0) / calibracion.length
        : 0;
    const calibradoresActivos = calibracion.filter((c) => c.calibradorActivo).length;

    return {
      totalApuestas,
      totalGanadas,
      roi,
      winRate: totalApuestas > 0 ? totalGanadas / totalApuestas : 0,
      gananciaNeta,
      brierPromedio,
      ecePromedio,
      calibradoresActivos,
      totalCalibradores: calibracion.length,
    };
  }, [calibracion, rendimiento]);

  // Agrupar rendimiento por categoria
  const rendimientoPorCategoria = useMemo(() => {
    const categorias: CategoriaMercado[] = ['corners', 'goles', 'disparos'];
    const labels: Record<CategoriaMercado, string> = {
      corners: 'Corners',
      goles: 'Goles',
      disparos: 'Disparos',
    };

    return categorias.map((cat) => {
      const mercados = rendimiento.filter((r) =>
        r.mercado.toLowerCase().startsWith(cat.toUpperCase())
      );
      const apuestas = mercados.reduce((acc, m) => acc + m.nApuestas, 0);
      const stake = mercados.reduce((acc, m) => acc + m.stakeTotal, 0);
      const ganancia = mercados.reduce((acc, m) => acc + m.gananciaNeta, 0);
      const roi = stake > 0 ? ganancia / stake : 0;

      return {
        categoria: cat,
        nombre: labels[cat],
        roi,
        apuestas,
      };
    });
  }, [rendimiento]);

  const maxROI = Math.max(
    ...rendimientoPorCategoria.map((r) => Math.abs(r.roi)),
    0.1
  );

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => navegar('/futbol')}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg
                         border border-neon-cyan/30 bg-futurista-oscuro/50
                         text-neon-cyan hover:bg-neon-cyan/10 hover:border-neon-cyan/50
                         transition-all duration-200 text-sm font-medium"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="hidden sm:inline">Futbol</span>
            </button>

            <div>
              <h1 className="text-2xl font-futurista font-bold text-texto-principal tracking-wider flex items-center gap-3">
                <BarChart3 className="w-6 h-6 text-neon-cyan" />
                DASHBOARD
              </h1>
              <p className="text-sm text-texto-secundario">
                Metricas y rendimiento del sistema
              </p>
            </div>
          </div>

          <Boton
            variante="secundario"
            iconoInicio={<RefreshCw size={16} />}
            onClick={() => void cargarDatos(true)}
            cargando={cargando}
          >
            Actualizar
          </Boton>
        </div>

        {/* Error */}
        {error && (
          <MensajeError
            titulo="Error al cargar metricas"
            mensaje={error}
            onCerrar={() => void cargarDatos(true)}
          />
        )}

        {/* Loading */}
        {cargando && (
          <div className="flex items-center justify-center py-12">
            <Spinner tamano="lg" texto="Cargando metricas..." centrado />
          </div>
        )}

        {/* Contenido principal */}
        {!cargando && !error && (
          <>
            {/* Metricas principales */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <TarjetaMetrica
                titulo="ROI Global"
                valor={formatearPorcentaje(metricasGlobales.roi)}
                subtitulo={`${metricasGlobales.totalApuestas} apuestas`}
                icono={<TrendingUp size={18} className="text-neon-cyan" />}
                colorValor={
                  metricasGlobales.roi >= 0 ? 'text-neon-verde' : 'text-neon-rojo'
                }
                tendencia={metricasGlobales.roi >= 0 ? 'up' : 'down'}
              />
              <TarjetaMetrica
                titulo="Win Rate"
                valor={formatearPorcentaje(metricasGlobales.winRate)}
                subtitulo={`${metricasGlobales.totalGanadas} ganadas`}
                icono={<Target size={18} className="text-neon-magenta" />}
                colorValor={
                  metricasGlobales.winRate >= 0.5
                    ? 'text-neon-verde'
                    : 'text-neon-amarillo'
                }
              />
              <TarjetaMetrica
                titulo="Brier Score"
                valor={metricasGlobales.brierPromedio.toFixed(4)}
                subtitulo="Menor es mejor"
                icono={<Activity size={18} className="text-neon-verde" />}
                colorValor={
                  metricasGlobales.brierPromedio <= 0.15
                    ? 'text-neon-verde'
                    : 'text-neon-amarillo'
                }
              />
              <TarjetaMetrica
                titulo="ECE"
                valor={`${(metricasGlobales.ecePromedio * 100).toFixed(2)}%`}
                subtitulo={`${metricasGlobales.calibradoresActivos}/${metricasGlobales.totalCalibradores} calibradores`}
                icono={<Percent size={18} className="text-neon-amarillo" />}
                colorValor={
                  metricasGlobales.ecePromedio <= 0.05
                    ? 'text-neon-verde'
                    : 'text-neon-amarillo'
                }
              />
            </div>

            {/* Observabilidad operativa (A5) */}
            {saludBackend && observabilidadHTTP && (
              <Tarjeta className="space-y-4">
                <div className="flex items-center gap-3">
                  <Activity size={20} className="text-neon-cyan" />
                  <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-texto-principal">
                    Salud y Observabilidad HTTP
                  </h3>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <TarjetaMetrica
                    titulo="Estado API"
                    valor={saludBackend.estado.toUpperCase()}
                    subtitulo={saludBackend.servicios.modelo}
                    icono={<CheckCircle size={18} className="text-neon-cyan" />}
                    colorValor={
                      saludBackend.estado === 'saludable'
                        ? 'text-neon-verde'
                        : 'text-neon-amarillo'
                    }
                  />
                  <TarjetaMetrica
                    titulo="HTTP p95"
                    valor={`${(observabilidadHTTP.http.latency_p95_ms ?? 0).toFixed(2)} ms`}
                    subtitulo={`req: ${observabilidadHTTP.http.requests_total}`}
                    icono={<TrendingUp size={18} className="text-neon-magenta" />}
                    colorValor={
                      (observabilidadHTTP.http.latency_p95_ms ?? 0) <=
                      observabilidadHTTP.umbrales.latency_p95_ms
                        ? 'text-neon-verde'
                        : 'text-neon-rojo'
                    }
                  />
                  <TarjetaMetrica
                    titulo="Error rate 5xx"
                    valor={`${(observabilidadHTTP.http.error_rate * 100).toFixed(2)}%`}
                    subtitulo={`5xx: ${observabilidadHTTP.http.errors_5xx}`}
                    icono={<AlertTriangle size={18} className="text-neon-amarillo" />}
                    colorValor={
                      observabilidadHTTP.http.error_rate <= observabilidadHTTP.umbrales.error_rate
                        ? 'text-neon-verde'
                        : 'text-neon-rojo'
                    }
                  />
                  <TarjetaMetrica
                    titulo="Alertas"
                    valor={observabilidadHTTP.alertas.length}
                    subtitulo={`uptime: ${Math.round(observabilidadHTTP.uptime.segundos)} s`}
                    icono={<Database size={18} className="text-neon-cyan" />}
                    colorValor={
                      observabilidadHTTP.alertas.length === 0
                        ? 'text-neon-verde'
                        : 'text-neon-amarillo'
                    }
                  />
                </div>

                {observabilidadHTTP.alertas.length > 0 && (
                  <div className="rounded-lg border border-neon-amarillo/40 bg-neon-amarillo/10 p-3">
                    <ul className="space-y-1 text-xs text-neon-amarillo">
                      {observabilidadHTTP.alertas.map((alerta) => (
                        <li key={alerta}>• {alerta}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </Tarjeta>
            )}

            {/* ROI por mercado */}
            <Tarjeta className="space-y-4">
              <div className="flex items-center gap-3">
                <Award size={20} className="text-neon-amarillo" />
                <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-texto-principal">
                  ROI por Categoria
                </h3>
              </div>

              <div className="space-y-4">
                {rendimientoPorCategoria.map((cat) => (
                  <BarraROIMercado
                    key={cat.categoria}
                    nombre={cat.nombre}
                    roi={cat.roi}
                    apuestas={cat.apuestas}
                    maxROI={maxROI}
                  />
                ))}
              </div>
            </Tarjeta>

            {/* Seccion de calibracion */}
            <Tarjeta className="space-y-4">
              <div className="flex items-center gap-3">
                <Activity size={20} className="text-neon-magenta" />
                <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-texto-principal">
                  Calibracion del Sistema
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10">
                  <div className="flex items-center gap-2 mb-2">
                    <Target size={16} className="text-neon-cyan" />
                    <span className="text-xs text-texto-terciario uppercase tracking-wider">
                      Brier Score
                    </span>
                  </div>
                  <p
                    className={clsx(
                      'text-3xl font-mono font-bold',
                      metricasGlobales.brierPromedio <= 0.1
                        ? 'text-neon-verde'
                        : metricasGlobales.brierPromedio <= 0.15
                        ? 'text-neon-verde/80'
                        : 'text-neon-amarillo'
                    )}
                  >
                    {metricasGlobales.brierPromedio.toFixed(4)}
                  </p>
                  <p className="text-xs text-texto-terciario mt-1">
                    Menor es mejor (0.0 - 1.0)
                  </p>
                </div>

                <div className="p-4 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10">
                  <div className="flex items-center gap-2 mb-2">
                    <Percent size={16} className="text-neon-magenta" />
                    <span className="text-xs text-texto-terciario uppercase tracking-wider">
                      ECE
                    </span>
                  </div>
                  <p
                    className={clsx(
                      'text-3xl font-mono font-bold',
                      metricasGlobales.ecePromedio <= 0.03
                        ? 'text-neon-verde'
                        : metricasGlobales.ecePromedio <= 0.05
                        ? 'text-neon-verde/80'
                        : 'text-neon-amarillo'
                    )}
                  >
                    {(metricasGlobales.ecePromedio * 100).toFixed(2)}%
                  </p>
                  <p className="text-xs text-texto-terciario mt-1">
                    Error de calibracion esperado
                  </p>
                </div>

                <div className="p-4 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle size={16} className="text-neon-verde" />
                    <span className="text-xs text-texto-terciario uppercase tracking-wider">
                      Calibradores
                    </span>
                  </div>
                  <p className="text-3xl font-mono font-bold text-neon-verde">
                    {metricasGlobales.calibradoresActivos}
                    <span className="text-lg text-texto-terciario">
                      /{metricasGlobales.totalCalibradores}
                    </span>
                  </p>
                  <p className="text-xs text-texto-terciario mt-1">
                    Calibradores activos
                  </p>
                </div>
              </div>
            </Tarjeta>

            {/* Estado de modelos */}
            <Tarjeta className="space-y-4">
              <div className="flex items-center gap-3">
                <Cpu size={20} className="text-neon-cyan" />
                <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-texto-principal">
                  Estado de Modelos
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {modelos.map((modelo) => (
                  <TarjetaModelo key={modelo.tipoModelo} modelo={modelo} />
                ))}
              </div>
            </Tarjeta>

            {/* Grafico temporal */}
            {datosTemporales.length > 0 && (
              <Suspense
                fallback={(
                  <Tarjeta className="min-h-[220px] flex items-center justify-center">
                    <Spinner tamano="md" texto="Cargando gráfico ROI..." centrado />
                  </Tarjeta>
                )}
              >
                <GraficoRoiTemporalFutbol datos={datosTemporales} />
              </Suspense>
            )}

            {/* Resumen completo con componente existente */}
            {(calibracion.length > 0 || rendimiento.length > 0 || modelos.length > 0) && (
              <ResumenMetricasFutbol
                metricas={{
                  calibracion,
                  rendimiento,
                  modelos,
                }}
                compacto
              />
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-neon-cyan/10 bg-futurista-negro/80 backdrop-blur-sm">
        <div className="contenedor py-4">
          <p className="text-texto-terciario text-xs text-center uppercase tracking-wider">
            Dashboard de Futbol — Metricas de Calibracion y Rendimiento
          </p>
        </div>
      </footer>
    </div>
  );
}
