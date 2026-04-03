/**
 * PanelComparacionPrediccion.tsx — Panel de comparación Base vs Ajustada
 *
 * Muestra lado a lado la predicción BASE vs la predicción AJUSTADA,
 * permitiendo al usuario ver el impacto de los ajustes contextuales.
 */

import { useMemo } from 'react';
import { Activity, ArrowRight, TrendingUp, TrendingDown, Check, AlertTriangle } from 'lucide-react';
import { clsx } from 'clsx';
import { Tarjeta } from '../atomos';
import type { NivelConfianza } from '../../tipos/analisis';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface DatosPrediccion {
  media: number;
  probabilidadOver: number;
  probabilidadUnder: number;
}

interface PropsPanelComparacion {
  /** Datos de la predicción base (sin ajustes) */
  prediccionBase: DatosPrediccion;
  /** Datos de la predicción ajustada (con contexto) */
  prediccionAjustada: DatosPrediccion;
  /** Línea analizada */
  linea: number;
  /** Nivel de confianza base */
  confianzaBase: NivelConfianza | string;
  /** Nivel de confianza ajustada */
  confianzaAjustada: NivelConfianza | string;
  /** Clase CSS adicional */
  className?: string;
  /** Unidad semántica a mostrar */
  unidadLabel?: string;
}

// ══════════════════════════════════════════════════════════════
// UTILIDADES
// ══════════════════════════════════════════════════════════════

/**
 * Formatea un porcentaje para mostrar
 */
function formatearPorcentaje(valor: number): string {
  return `${(valor * 100).toFixed(1)}%`;
}

/**
 * Formatea la diferencia de puntos con signo
 */
function formatearDiferenciaPuntos(diferencia: number, unidadLabel: string): string {
  const signo = diferencia >= 0 ? '+' : '';
  return `${signo}${diferencia.toFixed(1)} ${unidadLabel}`;
}

/**
 * Formatea la diferencia de porcentaje con signo
 */
function formatearDiferenciaPorcentaje(diferencia: number): string {
  const signo = diferencia >= 0 ? '+' : '';
  return `${signo}${(diferencia * 100).toFixed(1)}%`;
}

/**
 * Obtiene el color según la confianza
 */
