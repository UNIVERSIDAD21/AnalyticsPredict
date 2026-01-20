/**
 * SeccionFormaReciente.tsx — Forma reciente de ambos equipos
 *
 * Muestra la forma reciente de ambos equipos lado a lado: record, racha,
 * PPG, y comparación vs temporada. Incluye contexto de descanso.
 */

import { useState, useMemo } from 'react';
import {
  Flame,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Calendar,
  Clock,
  ChevronRight,
} from 'lucide-react';
import { clsx } from 'clsx';
import { Tarjeta } from '../atomos';
import type { ContextoForma, ContextoDescanso, TendenciaForma } from '../../tipos/analisis';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsSeccionForma {
  /** Forma reciente del equipo principal */
  formaEquipo: ContextoForma;
  /** Forma reciente del rival */
  formaRival: ContextoForma;
  /** Contexto de descanso del equipo principal */
  descansoEquipo: ContextoDescanso;
  /** Contexto de descanso del rival */
  descansoRival: ContextoDescanso;
  /** Nombre del equipo principal */
  equipoNombre: string;
  /** Nombre del rival */
  rivalNombre: string;
  /** ID del equipo principal (opcional, para navegación) */
  equipoId?: string;
  /** ID del rival (opcional, para navegación) */
  rivalId?: string;
  /** Iniciar expandido o colapsado */
  inicialmenteExpandido?: boolean;
  /** Clase CSS adicional */
  className?: string;
  /** Callback cuando el usuario quiere ver estadísticas de un equipo */
  onVerEstadisticas?: (equipoId: string) => void;
}

interface PropsTarjetaFormaEquipo {
  nombre: string;
  forma: ContextoForma;
  descanso: ContextoDescanso;
  /** ID del equipo (opcional, para navegación a estadísticas) */
  equipoId?: string;
  /** Callback cuando el usuario quiere ver estadísticas */
  onVerEstadisticas?: (equipoId: string) => void;
}

// ══════════════════════════════════════════════════════════════
// UTILIDADES
// ══════════════════════════════════════════════════════════════

/**
 * Genera emojis de fuego según la racha
 */
function generarEmojisFuego(racha: string): string {
  // Extraer número de la racha (ej: "W5" -> 5)
  const match = racha.match(/W(\d+)/);
  if (!match) return '';

  const wins = parseInt(match[1], 10);
  if (wins >= 5) return ' 🔥🔥';
  if (wins >= 3) return ' 🔥';
  return '';
}

/**
 * Formatea la racha para mostrar
 */
function formatearRacha(racha: string): string {
  // Convertir "W3" a "3V" (3 victorias), "L2" a "2D" (2 derrotas)
  return racha
    .replace(/W/g, 'V')
    .replace(/L/g, 'D');
}

/**
 * Obtiene el icono de tendencia
 */
function IconoTendencia({ tendencia }: { tendencia: TendenciaForma }) {
  switch (tendencia) {
    case 'MEJORANDO':
      return <TrendingUp className="w-4 h-4 text-neon-verde" />;
    case 'EMPEORANDO':
      return <TrendingDown className="w-4 h-4 text-neon-rojo" />;
    case 'ESTABLE':
    default:
      return <Minus className="w-4 h-4 text-texto-terciario" />;
  }
}

/**
 * Obtiene el color de la tendencia
 */
function obtenerColorTendencia(tendencia: TendenciaForma): string {
  switch (tendencia) {
    case 'MEJORANDO':
      return 'text-neon-verde';
    case 'EMPEORANDO':
      return 'text-neon-rojo';
    case 'ESTABLE':
    default:
      return 'text-texto-secundario';
  }
}

/**
 * Calcula el porcentaje de victorias para la barra
 */
function calcularPorcentajeVictorias(victorias: number, ultimos_n: number): number {
  return (victorias / ultimos_n) * 100;
}

/**
 * Formatea una fecha ISO a formato corto
 */
