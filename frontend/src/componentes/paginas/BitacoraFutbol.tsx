/**
 * BitacoraFutbol.tsx — Pagina de bitacora de apuestas de futbol
 *
 * Muestra el historial de apuestas con:
 * - Tarjetas de resumen (Total, Ganadas, Perdidas, ROI)
 * - Filtros avanzados (Estado, Mercado, Confianza, Fechas, Busqueda)
 * - Lista de apuestas con badges de estado
 * - Paginacion
 * - Acciones: Ver partido, Editar, Cancelar
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArrowLeft,
  Search,
  Filter,
  Calendar,
  TrendingUp,
  Target,
  Trophy,
  Eye,
  Edit2,
  X,
  ChevronLeft,
  ChevronRight,
  RotateCw,
  BarChart3,
  Clock,
  CheckCircle,
  XCircle,
  MinusCircle,
  AlertCircle,
} from 'lucide-react';
import { clsx } from 'clsx';
import { Encabezado } from '../organismos';
import { MensajeError, BadgeConfianza } from '../moleculas';
import { Boton, Spinner, Tarjeta } from '../atomos';
import { useBitacoraFutbol } from '../../hooks';
import { cancelarApuesta } from '../../servicios/futbol';
import { useToasts } from '../../contextos/Toasts';
import { useGateNavigation } from '../../hooks/useGateNavigation';
import type {
  ApuestaFutbol,
  EstadoApuesta,
  TipoMercadoFutbol,
  NivelConfianza,
  FiltrosApuestas,
} from '../../tipos/futbol';
import {
  ETIQUETAS_MERCADOS as etiquetasMercados,
  COLORES_ESTADO_APUESTA as coloresEstado,
  MERCADOS_CORNERS,
  MERCADOS_GOLES,
  MERCADOS_DISPAROS,
} from '../../tipos/futbol';

const TAMANO_PAGINA = 20;

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

const navegar = (ruta: string) => {
  if (window.location.pathname === ruta) return;
  window.history.pushState({}, '', ruta);
  window.dispatchEvent(new PopStateEvent('popstate'));
};

function formatearFecha(fechaISO: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function formatearMoneda(valor: number): string {
  const signo = valor >= 0 ? '+' : '';
  return `${signo}$${valor.toFixed(2)}`;
}

function formatearPorcentaje(valor: number | null): string {
  if (valor === null) return '--';
  const signo = valor >= 0 ? '+' : '';
  return `${signo}${(valor * 100).toFixed(1)}%`;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE TARJETA RESUMEN
// ══════════════════════════════════════════════════════════════

interface PropsTarjetaResumen {
  titulo: string;
  valor: string | number;
  subtitulo?: string;
  icono: React.ReactNode;
  colorValor?: string;
  loading?: boolean;
}

function TarjetaResumen({
  titulo,
  valor,
  subtitulo,
  icono,
  colorValor = 'text-texto-principal',
  loading = false,
}: PropsTarjetaResumen) {
  if (loading) {
    return (
      <Tarjeta padding="sm" className="animate-pulse">
        <div className="h-3 bg-neon-cyan/20 rounded w-16 mb-2" />
        <div className="h-8 bg-neon-cyan/30 rounded w-20 mb-1" />
        <div className="h-3 bg-neon-cyan/10 rounded w-24" />
      </Tarjeta>
    );
  }

  return (
    <Tarjeta padding="sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-texto-terciario uppercase tracking-widest mb-1">
            {titulo}
          </p>
          <p className={clsx('text-2xl font-mono font-bold', colorValor)}>
            {valor}
          </p>
          {subtitulo && (
            <p className="text-xs text-texto-secundario mt-1">{subtitulo}</p>
          )}
        </div>
        <div className="p-2 rounded-lg bg-futurista-medio/30">{icono}</div>
      </div>
    </Tarjeta>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE FILTROS
// ══════════════════════════════════════════════════════════════

interface PropsFiltros {
  filtros: {
    estado: string;
    mercado: string;
    confianza: string;
    desde: string;
    hasta: string;
    busqueda: string;
  };
  onChange: (campo: string, valor: string) => void;
  onLimpiar: () => void;
  cargando?: boolean;
}

function PanelFiltros({
  filtros,
  onChange,
  onLimpiar,
  cargando = false,
}: PropsFiltros) {
  const hayFiltrosActivos =
    filtros.estado ||
    filtros.mercado ||
    filtros.confianza ||
    filtros.desde ||
    filtros.hasta ||
    filtros.busqueda;

  const opcionesEstado: { valor: EstadoApuesta | ''; label: string }[] = [
    { valor: '', label: 'Todos los estados' },
    { valor: 'PENDIENTE', label: 'Pendiente' },
    { valor: 'GANADA', label: 'Ganada' },
    { valor: 'PERDIDA', label: 'Perdida' },
    { valor: 'PUSH', label: 'Push' },
    { valor: 'CANCELADA', label: 'Cancelada' },
    { valor: 'VOID', label: 'Void' },
  ];

  const opcionesConfianza: { valor: NivelConfianza | ''; label: string }[] = [
    { valor: '', label: 'Toda confianza' },
    { valor: 'MUY_ALTA', label: 'Muy Alta' },
    { valor: 'ALTA', label: 'Alta' },
    { valor: 'MEDIA', label: 'Media' },
    { valor: 'BAJA', label: 'Baja' },
    { valor: 'MUY_BAJA', label: 'Muy Baja' },
  ];

  const opcionesMercado = [
    { valor: '', label: 'Todos los mercados' },
    { valor: 'corners', label: '--- Corners ---', disabled: true },
    ...MERCADOS_CORNERS.map((m) => ({ valor: m, label: etiquetasMercados[m] })),
    { valor: 'goles', label: '--- Goles ---', disabled: true },
    ...MERCADOS_GOLES.map((m) => ({ valor: m, label: etiquetasMercados[m] })),
    { valor: 'disparos', label: '--- Disparos ---', disabled: true },
    ...MERCADOS_DISPAROS.map((m) => ({ valor: m, label: etiquetasMercados[m] })),
  ];

  return (
    <Tarjeta className="space-y-4">
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
            Limpiar filtros
          </button>
        )}
      </div>

      {/* Busqueda */}
      <div className="relative">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-texto-terciario"
        />
        <input
          type="text"
          value={filtros.busqueda}
          onChange={(e) => onChange('busqueda', e.target.value)}
          placeholder="Buscar partido o equipo..."
          disabled={cargando}
          className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-futurista-oscuro/80 border border-neon-cyan/20 text-texto-principal placeholder-texto-terciario text-sm focus:border-neon-cyan focus:outline-none transition-colors"
        />
        {filtros.busqueda && (
          <button
            onClick={() => onChange('busqueda', '')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-texto-terciario hover:text-texto-secundario"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Selectores */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Estado */}
        <div className="space-y-1">
          <label className="text-xs text-texto-terciario uppercase tracking-wider">
            Estado
          </label>
          <select
            value={filtros.estado}
            onChange={(e) => onChange('estado', e.target.value)}
            disabled={cargando}
            className="select-base"
          >
            {opcionesEstado.map((opt) => (
              <option key={opt.valor} value={opt.valor}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Mercado */}
        <div className="space-y-1">
          <label className="text-xs text-texto-terciario uppercase tracking-wider">
            Mercado
          </label>
          <select
            value={filtros.mercado}
            onChange={(e) => onChange('mercado', e.target.value)}
            disabled={cargando}
            className="select-base"
          >
            {opcionesMercado.map((opt) => (
              <option
                key={opt.valor}
                value={opt.valor}
                disabled={'disabled' in opt && opt.disabled}
              >
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Confianza */}
        <div className="space-y-1">
          <label className="text-xs text-texto-terciario uppercase tracking-wider">
            Confianza
          </label>
          <select
            value={filtros.confianza}
            onChange={(e) => onChange('confianza', e.target.value)}
            disabled={cargando}
            className="select-base"
          >
            {opcionesConfianza.map((opt) => (
              <option key={opt.valor} value={opt.valor}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Rango de fechas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1">
          <label className="text-xs text-texto-terciario uppercase tracking-wider">
            Desde
          </label>
          <div className="flex items-center gap-2 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20">
            <Calendar className="w-4 h-4 text-neon-cyan" />
            <input
              type="date"
              value={filtros.desde}
              onChange={(e) => onChange('desde', e.target.value)}
              disabled={cargando}
              className="bg-transparent text-sm text-texto-principal focus:outline-none flex-1"
            />
          </div>
        </div>
        <div className="space-y-1">
          <label className="text-xs text-texto-terciario uppercase tracking-wider">
            Hasta
          </label>
          <div className="flex items-center gap-2 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20">
            <Calendar className="w-4 h-4 text-neon-cyan" />
            <input
              type="date"
              value={filtros.hasta}
              onChange={(e) => onChange('hasta', e.target.value)}
              disabled={cargando}
              className="bg-transparent text-sm text-texto-principal focus:outline-none flex-1"
            />
          </div>
        </div>
      </div>
    </Tarjeta>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE FILA APUESTA
// ══════════════════════════════════════════════════════════════

interface PropsFilaApuesta {
  apuesta: ApuestaFutbol;
  onVerPartido: () => void;
  onEditar?: () => void;
  onCancelar?: () => void;
}

function FilaApuesta({
  apuesta,
  onVerPartido,
  onEditar,
  onCancelar,
}: PropsFilaApuesta) {
  const colores = coloresEstado[apuesta.estado];
  const etiquetaMercado = etiquetasMercados[apuesta.mercado];
  const esPendiente = apuesta.estado === 'PENDIENTE';
  const esGanada = apuesta.estado === 'GANADA';
  const esPerdida = apuesta.estado === 'PERDIDA';

  const IconoEstado =
    apuesta.estado === 'GANADA'
      ? CheckCircle
      : apuesta.estado === 'PERDIDA'
      ? XCircle
      : apuesta.estado === 'PUSH'
      ? MinusCircle
      : apuesta.estado === 'PENDIENTE'
      ? Clock
      : AlertCircle;

  return (
    <div
      className={clsx(
        'p-4 rounded-lg border transition-all duration-200',
        'bg-futurista-oscuro/50 backdrop-blur-sm',
        'hover:border-neon-cyan/30',
        esPendiente && 'border-neon-amarillo/30',
        esGanada && 'border-neon-verde/30',
        esPerdida && 'border-neon-rojo/30',
        !esPendiente && !esGanada && !esPerdida && 'border-futurista-medio/30'
      )}
    >
      <div className="flex flex-col lg:flex-row lg:items-center gap-4">
        {/* Info principal */}
        <div className="flex-1 min-w-0">
          {/* Partido */}
          <div className="flex items-center gap-2 mb-2">
            <Trophy size={14} className="text-neon-amarillo flex-shrink-0" />
            <span className="text-sm font-semibold text-texto-principal truncate">
              {apuesta.partido.equipoLocalNombre} vs{' '}
              {apuesta.partido.equipoVisitanteNombre}
            </span>
          </div>

          {/* Mercado y apuesta */}
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className="text-xs text-texto-terciario">{etiquetaMercado}</span>
            <span className="text-xs text-texto-terciario">|</span>
            <span
              className={clsx(
                'px-2 py-0.5 rounded text-xs font-semibold',
                apuesta.lado === 'OVER'
                  ? 'bg-neon-verde/20 text-neon-verde'
                  : 'bg-neon-rojo/20 text-neon-rojo'
              )}
            >
              {apuesta.lado} {apuesta.linea}
            </span>
            <span className="text-xs text-texto-terciario">@</span>
            <span className="text-sm font-mono text-neon-cyan">
              {apuesta.cuota.toFixed(2)}
            </span>
          </div>

          {/* Fecha y confianza */}
          <div className="flex items-center gap-3 text-xs text-texto-terciario">
            <span>{formatearFecha(apuesta.fechaCreacion)}</span>
            <BadgeConfianza nivel={apuesta.confianza} tamano="sm" />
          </div>
        </div>

        {/* Stake y resultado */}
        <div className="flex items-center gap-6">
          {/* Stake */}
          <div className="text-right">
            <p className="text-xs text-texto-terciario">Stake</p>
            <p className="font-mono font-semibold text-texto-principal">
              ${apuesta.stake.toFixed(2)}
            </p>
          </div>

          {/* Resultado */}
          <div className="text-right min-w-[80px]">
            <p className="text-xs text-texto-terciario">Resultado</p>
            <p
              className={clsx(
                'font-mono font-semibold',
                esGanada && 'text-neon-verde',
                esPerdida && 'text-neon-rojo',
                !esGanada && !esPerdida && 'text-texto-secundario'
              )}
            >
              {apuesta.gananciasReales !== undefined
                ? formatearMoneda(apuesta.gananciasReales)
                : '--'}
            </p>
          </div>

          {/* Badge de estado */}
          <div
            className={clsx(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold',
              colores.bg,
              colores.text
            )}
          >
            <IconoEstado size={14} />
            <span className="uppercase">{apuesta.estado}</span>
          </div>
        </div>

        {/* Acciones */}
        <div className="flex items-center gap-2 lg:ml-4">
          <button
            onClick={onVerPartido}
            className="p-2 rounded-lg border border-neon-cyan/30 text-neon-cyan hover:bg-neon-cyan/10 transition-colors"
            title="Ver partido"
          >
            <Eye size={16} />
          </button>
          {esPendiente && onEditar && (
            <button
              onClick={onEditar}
              className="p-2 rounded-lg border border-neon-amarillo/30 text-neon-amarillo hover:bg-neon-amarillo/10 transition-colors"
              title="Editar"
            >
              <Edit2 size={16} />
            </button>
          )}
          {esPendiente && onCancelar && (
            <button
              onClick={onCancelar}
              className="p-2 rounded-lg border border-neon-rojo/30 text-neon-rojo hover:bg-neon-rojo/10 transition-colors"
              title="Cancelar"
            >
              <X size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE ESTADO VACIO
// ══════════════════════════════════════════════════════════════

function EstadoVacio({ mensaje }: { mensaje: string }) {
  return (
    <Tarjeta className="text-center py-12">
      <BarChart3 className="w-16 h-16 text-texto-terciario mx-auto mb-4" />
      <h3 className="text-lg font-futurista text-texto-principal mb-2">
        Sin apuestas
      </h3>
      <p className="text-texto-secundario text-sm max-w-md mx-auto">{mensaje}</p>
    </Tarjeta>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Pagina de bitacora de apuestas de futbol
 */
export function BitacoraFutbol() {
  const { agregarToast } = useToasts();
  const { navegarConGate } = useGateNavigation(navegar);

  // Estado de filtros locales
  const [filtrosLocales, setFiltrosLocales] = useState({
    estado: '',
    mercado: '',
    confianza: '',
    desde: '',
    hasta: '',
    busqueda: '',
  });

  // Estado para confirmacion de cancelacion
  const [apuestaACancelar, setApuestaACancelar] = useState<ApuestaFutbol | null>(
    null
  );
  const [cancelando, setCancelando] = useState(false);

  // Convertir filtros locales a formato del hook
  const filtrosParaHook = useMemo<FiltrosApuestas>(() => {
    const f: FiltrosApuestas = {};
    if (filtrosLocales.estado)
      f.estado = filtrosLocales.estado as EstadoApuesta;
    if (filtrosLocales.mercado)
      f.mercado = filtrosLocales.mercado as TipoMercadoFutbol;
    if (filtrosLocales.confianza)
      f.confianza = filtrosLocales.confianza as NivelConfianza;
    if (filtrosLocales.desde) f.desde = filtrosLocales.desde;
    if (filtrosLocales.hasta) f.hasta = filtrosLocales.hasta;
    if (filtrosLocales.busqueda) f.busqueda = filtrosLocales.busqueda;
    return f;
  }, [filtrosLocales]);

  // Hook de bitacora
  const {
    apuestas,
    resumen,
    cargando,
    error,
    recargar,
    pagina,
    setPagina,
    setFiltros,
  } = useBitacoraFutbol({
    filtrosIniciales: filtrosParaHook,
    tamano: TAMANO_PAGINA,
    cargarAlMontar: true,
  });

  // Actualizar filtros en el hook
  useEffect(() => {
    setFiltros(filtrosParaHook);
    setPagina(1);
  }, [filtrosParaHook, setFiltros, setPagina]);

  // Handler de cambio de filtro
  const handleCambioFiltro = useCallback((campo: string, valor: string) => {
    setFiltrosLocales((prev) => ({ ...prev, [campo]: valor }));
  }, []);

  // Handler de limpiar filtros
  const handleLimpiarFiltros = useCallback(() => {
    setFiltrosLocales({
      estado: '',
      mercado: '',
      confianza: '',
      desde: '',
      hasta: '',
      busqueda: '',
    });
  }, []);

  // Handler de cancelar apuesta
  const handleConfirmarCancelacion = useCallback(async () => {
    if (!apuestaACancelar) return;

    setCancelando(true);
    try {
      await cancelarApuesta(apuestaACancelar.id);
      agregarToast({
        titulo: 'Apuesta cancelada',
        mensaje: 'La apuesta se cancelo correctamente.',
        tipo: 'success',
      });
      setApuestaACancelar(null);
      void recargar();
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al cancelar';
      agregarToast({
        titulo: 'Error',
        mensaje,
        tipo: 'error',
      });
    } finally {
      setCancelando(false);
    }
  }, [apuestaACancelar, agregarToast, recargar]);

  // Calcular total de paginas
  const totalPaginas = Math.ceil(resumen.total / TAMANO_PAGINA);

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => navegarConGate('/futbol', 'futbol.base')}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg
                         border border-neon-cyan/30 bg-futurista-oscuro/50
                         text-neon-cyan hover:bg-neon-cyan/10 hover:border-neon-cyan/50
                         transition-all duration-200 text-sm font-medium"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="hidden sm:inline">Futbol</span>
            </button>

            <div>
              <h1 className="text-2xl font-futurista font-bold text-texto-principal tracking-wider">
                BITACORA FUTBOL
              </h1>
              <p className="text-sm text-texto-secundario">
                Historial de apuestas
              </p>
            </div>
          </div>

          <Boton
            variante="secundario"
            iconoInicio={<RotateCw size={16} />}
            onClick={recargar}
            cargando={cargando}
          >
            Actualizar
          </Boton>
        </div>

        {/* Tarjetas de resumen */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <TarjetaResumen
            titulo="Total"
            valor={resumen.total}
            icono={<Target size={20} className="text-neon-cyan" />}
            loading={cargando}
          />
          <TarjetaResumen
            titulo="Ganadas"
            valor={resumen.ganadas}
            subtitulo={`${resumen.perdidas} perdidas`}
            icono={<CheckCircle size={20} className="text-neon-verde" />}
            colorValor="text-neon-verde"
            loading={cargando}
          />
          <TarjetaResumen
            titulo="ROI"
            valor={formatearPorcentaje(resumen.roi)}
            subtitulo={`Win rate: ${formatearPorcentaje(resumen.winRate)}`}
            icono={<TrendingUp size={20} className="text-neon-magenta" />}
            colorValor={
              (resumen.roi ?? 0) >= 0 ? 'text-neon-verde' : 'text-neon-rojo'
            }
            loading={cargando}
          />
          <TarjetaResumen
            titulo="Ganancia Neta"
            valor={formatearMoneda(resumen.gananciaNeta)}
            subtitulo={`Stake: $${resumen.stakeTotal.toFixed(2)}`}
            icono={<BarChart3 size={20} className="text-neon-amarillo" />}
            colorValor={
              resumen.gananciaNeta >= 0 ? 'text-neon-verde' : 'text-neon-rojo'
            }
            loading={cargando}
          />
        </div>

        {/* Error */}
        {error && (
          <MensajeError
            titulo="Error al cargar bitacora"
            mensaje={error}
            onCerrar={recargar}
          />
        )}

        {/* Filtros */}
        <PanelFiltros
          filtros={filtrosLocales}
          onChange={handleCambioFiltro}
          onLimpiar={handleLimpiarFiltros}
          cargando={cargando}
        />

        {/* Lista de apuestas */}
        {cargando && apuestas.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <Spinner tamano="lg" texto="Cargando apuestas..." centrado />
          </div>
        ) : apuestas.length === 0 ? (
          <EstadoVacio
            mensaje={
              Object.values(filtrosLocales).some(Boolean)
                ? 'No se encontraron apuestas con los filtros seleccionados.'
                : 'Aun no tienes apuestas registradas. Analiza un partido para comenzar.'
            }
          />
        ) : (
          <div className="space-y-3">
            {apuestas.map((apuesta) => (
              <FilaApuesta
                key={apuesta.id}
                apuesta={apuesta}
                onVerPartido={() =>
                  navegar(`/futbol/partidos/${apuesta.partidoId}`)
                }
                onEditar={
                  apuesta.estado === 'PENDIENTE'
                    ? () => {
                        /* TODO: Implementar edicion */
                      }
                    : undefined
                }
                onCancelar={
                  apuesta.estado === 'PENDIENTE'
                    ? () => setApuestaACancelar(apuesta)
                    : undefined
                }
              />
            ))}
          </div>
        )}

        {/* Paginacion */}
        {totalPaginas > 1 && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-texto-secundario">
              Pagina {pagina} de {totalPaginas}
            </span>
            <div className="flex items-center gap-2">
              <Boton
                variante="secundario"
                tamano="sm"
                iconoInicio={<ChevronLeft size={16} />}
                onClick={() => setPagina(Math.max(1, pagina - 1))}
                disabled={pagina <= 1 || cargando}
              >
                Anterior
              </Boton>
              <Boton
                variante="secundario"
                tamano="sm"
                iconoFin={<ChevronRight size={16} />}
                onClick={() => setPagina(Math.min(totalPaginas, pagina + 1))}
                disabled={pagina >= totalPaginas || cargando}
              >
                Siguiente
              </Boton>
            </div>
          </div>
        )}
      </main>

      {/* Modal de confirmacion de cancelacion */}
      {apuestaACancelar && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <Tarjeta className="w-full max-w-md">
            <h3 className="text-lg font-futurista text-texto-principal mb-4">
              Confirmar cancelacion
            </h3>
            <p className="text-texto-secundario mb-2">
              ¿Estas seguro de que deseas cancelar esta apuesta?
            </p>
            <div className="bg-futurista-medio/50 rounded-lg p-3 mb-4">
              <p className="text-texto-principal font-semibold">
                {apuestaACancelar.partido.equipoLocalNombre} vs{' '}
                {apuestaACancelar.partido.equipoVisitanteNombre}
              </p>
              <p className="text-sm text-texto-secundario">
                {apuestaACancelar.lado} {apuestaACancelar.linea} @{' '}
                {apuestaACancelar.cuota.toFixed(2)}
              </p>
            </div>
            <p className="text-xs text-neon-rojo mb-4">
              Esta accion no se puede deshacer.
            </p>
            <div className="flex justify-end gap-3">
              <Boton
                variante="fantasma"
                onClick={() => setApuestaACancelar(null)}
                disabled={cancelando}
              >
                Volver
              </Boton>
              <Boton
                variante="peligro"
                onClick={handleConfirmarCancelacion}
                cargando={cancelando}
                textoCargando="Cancelando..."
              >
                Cancelar Apuesta
              </Boton>
            </div>
          </Tarjeta>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-neon-cyan/10 bg-futurista-negro/80 backdrop-blur-sm">
        <div className="contenedor py-4">
          <p className="text-texto-terciario text-xs text-center uppercase tracking-wider">
            Bitacora de Futbol — Registro historico de apuestas
          </p>
        </div>
      </footer>
    </div>
  );
}
