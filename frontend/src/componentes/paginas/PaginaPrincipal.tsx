import { CabeceraAnalizadorBaloncesto } from '../organismos/CabeceraAnalizadorBaloncesto';
// hace parte del diseño de analisis
/**
 * PaginaPrincipal.tsx — Página principal con layout futurista full-screen
 */

import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  CreadorCombinada,
  FormularioAnalisis,
  FormularioGuardarApuesta,
} from '../organismos';
import { ResultadoAnalisis } from '../organismos/ResultadoAnalisis';
import { MensajeError, ProgresoAnalisis } from '../moleculas';
import { Spinner } from '../atomos';
import { useEquipos, useAnalisis, useEstadisticasEquipos } from '../../hooks';
import { ArrowLeft } from 'lucide-react';
import { EstadoVacio, PanelesAnalisisBaloncesto } from '../organismos/PanelesAnalisisBaloncesto';
import { LadoApuesta, PeticionAnalisisNBA, SeleccionCombinadaInput } from '../../tipos';
import { crearApuesta } from '../../servicios';
import { useToasts } from '../../contextos/Toasts';

const TablaEstadisticasEquipos = lazy(async () => ({
  default: (await import('../organismos/TablaEstadisticasEquipos')).TablaEstadisticasEquipos,
}));
const HistorialEquipo = lazy(async () => ({
  default: (await import('../organismos/HistorialEquipo')).HistorialEquipo,
}));

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Página principal del Analizador NBA con diseño futurista
 */
