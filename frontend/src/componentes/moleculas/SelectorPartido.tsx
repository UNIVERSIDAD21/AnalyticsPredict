/**
 * SelectorPartido.tsx — Selector de partido para análisis
 *
 * CRÍTICO: Este componente permite seleccionar un partido real
 * para que las predicciones se registren correctamente.
 *
 * Sin selección de partido, las predicciones NO se registran.
 */

import { useEffect, useState, useMemo } from 'react';
import { Calendar, AlertTriangle, RefreshCw } from 'lucide-react';
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
      {/* Etiqueta */}
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold uppercase tracking-wider text-texto-secundario flex items-center gap-2">
          <Calendar className="w-4 h-4 text-neon-cyan" />
          Partido a analizar
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

      {/* Partido seleccionado o selector */}
      {partidoSeleccionado ? (
        <div className="p-3 rounded-lg bg-neon-cyan/10 border border-neon-cyan/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-texto-principal">
                {partidoSeleccionado.equipo_local_nombre} vs{' '}
                {partidoSeleccionado.equipo_visitante_nombre}
              </p>
              <p className="text-xs text-texto-secundario">
                {formatearFechaPartido(partidoSeleccionado.fecha_partido)} -{' '}
                {partidoSeleccionado.temporada_nombre}
              </p>
            </div>
            <button
              type="button"
              onClick={handleLimpiar}
              disabled={deshabilitado}
              className="text-xs text-neon-rojo hover:text-neon-rojo/80"
            >
              Cambiar
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Botón para expandir/colapsar */}
          <button
            type="button"
            onClick={() => setExpandido(!expandido)}
            disabled={deshabilitado || cargando}
            className={`w-full p-3 rounded-lg border text-left transition-all ${
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

          {/* Advertencia si no hay partido seleccionado */}
          <div className="flex items-start gap-2 p-3 rounded-lg bg-neon-amarillo/10 border border-neon-amarillo/30">
            <AlertTriangle className="w-4 h-4 text-neon-amarillo flex-shrink-0 mt-0.5" />
            <div className="text-xs text-neon-amarillo">
              <p className="font-semibold">Sin partido seleccionado</p>
              <p className="text-neon-amarillo/80">
                Para auditar y calibrar predicciones, selecciona un partido real. Sin
                partido, el análisis no se registra.
              </p>
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
