/**
 * FormularioAnalisis.tsx — Formulario principal para analizar partidos
 */

import { useState, useCallback } from 'react';
import { Search, RotateCcw } from 'lucide-react';
import { Boton, Tarjeta } from '../atomos';
import {
  SelectorEquipo,
  SelectorMercado,
  InputLinea,
  InputCuota,
  MensajeError,
} from '../moleculas';
import { Equipo, Mercado, PeticionAnalisis } from '../../tipos';
import { validarPeticionAnalisis } from '../../servicios';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsFormularioAnalisis {
  /** Lista de equipos disponibles */
  equipos: Equipo[];
  /** Callback cuando se envía el formulario */
  onAnalizar: (peticion: PeticionAnalisis) => void;
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
  cuota: string;
}

const ESTADO_INICIAL: EstadoFormulario = {
  equipoLocal: '',
  equipoVisitante: '',
  mercado: '',
  linea: '',
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
  onAnalizar,
  cargando = false,
  cargandoEquipos = false,
}: PropsFormularioAnalisis) {
  // Estado del formulario
  const [formulario, setFormulario] = useState<EstadoFormulario>(ESTADO_INICIAL);
  const [errores, setErrores] = useState<string[]>([]);

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
      };

      // Validar
      const erroresValidacion = validarPeticionAnalisis(peticion);
      if (erroresValidacion.length > 0) {
        setErrores(erroresValidacion);
        return;
      }

      // Enviar
      onAnalizar(peticion as PeticionAnalisis);
    },
    [formulario, onAnalizar]
  );

  const esJuegoCompleto = formulario.mercado === 'COMPLETO';

  return (
    <Tarjeta className="animate-entrada">
      <form onSubmit={manejarEnvio} className="space-y-6">
        {/* Título */}
        <div className="border-b border-nba-gris-200 pb-4">
          <h2 className="text-xl font-bold text-nba-gris-900">
            Configurar Análisis
          </h2>
          <p className="text-sm text-nba-gris-500 mt-1">
            Selecciona los equipos y el mercado que deseas analizar
          </p>
        </div>

        {/* Errores de validación */}
        {errores.length > 0 && (
          <MensajeError
            titulo="Corrige los siguientes errores"
            mensaje={errores.join('. ')}
            onCerrar={() => setErrores([])}
          />
        )}

        {/* Grid de campos */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Equipo Local */}
          <SelectorEquipo
            etiqueta="Equipo Local"
            equipos={equipos}
            valor={formulario.equipoLocal}
            onChange={(valor) => actualizarCampo('equipoLocal', valor)}
            equipoExcluido={formulario.equipoVisitante}
            deshabilitado={cargando || cargandoEquipos}
            placeholder={cargandoEquipos ? 'Cargando equipos...' : 'Selecciona equipo local'}
          />

          {/* Equipo Visitante */}
          <SelectorEquipo
            etiqueta="Equipo Visitante"
            equipos={equipos}
            valor={formulario.equipoVisitante}
            onChange={(valor) => actualizarCampo('equipoVisitante', valor)}
            equipoExcluido={formulario.equipoLocal}
            deshabilitado={cargando || cargandoEquipos}
            placeholder={cargandoEquipos ? 'Cargando equipos...' : 'Selecciona equipo visitante'}
          />

          {/* Mercado */}
          <SelectorMercado
            valor={formulario.mercado}
            onChange={(valor) => actualizarCampo('mercado', valor)}
            deshabilitado={cargando}
          />

          {/* Línea */}
          <InputLinea
            valor={formulario.linea}
            onChange={(valor) => actualizarCampo('linea', valor)}
            deshabilitado={cargando}
            esJuegoCompleto={esJuegoCompleto}
          />

          {/* Cuota */}
          <div className="md:col-span-2 max-w-xs">
            <InputCuota
              valor={formulario.cuota}
              onChange={(valor) => actualizarCampo('cuota', valor)}
              deshabilitado={cargando}
            />
          </div>
        </div>

        {/* Botones */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-nba-gris-200">
          <Boton
            type="submit"
            variante="primario"
            tamano="lg"
            cargando={cargando}
            textoCargando="Analizando..."
            iconoInicio={<Search size={20} />}
            className="flex-1 sm:flex-none"
          >
            Analizar Partido
          </Boton>

          <Boton
            type="button"
            variante="secundario"
            tamano="lg"
            onClick={resetearFormulario}
            disabled={cargando}
            iconoInicio={<RotateCcw size={20} />}
          >
            Limpiar
          </Boton>
        </div>
      </form>
    </Tarjeta>
  );
}
