/**
 * PaginaFutbol.tsx — módulo fútbol alineado al canon NBA.
 *
 * Regla de producto: mismo flujo/base visual de NBA; solo cambia el contenido del dominio.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Activity, BarChart3, Trophy } from 'lucide-react';
import { Encabezado, FormularioAnalisis } from '../organismos';
import { ResultadoAnalisis } from '../organismos/ResultadoAnalisis';
import { MensajeError, PanelDepthPremium, ProgresoAnalisis } from '../moleculas';
import { Boton, Tarjeta } from '../atomos';
import { Spinner } from '../atomos/Spinner';
import { usePartidosFutbol } from '../../hooks';
import { analizarPartido, obtenerH2HPartidos, obtenerPartidosEquipoDetalle } from '../../servicios/futbol';
import { useAccessPolicy } from '../../contextos/AccessPolicyContext';
import { useGateNavigation } from '../../hooks/useGateNavigation';
import { adaptarAnalisisFutbolAResultadoAnalisis } from '../../utilidades/adaptadores/futbolToNbaAnalisis';
import type {
  AnalisisFutbolResponse,
  PartidoFutbolEstadistico,
  PartidoFutbolResumen,
  UbicacionHistorialEquipo,
} from '../../tipos/futbol';
import type { Equipo, Mercado, PartidoResumen, PeticionAnalisis } from '../../tipos';
import { PanelH2HFutbol } from '../organismos/PanelH2HFutbol';
import { PanelHistorialEquipoFutbol } from '../organismos/PanelHistorialEquipoFutbol';

const navegar = (ruta: string) => {
  if (window.location.pathname === ruta && window.location.search === '') return;
  window.history.pushState({}, '', ruta);
  window.dispatchEvent(new PopStateEvent('popstate'));
};

function EstadoVacioFutbol() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center p-8">
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-neon-cyan/10 blur-3xl rounded-full animate-pulse" />
        <div className="relative w-32 h-32 rounded-2xl border border-neon-cyan/20 bg-futurista-oscuro/50 flex items-center justify-center">
          <BarChart3 className="w-16 h-16 text-neon-cyan/50" />
        </div>
      </div>

      <h3 className="text-2xl font-futurista text-texto-principal mb-3 tracking-wider">ESPERANDO ANÁLISIS</h3>
      <p className="text-texto-secundario max-w-md mb-8">
        Selecciona un partido de fútbol y ejecuta el análisis en el mismo flujo operativo de NBA.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-2xl">
        <div className="p-4 rounded-lg border border-neon-cyan/10 bg-futurista-oscuro/30">
          <Activity className="w-6 h-6 text-neon-cyan mb-2 mx-auto" />
          <p className="text-xs text-texto-secundario uppercase tracking-wider">Flujo canónico</p>
        </div>
        <div className="p-4 rounded-lg border border-neon-verde/10 bg-futurista-oscuro/30">
          <Trophy className="w-6 h-6 text-neon-verde mb-2 mx-auto" />
          <p className="text-xs text-texto-secundario uppercase tracking-wider">Mercados fútbol</p>
        </div>
        <div className="p-4 rounded-lg border border-neon-magenta/10 bg-futurista-oscuro/30">
          <BarChart3 className="w-6 h-6 text-neon-magenta mb-2 mx-auto" />
          <p className="text-xs text-texto-secundario uppercase tracking-wider">Resultados unificados</p>
        </div>
      </div>
    </div>
  );
}

export function PaginaFutbol() {
  const { can } = useAccessPolicy();
  const { navegarConGate } = useGateNavigation(navegar);

  const [partidoSeleccionadoId, setPartidoSeleccionadoId] = useState('');
  const [analisis, setAnalisis] = useState<AnalisisFutbolResponse | null>(null);
  const [cargandoAnalisis, setCargandoAnalisis] = useState(false);
  const [errorAnalisis, setErrorAnalisis] = useState<string | null>(null);

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

  const historialCacheRef = useRef<Map<string, PartidoFutbolEstadistico[]>>(new Map());
  const h2hCacheRef = useRef<Map<string, PartidoFutbolEstadistico[]>>(new Map());

  const { partidos, cargando: cargandoPartidos, error: errorPartidos, recargar } = usePartidosFutbol({
    tipo: 'proximos',
    filtrosIniciales: { dias: 7 },
    cargarAlMontar: true,
  });

  const partidoSeleccionado = useMemo(
    () => partidos.find((p) => p.id === partidoSeleccionadoId) ?? null,
    [partidoSeleccionadoId, partidos]
  );

  useEffect(() => {
    const qs = new URLSearchParams(window.location.search);
    const porQuery = qs.get('partidoId');
    if (porQuery && partidos.some((p) => p.id === porQuery)) {
      setPartidoSeleccionadoId(porQuery);
      return;
    }
    if (!partidoSeleccionadoId && partidos.length > 0) {
      setPartidoSeleccionadoId(partidos[0].id);
    }
  }, [partidoSeleccionadoId, partidos]);

  const equiposAnalisis: Equipo[] = useMemo(() => {
    if (!partidoSeleccionado) return [];
    return [
      {
        id: String(partidoSeleccionado.equipoLocal),
        nombre: partidoSeleccionado.equipoLocalNombre,
        nombre_corto: partidoSeleccionado.equipoLocalNombre,
        abreviatura: partidoSeleccionado.equipoLocalNombre.slice(0, 3).toUpperCase(),
      },
      {
        id: String(partidoSeleccionado.equipoVisitante),
        nombre: partidoSeleccionado.equipoVisitanteNombre,
        nombre_corto: partidoSeleccionado.equipoVisitanteNombre,
        abreviatura: partidoSeleccionado.equipoVisitanteNombre.slice(0, 3).toUpperCase(),
      },
    ];
  }, [partidoSeleccionado]);

  const partidosSelector: PartidoResumen[] = useMemo(() => (
    partidos.map((partido) => ({
      id: partido.id,
      fecha_partido: partido.fechaPartido.split('T')[0],
      tipo_partido: 'REG',
      equipo_local_id: String(partido.equipoLocal),
      equipo_local_nombre: partido.equipoLocalNombre,
      equipo_visitante_id: String(partido.equipoVisitante),
      equipo_visitante_nombre: partido.equipoVisitanteNombre,
      temporada_id: partido.competicion,
      temporada_nombre: partido.competicionNombre,
      local_total: null,
      visitante_total: null,
      finalizado: false,
    }))
  ), [partidos]);

  const opcionesMercadoFutbol: Array<{ valor: Mercado; etiqueta: string }> = useMemo(
    () => [
      { valor: 'Q1', etiqueta: 'Corners' },
      { valor: 'Q2', etiqueta: 'Goles' },
      { valor: 'Q3', etiqueta: 'Tiros a puerta' },
    ],
    []
  );

  const cargarContexto = useCallback(async (partido: PartidoFutbolResumen) => {
    const localId = String(partido.equipoLocal);
    const visitanteId = String(partido.equipoVisitante);
    if (!localId || !visitanteId) return;

    const keyH2h = `${localId}|${visitanteId}|${limiteH2h}`;
    const keyLocal = `${localId}|${limiteLocal}|${ubicacionLocal}`;
    const keyVisit = `${visitanteId}|${limiteVisitante}|${ubicacionVisitante}`;

    try {
      setCargandoContexto(true);
      setErrorContexto(null);

      const h2h = h2hCacheRef.current.get(keyH2h) || await obtenerH2HPartidos(localId, visitanteId, limiteH2h);
      const local = historialCacheRef.current.get(keyLocal) || await obtenerPartidosEquipoDetalle(localId, limiteLocal, ubicacionLocal);
      const visit = historialCacheRef.current.get(keyVisit) || await obtenerPartidosEquipoDetalle(visitanteId, limiteVisitante, ubicacionVisitante);

      h2hCacheRef.current.set(keyH2h, h2h);
      historialCacheRef.current.set(keyLocal, local);
      historialCacheRef.current.set(keyVisit, visit);

      setH2hPartidos(h2h);
      setHistorialLocal(local);
      setHistorialVisitante(visit);
    } catch (error) {
      setErrorContexto(error instanceof Error ? error.message : 'No se pudo cargar el contexto del partido');
    } finally {
      setCargandoContexto(false);
    }
  }, [limiteH2h, limiteLocal, limiteVisitante, ubicacionLocal, ubicacionVisitante]);

  useEffect(() => {
    if (!partidoSeleccionado) return;
    void cargarContexto(partidoSeleccionado);
  }, [partidoSeleccionado, cargarContexto]);

  const ejecutarAnalisis = useCallback(async (peticion: PeticionAnalisis) => {
    const partidoIdObjetivo = peticion.partido_id || partidoSeleccionadoId;
    if (!partidoIdObjetivo) {
      setErrorAnalisis('Selecciona un partido para analizar.');
      return;
    }

    if (partidoIdObjetivo !== partidoSeleccionadoId) {
      setPartidoSeleccionadoId(partidoIdObjetivo);
    }

    try {
      setCargandoAnalisis(true);
      setErrorAnalisis(null);
      const data = await analizarPartido({
        partidoId: partidoIdObjetivo,
        h2hLimite: limiteH2h,
      });
      setAnalisis(data);
    } catch (error) {
      setErrorAnalisis(error instanceof Error ? error.message : 'No se pudo completar el análisis de fútbol');
    } finally {
      setCargandoAnalisis(false);
    }
  }, [partidoSeleccionadoId, limiteH2h]);

  const recargarTodo = useCallback(() => {
    historialCacheRef.current.clear();
    h2hCacheRef.current.clear();
    recargar();
    if (partidoSeleccionado) {
      void cargarContexto(partidoSeleccionado);
    }
  }, [cargarContexto, partidoSeleccionado, recargar]);

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8">
        <div className="mb-6">
          <PanelDepthPremium
            modulo="futbol"
            titulo="Depth premium Fútbol"
            descripcion="Mismo contrato operativo visual que NBA; fútbol solo ajusta datos y mercados del dominio."
            bullets={[
              'comparativas_multi_mercado por partido',
              'contexto_historico_extendido de H2H e historial',
              'priorizacion_operativa_avanzada sobre recomendaciones',
            ]}
            activo={can('premium.depth')}
            onAbrirDepth={() => navegarConGate('/configuracion', 'premium.depth')}
          />
        </div>

        {(errorPartidos || errorContexto) && (
          <div className="mb-6">
            <MensajeError
              titulo="Error de carga"
              mensaje={errorPartidos || errorContexto || 'No se pudieron cargar los datos'}
              onCerrar={recargarTodo}
            />
          </div>
        )}

        <div className="flex flex-col lg:flex-row gap-6 lg:gap-8 min-h-[calc(100vh-200px)]">
          <div className="w-full lg:w-[400px] xl:w-[450px] flex-shrink-0">
            <div className="lg:sticky lg:top-6 space-y-4">
              <FormularioAnalisis
                equipos={equiposAnalisis}
                estadisticas={[]}
                onAnalizar={ejecutarAnalisis}
                cargando={cargandoAnalisis}
                cargandoEquipos={cargandoPartidos}
                partidosDisponibles={partidosSelector}
                opcionesMercado={opcionesMercadoFutbol}
              />
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

            {analisis && !cargandoAnalisis && (
              <div className="space-y-4">
                <ResultadoAnalisis
                  resultado={adaptarAnalisisFutbolAResultadoAnalisis(analisis)}
                  advertencias={[]}
                  seleccionUsuario={analisis.recomendaciones?.[0]
                    ? { lado: analisis.recomendaciones[0].lado, linea: analisis.recomendaciones[0].linea }
                    : null}
                  equipoLocalId={partidoSeleccionado?.equipoLocal}
                  equipoVisitanteId={partidoSeleccionado?.equipoVisitante}
                />

                {cargandoContexto ? (
                  <Tarjeta className="flex items-center justify-center py-12">
                    <Spinner tamano="lg" texto="Cargando contexto del partido..." centrado />
                  </Tarjeta>
                ) : (
                  <>
                    <PanelH2HFutbol partidos={h2hPartidos} limite={limiteH2h} onCambiarLimite={setLimiteH2h} />
                    {partidoSeleccionado && (
                      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                        <PanelHistorialEquipoFutbol
                          equipoId={String(partidoSeleccionado.equipoLocal)}
                          equipoNombre={partidoSeleccionado.equipoLocalNombre}
                          partidos={historialLocal}
                          limite={limiteLocal}
                          onCambiarLimite={setLimiteLocal}
                          ubicacion={ubicacionLocal}
                          onCambiarUbicacion={setUbicacionLocal}
                        />
                        <PanelHistorialEquipoFutbol
                          equipoId={String(partidoSeleccionado.equipoVisitante)}
                          equipoNombre={partidoSeleccionado.equipoVisitanteNombre}
                          partidos={historialVisitante}
                          limite={limiteVisitante}
                          onCambiarLimite={setLimiteVisitante}
                          ubicacion={ubicacionVisitante}
                          onCambiarUbicacion={setUbicacionVisitante}
                        />
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {!analisis && !cargandoAnalisis && (
              <div className="tarjeta h-full min-h-[500px]">
                <EstadoVacioFutbol />
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="border-t border-neon-cyan/10 bg-futurista-negro/80 backdrop-blur-sm">
        <div className="contenedor py-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-2 text-center md:text-left">
            <p className="text-texto-terciario text-xs uppercase tracking-wider">
              Football Analyzer — Flujo base canónico NBA
            </p>
            <p className="text-texto-terciario/60 text-xs">Las predicciones son orientativas. Apuesta responsablemente.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
