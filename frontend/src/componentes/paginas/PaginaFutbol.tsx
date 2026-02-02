/**
 * PaginaFutbol.tsx — Pagina principal del modulo de futbol
 *
 * Muestra partidos proximos agrupados por fecha con filtros,
 * resumen rapido y navegacion a analisis.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
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
import type { Competicion, FiltrosPartidos } from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

const navegar = (ruta: string) => {
  if (window.location.pathname === ruta) return;
  window.history.pushState({}, '', ruta);
  window.dispatchEvent(new PopStateEvent('popstate'));
};

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
  const [sidebarVisible, setSidebarVisible] = useState(false);

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
  }, [filtros, setFiltros]);

  // Calcular estadisticas rapidas
  const estadisticasRapidas = useMemo(() => {
    const hoy = new Date().toISOString().split('T')[0];
    const partidosHoy = partidos.filter(
      (p) => p.fechaPartido.split('T')[0] === hoy
    ).length;

    // Estos valores serian de un servicio real
    return {
      partidosHoy,
      apuestasActivas: 3, // Mock
      roiMensual: 8.5, // Mock
    };
  }, [partidos]);

  // Handlers
  const limpiarFiltros = useCallback(() => {
    setCompeticionSeleccionada('');
    setFechaDesde('');
    setFechaHasta('');
  }, []);

  const irAAnalisis = useCallback((partidoId: string) => {
    navegar(`/futbol/partidos/${partidoId}`);
  }, []);

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
              onClick={recargar}
              cargando={cargandoPartidos}
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
            subtitulo="programados"
            icono={<Clock size={20} className="text-neon-cyan" />}
            color="cyan"
            loading={cargandoPartidos}
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
        {error && (
          <div className="mb-6">
            <MensajeError
              titulo="Error al cargar partidos"
              mensaje={error}
              onCerrar={recargar}
            />
          </div>
        )}

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
              partidos={partidos}
              cargando={cargandoPartidos}
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
