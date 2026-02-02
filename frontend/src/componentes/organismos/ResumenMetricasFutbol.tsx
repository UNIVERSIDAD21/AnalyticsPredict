/**
 * ResumenMetricasFutbol.tsx — Dashboard de métricas del módulo de fútbol
 *
 * Muestra métricas de calibración, rendimiento por mercado y estado de modelos.
 * Diseño futurista glassmorphism con barras de progreso y gauges.
 */

import { useMemo } from 'react';
import { clsx } from 'clsx';
import {
  BarChart3,
  Target,
  TrendingUp,
  TrendingDown,
  Activity,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Cpu,
  Calendar,
  Database,
  Percent,
  Award,
  AlertCircle,
} from 'lucide-react';
import { Tarjeta } from '../atomos';
import {
  MetricasCalibracionFutbol,
  MetricasRendimientoFutbol,
  EstadoModeloFutbol,
  CategoriaMercado,
  TipoMercadoFutbol,
  ETIQUETAS_MERCADOS,
} from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsResumenMetricasFutbol {
  /** Métricas agrupadas */
  metricas: {
    calibracion: MetricasCalibracionFutbol[];
    rendimiento: MetricasRendimientoFutbol[];
    modelos: EstadoModeloFutbol[];
  };
  /** Mostrar en modo compacto */
  compacto?: boolean;
  /** Clase CSS adicional */
  className?: string;
}

interface MetricaAgrupada {
  categoria: CategoriaMercado;
  label: string;
  calibracion: MetricasCalibracionFutbol[];
  rendimiento: MetricasRendimientoFutbol[];
  modelo?: EstadoModeloFutbol;
}

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

/**
 * Obtiene la categoría de un mercado
 */
function getCategoriaMercado(mercado: TipoMercadoFutbol): CategoriaMercado {
  if (mercado.startsWith('CORNERS')) return 'corners';
  if (mercado.startsWith('GOLES')) return 'goles';
  if (mercado.startsWith('DISPAROS')) return 'disparos';
  return 'corners';
}

/**
 * Obtiene el color basado en el Brier Score
 */
function getColorBrier(brier: number): string {
  if (brier <= 0.1) return 'text-neon-verde';
  if (brier <= 0.15) return 'text-neon-verde/80';
  if (brier <= 0.2) return 'text-neon-amarillo';
  if (brier <= 0.25) return 'text-neon-rojo/70';
  return 'text-neon-rojo';
}

/**
 * Obtiene el color basado en el ECE
 */
function getColorECE(ece: number): string {
  if (ece <= 0.03) return 'text-neon-verde';
  if (ece <= 0.05) return 'text-neon-verde/80';
  if (ece <= 0.08) return 'text-neon-amarillo';
  if (ece <= 0.1) return 'text-neon-rojo/70';
  return 'text-neon-rojo';
}

/**
 * Obtiene el color basado en el ROI
 */
function getColorROI(roi: number): string {
  if (roi >= 0.1) return 'text-neon-verde texto-glow-verde';
  if (roi >= 0.05) return 'text-neon-verde';
  if (roi >= 0) return 'text-neon-verde/70';
  if (roi >= -0.05) return 'text-neon-rojo/70';
  return 'text-neon-rojo';
}

/**
 * Obtiene el color basado en Win Rate
 */
function getColorWinRate(winRate: number): string {
  if (winRate >= 0.6) return 'text-neon-verde';
  if (winRate >= 0.55) return 'text-neon-verde/80';
  if (winRate >= 0.5) return 'text-neon-amarillo';
  if (winRate >= 0.45) return 'text-neon-rojo/70';
  return 'text-neon-rojo';
}

/**
 * Formatea fecha ISO
 */
