/**
 * AnalisisPartidoFutbol.tsx — Pagina de analisis de partido de futbol
 *
 * Pagina principal de analisis con:
 * - Header del partido
 * - Comparativa de equipos
 * - Tabs de analisis por categoria (CORNERS/GOLES/DISPAROS)
 * - Recomendaciones de apuestas
 * - Formulario para registrar apuestas
 *
 * URL: /futbol/partidos/:id
 */

import { useCallback, useEffect, useState } from 'react';
import {
  ArrowLeft,
  Calendar,
  Clock,
  Trophy,
  MapPin,
  BookmarkPlus,
  RefreshCw,
} from 'lucide-react';
import {
  Encabezado,
  PanelAnalisisMercadoFutbol,
  PanelH2HFutbol,
  PanelHistorialEquipoFutbol,
  FormularioApuestaFutbol,
} from '../organismos';
import { MensajeError } from '../moleculas';
import { Boton, Spinner, Tarjeta } from '../atomos';
import {
  obtenerPartido,
  obtenerH2HPartidos,
  obtenerPartidosEquipoDetalle,
  crearApuesta,
} from '../../servicios/futbol';
import { useToasts } from '../../contextos/Toasts';
import type {
  PartidoFutbolDetalle,
  TipoMercadoFutbol,
  PartidoFutbolEstadistico,
} from '../../tipos/futbol';
import type { DatosApuestaFutbol } from '../organismos/FormularioApuestaFutbol';

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

/**
 * Extrae el ID del partido de la URL /futbol/partidos/:id
 */
function extraerPartidoIdDeURL(): string | null {
  const path = window.location.pathname;
  const match = path.match(/^\/futbol\/partidos\/([^/]+)$/);
  return match ? match[1] : null;
}

const navegar = (ruta: string) => {
  if (window.location.pathname === ruta) return;
  window.history.pushState({}, '', ruta);
  window.dispatchEvent(new PopStateEvent('popstate'));
};