function formatearFechaCorta(fechaISO: string): string {
  try {
    const fecha = new Date(fechaISO);
    return fecha.toLocaleDateString('es-ES', {
      day: 'numeric',
      month: 'short',
    });
  } catch {
    return fechaISO;
  }
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE TARJETA DE FORMA
// ══════════════════════════════════════════════════════════════

function TarjetaFormaEquipo({ nombre, forma, descanso, equipoId, onVerEstadisticas }: PropsTarjetaFormaEquipo) {
  const porcentajeVictorias = calcularPorcentajeVictorias(
    forma.victorias,
    forma.ultimos_n
  );
  const diferenciaVsTemporada = forma.diferencia_vs_temporada;

  return (
    <div className="p-4 rounded-lg bg-futurista-negro/50 border border-neon-cyan/20 space-y-4">
      {/* Nombre del equipo */}
      <div className="flex items-center gap-2">
        <span className="text-lg">🏀</span>
        <h4 className="font-futurista text-texto-principal tracking-wide truncate">
          {nombre}
        </h4>
      </div>

      {/* Record y racha */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-texto-terciario uppercase tracking-wider mb-1">
            Record
          </p>
          <p className="text-xl font-mono">
            <span className="text-neon-verde">{forma.victorias}</span>
            <span className="text-texto-terciario">-</span>
            <span className="text-neon-rojo">{forma.derrotas}</span>
          </p>
        </div>
        <div>
          <p className="text-xs text-texto-terciario uppercase tracking-wider mb-1">
            Racha
          </p>
          <p className="text-xl font-mono text-texto-principal">
            {formatearRacha(forma.racha)}
            {generarEmojisFuego(forma.racha)}
          </p>
        </div>
      </div>

      {/* PPG y vs temporada */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-texto-secundario">PPG</span>
          <span className="font-mono text-texto-principal">
            {forma.ppg.toFixed(1)}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-texto-secundario">vs temporada</span>
          <span
            className={clsx(
              'font-mono text-sm flex items-center gap-1',
              diferenciaVsTemporada > 0
                ? 'text-neon-verde'
                : diferenciaVsTemporada < 0
                ? 'text-neon-rojo'
                : 'text-texto-terciario'
            )}
          >
            {diferenciaVsTemporada > 0 ? '+' : ''}
            {diferenciaVsTemporada.toFixed(1)}
            {diferenciaVsTemporada > 0 ? (
              <TrendingUp className="w-3 h-3" />
            ) : diferenciaVsTemporada < 0 ? (
              <TrendingDown className="w-3 h-3" />
            ) : null}
          </span>
        </div>
      </div>

      {/* OPP y Net Rating */}
      <div className="grid grid-cols-2 gap-4 pt-2 border-t border-futurista-medio">
        <div>
          <p className="text-xs text-texto-terciario mb-1">OPP PPG</p>
          <p className="font-mono text-texto-principal">{forma.opp_ppg.toFixed(1)}</p>
        </div>
        <div>
          <p className="text-xs text-texto-terciario mb-1">Net Rating</p>
          <p
            className={clsx(
              'font-mono',
              forma.net_rating > 0
                ? 'text-neon-verde'
                : forma.net_rating < 0
                ? 'text-neon-rojo'
                : 'text-texto-principal'
            )}
          >
            {forma.net_rating > 0 ? '+' : ''}
            {forma.net_rating.toFixed(1)}
          </p>
        </div>
      </div>

      {/* Tendencia */}
      <div className="flex items-center justify-between pt-2 border-t border-futurista-medio">
        <span className="text-sm text-texto-secundario">Tendencia</span>
        <div className="flex items-center gap-2">
          <span className={clsx('text-sm', obtenerColorTendencia(forma.tendencia))}>
            {forma.tendencia}
          </span>
          <IconoTendencia tendencia={forma.tendencia} />
        </div>
      </div>

      {/* Barra de victorias */}
      <div className="space-y-1">
        <div className="h-2 bg-futurista-medio rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-neon-verde/70 to-neon-verde rounded-full transition-all duration-500"
            style={{ width: `${porcentajeVictorias}%` }}
            role="progressbar"
            aria-valuenow={forma.victorias}
            aria-valuemin={0}
            aria-valuemax={forma.ultimos_n}
            aria-label={`${forma.victorias} victorias de ${forma.ultimos_n}`}
          />
        </div>
        <p className="text-xs text-texto-terciario text-center">
          {porcentajeVictorias.toFixed(0)}% victorias
        </p>
      </div>

      {/* Indicador B2B si aplica */}
      {descanso.es_back_to_back && (
        <div className="flex items-center gap-2 p-2 rounded bg-advertencia-500/10 border border-advertencia-500/20">
          <AlertTriangle className="w-4 h-4 text-advertencia-500 flex-shrink-0" />
          <span className="text-xs text-advertencia-500 font-medium">
            BACK-TO-BACK
          </span>
        </div>
      )}

      {/* Botón para ver estadísticas completas */}
      {equipoId && onVerEstadisticas && (
        <button
          onClick={() => onVerEstadisticas(equipoId)}
          className="mt-2 w-full py-2 px-4 rounded-lg bg-neon-cyan/10
                     border border-neon-cyan/30 text-neon-cyan
                     hover:bg-neon-cyan/20 hover:border-neon-cyan/50
                     transition-all duration-200 flex items-center
                     justify-center gap-2 text-sm font-medium"
        >
          <span>Ver estadísticas completas</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

export function SeccionFormaReciente({
  formaEquipo,
  formaRival,
  descansoEquipo,
  descansoRival,
  equipoNombre,
  rivalNombre,
  equipoId,
  rivalId,
  inicialmenteExpandido = true,
  className,
  onVerEstadisticas,
}: PropsSeccionForma) {
  const [expandido, setExpandido] = useState(inicialmenteExpandido);

  // Calcular ventaja de descanso
  const ventajaDescanso = useMemo(() => {
    const diferencia = descansoEquipo.dias_descanso - descansoRival.dias_descanso;
    if (diferencia > 0) {
      return { equipo: equipoNombre, dias: diferencia };
    } else if (diferencia < 0) {
      return { equipo: rivalNombre, dias: Math.abs(diferencia) };
    }
    return null;
  }, [descansoEquipo, descansoRival, equipoNombre, rivalNombre]);

  return (
    <Tarjeta className={clsx('space-y-4', className)} padding="md">
      {/* Encabezado colapsable */}
      <button
        onClick={() => setExpandido(!expandido)}
        className="w-full flex items-center justify-between gap-2 group"
        aria-expanded={expandido}
        aria-controls="contenido-forma"
      >
        <div className="flex items-center gap-2">
          <Flame className="w-5 h-5 text-neon-cyan" />
          <h3 className="text-lg font-futurista text-texto-principal tracking-wide">
            Forma Reciente
          </h3>
          <span className="text-sm text-texto-terciario">
            (últimos {formaEquipo.ultimos_n} partidos)
          </span>
        </div>

        {expandido ? (
          <ChevronUp className="w-5 h-5 text-texto-terciario group-hover:text-texto-secundario transition-colors" />
        ) : (
          <ChevronDown className="w-5 h-5 text-texto-terciario group-hover:text-texto-secundario transition-colors" />
        )}
      </button>

      {/* Contenido expandible */}
      {expandido && (
        <div id="contenido-forma" className="space-y-4">
          {/* Grid de tarjetas de equipos */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TarjetaFormaEquipo
              nombre={equipoNombre}
              forma={formaEquipo}
              descanso={descansoEquipo}
              equipoId={equipoId}
              onVerEstadisticas={onVerEstadisticas}
            />
            <TarjetaFormaEquipo
              nombre={rivalNombre}
              forma={formaRival}
              descanso={descansoRival}
              equipoId={rivalId}
              onVerEstadisticas={onVerEstadisticas}
            />
          </div>

          {/* Contexto del partido */}
          <div className="p-4 rounded-lg bg-futurista-medio/30 border border-neon-cyan/10 space-y-3">
            <div className="flex items-center gap-2 mb-3">
              <Calendar className="w-4 h-4 text-neon-cyan" />
              <h4 className="text-sm font-semibold text-texto-principal uppercase tracking-wider">
                Contexto del Partido
              </h4>
            </div>

            {/* Descanso de cada equipo */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {/* Equipo */}
              <div className="flex items-start gap-2">
                <Clock className="w-4 h-4 text-texto-terciario flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-texto-principal font-medium">
                    {equipoNombre}
                  </p>
                  <p className="text-xs text-texto-secundario">
                    {descansoEquipo.es_back_to_back ? (
                      <span className="text-advertencia-500 font-medium">
                        BACK-TO-BACK (jugaron ayer)
                      </span>
                    ) : (
                      <>
                        {descansoEquipo.dias_descanso} días de descanso
                        {descansoEquipo.ultimo_partido && (
                          <span className="text-texto-terciario">
                            {' '}
                            (último:{' '}
                            {formatearFechaCorta(descansoEquipo.ultimo_partido.fecha)})
                          </span>
                        )}
                      </>
                    )}
                  </p>
                </div>
              </div>

              {/* Rival */}
              <div className="flex items-start gap-2">
                <Clock className="w-4 h-4 text-texto-terciario flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-texto-principal font-medium">
                    {rivalNombre}
                  </p>
                  <p className="text-xs text-texto-secundario">
                    {descansoRival.es_back_to_back ? (
                      <span className="text-advertencia-500 font-medium">
                        BACK-TO-BACK (jugaron ayer)
                      </span>
                    ) : (
                      <>
                        {descansoRival.dias_descanso} días de descanso
                        {descansoRival.ultimo_partido && (
                          <span className="text-texto-terciario">
                            {' '}
                            (último:{' '}
                            {formatearFechaCorta(descansoRival.ultimo_partido.fecha)})
                          </span>
                        )}
                      </>
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* Ventaja de descanso */}
            {ventajaDescanso && (
              <div className="pt-3 border-t border-futurista-medio/50">
                <div className="flex items-center gap-2">
                  <div
                    className={clsx(
                      'w-2 h-2 rounded-full',
                      ventajaDescanso.dias >= 2
                        ? 'bg-neon-verde'
                        : 'bg-neon-amarillo'
                    )}
                  />
                  <p className="text-sm">
                    <span className="text-texto-secundario">
                      Ventaja de descanso:
                    </span>{' '}
                    <span className="text-texto-principal font-medium">
                      {ventajaDescanso.equipo}
                    </span>{' '}
                    <span className="text-neon-cyan font-mono">
                      (+{ventajaDescanso.dias} días)
                    </span>
                  </p>
                </div>
              </div>
            )}

            {/* Ambos con mismo descanso */}
            {!ventajaDescanso && (
              <div className="pt-3 border-t border-futurista-medio/50">
                <p className="text-sm text-texto-terciario">
                  Ambos equipos tienen el mismo descanso (
                  {descansoEquipo.dias_descanso} días)
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </Tarjeta>
  );
}
