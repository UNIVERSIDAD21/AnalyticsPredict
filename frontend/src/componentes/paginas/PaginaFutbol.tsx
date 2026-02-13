/**
 * PaginaFutbol.tsx — Pagina principal del modulo de futbol
 *
 * Muestra partidos proximos agrupados por fecha con filtros,
 * resumen rapido y navegacion a analisis.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ArrowLeft,
  Calendar,
  Clock,
  Target,
  TrendingUp,
  Trophy,
  Filter,
  RefreshCw,
  Activity,
  X,
} from 'lucide-react';
import { clsx } from 'clsx';
import { Encabezado, ListaPartidosFutbol } from '../organismos';
import { SelectorCompeticion, MensajeError } from '../moleculas';
import { Boton, Tarjeta } from '../atomos';
import { usePartidosFutbol } from '../../hooks';
import { obtenerCompeticiones } from '../../servicios/futbol';
import { obtenerFechaISOBogota, obtenerHoyISOBogota } from '../../utilidades';
import type { Competicion, FiltrosPartidos, PartidoFutbolResumen } from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

const navegar = (ruta: string) => {
  if (window.location.pathname === ruta) return;
  window.history.pushState({}, '', ruta);
  window.dispatchEvent(new PopStateEvent('popstate'));
};

const obtenerFechaPartidoISO = (valor: string): string => obtenerFechaISOBogota(valor);

function formatearFechaHoraCorta(fechaISO: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleString('es-ES', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

interface PropsPanelSeleccionPartido {
  partidos: PartidoFutbolResumen[];
  partidoSeleccionadoId: string;
  onSeleccionarPartido: (partidoId: string) => void;
  onAnalizarPartido: () => void;
  cargando: boolean;
}

function PanelSeleccionPartido({
  partidos,
  partidoSeleccionadoId,
  onSeleccionarPartido,
  onAnalizarPartido,
  cargando,
}: PropsPanelSeleccionPartido) {
  const partidoSeleccionado = useMemo(
    () => partidos.find((partido) => partido.id === partidoSeleccionadoId) ?? null,
    [partidoSeleccionadoId, partidos]
  );

  return (
    <Tarjeta className="mb-6 border border-neon-cyan/25">
      <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-4 items-end">
        <div className="space-y-3">
          <div>
            <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-neon-cyan">
              Seleccionar partido para analizar
            </h3>
            <p className="text-xs text-texto-secundario mt-1">
              Flujo directo: eliges un partido y vas al análisis, como en NBA.
            </p>
          </div>

          <label className="flex flex-col gap-2 text-sm text-texto-secundario">
            Partido
            <select
              value={partidoSeleccionadoId}
              onChange={(event) => onSeleccionarPartido(event.target.value)}
              disabled={cargando || partidos.length === 0}
              className="bg-futurista-negro/60 border border-neon-cyan/30 rounded px-3 py-2 text-sm text-texto-principal"
            >
              <option value="">Selecciona un partido...</option>
              {partidos.map((partido) => (
                <option key={partido.id} value={partido.id}>
                  {partido.equipoLocalNombre} vs {partido.equipoVisitanteNombre} ·{' '}
                  {formatearFechaHoraCorta(partido.fechaPartido)}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="space-y-3">
          <div className="rounded-lg border border-neon-cyan/20 bg-futurista-negro/40 p-3 min-h-[92px]">
            {partidoSeleccionado ? (
              <div className="space-y-1">
                <p className="text-sm font-semibold text-texto-principal">
                  {partidoSeleccionado.equipoLocalNombre} vs {partidoSeleccionado.equipoVisitanteNombre}
                </p>
                <p className="text-xs text-texto-secundario">
                  {partidoSeleccionado.competicionNombre}
                </p>
                <p className="text-xs text-neon-cyan">
                  {formatearFechaHoraCorta(partidoSeleccionado.fechaPartido)}
                </p>
              </div>
            ) : (
              <p className="text-xs text-texto-terciario">
                Selecciona un partido para habilitar el análisis.
              </p>
            )}
          </div>

          <Boton
            variante="primario"
            anchoCompleto
            onClick={onAnalizarPartido}
            disabled={!partidoSeleccionadoId}
          >
            Analizar partido
          </Boton>
        </div>
      </div>
    </Tarjeta>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE SKELETON
// ══════════════════════════════════════════════════════════════

function SkeletonTarjetaResumen() {
  return (
    <div className="tarjeta p-4 animate-pulse">
      <div className="h-3 bg-neon-cyan/20 rounded w-20 mb-3" />
      <div className="h-8 bg-neon-cyan/30 rounded w-16 mb-1" />
      <div className="h-3 bg-neon-cyan/10 rounded w-24" />
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE TARJETA RESUMEN
// ══════════════════════════════════════════════════════════════

interface PropsTarjetaResumen {
  titulo: string;
  valor: string | number;
  subtitulo?: string;
  icono: React.ReactNode;
  color: 'cyan' | 'verde' | 'magenta' | 'amarillo';
  loading?: boolean;
}

function TarjetaResumen({
  titulo,
  valor,
  subtitulo,
  icono,
  color,
  loading = false,
}: PropsTarjetaResumen) {
  const colores = {
    cyan: {
      bg: 'bg-neon-cyan/10',
      border: 'border-neon-cyan/30',
      text: 'text-neon-cyan',
      glow: 'shadow-glow-cyan/20',
    },
    verde: {
      bg: 'bg-neon-verde/10',
      border: 'border-neon-verde/30',
      text: 'text-neon-verde',
      glow: 'shadow-glow-verde/20',
    },
    magenta: {
      bg: 'bg-neon-magenta/10',
      border: 'border-neon-magenta/30',
      text: 'text-neon-magenta',
      glow: 'shadow-glow-magenta/20',
    },
    amarillo: {
      bg: 'bg-neon-amarillo/10',
      border: 'border-neon-amarillo/30',
      text: 'text-neon-amarillo',
      glow: 'shadow-glow-amarillo/20',
    },
  };

  const estilos = colores[color];

  if (loading) {
    return <SkeletonTarjetaResumen />;
  }

  return (
    <Tarjeta
      className={clsx(
        'relative overflow-hidden border',
        estilos.border,
        estilos.glow
      )}
      padding="sm"
    >
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-current to-transparent opacity-30" />
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-texto-terciario uppercase tracking-widest mb-1">
            {titulo}
          </p>
          <p className={clsx('text-2xl font-mono font-bold', estilos.text)}>
            {valor}
          </p>
          {subtitulo && (
            <p className="text-xs text-texto-secundario mt-1">{subtitulo}</p>
          )}
        </div>
        <div className={clsx('p-2 rounded-lg', estilos.bg)}>{icono}</div>
      </div>
    </Tarjeta>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE SIDEBAR FILTROS
// ══════════════════════════════════════════════════════════════

interface PropsSidebarFiltros {
  competiciones: Competicion[];
  competicionSeleccionada: string;
  onCambiarCompeticion: (id: string) => void;
  fechaDesde: string;
  fechaHasta: string;
  onCambiarFechaDesde: (fecha: string) => void;
  onCambiarFechaHasta: (fecha: string) => void;
  onLimpiar: () => void;
  cargando?: boolean;
  visible: boolean;
  onCerrar: () => void;
}

function SidebarFiltros({
  competiciones,
  competicionSeleccionada,
  onCambiarCompeticion,
  fechaDesde,
  fechaHasta,
  onCambiarFechaDesde,
  onCambiarFechaHasta,
  onLimpiar,
  cargando = false,
  visible,
  onCerrar,
}: PropsSidebarFiltros) {
  const hayFiltrosActivos = competicionSeleccionada || fechaDesde || fechaHasta;

  return (
    <>
      {/* Overlay para mobile */}
      {visible && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onCerrar}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed lg:static inset-y-0 left-0 z-50 lg:z-auto',
          'w-80 lg:w-72 xl:w-80',
          'bg-futurista-oscuro lg:bg-transparent',
          'border-r lg:border-r-0 border-neon-cyan/20',
          'transition-transform duration-300 lg:transform-none',
          visible ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        <div className="h-full lg:h-auto p-4 lg:p-0 overflow-y-auto lg:overflow-visible">
          {/* Header mobile */}
          <div className="flex items-center justify-between mb-6 lg:hidden">
            <h3 className="text-lg font-futurista font-bold text-texto-principal">
              Filtros
            </h3>
            <button
              onClick={onCerrar}
              className="p-2 rounded-lg text-texto-secundario hover:text-texto-principal"
            >
              <X size={20} />
            </button>
          </div>

          <Tarjeta className="space-y-6 lg:sticky lg:top-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Filter size={18} className="text-neon-cyan" />
                <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-texto-principal">
                  Filtros
                </h3>
              </div>
              {hayFiltrosActivos && (
                <button
                  onClick={onLimpiar}
                  className="text-xs text-neon-cyan hover:text-neon-cyan/80 font-medium"
                >
                  Limpiar
                </button>
              )}
            </div>

            {/* Competicion */}
            <SelectorCompeticion
              competiciones={competiciones}
              valor={competicionSeleccionada}
              onChange={onCambiarCompeticion}
              etiqueta="Competicion"
              placeholder="Todas las competiciones"
              deshabilitado={cargando}
            />

            {/* Rango de fechas */}
            <div className="space-y-4">
              <label className="etiqueta flex items-center gap-2">
                <Calendar size={14} className="text-neon-magenta" />
                Rango de fechas
              </label>

              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs text-texto-terciario">Desde</label>
                  <div className="flex items-center gap-2 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20">
                    <Calendar className="w-4 h-4 text-neon-cyan" />
                    <input
                      type="date"
                      value={fechaDesde}
                      onChange={(e) => onCambiarFechaDesde(e.target.value)}
                      disabled={cargando}
                      className="bg-transparent text-sm text-texto-principal focus:outline-none flex-1"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs text-texto-terciario">Hasta</label>
                  <div className="flex items-center gap-2 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20">
                    <Calendar className="w-4 h-4 text-neon-cyan" />
                    <input
                      type="date"
                      value={fechaHasta}
                      onChange={(e) => onCambiarFechaHasta(e.target.value)}
                      disabled={cargando}
                      className="bg-transparent text-sm text-texto-principal focus:outline-none flex-1"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Indicador de filtros activos */}
            {hayFiltrosActivos && (
              <div className="p-3 rounded-lg bg-neon-cyan/5 border border-neon-cyan/20">
                <div className="flex items-center gap-2 text-xs text-neon-cyan">
                  <div className="w-2 h-2 rounded-full bg-neon-cyan animate-pulse" />
                  <span>Filtros aplicados</span>
                </div>
              </div>
            )}
          </Tarjeta>
        </div>
      </aside>
    </>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Pagina principal del modulo de futbol con lista de partidos proximos
 */
