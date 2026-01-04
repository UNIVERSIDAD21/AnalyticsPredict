/**
 * FormularioAnalisis.tsx — Formulario principal con diseño futurista
 */

import { useEffect, useState, useCallback } from 'react';
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
import { validarPeticionAnalisis } from '../../servicios';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsFormularioAnalisis {
  /** Lista de equipos disponibles */
  equipos: Equipo[];
  /** Estadísticas de equipos */
  estadisticas?: EstadisticasEquipo[];
  /** Temporadas disponibles */
  temporadasDisponibles?: TemporadaDisponible[];
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
  temporadasSeleccionadas: string[];
}

const ESTADO_INICIAL: EstadoFormulario = {
  equipoLocal: '',
  equipoVisitante: '',
  mercado: '',
  linea: '',
  ladoApuesta: 'OVER',
  cuota: '',
  temporadasSeleccionadas: [],
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
  temporadasDisponibles = [],
  onAnalizar,
  cargando = false,
  cargandoEquipos = false,
}: PropsFormularioAnalisis) {
  // Estado del formulario
  const [formulario, setFormulario] = useState<EstadoFormulario>(ESTADO_INICIAL);
  const [errores, setErrores] = useState<string[]>([]);

  useEffect(() => {
    if (temporadasDisponibles.length === 0) {
      return;
    }

    setFormulario((prev) => {
      if (prev.temporadasSeleccionadas.length > 0) {
        return prev;
      }
      return {
        ...prev,
        temporadasSeleccionadas: temporadasDisponibles.map((temporada) => temporada.id),
      };
    });
  }, [temporadasDisponibles]);

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
        temporadas:
          temporadasDisponibles.length > 0 ? formulario.temporadasSeleccionadas : undefined,
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
  const temporadasSeleccionadas = formulario.temporadasSeleccionadas;
  const toggleTemporada = (temporadaId: string) => {
    setFormulario((prev) => {
      const yaSeleccionada = prev.temporadasSeleccionadas.includes(temporadaId);
      const nuevasTemporadas = yaSeleccionada
        ? prev.temporadasSeleccionadas.filter((id) => id !== temporadaId)
        : [...prev.temporadasSeleccionadas, temporadaId];
      return { ...prev, temporadasSeleccionadas: nuevasTemporadas };
    });
  };
  const seleccionarTodas = () => {
    setFormulario((prev) => ({
      ...prev,
      temporadasSeleccionadas: temporadasDisponibles.map((temporada) => temporada.id),
    }));
  };

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

          {temporadasDisponibles.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-texto-principal">Temporadas</p>
                <button
                  type="button"
                  className="text-xs text-neon-cyan hover:text-neon-cyan/80"
                  onClick={seleccionarTodas}
                  disabled={cargando}
                >
                  Seleccionar todas
                </button>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {temporadasDisponibles.map((temporada) => (
                  <label
                    key={temporada.id}
                    className="flex items-center gap-2 rounded-md border border-neon-cyan/10 bg-futurista-oscuro/40 px-3 py-2 text-xs text-texto-secundario"
                  >
                    <input
                      type="checkbox"
                      className="accent-neon-cyan"
                      checked={temporadasSeleccionadas.includes(temporada.id)}
                      onChange={() => toggleTemporada(temporada.id)}
                      disabled={cargando}
                    />
                    <span>{temporada.nombre}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

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
