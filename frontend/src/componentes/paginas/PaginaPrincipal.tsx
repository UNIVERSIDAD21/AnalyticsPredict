// hace parte del diseño de analisis
/**
 * PaginaPrincipal.tsx — Página principal con layout futurista full-screen
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Encabezado,
  CreadorCombinada,
  FormularioAnalisis,
  FormularioGuardarApuesta,
  HistorialEquipo,
  ResultadoAnalisis,
  TablaEstadisticasEquipos,
} from '../organismos';
import { MensajeError, ProgresoAnalisis } from '../moleculas';
import { Spinner } from '../atomos';
import { useEquipos, useAnalisis, useEstadisticasEquipos } from '../../hooks';
import { Activity, TrendingUp, Target, BarChart3 } from 'lucide-react';
import { LadoApuesta, PeticionAnalisis, SeleccionCombinadaInput } from '../../tipos';
import { crearApuesta } from '../../servicios';
import { useToasts } from '../../contextos/Toasts';

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
    advertencias,
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
    temporadasDisponibles,
    temporadaActual,
    cambiarTemporada,
  } = useEstadisticasEquipos();

  // Estado para la selección Over/Under del usuario
  const [seleccionUsuario, setSeleccionUsuario] = useState<{
    lado: LadoApuesta;
    linea: number;
  } | null>(null);
  const [ultimaPeticion, setUltimaPeticion] = useState<PeticionAnalisis | null>(null);

  const [tabActivo, setTabActivo] = useState<'analisis' | 'estadisticas'>('analisis');
  const [mostrarGuardar, setMostrarGuardar] = useState(false);
  const [errorGuardar, setErrorGuardar] = useState<string | null>(null);
  const [equipoHistorialId, setEquipoHistorialId] = useState<string | null>(null);

  const seleccionCombinadaActual = useMemo<SeleccionCombinadaInput | null>(() => {
    if (!resultado || !seleccionUsuario) return null;
    const mercado = (resultado.metadata?.mercado || 'COMPLETO') as SeleccionCombinadaInput['mercado'];
    const detalle = resultado.mejor_apuesta_detalle;
    const analisisMercado = resultado.analisis_mercado;
    const cuota = detalle?.cuota
      ?? (seleccionUsuario.lado === 'OVER' ? analisisMercado?.cuota_over : analisisMercado?.cuota_under)
      ?? analisisMercado?.cuota
      ?? (seleccionUsuario.lado === 'OVER' ? ultimaPeticion?.cuota_over : ultimaPeticion?.cuota_under)
      ?? ultimaPeticion?.cuota;

    if (!cuota) return null;

    const prediccion = mercado === 'COMPLETO'
      ? resultado.prediccion_juego_completo
      : resultado.predicciones[mercado];

    const fechaPartido = (ultimaPeticion?.fecha_partido
      ?? resultado.metadata?.fecha_partido) as string | undefined;

    const partidoId = (ultimaPeticion?.partido_id ?? resultado.metadata?.partido_id) as string | undefined;

    const probabilidad = seleccionUsuario.lado === 'OVER'
      ? resultado.probabilidad_over
      : resultado.probabilidad_under;

    return {
      partido_id: partidoId ?? null,
      equipo_local: resultado.equipo_nombre_completo,
      equipo_visitante: resultado.rival_nombre_completo,
      fecha_partido: fechaPartido,
      mercado,
      lado: seleccionUsuario.lado,
      linea: seleccionUsuario.linea,
      cuota,
      cuota_over: analisisMercado?.cuota_over ?? ultimaPeticion?.cuota_over ?? null,
      cuota_under: analisisMercado?.cuota_under ?? ultimaPeticion?.cuota_under ?? null,
      probabilidad_sistema: probabilidad ?? 0,
      prediccion_media: prediccion?.media_total ?? null,
      prediccion_desviacion: prediccion?.desviacion_total ?? null,
      confianza_sistema: resultado.nivel_confianza,
      valor_esperado_individual: analisisMercado?.valor_esperado ?? null,
      razones: resultado.razones as Array<Record<string, unknown>>,
    };
  }, [resultado, seleccionUsuario, ultimaPeticion]);
  const historialRef = useRef<HTMLDivElement>(null);
  const { agregarToast } = useToasts();
  const ultimoResultadoRef = useRef<string | null>(null);
  const ultimoErrorRef = useRef<string | null>(null);
  const ultimaAdvertenciaRef = useRef<string | null>(null);
  const navegar = (ruta: string) => {
    if (window.location.pathname === ruta) return;
    window.history.pushState({}, '', ruta);
    window.dispatchEvent(new PopStateEvent('popstate'));
  };

  const obtenerAdvertenciasCriticas = (lista: string[]) => {
    const mapeo: Record<string, string> = {
      DEVIG_ESTIMADO_PENALIZA: 'De-vig estimado: los resultados están penalizados.',
      OVERROUND_ALTO_REVISAR: 'Overround alto: revisa las cuotas antes de apostar.',
      OVERROUND_BAJO_POSIBLE_ARB: 'Overround bajo: posible arbitraje o cuota anómala.',
    };

    return lista
      .map((item) => mapeo[item] || item)
      .filter((item) =>
        /devig|overround|penaliza|riesgo/i.test(item)
      );
  };

  // Scroll al resultado cuando se completa el análisis (solo en móvil)
  useEffect(() => {
    if (resultado && window.innerWidth < 1024) {
      const elementoResultado = document.getElementById('resultado-analisis');
      if (elementoResultado) {
        elementoResultado.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }, [resultado]);

  useEffect(() => {
    if (tabActivo !== 'estadisticas') {
      setEquipoHistorialId(null);
    }
  }, [tabActivo]);

  useEffect(() => {
    if (estadoAnalisis === 'exito' && resultado) {
      const claveResultado = `${resultado.fecha_analisis}-${resultado.equipo}-${resultado.rival}`;
      if (ultimoResultadoRef.current !== claveResultado) {
        agregarToast({
          titulo: 'Análisis completado',
          mensaje: 'El motor terminó y los resultados están listos.',
          tipo: 'success',
        });
        ultimoResultadoRef.current = claveResultado;
      }

      const criticas = obtenerAdvertenciasCriticas(advertencias);
      if (criticas.length > 0 && ultimaAdvertenciaRef.current !== criticas[0]) {
        agregarToast({
          titulo: 'Advertencia del motor',
          mensaje: criticas[0],
          tipo: 'warning',
        });
        ultimaAdvertenciaRef.current = criticas[0];
      }
    }
  }, [estadoAnalisis, resultado, advertencias, agregarToast]);

  useEffect(() => {
    if (estadoAnalisis === 'error' && errorAnalisis && ultimoErrorRef.current !== errorAnalisis) {
      agregarToast({
        titulo: 'No se pudo completar el análisis',
        mensaje: errorAnalisis,
        tipo: 'error',
      });
      ultimoErrorRef.current = errorAnalisis;
    }
  }, [estadoAnalisis, errorAnalisis, agregarToast]);

  // Scroll al historial cuando se selecciona un equipo
  useEffect(() => {
    if (equipoHistorialId && historialRef.current) {
      setTimeout(() => {
        historialRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }, [equipoHistorialId]);

  // Leer parámetros de URL para navegación directa a estadísticas de equipo
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get('tab');
    const equipo = params.get('equipo');

    if (tab === 'estadisticas') {
      setTabActivo('estadisticas');
      if (equipo) {
        setEquipoHistorialId(equipo);
      }
      // Limpiar los parámetros de la URL sin recargar
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

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
                    setUltimaPeticion(peticion);
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
                <ProgresoAnalisis />
              )}

              {/* Resultados */}
              {resultado && estadoAnalisis !== 'cargando' && (
                <div className="space-y-4">
                  <ResultadoAnalisis
                    resultado={resultado}
                    advertencias={advertencias}
                    seleccionUsuario={seleccionUsuario}
                    equipoLocalId={ultimaPeticion?.equipo_local_id}
                    equipoVisitanteId={ultimaPeticion?.equipo_visitante_id}
                    onGuardar={() => {
                      setMostrarGuardar(true);
                      setErrorGuardar(null);
                    }}
                    onConfigurarBankroll={() => navegar('/configuracion')}
                  />
                </div>
              )}

              {/* Estado vacío */}
              {!resultado && estadoAnalisis !== 'cargando' && !errorAnalisis && (
                <div className="tarjeta h-full min-h-[500px]">
                  <EstadoVacio />
                </div>
              )}

              <div className="mt-4">
                <CreadorCombinada seleccionActual={seleccionCombinadaActual} />
              </div>
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
              <div className="space-y-6">
                <TablaEstadisticasEquipos
                  equipos={estadisticasEquipos}
                  equiposCatalogo={equipos}
                  fechaActualizacion={fechaActualizacion}
                  temporadasDisponibles={temporadasDisponibles}
                  temporadaActual={temporadaActual}
                  onCambiarTemporada={cambiarTemporada}
                  onSeleccionarEquipo={(equipoId) => setEquipoHistorialId(equipoId)}
                />
                {equipoHistorialId && (
                  <div ref={historialRef}>
                    <HistorialEquipo
                      equipoId={equipoHistorialId}
                      onCerrar={() => setEquipoHistorialId(null)}
                    />
                  </div>
                )}
              </div>
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
          fechaPartido={ultimaPeticion?.fecha_partido}
          partidoId={ultimaPeticion?.partido_id}
          cuotaSeleccionada={ultimaPeticion
            ? (ultimaPeticion.lado === 'OVER'
              ? (ultimaPeticion.cuota_over ?? ultimaPeticion.cuota)
              : (ultimaPeticion.cuota_under ?? ultimaPeticion.cuota))
            : undefined}
          cuotaOver={ultimaPeticion?.cuota_over}
          cuotaUnder={ultimaPeticion?.cuota_under}
          onCerrar={() => setMostrarGuardar(false)}
          onGuardar={async (apuesta) => {
            try {
              await crearApuesta(apuesta);
              setMostrarGuardar(false);
              agregarToast({
                titulo: 'Guardado en bitácora',
                mensaje: 'La apuesta se registró correctamente.',
                tipo: 'success',
              });
            } catch (error) {
              const mensaje = error instanceof Error ? error.message : 'No se pudo guardar la apuesta';
              setErrorGuardar(mensaje);
              agregarToast({
                titulo: 'No se pudo guardar',
                mensaje,
                tipo: 'error',
              });
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
