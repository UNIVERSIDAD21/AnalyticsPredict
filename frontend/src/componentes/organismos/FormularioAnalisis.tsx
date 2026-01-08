// hace parte del diseño de analisis
/**
 * FormularioAnalisis.tsx — Formulario principal con diseño futurista
 */

import { useEffect, useMemo, useState, useCallback } from 'react';
import { Search, RotateCcw, Zap } from 'lucide-react';
import { Boton, Tarjeta } from '../atomos';
import {
  SelectorEquipo,
  SelectorMercado,
  InputLinea,
  InputCuota,
  MensajeError,
  PanelEstadisticasEquipo,
} from '../moleculas';
import {
  Equipo,
  Mercado,
  PeticionAnalisis,
  LadoApuesta,
  EstadisticasEquipo,
  TemporadaDisponible,
} from '../../tipos';
import { buscarEquipo, obtenerTemporadasEquipos, validarPeticionAnalisis } from '../../servicios';

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
  cuota: string;
}

const ESTADO_INICIAL: EstadoFormulario = {
  equipoLocal: '',
  equipoVisitante: '',
  mercado: '',
  linea: '',
  ladoApuesta: 'OVER',
  cuota: '',
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
  }, []);

  // Manejar envío
  const manejarEnvio = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();

      // Construir petición
      const peticion: Partial<PeticionAnalisis> = {
        equipo_local: formulario.equipoLocal,
        equipo_visitante: formulario.equipoVisitante,
        mercado: formulario.mercado as Mercado,
        linea: formulario.linea ? parseFloat(formulario.linea) : undefined,
        cuota: formulario.cuota ? parseFloat(formulario.cuota) : undefined,
        temporadas: temporadasSeleccionadas,
      };

      // Validar
      const erroresValidacion = validarPeticionAnalisis(peticion);
      if (erroresValidacion.length > 0) {
        setErrores(erroresValidacion);
        return;
      }

      // Enviar con lado seleccionado
      onAnalizar(peticion as PeticionAnalisis, formulario.ladoApuesta);
    },
    [formulario, onAnalizar]
  );

  const esJuegoCompleto = formulario.mercado === 'COMPLETO';
  const buscarEstadisticas = (nombre: string) =>
    estadisticas.find((equipo) => equipo.nombre.toLowerCase() === nombre.toLowerCase());

  const equipoLocalSeleccionado = useMemo(
    () => buscarEquipo(equipos, formulario.equipoLocal),
    [equipos, formulario.equipoLocal]
  );
  const equipoVisitanteSeleccionado = useMemo(
    () => buscarEquipo(equipos, formulario.equipoVisitante),
    [equipos, formulario.equipoVisitante]
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
          {/* Equipo Local */}
          <SelectorEquipo
            etiqueta="Equipo Local"
            equipos={equipos}
            valor={formulario.equipoLocal}
            onChange={(valor) => actualizarCampo('equipoLocal', valor)}
            equipoExcluido={formulario.equipoVisitante}
            deshabilitado={cargando || cargandoEquipos}
            placeholder={cargandoEquipos ? 'Cargando...' : 'Selecciona local'}
          />

          {/* Equipo Visitante */}
          <SelectorEquipo
            etiqueta="Equipo Visitante"
            equipos={equipos}
            valor={formulario.equipoVisitante}
            onChange={(valor) => actualizarCampo('equipoVisitante', valor)}
            equipoExcluido={formulario.equipoLocal}
            deshabilitado={cargando || cargandoEquipos}
            placeholder={cargandoEquipos ? 'Cargando...' : 'Selecciona visitante'}
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
                        className={`px-3 py-1 rounded-full text-xs font-semibold border transition ${
                          seleccionada
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

          {/* Cuota */}
          <InputCuota
            valor={formulario.cuota}
            onChange={(valor) => actualizarCampo('cuota', valor)}
            deshabilitado={cargando}
          />
        </div>

        {/* Resumen de apuesta */}
        {formulario.linea && (
          <div className="p-3 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10">
            <p className="text-xs text-texto-secundario uppercase tracking-wider mb-1">
              Tu predicción
            </p>
            <p className={`text-sm font-semibold ${
              formulario.ladoApuesta === 'OVER' ? 'text-neon-verde' : 'text-neon-rojo'
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
