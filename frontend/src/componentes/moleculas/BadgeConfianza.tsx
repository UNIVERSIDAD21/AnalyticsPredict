/**
 * BadgeConfianza.tsx — Badge de nivel de confianza
 *
 * Muestra el nivel de confianza con colores apropiados según COLORES_CONFIANZA.
 */

import { clsx } from 'clsx';
import { Shield, ShieldCheck, ShieldAlert, ShieldOff } from 'lucide-react';
import { NivelConfianza, COLORES_CONFIANZA } from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsBadgeConfianza {
  /** Nivel de confianza */
  nivel: NivelConfianza;
  /** Mostrar icono */
  mostrarIcono?: boolean;
  /** Mostrar etiqueta de texto */
  mostrarEtiqueta?: boolean;
  /** Tamaño del badge */
  tamano?: 'sm' | 'md' | 'lg';
  /** Clase CSS adicional */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// CONSTANTES
// ══════════════════════════════════════════════════════════════

const ETIQUETAS_CONFIANZA: Record<NivelConfianza, string> = {
  MUY_ALTA: 'Muy Alta',
  ALTA: 'Alta',
  MEDIA: 'Media',
  BAJA: 'Baja',
  MUY_BAJA: 'Muy Baja',
};

const ICONOS_CONFIANZA: Record<NivelConfianza, typeof ShieldCheck> = {
  MUY_ALTA: ShieldCheck,
  ALTA: ShieldCheck,
  MEDIA: Shield,
  BAJA: ShieldAlert,
  MUY_BAJA: ShieldOff,
};

const TAMANOS = {
  sm: {
    padding: 'px-2 py-0.5',
    text: 'text-xs',
    iconSize: 12,
    gap: 'gap-1',
  },
  md: {
    padding: 'px-2.5 py-1',
    text: 'text-sm',
    iconSize: 14,
    gap: 'gap-1.5',
  },
  lg: {
    padding: 'px-3 py-1.5',
    text: 'text-base',
    iconSize: 16,
    gap: 'gap-2',
  },
};

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Badge que muestra el nivel de confianza con estilo futurista
 */
export function BadgeConfianza({
  nivel,
  mostrarIcono = true,
  mostrarEtiqueta = true,
  tamano = 'md',
  className,
}: PropsBadgeConfianza) {
  const colores = COLORES_CONFIANZA[nivel];
  const etiqueta = ETIQUETAS_CONFIANZA[nivel];
  const Icono = ICONOS_CONFIANZA[nivel];
  const estilosTamano = TAMANOS[tamano];

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full font-medium',
        'border backdrop-blur-sm',
        'transition-all duration-200',
        estilosTamano.padding,
        estilosTamano.text,
        estilosTamano.gap,
        colores.bg,
        colores.border,
        colores.text,
        className
      )}
      role="status"
      aria-label={`Nivel de confianza: ${etiqueta}`}
    >
      {mostrarIcono && (
        <Icono
          size={estilosTamano.iconSize}
          className={clsx(
            'flex-shrink-0',
            nivel === 'MUY_ALTA' && 'animate-pulse'
          )}
        />
      )}
      {mostrarEtiqueta && (
        <span className="font-semibold uppercase tracking-wide">
          {etiqueta}
        </span>
      )}
    </span>
  );
}

// ══════════════════════════════════════════════════════════════
// VARIANTES ADICIONALES
// ══════════════════════════════════════════════════════════════

/**
 * Badge de confianza solo con icono (para espacios reducidos)
 */
export function BadgeConfianzaIcono({
  nivel,
  tamano = 'md',
  className,
}: Omit<PropsBadgeConfianza, 'mostrarIcono' | 'mostrarEtiqueta'>) {
  return (
    <BadgeConfianza
      nivel={nivel}
      mostrarIcono
      mostrarEtiqueta={false}
      tamano={tamano}
      className={className}
    />
  );
}

/**
 * Indicador de confianza en formato de barra
 */
export function BarraConfianza({
  nivel,
  className,
}: {
  nivel: NivelConfianza;
  className?: string;
}) {
  const colores = COLORES_CONFIANZA[nivel];

  // Mapear nivel a porcentaje
  const porcentajes: Record<NivelConfianza, number> = {
    MUY_ALTA: 100,
    ALTA: 80,
    MEDIA: 60,
    BAJA: 40,
    MUY_BAJA: 20,
  };

  const porcentaje = porcentajes[nivel];

  return (
    <div
      className={clsx(
        'flex items-center gap-2',
        className
      )}
    >
      <div className="flex-1 h-1.5 rounded-full bg-futurista-medio/50 overflow-hidden">
        <div
          className={clsx(
            'h-full rounded-full transition-all duration-500',
            nivel === 'MUY_ALTA' && 'bg-neon-verde',
            nivel === 'ALTA' && 'bg-neon-verde/80',
            nivel === 'MEDIA' && 'bg-neon-amarillo',
            nivel === 'BAJA' && 'bg-neon-rojo/70',
            nivel === 'MUY_BAJA' && 'bg-neon-rojo'
          )}
          style={{ width: `${porcentaje}%` }}
          role="progressbar"
          aria-valuenow={porcentaje}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      <span className={clsx('text-xs font-mono', colores.text)}>
        {porcentaje}%
      </span>
    </div>
  );
}
