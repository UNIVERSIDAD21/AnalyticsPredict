/**
 * ListaPartidosFutbol.tsx — Lista de partidos de fútbol
 *
 * Muestra partidos agrupados por fecha con soporte para:
 * - Filtrado por competición
 * - Estado de carga con skeleton loaders
 * - Estado vacío con mensaje amigable
 * - Diseño glassmorphism futurista
 */

import { useMemo, useState } from 'react';
import { Calendar, Filter, Trophy, Search, X, ChevronDown } from 'lucide-react';
import { clsx } from 'clsx';
import { PartidoFutbolResumen } from '../../tipos/futbol';
import {
  formatearFechaPartidoBogota,
  obtenerFechaISOBogota,
  obtenerHoyISOBogota,
} from '../../utilidades';
import { TarjetaPartidoFutbol } from '../moleculas/TarjetaPartidoFutbol';
import { Tarjeta } from '../atomos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsListaPartidosFutbol {
  /** Lista de partidos a mostrar */
  partidos: PartidoFutbolResumen[];
  /** Indica si está cargando */
  cargando?: boolean;
  /** Callback al hacer clic en analizar */
  onAnalizar?: (partidoId: string) => void;
  /** Clase CSS adicional */
  className?: string;
}

interface PartidosAgrupados {
  fecha: string;
  fechaFormateada: string;
  partidos: PartidoFutbolResumen[];
}

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

/**
 * Formatea una fecha ISO a formato legible
 */
function formatearFechaGrupo(fechaISO: string): string {
  const hoy = new Date(`${obtenerHoyISOBogota()}T00:00:00-05:00`);
  const manana = new Date(hoy);
  manana.setDate(manana.getDate() + 1);
  const ayer = new Date(hoy);
  ayer.setDate(ayer.getDate() - 1);

  const fechaSolo = fechaISO;
  const hoySolo = obtenerHoyISOBogota();
  const mananaSolo = `${manana.getFullYear()}-${String(manana.getMonth() + 1).padStart(2, '0')}-${String(manana.getDate()).padStart(2, '0')}`;
  const ayerSolo = `${ayer.getFullYear()}-${String(ayer.getMonth() + 1).padStart(2, '0')}-${String(ayer.getDate()).padStart(2, '0')}`;

  if (fechaSolo === hoySolo) {
    return 'Hoy';
  } else if (fechaSolo === mananaSolo) {
    return 'Mañana';
  } else if (fechaSolo === ayerSolo) {
    return 'Ayer';
  }

  return formatearFechaPartidoBogota(`${fechaISO}T00:00:00Z`, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });
}

/**
 * Agrupa partidos por fecha
 */
function agruparPorFecha(partidos: PartidoFutbolResumen[]): PartidosAgrupados[] {
  const grupos: Record<string, PartidoFutbolResumen[]> = {};

  partidos.forEach((partido) => {
    const fecha = obtenerFechaISOBogota(partido.fechaPartido);
    if (!grupos[fecha]) {
      grupos[fecha] = [];
    }
    grupos[fecha].push(partido);
  });

  return Object.entries(grupos)
    .map(([fecha, partidos]) => ({
      fecha,
      fechaFormateada: formatearFechaGrupo(fecha),
      partidos: partidos.sort(
        (a, b) => new Date(a.fechaPartido).getTime() - new Date(b.fechaPartido).getTime()
      ),
    }))
    .sort((a, b) => a.fecha.localeCompare(b.fecha));
}

/**
 * Obtiene lista única de competiciones
 */
