/**
 * PanelAnalisisFutbol.tsx — Panel principal de análisis de fútbol
 *
 * Muestra análisis completo por categorías (CORNERS, GOLES, DISPAROS) con tabs.
 * Diseño futurista glassmorphism con efectos neón.
 */

import { useState, useMemo } from 'react';
import { clsx } from 'clsx';
import {
  CornerUpRight,
  Target,
  Crosshair,
  Download,
  TrendingUp,
  TrendingDown,
  Clock,
} from 'lucide-react';
import { Tarjeta, Boton } from '../atomos';
import { IndicadorMercadoFutbol, BadgeConfianza } from '../moleculas';
import {
  AnalisisFutbolResponse,
  PrediccionMercadoFutbol,
  TipoMercadoFutbol,
  CategoriaMercado,
  ETIQUETAS_MERCADOS,
  MERCADOS_CORNERS,
  MERCADOS_GOLES,
  MERCADOS_DISPAROS,
} from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsPanelAnalisisFutbol {
  /** Respuesta del análisis de fútbol */
  analisis: AnalisisFutbolResponse;
  /** Callback al registrar una apuesta */
  onRegistrarApuesta?: (mercado: TipoMercadoFutbol, linea: number, lado: 'OVER' | 'UNDER') => void;
  /** Callback para exportar datos */
  onExportar?: () => void;
  /** Clase CSS adicional */
  className?: string;
}

interface TabConfig {
  id: CategoriaMercado;
  label: string;
  icon: typeof CornerUpRight;
  color: string;
  bgColor: string;
  borderColor: string;
  glowColor: string;
}

// ══════════════════════════════════════════════════════════════
// CONSTANTES
// ══════════════════════════════════════════════════════════════

const TABS: TabConfig[] = [
  {
    id: 'corners',
    label: 'CORNERS',
    icon: CornerUpRight,
    color: 'text-neon-cyan',
    bgColor: 'bg-neon-cyan/10',
    borderColor: 'border-neon-cyan/50',
    glowColor: 'shadow-glow-cyan',
  },
  {
    id: 'goles',
    label: 'GOLES',
    icon: Target,
    color: 'text-neon-verde',
    bgColor: 'bg-neon-verde/10',
    borderColor: 'border-neon-verde/50',
    glowColor: 'shadow-glow-verde',
  },
  {
    id: 'disparos',
    label: 'DISPAROS',
    icon: Crosshair,
    color: 'text-neon-amarillo',
    bgColor: 'bg-neon-amarillo/10',
    borderColor: 'border-neon-amarillo/50',
    glowColor: 'shadow-glow-amarillo',
  },
];

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

/**
 * Obtiene los mercados por categoría del análisis
 */
function getMercadosCategoria(
  analisis: AnalisisFutbolResponse,
  categoria: CategoriaMercado
): Record<string, PrediccionMercadoFutbol> {
  switch (categoria) {
    case 'corners':
      return analisis.mercadosCorners;
    case 'goles':
      return analisis.mercadosGoles;
    case 'disparos':
      return analisis.mercadosDisparos;
    default:
      return {};
  }
}

/**
 * Obtiene los tipos de mercado por categoría
 */
function getMercadosTipo(categoria: CategoriaMercado): TipoMercadoFutbol[] {
  switch (categoria) {
    case 'corners':
      return MERCADOS_CORNERS;
    case 'goles':
      return MERCADOS_GOLES;
    case 'disparos':
      return MERCADOS_DISPAROS;
    default:
      return [];
  }
}

/**
 * Formatea fecha ISO a formato legible
 */