function obtenerColorConfianza(confianza: string): string {
  switch (confianza.toUpperCase()) {
    case 'ALTA':
      return 'text-neon-verde';
    case 'MEDIA':
      return 'text-neon-amarillo';
    case 'BAJA':
      return 'text-neon-rojo';
    default:
      return 'text-texto-secundario';
  }
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

export function PanelComparacionPrediccion({
  prediccionBase,
  prediccionAjustada,
  linea,
  confianzaBase,
  confianzaAjustada,
  className,
  unidadLabel = 'unidades',
}: PropsPanelComparacion) {
  // Cálculos derivados
  const datos = useMemo(() => {
    const diferenciaPuntos = prediccionAjustada.media - prediccionBase.media;
    const diferenciaProbOver =
      prediccionAjustada.probabilidadOver - prediccionBase.probabilidadOver;
    const diferenciaProbUnder =
      prediccionAjustada.probabilidadUnder - prediccionBase.probabilidadUnder;

    // Determinar recomendaciones
    const recomendacionBase =
      prediccionBase.probabilidadOver > 0.5 ? 'OVER' : 'UNDER';
    const recomendacionAjustada =
      prediccionAjustada.probabilidadOver > 0.5 ? 'OVER' : 'UNDER';
    const recomendacionCambio = recomendacionBase !== recomendacionAjustada;

    // Probabilidad del lado recomendado
    const probLadoBase =
      recomendacionBase === 'OVER'
        ? prediccionBase.probabilidadOver
        : prediccionBase.probabilidadUnder;
    const probLadoAjustada =
      recomendacionAjustada === 'OVER'
        ? prediccionAjustada.probabilidadOver
        : prediccionAjustada.probabilidadUnder;

    const sinAjusteReal = Math.abs(diferenciaPuntos) < 1e-9
      && Math.abs(diferenciaProbOver) < 1e-9
      && Math.abs(diferenciaProbUnder) < 1e-9;

    return {
      diferenciaPuntos,
      diferenciaProbOver,
      diferenciaProbUnder,
      recomendacionBase,
      recomendacionAjustada,
      recomendacionCambio,
      probLadoBase,
      probLadoAjustada,
      sinAjusteReal,
    };
  }, [prediccionBase, prediccionAjustada]);

  return (
    <Tarjeta className={clsx('space-y-4', className)} padding="md">
      {/* Encabezado */}
      <div className="flex items-center gap-2">
        <Activity className="w-5 h-5 text-neon-cyan" />
        <h3 className="text-lg font-futurista text-texto-principal tracking-wide">
          Impacto de Ajustes Contextuales
        </h3>
      </div>

      {/* Grid de comparación */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Columna Base */}
        <div className="p-4 rounded-lg bg-futurista-negro/50 border border-neon-cyan/20">
          <p className="text-xs uppercase tracking-widest text-texto-terciario mb-3">
            Predicción Base
          </p>

          {/* Media */}
          <div className="mb-4">
            <p className="text-xs text-texto-terciario mb-1">Media Total</p>
            <p className="text-2xl font-mono text-texto-principal">
              {prediccionBase.media.toFixed(1)}
              <span className="text-sm text-texto-terciario ml-1">{unidadLabel}</span>
            </p>
          </div>

          <div className="h-px bg-gradient-to-r from-transparent via-neon-cyan/20 to-transparent my-3" />

          {/* Probabilidades */}
          <div className="space-y-3">
            {/* OVER */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-texto-secundario">
                P(OVER {linea})
              </span>
              <span
                className={clsx(
                  'font-mono text-sm',
                  datos.recomendacionBase === 'OVER'
                    ? 'text-over-medio'
                    : 'text-texto-secundario'
                )}
              >
                {formatearPorcentaje(prediccionBase.probabilidadOver)}
              </span>
            </div>

            {/* UNDER */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-texto-secundario">
                P(UNDER {linea})
              </span>
              <span
                className={clsx(
                  'font-mono text-sm',
                  datos.recomendacionBase === 'UNDER'
                    ? 'text-under-medio'
                    : 'text-texto-secundario'
                )}
              >
                {formatearPorcentaje(prediccionBase.probabilidadUnder)}
              </span>
            </div>
          </div>

          <div className="h-px bg-gradient-to-r from-transparent via-neon-cyan/20 to-transparent my-3" />

          {/* Confianza */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-texto-terciario">Confianza</span>
            <span
              className={clsx(
                'text-sm font-semibold uppercase',
                obtenerColorConfianza(confianzaBase)
              )}
            >
              {confianzaBase}
            </span>
          </div>
        </div>

        {/* Flecha central (visible en desktop) */}
        <div className="hidden md:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
          <div className="w-10 h-10 rounded-full bg-futurista-medio border border-neon-cyan/30 flex items-center justify-center">
            <ArrowRight className="w-5 h-5 text-neon-cyan" />
          </div>
        </div>

        {/* Columna Ajustada */}
        <div className="p-4 rounded-lg bg-futurista-negro/50 border border-neon-verde/30 relative">
          <p className="text-xs uppercase tracking-widest text-neon-verde mb-3">
            Predicción Ajustada
          </p>

          {/* Media */}
          <div className="mb-4">
            <p className="text-xs text-texto-terciario mb-1">Media Total</p>
            <div className="flex items-baseline gap-2">
              <p className="text-2xl font-mono text-texto-principal">
                {prediccionAjustada.media.toFixed(1)}
                <span className="text-sm text-texto-terciario ml-1">{unidadLabel}</span>
              </p>
              <span
                className={clsx(
                  'text-sm font-mono',
                  datos.diferenciaPuntos > 0
                    ? 'text-neon-verde'
                    : datos.diferenciaPuntos < 0
                    ? 'text-neon-rojo'
                    : 'text-texto-terciario'
                )}
              >
                ({formatearDiferenciaPuntos(datos.diferenciaPuntos, unidadLabel)})
              </span>
            </div>
          </div>

          <div className="h-px bg-gradient-to-r from-transparent via-neon-verde/20 to-transparent my-3" />

          {/* Probabilidades */}
          <div className="space-y-3">
            {/* OVER */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm text-texto-secundario">
                  P(OVER {linea})
                </span>
                {datos.recomendacionAjustada === 'OVER' && (
                  <Check className="w-4 h-4 text-over-medio" />
                )}
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={clsx(
                    'font-mono text-sm',
                    datos.recomendacionAjustada === 'OVER'
                      ? 'text-over-medio'
                      : 'text-texto-secundario'
                  )}
                >
                  {formatearPorcentaje(prediccionAjustada.probabilidadOver)}
                </span>
                {datos.diferenciaProbOver !== 0 && (
                  <span
                    className={clsx(
                      'text-xs font-mono flex items-center gap-0.5',
                      datos.diferenciaProbOver > 0
                        ? 'text-neon-verde'
                        : 'text-neon-rojo'
                    )}
                  >
                    {datos.diferenciaProbOver > 0 ? (
                      <TrendingUp className="w-3 h-3" />
                    ) : (
                      <TrendingDown className="w-3 h-3" />
                    )}
                    {formatearDiferenciaPorcentaje(
                      Math.abs(datos.diferenciaProbOver)
                    )}
                  </span>
                )}
              </div>
            </div>

            {/* UNDER */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm text-texto-secundario">
                  P(UNDER {linea})
                </span>
                {datos.recomendacionAjustada === 'UNDER' && (
                  <Check className="w-4 h-4 text-under-medio" />
                )}
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={clsx(
                    'font-mono text-sm',
                    datos.recomendacionAjustada === 'UNDER'
                      ? 'text-under-medio'
                      : 'text-texto-secundario'
                  )}
                >
                  {formatearPorcentaje(prediccionAjustada.probabilidadUnder)}
                </span>
                {datos.diferenciaProbUnder !== 0 && (
                  <span
                    className={clsx(
                      'text-xs font-mono flex items-center gap-0.5',
                      datos.diferenciaProbUnder > 0
                        ? 'text-neon-verde'
                        : 'text-neon-rojo'
                    )}
                  >
                    {datos.diferenciaProbUnder > 0 ? (
                      <TrendingUp className="w-3 h-3" />
                    ) : (
                      <TrendingDown className="w-3 h-3" />
                    )}
                    {formatearDiferenciaPorcentaje(
                      Math.abs(datos.diferenciaProbUnder)
                    )}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="h-px bg-gradient-to-r from-transparent via-neon-verde/20 to-transparent my-3" />

          {/* Confianza */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-texto-terciario">Confianza</span>
            <div className="flex items-center gap-2">
              <span
                className={clsx(
                  'text-sm font-semibold uppercase',
                  obtenerColorConfianza(confianzaAjustada)
                )}
              >
                {confianzaAjustada}
              </span>
              {confianzaBase !== confianzaAjustada && (
                <span className="text-xs text-texto-terciario">
                  (cambió)
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {datos.sinAjusteReal && (
        <div className="p-3 rounded-lg bg-neon-cyan/10 border border-neon-cyan/30 text-sm text-texto-secundario">
          No hubo ajuste contextual real para este mercado objetivo: base y ajustada son idénticas.
        </div>
      )}

      {/* Alerta de cambio de recomendación */}
      {datos.recomendacionCambio && (
        <div className="p-3 rounded-lg bg-advertencia-600/10 border border-advertencia-500/30 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-advertencia-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-advertencia-500 font-medium">
              La recomendación cambió
            </p>
            <p className="text-sm text-texto-secundario mt-1">
              De{' '}
              <span
                className={clsx(
                  'font-semibold',
                  datos.recomendacionBase === 'OVER'
                    ? 'text-over-medio'
                    : 'text-under-medio'
                )}
              >
                {datos.recomendacionBase}
              </span>{' '}
              →{' '}
              <span
                className={clsx(
                  'font-semibold',
                  datos.recomendacionAjustada === 'OVER'
                    ? 'text-over-medio'
                    : 'text-under-medio'
                )}
              >
                {datos.recomendacionAjustada}
              </span>{' '}
              ({formatearDiferenciaPorcentaje(Math.abs(datos.diferenciaProbOver))} de
              diferencia)
            </p>
          </div>
        </div>
      )}
    </Tarjeta>
  );
}