function obtenerCompeticiones(partidos: PartidoFutbolResumen[]): string[] {
  const competiciones = new Set<string>();
  partidos.forEach((partido) => {
    competiciones.add(partido.competicionNombre);
  });
  return Array.from(competiciones).sort();
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE SKELETON
// ══════════════════════════════════════════════════════════════

function SkeletonPartido() {
  return (
    <div className="tarjeta animate-pulse space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="h-3 bg-neon-cyan/20 rounded w-24" />
        <div className="h-5 bg-neon-cyan/10 rounded w-20" />
      </div>

      {/* Equipos */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-neon-cyan/10" />
          <div className="space-y-2">
            <div className="h-4 bg-neon-cyan/20 rounded w-24" />
            <div className="h-3 bg-neon-cyan/10 rounded w-12" />
          </div>
        </div>

        <div className="h-6 bg-neon-cyan/20 rounded w-8" />

        <div className="flex-1 flex items-center justify-end gap-3">
          <div className="space-y-2 text-right">
            <div className="h-4 bg-neon-cyan/20 rounded w-24 ml-auto" />
            <div className="h-3 bg-neon-cyan/10 rounded w-12 ml-auto" />
          </div>
          <div className="w-10 h-10 rounded-full bg-neon-cyan/10" />
        </div>
      </div>

      {/* Fecha */}
      <div className="flex items-center justify-center gap-4">
        <div className="h-4 bg-neon-cyan/10 rounded w-20" />
        <div className="h-4 bg-neon-cyan/10 rounded w-12" />
      </div>

      {/* Boton */}
      <div className="h-9 bg-neon-cyan/10 rounded w-full" />
    </div>
  );
}

function SkeletonGrupo() {
  return (
    <div className="space-y-4">
      {/* Header de fecha */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-neon-cyan/10 animate-pulse" />
        <div className="h-5 bg-neon-cyan/20 rounded w-32 animate-pulse" />
      </div>

      {/* Partidos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <SkeletonPartido />
        <SkeletonPartido />
        <SkeletonPartido />
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE ESTADO VACIO
// ══════════════════════════════════════════════════════════════

function EstadoVacio({ mensaje }: { mensaje: string }) {
  return (
    <Tarjeta className="text-center py-12 space-y-4">
      <div className="w-16 h-16 mx-auto rounded-full bg-futurista-medio/50 flex items-center justify-center">
        <Trophy size={32} className="text-texto-terciario" />
      </div>
      <div className="space-y-2">
        <h3 className="text-lg font-futurista text-texto-principal">
          No hay partidos
        </h3>
        <p className="text-texto-secundario text-sm max-w-md mx-auto">
          {mensaje}
        </p>
      </div>
    </Tarjeta>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Lista de partidos de fútbol con agrupación por fecha y filtros
 */
export function ListaPartidosFutbol({
  partidos,
  cargando = false,
  onAnalizar,
  className,
}: PropsListaPartidosFutbol) {
  const [filtroCompeticion, setFiltroCompeticion] = useState<string>('');
  const [busqueda, setBusqueda] = useState<string>('');
  const [mostrarFiltros, setMostrarFiltros] = useState(false);
  const [gruposColapsados, setGruposColapsados] = useState<Record<string, boolean>>(() => {
    if (typeof window === 'undefined') return {};
    try {
      const raw = window.sessionStorage.getItem('futbol_grupos_colapsados');
      return raw ? (JSON.parse(raw) as Record<string, boolean>) : {};
    } catch {
      return {};
    }
  });

  const alternarGrupo = (fecha: string) => {
    setGruposColapsados((prev) => {
      const next = { ...prev, [fecha]: !prev[fecha] };
      if (typeof window !== 'undefined') {
        window.sessionStorage.setItem('futbol_grupos_colapsados', JSON.stringify(next));
      }
      return next;
    });
  };


  // Obtener competiciones disponibles
  const competiciones = useMemo(() => obtenerCompeticiones(partidos), [partidos]);

  // Filtrar partidos
  const partidosFiltrados = useMemo(() => {
    let resultado = partidos;

    // Filtro por competición
    if (filtroCompeticion) {
      resultado = resultado.filter((p) => p.competicionNombre === filtroCompeticion);
    }

    // Filtro por búsqueda
    if (busqueda.trim()) {
      const termino = busqueda.toLowerCase().trim();
      resultado = resultado.filter(
        (p) =>
          p.equipoLocalNombre.toLowerCase().includes(termino) ||
          p.equipoVisitanteNombre.toLowerCase().includes(termino) ||
          p.competicionNombre.toLowerCase().includes(termino)
      );
    }

    return resultado;
  }, [partidos, filtroCompeticion, busqueda]);

  // Agrupar por fecha
  const partidosAgrupados = useMemo(
    () => agruparPorFecha(partidosFiltrados),
    [partidosFiltrados]
  );

  // Limpiar filtros
  const limpiarFiltros = () => {
    setFiltroCompeticion('');
    setBusqueda('');
  };

  const hayFiltrosActivos = filtroCompeticion || busqueda.trim();

  // Estado de carga
  if (cargando) {
    return (
      <div className={clsx('space-y-8', className)}>
        <SkeletonGrupo />
        <SkeletonGrupo />
      </div>
    );
  }

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Barra de filtros */}
      <div className="space-y-4">
        {/* Header con búsqueda y toggle de filtros */}
        <div className="flex items-center gap-3">
          {/* Búsqueda */}
          <div className="flex-1 relative">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-texto-terciario"
            />
            <input
              type="text"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar equipo o competición..."
              className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-futurista-oscuro/80 border border-neon-cyan/20 text-texto-principal placeholder-texto-terciario text-sm focus:border-neon-cyan focus:outline-none transition-colors"
            />
            {busqueda && (
              <button
                onClick={() => setBusqueda('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-texto-terciario hover:text-texto-secundario"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Toggle filtros */}
          <button
            onClick={() => setMostrarFiltros(!mostrarFiltros)}
            className={clsx(
              'flex items-center gap-2 px-4 py-2.5 rounded-lg border text-sm font-medium transition-all',
              mostrarFiltros || hayFiltrosActivos
                ? 'bg-neon-cyan/10 border-neon-cyan/30 text-neon-cyan'
                : 'bg-futurista-oscuro/80 border-neon-cyan/20 text-texto-secundario hover:text-texto-principal'
            )}
          >
            <Filter size={16} />
            <span className="hidden sm:inline">Filtros</span>
            {hayFiltrosActivos && (
              <span className="w-2 h-2 rounded-full bg-neon-cyan animate-pulse" />
            )}
          </button>
        </div>

        {/* Panel de filtros expandible */}
        {mostrarFiltros && (
          <div className="p-4 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10 space-y-4 animate-entrada">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-texto-secundario uppercase tracking-wider">
                Filtrar por competición
              </h4>
              {hayFiltrosActivos && (
                <button
                  onClick={limpiarFiltros}
                  className="text-xs text-neon-cyan hover:text-neon-cyan/80 font-medium"
                >
                  Limpiar filtros
                </button>
              )}
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setFiltroCompeticion('')}
                className={clsx(
                  'px-3 py-1.5 rounded-full text-xs font-semibold border transition-all',
                  !filtroCompeticion
                    ? 'bg-neon-cyan/20 border-neon-cyan text-neon-cyan'
                    : 'border-neon-cyan/20 text-texto-terciario hover:text-texto-secundario hover:border-neon-cyan/30'
                )}
              >
                Todas
              </button>
              {competiciones.map((comp) => (
                <button
                  key={comp}
                  onClick={() => setFiltroCompeticion(comp)}
                  className={clsx(
                    'px-3 py-1.5 rounded-full text-xs font-semibold border transition-all',
                    filtroCompeticion === comp
                      ? 'bg-neon-cyan/20 border-neon-cyan text-neon-cyan'
                      : 'border-neon-cyan/20 text-texto-terciario hover:text-texto-secundario hover:border-neon-cyan/30'
                  )}
                >
                  {comp}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Resumen de resultados */}
        <div className="flex items-center justify-between text-xs text-texto-terciario">
          <span>
            {partidosFiltrados.length} partido{partidosFiltrados.length !== 1 ? 's' : ''} encontrado{partidosFiltrados.length !== 1 ? 's' : ''}
          </span>
          {hayFiltrosActivos && (
            <span className="text-neon-cyan">
              Mostrando resultados filtrados
            </span>
          )}
        </div>
      </div>

      {/* Lista de partidos */}
      {partidosAgrupados.length === 0 ? (
        <EstadoVacio
          mensaje={
            hayFiltrosActivos
              ? 'No se encontraron partidos con los filtros seleccionados. Intenta ajustar tu búsqueda.'
              : 'No hay partidos programados en este momento. Vuelve más tarde para ver los próximos encuentros.'
          }
        />
      ) : (
        <div className="space-y-8">
          {partidosAgrupados.map((grupo) => {
            const colapsado = gruposColapsados[grupo.fecha] ?? (grupo.fechaFormateada !== 'Hoy' && grupo.fechaFormateada !== 'Mañana');
            return (
            <div key={grupo.fecha} className="space-y-4">
              {/* Header de fecha */}
              <button
                type="button"
                onClick={() => alternarGrupo(grupo.fecha)}
                className="flex w-full items-center gap-3 text-left"
              >
                <div className="w-8 h-8 rounded-lg bg-neon-magenta/10 border border-neon-magenta/30 flex items-center justify-center">
                  <Calendar size={16} className="text-neon-magenta" />
                </div>
                <h3 className="text-lg font-futurista font-semibold text-texto-principal capitalize">
                  {grupo.fechaFormateada}
                </h3>
                <span className="text-xs text-texto-terciario px-2 py-0.5 rounded-full bg-futurista-medio/50">
                  {grupo.partidos.length} partido{grupo.partidos.length !== 1 ? 's' : ''}
                </span>
                <ChevronDown size={18} className={clsx('ml-auto text-texto-terciario transition-transform', colapsado && '-rotate-90')} />
              </button>

              {/* Grid de partidos */}
              {!colapsado && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-entrada">
                {grupo.partidos.map((partido) => (
                  <TarjetaPartidoFutbol
                    key={partido.id}
                    partido={partido}
                    onAnalizar={onAnalizar ? () => onAnalizar(partido.id) : undefined}
                  />
                ))}
              </div>
              )}
            </div>
          );})}
        </div>
      )}
    </div>
  );
}
