/**
 * GraficoDistribucion.tsx — Gráfico de distribución normal
 *
 * Muestra una curva de campana (distribución normal) con:
 * - Línea vertical para la línea de apuestas
 * - Áreas sombreadas para over/under
 * - Diseño SVG futurista
 */

import { useMemo, useCallback } from 'react';
import { clsx } from 'clsx';
import { Tarjeta } from '../atomos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsGraficoDistribucion {
  /** Media de la distribución */
  media: number;
  /** Desviación estándar */
  std: number;
  /** Línea de apuestas */
  linea: number;
  /** Lado a resaltar */
  lado?: 'OVER' | 'UNDER';
  /** Altura del gráfico en píxeles */
  altura?: number;
  /** Clase CSS adicional */
  className?: string;
  /** Mostrar leyenda */
  mostrarLeyenda?: boolean;
  /** Título del gráfico */
  titulo?: string;
}

// ══════════════════════════════════════════════════════════════
// CONSTANTES
// ══════════════════════════════════════════════════════════════

const PADDING_X = 40;
const PADDING_Y = 30;
const PUNTOS_CURVA = 100;

// Colores
const COLOR_CURVA = '#22d3ee'; // neon-cyan
const COLOR_OVER = '#10b981'; // neon-verde
const COLOR_UNDER = '#ec4899'; // neon-magenta
const COLOR_LINEA = '#f59e0b'; // neon-amarillo
const COLOR_MEDIA = '#6366f1'; // neon-azul
const COLOR_TEXTO = '#9AA4B2'; // texto-secundario
const COLOR_GRID = 'rgba(34, 211, 238, 0.1)';

// ══════════════════════════════════════════════════════════════
// HELPERS MATEMÁTICOS
// ══════════════════════════════════════════════════════════════

/**
 * Función de densidad de probabilidad normal
 */
function pdf(x: number, media: number, std: number): number {
  const coeficiente = 1 / (std * Math.sqrt(2 * Math.PI));
  const exponente = -0.5 * Math.pow((x - media) / std, 2);
  return coeficiente * Math.exp(exponente);
}

/**
 * Función de distribución acumulada normal (aproximación)
 */
function cdf(x: number, media: number, std: number): number {
  const z = (x - media) / std;
  const t = 1 / (1 + 0.2316419 * Math.abs(z));
  const d = 0.3989423 * Math.exp(-z * z / 2);
  const p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
  return z > 0 ? 1 - p : p;
}

/**
 * Genera puntos para la curva de distribución
 */
