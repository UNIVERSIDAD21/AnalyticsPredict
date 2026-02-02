/**
 * EstadisticaEquipoMini.tsx — Vista compacta de estadísticas de equipo
 *
 * Muestra estadísticas de equipo en formato compacto para comparaciones.
 */

import { clsx } from 'clsx';
import { Target, CornerUpRight, Crosshair, TrendingUp, TrendingDown } from 'lucide-react';
import { EstadisticasEquipoFutbol } from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsEstadisticaEquipoMini {
  /** Estadísticas del equipo */
  estadisticas: EstadisticasEquipoFutbol;
  /** Nombre del equipo */
  equipo: string;
  /** Logo del equipo (opcional) */
  logoUrl?: string;
  /** Mostrar como local o visitante */
  tipo?: 'local' | 'visitante';
  /** Mostrar estadísticas extendidas */
  extendido?: boolean;
  /** Clase CSS adicional */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

/**
 * Formatea el record del equipo
 */
function formatearRecord(stats: EstadisticasEquipoFutbol): string {
  return `${stats.victorias}V-${stats.empates}E-${stats.derrotas}D`;
}

/**
 * Calcula el porcentaje de victorias
 */
function calcularWinRate(stats: EstadisticasEquipoFutbol): number {
  if (stats.partidosJugados === 0) return 0;
  return (stats.victorias / stats.partidosJugados) * 100;
}

/**
 * Determina si el valor es positivo, negativo o neutro
 */
function getTendencia(favor: number, contra: number): 'positivo' | 'negativo' | 'neutro' {
  const diferencia = favor - contra;
  if (diferencia > 0.5) return 'positivo';
  if (diferencia < -0.5) return 'negativo';
  return 'neutro';
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE STAT MINI
// ══════════════════════════════════════════════════════════════

function StatMini({
  icono: Icono,
  etiqueta,
  valor,
  valorSecundario,
  colorIcono = 'text-neon-cyan',
}: {
  icono: typeof Target;
  etiqueta: string;
  valor: string | number;
  valorSecundario?: string | number;
  colorIcono?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-2 py-1">
      <div className="flex items-center gap-2">
        <Icono size={12} className={colorIcono} />
        <span className="text-xs text-texto-terciario">{etiqueta}</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="text-sm font-mono font-semibold text-texto-principal">{valor}</span>
        {valorSecundario !== undefined && (
          <span className="text-xs text-texto-terciario">({valorSecundario})</span>
        )}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Vista compacta de estadísticas de equipo para comparaciones
 */
export function EstadisticaEquipoMini({
  estadisticas,
  equipo,
  logoUrl,
  tipo,
  extendido = false,
  className,
}: PropsEstadisticaEquipoMini) {
  const winRate = calcularWinRate(estadisticas);
  const golesTendencia = getTendencia(
    estadisticas.promedioGolesFavor,
    estadisticas.promedioGolesContra
  );
  const cornersTendencia = getTendencia(
    estadisticas.promedioCornersFavor,
    estadisticas.promedioCornersContra
  );

  return (
    <div
      className={clsx(
        'p-3 rounded-lg',
        'bg-futurista-oscuro/50 backdrop-blur-sm',
        'border border-neon-cyan/10',
        className
      )}
    >
      {/* Header: Equipo */}
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-neon-cyan/10">
        {logoUrl && (
          <img
            src={logoUrl}
            alt={equipo}
            className="w-6 h-6 object-contain"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        )}
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-texto-principal truncate">{equipo}</h4>
          {tipo && (
            <span className="text-xs text-texto-terciario capitalize">{tipo}</span>
          )}
        </div>
        <div className="text-right">
          <span className="text-xs font-mono text-texto-secundario">
            {formatearRecord(estadisticas)}
          </span>
          <div className="flex items-center gap-1 justify-end">
            {winRate >= 50 ? (
              <TrendingUp size={10} className="text-neon-verde" />
            ) : (
              <TrendingDown size={10} className="text-neon-rojo" />
            )}
            <span
              className={clsx(
                'text-xs font-semibold',
                winRate >= 50 ? 'text-neon-verde' : 'text-neon-rojo'
              )}
            >
              {winRate.toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Estadísticas principales */}
      <div className="space-y-0.5">
        {/* Goles */}
        <StatMini
          icono={Target}
          etiqueta="Goles F/C"
          valor={estadisticas.promedioGolesFavor.toFixed(1)}
          valorSecundario={estadisticas.promedioGolesContra.toFixed(1)}
          colorIcono={
            golesTendencia === 'positivo'
              ? 'text-neon-verde'
              : golesTendencia === 'negativo'
              ? 'text-neon-rojo'
              : 'text-neon-cyan'
          }
        />

        {/* Corners */}
        <StatMini
          icono={CornerUpRight}
          etiqueta="Corners F/C"
          valor={estadisticas.promedioCornersFavor.toFixed(1)}
          valorSecundario={estadisticas.promedioCornersContra.toFixed(1)}
          colorIcono={
            cornersTendencia === 'positivo'
              ? 'text-neon-verde'
              : cornersTendencia === 'negativo'
              ? 'text-neon-rojo'
              : 'text-neon-cyan'
          }
        />

        {/* Disparos */}
        <StatMini
          icono={Crosshair}
          etiqueta="Disparos"
          valor={estadisticas.promedioDisparos.toFixed(1)}
          colorIcono="text-neon-amarillo"
        />
      </div>

      {/* Estadísticas extendidas */}
      {extendido && (
        <div className="mt-3 pt-3 border-t border-neon-cyan/10 space-y-2">
          {/* Por ubicación */}
          <div className="text-xs text-texto-terciario uppercase tracking-wider mb-2">
            Por ubicación
          </div>

          <div className="grid grid-cols-2 gap-2">
            {/* Local */}
            <div className="p-2 rounded bg-futurista-negro/50">
              <span className="text-xs text-texto-terciario block mb-1">Como Local</span>
              <div className="flex justify-between text-xs">
                <span className="text-texto-secundario">Goles:</span>
                <span className="font-mono text-texto-principal">
                  {estadisticas.promedioGolesFavorLocal.toFixed(1)}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-texto-secundario">Corners:</span>
                <span className="font-mono text-texto-principal">
                  {estadisticas.promedioCornersFavorLocal.toFixed(1)}
                </span>
              </div>
            </div>

            {/* Visitante */}
            <div className="p-2 rounded bg-futurista-negro/50">
              <span className="text-xs text-texto-terciario block mb-1">Como Visitante</span>
              <div className="flex justify-between text-xs">
                <span className="text-texto-secundario">Goles:</span>
                <span className="font-mono text-texto-principal">
                  {estadisticas.promedioGolesFavorVisitante.toFixed(1)}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-texto-secundario">Corners:</span>
                <span className="font-mono text-texto-principal">
                  {estadisticas.promedioCornersFavorVisitante.toFixed(1)}
                </span>
              </div>
            </div>
          </div>

          {/* Totales absolutos */}
          <div className="flex justify-between text-xs pt-2">
            <span className="text-texto-terciario">Partidos jugados:</span>
            <span className="font-mono text-texto-principal">{estadisticas.partidosJugados}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-texto-terciario">Total goles F/C:</span>
            <span className="font-mono text-texto-principal">
              {estadisticas.golesFavor}/{estadisticas.golesContra}
            </span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-texto-terciario">Total corners F/C:</span>
            <span className="font-mono text-texto-principal">
              {estadisticas.cornersFavor}/{estadisticas.cornersContra}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE COMPARATIVO
// ══════════════════════════════════════════════════════════════

/**
 * Comparación lado a lado de dos equipos
 */
export function ComparacionEquiposMini({
  estadisticasLocal,
  estadisticasVisitante,
  equipoLocal,
  equipoVisitante,
  logoLocal,
  logoVisitante,
  className,
}: {
  estadisticasLocal: EstadisticasEquipoFutbol;
  estadisticasVisitante: EstadisticasEquipoFutbol;
  equipoLocal: string;
  equipoVisitante: string;
  logoLocal?: string;
  logoVisitante?: string;
  className?: string;
}) {
  return (
    <div className={clsx('grid grid-cols-2 gap-3', className)}>
      <EstadisticaEquipoMini
        estadisticas={estadisticasLocal}
        equipo={equipoLocal}
        logoUrl={logoLocal}
        tipo="local"
      />
      <EstadisticaEquipoMini
        estadisticas={estadisticasVisitante}
        equipo={equipoVisitante}
        logoUrl={logoVisitante}
        tipo="visitante"
      />
    </div>
  );
}
