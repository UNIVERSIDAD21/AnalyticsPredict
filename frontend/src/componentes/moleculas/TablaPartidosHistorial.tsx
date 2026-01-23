/**
 * TablaPartidosHistorial.tsx — Tabla de partidos con datos dinámicos por mercado
 *
 * Muestra fecha, rival, resultado, total, badge OVER/UNDER y margen vs línea.
 */

import { clsx } from 'clsx';
import type { PartidoConMercado } from '../../tipos';
import type { Mercado } from '../../tipos/analisis';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsTablaPartidosHistorial {
  /** Lista de partidos con datos calculados del mercado */
  partidos: PartidoConMercado[];
  /** Abreviatura del equipo analizado */
  equipoAbr: string;
  /** Línea de referencia para comparación */
  linea: number;
  /** Mercado seleccionado */
  mercado: Mercado;
  /** Estado de carga */
  cargando?: boolean;
  /** Clase CSS adicional */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// UTILIDADES
// ══════════════════════════════════════════════════════════════

/**
 * Formatea una fecha ISO a formato corto (ej: "24 dic")
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
// COMPONENTE SKELETON
// ══════════════════════════════════════════════════════════════

function SkeletonTabla({ filas = 5 }: { filas?: number }) {
  return (
    <div className="animate-pulse space-y-2">
      {/* Header skeleton */}
      <div className="h-10 bg-futurista-medio/50 rounded-t-lg" />
      {/* Filas skeleton */}
      {Array.from({ length: filas }).map((_, i) => (
        <div key={i} className="h-12 bg-futurista-oscuro/30 rounded" />
      ))}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Tabla de partidos con columnas dinámicas según el mercado seleccionado
 */
export function TablaPartidosHistorial({
  partidos,
  equipoAbr,
  linea,
  mercado,
  cargando,
  className,
}: PropsTablaPartidosHistorial) {
  // Estado de carga
  if (cargando) {
    return <SkeletonTabla filas={5} />;
  }

  // Estado vacío
  if (partidos.length === 0) {
    return (
      <div className="text-center py-8 text-texto-terciario border border-neon-cyan/10 rounded-lg bg-futurista-negro/30">
        No hay partidos disponibles con los filtros seleccionados
      </div>
    );
  }

  return (
    <div className={clsx('overflow-x-auto rounded-lg border border-neon-cyan/10', className)}>
      <table className="w-full text-sm">
        {/* Header */}
        <thead>
          <tr className="bg-futurista-medio/50 border-b border-neon-cyan/20">
            <th className="text-left py-3 px-4 text-texto-terciario font-medium uppercase tracking-wider text-xs">
              Fecha
            </th>
            <th className="text-left py-3 px-4 text-texto-terciario font-medium uppercase tracking-wider text-xs">
              Rival
            </th>
            <th className="text-center py-3 px-4 text-texto-terciario font-medium uppercase tracking-wider text-xs">
              Resultado
            </th>
            <th className="text-center py-3 px-4 text-texto-terciario font-medium uppercase tracking-wider text-xs">
              Total
            </th>
            <th className="text-center py-3 px-4 text-texto-terciario font-medium uppercase tracking-wider text-xs">
              vs Línea
            </th>
            <th className="text-center py-3 px-4 text-texto-terciario font-medium uppercase tracking-wider text-xs">
              Margen
            </th>
          </tr>
        </thead>

        {/* Body */}
        <tbody className="divide-y divide-texto-terciario/10">
          {partidos.map((partido) => {
            const esLocal = partido.ubicacionEquipo === 'LOCAL';
            const rivalAbr = esLocal ? partido.visitanteAbr : partido.localAbr;
            const prefijoRival = esLocal ? '' : '@';
            const esVictoria = partido.resultado === 'VICTORIA';

            return (
              <tr
                key={partido.id}
                className={clsx(
                  'transition-colors',
                  partido.esOver ? 'hover:bg-over-claro/30' : 'hover:bg-under-claro/30'
                )}
              >
                {/* Fecha */}
                <td className="py-3 px-4 text-texto-secundario whitespace-nowrap">
                  {formatearFechaCorta(partido.fecha)}
                </td>

                {/* Rival */}
                <td className="py-3 px-4">
                  <span
                    className={clsx(
                      'font-medium',
                      esLocal ? 'text-texto-principal' : 'text-texto-secundario'
                    )}
                  >
                    {prefijoRival}
                    {rivalAbr}
                  </span>
                </td>

                {/* Resultado */}
                <td className="py-3 px-4 text-center font-mono">
                  <span className={esVictoria ? 'text-neon-verde' : 'text-neon-rojo'}>
                    {partido.resultadoMercado}
                  </span>
                </td>

                {/* Total */}
                <td className="py-3 px-4 text-center">
                  <span className="font-mono font-bold text-neon-cyan">
                    {partido.totalMercado}
                  </span>
                </td>

                {/* vs Línea (Badge) */}
                <td className="py-3 px-4 text-center">
                  <span
                    className={clsx(
                      'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold border',
                      partido.esOver
                        ? 'bg-over-claro text-over-medio border-over-medio/30'
                        : 'bg-under-claro text-under-medio border-under-medio/30'
                    )}
                  >
                    {partido.esOver ? 'OVER' : 'UNDER'}
                  </span>
                </td>

                {/* Margen */}
                <td className="py-3 px-4 text-center font-mono">
                  <span
                    className={clsx(
                      'font-medium',
                      partido.margenVsLinea > 0 ? 'text-over-medio' : 'text-under-medio'
                    )}
                  >
                    {partido.margenVsLinea > 0 ? '+' : ''}
                    {partido.margenVsLinea.toFixed(1)}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
