/**
 * TarjetaPartidoFutbol.tsx — Tarjeta de partido de fútbol
 *
 * Muestra información del partido con predicciones y botón de análisis.
 * Diseño glassmorphism futurista.
 */

import { Calendar, Clock, Target, CornerUpRight, Crosshair, ArrowRight } from 'lucide-react';
import { clsx } from 'clsx';
import { PartidoFutbolResumen, EstadoPartido } from '../../tipos/futbol';
import { Tarjeta, Boton } from '../atomos';
import {
  formatearFechaPartidoBogota,
  formatearHoraPartidoBogota,
} from '../../utilidades';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsTarjetaPartidoFutbol {
  /** Datos del partido */
  partido: PartidoFutbolResumen;
  /** Callback al hacer clic en analizar */
  onAnalizar?: () => void;
  /** Resumen de predicciones (opcional) */
  predicciones?: {
    cornersPromedio?: number;
    golesPromedio?: number;
    disparosPromedio?: number;
  };
  /** Clase CSS adicional */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

/**
 * Formatea fecha del partido
 */
function formatearFecha(fechaISO: string): string {
  return formatearFechaPartidoBogota(fechaISO, {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
  });
}

/**
 * Formatea hora del partido
 */
function formatearHora(fechaISO: string): string {
  return formatearHoraPartidoBogota(fechaISO);
}

/**
 * Obtiene estilos del estado del partido
 */
function getEstilosEstado(estado: EstadoPartido): { bg: string; text: string; label: string } {
  switch (estado) {
    case 'EN_VIVO':
      return {
        bg: 'bg-neon-rojo/20',
        text: 'text-neon-rojo',
        label: 'EN VIVO',
      };
    case 'ENTRETIEMPO':
      return {
        bg: 'bg-neon-amarillo/20',
        text: 'text-neon-amarillo',
        label: 'DESCANSO',
      };
    case 'FINALIZADO':
      return {
        bg: 'bg-futurista-medio/50',
        text: 'text-texto-secundario',
        label: 'FINALIZADO',
      };
    case 'SUSPENDIDO':
    case 'APLAZADO':
    case 'CANCELADO':
      return {
        bg: 'bg-neon-rojo/10',
        text: 'text-neon-rojo/70',
        label: estado,
      };
    default:
      return {
        bg: 'bg-neon-cyan/10',
        text: 'text-neon-cyan',
        label: 'PROGRAMADO',
      };
  }
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Tarjeta de partido de fútbol con información y predicciones
 */
export function TarjetaPartidoFutbol({
  partido,
  onAnalizar,
  predicciones,
  className,
}: PropsTarjetaPartidoFutbol) {
  const estilosEstado = getEstilosEstado(partido.estado);
  const esFinalizado = partido.estado === 'FINALIZADO';
  const esEnVivo = partido.estado === 'EN_VIVO' || partido.estado === 'ENTRETIEMPO';

  return (
    <Tarjeta
      className={clsx(
        'space-y-4 relative overflow-hidden',
        'border border-neon-cyan/10 hover:border-neon-cyan/30',
        'transition-all duration-300',
        className
      )}
      hover
    >
      {/* Efecto de brillo superior */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neon-cyan/50 to-transparent" />

      {/* Header: Competición y Estado */}
      <div className="flex items-center justify-between gap-4">
        <span className="text-xs text-texto-terciario uppercase tracking-wider truncate">
          {partido.competicionNombre}
          {partido.jornada && ` · J${partido.jornada}`}
        </span>
        <span
          className={clsx(
            'px-2 py-0.5 rounded text-xs font-semibold uppercase',
            estilosEstado.bg,
            estilosEstado.text,
            esEnVivo && 'animate-pulse'
          )}
        >
          {estilosEstado.label}
        </span>
      </div>

      {/* Equipos */}
      <div className="flex items-center justify-between gap-4">
        {/* Equipo Local */}
        <div className="flex-1 flex items-center gap-3">
          {partido.equipoLocalLogo && (
            <img
              src={partido.equipoLocalLogo}
              alt={partido.equipoLocalNombre}
              className="w-10 h-10 object-contain"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          )}
          <div className="flex flex-col">
            <span className="text-texto-principal font-semibold truncate max-w-[120px]">
              {partido.equipoLocalNombre}
            </span>
            <span className="text-xs text-texto-terciario">Local</span>
          </div>
        </div>

        {/* Marcador o VS */}
        <div className="flex flex-col items-center">
          {esFinalizado || esEnVivo ? (
            <div className="flex items-center gap-2">
              <span className="text-2xl font-mono font-bold text-texto-principal">
                {partido.golesLocal ?? 0}
              </span>
              <span className="text-texto-terciario">-</span>
              <span className="text-2xl font-mono font-bold text-texto-principal">
                {partido.golesVisitante ?? 0}
              </span>
            </div>
          ) : (
            <span className="text-lg font-semibold text-neon-cyan">VS</span>
          )}
        </div>

        {/* Equipo Visitante */}
        <div className="flex-1 flex items-center justify-end gap-3">
          <div className="flex flex-col items-end">
            <span className="text-texto-principal font-semibold truncate max-w-[120px]">
              {partido.equipoVisitanteNombre}
            </span>
            <span className="text-xs text-texto-terciario">Visitante</span>
          </div>
          {partido.equipoVisitanteLogo && (
            <img
              src={partido.equipoVisitanteLogo}
              alt={partido.equipoVisitanteNombre}
              className="w-10 h-10 object-contain"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          )}
        </div>
      </div>

      {/* Fecha y Hora */}
      {!esFinalizado && (
        <div className="flex items-center justify-center gap-4 text-sm text-texto-secundario">
          <div className="flex items-center gap-1.5">
            <Calendar size={14} className="text-neon-magenta" />
            <span>{formatearFecha(partido.fechaPartido)}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock size={14} className="text-neon-cyan" />
            <span>{formatearHora(partido.fechaPartido)}</span>
          </div>
        </div>
      )}

      {/* Predicciones resumen */}
      {predicciones && (
        <div className="grid grid-cols-3 gap-2 pt-2 border-t border-neon-cyan/10">
          {predicciones.cornersPromedio !== undefined && (
            <div className="flex flex-col items-center p-2 rounded-lg bg-futurista-negro/50">
              <CornerUpRight size={14} className="text-neon-cyan mb-1" />
              <span className="text-xs text-texto-terciario">Corners</span>
              <span className="text-sm font-mono font-semibold text-texto-principal">
                {predicciones.cornersPromedio.toFixed(1)}
              </span>
            </div>
          )}
          {predicciones.golesPromedio !== undefined && (
            <div className="flex flex-col items-center p-2 rounded-lg bg-futurista-negro/50">
              <Target size={14} className="text-neon-verde mb-1" />
              <span className="text-xs text-texto-terciario">Goles</span>
              <span className="text-sm font-mono font-semibold text-texto-principal">
                {predicciones.golesPromedio.toFixed(1)}
              </span>
            </div>
          )}
          {predicciones.disparosPromedio !== undefined && (
            <div className="flex flex-col items-center p-2 rounded-lg bg-futurista-negro/50">
              <Crosshair size={14} className="text-neon-amarillo mb-1" />
              <span className="text-xs text-texto-terciario">Disparos</span>
              <span className="text-sm font-mono font-semibold text-texto-principal">
                {predicciones.disparosPromedio.toFixed(1)}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Botón Analizar */}
      {onAnalizar && (
        <div className="pt-2">
          <Boton
            variante="secundario"
            tamano="sm"
            anchoCompleto
            onClick={onAnalizar}
            iconoFin={<ArrowRight size={16} />}
          >
            Analizar
          </Boton>
        </div>
      )}
    </Tarjeta>
  );
}