export function PaginaPrincipal({ partidoAgenda = null }: { partidoAgenda?: import('../../servicios/agendaBaloncesto').PartidoAgendaBaloncesto | null }) {
  const historico = Boolean(partidoAgenda?.reconstruccion);
  const navegar = useNavigate();
  const [params, setParams] = useSearchParams();
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
  const [ultimaPeticion, setUltimaPeticion] = useState<PeticionAnalisisNBA | null>(null);
  const [cuartosAnalisis, setCuartosAnalisis] = useState(0);

  const [tabActivo, setTabActivo] = useState<'analisis' | 'estadisticas'>('analisis');
  const [mostrarGuardar, setMostrarGuardar] = useState(false);
  const [errorGuardar, setErrorGuardar] = useState<string | null>(null);
  const [equipoHistorialId, setEquipoHistorialId] = useState<string | null>(null);
  const invalidarParametros = useCallback(() => {
    limpiarAnalisis(); setSeleccionUsuario(null); setUltimaPeticion(null); setMostrarGuardar(false);
  }, [limpiarAnalisis]);
  // Se removió el panel de salud del sistema por requerimiento de producto.

  const seleccionCombinadaActual = useMemo<SeleccionCombinadaInput | null>(() => {
    if (!resultado || !seleccionUsuario || resultado.es_en_vivo) return null;
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
      razones: resultado.razones as unknown as Array<Record<string, unknown>>,
    };
  }, [resultado, seleccionUsuario, ultimaPeticion]);
  const historialRef = useRef<HTMLDivElement>(null);
  const { agregarToast } = useToasts();

  // Función para navegar a estadísticas de un equipo sin recargar la página
  const navegarAEstadisticasEquipo = useCallback((equipoId: string) => {
    setTabActivo('estadisticas');
    setEquipoHistorialId(equipoId);
  }, []);
  const ultimoResultadoRef = useRef<string | null>(null);
  const ultimoErrorRef = useRef<string | null>(null);
  const ultimaAdvertenciaRef = useRef<string | null>(null);

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

  // Scroll a la fila del equipo SOLO cuando los datos estén listos
  useEffect(() => {
    // Condiciones necesarias:
    // 1. Estamos en la pestaña de estadísticas
    // 2. Hay un equipo seleccionado
    // 3. Los datos ya cargaron exitosamente
    if (
      tabActivo === 'estadisticas' &&
      equipoHistorialId &&
      estadoEstadisticas === 'exito'
    ) {
      // Usar requestAnimationFrame + setTimeout para máxima confiabilidad
      const timeoutId = setTimeout(() => {
        requestAnimationFrame(() => {
          const filaEquipo = document.querySelector(
            `tr[data-equipo-id="${equipoHistorialId}"]`
          );
          if (filaEquipo) {
            filaEquipo.scrollIntoView({
              behavior: 'smooth',
              block: 'center',
            });
          }
        });
      }, 100);

      return () => clearTimeout(timeoutId);
    }
  }, [tabActivo, equipoHistorialId, estadoEstadisticas]);

  // Leer parámetros de URL para navegación directa a estadísticas de equipo
  useEffect(() => {
    const tab = params.get('tab');
    const equipo = params.get('equipo');

    if (tab === 'estadisticas') {
      setTabActivo('estadisticas');
      if (equipo) {
        setEquipoHistorialId(equipo);
      }
      // Limpiar los parámetros de la URL sin recargar
      const siguientes = new URLSearchParams(params);
      siguientes.delete('tab');
      siguientes.delete('equipo');
      setParams(siguientes, { replace: true });
    }
  }, [params, setParams]);

  // Panel de salud removido por requerimiento.

  return (
    <div aria-label="Analizador NBA">
        {historico && <p role="note" className="tarjeta p-4 mb-4 text-sm text-neon-cyan">Reconstrucción histórica · datos anteriores al día del encuentro. Solo consulta; sin registrar apuestas ni predicciones. No acredita un pronóstico emitido entonces.</p>}
        <CabeceraAnalizadorBaloncesto tabActivo={tabActivo} onTab={setTabActivo} />

        {/* Panel de salud removido por requerimiento */}
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
          <PanelesAnalisisBaloncesto formulario={
                <FormularioAnalisis
                  equipos={equipos}
                  partidoActual={partidoAgenda ?? undefined}
                  ocultarSelectorPartido={Boolean(partidoAgenda)} consultaHistorica={Boolean(partidoAgenda?.reconstruccion)}
                  estadisticas={estadisticasEquipos}
                  onAnalizar={(peticion, lado) => {
                    if (lado && peticion.linea) {
                      setSeleccionUsuario({ lado, linea: peticion.linea });
                    }
                    setUltimaPeticion(peticion);
                    analizar(peticion);
                  }}
                  cargando={estadoAnalisis === 'cargando'}
                  onCambiarParametros={invalidarParametros}
                  onCambiarModo={setCuartosAnalisis}
                  cargandoEquipos={false}
                />
          }>
            {/* Panel Derecho - Resultados */}
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
                    onGuardar={(resultado.es_en_vivo || historico || resultado.metadata?.modo_analisis === 'HISTORICO_RECONSTRUIDO') ? undefined : () => {
                      setMostrarGuardar(true);
                      setErrorGuardar(null);
                    }}
                    onConfigurarBankroll={() => navegar('/configuracion')}
                    onNavegarlEquipo={navegarAEstadisticasEquipo}
                  />
                </div>
              )}

              {/* Estado vacío */}
              {!resultado && estadoAnalisis !== 'cargando' && !errorAnalisis && (
                <div className="tarjeta h-full min-h-[500px]">
                  <EstadoVacio />
                </div>
              )}

              {cuartosAnalisis === 0 && !resultado?.es_en_vivo && !historico && resultado?.metadata?.modo_analisis !== 'HISTORICO_RECONSTRUIDO' && <div className="mt-4">
                <CreadorCombinada seleccionActual={seleccionCombinadaActual} />
              </div>}
          </PanelesAnalisisBaloncesto>
        )}

        {tabActivo === 'estadisticas' && (
          <div className="space-y-4">
            {/* Botón de regresar */}
            <button
              type="button"
              onClick={() => setTabActivo('analisis')}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg
                         border border-neon-cyan/30 bg-futurista-oscuro/50
                         text-neon-cyan hover:bg-neon-cyan/10 hover:border-neon-cyan/50
                         transition-all duration-200 text-sm font-medium"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Volver a Análisis</span>
            </button>
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
              <Suspense
                fallback={(
                  <div className="tarjeta flex items-center justify-center min-h-[220px]">
                    <Spinner tamano="md" texto="Cargando módulo de estadísticas..." centrado />
                  </div>
                )}
              >
                <div className="space-y-6">
                  <TablaEstadisticasEquipos
                    equipos={estadisticasEquipos}
                    equiposCatalogo={equipos}
                    fechaActualizacion={fechaActualizacion}
                    temporadasDisponibles={temporadasDisponibles}
                    temporadaActual={temporadaActual}
                    onCambiarTemporada={cambiarTemporada}
                    onSeleccionarEquipo={(equipoId) => setEquipoHistorialId(equipoId)}
                    equipoResaltadoId={equipoHistorialId ?? undefined}
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
              </Suspense>
            )}
          </div>
        )}

      {resultado && !resultado.es_en_vivo && !historico && resultado.metadata?.modo_analisis !== 'HISTORICO_RECONSTRUIDO' && seleccionUsuario && (
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


    </div>
  );
}
