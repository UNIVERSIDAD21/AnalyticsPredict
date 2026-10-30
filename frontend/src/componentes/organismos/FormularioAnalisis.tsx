// hace parte del diseño de analisis
/**
 * FormularioAnalisis.tsx — Formulario principal con diseño futurista
 *
 * Soporta cuotas duales (over/under) para de-vig exacto,
 * indicador de overround en tiempo real, y selector de partido mejorado.
 */

import { useEffect, useMemo, useState, useCallback } from 'react';
import { Search, RotateCcw, Zap } from 'lucide-react';
import { Boton, Tarjeta } from '../atomos';
import {
  SelectorEquipo,
  SelectorMercado,
  SelectorPartido,
  InputLinea,
  InputCuotasDuales,
  IndicadorOverround,
  MensajeError,
  PanelEstadisticasEquipo,
} from '../moleculas';
import {
  Equipo,
  Mercado,
  PeticionAnalisis,
  PeticionAnalisisEnVivo,
  PeticionAnalisisNBA,
  LadoApuesta,
  ModoDevig,
  EstadisticasEquipo,
  TemporadaDisponible,
  PartidoResumen,
} from '../../tipos';
import { buscarEquipo, obtenerTemporadasEquipos, validarPeticionAnalisis } from '../../servicios';
import { esCuotaValida } from '../../utilidades/validadores';
import type { PeticionEuro } from '../../servicios/euroliga';
import { obtenerTemporadasWnba, type FormularioWnba } from '../../servicios/wnba';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface OpcionMercadoCustom {
  valor: Mercado;
  etiqueta: string;
}

interface PropsBaseFormularioAnalisis {
  valoresIniciales?: { id: string; equipoLocal:string; equipoVisitante:string; mercado:Mercado; linea:string; ladoApuesta:LadoApuesta;
    cuotaOver:string; cuotaUnder:string; temporadas:string[]; parciales:[number,number][] };
  /** Lista de equipos disponibles */
  equipos: Equipo[];
  /** Estadísticas de equipos */
  estadisticas?: EstadisticasEquipo[];
  /** Indica si está cargando */
  cargando?: boolean;
  /** Indica si los equipos están cargando */
  cargandoEquipos?: boolean;
  /** Permite inyectar partidos desde módulo (ej: fútbol) */
  partidosDisponibles?: PartidoResumen[];
  /** Opciones de mercado personalizadas por módulo */
  opcionesMercado?: OpcionMercadoCustom[];
  /** Texto de ayuda en selector de mercado */
  textoAyudaMercado?: string;
  /** Unidad semántica del módulo (p.ej. goles/corners/disparos) */
  unidadLineaLabel?: string;
  /** Invalida una salida cuando cambian los parámetros del formulario. */
  onCambiarParametros?: () => void;
  onActualizarPartidos?: () => void;
  onCambiarModo?: (cuartosCompletos: number) => void;
  estadoCalendario?: import('../../servicios/wnba').ComprobacionCalendario;
  partidoActual?: PartidoResumen | null;
  consultaHistorica?: boolean;
  /** La agenda de fútbol ya permite seleccionar y cambiar el encuentro. */
  ocultarSelectorPartido?: boolean;
  onSeleccionarPartido?: (partido: PartidoResumen | null) => void;
}

type PropsFormularioAnalisis = PropsBaseFormularioAnalisis & (
  | { deporte: 'EUROLIGA'; onAnalizar: (peticion: PeticionEuro, ladoSeleccionado?: LadoApuesta) => void }
  | { deporte: 'WNBA'; onAnalizar: (peticion: FormularioWnba, ladoSeleccionado?: LadoApuesta) => void }
  | { deporte?: 'NBA' | 'FUTBOL'; onAnalizar: (peticion: PeticionAnalisisNBA, ladoSeleccionado?: LadoApuesta) => void }
);

interface EstadoFormulario {
  equipoLocal: string;
  equipoVisitante: string;
  mercado: Mercado | '';
  linea: string;
  ladoApuesta: LadoApuesta;
  cuotaOver: string;
  cuotaUnder: string;
}

