/**
 * SeccionH2H.tsx — Historial de enfrentamientos directos
 *
 * Muestra el historial de enfrentamientos directos entre ambos equipos
 * con resultados, totales, y tendencias OVER/UNDER.
 */

import { useState, useMemo } from 'react';
import { Users, ChevronDown, ChevronUp, TrendingUp, Info } from 'lucide-react';
import { clsx } from 'clsx';
import { Tarjeta } from '../atomos';
import type { ContextoH2H } from '../../tipos/analisis';

// ══════════════════════════════════════════════════════════════
// CONSTANTES
// ══════════════════════════════════════════════════════════════

/** Número máximo de partidos a mostrar en la tabla */
const MAX_PARTIDOS_MOSTRAR = 5;

/** Línea típica de referencia para determinar OVER/UNDER en H2H */
const LINEA_TIPICA = 220;

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsSeccionH2H {
  /** Datos de enfrentamientos directos */
  h2h: ContextoH2H;
  /** Nombre del equipo principal */
  equipoNombre: string;
  /** Nombre del equipo rival */
  rivalNombre: string;
  /** Línea actual para comparar (opcional) */
  lineaActual?: number;
  /** Iniciar expandido o colapsado */
  inicialmenteExpandido?: boolean;
  /** Clase CSS adicional */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// UTILIDADES
// ══════════════════════════════════════════════════════════════

/**
 * Formatea una fecha ISO a formato legible
 */
function formatearFecha(fechaISO: string): string {
  try {
    const fecha = new Date(fechaISO);
    return fecha.toLocaleDateString('es-ES', {
      day: '2-digit',
      month: 'short',
      year: '2-digit',
    });
  } catch {
    return fechaISO;
  }
}

/**
 * Genera un nombre corto para un equipo (máx 3 caracteres)
 */
function nombreCorto(nombre: string): string {
  // Extraer las primeras 3 letras significativas
  const palabras = nombre.split(/\s+/);
  if (palabras.length > 1) {
    return palabras.map((p) => p[0]).join('').toUpperCase().slice(0, 3);
  }
  return nombre.slice(0, 3).toUpperCase();
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

export function SeccionH2H({
  h2h,
  equipoNombre,
  rivalNombre,
  lineaActual,
  inicialmenteExpandido = false,
  className,
}: PropsSeccionH2H) {
  const [expandido, setExpandido] = useState(inicialmenteExpandido);

  // Calcular estadísticas derivadas
  const stats = useMemo(() => {
    const linea = lineaActual || LINEA_TIPICA;
    const porcentajeOver = (h2h.tendencia_over * 100).toFixed(0);
    const empates =
      h2h.total_partidos - h2h.victorias_equipo - h2h.victorias_rival;

    // Tomar solo los últimos N partidos
    const partidosMostrar = h2h.partidos.slice(0, MAX_PARTIDOS_MOSTRAR);

    return {
      linea,
      porcentajeOver,
      empates,
      partidosMostrar,
    };
  }, [h2h, lineaActual]);

  // Si no hay datos H2H
  if (h2h.total_partidos === 0) {
    return (
      <Tarjeta className={clsx('space-y-4', className)} padding="md">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-neon-cyan" />
          <h3 className="text-lg font-futurista text-texto-principal tracking-wide">
            Head-to-Head
          </h3>
        </div>

        <div className="flex items-center gap-3 p-4 rounded-lg bg-futurista-medio/30 border border-texto-terciario/20">
          <Info className="w-5 h-5 text-texto-terciario flex-shrink-0" />
          <p className="text-sm text-texto-secundario">
            No hay enfrentamientos directos registrados entre estos equipos.
          </p>
        </div>
      </Tarjeta>
    );
  }

  return (
    <Tarjeta className={clsx('space-y-4', className)} padding="md">
      {/* Encabezado colapsable */}
      <button
        onClick={() => setExpandido(!expandido)}
        className="w-full flex items-center justify-between gap-2 group"
        aria-expanded={expandido}
        aria-controls="contenido-h2h"
      >
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-neon-cyan" />
          <h3 className="text-lg font-futurista text-texto-principal tracking-wide">
            Head-to-Head
          </h3>
          <span className="text-sm text-texto-terciario">
            ({h2h.total_partidos} partidos)
          </span>
        </div>

        {expandido ? (
          <ChevronUp className="w-5 h-5 text-texto-terciario group-hover:text-texto-secundario transition-colors" />
        ) : (
          <ChevronDown className="w-5 h-5 text-texto-terciario group-hover:text-texto-secundario transition-colors" />
        )}
      </button>

      {/* Resumen (siempre visible) */}
      <div className="flex flex-wrap items-center gap-4 text-sm">
        {/* Record */}
        <div className="flex items-center gap-1.5">
          <span className="text-texto-secundario">Record:</span>
          <span className="font-mono">
            <span className="text-neon-verde">{h2h.victorias_equipo}</span>
            <span className="text-texto-terciario">-</span>
            <span className="text-neon-rojo">{h2h.victorias_rival}</span>
          </span>
        </div>

        {/* Separador */}
        <span className="text-texto-terciario hidden sm:inline">|</span>

        {/* Promedio */}
        <div className="flex items-center gap-1.5">
          <span className="text-texto-secundario">Promedio:</span>
          <span className="font-mono text-texto-principal">
            {h2h.promedio_total.toFixed(1)} pts
          </span>
        </div>

        {/* Separador */}
        <span className="text-texto-terciario hidden sm:inline">|</span>

        {/* Tendencia OVER */}
        <div className="flex items-center gap-1.5">
          <span className="text-texto-secundario">OVER:</span>
          <span
            className={clsx(
              'font-mono font-semibold',
              h2h.tendencia_over >= 0.6
                ? 'text-over-medio'
                : h2h.tendencia_over <= 0.4
                ? 'text-under-medio'
                : 'text-texto-principal'
            )}
          >
            {stats.porcentajeOver}%
          </span>
        </div>
      </div>

      {/* Contenido expandible */}
      {expandido && (
        <div id="contenido-h2h" className="space-y-4">
          {/* Tabla de partidos */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neon-cyan/20">
                  <th className="text-left py-2 px-2 text-xs uppercase tracking-wider text-texto-terciario font-normal">
                    Fecha
                  </th>
                  <th className="text-left py-2 px-2 text-xs uppercase tracking-wider text-texto-terciario font-normal">
                    Resultado
                  </th>
                  <th className="text-center py-2 px-2 text-xs uppercase tracking-wider text-texto-terciario font-normal">
                    Total
                  </th>
                  <th className="text-center py-2 px-2 text-xs uppercase tracking-wider text-texto-terciario font-normal">
                    vs Línea
                  </th>
                </tr>
              </thead>
              <tbody>
                {stats.partidosMostrar.map((partido, index) => {
                  const esOver = partido.total > stats.linea;
                  const esEquipoGanador =
                    partido.puntos_equipo > partido.puntos_rival;

                  return (
                    <tr
                      key={`${partido.fecha}-${index}`}
                      className="border-b border-futurista-medio/50 hover:bg-futurista-medio/30 transition-colors"
                    >
                      {/* Fecha */}
                      <td className="py-2 px-2 text-texto-secundario font-mono text-xs">
                        {formatearFecha(partido.fecha)}
                      </td>

                      {/* Resultado */}
                      <td className="py-2 px-2">
                        <div className="flex items-center gap-2">
                          <span
                            className={clsx(
                              'font-mono',
                              esEquipoGanador
                                ? 'text-neon-verde'
                                : 'text-texto-principal'
                            )}
                          >
                            {nombreCorto(equipoNombre)} {partido.puntos_equipo}
                          </span>
                          <span className="text-texto-terciario">-</span>
                          <span
                            className={clsx(
                              'font-mono',
                              !esEquipoGanador
                                ? 'text-neon-verde'
                                : 'text-texto-principal'
                            )}
                          >
                            {nombreCorto(rivalNombre)} {partido.puntos_rival}
                          </span>
                        </div>
                      </td>

                      {/* Total */}
                      <td className="py-2 px-2 text-center font-mono text-texto-principal">
                        {partido.total}
                      </td>

                      {/* vs Línea */}
                      <td className="py-2 px-2 text-center">
                        <span
                          className={clsx(
                            'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
                            esOver
                              ? 'bg-over-claro text-over-medio'
                              : 'bg-under-claro text-under-medio'
                          )}
                        >
                          {esOver ? 'OVER' : 'UNDER'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Nota de tendencia */}
          <div className="flex items-start gap-2 p-3 rounded-lg bg-futurista-medio/30 border border-neon-cyan/10">
            <TrendingUp className="w-4 h-4 text-neon-cyan flex-shrink-0 mt-0.5" />
            <p className="text-sm text-texto-secundario">
              <span className="text-neon-cyan font-medium">Tendencia:</span>{' '}
              {Math.round(h2h.tendencia_over * h2h.total_partidos)}/
              {h2h.total_partidos} partidos fueron{' '}
              <span className="text-over-medio font-medium">OVER</span>
              {lineaActual && (
                <span className="text-texto-terciario">
                  {' '}
                  (línea ~{stats.linea})
                </span>
              )}
            </p>
          </div>

          {/* Promedios individuales */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 rounded-lg bg-futurista-negro/50 border border-texto-terciario/10">
              <p className="text-xs text-texto-terciario mb-1 uppercase tracking-wider">
                Promedio {nombreCorto(equipoNombre)}
              </p>
              <p className="text-xl font-mono text-texto-principal">
                {h2h.promedio_equipo.toFixed(1)}
                <span className="text-sm text-texto-terciario ml-1">pts</span>
              </p>
            </div>
            <div className="p-3 rounded-lg bg-futurista-negro/50 border border-texto-terciario/10">
              <p className="text-xs text-texto-terciario mb-1 uppercase tracking-wider">
                Promedio {nombreCorto(rivalNombre)}
              </p>
              <p className="text-xl font-mono text-texto-principal">
                {h2h.promedio_rival.toFixed(1)}
                <span className="text-sm text-texto-terciario ml-1">pts</span>
              </p>
            </div>
          </div>
        </div>
      )}
    </Tarjeta>
  );
}