function generarPuntosCurva(
  media: number,
  std: number,
  xMin: number,
  xMax: number,
  numPuntos: number
): Array<{ x: number; y: number }> {
  const puntos: Array<{ x: number; y: number }> = [];
  const paso = (xMax - xMin) / (numPuntos - 1);

  for (let i = 0; i < numPuntos; i++) {
    const x = xMin + i * paso;
    const y = pdf(x, media, std);
    puntos.push({ x, y });
  }

  return puntos;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Gráfico de distribución normal con línea de apuestas y áreas sombreadas
 */
export function GraficoDistribucion({
  media,
  std,
  linea,
  lado,
  altura = 240,
  className,
  mostrarLeyenda = true,
  titulo,
}: PropsGraficoDistribucion) {
  // Calcular dimensiones del gráfico
  const ancho = 400; // Ancho base (se escala con viewBox)
  const areaAncho = ancho - PADDING_X * 2;
  const areaAltura = altura - PADDING_Y * 2;

  // Calcular rango del eje X (3 desviaciones estándar)
  const stdSafe = Math.max(std, 0.5);
  const xMin = media - 3.5 * stdSafe;
  const xMax = media + 3.5 * stdSafe;

  // Generar puntos de la curva
  const puntosCurva = useMemo(
    () => generarPuntosCurva(media, stdSafe, xMin, xMax, PUNTOS_CURVA),
    [media, stdSafe, xMin, xMax]
  );

  // Calcular escala
  const yMax = useMemo(() => {
    return Math.max(...puntosCurva.map((p) => p.y)) * 1.1;
  }, [puntosCurva]);

  // Funciones de transformación
  const transformarX = useCallback((x: number): number => {
    return PADDING_X + ((x - xMin) / (xMax - xMin)) * areaAncho;
  }, [xMin, xMax, areaAncho]);

  const transformarY = useCallback((y: number): number => {
    return PADDING_Y + areaAltura - (y / yMax) * areaAltura;
  }, [areaAltura, yMax]);

  // Generar path de la curva
  const pathCurva = useMemo(() => {
    return puntosCurva
      .map((p, i) => {
        const x = transformarX(p.x);
        const y = transformarY(p.y);
        return i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
      })
      .join(' ');
  }, [puntosCurva, transformarX, transformarY]);

  // Generar path del área sombreada (over o under)
  const pathArea = useMemo(() => {
    if (!lado) return '';

    const lineaX = transformarX(linea);
    const baseY = transformarY(0);
    let areaPath = '';

    if (lado === 'OVER') {
      // Área desde la línea hasta el final
      const puntosOver = puntosCurva.filter((p) => p.x >= linea);
      if (puntosOver.length > 0) {
        areaPath = `M ${lineaX} ${baseY}`;
        puntosOver.forEach((p) => {
          areaPath += ` L ${transformarX(p.x)} ${transformarY(p.y)}`;
        });
        areaPath += ` L ${transformarX(xMax)} ${baseY} Z`;
      }
    } else {
      // Área desde el inicio hasta la línea
      const puntosUnder = puntosCurva.filter((p) => p.x <= linea);
      if (puntosUnder.length > 0) {
        areaPath = `M ${transformarX(xMin)} ${baseY}`;
        puntosUnder.forEach((p) => {
          areaPath += ` L ${transformarX(p.x)} ${transformarY(p.y)}`;
        });
        areaPath += ` L ${lineaX} ${baseY} Z`;
      }
    }

    return areaPath;
  }, [puntosCurva, linea, lado, xMin, xMax, transformarX, transformarY]);

  // Calcular probabilidades
  const probabilidades = useMemo(() => {
    const probUnder = cdf(linea, media, stdSafe);
    const probOver = 1 - probUnder;
    return { over: probOver, under: probUnder };
  }, [linea, media, stdSafe]);

  // Posiciones de elementos
  const lineaXPos = transformarX(linea);
  const mediaXPos = transformarX(media);
  const baseY = transformarY(0);

  // Generar marcas del eje X
  const marcasX = useMemo(() => {
    const marcas: Array<{ valor: number; x: number }> = [];
    const rango = xMax - xMin;
    const paso = rango / 6;

    for (let i = 0; i <= 6; i++) {
      const valor = xMin + i * paso;
      marcas.push({ valor, x: transformarX(valor) });
    }

    return marcas;
  }, [xMin, xMax, transformarX]);

  return (
    <Tarjeta className={clsx('space-y-4', className)}>
      {/* Título */}
      {titulo && (
        <h4 className="text-sm font-semibold text-texto-secundario text-center uppercase tracking-wider">
          {titulo}
        </h4>
      )}

      {/* Gráfico SVG */}
      <div className="relative">
        <svg
          viewBox={`0 0 ${ancho} ${altura}`}
          className="w-full h-auto"
          style={{ maxHeight: altura }}
        >
          {/* Definiciones de gradientes */}
          <defs>
            <linearGradient id="gradientOver" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={COLOR_OVER} stopOpacity="0.6" />
              <stop offset="100%" stopColor={COLOR_OVER} stopOpacity="0.1" />
            </linearGradient>
            <linearGradient id="gradientUnder" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={COLOR_UNDER} stopOpacity="0.6" />
              <stop offset="100%" stopColor={COLOR_UNDER} stopOpacity="0.1" />
            </linearGradient>
            <linearGradient id="gradientCurva" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={COLOR_CURVA} stopOpacity="0.8" />
              <stop offset="50%" stopColor={COLOR_CURVA} stopOpacity="1" />
              <stop offset="100%" stopColor={COLOR_CURVA} stopOpacity="0.8" />
            </linearGradient>
            {/* Glow filter */}
            <filter id="glowCyan" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Líneas de grid verticales */}
          {marcasX.map((marca, i) => (
            <line
              key={i}
              x1={marca.x}
              y1={PADDING_Y}
              x2={marca.x}
              y2={baseY}
              stroke={COLOR_GRID}
              strokeWidth="1"
            />
          ))}

          {/* Línea base */}
          <line
            x1={PADDING_X}
            y1={baseY}
            x2={ancho - PADDING_X}
            y2={baseY}
            stroke={COLOR_TEXTO}
            strokeWidth="1"
            opacity="0.3"
          />

          {/* Área sombreada */}
          {pathArea && (
            <path
              d={pathArea}
              fill={lado === 'OVER' ? 'url(#gradientOver)' : 'url(#gradientUnder)'}
            />
          )}

          {/* Curva de distribución */}
          <path
            d={pathCurva}
            fill="none"
            stroke="url(#gradientCurva)"
            strokeWidth="2.5"
            strokeLinecap="round"
            filter="url(#glowCyan)"
          />

          {/* Línea de la media */}
          <line
            x1={mediaXPos}
            y1={PADDING_Y}
            x2={mediaXPos}
            y2={baseY}
            stroke={COLOR_MEDIA}
            strokeWidth="1.5"
            strokeDasharray="4 4"
            opacity="0.7"
          />

          {/* Línea de apuestas */}
          <line
            x1={lineaXPos}
            y1={PADDING_Y}
            x2={lineaXPos}
            y2={baseY}
            stroke={COLOR_LINEA}
            strokeWidth="2"
          />

          {/* Punto en la línea de apuestas */}
          <circle
            cx={lineaXPos}
            cy={transformarY(pdf(linea, media, stdSafe))}
            r="4"
            fill={COLOR_LINEA}
            filter="url(#glowCyan)"
          />

          {/* Etiquetas del eje X */}
          {marcasX.map((marca, i) => (
            <text
              key={i}
              x={marca.x}
              y={baseY + 18}
              textAnchor="middle"
              fill={COLOR_TEXTO}
              fontSize="10"
              fontFamily="monospace"
            >
              {marca.valor.toFixed(1)}
            </text>
          ))}

          {/* Etiqueta de la media */}
          <text
            x={mediaXPos}
            y={PADDING_Y - 8}
            textAnchor="middle"
            fill={COLOR_MEDIA}
            fontSize="10"
            fontWeight="bold"
          >
            Media: {media.toFixed(2)}
          </text>

          {/* Etiqueta de la línea */}
          <text
            x={lineaXPos}
            y={PADDING_Y - 8}
            textAnchor="middle"
            fill={COLOR_LINEA}
            fontSize="10"
            fontWeight="bold"
          >
            Linea: {linea.toFixed(1)}
          </text>

          {/* Probabilidades en las áreas */}
          {lado && (
            <>
              {lado === 'OVER' && (
                <text
                  x={lineaXPos + (ancho - PADDING_X - lineaXPos) / 2}
                  y={altura / 2}
                  textAnchor="middle"
                  fill={COLOR_OVER}
                  fontSize="14"
                  fontWeight="bold"
                >
                  {(probabilidades.over * 100).toFixed(1)}%
                </text>
              )}
              {lado === 'UNDER' && (
                <text
                  x={PADDING_X + (lineaXPos - PADDING_X) / 2}
                  y={altura / 2}
                  textAnchor="middle"
                  fill={COLOR_UNDER}
                  fontSize="14"
                  fontWeight="bold"
                >
                  {(probabilidades.under * 100).toFixed(1)}%
                </text>
              )}
            </>
          )}
        </svg>
      </div>

      {/* Leyenda */}
      {mostrarLeyenda && (
        <div className="flex flex-wrap items-center justify-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLOR_MEDIA }} />
            <span className="text-texto-secundario">Media: {media.toFixed(2)}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLOR_LINEA }} />
            <span className="text-texto-secundario">Linea: {linea.toFixed(1)}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-texto-terciario">Std: {std.toFixed(2)}</span>
          </div>
        </div>
      )}

      {/* Probabilidades detalladas */}
      <div className="grid grid-cols-2 gap-4 pt-2 border-t border-neon-cyan/10">
        <div
          className={clsx(
            'p-3 rounded-lg text-center transition-all',
            lado === 'UNDER'
              ? 'bg-neon-magenta/10 border border-neon-magenta/30'
              : 'bg-futurista-medio/30'
          )}
        >
          <p className="text-xs text-texto-terciario uppercase tracking-wider mb-1">Under {linea}</p>
          <p
            className={clsx(
              'text-lg font-mono font-bold',
              lado === 'UNDER' ? 'text-neon-magenta' : 'text-texto-secundario'
            )}
          >
            {(probabilidades.under * 100).toFixed(1)}%
          </p>
        </div>
        <div
          className={clsx(
            'p-3 rounded-lg text-center transition-all',
            lado === 'OVER'
              ? 'bg-neon-verde/10 border border-neon-verde/30'
              : 'bg-futurista-medio/30'
          )}
        >
          <p className="text-xs text-texto-terciario uppercase tracking-wider mb-1">Over {linea}</p>
          <p
            className={clsx(
              'text-lg font-mono font-bold',
              lado === 'OVER' ? 'text-neon-verde' : 'text-texto-secundario'
            )}
          >
            {(probabilidades.over * 100).toFixed(1)}%
          </p>
        </div>
      </div>
    </Tarjeta>
  );
}
