/**
 * TarjetaRecomendacion.tsx — Tarjeta de recomendación de apuesta
 *
 * Muestra una apuesta recomendada con badge de confianza, probabilidad,
 * valor esperado y botón para registrar.
 * Diseño futurista glassmorphism con efectos neón.
 */

import { clsx } from 'clsx';
import {
  TrendingUp,
  TrendingDown,
  Target,
  Percent,
  Calculator,
  BookmarkPlus,
  Sparkles,
  AlertCircle,
} from 'lucide-react';
import { Tarjeta, Boton } from '../atomos';
import { BadgeConfianza } from '../moleculas';
import {
  RecomendacionApuesta,
  NivelConfianza,
  ETIQUETAS_MERCADOS,
  COLORES_CONFIANZA,
} from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsTarjetaRecomendacion {
  /** Datos de la recomendación */
  recomendacion: RecomendacionApuesta;
  /** Callback al registrar la apuesta */
  onRegistrar?: () => void;
  /** Mostrar versión compacta */
  compacta?: boolean;
  /** Destacar la tarjeta */
  destacada?: boolean;
  /** Clase CSS adicional */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

/**
 * Obtiene el color principal basado en el nivel de confianza
 */
function getColorPrincipal(nivel: NivelConfianza): {
  border: string;
  glow: string;
  bg: string;
  text: string;
  icon: string;
} {
  switch (nivel) {
    case 'MUY_ALTA':
      return {
        border: 'border-neon-verde/50',
        glow: 'shadow-glow-verde',
        bg: 'bg-neon-verde/10',
        text: 'text-neon-verde',
        icon: 'text-neon-verde',
      };
    case 'ALTA':
      return {
        border: 'border-neon-verde/30',
        glow: '',
        bg: 'bg-neon-verde/5',
        text: 'text-neon-verde',
        icon: 'text-neon-verde/80',
      };
    case 'MEDIA':
      return {
        border: 'border-neon-amarillo/30',
        glow: '',
        bg: 'bg-neon-amarillo/5',
        text: 'text-neon-amarillo',
        icon: 'text-neon-amarillo',
      };
    case 'BAJA':
      return {
        border: 'border-neon-rojo/30',
        glow: '',
        bg: 'bg-neon-rojo/5',
        text: 'text-neon-rojo/80',
        icon: 'text-neon-rojo/70',
      };
    case 'MUY_BAJA':
      return {
        border: 'border-neon-rojo/50',
        glow: '',
        bg: 'bg-neon-rojo/10',
        text: 'text-neon-rojo',
        icon: 'text-neon-rojo',
      };
  }
}

/**
 * Formatea el valor esperado para display
 */
function formatearEV(ev?: number): string {
  if (ev === undefined || ev === null) return '--';
  const signo = ev >= 0 ? '+' : '';
  return `${signo}${(ev * 100).toFixed(1)}%`;
}

/**
 * Obtiene el color del EV
 */
function getColorEV(ev?: number): string {
  if (ev === undefined || ev === null) return 'text-texto-terciario';
  if (ev >= 0.05) return 'text-neon-verde texto-glow-verde';
  if (ev >= 0) return 'text-neon-verde';
  if (ev >= -0.05) return 'text-neon-rojo/80';
  return 'text-neon-rojo';
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE COMPACTO
// ══════════════════════════════════════════════════════════════

function TarjetaRecomendacionCompacta({
  recomendacion,
  onRegistrar,
  destacada,
  className,
}: Omit<PropsTarjetaRecomendacion, 'compacta'>) {
  const colores = getColorPrincipal(recomendacion.confianza);
  const etiqueta = ETIQUETAS_MERCADOS[recomendacion.mercado];
  const esOver = recomendacion.lado === 'OVER';

  return (
    <div
      className={clsx(
        'p-3 rounded-lg border transition-all duration-300',
        'bg-futurista-oscuro/50 backdrop-blur-sm',
        colores.border,
        destacada && colores.glow,
        'hover:border-neon-cyan/30',
        className
      )}
    >
      <div className="flex items-center justify-between gap-3">
        {/* Info principal */}
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {/* Icono del lado */}
          <div
            className={clsx(
              'p-2 rounded-lg',
              esOver ? 'bg-neon-verde/10' : 'bg-neon-rojo/10'
            )}
          >
            {esOver ? (
              <TrendingUp size={20} className="text-neon-verde" />
            ) : (
              <TrendingDown size={20} className="text-neon-rojo" />
            )}
          </div>

          {/* Texto */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span
                className={clsx(
                  'font-semibold',
                  esOver ? 'text-neon-verde' : 'text-neon-rojo'
                )}
              >
                {recomendacion.lado} {recomendacion.linea}
              </span>
              <BadgeConfianza nivel={recomendacion.confianza} tamano="sm" mostrarEtiqueta={false} />
            </div>
            <span className="text-xs text-texto-terciario truncate block">
              {etiqueta}
            </span>
          </div>

          {/* Probabilidad */}
          <div className="text-right">
            <div className="font-mono font-bold text-neon-cyan">
              {(recomendacion.probabilidad * 100).toFixed(1)}%
            </div>
            {recomendacion.valorEsperado !== undefined && (
              <div className={clsx('text-xs font-mono', getColorEV(recomendacion.valorEsperado))}>
                EV: {formatearEV(recomendacion.valorEsperado)}
              </div>
            )}
          </div>
        </div>

        {/* Botón registrar */}
        {onRegistrar && (
          <button
            onClick={onRegistrar}
            className={clsx(
              'p-2 rounded-lg border transition-all',
              'border-neon-cyan/30 text-neon-cyan',
              'hover:bg-neon-cyan/10 hover:border-neon-cyan/50'
            )}
            title="Registrar apuesta"
          >
            <BookmarkPlus size={18} />
          </button>
        )}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Tarjeta de recomendación de apuesta
 */
export function TarjetaRecomendacion({
  recomendacion,
  onRegistrar,
  compacta = false,
  destacada = false,
  className,
}: PropsTarjetaRecomendacion) {
  // Versión compacta
  if (compacta) {
    return (
      <TarjetaRecomendacionCompacta
        recomendacion={recomendacion}
        onRegistrar={onRegistrar}
        destacada={destacada}
        className={className}
      />
    );
  }

  const colores = getColorPrincipal(recomendacion.confianza);
  const etiqueta = ETIQUETAS_MERCADOS[recomendacion.mercado];
  const esOver = recomendacion.lado === 'OVER';
  const tieneEV = recomendacion.valorEsperado !== undefined;
  const evPositivo = (recomendacion.valorEsperado ?? 0) >= 0;

  return (
    <Tarjeta
      className={clsx(
        'relative overflow-hidden transition-all duration-300',
        colores.border,
        destacada && colores.glow,
        className
      )}
    >
      {/* Efecto de brillo superior */}
      <div
        className={clsx(
          'absolute top-0 left-0 right-0 h-px',
          'bg-gradient-to-r from-transparent to-transparent',
          recomendacion.confianza === 'MUY_ALTA' && 'via-neon-verde/80',
          recomendacion.confianza === 'ALTA' && 'via-neon-verde/50',
          recomendacion.confianza === 'MEDIA' && 'via-neon-amarillo/50',
          recomendacion.confianza === 'BAJA' && 'via-neon-rojo/30',
          recomendacion.confianza === 'MUY_BAJA' && 'via-neon-rojo/50'
        )}
      />

      {/* Icono decorativo */}
      {destacada && (
        <div className="absolute top-3 right-3">
          <Sparkles size={20} className={colores.icon} />
        </div>
      )}

      {/* Encabezado: Mercado y Confianza */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <span className="text-xs text-texto-terciario uppercase tracking-wider">
            {etiqueta}
          </span>
          <div className="flex items-center gap-3 mt-1">
            <BadgeConfianza nivel={recomendacion.confianza} tamano="md" />
          </div>
        </div>
      </div>

      {/* Apuesta recomendada */}
      <div
        className={clsx(
          'p-4 rounded-xl border mb-4',
          esOver
            ? 'bg-gradiente-over border-neon-verde/30'
            : 'bg-gradiente-under border-neon-rojo/30'
        )}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {esOver ? (
              <TrendingUp size={32} className="text-neon-verde" />
            ) : (
              <TrendingDown size={32} className="text-neon-rojo" />
            )}
            <div>
              <div
                className={clsx(
                  'text-2xl font-futurista font-bold tracking-wider',
                  esOver ? 'text-neon-verde texto-glow-verde' : 'text-neon-rojo texto-glow-rojo'
                )}
              >
                {recomendacion.lado}
              </div>
              <div className="text-3xl font-mono font-bold text-texto-principal">
                {recomendacion.linea.toFixed(1)}
              </div>
            </div>
          </div>

          {/* Probabilidad grande */}
          <div className="text-right">
            <div className="text-4xl font-mono font-bold text-neon-cyan texto-glow-cyan">
              {(recomendacion.probabilidad * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-texto-terciario">Probabilidad</div>
          </div>
        </div>
      </div>

      {/* Métricas */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {/* Probabilidad precisa */}
        <div className="text-center p-3 rounded-lg bg-futurista-oscuro/30">
          <div className="flex items-center justify-center gap-1 text-texto-terciario mb-1">
            <Percent size={12} />
            <span className="text-xs uppercase tracking-wider">Prob.</span>
          </div>
          <div className="text-lg font-mono font-bold text-neon-cyan">
            {(recomendacion.probabilidad * 100).toFixed(1)}%
          </div>
        </div>

        {/* Valor Esperado */}
        <div className="text-center p-3 rounded-lg bg-futurista-oscuro/30">
          <div className="flex items-center justify-center gap-1 text-texto-terciario mb-1">
            <Calculator size={12} />
            <span className="text-xs uppercase tracking-wider">EV</span>
          </div>
          <div className={clsx('text-lg font-mono font-bold', getColorEV(recomendacion.valorEsperado))}>
            {formatearEV(recomendacion.valorEsperado)}
          </div>
        </div>

        {/* Indicador de confianza */}
        <div className="text-center p-3 rounded-lg bg-futurista-oscuro/30">
          <div className="flex items-center justify-center gap-1 text-texto-terciario mb-1">
            <Target size={12} />
            <span className="text-xs uppercase tracking-wider">Confianza</span>
          </div>
          <div className={clsx('text-lg font-mono font-bold', colores.text)}>
            {recomendacion.confianza.replace('_', ' ')}
          </div>
        </div>
      </div>

      {/* Razón */}
      <div className="p-3 rounded-lg bg-futurista-negro/30 border border-neon-cyan/10 mb-4">
        <div className="flex items-start gap-2">
          <AlertCircle size={14} className="text-neon-cyan mt-0.5 flex-shrink-0" />
          <p className="text-sm text-texto-secundario">{recomendacion.razon}</p>
        </div>
      </div>

      {/* Botón registrar */}
      {onRegistrar && (
        <Boton
          variante="primario"
          anchoCompleto
          onClick={onRegistrar}
          iconoInicio={<BookmarkPlus size={18} />}
        >
          Registrar Apuesta
        </Boton>
      )}

      {/* Advertencia EV negativo */}
      {tieneEV && !evPositivo && (
        <div className="mt-3 flex items-center gap-2 text-xs text-neon-rojo/80">
          <AlertCircle size={12} />
          <span>EV negativo: considera revisar antes de apostar</span>
        </div>
      )}
    </Tarjeta>
  );
}

// ══════════════════════════════════════════════════════════════
// VARIANTES EXPORTADAS
// ══════════════════════════════════════════════════════════════

/**
 * Lista de recomendaciones
 */
export function ListaRecomendaciones({
  recomendaciones,
  onRegistrar,
  maxItems = 5,
  className,
}: {
  recomendaciones: RecomendacionApuesta[];
  onRegistrar?: (recomendacion: RecomendacionApuesta) => void;
  maxItems?: number;
  className?: string;
}) {
  const items = recomendaciones.slice(0, maxItems);

  if (items.length === 0) {
    return (
      <div className={clsx('text-center py-8 text-texto-terciario', className)}>
        <Target size={48} className="mx-auto mb-3 opacity-50" />
        <p>No hay recomendaciones disponibles</p>
      </div>
    );
  }

  return (
    <div className={clsx('space-y-3', className)}>
      {items.map((rec, idx) => (
        <TarjetaRecomendacion
          key={`${rec.mercado}-${rec.linea}-${idx}`}
          recomendacion={rec}
          onRegistrar={onRegistrar ? () => onRegistrar(rec) : undefined}
          compacta={idx > 0}
          destacada={idx === 0}
        />
      ))}
      {recomendaciones.length > maxItems && (
        <div className="text-center text-sm text-texto-terciario py-2">
          +{recomendaciones.length - maxItems} recomendaciones más
        </div>
      )}
    </div>
  );
}
