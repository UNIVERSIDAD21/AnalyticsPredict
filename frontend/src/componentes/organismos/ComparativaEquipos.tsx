/**
 * ComparativaEquipos.tsx — Comparación visual de equipos
 *
 * Muestra un gráfico de barras horizontales comparando estadísticas
 * entre el equipo local (cyan) y visitante (magenta).
 * Diseño glassmorphism futurista.
 */

import { useMemo } from 'react';
import { clsx } from 'clsx';
import { Target, CornerUpRight, Crosshair, TrendingUp, Shield, Swords } from 'lucide-react';
import { Tarjeta } from '../atomos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface EstadisticasEquipo {
  golesFavor?: number;
  golesContra?: number;
  cornersFavor?: number;
  cornersContra?: number;
  disparosTotal?: number;
  disparosArco?: number;
  victorias?: number;
  derrotas?: number;
  empates?: number;
  partidosJugados?: number;
  promedioGolesFavor?: number;
  promedioGolesContra?: number;
  promedioCornersFavor?: number;
  promedioCornersContra?: number;
  promedioDisparos?: number;
}

interface PropsComparativaEquipos {
  /** Equipo local con nombre y estadísticas */
  equipoLocal: {
    nombre: string;
    estadisticas: EstadisticasEquipo;
  };
  /** Equipo visitante con nombre y estadísticas */
  equipoVisitante: {
    nombre: string;
    estadisticas: EstadisticasEquipo;
  };
  /** Clase CSS adicional */
  className?: string;
}

interface Metrica {
  id: string;
  etiqueta: string;
  icono: React.ReactNode;
  valorLocal: number;
  valorVisitante: number;
  formato?: 'numero' | 'decimal' | 'porcentaje';
}

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

/**
 * Formatea un valor según el tipo especificado
 */
function formatearValor(valor: number, formato: 'numero' | 'decimal' | 'porcentaje' = 'numero'): string {
  if (valor === null || valor === undefined || !isFinite(valor)) return '-';

  switch (formato) {
    case 'decimal':
      return valor.toFixed(1);
    case 'porcentaje':
      return `${(valor * 100).toFixed(0)}%`;
    default:
      return Math.round(valor).toString();
  }
}

/**
 * Calcula el porcentaje para la barra de comparación
 */
