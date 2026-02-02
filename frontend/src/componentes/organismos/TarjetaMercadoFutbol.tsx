/**
 * TarjetaMercadoFutbol.tsx — Tarjeta detallada de mercado de fútbol
 *
 * Muestra información completa de un mercado con tabla de probabilidades,
 * barras visuales Over/Under y nivel de confianza.
 * Diseño futurista glassmorphism con efectos neón.
 */

import { useState } from 'react';
import { clsx } from 'clsx';
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Info,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Tarjeta } from '../atomos';
import { BadgeConfianza, BarraConfianza } from '../moleculas';
import {
  PrediccionMercadoFutbol,
  ProbabilidadLinea,
  ETIQUETAS_MERCADOS,
  NivelConfianza,
} from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsTarjetaMercadoFutbol {
  /** Datos de la predicción del mercado */
  prediccion: PrediccionMercadoFutbol;
  /** Callback al seleccionar una línea/lado */
  onSeleccionar?: (linea: number, lado: 'OVER' | 'UNDER') => void;
  /** Mostrar vista expandida inicialmente */
  expandidoInicial?: boolean;
  /** Ocultar encabezado (para uso embebido) */
  ocultarEncabezado?: boolean;
  /** Clase CSS adicional */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

/**
 * Obtiene el color del texto basado en la probabilidad
 */
function getColorProbabilidad(probabilidad: number): string {
  if (probabilidad >= 0.7) return 'text-neon-verde';
  if (probabilidad >= 0.6) return 'text-neon-verde/80';
  if (probabilidad >= 0.5) return 'text-texto-principal';
  if (probabilidad >= 0.4) return 'text-texto-secundario';
  return 'text-texto-terciario';
}

/**
 * Obtiene el color del gradiente para la barra
 */
function getGradienteBarra(esOver: boolean, probabilidad: number): string {
  if (esOver) {
    if (probabilidad >= 0.6) return 'from-neon-verde to-neon-verde/60';
    return 'from-neon-verde/60 to-neon-verde/30';
  } else {
    if (probabilidad >= 0.6) return 'from-neon-rojo/60 to-neon-rojo';
    return 'from-neon-rojo/30 to-neon-rojo/60';
  }
}

/**
 * Obtiene descripción del nivel de confianza
 */
function getDescripcionConfianza(nivel: NivelConfianza): string {
  const descripciones: Record<NivelConfianza, string> = {
    MUY_ALTA: 'Datos abundantes y modelo muy estable',
    ALTA: 'Buena cantidad de datos, modelo confiable',
    MEDIA: 'Datos suficientes, variabilidad moderada',
    BAJA: 'Datos limitados, usar con precaución',
    MUY_BAJA: 'Pocos datos, alta incertidumbre',
  };
  return descripciones[nivel];
}

// ══════════════════════════════════════════════════════════════
// SUB-COMPONENTES
// ══════════════════════════════════════════════════════════════

/**
 * Fila de probabilidad con barra visual
 */
function FilaProbabilidad({
  probabilidad,
  onSeleccionar,
  destacada = false,
}: {
  probabilidad: ProbabilidadLinea;
  onSeleccionar?: (linea: number, lado: 'OVER' | 'UNDER') => void;
  destacada?: boolean;
}) {
  const esOverFavorito = probabilidad.overCalibrada > probabilidad.underCalibrada;
  const porcentajeOver = probabilidad.overCalibrada * 100;
  const porcentajeUnder = probabilidad.underCalibrada * 100;

  return (
    <div
      className={clsx(
        'p-3 rounded-lg transition-all duration-300',
        destacada
          ? 'bg-futurista-medio/40 border border-neon-cyan/20'
          : 'bg-futurista-oscuro/30 hover:bg-futurista-medio/20'
      )}
    >
      {/* Línea */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl font-mono font-bold text-neon-cyan">
            {probabilidad.linea.toFixed(1)}
          </span>
          {destacada && (
            <span className="px-2 py-0.5 rounded text-xs bg-neon-cyan/20 text-neon-cyan">
              Principal
            </span>
          )}
        </div>
        {onSeleccionar && (
          <div className="flex gap-2">
            <button
              onClick={() => onSeleccionar(probabilidad.linea, 'OVER')}
              className={clsx(
                'px-3 py-1.5 rounded-lg border text-sm font-semibold',
                'transition-all duration-200',
                esOverFavorito
                  ? 'border-neon-verde/50 bg-neon-verde/10 text-neon-verde hover:bg-neon-verde/20'
                  : 'border-futurista-medio/30 text-texto-secundario hover:border-neon-verde/30 hover:text-neon-verde'
              )}
            >
              <TrendingUp size={14} className="inline mr-1" />
              Over
            </button>
            <button
              onClick={() => onSeleccionar(probabilidad.linea, 'UNDER')}
              className={clsx(
                'px-3 py-1.5 rounded-lg border text-sm font-semibold',
                'transition-all duration-200',
                !esOverFavorito
                  ? 'border-neon-rojo/50 bg-neon-rojo/10 text-neon-rojo hover:bg-neon-rojo/20'
                  : 'border-futurista-medio/30 text-texto-secundario hover:border-neon-rojo/30 hover:text-neon-rojo'
              )}
            >
              <TrendingDown size={14} className="inline mr-1" />
              Under
            </button>
          </div>
        )}
      </div>

      {/* Barra de probabilidad visual */}
      <div className="relative h-8 rounded-lg overflow-hidden bg-futurista-negro/50 border border-futurista-medio/30">
        {/* Lado Over */}
        <div
          className={clsx(
            'absolute left-0 top-0 h-full transition-all duration-500',
            'bg-gradient-to-r',
            getGradienteBarra(true, probabilidad.overCalibrada)
          )}
          style={{ width: `${porcentajeOver}%` }}
        />

        {/* Lado Under */}
        <div
          className={clsx(
            'absolute right-0 top-0 h-full transition-all duration-500',
            'bg-gradient-to-l',
            getGradienteBarra(false, probabilidad.underCalibrada)
          )}
          style={{ width: `${porcentajeUnder}%` }}
        />

        {/* Divisor central */}
        <div
          className="absolute top-0 w-0.5 h-full bg-texto-principal/50 z-10"
          style={{ left: `${porcentajeOver}%`, transform: 'translateX(-50%)' }}
        />

        {/* Labels en la barra */}
        <div className="absolute inset-0 flex items-center justify-between px-3 z-20">
          <span
            className={clsx(
              'font-mono font-bold',
              esOverFavorito ? 'text-neon-verde texto-glow-verde' : 'text-texto-secundario'
            )}
          >
            {porcentajeOver.toFixed(1)}%
          </span>
          <span
            className={clsx(
              'font-mono font-bold',
              !esOverFavorito ? 'text-neon-rojo texto-glow-rojo' : 'text-texto-secundario'
            )}
          >
            {porcentajeUnder.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Probabilidades raw vs calibradas */}
      <div className="mt-2 flex items-center justify-between text-xs text-texto-terciario">
        <span>
          Raw: {(probabilidad.overRaw * 100).toFixed(1)}% / {(probabilidad.underRaw * 100).toFixed(1)}%
        </span>
        <span>
          Calibrada: {porcentajeOver.toFixed(1)}% / {porcentajeUnder.toFixed(1)}%
        </span>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Tarjeta detallada de mercado de fútbol
 */
export function TarjetaMercadoFutbol({
  prediccion,
  onSeleccionar,
  expandidoInicial = true,
  ocultarEncabezado = false,
  className,
}: PropsTarjetaMercadoFutbol) {
  const [expandido, setExpandido] = useState(expandidoInicial);
  const [mostrarInfo, setMostrarInfo] = useState(false);

  const etiquetaMercado = ETIQUETAS_MERCADOS[prediccion.mercado];

  return (
    <Tarjeta className={clsx('relative overflow-hidden', className)}>
      {/* Efecto de brillo superior */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neon-cyan/50 to-transparent" />

      {/* Encabezado */}
      {!ocultarEncabezado && (
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-futurista font-bold text-texto-principal tracking-wider mb-2">
              {etiquetaMercado}
            </h3>
            <div className="flex items-center gap-3">
              <BadgeConfianza nivel={prediccion.confianza} tamano="md" />
              <button
                onClick={() => setMostrarInfo(!mostrarInfo)}
                className="text-texto-terciario hover:text-neon-cyan transition-colors"
              >
                <Info size={16} />
              </button>
            </div>

            {/* Info expandible */}
            {mostrarInfo && (
              <div className="mt-3 p-3 rounded-lg bg-futurista-negro/50 border border-neon-cyan/10 text-sm text-texto-secundario">
                <p>{getDescripcionConfianza(prediccion.confianza)}</p>
              </div>
            )}
          </div>

          {/* Estadísticas principales */}
          <div className="flex gap-4">
            <div className="text-center p-3 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10">
              <div className="text-xs text-texto-terciario uppercase tracking-wider mb-1">
                Media
              </div>
              <div className="text-2xl font-mono font-bold text-neon-cyan texto-glow-cyan">
                {prediccion.media.toFixed(2)}
              </div>
            </div>
            <div className="text-center p-3 rounded-lg bg-futurista-oscuro/50 border border-neon-magenta/10">
              <div className="text-xs text-texto-terciario uppercase tracking-wider mb-1">
                Std
              </div>
              <div className="text-2xl font-mono font-bold text-neon-magenta texto-glow-magenta">
                ±{prediccion.std.toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Barra de confianza visual */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-texto-terciario">Nivel de confianza</span>
        </div>
        <BarraConfianza nivel={prediccion.confianza} />
      </div>

      {/* Botón expandir/colapsar */}
      <button
        onClick={() => setExpandido(!expandido)}
        className={clsx(
          'w-full flex items-center justify-center gap-2 py-2 rounded-lg',
          'text-sm text-texto-secundario',
          'bg-futurista-oscuro/30 hover:bg-futurista-medio/30',
          'border border-futurista-medio/30 hover:border-neon-cyan/20',
          'transition-all duration-200'
        )}
      >
        <BarChart3 size={16} />
        <span>
          {expandido ? 'Ocultar' : 'Mostrar'} tabla de probabilidades
          ({prediccion.probabilidades.length} líneas)
        </span>
        {expandido ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {/* Tabla de probabilidades expandible */}
      {expandido && (
        <div className="mt-4 space-y-3 animate-deslizar-arriba">
          {prediccion.probabilidades.map((prob, idx) => (
            <FilaProbabilidad
              key={prob.linea}
              probabilidad={prob}
              onSeleccionar={onSeleccionar}
              destacada={idx === 0}
            />
          ))}
        </div>
      )}

      {/* Footer con información adicional */}
      <div className="mt-4 pt-4 border-t border-neon-cyan/10 flex items-center justify-between text-xs text-texto-terciario">
        <div className="flex items-center gap-4">
          <span>
            <TrendingUp size={12} className="inline text-neon-verde mr-1" />
            Over favorito: {prediccion.probabilidades.filter(p => p.overCalibrada > 0.5).length} líneas
          </span>
          <span>
            <TrendingDown size={12} className="inline text-neon-rojo mr-1" />
            Under favorito: {prediccion.probabilidades.filter(p => p.underCalibrada > 0.5).length} líneas
          </span>
        </div>
        <span className="text-neon-cyan/70">
          {prediccion.probabilidades.length} líneas disponibles
        </span>
      </div>
    </Tarjeta>
  );
}
