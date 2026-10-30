import type { ResultadoVista } from '../../tipos/resultadoVista';
/**
 * PaginaFutbol.tsx — módulo fútbol alineado al canon NBA.
 *
 * Regla de producto: mismo flujo/base visual de NBA; solo cambia el contenido del dominio.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { CreadorCombinada, Encabezado, FormularioAnalisis, ModalGuardarApuestaFutbol } from '../organismos';
import { ResultadoAnalisis } from '../organismos/ResultadoAnalisis';
import { MensajeError, ProgresoAnalisis, TarjetaCalidadDatosFutbol } from '../moleculas';
import { Boton, Tarjeta } from '../atomos';
import { Spinner } from '../atomos/Spinner';
import { CatalogoFutbol } from '../moleculas/CatalogoFutbol';
import { BotonFavorito } from '../moleculas/FavoritosLocales';
import { favoritoEquipo } from '../../servicios/favoritosLocales';
import { HistoricoAnalisisFutbol } from '../moleculas/HistoricoAnalisisFutbol';
import { puedeAnalizarPartido, requiereReconstruccion, fechaVisiblePartido } from '../../utilidades/agendaFutbol';
import { analizarPartido, crearApuesta, obtenerH2HPartidos, obtenerPartido, obtenerPartidosEquipoDetalle } from '../../servicios/futbol';
import { useToasts } from '../../contextos/Toasts';
import { adaptarAnalisisFutbolAResultadoAnalisis } from '../../utilidades/adaptadores/futbolToNbaAnalisis';
import { prepararApuestaGuardableFutbol } from '../../utilidades/seleccionApuestaFutbol';
import { archivarPartidoGuardado, guardarPartidoParaRevisar, listarPartidosGuardados } from '../../servicios/bitacora';
import type {
  AnalisisFutbolResponse,
  PartidoFutbolEstadistico,
  PartidoFutbolResumen,
  RecomendacionApuesta,
  TipoMercadoFutbol,
  UbicacionHistorialEquipo,
} from '../../tipos/futbol';
import type { Equipo, Mercado, PartidoResumen, PeticionAnalisis, SeleccionCombinadaInput } from '../../tipos';

const navegar = (ruta: string) => {
  if (window.location.pathname === ruta && window.location.search === '') return;
  window.history.pushState({}, '', ruta);
  window.dispatchEvent(new PopStateEvent('popstate'));
};

type CategoriaSeleccionFutbol = 'GOLES' | 'CORNERS' | 'TIROS_AL_ARCO';
type PeriodoSeleccionFutbol = '1T' | '2T' | 'FT';
type AlcanceSeleccionFutbol = 'TOTAL' | 'LOCAL' | 'VISITANTE';

interface SeleccionCanonicaFutbol {
  categoria: CategoriaSeleccionFutbol;
  periodo: PeriodoSeleccionFutbol;
  alcance: AlcanceSeleccionFutbol;
  lado: 'OVER' | 'UNDER';
  linea: number;
  cuotas: {
    over?: number;
    under?: number;
  };
  partidoId: string;
  mercadoObjetivo: TipoMercadoFutbol;
  trazabilidad: {
    idSeleccion: string;
    origen: 'ui-futbol';
    timestampIso: string;
  };
}

interface RenderCanonicoFutbol {
  seleccion: SeleccionCanonicaFutbol;
  recomendacion: RecomendacionApuesta | null;
  mercadoObjetivo: AnalisisFutbolResponse['objetivo'];
  resultado: ResultadoVista;
  combinada: SeleccionCombinadaInput | null;
  guardar: {
    mercado: TipoMercadoFutbol;
    lado: 'OVER' | 'UNDER';
    linea: number;
    cuota: number;
    probabilidad: number | null;
    confianza: RecomendacionApuesta['confianza'] | null;
    valorEsperado: number | null;
    trazabilidad: string;
    tieneRecomendacion: boolean;
  };
}

function resolverMercadoCanonicoFutbol(
  categoria: CategoriaSeleccionFutbol,
  alcance: AlcanceSeleccionFutbol,
  periodo: PeriodoSeleccionFutbol,
): TipoMercadoFutbol {
  const periodoTag = periodo;
  if (categoria === 'CORNERS') {
    if (alcance === 'LOCAL') return `CORNERS_LOCAL_${periodoTag}` as TipoMercadoFutbol;
    if (alcance === 'VISITANTE') return `CORNERS_VISITANTE_${periodoTag}` as TipoMercadoFutbol;
    return `CORNERS_${periodoTag}` as TipoMercadoFutbol;
  }
  if (categoria === 'GOLES') {
    if (alcance === 'LOCAL') return `GOLES_LOCAL_${periodoTag}` as TipoMercadoFutbol;
    if (alcance === 'VISITANTE') return `GOLES_VISITANTE_${periodoTag}` as TipoMercadoFutbol;
    return `GOLES_${periodoTag}` as TipoMercadoFutbol;
  }
  if (alcance === 'LOCAL') return `DISPAROS_LOCAL_ARCO_${periodoTag}` as TipoMercadoFutbol;
  if (alcance === 'VISITANTE') return `DISPAROS_VISITANTE_ARCO_${periodoTag}` as TipoMercadoFutbol;
  return `DISPAROS_ARCO_${periodoTag}` as TipoMercadoFutbol;
}

function EstadoVacioFutbol() {
  return <div className="p-6 space-y-3" role="status"><h2 className="text-xl font-semibold">Configura la consulta</h2><p className="text-texto-secundario">Elige mercado, alcance, periodo y línea. El resultado aparecerá aquí cuando ejecutes el análisis.</p><p className="text-sm text-texto-secundario">90 minutos más añadido, sin prórroga ni penales. Las consultas retrospectivas usan un corte anterior al inicio; no son pronósticos emitidos entonces.</p></div>;
}

export function PaginaFutbol() {
  const { agregarToast } = useToasts();

  const [partidoSeleccionadoId, setPartidoSeleccionadoId] = useState('');
  const [agendaAbierta, setAgendaAbierta] = useState(true);
  useEffect(() => { if (partidoSeleccionadoId) setAgendaAbierta(false); }, [partidoSeleccionadoId]);
  const [partidoFueraDeLista, setPartidoFueraDeLista] = useState<PartidoFutbolResumen | null>(null);
  const [partidosGuardadosIds, setPartidosGuardadosIds] = useState<Set<string>>(new Set());
  const [guardandoPartido, setGuardandoPartido] = useState(false);
  const [categoriaMercadoFutbol, setCategoriaMercadoFutbol] = useState<CategoriaSeleccionFutbol>('CORNERS');
  const [alcanceMercadoFutbol, setAlcanceMercadoFutbol] = useState<AlcanceSeleccionFutbol>('TOTAL');
  const [seleccionCanonicaActiva, setSeleccionCanonicaActiva] = useState<SeleccionCanonicaFutbol | null>(null);
  const [analisis, setAnalisis] = useState<AnalisisFutbolResponse | null>(null);
  const [cargandoAnalisis, setCargandoAnalisis] = useState(false);
  const [errorAnalisis, setErrorAnalisis] = useState<string | null>(null);
  const [mostrarGuardar, setMostrarGuardar] = useState(false);
  const [guardandoApuesta, setGuardandoApuesta] = useState(false);

  const [h2hPartidos, setH2hPartidos] = useState<PartidoFutbolEstadistico[]>([]);
  const [historialLocal, setHistorialLocal] = useState<PartidoFutbolEstadistico[]>([]);
  const [historialVisitante, setHistorialVisitante] = useState<PartidoFutbolEstadistico[]>([]);
  const [limiteH2h, setLimiteH2h] = useState(10);
  const [limiteLocal, setLimiteLocal] = useState(10);
  const [limiteVisitante, setLimiteVisitante] = useState(10);
  const [ubicacionLocal, setUbicacionLocal] = useState<UbicacionHistorialEquipo>('todos');
  const [ubicacionVisitante, setUbicacionVisitante] = useState<UbicacionHistorialEquipo>('todos');
  const [cargandoContexto, setCargandoContexto] = useState(false);
  const [errorContexto, setErrorContexto] = useState<string | null>(null);
  const [equipoLocalIdReal, setEquipoLocalIdReal] = useState<string>('');
  const [equipoVisitanteIdReal, setEquipoVisitanteIdReal] = useState<string>('');

  const historialCacheRef = useRef<Map<string, PartidoFutbolEstadistico[]>>(new Map());
  const h2hCacheRef = useRef<Map<string, PartidoFutbolEstadistico[]>>(new Map());
  const seleccionInicialAplicada = useRef(false);

  const [partidos, setPartidos] = useState<PartidoFutbolResumen[]>([]);
  const [cargandoPartidos, setCargandoPartidos] = useState(true);
  const [instanteAgenda, setInstanteAgenda] = useState(Date.now());
  const [errorPartidos, setErrorPartidos] = useState<string | null>(null);
  const [revisionCatalogo, setRevisionCatalogo] = useState(0);
  const [configuracionHistorico, setConfiguracionHistorico] = useState<{ competicionId: string; ids: string[] }>({ competicionId: '', ids: [] });
  const analisisSecuencia = useRef(0);
  const analisisControlador = useRef<AbortController | null>(null);
  const contextoSecuencia = useRef(0);
  const limpiarResultado = useCallback(() => {
    analisisSecuencia.current += 1;
    analisisControlador.current?.abort();
    setAnalisis(null); setSeleccionCanonicaActiva(null); setErrorAnalisis(null); setCargandoAnalisis(false);
  }, []);
  const cambiarTemporadas = useCallback((competicionId: string, ids: string[]) => {
    limpiarResultado(); setConfiguracionHistorico({ competicionId, ids });
  }, [limpiarResultado]);
  const cambiarCatalogo = useCallback(() => {
    limpiarResultado(); contextoSecuencia.current += 1;
    setPartidoSeleccionadoId(''); setPartidoFueraDeLista(null);
    setConfiguracionHistorico({ competicionId: '', ids: [] });
    setH2hPartidos([]); setHistorialLocal([]); setHistorialVisitante([]);
    setEquipoLocalIdReal(''); setEquipoVisitanteIdReal(''); setCargandoContexto(false);
  }, [limpiarResultado]);
  const recargar = useCallback(() => setRevisionCatalogo(n => n + 1), []);
  useEffect(() => () => { analisisControlador.current?.abort(); analisisSecuencia.current += 1; contextoSecuencia.current += 1; }, []);
  useEffect(() => {
    const timer = window.setInterval(() => setInstanteAgenda(Date.now()), 15000);
    return () => window.clearInterval(timer);
  }, []);

  const partidosVista = useMemo(() => {
    if (!partidoFueraDeLista || partidos.some((p) => p.id === partidoFueraDeLista.id)) return partidos;
    return [...partidos, partidoFueraDeLista];
  }, [partidoFueraDeLista, partidos]);

  const partidoSeleccionado = useMemo(
    () => partidosVista.find((p) => p.id === partidoSeleccionadoId) ?? null,
    [partidoSeleccionadoId, partidosVista]
  );
  const temporadasCatalogo = useMemo(() => configuracionHistorico.competicionId === partidoSeleccionado?.competicion ? configuracionHistorico.ids : [], [configuracionHistorico, partidoSeleccionado?.competicion]);
  const seleccionAnalizable = partidoSeleccionado ? puedeAnalizarPartido(partidoSeleccionado, instanteAgenda) : false;
  const seleccionRetrospectiva = Boolean(partidoSeleccionado && (requiereReconstruccion(partidoSeleccionado, instanteAgenda) || analisis?.modo === 'HISTORICO_RECONSTRUIDO'));
  useEffect(() => {
    if (partidoSeleccionadoId && !seleccionAnalizable) limpiarResultado();
  }, [partidoSeleccionadoId, seleccionAnalizable, limpiarResultado]);
  useEffect(() => {
    if (seleccionRetrospectiva) setMostrarGuardar(false);
  }, [seleccionRetrospectiva]);

  useEffect(() => {
    if (seleccionInicialAplicada.current || cargandoPartidos) return;
    const qs = new URLSearchParams(window.location.search);
    const porQuery = qs.get('partidoId');
    if (porQuery) {
      seleccionInicialAplicada.current = true;
      setPartidoSeleccionadoId(porQuery);
      if (!partidos.some((p) => p.id === porQuery)) {
        void obtenerPartido(porQuery, false)
          .then(setPartidoFueraDeLista)
          .catch((error) => agregarToast({
            titulo: 'No se pudo abrir el partido guardado',
            mensaje: error instanceof Error ? error.message : 'Partido no disponible',
            tipo: 'error',
          }));
      }
      return;
    }
    seleccionInicialAplicada.current = true;
  }, [agregarToast, cargandoPartidos, partidoSeleccionadoId, partidos]);

  useEffect(() => {
    void listarPartidosGuardados()
      .then((respuesta) => setPartidosGuardadosIds(new Set(respuesta.partidos.map((partido) => partido.partido_id))))
      .catch(() => setPartidosGuardadosIds(new Set()));
  }, []);

  const equiposAnalisis: Equipo[] = useMemo(() => {
    const catalogo = new Map<string, Equipo>();
    for (const partido of partidosVista) {
      for (const [id, nombre] of [[partido.equipoLocal, partido.equipoLocalNombre], [partido.equipoVisitante, partido.equipoVisitanteNombre]]) {
        catalogo.set(String(id), { id: String(id), nombre, nombre_corto: nombre, abreviatura: nombre.slice(0, 3).toUpperCase() });
      }
    }
    return [...catalogo.values()];
  }, [partidosVista]);

  const partidosSelector: PartidoResumen[] = useMemo(() => (
    partidosVista.map((partido) => ({
      id: partido.id,
      fecha_partido: partido.fechaPartido,
      tipo_partido: 'REG',
      equipo_local_id: String(partido.equipoLocal),
      equipo_local_nombre: partido.equipoLocalNombre,
      equipo_visitante_id: String(partido.equipoVisitante),
      equipo_visitante_nombre: partido.equipoVisitanteNombre,
      temporada_id: partido.temporadaId || partido.competicion,
      temporada_nombre: partido.competicionNombre,
      local_total: partido.golesLocal ?? null,
      visitante_total: partido.golesVisitante ?? null,
      finalizado: partido.estado === 'FINALIZADO',
    }))
  ), [partidosVista]);

  const seleccionarPartidoFormulario = useCallback((partido: PartidoResumen | null) => {
    limpiarResultado();
    contextoSecuencia.current += 1;
    setH2hPartidos([]); setHistorialLocal([]); setHistorialVisitante([]);
    setEquipoLocalIdReal(''); setEquipoVisitanteIdReal('');
    setPartidoSeleccionadoId(partido?.id ?? '');
    setConfiguracionHistorico({ competicionId: '', ids: [] });
  }, [limpiarResultado]);

  const seleccionarDesdeAgenda = useCallback((partido: PartidoFutbolResumen) => {
    if (!puedeAnalizarPartido(partido)) return;
    limpiarResultado(); contextoSecuencia.current += 1;
    setH2hPartidos([]); setHistorialLocal([]); setHistorialVisitante([]);
    setEquipoLocalIdReal(''); setEquipoVisitanteIdReal(''); setErrorContexto(null);
    setPartidoFueraDeLista(partido); setPartidoSeleccionadoId(partido.id);
    setConfiguracionHistorico({ competicionId: partido.competicion, ids: [] });
  }, [limpiarResultado]);

  const manejarGuardarPartido = useCallback(async () => {
    if (!partidoSeleccionado) return;
    setGuardandoPartido(true);
    try {
      await guardarPartidoParaRevisar(partidoSeleccionado.id);
      setPartidosGuardadosIds((actuales) => new Set(actuales).add(partidoSeleccionado.id));
      agregarToast({ titulo: 'Partido guardado', mensaje: 'Quedó en Seguimiento para volver a revisarlo. No se registró una apuesta.', tipo: 'success' });
    } catch (error) {
      agregarToast({ titulo: 'No se pudo guardar', mensaje: error instanceof Error ? error.message : 'Intenta de nuevo.', tipo: 'error' });
    } finally {
      setGuardandoPartido(false);
    }
  }, [agregarToast, partidoSeleccionado]);

  const manejarQuitarPartido = useCallback(async () => {
    if (!partidoSeleccionado) return;
    setGuardandoPartido(true);
    try {
      await archivarPartidoGuardado(partidoSeleccionado.id);
      setPartidosGuardadosIds((actuales) => {
        const nuevos = new Set(actuales);
        nuevos.delete(partidoSeleccionado.id);
        return nuevos;
      });
      agregarToast({ titulo: 'Partido quitado', mensaje: 'Se retiró de tu lista de partidos guardados.', tipo: 'success' });
    } catch (error) {
      agregarToast({ titulo: 'No se pudo quitar', mensaje: error instanceof Error ? error.message : 'Intenta de nuevo.', tipo: 'error' });
    } finally {
      setGuardandoPartido(false);
    }
  }, [agregarToast, partidoSeleccionado]);

  const opcionesMercadoFutbol: Array<{ valor: Mercado; etiqueta: string }> = useMemo(
    () => [
      { valor: 'Q1', etiqueta: 'Primer tiempo' },
      { valor: 'Q2', etiqueta: 'Segundo tiempo' },
      { valor: 'COMPLETO', etiqueta: 'Juego completo' },
    ],
    []
  );

  const unidadLineaLabel = useMemo(() => {
    if (categoriaMercadoFutbol === 'CORNERS') return 'corners';
    if (categoriaMercadoFutbol === 'GOLES') return 'goles';
    return 'tiros a puerta';
  }, [categoriaMercadoFutbol]);

  const renderCanonico = useMemo<RenderCanonicoFutbol | null>(() => {
    if (!analisis || !partidoSeleccionado || !seleccionCanonicaActiva) return null;

    const resultado = adaptarAnalisisFutbolAResultadoAnalisis(analisis, { h2h: h2hPartidos, historialLocal, historialVisitante });
    const recomendacion = analisis.recomendaciones.find((rec) => (
      rec.mercado === seleccionCanonicaActiva.mercadoObjetivo
      && rec.lado === seleccionCanonicaActiva.lado
      && Math.abs(rec.linea - seleccionCanonicaActiva.linea) < 1e-9
    )) ?? null;

    const guardable = prepararApuestaGuardableFutbol(analisis, {
      mercado: seleccionCanonicaActiva.mercadoObjetivo,
      lado: seleccionCanonicaActiva.lado,
      linea: seleccionCanonicaActiva.linea,
      cuotas: seleccionCanonicaActiva.cuotas,
      trazabilidad: seleccionCanonicaActiva.trazabilidad,
    });
    const cuotaCanonica = guardable.cuota;

    const periodoCombinada: Mercado = seleccionCanonicaActiva.periodo === '1T'
      ? 'Q1'
      : (seleccionCanonicaActiva.periodo === '2T' ? 'Q2' : 'COMPLETO');

    const probabilidadCanonica = guardable.probabilidad ?? 0;
    const mediaCanonica = resultado.mejor_apuesta_detalle?.prediccion_media
      ?? analisis.objetivo.mediaObjetivo
      ?? null;
    const desviacionCanonica = resultado.mejor_apuesta_detalle?.prediccion_desviacion
      ?? analisis.objetivo.desviacionObjetivo
      ?? null;

    const combinada: SeleccionCombinadaInput | null = recomendacion
      ? {
          partido_id: partidoSeleccionado.id,
          equipo_local: partidoSeleccionado.equipoLocalNombre,
          equipo_visitante: partidoSeleccionado.equipoVisitanteNombre,
          fecha_partido: partidoSeleccionado.fechaPartido,
          mercado: periodoCombinada,
          lado: seleccionCanonicaActiva.lado,
          linea: seleccionCanonicaActiva.linea,
          cuota: cuotaCanonica,
          cuota_over: seleccionCanonicaActiva.cuotas.over ?? recomendacion.cuotaOver ?? null,
          cuota_under: seleccionCanonicaActiva.cuotas.under ?? recomendacion.cuotaUnder ?? null,
          probabilidad_sistema: probabilidadCanonica,
          prediccion_media: mediaCanonica,
          prediccion_desviacion: desviacionCanonica,
          confianza_sistema: recomendacion.confianza === 'MUY_ALTA'
            ? 'ALTA'
            : (recomendacion.confianza === 'MUY_BAJA' ? 'BAJA' : (recomendacion.confianza as 'ALTA' | 'MEDIA' | 'BAJA')),
          valor_esperado_individual: resultado.mejor_apuesta_detalle?.valor_esperado ?? recomendacion.valorEsperado ?? null,
          razones: [{ razon: recomendacion.razon }],
        }
      : null;

    return {
      seleccion: seleccionCanonicaActiva,
      recomendacion,
      mercadoObjetivo: analisis.objetivo,
      resultado,
      combinada,
      guardar: {
        ...guardable,
      },
    };
  }, [analisis, h2hPartidos, historialLocal, historialVisitante, partidoSeleccionado, seleccionCanonicaActiva]);

  const cargarContexto = useCallback(async (partido: PartidoFutbolResumen) => {
    const secuencia = ++contextoSecuencia.current;
    try {
      setCargandoContexto(true);
      setErrorContexto(null);

      const detalle = await obtenerPartido(partido.id, false);
      if (secuencia !== contextoSecuencia.current) return;
      const localId = String(detalle.equipoLocalId || detalle.equipoLocal || '');
      const visitanteId = String(detalle.equipoVisitanteId || detalle.equipoVisitante || '');

      if (!localId || !visitanteId) {
        setH2hPartidos([]);
        setHistorialLocal([]);
        setHistorialVisitante([]);
        setEquipoLocalIdReal('');
        setEquipoVisitanteIdReal('');
        setErrorContexto('No se pudo resolver el ID real de los equipos para H2H/historial.');
        return;
      }

      setEquipoLocalIdReal(localId);
      setEquipoVisitanteIdReal(visitanteId);

      const ambito = { competicionId: partido.competicion, antesDe: new Date(Math.min(Date.now(), Date.parse(partido.fechaPartido))).toISOString() };
      const llaveAmbito = `${partido.competicion}|${partido.fechaPartido}`;
      const keyH2h = `${llaveAmbito}|${localId}|${visitanteId}|${limiteH2h}`;
      const keyLocal = `${llaveAmbito}|${localId}|${limiteLocal}|${ubicacionLocal}`;
      const keyVisit = `${llaveAmbito}|${visitanteId}|${limiteVisitante}|${ubicacionVisitante}`;

      const h2h = h2hCacheRef.current.get(keyH2h) || await obtenerH2HPartidos(localId, visitanteId, limiteH2h, ambito);
      const local = historialCacheRef.current.get(keyLocal) || await obtenerPartidosEquipoDetalle(localId, limiteLocal, ubicacionLocal, ambito);
      const visit = historialCacheRef.current.get(keyVisit) || await obtenerPartidosEquipoDetalle(visitanteId, limiteVisitante, ubicacionVisitante, ambito);

      if (secuencia !== contextoSecuencia.current) return;
      h2hCacheRef.current.set(keyH2h, h2h);
      historialCacheRef.current.set(keyLocal, local);
      historialCacheRef.current.set(keyVisit, visit);

      setH2hPartidos(h2h);
      setHistorialLocal(local);
      setHistorialVisitante(visit);
    } catch (error) {
      if (secuencia === contextoSecuencia.current) setErrorContexto(error instanceof Error ? error.message : 'No se pudo cargar el contexto del partido');
    } finally {
      if (secuencia === contextoSecuencia.current) setCargandoContexto(false);
    }
  }, [limiteH2h, limiteLocal, limiteVisitante, ubicacionLocal, ubicacionVisitante]);

  useEffect(() => {
    if (!partidoSeleccionado) return;
    void cargarContexto(partidoSeleccionado);
  }, [partidoSeleccionado, cargarContexto]);

  const ejecutarAnalisis = useCallback(async (peticion: PeticionAnalisis) => {
    const partidoIdObjetivo = peticion.partido_id;
    if (!partidoIdObjetivo) {
      setErrorAnalisis('Selección inválida: falta partido_id en la selección canónica.');
      return;
    }
    const partidoVigente = partidosVista.find(p => p.id === partidoIdObjetivo);
    if (!partidoVigente || !puedeAnalizarPartido(partidoVigente)) {
      limpiarResultado();
      setErrorAnalisis('El estado o la fecha de este partido no permite consultar el análisis. Actualiza la agenda.');
      return;
    }

    const periodo: PeriodoSeleccionFutbol = peticion.mercado === 'Q1'
      ? '1T'
      : (peticion.mercado === 'Q2' ? '2T' : 'FT');

    const lineaObjetivo = peticion.linea;
    if (lineaObjetivo === undefined || !Number.isFinite(lineaObjetivo) || lineaObjetivo <= 0) {
      setErrorAnalisis('Selección inválida: línea obligatoria para fútbol.');
      return;
    }

    const ladoObjetivo = peticion.lado;
    if (!ladoObjetivo) {
      setErrorAnalisis('Selección inválida: lado obligatorio para fútbol.');
      return;
    }

    const mercadoObjetivo = resolverMercadoCanonicoFutbol(categoriaMercadoFutbol, alcanceMercadoFutbol, periodo);
    const seleccionCanonica: SeleccionCanonicaFutbol = {
      categoria: categoriaMercadoFutbol,
      periodo,
      alcance: alcanceMercadoFutbol,
      lado: ladoObjetivo,
      linea: lineaObjetivo,
      cuotas: {
        over: peticion.cuota_over,
        under: peticion.cuota_under,
      },
      partidoId: partidoIdObjetivo,
      mercadoObjetivo,
      trazabilidad: {
        idSeleccion: `${partidoIdObjetivo}:${mercadoObjetivo}:${ladoObjetivo}:${lineaObjetivo}`,
        origen: 'ui-futbol',
        timestampIso: new Date().toISOString(),
      },
    };

    if (partidoIdObjetivo !== partidoSeleccionadoId) {
      setPartidoSeleccionadoId(partidoIdObjetivo);
    }

    const cuotasPorLinea = (seleccionCanonica.cuotas.over || seleccionCanonica.cuotas.under)
      ? {
          [`${seleccionCanonica.mercadoObjetivo}|${seleccionCanonica.linea}`]: {
            cuota_over: seleccionCanonica.cuotas.over,
            cuota_under: seleccionCanonica.cuotas.under,
          },
        }
      : undefined;

    const incluirLinea = (base: number[], linea: number): number[] => {
      const valores = [...base, linea];
      return Array.from(new Set(valores.map((v) => Number(v.toFixed(2))))).sort((a, b) => a - b);
    };

    const lineasCorners = categoriaMercadoFutbol === 'CORNERS'
      ? incluirLinea([8.5, 9.5, 10.5, 11.5], seleccionCanonica.linea)
      : undefined;
    const lineasGoles = categoriaMercadoFutbol === 'GOLES'
      ? incluirLinea([1.5, 2.5, 3.5], seleccionCanonica.linea)
      : undefined;
    const lineasDisparos = categoriaMercadoFutbol === 'TIROS_AL_ARCO'
      ? incluirLinea([22.5, 24.5, 26.5], seleccionCanonica.linea)
      : undefined;

    const secuencia = ++analisisSecuencia.current;
    analisisControlador.current?.abort();
    const controlador = new AbortController();
    analisisControlador.current = controlador;
    const partidoObjetivo = partidosVista.find(p => p.id === seleccionCanonica.partidoId);
    try {
      setCargandoAnalisis(true);
      setErrorAnalisis(null);
      setSeleccionCanonicaActiva(seleccionCanonica);
      const data = await analizarPartido({
        partidoId: seleccionCanonica.partidoId,
        h2hLimite: limiteH2h,
        mercadoObjetivo: seleccionCanonica.mercadoObjetivo,
        ladoObjetivo: seleccionCanonica.lado,
        lineaObjetivo: seleccionCanonica.linea,
        lineasCorners,
        lineasGoles,
        lineasDisparos,
        cuotasPorLinea,
        modoHistorico: partidoObjetivo ? requiereReconstruccion(partidoObjetivo) : false,
        soloConsulta: partidoObjetivo ? requiereReconstruccion(partidoObjetivo) : false,
        temporadas: temporadasCatalogo.length ? temporadasCatalogo : undefined,
      }, controlador.signal);
      if (secuencia === analisisSecuencia.current) setAnalisis(data);
    } catch (error) {
      if (!controlador.signal.aborted && secuencia === analisisSecuencia.current) setErrorAnalisis(error instanceof Error ? error.message : 'No se pudo completar el análisis de fútbol');
    } finally {
      if (secuencia === analisisSecuencia.current) setCargandoAnalisis(false);
    }
  }, [alcanceMercadoFutbol, categoriaMercadoFutbol, limiteH2h, partidoSeleccionadoId, partidosVista, temporadasCatalogo, limpiarResultado]);

  const recargarTodo = useCallback(() => {
    historialCacheRef.current.clear();
    h2hCacheRef.current.clear();
    recargar();
    if (partidoSeleccionado) {
      void cargarContexto(partidoSeleccionado);
    }
  }, [cargarContexto, partidoSeleccionado, recargar]);

  const guardarApuesta = useCallback(async (stake: number) => {
    if (!partidoSeleccionado || !renderCanonico?.guardar || requiereReconstruccion(partidoSeleccionado)) return;
    try {
      setGuardandoApuesta(true);
      await crearApuesta({
        partidoId: partidoSeleccionado.id,
        mercado: renderCanonico.guardar.mercado,
        lado: renderCanonico.guardar.lado,
        linea: renderCanonico.guardar.linea,
        cuota: renderCanonico.guardar.cuota,
        stake,
        probabilidadSistema: renderCanonico.guardar.probabilidad,
        confianzaSistema: renderCanonico.guardar.confianza,
        valorEsperado: renderCanonico.guardar.valorEsperado,
        notas: `${renderCanonico.guardar.tieneRecomendacion ? 'Recomendación exacta' : 'Selección manual'} desde análisis fútbol (${renderCanonico.guardar.trazabilidad})`,
      });
      setMostrarGuardar(false);
      agregarToast({ titulo: 'Apuesta guardada', mensaje: 'Se registró en seguimiento.', tipo: 'success' });
    } catch (error) {
      agregarToast({ titulo: 'Error al guardar', mensaje: error instanceof Error ? error.message : 'No se pudo guardar', tipo: 'error' });
    } finally {
      setGuardandoApuesta(false);
    }
  }, [agregarToast, partidoSeleccionado, renderCanonico]);

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main id="contenido-principal" tabIndex={-1} className="flex-1 contenedor py-6 lg:py-8">

        {(errorPartidos || errorContexto) && (
          <div className="mb-6">
            <MensajeError
              titulo="Error de carga"
              mensaje={errorPartidos || errorContexto || 'No se pudieron cargar los datos'}
              onCerrar={recargarTodo}
            />
          </div>
        )}

        <details open={!partidoSeleccionado || agendaAbierta} className="space-y-4">
          <summary id="resumen-agenda-futbol" className="cursor-pointer text-neon-cyan py-2" onClick={e => { e.preventDefault(); if (partidoSeleccionado) setAgendaAbierta(v => !v); }}>
            {partidoSeleccionado ? 'Agenda · elegir otro partido' : 'Agenda de fútbol · elige un partido'}
          </summary>
          <CatalogoFutbol revision={revisionCatalogo} onInicio={cambiarCatalogo} onCargando={setCargandoPartidos}
            onError={setErrorPartidos} onDatos={setPartidos} onSeleccionar={seleccionarDesdeAgenda}
            seleccionadoId={partidoSeleccionadoId} guardadosIds={partidosGuardadosIds} />
        </details>

        {partidoSeleccionado && <div id="configuracion-futbol" className="mt-6 flex scroll-mt-5 flex-col lg:flex-row gap-6 lg:gap-8">
          <div className="w-full lg:w-[400px] xl:w-[450px] flex-shrink-0">
            <div className="lg:sticky lg:top-6 space-y-4">
              {partidoSeleccionado && (
                <Tarjeta className="border border-neon-verde/20">
                  <p className="text-xs uppercase tracking-wider text-texto-secundario">Partido seleccionado</p>
                  <p className="mt-2 font-semibold text-texto-principal">
                    {partidoSeleccionado.equipoLocalNombre} vs {partidoSeleccionado.equipoVisitanteNombre}
                  </p>
                  <p className="mt-1 text-xs text-texto-secundario">
                    {partidoSeleccionado.competicionNombre} · {fechaVisiblePartido(partidoSeleccionado)}
                  </p>
                  {partidoSeleccionado.estado === 'FINALIZADO' && <p className="mt-2 text-sm text-texto-principal">Resultado final: {partidoSeleccionado.golesLocal ?? 'N/D'} – {partidoSeleccionado.golesVisitante ?? 'N/D'}</p>}
                  {seleccionRetrospectiva && <p className="mt-2 text-xs leading-relaxed text-neon-cyan">Consulta con datos anteriores al inicio. {partidoSeleccionado.estado !== 'FINALIZADO' ? 'El estado y resultado del encuentro aún pueden estar pendientes de actualizar.' : 'El resultado de este partido no interviene en el cálculo.'}</p>}
                  <button type="button" className="my-3 text-xs text-neon-cyan" onClick={() => { setAgendaAbierta(true); requestAnimationFrame(() => { const resumen = document.getElementById('resumen-agenda-futbol'); resumen?.focus(); resumen?.scrollIntoView({ behavior: 'instant', block: 'start' }); }); }}>← Elegir otro partido en la agenda</button>
                  <div className="flex flex-wrap gap-x-5"><BotonFavorito favorito={{ tipo: 'competicion', liga: 'futbol', id: partidoSeleccionado.competicion, nombre: partidoSeleccionado.competicionNombre }} />{[[partidoSeleccionado.equipoLocal, partidoSeleccionado.equipoLocalNombre], [partidoSeleccionado.equipoVisitante, partidoSeleccionado.equipoVisitanteNombre]].map(([id, nombre]) => <BotonFavorito key={id} favorito={favoritoEquipo('futbol', id, nombre)} />)}</div>
                  <details className="mt-3"><summary className="cursor-pointer text-sm">Seguimiento en Seguimiento</summary><div className="pt-3">
                  {partidosGuardadosIds.has(partidoSeleccionado.id) ? (
                    <Boton variante="secundario" anchoCompleto onClick={manejarQuitarPartido} disabled={guardandoPartido}>
                      {guardandoPartido ? 'Actualizando…' : 'Quitar de Seguimiento'}
                    </Boton>
                  ) : (
                    <Boton variante="secundario" anchoCompleto onClick={manejarGuardarPartido} disabled={guardandoPartido}>
                      {guardandoPartido ? 'Guardando…' : 'Guardar para revisar'}
                    </Boton>
                  )}
                  <p className="mt-2 text-xs text-texto-secundario">
                    Guardar aquí solo marca el partido en la BD para volver a consultarlo; no crea apuesta ni pick.
                  </p></div></details>
                  <p className="mt-2 text-xs text-neon-amarillo">Análisis exploratorio · probabilidades sin calibrar.</p>
                </Tarjeta>
              )}

              {!seleccionAnalizable && <Tarjeta className="border border-neon-amarillo/30"><p className="text-sm text-neon-amarillo">Estado o fecha por verificar</p><p className="mt-2 text-xs text-texto-secundario">El estado registrado no permite un análisis previo a este encuentro futuro. Actualiza la agenda para consultar sus datos.</p></Tarjeta>}
              {seleccionAnalizable && <>
              <HistoricoAnalisisFutbol key={`historico-${partidoSeleccionado.id}`} partido={partidoSeleccionado} seleccion={temporadasCatalogo} onCambiar={cambiarTemporadas} />

              <Tarjeta className="border border-neon-cyan/20">
                <label htmlFor="categoria-futbol" className="text-xs font-semibold uppercase tracking-wider text-texto-secundario">
                  Mercado fútbol
                </label>
                <select
                  id="categoria-futbol"
                  value={categoriaMercadoFutbol}
                  onChange={(e) => { limpiarResultado(); setCategoriaMercadoFutbol(e.target.value as CategoriaSeleccionFutbol); }}
                  className="mt-2 w-full bg-futurista-negro/60 border border-neon-cyan/30 rounded px-3 py-2 text-sm text-texto-principal"
                >
                  <option value="CORNERS">Corners</option>
                  <option value="GOLES">Goles</option>
                  <option value="TIROS_AL_ARCO">Tiros al arco</option>
                </select>
                <label htmlFor="alcance-futbol" className="block mt-3 text-xs font-semibold uppercase tracking-wider text-texto-secundario">
                  Alcance
                </label>
                <select
                  id="alcance-futbol"
                  value={alcanceMercadoFutbol}
                  onChange={(e) => { limpiarResultado(); setAlcanceMercadoFutbol(e.target.value as AlcanceSeleccionFutbol); }}
                  className="mt-2 w-full bg-futurista-negro/60 border border-neon-cyan/30 rounded px-3 py-2 text-sm text-texto-principal"
                >
                  <option value="TOTAL">Total</option>
                  <option value="LOCAL">Local</option>
                  <option value="VISITANTE">Visitante</option>
                </select>
              </Tarjeta>

              <FormularioAnalisis
                key={`formulario-${partidoSeleccionado.id}`}
                deporte="FUTBOL"
                ocultarSelectorPartido
                onCambiarParametros={limpiarResultado}
                equipos={equiposAnalisis}
                estadisticas={[]}
                onAnalizar={ejecutarAnalisis}
                cargando={cargandoAnalisis}
                cargandoEquipos={cargandoPartidos}
                partidosDisponibles={partidosSelector}
                partidoActual={partidosSelector.find(p => p.id === partidoSeleccionadoId) ?? null}
                onSeleccionarPartido={seleccionarPartidoFormulario}
                opcionesMercado={opcionesMercadoFutbol}
                textoAyudaMercado="Primer/segundo tiempo o 90 minutos más añadido, sin prórroga ni penales. Los campos ausentes permanecen N/D."
                unidadLineaLabel={unidadLineaLabel}
              />
              </>}
              <Boton variante="secundario" anchoCompleto onClick={recargarTodo}>
                Actualizar datos
              </Boton>
            </div>
          </div>

          <div className="flex-1 min-w-0" id="resultado-analisis">
            {cargandoAnalisis && <ProgresoAnalisis />}

            {errorAnalisis && !cargandoAnalisis && (
              <MensajeError
                titulo="Error en el análisis"
                mensaje={errorAnalisis}
                onCerrar={() => setErrorAnalisis(null)}
              />
            )}

            {renderCanonico && !cargandoAnalisis && (
              <div className="space-y-4">
                {(analisis?.advertencias ?? []).map(aviso => <p key={aviso} className="tarjeta text-sm text-neon-amarillo">{aviso}</p>)}
                <TarjetaCalidadDatosFutbol calidad={renderCanonico.mercadoObjetivo.calidadDatos} />

                <ResultadoAnalisis
                  resultado={renderCanonico.resultado}
                  advertencias={[]}
                  seleccionUsuario={{ lado: renderCanonico.seleccion.lado, linea: renderCanonico.seleccion.linea }}
                  equipoLocalId={equipoLocalIdReal || undefined}
                  equipoVisitanteId={equipoVisitanteIdReal || undefined}
                  onGuardar={seleccionRetrospectiva ? undefined : () => setMostrarGuardar(true)}
                />

                {cargandoContexto && (
                  <Tarjeta className="flex items-center justify-center py-12">
                    <Spinner tamano="lg" texto="Cargando contexto del partido..." centrado />
                  </Tarjeta>
                )}
              </div>
            )}

            {renderCanonico && !cargandoAnalisis && !seleccionRetrospectiva && (
              <div className="mt-4">
                <CreadorCombinada seleccionActual={renderCanonico.combinada} />
              </div>
            )}

            {!analisis && !cargandoAnalisis && (
              <div className="tarjeta">
                <EstadoVacioFutbol />
              </div>
            )}
          </div>
        </div>}
      </main>

      {renderCanonico?.guardar && partidoSeleccionado && !seleccionRetrospectiva && (
        <ModalGuardarApuestaFutbol
          mostrar={mostrarGuardar}
          onCerrar={() => setMostrarGuardar(false)}
          onGuardar={guardarApuesta}
          cargando={guardandoApuesta}
          partidoInfo={{
            equipoLocal: partidoSeleccionado.equipoLocalNombre,
            equipoVisitante: partidoSeleccionado.equipoVisitanteNombre,
            fecha: partidoSeleccionado.fechaPartido,
          }}
          recomendacion={{
            mercado: renderCanonico.guardar.mercado,
            lado: renderCanonico.guardar.lado,
            linea: renderCanonico.guardar.linea,
            cuota: renderCanonico.guardar.cuota,
            probabilidad: renderCanonico.guardar.probabilidad,
            confianza: renderCanonico.guardar.confianza,
            esRecomendacion: renderCanonico.guardar.tieneRecomendacion,
          }}
        />
      )}

      <footer className="border-t border-neon-cyan/10 bg-futurista-negro/80 backdrop-blur-sm">
        <div className="contenedor py-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-2 text-center md:text-left">
            <p className="text-texto-terciario text-xs uppercase tracking-wider">
              AnalyticsPredict — Fútbol
            </p>
            <p className="text-texto-terciario/60 text-xs">Las predicciones son orientativas. Apuesta responsablemente.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
