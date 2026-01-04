/**
 * PaginaPrincipal.tsx — Página principal con layout futurista full-screen
 */

import { useEffect, useState } from 'react';
import {
  Encabezado,
  FormularioAnalisis,
  FormularioGuardarApuesta,
  ResultadoAnalisis,
  TablaEstadisticasEquipos,
} from '../organismos';
import { MensajeError } from '../moleculas';
import { Spinner } from '../atomos';
import { useEquipos, useAnalisis, useEstadisticasEquipos } from '../../hooks';
import { Activity, TrendingUp, Target, BarChart3 } from 'lucide-react';
import { LadoApuesta } from '../../tipos';
import { crearApuesta } from '../../servicios';

// ══════════════════════════════════════════════════════════════
// COMPONENTE ESTADO VACÍO
// ══════════════════════════════════════════════════════════════

function EstadoVacio() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center p-8">
      {/* Icono animado */}
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-neon-cyan/10 blur-3xl rounded-full animate-pulse" />
        <div className="relative w-32 h-32 rounded-2xl border border-neon-cyan/20 bg-futurista-oscuro/50 flex items-center justify-center">
          <BarChart3 className="w-16 h-16 text-neon-cyan/50" />
        </div>
      </div>

      {/* Texto */}
      <h3 className="text-2xl font-futurista text-texto-principal mb-3 tracking-wider">
        ESPERANDO ANÁLISIS
      </h3>
      <p className="text-texto-secundario max-w-md mb-8">
        Configura los parámetros del partido en el panel izquierdo para obtener predicciones
        basadas en análisis estadístico avanzado.
      </p>

      {/* Características */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-2xl">
        <div className="p-4 rounded-lg border border-neon-cyan/10 bg-futurista-oscuro/30">
          <Activity className="w-6 h-6 text-neon-cyan mb-2 mx-auto" />
          <p className="text-xs text-texto-secundario uppercase tracking-wider">
            Análisis por Cuarto
          </p>
        </div>
        <div className="p-4 rounded-lg border border-neon-verde/10 bg-futurista-oscuro/30">
          <TrendingUp className="w-6 h-6 text-neon-verde mb-2 mx-auto" />
          <p className="text-xs text-texto-secundario uppercase tracking-wider">
            Probabilidades Over/Under
          </p>
        </div>
        <div className="p-4 rounded-lg border border-neon-magenta/10 bg-futurista-oscuro/30">
          <Target className="w-6 h-6 text-neon-magenta mb-2 mx-auto" />
          <p className="text-xs text-texto-secundario uppercase tracking-wider">
            Detección de Valor
          </p>
        </div>
      </div>

      {/* Línea decorativa */}
      <div className="mt-8 w-48 h-[1px] bg-gradient-to-r from-transparent via-neon-cyan/30 to-transparent" />
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Página principal del Analizador NBA con diseño futurista
 */
export function PaginaPrincipal() {
  const {
    equipos,
    estado: estadoEquipos,
    error: errorEquipos,
    recargar: recargarEquipos,
  } = useEquipos();

  const {
    resultado,
    estado: estadoAnalisis,
    error: errorAnalisis,
    analizar,
    limpiar: limpiarAnalisis,
  } = useAnalisis();

  const {
    equipos: estadisticasEquipos,
    fechaActualizacion,
    estado: estadoEstadisticas,
    error: errorEstadisticas,
    recargar: recargarEstadisticas,
  } = useEstadisticasEquipos();

  // Estado para la selección Over/Under del usuario
  const [seleccionUsuario, setSeleccionUsuario] = useState<{
    lado: LadoApuesta;
    linea: number;
  } | null>(null);

  const [tabActivo, setTabActivo] = useState<'analisis' | 'estadisticas'>('analisis');
  const [mostrarGuardar, setMostrarGuardar] = useState(false);
  const [errorGuardar, setErrorGuardar] = useState<string | null>(null);

  // Scroll al resultado cuando se completa el análisis (solo en móvil)
  useEffect(() => {
    if (resultado && window.innerWidth < 1024) {
      const elementoResultado = document.getElementById('resultado-analisis');
      if (elementoResultado) {
        elementoResultado.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }, [resultado]);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Encabezado */}
      <Encabezado />

      {/* Contenido principal - Full height */}
      <main className="flex-1 contenedor py-6 lg:py-8">
        {/* Tabs */}
        <div className="mb-6 flex items-center gap-3">
          <button
            type="button"
            className={`px-4 py-2 rounded-md text-sm font-semibold border ${
              tabActivo === 'analisis'
                ? 'bg-neon-cyan/20 border-neon-cyan text-neon-cyan'
                : 'border-neon-cyan/20 text-texto-secundario'
            }`}
            onClick={() => setTabActivo('analisis')}
          >
            Análisis
          </button>
          <button
            type="button"
            className={`px-4 py-2 rounded-md text-sm font-semibold border ${
              tabActivo === 'estadisticas'
                ? 'bg-neon-cyan/20 border-neon-cyan text-neon-cyan'
                : 'border-neon-cyan/20 text-texto-secundario'
            }`}
            onClick={() => setTabActivo('estadisticas')}
          >
            Estadísticas de equipos
          </button>
        </div>
        {/* Error de conexión */}
        {estadoEquipos === 'error' && (
          <div className="mb-6">
            <MensajeError
              titulo="Error de conexión"
              mensaje={errorEquipos || 'No se pudo conectar con el servidor'}
              onCerrar={recargarEquipos}
            />
          </div>
        )}

        {/* Estado de carga inicial */}
        {estadoEquipos === 'cargando' && (
          <div className="flex-1 flex items-center justify-center py-20">
            <div className="text-center">
              <Spinner tamano="lg" texto="Inicializando sistema..." centrado />
              <p className="text-texto-terciario text-sm mt-4 font-mono">
                Conectando con el servidor de análisis
              </p>
            </div>
          </div>
        )}

        {/* Layout principal de dos columnas */}
        {estadoEquipos === 'exito' && tabActivo === 'analisis' && (
          <div className="flex flex-col lg:flex-row gap-6 lg:gap-8 min-h-[calc(100vh-200px)]">
            {/* Panel Izquierdo - Formulario */}
            <div className="w-full lg:w-[400px] xl:w-[450px] flex-shrink-0">
              <div className="lg:sticky lg:top-6">
                <FormularioAnalisis
                  equipos={equipos}
                  estadisticas={estadisticasEquipos}
                  onAnalizar={(peticion, lado) => {
                    if (lado && peticion.linea) {
                      setSeleccionUsuario({ lado, linea: peticion.linea });
                    }
                    analizar(peticion);
                  }}
                  cargando={estadoAnalisis === 'cargando'}
                  cargandoEquipos={estadoEquipos === 'cargando'}
                />
              </div>
            </div>

            {/* Panel Derecho - Resultados */}
            <div className="flex-1 min-w-0" id="resultado-analisis">
              {/* Error de análisis */}
              {errorAnalisis && (
                <MensajeError
                  titulo="Error en el análisis"
                  mensaje={errorAnalisis}
                  onCerrar={limpiarAnalisis}
                />
              )}

              {/* Spinner de análisis */}
              {estadoAnalisis === 'cargando' && (
                <div className="tarjeta h-full min-h-[400px] flex items-center justify-center">
                  <div className="text-center">
                    <div className="relative inline-block mb-6">
                      <div className="absolute inset-0 bg-neon-cyan/20 blur-xl rounded-full animate-pulse" />
                      <Spinner tamano="lg" centrado />
                    </div>
                    <p className="text-texto-principal font-futurista tracking-wider">
                      PROCESANDO ANÁLISIS
                    </p>
                    <p className="text-texto-terciario text-sm mt-2 font-mono">
                      Calculando probabilidades...
                    </p>
                  </div>
                </div>
              )}

              {/* Resultados */}
              {resultado && estadoAnalisis !== 'cargando' && (
                <ResultadoAnalisis
                  resultado={resultado}
                  seleccionUsuario={seleccionUsuario}
                  onGuardar={() => {
                    setMostrarGuardar(true);
                    setErrorGuardar(null);
                  }}
                />
              )}

              {/* Estado vacío */}
              {!resultado && estadoAnalisis !== 'cargando' && !errorAnalisis && (
                <div className="tarjeta h-full min-h-[500px]">
                  <EstadoVacio />
                </div>
              )}
            </div>
          </div>
        )}

        {tabActivo === 'estadisticas' && (
          <div className="space-y-4">
            {estadoEstadisticas === 'error' && (
              <MensajeError
                titulo="Error al cargar estadísticas"
                mensaje={errorEstadisticas || 'No se pudieron cargar estadísticas'}
                onCerrar={recargarEstadisticas}
              />
            )}
            {estadoEstadisticas === 'cargando' && (
              <div className="tarjeta flex items-center justify-center min-h-[300px]">
                <Spinner tamano="lg" texto="Cargando estadísticas..." centrado />
              </div>
            )}
            {estadoEstadisticas === 'exito' && (
              <TablaEstadisticasEquipos
                equipos={estadisticasEquipos}
                equiposCatalogo={equipos}
                fechaActualizacion={fechaActualizacion}
              />
            )}
          </div>
        )}
      </main>

      {resultado && seleccionUsuario && (
        <FormularioGuardarApuesta
          abierto={mostrarGuardar}
          resultado={resultado}
          ladoSeleccionado={seleccionUsuario.lado}
          lineaSeleccionada={seleccionUsuario.linea}
          onCerrar={() => setMostrarGuardar(false)}
          onGuardar={async (apuesta) => {
            try {
              await crearApuesta(apuesta);
              setMostrarGuardar(false);
            } catch (error) {
              const mensaje = error instanceof Error ? error.message : 'No se pudo guardar la apuesta';
              setErrorGuardar(mensaje);
            }
          }}
        />
      )}

      {errorGuardar && (
        <div className="fixed bottom-6 right-6 max-w-md">
          <MensajeError
            titulo="No se pudo guardar"
            mensaje={errorGuardar}
            onCerrar={() => setErrorGuardar(null)}
          />
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-neon-cyan/10 bg-futurista-negro/80 backdrop-blur-sm">
        <div className="contenedor py-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-2 text-center md:text-left">
            <p className="text-texto-terciario text-xs uppercase tracking-wider">
              NBA Analyzer Pro — Sistema de Predicción Avanzada
            </p>
            <p className="text-texto-terciario/60 text-xs">
              Los análisis son orientativos. Apuesta responsablemente.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
