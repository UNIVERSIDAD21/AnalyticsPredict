/**
 * PaginaBitacora.tsx — Página de bitácora
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Encabezado, FiltrosApuestas, ListaBitacoraUnificada } from '../organismos';
import { ModalResultado, MensajeError } from '../moleculas';
import { Boton } from '../atomos';
import { useBitacora } from '../../hooks';
import { actualizarResultadoApuesta, eliminarApuesta, eliminarCombinada, actualizarResultadoCombinada, archivarPartidoGuardado, listarPartidosGuardados, resolverPendientesBitacora } from '../../servicios';
import { RegistroBitacoraUnificada, ResultadoApuesta } from '../../tipos';
import type { PartidoGuardadoFutbol } from '../../tipos';

const TAMANO_PAGINA = 20;

export function PaginaBitacora() {
  const [pagina, setPagina] = useState(1);
  const [busquedaInput, setBusquedaInput] = useState('');
  const [filtros, setFiltros] = useState({
    resultado: '',
    deporte: '',
    mercado: '',
    confianza: '',
    orden: 'reciente',
    busqueda: '',
    desde: '',
    hasta: '',
    tipo_apuesta: '',
  });

  const [apuestaSeleccionada, setApuestaSeleccionada] = useState<RegistroBitacoraUnificada | null>(null);
  const [mostrandoResultado, setMostrandoResultado] = useState(false);
  const [mensajeError, setMensajeError] = useState<string | null>(null);
  const [resolviendo, setResolviendo] = useState(false);
  const [mensajeResolucion, setMensajeResolucion] = useState<string | null>(null);
  const [apuestaAEliminar, setApuestaAEliminar] = useState<RegistroBitacoraUnificada | null>(null);
  const [eliminando, setEliminando] = useState(false);
  const [partidosGuardados, setPartidosGuardados] = useState<PartidoGuardadoFutbol[]>([]);
  const [cargandoPartidosGuardados, setCargandoPartidosGuardados] = useState(true);
  const [partidoArchivando, setPartidoArchivando] = useState<string | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setFiltros((prev) => ({ ...prev, busqueda: busquedaInput }));
      setPagina(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [busquedaInput]);

  const filtrosActivos = useMemo(() => ({
    ...filtros,
    busqueda: filtros.busqueda || undefined,
    resultado: filtros.resultado || undefined,
    deporte: filtros.deporte || undefined,
    mercado: filtros.mercado || undefined,
    confianza: filtros.confianza || undefined,
    desde: filtros.desde || undefined,
    hasta: filtros.hasta || undefined,
    orden: filtros.orden || undefined,
    tipo_apuesta: filtros.tipo_apuesta || undefined,
  }), [filtros]);

  const {
    apuestas,
    total,
    totalPaginas,
    resumen,
    estado,
    error,
    recargar,
  } = useBitacora(filtrosActivos, pagina, TAMANO_PAGINA);

  useEffect(() => {
    if (error) {
      setMensajeError(error);
    }
  }, [error]);

  const recargarPartidosGuardados = useCallback(async () => {
    try {
      const respuesta = await listarPartidosGuardados();
      setPartidosGuardados(respuesta.partidos);
    } catch (errorCarga) {
      setMensajeError(errorCarga instanceof Error ? errorCarga.message : 'No se pudieron cargar los partidos guardados');
    } finally {
      setCargandoPartidosGuardados(false);
    }
  }, []);

  useEffect(() => {
    void recargarPartidosGuardados();
  }, [recargarPartidosGuardados]);

  const manejarArchivarPartido = async (partidoId: string) => {
    setPartidoArchivando(partidoId);
    try {
      await archivarPartidoGuardado(partidoId);
      setPartidosGuardados((actuales) => actuales.filter((partido) => partido.partido_id !== partidoId));
    } catch (errorArchivar) {
      setMensajeError(errorArchivar instanceof Error ? errorArchivar.message : 'No se pudo quitar el partido guardado');
    } finally {
      setPartidoArchivando(null);
    }
  };

  const manejarFiltro = (campo: string, valor: string) => {
    if (campo === 'busqueda') {
      setBusquedaInput(valor);
      return;
    }
    setFiltros((prev) => ({ ...prev, [campo]: valor }));
    setPagina(1);
  };

  const limpiarFiltros = () => {
    setFiltros({
      resultado: '',
      deporte: '',
      mercado: '',
      confianza: '',
      orden: 'reciente',
      busqueda: '',
      desde: '',
      hasta: '',
      tipo_apuesta: '',
    });
    setBusquedaInput('');
    setPagina(1);
  };

  const manejarResolver = (apuesta: RegistroBitacoraUnificada) => {
    setApuestaSeleccionada(apuesta);
    setMostrandoResultado(true);
  };

  const completarPendientes = async () => {
    setResolviendo(true);
    setMensajeResolucion(null);
    try {
      const r = await resolverPendientesBitacora();
      const motivos: Record<string, string> = {
        sin_partido: 'sin partido vinculado', partido_no_valido: 'partido no válido',
        partido_no_finalizado: 'partido aún no finalizado en los datos',
        partido_futuro: 'partido futuro', fecha_no_disponible: 'fecha no disponible',
        sin_datos_mercado: 'resultado o estadística del mercado incompletos',
        competicion_inconsistente: 'competición del registro no coincide',
        competicion_no_soportada: 'competición no compatible',
        contrato_apuesta_invalido: 'selección o línea inválida',
        linea_asiatica_no_soportada: 'línea asiática que requiere revisión',
      };
      const detalle = Object.entries(r.motivos_pendientes).map(([motivo, n]) => `${n} ${motivos[motivo] || motivo}`).join('; ');
      setMensajeResolucion(`${r.resueltas} apuestas completadas con los resultados guardados. ${r.pendientes} pendientes${detalle ? `: ${detalle}` : ''}. ${r.errores} errores.${r.importes_no_disponibles ? ` ${r.importes_no_disponibles} completadas con importe N/D por cuota o stake ausentes/inválidos.` : ''}`);
      await recargar();
    } catch (errorResolucion) {
      setMensajeError(errorResolucion instanceof Error ? errorResolucion.message : 'No se pudieron completar las apuestas');
    } finally {
      setResolviendo(false);
    }
  };

  const manejarEliminar = (apuesta: RegistroBitacoraUnificada) => {
    setApuestaAEliminar(apuesta);
  };

  const confirmarEliminar = async () => {
    if (!apuestaAEliminar) return;
    setEliminando(true);
    try {
      if (apuestaAEliminar.tipo_apuesta === 'COMBINADA') {
        await eliminarCombinada(apuestaAEliminar.id);
      } else {
        await eliminarApuesta(apuestaAEliminar.id);
      }
      setApuestaAEliminar(null);
      await recargar();
    } catch (errorEliminar) {
      setMensajeError(errorEliminar instanceof Error ? errorEliminar.message : 'No se pudo eliminar');
    } finally {
      setEliminando(false);
    }
  };

  const cancelarEliminar = () => {
    setApuestaAEliminar(null);
  };

  const manejarGuardarResultado = async (resultado: ResultadoApuesta, puntosReales?: number) => {
    if (!apuestaSeleccionada) return;
    try {
      if (apuestaSeleccionada.tipo_apuesta === 'COMBINADA') {
        await actualizarResultadoCombinada(apuestaSeleccionada.id, {
          resultado: resultado as 'GANADA' | 'PERDIDA' | 'PUSH' | 'ANULADA',
        });
      } else {
        await actualizarResultadoApuesta(apuestaSeleccionada.id, {
          resultado: resultado as Exclude<ResultadoApuesta, 'PENDIENTE'>,
          puntos_reales: puntosReales,
        });
      }
      setMostrandoResultado(false);
      setApuestaSeleccionada(null);
      await recargar();
    } catch (errorActualizar) {
      setMensajeError(errorActualizar instanceof Error ? errorActualizar.message : 'No se pudo actualizar');
    }
  };

  const resumenDatos = {
    total: typeof resumen?.total_apuestas === 'number' ? resumen.total_apuestas : null,
    pendientes: typeof resumen?.pendientes === 'number' ? resumen.pendientes : null,
    ganancia: typeof resumen?.ganancia_total === 'number' ? resumen.ganancia_total : null,
    winrate: typeof resumen?.winrate === 'number' ? resumen.winrate : null,
    roi: typeof resumen?.roi === 'number' ? resumen.roi : null,
    pnlNoEvaluable: typeof resumen?.n_pnl_no_evaluable === 'number' ? resumen.n_pnl_no_evaluable : null,
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />
      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        {/* Botón de regresar al inicio */}
        <button
          type="button"
          onClick={() => {
            window.location.href = '/';
          }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg
                     border border-neon-cyan/30 bg-futurista-oscuro/50
                     text-neon-cyan hover:bg-neon-cyan/10 hover:border-neon-cyan/50
                     transition-all duration-200 text-sm font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Volver al Inicio</span>
        </button>

        <div className="flex items-center justify-between flex-wrap gap-3">
          <h2 className="text-2xl font-futurista text-texto-principal">Bitácora</h2>
          <div className="flex gap-2 flex-wrap">
            <Boton variante="secundario" disabled={resolviendo} onClick={() => void completarPendientes()}>
              {resolviendo ? 'Completando…' : 'Completar finalizadas'}
            </Boton>
            <Boton variante="secundario" onClick={recargar}>Refrescar</Boton>
          </div>
        </div>

        <p className="text-xs text-texto-secundario">“Completar finalizadas” verifica apuestas simples NBA, Euroliga y fútbol con los datos guardados. No descarga marcadores; un resultado ausente sigue pendiente.</p>
        {mensajeResolucion && <p role="status" className="text-sm text-neon-cyan">{mensajeResolucion}</p>}

        {mensajeError && (
          <MensajeError
            titulo="Error en bitácora"
            mensaje={mensajeError}
            onCerrar={() => setMensajeError(null)}
          />
        )}

        <p className="text-xs text-neon-amarillo">Agregados monetarios N/D: no hay soportes originales ni unidad acreditada. Los importes individuales se conservan. {resumenDatos.pnlNoEvaluable ? `${resumenDatos.pnlNoEvaluable} apuestas resueltas excluidas de P&L en este corte.` : 'Los conteos y resultados son registrados, no rendimiento certificado.'}</p>

        <section className="tarjeta p-4 space-y-3" aria-labelledby="partidos-guardados-titulo">
          <div>
            <h3 id="partidos-guardados-titulo" className="text-lg font-semibold text-texto-principal">Partidos guardados para revisar</h3>
            <p className="text-sm text-texto-secundario">Son marcadores de consulta, no apuestas y no cuentan en las métricas de apuestas.</p>
          </div>
          {cargandoPartidosGuardados ? (
            <p className="text-sm text-texto-secundario">Cargando partidos guardados…</p>
          ) : partidosGuardados.length === 0 ? (
            <p className="text-sm text-texto-secundario">Aún no guardas partidos. Selecciona uno en Fútbol y pulsa “Guardar para revisar”.</p>
          ) : (
            <ul className="space-y-3">
              {partidosGuardados.map(({ partido, partido_id: partidoId }) => (
                <li key={partidoId} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-lg border border-neon-cyan/15 bg-futurista-oscuro/40 p-3">
                  <div>
                    <p className="font-semibold text-texto-principal">
                      {partido.equipo_local || 'Local'} vs {partido.equipo_visitante || 'Visitante'}
                    </p>
                    <p className="text-xs text-texto-secundario">
                      {partido.competicion || 'Competición no disponible'}
                      {partido.fecha_partido ? ` · ${new Date(partido.fecha_partido).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })}` : ''}
                      {partido.goles_local != null && partido.goles_visitante != null ? ` · ${partido.goles_local}-${partido.goles_visitante}` : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <a
                      href={`/futbol?partidoId=${encodeURIComponent(partidoId)}`}
                      className="inline-flex items-center justify-center rounded-lg border border-neon-cyan/30 px-3 py-2 text-sm text-neon-cyan hover:bg-neon-cyan/10"
                    >
                      Abrir partido
                    </a>
                    <Boton variante="fantasma" tamano="sm" disabled={partidoArchivando === partidoId} onClick={() => void manejarArchivarPartido(partidoId)}>
                      {partidoArchivando === partidoId ? 'Quitando…' : 'Quitar'}
                    </Boton>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="tarjeta p-4">
            <p className="text-xs text-texto-secundario uppercase tracking-widest">Total</p>
            <p className="text-xl text-texto-principal font-bold">{resumenDatos.total ?? 'N/D'}</p>
          </div>
          <div className="tarjeta p-4">
            <p className="text-xs text-texto-secundario uppercase tracking-widest">Pendientes</p>
            <p className="text-xl text-texto-principal font-bold">{resumenDatos.pendientes ?? 'N/D'}</p>
          </div>
          <div className="tarjeta p-4">
            <p className="text-xs text-texto-secundario uppercase tracking-widest">Ganancia agregada</p>
            <p className="text-xl font-bold text-neon-amarillo">{resumenDatos.ganancia == null ? 'N/D' : resumenDatos.ganancia.toFixed(2)}</p>
          </div>
          <div className="tarjeta p-4">
            <p className="text-xs text-texto-secundario uppercase tracking-widest">Winrate</p>
            <p className="text-xl text-texto-principal font-bold">{resumenDatos.winrate == null ? 'N/D' : `${resumenDatos.winrate.toFixed(2)}%`}</p>
          </div>
          <div className="tarjeta p-4">
            <p className="text-xs text-texto-secundario uppercase tracking-widest">ROI histórico</p>
            <p className="text-xl text-texto-principal font-bold">{resumenDatos.roi == null ? 'N/D' : `${resumenDatos.roi.toFixed(2)}%`}</p>
          </div>
        </div>


        <FiltrosApuestas
          resultado={filtros.resultado}
          deporte={filtros.deporte}
          mercado={filtros.mercado}
          confianza={filtros.confianza}
          orden={filtros.orden}
          busqueda={busquedaInput}
          desde={filtros.desde}
          hasta={filtros.hasta}
          tipoApuesta={filtros.tipo_apuesta}
          onChange={manejarFiltro}
          onLimpiar={limpiarFiltros}
        />

        <ListaBitacoraUnificada
          apuestas={apuestas}
          estado={estado}
          mensajeVacio={Object.entries(filtros).some(([campo, valor]) => campo !== 'orden' && Boolean(valor))
            ? 'No hay apuestas con estos filtros.'
            : 'Aún no tienes apuestas guardadas.'}
          onResolver={manejarResolver}
          onEliminar={manejarEliminar}
        />

        <div className="flex items-center justify-between">
          <span className="text-sm text-texto-secundario">
            Página {pagina} de {totalPaginas || 1}
          </span>
          <div className="flex items-center gap-2">
            <Boton
              variante="secundario"
              tamano="sm"
              disabled={pagina <= 1}
              onClick={() => setPagina((prev) => Math.max(1, prev - 1))}
            >
              Anterior
            </Boton>
            <Boton
              variante="secundario"
              tamano="sm"
              disabled={pagina >= totalPaginas}
              onClick={() => setPagina((prev) => Math.min(totalPaginas, prev + 1))}
            >
              Siguiente
            </Boton>
          </div>
        </div>
      </main>

      <ModalResultado
        abierto={mostrandoResultado}
        onCerrar={() => setMostrandoResultado(false)}
        onGuardar={manejarGuardarResultado}
      />

      {/* Modal de confirmación para eliminar */}
      {apuestaAEliminar && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-md rounded-xl border border-neon-rojo/30 bg-futurista-oscuro p-6">
            <h3 className="text-lg font-futurista text-texto-principal mb-4">
              Confirmar eliminación
            </h3>
            <p className="text-texto-secundario mb-2">
              ¿Estás seguro de que deseas eliminar esta apuesta?
            </p>
            <div className="bg-futurista-medio/50 rounded-lg p-3 mb-4">
              <p className="text-texto-principal font-semibold">
                {apuestaAEliminar.tipo_apuesta === 'COMBINADA'
                  ? `Parlay de ${apuestaAEliminar.n_selecciones ?? 0} selecciones`
                  : `${apuestaAEliminar.equipo_local} vs ${apuestaAEliminar.equipo_visitante}`}
              </p>
              <p className="text-sm text-texto-secundario">
                {apuestaAEliminar.tipo_apuesta === 'COMBINADA'
                  ? `Cuota @${apuestaAEliminar.cuota_total ?? 0}`
                  : `${apuestaAEliminar.lado} ${apuestaAEliminar.linea} · ${apuestaAEliminar.mercado}`}
              </p>
            </div>
            <p className="text-xs text-neon-rojo mb-4">
              Esta acción no se puede deshacer.
            </p>
            <div className="flex justify-end gap-3">
              <Boton
                variante="fantasma"
                onClick={cancelarEliminar}
                disabled={eliminando}
              >
                Cancelar
              </Boton>
              <Boton
                variante="peligro"
                onClick={confirmarEliminar}
                disabled={eliminando}
              >
                {eliminando ? 'Eliminando...' : 'Eliminar'}
              </Boton>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
