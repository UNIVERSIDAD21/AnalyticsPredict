/**
 * SelectorPartido.tsx — Selector de partido para análisis
 *
 * CRÍTICO: Este componente permite seleccionar un partido real
 * para que las predicciones se registren correctamente.
 *
 * Sin selección de partido, las predicciones NO se registran.
 *
 * Mejoras v2:
 * - Nivel 1: Tooltip rápido con ícono de ayuda
 * - Nivel 2: Panel informativo colapsable
 * - Nivel 3: Estado visual claro (REGISTRABLE vs SOLO CÁLCULO)
 */

import { useEffect, useState, useMemo } from 'react';
import {
  Calendar,
  AlertTriangle,
  RefreshCw,
  HelpCircle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  BookOpen,
  BarChart3,
  History,
  Target,
} from 'lucide-react';
import { PartidoResumen } from '../../tipos';
import { obtenerPartidosProximos, formatearFechaPartido } from '../../servicios';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsSelectorPartido {
  /** Partido seleccionado actualmente */
  partidoSeleccionado: PartidoResumen | null;
  /** Callback cuando se selecciona un partido */
  onSeleccionar: (partido: PartidoResumen | null) => void;
  /** Deshabilitado */
  deshabilitado?: boolean;
  /** Días hacia adelante para buscar partidos */
  diasAdelante?: number;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

export function SelectorPartido({
  partidoSeleccionado,
  onSeleccionar,
  deshabilitado = false,
  diasAdelante = 7,
}: PropsSelectorPartido) {
  const [partidos, setPartidos] = useState<PartidoResumen[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandido, setExpandido] = useState(false);
  const [mostrarInfo, setMostrarInfo] = useState(false);
  const [mostrarTooltip, setMostrarTooltip] = useState(false);

  // Cargar partidos próximos
  const cargarPartidos = async () => {
    setCargando(true);
    setError(null);
    try {
      const lista = await obtenerPartidosProximos(diasAdelante);
      setPartidos(lista);
    } catch (err) {
      setError('No se pudieron cargar los partidos');
      console.error(err);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarPartidos();
  }, [diasAdelante]);

  // Agrupar partidos por fecha
  const partidosPorFecha = useMemo(() => {
    const grupos = new Map<string, PartidoResumen[]>();
    for (const partido of partidos) {
      const fecha = partido.fecha_partido;
      if (!grupos.has(fecha)) {
        grupos.set(fecha, []);
      }
      grupos.get(fecha)!.push(partido);
    }
    return grupos;
  }, [partidos]);

  const handleSeleccionar = (partido: PartidoResumen) => {
    onSeleccionar(partido);
    setExpandido(false);
  };

  const handleLimpiar = () => {
    onSeleccionar(null);
  };

  return (
    <div className="space-y-2">
      {/* Etiqueta con tooltip (Nivel 1) */}
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold uppercase tracking-wider text-texto-secundario flex items-center gap-2">
          <Calendar className="w-4 h-4 text-neon-cyan" />
          Partido a analizar
          {/* Ícono de ayuda con tooltip */}
          <div className="relative">
            <button
              type="button"
              onMouseEnter={() => setMostrarTooltip(true)}
              onMouseLeave={() => setMostrarTooltip(false)}
              onClick={() => setMostrarInfo(!mostrarInfo)}
              className="text-neon-cyan/60 hover:text-neon-cyan transition-colors"
            >
              <HelpCircle className="w-4 h-4" />
            </button>
            {/* Tooltip rápido */}
            {mostrarTooltip && (
              <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 z-50">
                <div className="bg-futurista-medio border border-neon-cyan/30 rounded-lg px-3 py-2 shadow-lg min-w-[200px]">
                  <p className="text-xs text-texto-principal whitespace-nowrap">
                    Selecciona un partido real para que el sistema aprenda de tus análisis
                  </p>
                </div>
                <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-neon-cyan/30" />
              </div>
            )}
          </div>
        </label>
        <button
          type="button"
          onClick={cargarPartidos}
          disabled={cargando || deshabilitado}
          className="text-xs text-neon-cyan hover:text-neon-cyan/80 flex items-center gap-1"
        >
          <RefreshCw className={`w-3 h-3 ${cargando ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {/* Panel informativo colapsable (Nivel 2) */}
      {mostrarInfo && (
        <div className="p-4 rounded-lg bg-futurista-oscuro/80 border border-neon-cyan/20 space-y-3 animate-entrada">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-neon-cyan flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              ¿Por qué importa seleccionar un partido?
            </h4>
            <button
              type="button"
              onClick={() => setMostrarInfo(false)}
              className="text-texto-terciario hover:text-texto-secundario"
            >
              <ChevronUp className="w-4 h-4" />
            </button>
          </div>

          <div className="grid gap-3">
            {/* Con partido */}
            <div className="flex items-start gap-3 p-3 rounded-lg bg-neon-verde/5 border border-neon-verde/20">
              <CheckCircle className="w-5 h-5 text-neon-verde flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-neon-verde mb-1">Con partido seleccionado</p>
                <ul className="text-xs text-texto-secundario space-y-1">
                  <li className="flex items-center gap-2">
                    <Target className="w-3 h-3 text-neon-cyan" />
                    Se registra en la base de datos
                  </li>
                  <li className="flex items-center gap-2">
                    <BarChart3 className="w-3 h-3 text-neon-cyan" />
                    Se compara con el resultado real (calibración)
                  </li>
                  <li className="flex items-center gap-2">
                    <History className="w-3 h-3 text-neon-cyan" />
                    Aparece en historial para auditar predicciones
                  </li>
                </ul>
              </div>
            </div>

            {/* Sin partido */}
            <div className="flex items-start gap-3 p-3 rounded-lg bg-neon-amarillo/5 border border-neon-amarillo/20">
              <AlertTriangle className="w-5 h-5 text-neon-amarillo flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-neon-amarillo mb-1">Sin partido (cálculo teórico)</p>
                <ul className="text-xs text-texto-secundario space-y-1">
                  <li>No se guarda en la base de datos</li>
                  <li>No se puede comparar con el resultado</li>
                  <li>No entrena el modelo ni aparece en historial</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Estado visual del partido (Nivel 3) */}
      {partidoSeleccionado ? (
        /* ESTADO: Partido seleccionado - REGISTRABLE */
        <div className="p-4 rounded-lg bg-neon-verde/10 border border-neon-verde/30 shadow-[0_0_15px_rgba(0,255,136,0.1)]">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-neon-verde/20 flex items-center justify-center flex-shrink-0">
                <CheckCircle className="w-5 h-5 text-neon-verde" />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-bold uppercase tracking-wider text-neon-verde">
                    Registrable
                  </span>
                </div>
                <p className="text-sm font-semibold text-texto-principal">
                  {partidoSeleccionado.equipo_local_nombre} vs{' '}
                  {partidoSeleccionado.equipo_visitante_nombre}
                </p>
                <p className="text-xs text-texto-secundario">
                  {formatearFechaPartido(partidoSeleccionado.fecha_partido)} -{' '}
                  {partidoSeleccionado.temporada_nombre}
                </p>
                <p className="text-xs text-neon-verde/80 mt-1">
                  Se guardará y comparará con resultado real
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleLimpiar}
              disabled={deshabilitado}
              className="text-xs text-neon-rojo hover:text-neon-rojo/80 font-semibold"
            >
              Cambiar
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Botón para expandir/colapsar lista de partidos */}
          <button
            type="button"
            onClick={() => setExpandido(!expandido)}
            disabled={deshabilitado || cargando}
            className={`w-full p-3 rounded-lg border text-left transition-all flex items-center justify-between ${
              expandido
                ? 'bg-futurista-oscuro border-neon-cyan/30'
                : 'bg-futurista-oscuro/50 border-neon-cyan/10 hover:border-neon-cyan/30'
            }`}
          >
            <span className="text-sm text-texto-secundario">
              {cargando
                ? 'Cargando partidos...'
                : partidos.length > 0
                  ? `Seleccionar partido (${partidos.length} disponibles)`
                  : 'No hay partidos próximos'}
            </span>
            {partidos.length > 0 && (
              expandido ? (
                <ChevronUp className="w-4 h-4 text-neon-cyan" />
              ) : (
                <ChevronDown className="w-4 h-4 text-neon-cyan" />
              )
            )}
          </button>

          {/* Lista de partidos */}
          {expandido && partidos.length > 0 && (
            <div className="max-h-64 overflow-y-auto rounded-lg border border-neon-cyan/20 bg-futurista-oscuro">
              {Array.from(partidosPorFecha.entries()).map(([fecha, lista]) => (
                <div key={fecha}>
                  {/* Cabecera de fecha */}
                  <div className="sticky top-0 px-3 py-2 bg-futurista-medio border-b border-neon-cyan/10">
                    <span className="text-xs font-semibold text-neon-cyan uppercase tracking-wider">
                      {formatearFechaPartido(fecha)}
                    </span>
                  </div>
                  {/* Partidos de esa fecha */}
                  {lista.map((partido) => (
                    <button
                      key={partido.id}
                      type="button"
                      onClick={() => handleSeleccionar(partido)}
                      className="w-full px-3 py-2 text-left hover:bg-neon-cyan/10 border-b border-neon-cyan/5 last:border-b-0 transition-colors"
                    >
                      <p className="text-sm text-texto-principal">
                        {partido.equipo_local_nombre} vs {partido.equipo_visitante_nombre}
                      </p>
                      <p className="text-xs text-texto-terciario">
                        {partido.tipo_partido === 'REG'
                          ? 'Temporada Regular'
                          : partido.tipo_partido === 'POST'
                            ? 'Playoffs'
                            : 'Pretemporada'}
                      </p>
                    </button>
                  ))}
                </div>
              ))}
            </div>
          )}

          {/* ESTADO: Sin partido - SOLO CÁLCULO */}
          <div className="p-4 rounded-lg bg-neon-amarillo/10 border border-neon-amarillo/30">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-neon-amarillo/20 flex items-center justify-center flex-shrink-0">
                <AlertTriangle className="w-5 h-5 text-neon-amarillo" />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-bold uppercase tracking-wider text-neon-amarillo">
                    Solo cálculo
                  </span>
                </div>
                <p className="text-xs text-neon-amarillo/80">
                  Sin partido, el análisis es teórico y no se registra.
                </p>
                {!mostrarInfo && (
                  <button
                    type="button"
                    onClick={() => setMostrarInfo(true)}
                    className="text-xs text-neon-cyan hover:text-neon-cyan/80 mt-1 flex items-center gap-1"
                  >
                    <ChevronDown className="w-3 h-3" />
                    ¿Por qué importa?
                  </button>
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Error */}
      {error && (
        <p className="text-xs text-neon-rojo">{error}</p>
      )}
    </div>
  );
}
