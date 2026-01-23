/**
 * FiltrosHistorial.tsx — Controles de filtro para historial de partidos
 *
 * Incluye selector de cantidad de partidos, tabs de ubicación y badge del mercado activo.
 */

import { clsx } from 'clsx';
import type { CantidadPartidos, FiltroUbicacion } from '../../tipos';
import type { Mercado } from '../../tipos/analisis';

// ══════════════════════════════════════════════════════════════
// CONSTANTES
// ══════════════════════════════════════════════════════════════

const OPCIONES_CANTIDAD: CantidadPartidos[] = [10, 15, 20, 30, 40];

const OPCIONES_UBICACION: { valor: FiltroUbicacion; etiqueta: string }[] = [
  { valor: 'TODOS', etiqueta: 'Todos' },
  { valor: 'LOCAL', etiqueta: 'Local' },
  { valor: 'VISITANTE', etiqueta: 'Visitante' },
];

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsFiltrosHistorial {
  /** Cantidad de partidos seleccionada */
  cantidad: CantidadPartidos;
  /** Filtro de ubicación seleccionado */
  ubicacion: FiltroUbicacion;
  /** Mercado activo para mostrar en badge */
  mercadoActivo: Mercado;
  /** Callback al cambiar cantidad */
  onCambiarCantidad: (cantidad: CantidadPartidos) => void;
  /** Callback al cambiar ubicación */
  onCambiarUbicacion: (ubicacion: FiltroUbicacion) => void;
  /** Clase CSS adicional */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Controles de filtro para la sección de historial detallado
 */
export function FiltrosHistorial({
  cantidad,
  ubicacion,
  mercadoActivo,
  onCambiarCantidad,
  onCambiarUbicacion,
  className,
}: PropsFiltrosHistorial) {
  return (
    <div className={clsx('flex flex-wrap items-center gap-3', className)}>
      {/* Selector de cantidad */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-texto-terciario uppercase tracking-wider">
          Partidos:
        </span>
        <select
          value={cantidad}
          onChange={(e) => onCambiarCantidad(Number(e.target.value) as CantidadPartidos)}
          className="px-3 py-1.5 text-sm rounded-lg bg-futurista-oscuro/80
                     border border-neon-cyan/30 text-texto-principal
                     hover:border-neon-cyan/50 focus:border-neon-cyan
                     focus:outline-none focus:ring-1 focus:ring-neon-cyan/30
                     transition-all cursor-pointer"
        >
          {OPCIONES_CANTIDAD.map((n) => (
            <option key={n} value={n} className="bg-futurista-oscuro">
              Últimos {n}
            </option>
          ))}
        </select>
      </div>

      {/* Tabs de ubicación */}
      <div className="flex rounded-lg border border-neon-cyan/20 overflow-hidden">
        {OPCIONES_UBICACION.map(({ valor, etiqueta }) => (
          <button
            key={valor}
            type="button"
            onClick={() => onCambiarUbicacion(valor)}
            className={clsx(
              'px-3 py-1.5 text-sm font-medium transition-all',
              ubicacion === valor
                ? 'bg-neon-cyan/20 text-neon-cyan'
                : 'bg-futurista-oscuro/50 text-texto-secundario hover:text-texto-principal hover:bg-futurista-medio/50'
            )}
          >
            {etiqueta}
          </button>
        ))}
      </div>

      {/* Badge mercado activo */}
      <div className="ml-auto">
        <span
          className="px-2 py-1 text-xs font-mono rounded bg-neon-cyan/10
                      text-neon-cyan border border-neon-cyan/30"
        >
          Mercado: {mercadoActivo === 'COMPLETO' ? 'Total' : mercadoActivo}
        </span>
      </div>
    </div>
  );
}