function formatearFechaCompleta(fechaISO: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleDateString('es-ES', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

function formatearHora(fechaISO: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleTimeString('es-ES', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE SKELETON HEADER
// ══════════════════════════════════════════════════════════════

function SkeletonHeader() {
  return (
    <Tarjeta className="animate-pulse">
      <div className="flex items-center justify-between mb-4">
        <div className="h-4 bg-neon-cyan/20 rounded w-32" />
        <div className="h-6 bg-neon-cyan/10 rounded w-24" />
      </div>
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-neon-cyan/10" />
          <div className="space-y-2">
            <div className="h-6 bg-neon-cyan/20 rounded w-32" />
            <div className="h-4 bg-neon-cyan/10 rounded w-20" />
          </div>
        </div>
        <div className="h-10 bg-neon-cyan/20 rounded w-12" />
        <div className="flex-1 flex items-center justify-end gap-4">
          <div className="space-y-2 text-right">
            <div className="h-6 bg-neon-cyan/20 rounded w-32 ml-auto" />
            <div className="h-4 bg-neon-cyan/10 rounded w-20 ml-auto" />
          </div>
          <div className="w-16 h-16 rounded-full bg-neon-cyan/10" />
        </div>
      </div>
    </Tarjeta>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE HEADER PARTIDO
// ══════════════════════════════════════════════════════════════

interface PropsHeaderPartido {
  partido: PartidoFutbolDetalle;
}

function HeaderPartido({ partido }: PropsHeaderPartido) {
  return (
    <Tarjeta className="relative overflow-hidden">
      {/* Linea decorativa */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-neon-cyan via-neon-magenta to-neon-cyan" />

      {/* Competicion y fecha */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-6">
        <div className="flex items-center gap-3">
          <Trophy size={18} className="text-neon-amarillo" />
          <span className="text-sm text-texto-secundario">
            {partido.competicionNombre}
            {partido.jornada && ` - Jornada ${partido.jornada}`}
          </span>
        </div>
        <div className="flex items-center gap-4 text-sm text-texto-secundario">
          <div className="flex items-center gap-1.5">
            <Calendar size={14} className="text-neon-magenta" />
            <span>{formatearFechaCompleta(partido.fechaPartido)}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock size={14} className="text-neon-cyan" />
            <span>{formatearHora(partido.fechaPartido)}</span>
          </div>
        </div>
      </div>

      {/* Equipos */}
      <div className="flex items-center justify-between gap-4 md:gap-8">
        {/* Equipo Local */}
        <div className="flex-1 flex items-center gap-4">
          {partido.equipoLocalLogo && (
            <img
              src={partido.equipoLocalLogo}
              alt={partido.equipoLocalNombre}
              className="w-16 h-16 md:w-20 md:h-20 object-contain"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          )}
          <div>
            <h2 className="text-xl md:text-2xl font-futurista font-bold text-texto-principal tracking-wider">
              {partido.equipoLocalNombre}
            </h2>
            <div className="flex items-center gap-1.5 text-sm text-neon-cyan">
              <MapPin size={12} />
              <span>Local</span>
            </div>
          </div>
        </div>

        {/* VS */}
        <div className="flex flex-col items-center">
          <span className="text-2xl md:text-3xl font-futurista font-bold text-neon-magenta">
            VS
          </span>
        </div>

        {/* Equipo Visitante */}
        <div className="flex-1 flex items-center justify-end gap-4">
          <div className="text-right">
            <h2 className="text-xl md:text-2xl font-futurista font-bold text-texto-principal tracking-wider">
              {partido.equipoVisitanteNombre}
            </h2>
            <div className="flex items-center justify-end gap-1.5 text-sm text-neon-magenta">
              <span>Visitante</span>
              <MapPin size={12} />
            </div>
          </div>
          {partido.equipoVisitanteLogo && (
            <img
              src={partido.equipoVisitanteLogo}
              alt={partido.equipoVisitanteNombre}
              className="w-16 h-16 md:w-20 md:h-20 object-contain"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          )}
        </div>
      </div>
    </Tarjeta>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE MODAL FORMULARIO APUESTA
// ══════════════════════════════════════════════════════════════

interface PropsModalApuesta {
  abierto: boolean;
  partidoId: string;
  nombrePartido: string;
  valoresIniciales?: {
    mercado?: TipoMercadoFutbol;
    lado?: 'OVER' | 'UNDER';
    linea?: number;
  };
  onCerrar: () => void;
  onGuardado: () => void;
}

function ModalApuesta({
  abierto,
  partidoId,
  nombrePartido,
  valoresIniciales,
  onCerrar,
  onGuardado,
}: PropsModalApuesta) {
  const [guardando, setGuardando] = useState(false);
  const { agregarToast } = useToasts();

  const handleSubmit = async (datos: DatosApuestaFutbol) => {
    setGuardando(true);
    try {
      await crearApuesta({
        partidoId: datos.partidoId,
        mercado: datos.mercado,
        lado: datos.lado,
        linea: datos.linea,
        cuota: datos.cuota,
        stake: datos.stake,
        casaApuestas: datos.casaApuestas,
        notas: datos.notas,
      });
      agregarToast({
        titulo: 'Apuesta registrada',
        mensaje: 'La apuesta se guardo correctamente en la bitacora.',
        tipo: 'success',
      });
      onGuardado();
      onCerrar();
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al guardar';
      agregarToast({
        titulo: 'Error al guardar',
        mensaje,
        tipo: 'error',
      });
    } finally {
      setGuardando(false);
    }
  };

  if (!abierto) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 overflow-y-auto">
      <div className="w-full max-w-2xl my-8">
        <FormularioApuestaFutbol
          partidoId={partidoId}
          nombrePartido={nombrePartido}
          onSubmit={handleSubmit}
          onCancelar={onCerrar}
          cargando={guardando}
          valoresIniciales={valoresIniciales}
        />
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Pagina de analisis detallado de un partido de futbol
 */
export function AnalisisPartidoFutbol() {
  // Obtener ID del partido de la URL
  const partidoId = extraerPartidoIdDeURL();

  // Estados
  const [partido, setPartido] = useState<PartidoFutbolDetalle | null>(null);
  const [cargandoPartido, setCargandoPartido] = useState(true);
  const [errorPartido, setErrorPartido] = useState<string | null>(null);
  const [modalApuestaAbierto, setModalApuestaAbierto] = useState(false);
  const [valoresFormulario, setValoresFormulario] = useState<{
    mercado?: TipoMercadoFutbol;
    lado?: 'OVER' | 'UNDER';
    linea?: number;
  }>({});
  const [h2hPartidos, setH2hPartidos] = useState<PartidoFutbolEstadistico[]>([]);
  const [historialLocal, setHistorialLocal] = useState<PartidoFutbolEstadistico[]>([]);
  const [historialVisitante, setHistorialVisitante] = useState<
    PartidoFutbolEstadistico[]
  >([]);
  const [limiteH2h, setLimiteH2h] = useState(10);
  const [limiteLocal, setLimiteLocal] = useState(10);
  const [limiteVisitante, setLimiteVisitante] = useState(10);
  const [refrescoContexto, setRefrescoContexto] = useState(0);
  const [cargandoContexto, setCargandoContexto] = useState(false);
  const [errorContexto, setErrorContexto] = useState<string | null>(null);

  // Cargar partido
  useEffect(() => {
    const cargarPartido = async () => {
      if (!partidoId) return;
      setCargandoPartido(true);
      setErrorPartido(null);

      try {
        const data = await obtenerPartido(partidoId);
        setPartido(data);
      } catch (err) {
        const mensaje =
          err instanceof Error ? err.message : 'Error al cargar el partido';
        setErrorPartido(mensaje);
      } finally {
        setCargandoPartido(false);
      }
    };

    void cargarPartido();
  }, [partidoId]);

  // Cargar contexto H2H e historial individual
  useEffect(() => {
    const cargarContexto = async () => {
      if (!partido?.equipoLocalId || !partido?.equipoVisitanteId) return;
      setCargandoContexto(true);
      setErrorContexto(null);

      try {
        const [h2h, local, visitante] = await Promise.all([
          obtenerH2HPartidos(
            partido.equipoLocalId,
            partido.equipoVisitanteId,
            limiteH2h
          ),
          obtenerPartidosEquipoDetalle(partido.equipoLocalId, limiteLocal),
          obtenerPartidosEquipoDetalle(partido.equipoVisitanteId, limiteVisitante),
        ]);
        setH2hPartidos(h2h);
        setHistorialLocal(local);
        setHistorialVisitante(visitante);
      } catch (err) {
        const mensaje =
          err instanceof Error ? err.message : 'Error al cargar el contexto del partido';
        setErrorContexto(mensaje);
      } finally {
        setCargandoContexto(false);
      }
    };

    void cargarContexto();
  }, [partido, limiteH2h, limiteLocal, limiteVisitante, refrescoContexto]);

  const handleActualizarContexto = useCallback(() => {
    setRefrescoContexto((valor) => valor + 1);
  }, []);

  // Nombre del partido para el formulario
  const nombrePartido = partido
    ? `${partido.equipoLocalNombre} vs ${partido.equipoVisitanteNombre}`
    : '';

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        {/* Header con navegacion */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <button
            type="button"
            onClick={() => navegar('/futbol')}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg
                       border border-neon-cyan/30 bg-futurista-oscuro/50
                       text-neon-cyan hover:bg-neon-cyan/10 hover:border-neon-cyan/50
                       transition-all duration-200 text-sm font-medium self-start"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Volver a partidos</span>
          </button>

          <div className="flex items-center gap-3">
            <Boton
              variante="secundario"
              tamano="sm"
              iconoInicio={<RefreshCw size={16} />}
              onClick={handleActualizarContexto}
              cargando={cargandoContexto}
            >
              Actualizar datos
            </Boton>
            <Boton
              variante="primario"
              tamano="sm"
              iconoInicio={<BookmarkPlus size={16} />}
              onClick={() => setModalApuestaAbierto(true)}
              disabled={!partido}
            >
              Nueva Apuesta
            </Boton>
          </div>
        </div>

        {/* Error de partido */}
        {errorPartido && (
          <MensajeError
            titulo="Error al cargar partido"
            mensaje={errorPartido}
            onCerrar={() => navegar('/futbol')}
          />
        )}

        {/* Loading de partido */}
        {cargandoPartido && <SkeletonHeader />}

        {/* Header del partido */}
        {partido && !cargandoPartido && <HeaderPartido partido={partido} />}

        {/* Estado de carga del contexto */}
        {cargandoContexto && (
          <Tarjeta className="flex flex-col items-center justify-center py-12 space-y-4">
            <Spinner tamano="lg" texto="Cargando contexto..." centrado />
            <p className="text-sm text-texto-secundario text-center max-w-md">
              Recuperando H2H e historiales individuales con corners, goles y disparos.
            </p>
          </Tarjeta>
        )}

        {/* Error de contexto */}
        {errorContexto && !cargandoContexto && (
          <MensajeError
            titulo="Error al cargar contexto"
            mensaje={errorContexto}
            onCerrar={handleActualizarContexto}
          />
        )}

        {partido && (!partido.equipoLocalId || !partido.equipoVisitanteId) && (
          <Tarjeta className="text-sm text-texto-secundario">
            No se pudieron obtener los IDs de los equipos para cargar el contexto H2H.
          </Tarjeta>
        )}

        {/* Panel analizador */}
        {partido && (
          <PanelAnalisisMercadoFutbol
            equipoLocalId={partido.equipoLocalId ?? ''}
            equipoVisitanteId={partido.equipoVisitanteId ?? ''}
            equipoLocalNombre={partido.equipoLocalNombre}
            equipoVisitanteNombre={partido.equipoVisitanteNombre}
            h2h={h2hPartidos}
            historialLocal={historialLocal}
            historialVisitante={historialVisitante}
          />
        )}

        {/* H2H */}
        <PanelH2HFutbol
          partidos={h2hPartidos}
          limite={limiteH2h}
          onCambiarLimite={setLimiteH2h}
        />

        {/* Historial individual */}
        {partido && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <PanelHistorialEquipoFutbol
              equipoId={partido.equipoLocalId ?? ''}
              equipoNombre={partido.equipoLocalNombre}
              partidos={historialLocal}
              limite={limiteLocal}
              onCambiarLimite={setLimiteLocal}
            />
            <PanelHistorialEquipoFutbol
              equipoId={partido.equipoVisitanteId ?? ''}
              equipoNombre={partido.equipoVisitanteNombre}
              partidos={historialVisitante}
              limite={limiteVisitante}
              onCambiarLimite={setLimiteVisitante}
            />
          </div>
        )}
      </main>

      {/* Modal de apuesta */}
      {partido && (
        <ModalApuesta
          abierto={modalApuestaAbierto}
          partidoId={partido.id}
          nombrePartido={nombrePartido}
          valoresIniciales={valoresFormulario}
          onCerrar={() => {
            setModalApuestaAbierto(false);
            setValoresFormulario({});
          }}
          onGuardado={() => {
            // Podria recargar estadisticas aqui si fuera necesario
          }}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-neon-cyan/10 bg-futurista-negro/80 backdrop-blur-sm">
        <div className="contenedor py-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-2 text-center md:text-left">
            <p className="text-texto-terciario text-xs uppercase tracking-wider">
              Analisis de Partido — Modelos de Corners, Goles y Disparos
            </p>
            <p className="text-texto-terciario/60 text-xs">
              Predicciones calibradas con datos historicos.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