function calcularPorcentaje(valor: number, maximo: number): number {
  if (maximo === 0) return 50;
  return Math.min(100, Math.max(0, (valor / maximo) * 100));
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE BARRA COMPARATIVA
// ══════════════════════════════════════════════════════════════

interface PropsBarraComparativa {
  metrica: Metrica;
}

function BarraComparativa({ metrica }: PropsBarraComparativa) {
  const { etiqueta, icono, valorLocal, valorVisitante, formato = 'numero' } = metrica;

  const maximo = Math.max(valorLocal, valorVisitante, 0.1);
  const porcentajeLocal = calcularPorcentaje(valorLocal, maximo);
  const porcentajeVisitante = calcularPorcentaje(valorVisitante, maximo);

  // Determinar quién tiene ventaja
  const ventajaLocal = valorLocal > valorVisitante;
  const empate = valorLocal === valorVisitante;

  return (
    <div className="space-y-2">
      {/* Etiqueta y valores */}
      <div className="flex items-center justify-between">
        <span
          className={clsx(
            'text-sm font-mono font-semibold',
            ventajaLocal ? 'text-neon-cyan' : empate ? 'text-texto-secundario' : 'text-texto-terciario'
          )}
        >
          {formatearValor(valorLocal, formato)}
        </span>

        <div className="flex items-center gap-2 text-xs text-texto-secundario">
          <span className="text-neon-cyan/50">{icono}</span>
          <span className="uppercase tracking-wider">{etiqueta}</span>
        </div>

        <span
          className={clsx(
            'text-sm font-mono font-semibold',
            !ventajaLocal && !empate ? 'text-neon-magenta' : empate ? 'text-texto-secundario' : 'text-texto-terciario'
          )}
        >
          {formatearValor(valorVisitante, formato)}
        </span>
      </div>

      {/* Barras */}
      <div className="flex items-center gap-1 h-3">
        {/* Barra local (derecha a izquierda) */}
        <div className="flex-1 h-full flex justify-end">
          <div
            className={clsx(
              'h-full rounded-l-full transition-all duration-500',
              ventajaLocal
                ? 'bg-gradient-to-l from-neon-cyan to-neon-cyan/50'
                : 'bg-neon-cyan/30'
            )}
            style={{ width: `${porcentajeLocal}%` }}
          />
        </div>

        {/* Separador central */}
        <div className="w-px h-full bg-texto-terciario/30" />

        {/* Barra visitante (izquierda a derecha) */}
        <div className="flex-1 h-full">
          <div
            className={clsx(
              'h-full rounded-r-full transition-all duration-500',
              !ventajaLocal && !empate
                ? 'bg-gradient-to-r from-neon-magenta/50 to-neon-magenta'
                : 'bg-neon-magenta/30'
            )}
            style={{ width: `${porcentajeVisitante}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Comparación visual head-to-head de estadísticas entre dos equipos
 */
export function ComparativaEquipos({
  equipoLocal,
  equipoVisitante,
  className,
}: PropsComparativaEquipos) {
  // Preparar métricas para comparar
  const metricas = useMemo<Metrica[]>(() => {
    const local = equipoLocal.estadisticas;
    const visitante = equipoVisitante.estadisticas;

    const listaMetricas: Metrica[] = [];

    // Goles a favor
    if (local.promedioGolesFavor !== undefined || visitante.promedioGolesFavor !== undefined) {
      listaMetricas.push({
        id: 'goles-favor',
        etiqueta: 'Goles/Partido',
        icono: <Target size={12} />,
        valorLocal: local.promedioGolesFavor ?? 0,
        valorVisitante: visitante.promedioGolesFavor ?? 0,
        formato: 'decimal',
      });
    }

    // Goles en contra
    if (local.promedioGolesContra !== undefined || visitante.promedioGolesContra !== undefined) {
      listaMetricas.push({
        id: 'goles-contra',
        etiqueta: 'Goles Recibidos',
        icono: <Shield size={12} />,
        valorLocal: local.promedioGolesContra ?? 0,
        valorVisitante: visitante.promedioGolesContra ?? 0,
        formato: 'decimal',
      });
    }

    // Corners a favor
    if (local.promedioCornersFavor !== undefined || visitante.promedioCornersFavor !== undefined) {
      listaMetricas.push({
        id: 'corners-favor',
        etiqueta: 'Corners/Partido',
        icono: <CornerUpRight size={12} />,
        valorLocal: local.promedioCornersFavor ?? 0,
        valorVisitante: visitante.promedioCornersFavor ?? 0,
        formato: 'decimal',
      });
    }

    // Corners en contra
    if (local.promedioCornersContra !== undefined || visitante.promedioCornersContra !== undefined) {
      listaMetricas.push({
        id: 'corners-contra',
        etiqueta: 'Corners Recibidos',
        icono: <CornerUpRight size={12} />,
        valorLocal: local.promedioCornersContra ?? 0,
        valorVisitante: visitante.promedioCornersContra ?? 0,
        formato: 'decimal',
      });
    }

    // Disparos
    if (local.promedioDisparos !== undefined || visitante.promedioDisparos !== undefined) {
      listaMetricas.push({
        id: 'disparos',
        etiqueta: 'Disparos/Partido',
        icono: <Crosshair size={12} />,
        valorLocal: local.promedioDisparos ?? 0,
        valorVisitante: visitante.promedioDisparos ?? 0,
        formato: 'decimal',
      });
    }

    // Victorias (totales)
    if (local.victorias !== undefined || visitante.victorias !== undefined) {
      listaMetricas.push({
        id: 'victorias',
        etiqueta: 'Victorias',
        icono: <TrendingUp size={12} />,
        valorLocal: local.victorias ?? 0,
        valorVisitante: visitante.victorias ?? 0,
        formato: 'numero',
      });
    }

    // Goles totales a favor
    if (local.golesFavor !== undefined || visitante.golesFavor !== undefined) {
      listaMetricas.push({
        id: 'goles-totales',
        etiqueta: 'Goles Totales',
        icono: <Target size={12} />,
        valorLocal: local.golesFavor ?? 0,
        valorVisitante: visitante.golesFavor ?? 0,
        formato: 'numero',
      });
    }

    // Corners totales a favor
    if (local.cornersFavor !== undefined || visitante.cornersFavor !== undefined) {
      listaMetricas.push({
        id: 'corners-totales',
        etiqueta: 'Corners Totales',
        icono: <CornerUpRight size={12} />,
        valorLocal: local.cornersFavor ?? 0,
        valorVisitante: visitante.cornersFavor ?? 0,
        formato: 'numero',
      });
    }

    // Disparos totales
    if (local.disparosTotal !== undefined || visitante.disparosTotal !== undefined) {
      listaMetricas.push({
        id: 'disparos-totales',
        etiqueta: 'Disparos Totales',
        icono: <Crosshair size={12} />,
        valorLocal: local.disparosTotal ?? 0,
        valorVisitante: visitante.disparosTotal ?? 0,
        formato: 'numero',
      });
    }

    // Disparos a puerta
    if (local.disparosArco !== undefined || visitante.disparosArco !== undefined) {
      listaMetricas.push({
        id: 'disparos-arco',
        etiqueta: 'Disparos a Puerta',
        icono: <Crosshair size={12} />,
        valorLocal: local.disparosArco ?? 0,
        valorVisitante: visitante.disparosArco ?? 0,
        formato: 'numero',
      });
    }

    return listaMetricas;
  }, [equipoLocal.estadisticas, equipoVisitante.estadisticas]);

  // Calcular resumen de ventaja
  const resumenVentaja = useMemo(() => {
    let ventajasLocal = 0;
    let ventajasVisitante = 0;
    let empates = 0;

    metricas.forEach((m) => {
      if (m.valorLocal > m.valorVisitante) {
        ventajasLocal++;
      } else if (m.valorVisitante > m.valorLocal) {
        ventajasVisitante++;
      } else {
        empates++;
      }
    });

    return { ventajasLocal, ventajasVisitante, empates };
  }, [metricas]);

  if (metricas.length === 0) {
    return (
      <Tarjeta className={clsx('text-center py-8', className)}>
        <p className="text-texto-secundario">
          No hay estadísticas disponibles para comparar
        </p>
      </Tarjeta>
    );
  }

  return (
    <Tarjeta className={clsx('space-y-6', className)}>
      {/* Header */}
      <div className="pb-4 border-b border-neon-cyan/20">
        <div className="flex items-center justify-center gap-3">
          <Swords size={20} className="text-neon-cyan" />
          <h3 className="text-lg font-futurista font-bold text-texto-principal uppercase tracking-wider">
            Comparativa Equipos
          </h3>
        </div>
      </div>

      {/* Nombres de equipos */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-neon-cyan" />
          <span className="text-sm font-semibold text-neon-cyan truncate max-w-[120px]">
            {equipoLocal.nombre}
          </span>
        </div>

        <span className="text-xs text-texto-terciario">VS</span>

        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-neon-magenta truncate max-w-[120px]">
            {equipoVisitante.nombre}
          </span>
          <div className="w-3 h-3 rounded-full bg-neon-magenta" />
        </div>
      </div>

      {/* Barras comparativas */}
      <div className="space-y-4">
        {metricas.map((metrica) => (
          <BarraComparativa key={metrica.id} metrica={metrica} />
        ))}
      </div>

      {/* Resumen de ventaja */}
      <div className="pt-4 border-t border-neon-cyan/10">
        <div className="flex items-center justify-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-texto-terciario">Ventaja:</span>
            <span className="px-2 py-0.5 rounded-full bg-neon-cyan/10 text-neon-cyan font-semibold">
              {equipoLocal.nombre}: {resumenVentaja.ventajasLocal}
            </span>
          </div>

          {resumenVentaja.empates > 0 && (
            <span className="px-2 py-0.5 rounded-full bg-futurista-medio/50 text-texto-secundario font-semibold">
              Iguales: {resumenVentaja.empates}
            </span>
          )}

          <span className="px-2 py-0.5 rounded-full bg-neon-magenta/10 text-neon-magenta font-semibold">
            {equipoVisitante.nombre}: {resumenVentaja.ventajasVisitante}
          </span>
        </div>
      </div>
    </Tarjeta>
  );
}