export function PaginaFutbol() {
  // Estado de filtros
  const [competicionSeleccionada, setCompeticionSeleccionada] = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [partidoSeleccionadoId, setPartidoSeleccionadoId] = useState('');
  const [sidebarVisible, setSidebarVisible] = useState(false);
  const [partidosHoyPersistidos, setPartidosHoyPersistidos] = useState<PartidoFutbolResumen[]>([]);
  const diaPersistidoRef = useRef<string>(obtenerHoyISOBogota());

  // Estado de competiciones
  const [competiciones, setCompeticiones] = useState<Competicion[]>([]);
  const [cargandoCompeticiones, setCargandoCompeticiones] = useState(true);

  // Filtros memorizados
  const filtros = useMemo<FiltrosPartidos>(() => {
    const f: FiltrosPartidos = {};
    if (competicionSeleccionada) f.competicion = competicionSeleccionada;
    if (!fechaDesde && !fechaHasta) {
      f.dias = 7; // Default: proximos 7 dias
    }
    return f;
  }, [competicionSeleccionada, fechaDesde, fechaHasta]);

  const filtrosHoy = useMemo<FiltrosPartidos>(() => {
    const f: FiltrosPartidos = {};
    if (competicionSeleccionada) f.competicion = competicionSeleccionada;
    return f;
  }, [competicionSeleccionada]);

  // Hook de partidos
  const {
    partidos,
    cargando: cargandoPartidos,
    error,
    recargar,
    setFiltros,
  } = usePartidosFutbol({
    tipo: 'proximos',
    filtrosIniciales: filtros,
    cargarAlMontar: true,
  });

  const {
    partidos: partidosHoy,
    cargando: cargandoHoy,
    error: errorHoy,
    recargar: recargarHoy,
    setFiltros: setFiltrosHoy,
  } = usePartidosFutbol({
    tipo: 'hoy',
    filtrosIniciales: filtrosHoy,
    cargarAlMontar: true,
  });

  // Cargar competiciones al montar
  useEffect(() => {
    const cargar = async () => {
      try {
        const data = await obtenerCompeticiones();
        setCompeticiones(data);
      } catch (err) {
        console.error('Error cargando competiciones:', err);
      } finally {
        setCargandoCompeticiones(false);
      }
    };
    void cargar();
  }, []);

  // Actualizar filtros cuando cambien
  useEffect(() => {
    setFiltros(filtros);
    setFiltrosHoy(filtrosHoy);
  }, [filtros, filtrosHoy, setFiltros, setFiltrosHoy]);

  // Reiniciar snapshot de "hoy" cuando cambia la competicion.
  useEffect(() => {
    setPartidosHoyPersistidos([]);
    diaPersistidoRef.current = obtenerHoyISOBogota();
  }, [competicionSeleccionada]);

  // Mantener un snapshot de todos los partidos de hoy hasta cambio de dia.
  useEffect(() => {
    const hoy = obtenerHoyISOBogota();

    if (diaPersistidoRef.current !== hoy) {
      diaPersistidoRef.current = hoy;
      setPartidosHoyPersistidos([]);
    }

    const candidatosHoy = [...partidos, ...partidosHoy].filter(
      (p) => obtenerFechaPartidoISO(p.fechaPartido) === hoy
    );

    if (candidatosHoy.length === 0) {
      return;
    }

    setPartidosHoyPersistidos((anteriores) => {
      const mapa = new Map<string, PartidoFutbolResumen>();

      anteriores.forEach((partido) => {
        mapa.set(partido.id, partido);
      });
      candidatosHoy.forEach((partido) => {
        mapa.set(partido.id, partido);
      });

      return Array.from(mapa.values()).sort(
        (a, b) => new Date(a.fechaPartido).getTime() - new Date(b.fechaPartido).getTime()
      );
    });
  }, [partidos, partidosHoy]);

  const partidosParaMostrar = useMemo<PartidoFutbolResumen[]>(() => {
    const hoy = obtenerHoyISOBogota();
    const partidosNoHoy = partidos.filter((p) => obtenerFechaPartidoISO(p.fechaPartido) !== hoy);
    const mapa = new Map<string, PartidoFutbolResumen>();

    [...partidosNoHoy, ...partidosHoyPersistidos].forEach((partido) => {
      mapa.set(partido.id, partido);
    });

    return Array.from(mapa.values()).sort(
      (a, b) => new Date(a.fechaPartido).getTime() - new Date(b.fechaPartido).getTime()
    );
  }, [partidos, partidosHoyPersistidos]);

  useEffect(() => {
    if (partidoSeleccionadoId && partidosParaMostrar.some((p) => p.id === partidoSeleccionadoId)) {
      return;
    }

    if (partidosParaMostrar.length > 0) {
      setPartidoSeleccionadoId(partidosParaMostrar[0].id);
      return;
    }

    setPartidoSeleccionadoId('');
  }, [partidoSeleccionadoId, partidosParaMostrar]);

  const recargarTodo = useCallback(() => {
    recargar();
    recargarHoy();
  }, [recargar, recargarHoy]);

  // Calcular estadisticas rapidas
  const estadisticasRapidas = useMemo(() => {
    const hoy = obtenerHoyISOBogota();
    const partidosHoy = partidosParaMostrar.filter(
      (p) => obtenerFechaPartidoISO(p.fechaPartido) === hoy
    ).length;

    // Estos valores serian de un servicio real
    return {
      partidosHoy,
      apuestasActivas: 3, // Mock
      roiMensual: 8.5, // Mock
    };
  }, [partidosParaMostrar]);

  // Handlers
  const limpiarFiltros = useCallback(() => {
    setCompeticionSeleccionada('');
    setFechaDesde('');
    setFechaHasta('');
  }, []);

  const irAAnalisis = useCallback((partidoId: string) => {
    navegar(`/futbol/partidos/${partidoId}`);
  }, []);

  const analizarPartidoSeleccionado = useCallback(() => {
    if (!partidoSeleccionadoId) return;
    irAAnalisis(partidoSeleccionadoId);
  }, [irAAnalisis, partidoSeleccionadoId]);

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => navegar('/')}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg
                         border border-neon-cyan/30 bg-futurista-oscuro/50
                         text-neon-cyan hover:bg-neon-cyan/10 hover:border-neon-cyan/50
                         transition-all duration-200 text-sm font-medium"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="hidden sm:inline">Inicio</span>
            </button>

            <div>
              <h1 className="text-2xl font-futurista font-bold text-texto-principal tracking-wider flex items-center gap-3">
                <Trophy className="w-6 h-6 text-neon-cyan" />
                FUTBOL
              </h1>
              <p className="text-sm text-texto-secundario">
                Partidos proximos y analisis
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Toggle filtros mobile */}
            <button
              onClick={() => setSidebarVisible(true)}
              className="lg:hidden flex items-center gap-2 px-4 py-2 rounded-lg border border-neon-cyan/30 text-texto-secundario hover:text-texto-principal"
            >
              <Filter size={16} />
              <span>Filtros</span>
            </button>

            <Boton
              variante="secundario"
              iconoInicio={<RefreshCw size={16} />}
              onClick={recargarTodo}
              cargando={cargandoPartidos || cargandoHoy}
            >
              <span className="hidden sm:inline">Actualizar</span>
            </Boton>

            <Boton
              variante="primario"
              iconoInicio={<Activity size={16} />}
              onClick={() => navegar('/futbol/dashboard')}
            >
              <span className="hidden sm:inline">Dashboard</span>
            </Boton>
          </div>
        </div>

        {/* Tarjetas de resumen rapido */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <TarjetaResumen
            titulo="Partidos Hoy"
            valor={estadisticasRapidas.partidosHoy}
            subtitulo="totales del dia"
            icono={<Clock size={20} className="text-neon-cyan" />}
            color="cyan"
            loading={cargandoPartidos || cargandoHoy}
          />
          <TarjetaResumen
            titulo="Apuestas Activas"
            valor={estadisticasRapidas.apuestasActivas}
            subtitulo="pendientes"
            icono={<Target size={20} className="text-neon-magenta" />}
            color="magenta"
          />
          <TarjetaResumen
            titulo="ROI Mensual"
            valor={`+${estadisticasRapidas.roiMensual}%`}
            subtitulo="ultimos 30 dias"
            icono={<TrendingUp size={20} className="text-neon-verde" />}
            color="verde"
          />
        </div>

        {/* Error */}
        {(error || errorHoy) && (
          <div className="mb-6">
            <MensajeError
              titulo="Error al cargar partidos"
              mensaje={error || errorHoy || 'Error desconocido'}
              onCerrar={recargarTodo}
            />
          </div>
        )}

        <PanelSeleccionPartido
          partidos={partidosParaMostrar}
          partidoSeleccionadoId={partidoSeleccionadoId}
          onSeleccionarPartido={setPartidoSeleccionadoId}
          onAnalizarPartido={analizarPartidoSeleccionado}
          cargando={cargandoPartidos || cargandoHoy}
        />

        {/* Layout principal */}
        <div className="flex gap-6">
          {/* Sidebar de filtros */}
          <SidebarFiltros
            competiciones={competiciones}
            competicionSeleccionada={competicionSeleccionada}
            onCambiarCompeticion={setCompeticionSeleccionada}
            fechaDesde={fechaDesde}
            fechaHasta={fechaHasta}
            onCambiarFechaDesde={setFechaDesde}
            onCambiarFechaHasta={setFechaHasta}
            onLimpiar={limpiarFiltros}
            cargando={cargandoPartidos || cargandoCompeticiones}
            visible={sidebarVisible}
            onCerrar={() => setSidebarVisible(false)}
          />

          {/* Contenido principal */}
          <div className="flex-1 min-w-0">
            <ListaPartidosFutbol
              partidos={partidosParaMostrar}
              cargando={cargandoPartidos || cargandoHoy}
              onAnalizar={irAAnalisis}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-neon-cyan/10 bg-futurista-negro/80 backdrop-blur-sm">
        <div className="contenedor py-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-2 text-center md:text-left">
            <p className="text-texto-terciario text-xs uppercase tracking-wider">
              Modulo de Futbol — Sistema de Analisis de Corners, Goles y Disparos
            </p>
            <p className="text-texto-terciario/60 text-xs">
              Los analisis son orientativos. Apuesta responsablemente.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