function formatearFecha(fechaISO: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

/**
 * Obtiene el estado de salud del modelo
 */
function getEstadoSalud(modelo: EstadoModeloFutbol): {
  estado: 'excelente' | 'bueno' | 'aceptable' | 'degradado';
  color: string;
  icono: typeof CheckCircle;
} {
  if (modelo.r2 >= 0.7 && modelo.mae <= 1.5) {
    return { estado: 'excelente', color: 'text-neon-verde', icono: CheckCircle };
  }
  if (modelo.r2 >= 0.5 && modelo.mae <= 2) {
    return { estado: 'bueno', color: 'text-neon-verde/80', icono: CheckCircle };
  }
  if (modelo.r2 >= 0.3 && modelo.mae <= 2.5) {
    return { estado: 'aceptable', color: 'text-neon-amarillo', icono: AlertTriangle };
  }
  return { estado: 'degradado', color: 'text-neon-rojo', icono: XCircle };
}

// ══════════════════════════════════════════════════════════════
// SUB-COMPONENTES
// ══════════════════════════════════════════════════════════════

/**
 * Barra de progreso con gradiente
 */
function BarraProgreso({
  valor,
  max = 1,
  colorInicio = 'from-neon-cyan',
  colorFin = 'to-neon-cyan/50',
  invertido = false,
  className,
}: {
  valor: number;
  max?: number;
  colorInicio?: string;
  colorFin?: string;
  invertido?: boolean;
  className?: string;
}) {
  const porcentaje = Math.min((valor / max) * 100, 100);
  const porcentajeVisual = invertido ? 100 - porcentaje : porcentaje;

  return (
    <div className={clsx('h-2 rounded-full bg-futurista-medio/30 overflow-hidden', className)}>
      <div
        className={clsx(
          'h-full rounded-full transition-all duration-500',
          'bg-gradient-to-r',
          colorInicio,
          colorFin
        )}
        style={{ width: `${porcentajeVisual}%` }}
      />
    </div>
  );
}

/**
 * Gauge circular para métricas
 */
function GaugeCircular({
  valor,
  max = 1,
  label,
  unidad = '%',
  colorPositivo = 'stroke-neon-verde',
  colorNegativo = 'stroke-neon-rojo',
  invertido = false,
  size = 80,
}: {
  valor: number;
  max?: number;
  label: string;
  unidad?: string;
  colorPositivo?: string;
  colorNegativo?: string;
  invertido?: boolean;
  size?: number;
}) {
  const porcentaje = Math.min(Math.abs(valor) / max, 1);
  const esPositivo = invertido ? valor <= 0 : valor >= 0;
  const circumference = 2 * Math.PI * 35;
  const strokeDashoffset = circumference * (1 - porcentaje);
  const valorDisplay = unidad === '%' ? (valor * 100).toFixed(1) : valor.toFixed(2);

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox="0 0 80 80" className="transform -rotate-90">
        {/* Fondo */}
        <circle
          cx="40"
          cy="40"
          r="35"
          fill="none"
          strokeWidth="6"
          className="stroke-futurista-medio/30"
        />
        {/* Progreso */}
        <circle
          cx="40"
          cy="40"
          r="35"
          fill="none"
          strokeWidth="6"
          strokeLinecap="round"
          className={clsx(
            'transition-all duration-500',
            esPositivo ? colorPositivo : colorNegativo
          )}
          style={{
            strokeDasharray: circumference,
            strokeDashoffset: strokeDashoffset,
          }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center" style={{ width: size, height: size }}>
        <span className={clsx('text-lg font-mono font-bold', esPositivo ? 'text-neon-verde' : 'text-neon-rojo')}>
          {valorDisplay}{unidad}
        </span>
      </div>
      <span className="text-xs text-texto-terciario mt-1">{label}</span>
    </div>
  );
}

/**
 * Tarjeta de estado del modelo
 */
function TarjetaEstadoModelo({ modelo }: { modelo: EstadoModeloFutbol }) {
  const { estado, color, icono: Icono } = getEstadoSalud(modelo);

  return (
    <div
      className={clsx(
        'p-4 rounded-lg border transition-all duration-300',
        'bg-futurista-oscuro/50 backdrop-blur-sm',
        'border-neon-cyan/10 hover:border-neon-cyan/20'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Cpu size={18} className="text-neon-cyan" />
          <span className="font-semibold text-texto-principal">{modelo.tipoModelo}</span>
        </div>
        <div className={clsx('flex items-center gap-1', color)}>
          <Icono size={16} />
          <span className="text-xs uppercase">{estado}</span>
        </div>
      </div>

      {/* Métricas del modelo */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="text-center p-2 rounded bg-futurista-negro/30">
          <div className="text-xs text-texto-terciario">MAE</div>
          <div className="font-mono font-semibold text-neon-cyan">{modelo.mae.toFixed(3)}</div>
        </div>
        <div className="text-center p-2 rounded bg-futurista-negro/30">
          <div className="text-xs text-texto-terciario">RMSE</div>
          <div className="font-mono font-semibold text-neon-magenta">{modelo.rmse.toFixed(3)}</div>
        </div>
        <div className="text-center p-2 rounded bg-futurista-negro/30">
          <div className="text-xs text-texto-terciario">R²</div>
          <div className={clsx('font-mono font-semibold', modelo.r2 >= 0.5 ? 'text-neon-verde' : 'text-neon-amarillo')}>
            {modelo.r2.toFixed(3)}
          </div>
        </div>
      </div>

      {/* Info adicional */}
      <div className="flex items-center justify-between text-xs text-texto-terciario">
        <div className="flex items-center gap-1">
          <Database size={12} />
          <span>{modelo.nPartidosEntrenamiento.toLocaleString()} partidos</span>
        </div>
        <div className="flex items-center gap-1">
          <Calendar size={12} />
          <span>v{modelo.version}</span>
        </div>
      </div>
    </div>
  );
}

/**
 * Tarjeta de calibración por mercado
 */
function TarjetaCalibracion({ calibracion }: { calibracion: MetricasCalibracionFutbol }) {
  const etiqueta = ETIQUETAS_MERCADOS[calibracion.mercado];

  return (
    <div className="p-3 rounded-lg bg-futurista-oscuro/30 border border-futurista-medio/30">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-texto-secundario truncate max-w-[150px]">{etiqueta}</span>
        <div className="flex items-center gap-1">
          {calibracion.calibradorActivo ? (
            <CheckCircle size={14} className="text-neon-verde" />
          ) : (
            <AlertCircle size={14} className="text-neon-rojo/70" />
          )}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <div className="text-xs text-texto-terciario">Brier</div>
          <div className={clsx('font-mono font-semibold', getColorBrier(calibracion.brierScore))}>
            {calibracion.brierScore.toFixed(4)}
          </div>
        </div>
        <div>
          <div className="text-xs text-texto-terciario">ECE</div>
          <div className={clsx('font-mono font-semibold', getColorECE(calibracion.ece))}>
            {(calibracion.ece * 100).toFixed(2)}%
          </div>
        </div>
      </div>
      {calibracion.mejoraBrier !== undefined && calibracion.mejoraBrier > 0 && (
        <div className="mt-2 text-xs text-neon-verde">
          +{(calibracion.mejoraBrier * 100).toFixed(1)}% mejora
        </div>
      )}
    </div>
  );
}

/**
 * Tarjeta de rendimiento por mercado
 */
function TarjetaRendimiento({ rendimiento }: { rendimiento: MetricasRendimientoFutbol }) {
  const etiqueta = ETIQUETAS_MERCADOS[rendimiento.mercado];
  const tieneApuestas = rendimiento.nApuestas > 0;

  return (
    <div className="p-3 rounded-lg bg-futurista-oscuro/30 border border-futurista-medio/30">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-texto-secundario truncate max-w-[150px]">{etiqueta}</span>
        <span className="text-xs text-texto-terciario">{rendimiento.nApuestas} apuestas</span>
      </div>
      {tieneApuestas ? (
        <div className="grid grid-cols-2 gap-2">
          <div>
            <div className="text-xs text-texto-terciario">ROI</div>
            <div className={clsx('font-mono font-semibold', getColorROI(rendimiento.roi))}>
              {rendimiento.roi >= 0 ? '+' : ''}{(rendimiento.roi * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-xs text-texto-terciario">Win Rate</div>
            <div className={clsx('font-mono font-semibold', getColorWinRate(rendimiento.winRate))}>
              {(rendimiento.winRate * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      ) : (
        <div className="text-xs text-texto-terciario text-center py-2">Sin datos</div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Dashboard de métricas del módulo de fútbol
 */
export function ResumenMetricasFutbol({
  metricas,
  compacto = false,
  className,
}: PropsResumenMetricasFutbol) {
  // Agrupar métricas por categoría
  const metricasAgrupadas = useMemo<MetricaAgrupada[]>(() => {
    const categorias: CategoriaMercado[] = ['corners', 'goles', 'disparos'];
    const labels: Record<CategoriaMercado, string> = {
      corners: 'Corners',
      goles: 'Goles',
      disparos: 'Disparos',
    };

    return categorias.map((cat) => ({
      categoria: cat,
      label: labels[cat],
      calibracion: metricas.calibracion.filter(
        (c) => getCategoriaMercado(c.mercado) === cat
      ),
      rendimiento: metricas.rendimiento.filter(
        (r) => getCategoriaMercado(r.mercado) === cat
      ),
      modelo: metricas.modelos.find(
        (m) => m.tipoModelo.toLowerCase() === cat
      ),
    }));
  }, [metricas]);

  // Calcular métricas globales
  const metricasGlobales = useMemo(() => {
    const totalApuestas = metricas.rendimiento.reduce((acc, r) => acc + r.nApuestas, 0);
    const totalGanadas = metricas.rendimiento.reduce((acc, r) => acc + r.ganadas, 0);
    const totalPerdidas = metricas.rendimiento.reduce((acc, r) => acc + r.perdidas, 0);
    const stakeTotal = metricas.rendimiento.reduce((acc, r) => acc + r.stakeTotal, 0);
    const gananciaNeta = metricas.rendimiento.reduce((acc, r) => acc + r.gananciaNeta, 0);

    const brierPromedio = metricas.calibracion.length > 0
      ? metricas.calibracion.reduce((acc, c) => acc + c.brierScore, 0) / metricas.calibracion.length
      : 0;
    const ecePromedio = metricas.calibracion.length > 0
      ? metricas.calibracion.reduce((acc, c) => acc + c.ece, 0) / metricas.calibracion.length
      : 0;

    return {
      totalApuestas,
      totalGanadas,
      totalPerdidas,
      winRate: totalApuestas > 0 ? totalGanadas / totalApuestas : 0,
      roi: stakeTotal > 0 ? gananciaNeta / stakeTotal : 0,
      stakeTotal,
      gananciaNeta,
      brierPromedio,
      ecePromedio,
      calibradoresActivos: metricas.calibracion.filter((c) => c.calibradorActivo).length,
      calibradoresTotal: metricas.calibracion.length,
    };
  }, [metricas]);

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Resumen global */}
      <Tarjeta className="relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-neon-cyan via-neon-magenta to-neon-cyan" />

        <h2 className="text-lg font-futurista font-bold text-texto-principal mb-4 flex items-center gap-2">
          <BarChart3 size={20} className="text-neon-cyan" />
          Resumen de Rendimiento
        </h2>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* ROI Global */}
          <div className="text-center p-4 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10">
            <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
              <TrendingUp size={14} />
              <span className="text-xs uppercase tracking-wider">ROI Global</span>
            </div>
            <div className={clsx('text-3xl font-mono font-bold', getColorROI(metricasGlobales.roi))}>
              {metricasGlobales.roi >= 0 ? '+' : ''}{(metricasGlobales.roi * 100).toFixed(1)}%
            </div>
            <BarraProgreso
              valor={Math.abs(metricasGlobales.roi)}
              max={0.3}
              colorInicio={metricasGlobales.roi >= 0 ? 'from-neon-verde' : 'from-neon-rojo'}
              colorFin={metricasGlobales.roi >= 0 ? 'to-neon-verde/50' : 'to-neon-rojo/50'}
              className="mt-2"
            />
          </div>

          {/* Win Rate */}
          <div className="text-center p-4 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10">
            <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
              <Target size={14} />
              <span className="text-xs uppercase tracking-wider">Win Rate</span>
            </div>
            <div className={clsx('text-3xl font-mono font-bold', getColorWinRate(metricasGlobales.winRate))}>
              {(metricasGlobales.winRate * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-texto-terciario mt-1">
              {metricasGlobales.totalGanadas}W / {metricasGlobales.totalPerdidas}L
            </div>
          </div>

          {/* Brier Score promedio */}
          <div className="text-center p-4 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10">
            <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
              <Activity size={14} />
              <span className="text-xs uppercase tracking-wider">Brier Score</span>
            </div>
            <div className={clsx('text-3xl font-mono font-bold', getColorBrier(metricasGlobales.brierPromedio))}>
              {metricasGlobales.brierPromedio.toFixed(4)}
            </div>
            <div className="text-xs text-texto-terciario mt-1">Promedio global</div>
          </div>

          {/* ECE promedio */}
          <div className="text-center p-4 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10">
            <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
              <Percent size={14} />
              <span className="text-xs uppercase tracking-wider">ECE</span>
            </div>
            <div className={clsx('text-3xl font-mono font-bold', getColorECE(metricasGlobales.ecePromedio))}>
              {(metricasGlobales.ecePromedio * 100).toFixed(2)}%
            </div>
            <div className="text-xs text-texto-terciario mt-1">
              {metricasGlobales.calibradoresActivos}/{metricasGlobales.calibradoresTotal} activos
            </div>
          </div>
        </div>
      </Tarjeta>

      {/* Estado de modelos */}
      {!compacto && metricas.modelos.length > 0 && (
        <Tarjeta>
          <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-neon-cyan mb-4 flex items-center gap-2">
            <span className="w-8 h-px bg-gradient-to-r from-neon-cyan to-transparent" />
            Estado de Modelos
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {metricas.modelos.map((modelo) => (
              <TarjetaEstadoModelo key={modelo.tipoModelo} modelo={modelo} />
            ))}
          </div>
        </Tarjeta>
      )}

      {/* Métricas por categoría */}
      {!compacto && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Calibración */}
          <Tarjeta>
            <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-neon-magenta mb-4 flex items-center gap-2">
              <span className="w-8 h-px bg-gradient-to-r from-neon-magenta to-transparent" />
              Calibración por Mercado
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[400px] overflow-y-auto">
              {metricas.calibracion.map((cal) => (
                <TarjetaCalibracion key={cal.mercado} calibracion={cal} />
              ))}
            </div>
          </Tarjeta>

          {/* Rendimiento */}
          <Tarjeta>
            <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-neon-verde mb-4 flex items-center gap-2">
              <span className="w-8 h-px bg-gradient-to-r from-neon-verde to-transparent" />
              Rendimiento por Mercado
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[400px] overflow-y-auto">
              {metricas.rendimiento.map((rend) => (
                <TarjetaRendimiento key={rend.mercado} rendimiento={rend} />
              ))}
            </div>
          </Tarjeta>
        </div>
      )}

      {/* ROI por categoría */}
      <Tarjeta>
        <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-neon-amarillo mb-4 flex items-center gap-2">
          <span className="w-8 h-px bg-gradient-to-r from-neon-amarillo to-transparent" />
          <Award size={16} />
          ROI por Categoría
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {metricasAgrupadas.map((grupo) => {
            const roiCategoria = grupo.rendimiento.length > 0
              ? grupo.rendimiento.reduce((acc, r) => acc + r.gananciaNeta, 0) /
                Math.max(grupo.rendimiento.reduce((acc, r) => acc + r.stakeTotal, 0), 1)
              : 0;
            const totalApuestas = grupo.rendimiento.reduce((acc, r) => acc + r.nApuestas, 0);

            return (
              <div
                key={grupo.categoria}
                className="p-4 rounded-lg bg-futurista-oscuro/50 border border-futurista-medio/30"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="font-semibold text-texto-principal">{grupo.label}</span>
                  {grupo.modelo && (
                    <span className="text-xs text-texto-terciario">
                      v{grupo.modelo.version}
                    </span>
                  )}
                </div>
                <div className={clsx('text-2xl font-mono font-bold mb-2', getColorROI(roiCategoria))}>
                  {roiCategoria >= 0 ? '+' : ''}{(roiCategoria * 100).toFixed(1)}%
                </div>
                <BarraProgreso
                  valor={Math.abs(roiCategoria)}
                  max={0.2}
                  colorInicio={roiCategoria >= 0 ? 'from-neon-verde' : 'from-neon-rojo'}
                  colorFin={roiCategoria >= 0 ? 'to-neon-verde/50' : 'to-neon-rojo/50'}
                  className="mb-2"
                />
                <div className="flex items-center justify-between text-xs text-texto-terciario">
                  <span>{totalApuestas} apuestas</span>
                  <span>{grupo.rendimiento.length} mercados</span>
                </div>
              </div>
            );
          })}
        </div>
      </Tarjeta>
    </div>
  );
}
