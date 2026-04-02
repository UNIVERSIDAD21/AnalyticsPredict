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

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ArrowLeft,
  Calendar,
  Clock,
  Trophy,
  MapPin,
  RefreshCw,
} from 'lucide-react';
import {
  Encabezado,
  PanelH2HFutbol,
  PanelHistorialEquipoFutbol,
  ModalGuardarApuestaFutbol,
} from '../organismos';
import { ResultadoAnalisis } from '../organismos/ResultadoAnalisis';
import { MensajeError, PanelDepthPremium } from '../moleculas';
import { Boton, Spinner, Tarjeta } from '../atomos';
import {
  obtenerPartido,
  obtenerH2HPartidos,
  obtenerPartidosEquipoDetalle,
  crearApuesta,
  analizarPartido,
} from '../../servicios/futbol';
import { useToasts } from '../../contextos/Toasts';
import {
  formatearFechaPartidoBogota,
  formatearHoraPartidoBogota,
} from '../../utilidades';
import type {
  PartidoFutbolDetalle,
  PartidoFutbolEstadistico,
  TipoMercadoFutbol,
  NivelConfianza,
  UbicacionHistorialEquipo,
  AnalisisFutbolResponse,
} from '../../tipos/futbol';
import { useAccessPolicy } from '../../contextos/AccessPolicyContext';
import { useGateNavigation } from '../../hooks/useGateNavigation';
import { adaptarAnalisisFutbolAResultadoAnalisis } from '../../utilidades/adaptadores/futbolToNbaAnalisis';

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
  return formatearFechaPartidoBogota(fechaISO, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

function formatearHora(fechaISO: string): string {
  return formatearHoraPartidoBogota(fechaISO);
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

interface RecomendacionSeleccionada {
  mercado: TipoMercadoFutbol;
  lado: 'OVER' | 'UNDER';
  linea: number;
  cuota?: number;
  probabilidad: number;
  confianza: NivelConfianza;
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
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Pagina de analisis detallado de un partido de futbol
 */
export function AnalisisPartidoFutbol() {
  const { can } = useAccessPolicy();
  const { navegarConGate } = useGateNavigation(navegar);

  // Obtener ID del partido de la URL
  const partidoId = extraerPartidoIdDeURL();

  // Estados
  const [partido, setPartido] = useState<PartidoFutbolDetalle | null>(null);
  const [cargandoPartido, setCargandoPartido] = useState(true);
  const [errorPartido, setErrorPartido] = useState<string | null>(null);
  const [mostrarModalGuardar, setMostrarModalGuardar] = useState(false);
  const [guardandoApuesta, setGuardandoApuesta] = useState(false);
  const [recomendacionSeleccionada, setRecomendacionSeleccionada] =
    useState<RecomendacionSeleccionada | null>(null);
  const [h2hPartidos, setH2hPartidos] = useState<PartidoFutbolEstadistico[]>([]);
  const [historialLocal, setHistorialLocal] = useState<PartidoFutbolEstadistico[]>([]);
  const [historialVisitante, setHistorialVisitante] = useState<
    PartidoFutbolEstadistico[]
  >([]);
  const [limiteH2h, setLimiteH2h] = useState(10);
  const [limiteLocal, setLimiteLocal] = useState(0);
  const [limiteVisitante, setLimiteVisitante] = useState(0);
  const [ubicacionLocal, setUbicacionLocal] =
    useState<UbicacionHistorialEquipo>('todos');
  const [ubicacionVisitante, setUbicacionVisitante] =
    useState<UbicacionHistorialEquipo>('todos');
  const [refrescoContexto, setRefrescoContexto] = useState(0);
  const [cargandoContexto, setCargandoContexto] = useState(false);
  const [errorContexto, setErrorContexto] = useState<string | null>(null);
  const [analisis, setAnalisis] = useState<AnalisisFutbolResponse | null>(null);
  const [cargandoAnalisis, setCargandoAnalisis] = useState(false);
  const [errorAnalisis, setErrorAnalisis] = useState<string | null>(null);
  const { agregarToast } = useToasts();
  const historialCacheRef = useRef<Map<string, PartidoFutbolEstadistico[]>>(new Map());
  const h2hCacheRef = useRef<Map<string, PartidoFutbolEstadistico[]>>(new Map());
  const solicitudContextoRef = useRef(0);

  useEffect(() => {
    historialCacheRef.current.clear();
    h2hCacheRef.current.clear();
  }, [partidoId]);

  const obtenerHistorialEquipoCached = useCallback(
    async (
      equipoId: string,
      limite: number,
      ubicacion: UbicacionHistorialEquipo
    ): Promise<PartidoFutbolEstadistico[]> => {
      const claveBase = `${equipoId}|${ubicacion}`;
      const claveExacta = `${claveBase}|${limite}`;

      const exactoCache = historialCacheRef.current.get(claveExacta);
      if (exactoCache) {
        return exactoCache;
      }

      if (limite > 0) {
        const todosCache = historialCacheRef.current.get(`${claveBase}|0`);
        if (todosCache) {
          const recorte = todosCache.slice(0, limite);
          historialCacheRef.current.set(claveExacta, recorte);
          return recorte;
        }
      }

      const data = await obtenerPartidosEquipoDetalle(
        equipoId,
        limite === 0 ? undefined : limite,
        ubicacion
      );
      historialCacheRef.current.set(claveExacta, data);
      if (limite === 0) {
        historialCacheRef.current.set(`${claveBase}|0`, data);
      }
      return data;
    },
    []
  );

  const obtenerH2HCached = useCallback(
    async (
      equipoLocalId: string,
      equipoVisitanteId: string,
      limite: number
    ): Promise<PartidoFutbolEstadistico[]> => {
      const claveEquipos =
        equipoLocalId < equipoVisitanteId
          ? `${equipoLocalId}|${equipoVisitanteId}`
          : `${equipoVisitanteId}|${equipoLocalId}`;
      const clave = `${claveEquipos}|${limite}`;

      const cache = h2hCacheRef.current.get(clave);
      if (cache) {
        return cache;
      }

      const data = await obtenerH2HPartidos(
        equipoLocalId,
        equipoVisitanteId,
        limite === 0 ? undefined : limite
      );
      h2hCacheRef.current.set(clave, data);
      return data;
    },
    []
  );

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
      const equipoLocalId = partido?.equipoLocalId ?? partido?.equipoLocal;
      const equipoVisitanteId = partido?.equipoVisitanteId ?? partido?.equipoVisitante;
      if (!equipoLocalId || !equipoVisitanteId) return;
      const solicitudId = ++solicitudContextoRef.current;
      setCargandoContexto(true);
      setErrorContexto(null);

      try {
        const [h2h, local, visitante] = await Promise.all([
          obtenerH2HCached(equipoLocalId, equipoVisitanteId, limiteH2h),
          obtenerHistorialEquipoCached(equipoLocalId, limiteLocal, ubicacionLocal),
          obtenerHistorialEquipoCached(
            equipoVisitanteId,
            limiteVisitante,
            ubicacionVisitante
          ),
        ]);

        if (solicitudId !== solicitudContextoRef.current) {
          return;
        }

        setH2hPartidos(h2h);
        setHistorialLocal(local);
        setHistorialVisitante(visitante);
      } catch (err) {
        if (solicitudId !== solicitudContextoRef.current) {
          return;
        }
        const mensaje =
          err instanceof Error ? err.message : 'Error al cargar el contexto del partido';
        setErrorContexto(mensaje);
      } finally {
        if (solicitudId === solicitudContextoRef.current) {
          setCargandoContexto(false);
        }
      }
    };

    const timer = window.setTimeout(() => {
      void cargarContexto();
    }, 180);

    return () => window.clearTimeout(timer);
  }, [
    partido,
    limiteH2h,
    limiteLocal,
    limiteVisitante,
    ubicacionLocal,
    ubicacionVisitante,
    refrescoContexto,
    obtenerH2HCached,
    obtenerHistorialEquipoCached,
  ]);

  // Cargar análisis unificado (misma UI que NBA)
  useEffect(() => {
    const cargarAnalisis = async () => {
      if (!partidoId) return;
      setCargandoAnalisis(true);
      setErrorAnalisis(null);
      try {
        const data = await analizarPartido({
          partidoId,
          h2hLimite: limiteH2h,
        });
        setAnalisis(data);
      } catch (err) {
        const mensaje = err instanceof Error ? err.message : 'Error al analizar partido de fútbol';
        setErrorAnalisis(mensaje);
      } finally {
        setCargandoAnalisis(false);
      }
    };

    void cargarAnalisis();
  }, [partidoId, limiteH2h]);

  const equipoLocalId = partido?.equipoLocalId ?? partido?.equipoLocal;
  const equipoVisitanteId = partido?.equipoVisitanteId ?? partido?.equipoVisitante;

  const handleActualizarContexto = useCallback(() => {
    historialCacheRef.current.clear();
    h2hCacheRef.current.clear();
    setRefrescoContexto((valor) => valor + 1);
  }, []);

  const handleSolicitarGuardar = useCallback(
    (recomendacion: RecomendacionSeleccionada) => {
      setRecomendacionSeleccionada(recomendacion);
      setMostrarModalGuardar(true);
    },
    []
  );

  const handleGuardarApuesta = useCallback(
    async (stake: number) => {
      if (!partido || !recomendacionSeleccionada) return;
      setGuardandoApuesta(true);
      try {
        await crearApuesta({
          partidoId: partido.id,
          mercado: recomendacionSeleccionada.mercado,
          lado: recomendacionSeleccionada.lado,
          linea: recomendacionSeleccionada.linea,
          cuota: recomendacionSeleccionada.cuota ?? 0,
          stake,
          notas: `Analisis automatico - Confianza: ${recomendacionSeleccionada.confianza}`,
        });
        setMostrarModalGuardar(false);
        setRecomendacionSeleccionada(null);
        agregarToast({
          titulo: 'Apuesta guardada',
          mensaje: 'Se registro correctamente en la bitacora',
          tipo: 'success',
        });
      } catch (error) {
        agregarToast({
          titulo: 'Error al guardar',
          mensaje: error instanceof Error ? error.message : 'Error desconocido',
          tipo: 'error',
        });
      } finally {
        setGuardandoApuesta(false);
      }
    },
    [agregarToast, partido, recomendacionSeleccionada]
  );

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        {/* Header con navegación + selector visual de deporte */}
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
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

            <div className="flex items-center gap-2 rounded-xl border border-neon-cyan/20 bg-futurista-negro/50 p-1">
              <button
                type="button"
                onClick={() => navegar('/app')}
                className="px-3 py-1.5 rounded-md text-xs font-semibold text-texto-secundario hover:text-texto-principal hover:bg-futurista-oscuro/70"
              >
                Baloncesto
              </button>
              <button
                type="button"
                className="px-3 py-1.5 rounded-md text-xs font-semibold bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40"
              >
                Fútbol
              </button>
            </div>

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
            </div>
          </div>

          <Tarjeta className="border border-neon-magenta/25 bg-gradient-to-r from-neon-cyan/5 via-transparent to-neon-magenta/5">
            <p className="text-xs uppercase tracking-wider text-neon-cyan font-semibold">Análisis unificado</p>
            <p className="text-sm text-texto-secundario mt-1">
              Esta vista usa la misma estructura visual detallada de NBA para mostrar el análisis de fútbol.
            </p>
          </Tarjeta>
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

        <PanelDepthPremium
          modulo="futbol_partido"
          titulo="Depth premium en análisis de partido"
          descripcion="La profundidad premium se activa sobre este análisis para ampliar comparativas, histórico y priorización operativa."
          bullets={[
            'comparativas_multi_mercado sobre corners, goles y disparos',
            'contexto_historico_extendido en H2H e historiales',
            'priorizacion_operativa_avanzada para decidir ejecución',
          ]}
          activo={can('premium.depth')}
          onAbrirDepth={() => navegarConGate('/configuracion', 'premium.depth')}
        />

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

        {/* Panel analizador unificado (misma UI NBA para fútbol) */}
        {cargandoAnalisis && (
          <Tarjeta className="flex items-center justify-center py-10">
            <Spinner tamano="lg" texto="Ejecutando análisis unificado..." centrado />
          </Tarjeta>
        )}

        {errorAnalisis && !cargandoAnalisis && (
          <MensajeError
            titulo="Error en análisis de fútbol"
            mensaje={errorAnalisis}
            onCerrar={() => setErrorAnalisis(null)}
          />
        )}

        {analisis && !cargandoAnalisis && (
          <ResultadoAnalisis
            resultado={adaptarAnalisisFutbolAResultadoAnalisis(analisis)}
            advertencias={[]}
            seleccionUsuario={analisis.recomendaciones?.[0] ? {
              lado: analisis.recomendaciones[0].lado,
              linea: analisis.recomendaciones[0].linea,
            } : null}
            equipoLocalId={equipoLocalId}
            equipoVisitanteId={equipoVisitanteId}
          />
        )}

        {/* H2H */}
        <PanelH2HFutbol
          partidos={h2hPartidos}
          limite={limiteH2h}
          onCambiarLimite={setLimiteH2h}
        />

        {/* Historial individual */}
        {partido && equipoLocalId && equipoVisitanteId && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <PanelHistorialEquipoFutbol
              equipoId={equipoLocalId}
              equipoNombre={partido.equipoLocalNombre}
              partidos={historialLocal}
              limite={limiteLocal}
              onCambiarLimite={setLimiteLocal}
              ubicacion={ubicacionLocal}
              onCambiarUbicacion={setUbicacionLocal}
            />
            <PanelHistorialEquipoFutbol
              equipoId={equipoVisitanteId}
              equipoNombre={partido.equipoVisitanteNombre}
              partidos={historialVisitante}
              limite={limiteVisitante}
              onCambiarLimite={setLimiteVisitante}
              ubicacion={ubicacionVisitante}
              onCambiarUbicacion={setUbicacionVisitante}
            />
          </div>
        )}
      </main>

      {partido && recomendacionSeleccionada && (
        <ModalGuardarApuestaFutbol
          mostrar={mostrarModalGuardar}
          onCerrar={() => {
            setMostrarModalGuardar(false);
            setRecomendacionSeleccionada(null);
          }}
          onGuardar={handleGuardarApuesta}
          cargando={guardandoApuesta}
          partidoInfo={{
            equipoLocal: partido.equipoLocalNombre,
            equipoVisitante: partido.equipoVisitanteNombre,
            fecha: formatearFechaCompleta(partido.fechaPartido),
          }}
          recomendacion={recomendacionSeleccionada}
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
              Predicciones con datos historicos.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