const ESTADO_INICIAL: EstadoFormulario = {
  equipoLocal: '',
  equipoVisitante: '',
  mercado: '',
  linea: '',
  ladoApuesta: 'OVER',
  cuotaOver: '',
  cuotaUnder: '',
};

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Formulario para configurar y ejecutar análisis de partidos
 */
export function FormularioAnalisis(props: PropsFormularioAnalisis) {
  const {
    equipos,
    estadisticas = [],
    cargando = false,
    cargandoEquipos = false,
    partidosDisponibles,
    opcionesMercado,
    textoAyudaMercado,
    unidadLineaLabel,
    deporte = 'NBA',
    partidoActual,
    consultaHistorica = false,
    ocultarSelectorPartido = false,
    onSeleccionarPartido,
    onCambiarParametros,
    onActualizarPartidos,
    onCambiarModo,
    estadoCalendario,
    valoresIniciales,
  } = props;
  const esEuroliga = deporte === 'EUROLIGA';
  const [cuartos, setCuartos] = useState(0);
  const esWnba = deporte === 'WNBA';
  const esCorteNBA = (deporte === 'NBA' || esWnba) && cuartos > 0;
  const [parciales, setParciales] = useState<[string, string][]>([['', ''], ['', ''], ['', '']]);
  useEffect(() => { onCambiarModo?.(cuartos); }, [cuartos, onCambiarModo]);
  // Estado del formulario
  const [formulario, setFormulario] = useState<EstadoFormulario>(ESTADO_INICIAL);
  const [errores, setErrores] = useState<string[]>([]);
  const [temporadasDisponibles, setTemporadasDisponibles] = useState<TemporadaDisponible[]>([]);
  const [temporadasSeleccionadas, setTemporadasSeleccionadas] = useState<string[]>([]);
  const [cargandoTemporadas, setCargandoTemporadas] = useState(false);
  const [errorTemporadas, setErrorTemporadas] = useState<string | null>(null);
  useEffect(() => {
    if (!valoresIniciales) return;
    const v = valoresIniciales;
    setFormulario({ equipoLocal:v.equipoLocal.toLowerCase(),equipoVisitante:v.equipoVisitante.toLowerCase(),
      mercado:v.mercado,linea:v.linea,ladoApuesta:v.ladoApuesta,cuotaOver:v.cuotaOver,cuotaUnder:v.cuotaUnder });
    setCuartos(v.parciales.length);
    setParciales(Array.from({length:3},(_,i)=>v.parciales[i]?.map(String) as [string,string] ?? ['', '']));
    setTemporadasSeleccionadas(v.temporadas);
  }, [valoresIniciales]);

  // Estado del partido seleccionado (CRÍTICO para registro de predicciones)
  const [partidoInterno, setPartidoInterno] = useState<PartidoResumen | null>(null);
  const partidoSeleccionado = partidoActual === undefined ? partidoInterno : partidoActual;

  useEffect(() => {
    if (!partidoSeleccionado) return;
    setFormulario((prev) => ({ ...prev,
      equipoLocal: partidoSeleccionado.equipo_local_nombre.toLowerCase(),
      equipoVisitante: partidoSeleccionado.equipo_visitante_nombre.toLowerCase(),
    }));
  }, [partidoSeleccionado]);

  // Actualizar campo del formulario
  const actualizarCampo = useCallback(
    <K extends keyof EstadoFormulario>(campo: K, valor: EstadoFormulario[K]) => {
      setFormulario((prev) => ({ ...prev, [campo]: valor }));
      onCambiarParametros?.();
      // Limpiar errores al modificar
      if (errores.length > 0) {
        setErrores([]);
      }
    },
    [errores.length, onCambiarParametros]
  );

  // Resetear formulario
  const resetearFormulario = useCallback(() => {
    setFormulario(ESTADO_INICIAL);
    setErrores([]);
    setTemporadasSeleccionadas([]);
    setTemporadasDisponibles([]);
    setErrorTemporadas(null);
    setPartidoInterno(null);
    onSeleccionarPartido?.(null);
    onCambiarParametros?.();
    setCuartos(0);
    setParciales([['', ''], ['', ''], ['', '']]);
  }, [onSeleccionarPartido, onCambiarParametros]);

  // Manejar selección de partido (autocompleta equipos)
  const manejarSeleccionPartido = useCallback(
    (partido: PartidoResumen | null) => {
      setPartidoInterno(partido);
      onSeleccionarPartido?.(partido);
      onCambiarParametros?.();
      setCuartos(0);
      setParciales([['', ''], ['', ''], ['', '']]);

      if (partido) {
        // Autocompletar equipos desde el partido seleccionado
        setFormulario((prev) => ({
          ...prev,
          equipoLocal: partido.equipo_local_nombre.toLowerCase(),
          equipoVisitante: partido.equipo_visitante_nombre.toLowerCase(),
        }));
      }
    },
    [onSeleccionarPartido, onCambiarParametros]
  );

  const esJuegoCompleto = formulario.mercado === 'COMPLETO';
  const buscarEstadisticas = (nombre: string) =>
    estadisticas.find((equipo) => equipo.nombre.toLowerCase() === nombre.toLowerCase());

  // Equipos seleccionados
  const equipoLocalSeleccionado = useMemo(
    () => buscarEquipo(equipos, formulario.equipoLocal),
    [equipos, formulario.equipoLocal]
  );
  const equipoVisitanteSeleccionado = useMemo(
    () => buscarEquipo(equipos, formulario.equipoVisitante),
    [equipos, formulario.equipoVisitante]
  );

  // Manejar envío
  const manejarEnvio = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (cargando) return;
      const scores = parciales.slice(0, cuartos).map(q => q.map(Number) as [number, number]);
      if (cuartos > 0 && (parciales.slice(0, cuartos).some(q => q.some(x => !x.trim())) || scores.some(q => q.some(x => !Number.isInteger(x) || x < 0 || x > 100)))) {
        setErrores(['Completa cada cuarto terminado con enteros entre 0 y 100.']); return;
      }
      if (cuartos > 0 && formulario.mercado !== 'COMPLETO' && Number(formulario.mercado.slice(1)) <= cuartos) {
        setErrores(['Selecciona un cuarto posterior al corte observado o el total de regulación.']); return;
      }

      if (props.deporte === 'EUROLIGA' || props.deporte === 'WNBA') {
        const erroresEuro: string[] = [];
        const scores = parciales.slice(0, cuartos).map(q => q.map(Number) as [number, number]);
        if (!equipoLocalSeleccionado || !equipoVisitanteSeleccionado) erroresEuro.push(`Selecciona los dos equipos ${props.deporte === 'WNBA' ? 'WNBA' : 'Euroliga'}.`);
        if (equipoLocalSeleccionado?.id === equipoVisitanteSeleccionado?.id) erroresEuro.push('Los equipos deben ser distintos.');
        if (equipoLocalSeleccionado?.elegible === false || equipoVisitanteSeleccionado?.elegible === false) erroresEuro.push('Equipo sin muestra suficiente para el predictor.');
        if (!formulario.mercado) erroresEuro.push('Selecciona el mercado.');
        const linea = Number(formulario.linea);
        if (!formulario.linea.trim() || !Number.isFinite(linea) || linea <= 0 || linea > 600) erroresEuro.push('La línea debe ser mayor a 0 y como máximo 600.');
        if (parciales.slice(0, cuartos).some(q => q.some(x => !x.trim())) || scores.some(q => q.some(x => !Number.isInteger(x) || x < 0 || x > 100))) erroresEuro.push('Completa cada cuarto terminado con enteros entre 0 y 100.');
        if (formulario.mercado !== 'COMPLETO' && Number(formulario.mercado.slice(1)) <= cuartos) erroresEuro.push('Selecciona un cuarto posterior al corte observado o el total de regulación.');
        for (const [nombre, valor] of [['Over', formulario.cuotaOver], ['Under', formulario.cuotaUnder]]) {
          if (valor.trim() && (!Number.isFinite(Number(valor)) || Number(valor) <= 1 || Number(valor) > 1000)) erroresEuro.push(`Cuota ${nombre} inválida (mayor a 1 y hasta 1000).`);
        }
        if (erroresEuro.length) { setErrores(erroresEuro); return; }
        if (props.deporte === 'WNBA') {
          if (!cuartos && !temporadasSeleccionadas.length) { setErrores(['Selecciona al menos una temporada WNBA.']); return; }
          const opuesta = formulario.ladoApuesta === 'OVER' ? formulario.cuotaUnder : formulario.cuotaOver;
          const propia = formulario.ladoApuesta === 'OVER' ? formulario.cuotaOver : formulario.cuotaUnder;
          if (!cuartos && opuesta.trim() && !propia.trim()) { setErrores([`Ingresaste cuota del lado contrario. Completa la cuota ${formulario.ladoApuesta} o cambia el lado de apuesta.`]); return; }
          props.onAnalizar({ equipo_local_id: equipoLocalSeleccionado!.id, equipo_visitante_id: equipoVisitanteSeleccionado!.id,
            mercado: formulario.mercado as Mercado, linea, partido_id: partidoSeleccionado?.id,
            temporadas: cuartos ? undefined : temporadasSeleccionadas, parciales: scores, modo: cuartos ? `CIERRE_Q${cuartos}` as FormularioWnba['modo'] : 'PREPARTIDO', lado: formulario.ladoApuesta,
            cuota_over: !cuartos && formulario.cuotaOver.trim() ? Number(formulario.cuotaOver) : undefined,
            cuota_under: !cuartos && formulario.cuotaUnder.trim() ? Number(formulario.cuotaUnder) : undefined }, formulario.ladoApuesta);
          return;
        }
        props.onAnalizar({ equipo_local: equipoLocalSeleccionado!.nombre, equipo_visitante: equipoVisitanteSeleccionado!.nombre,
          mercado: formulario.mercado as PeticionEuro['mercado'], linea, lado: formulario.ladoApuesta,
          cuota_over: formulario.cuotaOver.trim() ? Number(formulario.cuotaOver) : undefined, cuota_under: formulario.cuotaUnder.trim() ? Number(formulario.cuotaUnder) : undefined, partido_id: partidoSeleccionado?.id, parciales: scores }, formulario.ladoApuesta);
        return;
      }

      const ladoSeleccionado = formulario.ladoApuesta;

      // Parsear cuotas
      const cuotaOverValor = formulario.cuotaOver.trim()
        ? parseFloat(formulario.cuotaOver)
        : undefined;
      const cuotaUnderValor = formulario.cuotaUnder.trim()
        ? parseFloat(formulario.cuotaUnder)
        : undefined;

      // Validar cuotas
      const tieneOver = !esCorteNBA && cuotaOverValor !== undefined && esCuotaValida(cuotaOverValor);
      const tieneUnder = !esCorteNBA && cuotaUnderValor !== undefined && esCuotaValida(cuotaUnderValor);

      // Validación UX: no permitir solo cuota del lado opuesto
      const soloLadoOpuesto =
        (ladoSeleccionado === 'OVER' && tieneUnder && !tieneOver) ||
        (ladoSeleccionado === 'UNDER' && tieneOver && !tieneUnder);

      if (soloLadoOpuesto) {
        setErrores([
          `Ingresaste cuota del lado contrario. Completa la cuota ${ladoSeleccionado} o cambia el lado de apuesta.`,
        ]);
        return;
      }

      // Determinar modo_devig
      let modoDevig: ModoDevig | undefined;
      if (tieneOver && tieneUnder) {
        modoDevig = 'estricto';
      } else if (tieneOver || tieneUnder) {
        modoDevig = 'estimado';
      }

      // Cuota legacy para compatibilidad (solo si hay una cuota del lado seleccionado)
      let cuotaLegacy: number | undefined;
      if (ladoSeleccionado === 'OVER' && tieneOver) {
        cuotaLegacy = cuotaOverValor;
      } else if (ladoSeleccionado === 'UNDER' && tieneUnder) {
        cuotaLegacy = cuotaUnderValor;
      }

      const peticion: Partial<PeticionAnalisis> = {
        equipo_local: equipoLocalSeleccionado?.nombre || formulario.equipoLocal,
        equipo_visitante: equipoVisitanteSeleccionado?.nombre || formulario.equipoVisitante,
        mercado: formulario.mercado as Mercado,
        linea: formulario.linea ? parseFloat(formulario.linea) : undefined,
        // Cuotas duales
        cuota_over: tieneOver ? cuotaOverValor : undefined,
        cuota_under: tieneUnder ? cuotaUnderValor : undefined,
        // Legacy (para compatibilidad)
        cuota: cuotaLegacy,
        // Lado y modo
        lado: ladoSeleccionado,
        modo_devig: modoDevig,
        // Contexto
        temporadas: consultaHistorica && !esCorteNBA && temporadasSeleccionadas.length > 0 ? temporadasSeleccionadas : undefined,
        partido_id: partidoSeleccionado?.id,
        temporada_id: partidoSeleccionado?.temporada_id
          ?? (temporadasSeleccionadas.length > 0 ? temporadasSeleccionadas[0] : undefined),
        equipo_local_id: partidoSeleccionado?.equipo_local_id ?? equipoLocalSeleccionado?.id,
        equipo_visitante_id: partidoSeleccionado?.equipo_visitante_id ?? equipoVisitanteSeleccionado?.id,
        fecha_partido: partidoSeleccionado?.fecha_partido,
        tipo_partido: partidoSeleccionado?.tipo_partido as 'PRE' | 'REG' | 'POST' | undefined,
      };

      const erroresValidacion = validarPeticionAnalisis(peticion);
      if (erroresValidacion.length > 0) {
        setErrores(erroresValidacion);
        return;
      }

      if (esCorteNBA) {
        const live: PeticionAnalisisEnVivo = { ...peticion as PeticionAnalisis, marcador_q1: scores[0].join('-') };
        if (cuartos >= 2) live.marcador_q2 = scores[1].join('-');
        if (cuartos >= 3) live.marcador_q3 = scores[2].join('-');
        props.onAnalizar(live, ladoSeleccionado);
      } else props.onAnalizar(peticion as PeticionAnalisis, ladoSeleccionado);
    },
    [formulario, props, cargando, cuartos, parciales, esCorteNBA, equipoLocalSeleccionado, equipoVisitanteSeleccionado, temporadasSeleccionadas, partidoSeleccionado, consultaHistorica]
  );

  useEffect(() => {
    const ids = [equipoLocalSeleccionado?.id, equipoVisitanteSeleccionado?.id].filter(
      Boolean
    ) as string[];

    if ((deporte !== 'NBA' && deporte !== 'WNBA') || (deporte === 'NBA' && !consultaHistorica) || cuartos > 0 || ids.length === 0) {
      setTemporadasDisponibles([]);
      setTemporadasSeleccionadas([]);
      setErrorTemporadas(null);
      setCargandoTemporadas(false);
      return;
    }

    let activo = true;
    const controlador = new AbortController();
    setCargandoTemporadas(true);
    setErrorTemporadas(null);

    (deporte === 'WNBA' ? obtenerTemporadasWnba(ids, controlador.signal) : obtenerTemporadasEquipos(ids, controlador.signal))
      .then((temporadas) => {
        if (!activo) return;

        // Evitar temporadas duplicadas por nombre (pueden existir IDs duplicados legacy en BD).
        const temporadasUnicas = Array.from(
          new Map(temporadas.map((t) => [t.nombre.trim().toLowerCase(), t])).values()
        );

        setTemporadasDisponibles(temporadasUnicas);
        setTemporadasSeleccionadas((prev) => {
          const disponiblesIds = temporadasUnicas.map((temporada) => temporada.id);
          const filtradas = prev.filter((id) => disponiblesIds.includes(id));
          if (filtradas.length === 0 && disponiblesIds.length > 0) {
            return [...disponiblesIds];
          }
          return filtradas;
        });
      })
      .catch((err) => {
        if (!activo) return;
        const mensaje =
          err instanceof Error ? err.message : 'No se pudieron cargar las temporadas';
        setErrorTemporadas(mensaje);
        setTemporadasDisponibles([]);
        setTemporadasSeleccionadas([]);
      })
      .finally(() => {
        if (activo) {
          setCargandoTemporadas(false);
        }
      });

    return () => {
      activo = false;
      controlador.abort();
    };
  }, [deporte, consultaHistorica, cuartos, equipoLocalSeleccionado?.id, equipoVisitanteSeleccionado?.id]);

  const toggleTemporada = useCallback((temporadaId: string) => {
    onCambiarParametros?.();
    setTemporadasSeleccionadas((prev) =>
      prev.includes(temporadaId)
        ? prev.filter((id) => id !== temporadaId)
        : [...prev, temporadaId]
    );
  }, [onCambiarParametros]);

  const seleccionarTodasTemporadas = useCallback(() => {
    onCambiarParametros?.();
    setTemporadasSeleccionadas(temporadasDisponibles.map((temporada) => temporada.id));
  }, [temporadasDisponibles, onCambiarParametros]);

  const limpiarTemporadas = useCallback(() => {
    onCambiarParametros?.();
    setTemporadasSeleccionadas([]);
  }, [onCambiarParametros]);

  return (
    <Tarjeta className="animate-entrada">
      <form onSubmit={manejarEnvio} className="space-y-5">
        {/* Título */}
        <div className="pb-4 border-b border-neon-cyan/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-neon-cyan/10 border border-neon-cyan/30 flex items-center justify-center">
              <Zap className="w-5 h-5 text-neon-cyan" />
            </div>
            <div>
              <h2 className="text-lg font-futurista font-bold text-texto-principal tracking-wider">
                CONFIGURAR ANÁLISIS
              </h2>
              <p className="text-xs text-texto-secundario">
                Selecciona equipos, mercado y tu predicción
              </p>
            </div>
          </div>
        </div>

        {/* Errores de validación */}
        {errores.length > 0 && (
          <MensajeError
            titulo="Corrige los errores"
            mensaje={errores.join('. ')}
            onCerrar={() => setErrores([])}
          />
        )}

        {/* Campos */}
        <div className="space-y-4">
          {/* Selector de Partido - CRÍTICO para registro de predicciones */}
          {!ocultarSelectorPartido && <SelectorPartido
            partidoSeleccionado={partidoSeleccionado}
            onSeleccionar={manejarSeleccionPartido}
            deshabilitado={cargando}
            partidosDisponibles={partidosDisponibles}
            modoRegistro={deporte === 'FUTBOL' ? 'futbol' : deporte === 'WNBA' ? (esCorteNBA ? 'wnba_cierre' : 'wnba') : esEuroliga ? 'euroliga' : esCorteNBA ? 'nba_cierre' : 'nba'}
            onActualizar={onActualizarPartidos}
            estadoCalendario={estadoCalendario}
          />}

          {/* Equipo Local - deshabilitado si hay partido seleccionado */}
          <SelectorEquipo
            etiqueta="Equipo Local"
            equipos={equipos}
            valor={formulario.equipoLocal}
            onChange={(valor) => actualizarCampo('equipoLocal', valor)}
            equipoExcluido={formulario.equipoVisitante}
            deshabilitado={cargando || cargandoEquipos || partidoSeleccionado !== null}
            placeholder={
              partidoSeleccionado
                ? partidoSeleccionado.equipo_local_nombre
                : cargandoEquipos
                  ? 'Cargando...'
                  : 'Selecciona local'
            }
          />

          {/* Equipo Visitante - deshabilitado si hay partido seleccionado */}
          <SelectorEquipo
            etiqueta="Equipo Visitante"
            equipos={equipos}
            valor={formulario.equipoVisitante}
            onChange={(valor) => actualizarCampo('equipoVisitante', valor)}
            equipoExcluido={formulario.equipoLocal}
            deshabilitado={cargando || cargandoEquipos || partidoSeleccionado !== null}
            placeholder={
              partidoSeleccionado
                ? partidoSeleccionado.equipo_visitante_nombre
                : cargandoEquipos
                  ? 'Cargando...'
                  : 'Selecciona visitante'
            }
          />

          {!esEuroliga && <PanelEstadisticasEquipo
            equipoLocal={buscarEstadisticas(formulario.equipoLocal)}
            equipoVisitante={buscarEstadisticas(formulario.equipoVisitante)}
            cargando={cargando}
          />}

          {/* Mercado */}
          <SelectorMercado
            valor={formulario.mercado}
            onChange={(valor) => actualizarCampo('mercado', valor)}
            deshabilitado={cargando}
            opciones={opcionesMercado}
            textoAyuda={textoAyudaMercado}
            cuartosObservados={deporte === 'FUTBOL' ? 0 : cuartos}
          />

          {/* Línea con selector Over/Under */}
          <InputLinea
            valor={formulario.linea}
            onChange={(valor) => actualizarCampo('linea', valor)}
            ladoApuesta={formulario.ladoApuesta}
            onLadoChange={(lado) => actualizarCampo('ladoApuesta', lado)}
            deshabilitado={cargando}
            esJuegoCompleto={esJuegoCompleto}
            unidadLabel={unidadLineaLabel ?? 'puntos'}
            periodoLabel={deporte === 'FUTBOL' ? (formulario.mercado === 'Q1' ? 'primer tiempo' : formulario.mercado === 'Q2' ? 'segundo tiempo' : 'juego completo') : (formulario.mercado === 'COMPLETO' ? (esEuroliga || esCorteNBA || (consultaHistorica && deporte === 'NBA') ? `regulación de ${esWnba || esEuroliga ? 40 : 48} minutos (sin OT)` : 'juego completo (incluye OT)') : formulario.mercado ? `cuarto ${formulario.mercado}` : undefined)}
            placeholderLinea={esEuroliga ? (esJuegoCompleto ? 'Ej: 170.5' : 'Ej: 42.5') : undefined}
          />

          {(deporte === 'NBA' || esWnba || esEuroliga) && <div className="space-y-3">
            <label className="block etiqueta">Modo de análisis
              <select className="input-base w-full mt-2" value={cuartos} disabled={cargando} onChange={e => { setCuartos(Number(e.target.value)); onCambiarParametros?.(); setErrores([]); }}>
                <option value={0}>{consultaHistorica ? 'Reconstrucción anterior al encuentro' : 'Prepartido'}</option>
                {[1, 2, 3].map(q => <option key={q} value={q}>Corte al cierre de Q{q}</option>)}
              </select>
            </label>
            {Array.from({ length: cuartos }, (_, i) => <div key={i} className="grid grid-cols-2 gap-2">
              {[0, 1].map(lado => <label key={lado} className="block text-xs text-texto-secundario">Q{i + 1} {lado === 0 ? 'local' : 'visitante'}
                <input type="number" min="0" max="100" step="1" disabled={cargando} className="input-base w-full mt-1" value={parciales[i][lado]} onChange={e => { setParciales(prev => prev.map((q, j) => j === i ? q.map((x, k) => k === lado ? e.target.value : x) as [string, string] : q)); onCambiarParametros?.(); setErrores([]); }} />
              </label>)}
            </div>)}
            <p className="text-xs text-texto-secundario">{cuartos > 0 ? 'Puntos de cada cuarto completo, no acumulados. No admite reloj ni parciales del cuarto en curso.' : esEuroliga ? 'Cuartos de 10 minutos y total de 40 minutos, sin prórroga.' : consultaHistorica ? 'Reconstrucción de solo consulta con datos anteriores al día del encuentro. No es un pronóstico emitido entonces.' : 'Análisis previo al partido; no utiliza marcadores observados.'}</p>
            {esCorteNBA && <p className="text-xs text-texto-secundario">{esWnba ? 'Condicionamiento del modelo WNBA propio con todos los datos elegibles anteriores al corte' : 'Ajuste de ritmo heurístico con el modelo cargado'}, sin cuotas ni reajuste por temporadas. Probabilidades no calibradas para este corte; {esWnba ? 40 : 48} minutos de regulación, sin prórroga. Solo consulta: no registra apuestas ni predicciones prepartido.</p>}
          </div>}

          {/* Temporadas */}
          {deporte === 'NBA' && !consultaHistorica && !esCorteNBA && <p className="text-xs text-texto-secundario">Consulta del modelo publicado: no entrena ni registra una nueva versión. Su corte se muestra en el resultado; actualizar la BD no actualiza el modelo.</p>}
          {((deporte === 'NBA' && consultaHistorica) || esWnba) && !esCorteNBA && <div className="space-y-2" data-alcance-temporadas>
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-wider text-texto-secundario">
                Temporadas para el análisis
              </label>
              {cargandoTemporadas && (
                <span className="text-xs text-texto-terciario font-mono">Cargando...</span>
              )}
            </div>

            {errorTemporadas && (
              <p className="text-xs text-neon-rojo">{errorTemporadas}</p>
            )}

            {!errorTemporadas && temporadasDisponibles.length === 0 && !cargandoTemporadas && (
              <p className="text-xs text-texto-terciario">
                Selecciona equipos para ver temporadas disponibles.
              </p>
            )}

            {temporadasDisponibles.length > 0 && (
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  {temporadasDisponibles.map((temporada) => {
                    const seleccionada = temporadasSeleccionadas.includes(temporada.id);
                    return (
                      <button
                        key={temporada.id}
                        type="button"
                        onClick={() => toggleTemporada(temporada.id)}
                        className={`px-3 py-1 rounded-full text-xs font-semibold border transition ${seleccionada
                            ? 'bg-neon-cyan/20 border-neon-cyan text-neon-cyan'
                            : 'border-neon-cyan/20 text-texto-terciario hover:text-texto-secundario'
                          }`}
                      >
                        {temporada.nombre}
                      </button>
                    );
                  })}
                </div>

                <div className="flex gap-3 text-xs">
                  <button
                    type="button"
                    onClick={seleccionarTodasTemporadas}
                    className="text-neon-cyan hover:text-neon-cyan/80 font-semibold"
                  >
                    Seleccionar todas
                  </button>
                  <button
                    type="button"
                    onClick={limpiarTemporadas}
                    className="text-texto-terciario hover:text-texto-secundario"
                  >
                    Limpiar selección
                  </button>
                </div>
              </div>
            )}
          </div>}

          {/* Cuotas duales (Over/Under) */}
          {!esCorteNBA && <><InputCuotasDuales
            cuotaOver={formulario.cuotaOver}
            cuotaUnder={formulario.cuotaUnder}
            onCuotaOverChange={(valor) => actualizarCampo('cuotaOver', valor)}
            onCuotaUnderChange={(valor) => actualizarCampo('cuotaUnder', valor)}
            ladoSeleccionado={formulario.ladoApuesta}
            deshabilitado={cargando}
          />

          {/* Indicador de Overround (solo si hay ambas cuotas) */}
          <IndicadorOverround
            cuotaOver={formulario.cuotaOver}
            cuotaUnder={formulario.cuotaUnder}
          /></>}
          {esEuroliga && <p className="text-xs text-texto-secundario">Se conserva cada análisis en el historial Euroliga. Probabilidades RAW sin calibrar; no registra apuestas.</p>}
        </div>

        {/* Resumen de apuesta */}
        {formulario.linea && (
          <div className="p-3 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10">
            <p className="text-xs text-texto-secundario uppercase tracking-wider mb-1">
              Tu predicción
            </p>
            <p className={`text-sm font-semibold ${formulario.ladoApuesta === 'OVER' ? 'text-neon-verde' : 'text-neon-rojo'
              }`}>
              {formulario.ladoApuesta === 'OVER' ? 'Más de' : 'Menos de'} {formulario.linea} {unidadLineaLabel ?? 'puntos'}
              {formulario.mercado && ` en ${formulario.mercado === 'COMPLETO' ? (esEuroliga || esCorteNBA ? 'Regulación (sin OT)' : 'Juego completo') : deporte === 'FUTBOL' ? (formulario.mercado === 'Q1' ? 'Primer tiempo' : 'Segundo tiempo') : `Cuarto ${formulario.mercado}`}`}
            </p>
          </div>
        )}

        {/* Botones */}
        <div className="flex flex-col gap-3 pt-4 border-t border-neon-cyan/20">
          <Boton
            type="submit"
            variante="primario"
            tamano="lg"
            cargando={cargando}
            textoCargando="Analizando..."
            iconoInicio={<Search size={18} />}
            anchoCompleto
          >
            Analizar Partido
          </Boton>

          <Boton
            type="button"
            variante="secundario"
            tamano="lg"
            onClick={resetearFormulario}
            disabled={cargando}
            iconoInicio={<RotateCcw size={18} />}
            anchoCompleto
          >
            Limpiar
          </Boton>
        </div>
      </form>
    </Tarjeta>
  );
}