function formatearFecha(fechaISO: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleString('es-ES', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ══════════════════════════════════════════════════════════════
// SUB-COMPONENTES
// ══════════════════════════════════════════════════════════════

/**
 * Tabla de probabilidades para un mercado
 */
function TablaProbabilidades({
  prediccion,
  onSeleccionar,
}: {
  prediccion: PrediccionMercadoFutbol;
  onSeleccionar?: (linea: number, lado: 'OVER' | 'UNDER') => void;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-neon-cyan/10">
            <th className="px-3 py-2 text-left text-texto-terciario font-medium">Linea</th>
            <th className="px-3 py-2 text-center text-neon-verde font-medium">
              <div className="flex items-center justify-center gap-1">
                <TrendingUp size={12} />
                Over
              </div>
            </th>
            <th className="px-3 py-2 text-center text-neon-rojo font-medium">
              <div className="flex items-center justify-center gap-1">
                <TrendingDown size={12} />
                Under
              </div>
            </th>
            {onSeleccionar && <th className="px-3 py-2"></th>}
          </tr>
        </thead>
        <tbody>
          {prediccion.probabilidades.map((prob, idx) => {
            const esOverFavorito = prob.overCalibrada > prob.underCalibrada;
            return (
              <tr
                key={prob.linea}
                className={clsx(
                  'border-b border-futurista-medio/30 transition-colors',
                  'hover:bg-futurista-medio/20',
                  idx % 2 === 0 && 'bg-futurista-oscuro/20'
                )}
              >
                <td className="px-3 py-2 font-mono font-semibold text-neon-cyan">
                  {prob.linea.toFixed(1)}
                </td>
                <td className="px-3 py-2 text-center">
                  <div className="flex flex-col items-center">
                    <span
                      className={clsx(
                        'font-mono font-semibold',
                        esOverFavorito ? 'text-neon-verde' : 'text-texto-secundario'
                      )}
                    >
                      {(prob.overCalibrada * 100).toFixed(1)}%
                    </span>
                    {/* Barra visual */}
                    <div className="w-full h-1 mt-1 rounded-full bg-futurista-medio/30">
                      <div
                        className="h-full rounded-full bg-neon-verde/70 transition-all duration-300"
                        style={{ width: `${prob.overCalibrada * 100}%` }}
                      />
                    </div>
                  </div>
                </td>
                <td className="px-3 py-2 text-center">
                  <div className="flex flex-col items-center">
                    <span
                      className={clsx(
                        'font-mono font-semibold',
                        !esOverFavorito ? 'text-neon-rojo' : 'text-texto-secundario'
                      )}
                    >
                      {(prob.underCalibrada * 100).toFixed(1)}%
                    </span>
                    {/* Barra visual */}
                    <div className="w-full h-1 mt-1 rounded-full bg-futurista-medio/30">
                      <div
                        className="h-full rounded-full bg-neon-rojo/70 transition-all duration-300"
                        style={{ width: `${prob.underCalibrada * 100}%` }}
                      />
                    </div>
                  </div>
                </td>
                {onSeleccionar && (
                  <td className="px-3 py-2">
                    <div className="flex gap-1">
                      <button
                        onClick={() => onSeleccionar(prob.linea, 'OVER')}
                        className={clsx(
                          'px-2 py-1 text-xs rounded border transition-all',
                          'border-neon-verde/30 text-neon-verde/80',
                          'hover:bg-neon-verde/10 hover:border-neon-verde/50'
                        )}
                      >
                        O
                      </button>
                      <button
                        onClick={() => onSeleccionar(prob.linea, 'UNDER')}
                        className={clsx(
                          'px-2 py-1 text-xs rounded border transition-all',
                          'border-neon-rojo/30 text-neon-rojo/80',
                          'hover:bg-neon-rojo/10 hover:border-neon-rojo/50'
                        )}
                      >
                        U
                      </button>
                    </div>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Tarjeta de mercado individual
 */
function TarjetaMercadoItem({
  prediccion,
  onSeleccionar,
}: {
  prediccion: PrediccionMercadoFutbol;
  onSeleccionar?: (linea: number, lado: 'OVER' | 'UNDER') => void;
}) {
  const [expandido, setExpandido] = useState(false);
  const etiqueta = ETIQUETAS_MERCADOS[prediccion.mercado];

  return (
    <div
      className={clsx(
        'rounded-lg border transition-all duration-300',
        'bg-futurista-oscuro/50 backdrop-blur-sm',
        'border-neon-cyan/10 hover:border-neon-cyan/20'
      )}
    >
      {/* Header */}
      <button
        className="w-full p-4 flex items-center justify-between gap-4"
        onClick={() => setExpandido(!expandido)}
      >
        <div className="flex items-center gap-3">
          <span className="text-texto-principal font-semibold">{etiqueta}</span>
          <BadgeConfianza nivel={prediccion.confianza} tamano="sm" />
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-xs text-texto-terciario">Media</div>
            <div className="font-mono font-semibold text-neon-cyan">
              {prediccion.media.toFixed(2)}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-texto-terciario">Std</div>
            <div className="font-mono text-neon-magenta">
              ±{prediccion.std.toFixed(2)}
            </div>
          </div>
          <span
            className={clsx(
              'text-texto-terciario transition-transform',
              expandido && 'rotate-180'
            )}
          >
            ▼
          </span>
        </div>
      </button>

      {/* Contenido expandible */}
      {expandido && (
        <div className="px-4 pb-4 border-t border-neon-cyan/10">
          {/* Indicador visual */}
          <div className="py-3">
            {prediccion.probabilidades[0] && (
              <IndicadorMercadoFutbol
                mercado={prediccion.mercado}
                linea={prediccion.probabilidades[0].linea}
                probabilidadOver={prediccion.probabilidades[0].overCalibrada}
                probabilidadUnder={prediccion.probabilidades[0].underCalibrada}
                compacto
              />
            )}
          </div>

          {/* Tabla de probabilidades */}
          <TablaProbabilidades
            prediccion={prediccion}
            onSeleccionar={
              onSeleccionar
                ? (linea, lado) => onSeleccionar(linea, lado)
                : undefined
            }
          />
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Panel principal de análisis de fútbol con navegación por tabs
 */
export function PanelAnalisisFutbol({
  analisis,
  onRegistrarApuesta,
  onExportar,
  className,
}: PropsPanelAnalisisFutbol) {
  const [tabActivo, setTabActivo] = useState<CategoriaMercado>('corners');

  // Obtener mercados de la categoría activa
  const mercadosActivos = useMemo(() => {
    const mercadosCategoria = getMercadosCategoria(analisis, tabActivo);
    const tiposMercado = getMercadosTipo(tabActivo);

    // Filtrar y ordenar mercados disponibles
    return tiposMercado
      .filter((tipo) => mercadosCategoria[tipo])
      .map((tipo) => mercadosCategoria[tipo]);
  }, [analisis, tabActivo]);

  // Config del tab activo
  const tabConfig = TABS.find((t) => t.id === tabActivo) || TABS[0];

  // Handler para seleccionar apuesta
  const handleSeleccionar = (mercado: TipoMercadoFutbol, linea: number, lado: 'OVER' | 'UNDER') => {
    onRegistrarApuesta?.(mercado, linea, lado);
  };

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Header del panel */}
      <Tarjeta className="relative overflow-hidden">
        {/* Línea decorativa */}
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-neon-cyan via-neon-magenta to-neon-cyan" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Info del partido */}
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-lg font-futurista font-bold text-texto-principal">
                {analisis.partido.equipoLocalNombre}
              </span>
              <span className="text-neon-cyan font-mono">VS</span>
              <span className="text-lg font-futurista font-bold text-texto-principal">
                {analisis.partido.equipoVisitanteNombre}
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm text-texto-secundario">
              <div className="flex items-center gap-1">
                <Clock size={14} className="text-neon-magenta" />
                <span>{formatearFecha(analisis.timestampAnalisis)}</span>
              </div>
              <span className="text-texto-terciario">
                v{analisis.modeloVersion}
              </span>
            </div>
          </div>

          {/* Botón exportar */}
          {onExportar && (
            <Boton
              variante="secundario"
              tamano="sm"
              onClick={onExportar}
              iconoInicio={<Download size={16} />}
            >
              Exportar
            </Boton>
          )}
        </div>
      </Tarjeta>

      {/* Tabs de navegación */}
      <div className="flex gap-2 p-1 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = tab.id === tabActivo;
          const mercadosCategoria = getMercadosCategoria(analisis, tab.id);
          const numMercados = Object.keys(mercadosCategoria).length;

          return (
            <button
              key={tab.id}
              onClick={() => setTabActivo(tab.id)}
              className={clsx(
                'flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg',
                'font-futurista uppercase tracking-wider text-sm',
                'transition-all duration-300',
                isActive
                  ? `${tab.bgColor} ${tab.borderColor} border ${tab.color} ${tab.glowColor}`
                  : 'text-texto-secundario hover:text-texto-principal hover:bg-futurista-medio/30'
              )}
            >
              <Icon size={18} />
              <span>{tab.label}</span>
              <span
                className={clsx(
                  'px-1.5 py-0.5 rounded text-xs font-mono',
                  isActive
                    ? 'bg-futurista-negro/30 text-inherit'
                    : 'bg-futurista-medio/30 text-texto-terciario'
                )}
              >
                {numMercados}
              </span>
            </button>
          );
        })}
      </div>

      {/* Contenido de mercados */}
      <div className="space-y-3">
        {mercadosActivos.length === 0 ? (
          <Tarjeta className="text-center py-8">
            <tabConfig.icon size={48} className="mx-auto text-texto-terciario mb-4" />
            <p className="text-texto-secundario">
              No hay mercados disponibles para {tabConfig.label.toLowerCase()}
            </p>
          </Tarjeta>
        ) : (
          mercadosActivos.map((prediccion) => (
            <TarjetaMercadoItem
              key={prediccion.mercado}
              prediccion={prediccion}
              onSeleccionar={
                onRegistrarApuesta
                  ? (linea, lado) => handleSeleccionar(prediccion.mercado, linea, lado)
                  : undefined
              }
            />
          ))
        )}
      </div>

      {/* Resumen rápido de recomendaciones */}
      {analisis.recomendaciones.length > 0 && (
        <Tarjeta className="border-neon-verde/20">
          <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-neon-verde mb-3 flex items-center gap-2">
            <span className="w-8 h-px bg-gradient-to-r from-neon-verde to-transparent" />
            Top Recomendaciones ({tabConfig.label})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {analisis.recomendaciones
              .filter((rec) => {
                const tiposMercado = getMercadosTipo(tabActivo);
                return tiposMercado.includes(rec.mercado);
              })
              .slice(0, 3)
              .map((rec, idx) => (
                <div
                  key={`${rec.mercado}-${rec.linea}-${idx}`}
                  className={clsx(
                    'p-3 rounded-lg border',
                    'bg-futurista-oscuro/50',
                    'border-neon-verde/20'
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-texto-terciario">
                      {ETIQUETAS_MERCADOS[rec.mercado]}
                    </span>
                    <BadgeConfianza nivel={rec.confianza} tamano="sm" mostrarEtiqueta={false} />
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={clsx(
                        'px-2 py-1 rounded text-sm font-semibold',
                        rec.lado === 'OVER'
                          ? 'bg-neon-verde/20 text-neon-verde'
                          : 'bg-neon-rojo/20 text-neon-rojo'
                      )}
                    >
                      {rec.lado} {rec.linea}
                    </span>
                    <span className="font-mono text-neon-cyan">
                      {(rec.probabilidad * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
          </div>
        </Tarjeta>
      )}
    </div>
  );
}
