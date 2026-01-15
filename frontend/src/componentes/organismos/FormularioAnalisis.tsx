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
  LadoApuesta,
  ModoDevig,
  EstadisticasEquipo,
  TemporadaDisponible,
  PartidoResumen,
} from '../../tipos';
import { buscarEquipo, obtenerTemporadasEquipos, validarPeticionAnalisis } from '../../servicios';
import { esCuotaValida } from '../../utilidades/validadores';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsFormularioAnalisis {
  /** Lista de equipos disponibles */
  equipos: Equipo[];
  /** Estadísticas de equipos */
  estadisticas?: EstadisticasEquipo[];
  /** Callback cuando se envía el formulario */
  onAnalizar: (peticion: PeticionAnalisis, ladoSeleccionado?: LadoApuesta) => void;
  /** Indica si está cargando */
  cargando?: boolean;
  /** Indica si los equipos están cargando */
  cargandoEquipos?: boolean;
}

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
export function FormularioAnalisis({
  equipos,
  estadisticas = [],
  onAnalizar,
  cargando = false,
  cargandoEquipos = false,
}: PropsFormularioAnalisis) {
  // Estado del formulario
  const [formulario, setFormulario] = useState<EstadoFormulario>(ESTADO_INICIAL);
  const [errores, setErrores] = useState<string[]>([]);
  const [temporadasDisponibles, setTemporadasDisponibles] = useState<TemporadaDisponible[]>([]);
  const [temporadasSeleccionadas, setTemporadasSeleccionadas] = useState<string[]>([]);
  const [cargandoTemporadas, setCargandoTemporadas] = useState(false);
  const [errorTemporadas, setErrorTemporadas] = useState<string | null>(null);

  // Estado del partido seleccionado (CRÍTICO para registro de predicciones)
  const [partidoSeleccionado, setPartidoSeleccionado] = useState<PartidoResumen | null>(null);

  // Actualizar campo del formulario
  const actualizarCampo = useCallback(
    <K extends keyof EstadoFormulario>(campo: K, valor: EstadoFormulario[K]) => {
      setFormulario((prev) => ({ ...prev, [campo]: valor }));
      // Limpiar errores al modificar
      if (errores.length > 0) {
        setErrores([]);
      }
    },
    [errores.length]
  );

  // Resetear formulario
  const resetearFormulario = useCallback(() => {
    setFormulario(ESTADO_INICIAL);
    setErrores([]);
    setTemporadasSeleccionadas([]);
    setTemporadasDisponibles([]);
    setErrorTemporadas(null);
    setPartidoSeleccionado(null);
  }, []);

  // Manejar selección de partido (autocompleta equipos)
  const manejarSeleccionPartido = useCallback(
    (partido: PartidoResumen | null) => {
      setPartidoSeleccionado(partido);

      if (partido) {
        // Autocompletar equipos desde el partido seleccionado
        setFormulario((prev) => ({
          ...prev,
          equipoLocal: partido.equipo_local_nombre.toLowerCase(),
          equipoVisitante: partido.equipo_visitante_nombre.toLowerCase(),
        }));
      }
    },
    []
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

      const ladoSeleccionado = formulario.ladoApuesta;

      // Parsear cuotas
      const cuotaOverValor = formulario.cuotaOver.trim()
        ? parseFloat(formulario.cuotaOver)
        : undefined;
      const cuotaUnderValor = formulario.cuotaUnder.trim()
        ? parseFloat(formulario.cuotaUnder)
        : undefined;

      // Validar cuotas
      const tieneOver = cuotaOverValor !== undefined && esCuotaValida(cuotaOverValor);
      const tieneUnder = cuotaUnderValor !== undefined && esCuotaValida(cuotaUnderValor);

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
        equipo_local: formulario.equipoLocal,
        equipo_visitante: formulario.equipoVisitante,
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
        temporadas: temporadasSeleccionadas,
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

      onAnalizar(peticion as PeticionAnalisis, ladoSeleccionado);
    },
    [formulario, onAnalizar, equipoLocalSeleccionado?.id, equipoVisitanteSeleccionado?.id, temporadasSeleccionadas, partidoSeleccionado]
  );

  useEffect(() => {
    const ids = [equipoLocalSeleccionado?.id, equipoVisitanteSeleccionado?.id].filter(
      Boolean
    ) as string[];

    if (ids.length === 0) {
      setTemporadasDisponibles([]);
      setTemporadasSeleccionadas([]);
      setErrorTemporadas(null);
      return;
    }

    let activo = true;
    setCargandoTemporadas(true);
    setErrorTemporadas(null);

    obtenerTemporadasEquipos(ids)
      .then((temporadas) => {
        if (!activo) return;
        setTemporadasDisponibles(temporadas);
        setTemporadasSeleccionadas((prev) => {
          const disponiblesIds = temporadas.map((temporada) => temporada.id);
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
    };
  }, [equipoLocalSeleccionado?.id, equipoVisitanteSeleccionado?.id]);

  const toggleTemporada = useCallback((temporadaId: string) => {
    setTemporadasSeleccionadas((prev) =>
      prev.includes(temporadaId)
        ? prev.filter((id) => id !== temporadaId)
        : [...prev, temporadaId]
    );
  }, []);

  const seleccionarTodasTemporadas = useCallback(() => {
    setTemporadasSeleccionadas(temporadasDisponibles.map((temporada) => temporada.id));
  }, [temporadasDisponibles]);

  const limpiarTemporadas = useCallback(() => {
    setTemporadasSeleccionadas([]);
  }, []);

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
          <SelectorPartido
            partidoSeleccionado={partidoSeleccionado}
            onSeleccionar={manejarSeleccionPartido}
            deshabilitado={cargando}
          />

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

          <PanelEstadisticasEquipo
            equipoLocal={buscarEstadisticas(formulario.equipoLocal)}
            equipoVisitante={buscarEstadisticas(formulario.equipoVisitante)}
            cargando={cargando}
          />

          {/* Mercado */}
          <SelectorMercado
            valor={formulario.mercado}
            onChange={(valor) => actualizarCampo('mercado', valor)}
            deshabilitado={cargando}
          />

          {/* Línea con selector Over/Under */}
          <InputLinea
            valor={formulario.linea}
            onChange={(valor) => actualizarCampo('linea', valor)}
            ladoApuesta={formulario.ladoApuesta}
            onLadoChange={(lado) => actualizarCampo('ladoApuesta', lado)}
            deshabilitado={cargando}
            esJuegoCompleto={esJuegoCompleto}
          />

          {/* Temporadas */}
          <div className="space-y-2">
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
          </div>

          {/* Cuotas duales (Over/Under) */}
          <InputCuotasDuales
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
          />
        </div>

        {/* Resumen de apuesta */}
        {formulario.linea && (
          <div className="p-3 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10">
            <p className="text-xs text-texto-secundario uppercase tracking-wider mb-1">
              Tu predicción
            </p>
            <p className={`text-sm font-semibold ${formulario.ladoApuesta === 'OVER' ? 'text-neon-verde' : 'text-neon-rojo'
              }`}>
              {formulario.ladoApuesta === 'OVER' ? 'Más de' : 'Menos de'} {formulario.linea} puntos
              {formulario.mercado && ` en ${formulario.mercado === 'COMPLETO' ? 'Juego Completo' : formulario.mercado}`}
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
