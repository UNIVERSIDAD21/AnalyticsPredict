/**
 * PaginaBitacora.tsx — Página de bitácora
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { ChevronDown, ChevronUp, BarChart3, TrendingUp, Target, AlertTriangle } from 'lucide-react';
import { Encabezado, FiltrosApuestas, ListaApuestas } from '../organismos';
import { ModalResultado, MensajeError } from '../moleculas';
import { Boton, Spinner } from '../atomos';
import { useBitacora } from '../../hooks';
import { actualizarResultadoApuesta, eliminarApuesta, obtenerMetricasBitacora } from '../../servicios';
import { Apuesta, ResultadoApuesta, RespuestaMetricasBitacora } from '../../tipos';

const TAMANO_PAGINA = 10;

export function PaginaBitacora() {
  const [pagina, setPagina] = useState(1);
  const [busquedaInput, setBusquedaInput] = useState('');
  const [filtros, setFiltros] = useState({
    resultado: '',
    mercado: '',
    confianza: '',
    orden: 'reciente',
    busqueda: '',
    desde: '',
    hasta: '',
  });

  const [apuestaSeleccionada, setApuestaSeleccionada] = useState<Apuesta | null>(null);
  const [mostrandoResultado, setMostrandoResultado] = useState(false);
  const [mensajeError, setMensajeError] = useState<string | null>(null);

  // Estado para métricas detalladas
  const [mostrarMetricas, setMostrarMetricas] = useState(false);
  const [metricas, setMetricas] = useState<RespuestaMetricasBitacora | null>(null);
  const [cargandoMetricas, setCargandoMetricas] = useState(false);
  const [errorMetricas, setErrorMetricas] = useState<string | null>(null);

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
    mercado: filtros.mercado || undefined,
    confianza: filtros.confianza || undefined,
    desde: filtros.desde || undefined,
    hasta: filtros.hasta || undefined,
    orden: filtros.orden || undefined,
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

  // Cargar métricas detalladas
  const cargarMetricas = useCallback(async () => {
    setCargandoMetricas(true);
    setErrorMetricas(null);
    try {
      const datos = await obtenerMetricasBitacora();
      setMetricas(datos);
    } catch (err) {
      setErrorMetricas(err instanceof Error ? err.message : 'Error al cargar métricas');
    } finally {
      setCargandoMetricas(false);
    }
  }, []);

  // Cargar métricas cuando se expande la sección
  useEffect(() => {
    if (mostrarMetricas && !metricas && !cargandoMetricas) {
      void cargarMetricas();
    }
  }, [mostrarMetricas, metricas, cargandoMetricas, cargarMetricas]);

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
      mercado: '',
      confianza: '',
      orden: 'reciente',
      busqueda: '',
      desde: '',
      hasta: '',
    });
    setBusquedaInput('');
    setPagina(1);
  };

  const manejarResolver = (apuesta: Apuesta) => {
    setApuestaSeleccionada(apuesta);
    setMostrandoResultado(true);
  };

  const manejarEliminar = async (apuesta: Apuesta) => {
    try {
      await eliminarApuesta(apuesta.id);
      await recargar();
    } catch (errorEliminar) {
      setMensajeError(errorEliminar instanceof Error ? errorEliminar.message : 'No se pudo eliminar');
    }
  };

  const manejarGuardarResultado = async (resultado: ResultadoApuesta, puntosReales?: number) => {
    if (!apuestaSeleccionada) return;
    try {
      await actualizarResultadoApuesta(apuestaSeleccionada.id, {
        resultado: resultado as Exclude<ResultadoApuesta, 'PENDIENTE'>,
        puntos_reales: puntosReales,
      });
      setMostrandoResultado(false);
      setApuestaSeleccionada(null);
      await recargar();
    } catch (errorActualizar) {
      setMensajeError(errorActualizar instanceof Error ? errorActualizar.message : 'No se pudo actualizar');
    }
  };

  const resumenDatos = {
    total: resumen?.total_apuestas ?? 0,
    pendientes: resumen?.pendientes ?? 0,
    ganancia: resumen?.ganancia_total ?? 0,
    winrate: resumen?.winrate ?? 0,
    roi: resumen?.roi ?? 0,
  } as Record<string, number>;

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />
      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <h2 className="text-2xl font-futurista text-texto-principal">Bitácora</h2>
          <Boton variante="secundario" onClick={recargar}>
            Refrescar
          </Boton>
        </div>

        {mensajeError && (
          <MensajeError
            titulo="Error en bitácora"
            mensaje={mensajeError}
            onCerrar={() => setMensajeError(null)}
          />
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="tarjeta p-4">
            <p className="text-xs text-texto-secundario uppercase tracking-widest">Total</p>
            <p className="text-xl text-texto-principal font-bold">{resumenDatos.total}</p>
          </div>
          <div className="tarjeta p-4">
            <p className="text-xs text-texto-secundario uppercase tracking-widest">Pendientes</p>
            <p className="text-xl text-texto-principal font-bold">{resumenDatos.pendientes}</p>
          </div>
          <div className="tarjeta p-4">
            <p className="text-xs text-texto-secundario uppercase tracking-widest">Ganancia</p>
            <p className="text-xl font-bold text-neon-verde">{Number(resumenDatos.ganancia).toFixed(2)}</p>
          </div>
          <div className="tarjeta p-4">
            <p className="text-xs text-texto-secundario uppercase tracking-widest">Winrate</p>
            <p className="text-xl text-texto-principal font-bold">{Number(resumenDatos.winrate).toFixed(2)}%</p>
          </div>
          <div className="tarjeta p-4">
            <p className="text-xs text-texto-secundario uppercase tracking-widest">ROI</p>
            <p className="text-xl text-texto-principal font-bold">{Number(resumenDatos.roi).toFixed(2)}%</p>
          </div>
        </div>

        {/* Sección de métricas detalladas */}
        <div className="tarjeta">
          <button
            type="button"
            onClick={() => setMostrarMetricas(!mostrarMetricas)}
            className="w-full p-4 flex items-center justify-between text-left hover:bg-futurista-medio/30 transition-colors rounded-lg"
          >
            <div className="flex items-center gap-3">
              <BarChart3 className="w-5 h-5 text-neon-cyan" />
              <div>
                <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-texto-principal">
                  Métricas Detalladas
                </h3>
                <p className="text-xs text-texto-secundario">
                  Rendimiento por mercado, confianza y tendencia temporal
                </p>
              </div>
            </div>
            {mostrarMetricas ? (
              <ChevronUp className="w-5 h-5 text-texto-secundario" />
            ) : (
              <ChevronDown className="w-5 h-5 text-texto-secundario" />
            )}
          </button>

          {mostrarMetricas && (
            <div className="px-4 pb-4 space-y-6">
              {cargandoMetricas && (
                <div className="flex items-center justify-center py-8">
                  <Spinner tamano="lg" texto="Cargando métricas..." centrado />
                </div>
              )}

              {errorMetricas && (
                <MensajeError
                  titulo="Error al cargar métricas"
                  mensaje={errorMetricas}
                  onCerrar={() => setErrorMetricas(null)}
                />
              )}

              {metricas && !cargandoMetricas && (
                <div className="space-y-6">
                  {/* Advertencias */}
                  {metricas.advertencias.length > 0 && (
                    <div className="p-3 rounded-lg bg-neon-amarillo/10 border border-neon-amarillo/30">
                      <div className="flex items-center gap-2 text-neon-amarillo mb-2">
                        <AlertTriangle className="w-4 h-4" />
                        <span className="text-xs font-semibold uppercase">Advertencias</span>
                      </div>
                      <ul className="text-xs text-texto-secundario space-y-1">
                        {metricas.advertencias.map((adv, idx) => (
                          <li key={idx}>{adv}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Métricas por mercado */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Target className="w-4 h-4 text-neon-cyan" />
                      <h4 className="text-sm font-semibold text-texto-principal uppercase tracking-wider">
                        Por Mercado
                      </h4>
                    </div>
                    {metricas.por_mercado.length > 0 ? (
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead className="text-xs uppercase tracking-wider text-texto-terciario">
                            <tr className="border-b border-neon-cyan/20">
                              <th className="py-2 text-left">Mercado</th>
                              <th className="py-2 text-right">Total</th>
                              <th className="py-2 text-right">Ganadas</th>
                              <th className="py-2 text-right">Winrate</th>
                              <th className="py-2 text-right">ROI</th>
                              <th className="py-2 text-right">Ganancia</th>
                            </tr>
                          </thead>
                          <tbody>
                            {metricas.por_mercado.map((m) => (
                              <tr key={m.mercado} className="border-b border-neon-cyan/10">
                                <td className="py-2 font-semibold text-texto-principal">{m.mercado}</td>
                                <td className="py-2 text-right text-texto-secundario">{m.total}</td>
                                <td className="py-2 text-right text-neon-verde">{m.ganadas}</td>
                                <td className="py-2 text-right text-texto-secundario">
                                  {m.win_rate != null ? `${(m.win_rate * 100).toFixed(1)}%` : '—'}
                                </td>
                                <td className={`py-2 text-right ${m.roi != null && m.roi >= 0 ? 'text-neon-verde' : 'text-neon-rojo'}`}>
                                  {m.roi != null ? `${(m.roi * 100).toFixed(2)}%` : '—'}
                                </td>
                                <td className={`py-2 text-right font-mono ${m.ganancia_total >= 0 ? 'text-neon-verde' : 'text-neon-rojo'}`}>
                                  {m.ganancia_total.toFixed(2)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="text-sm text-texto-terciario">No hay datos por mercado aún.</p>
                    )}
                  </div>

                  {/* Métricas por confianza */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-neon-verde" />
                      <h4 className="text-sm font-semibold text-texto-principal uppercase tracking-wider">
                        Por Nivel de Confianza
                      </h4>
                    </div>
                    {metricas.por_confianza.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {metricas.por_confianza.map((c) => (
                          <div
                            key={c.confianza}
                            className={`p-4 rounded-lg border ${
                              c.confianza === 'ALTA'
                                ? 'border-neon-verde/30 bg-neon-verde/5'
                                : c.confianza === 'MEDIA'
                                  ? 'border-neon-amarillo/30 bg-neon-amarillo/5'
                                  : 'border-neon-rojo/30 bg-neon-rojo/5'
                            }`}
                          >
                            <h5 className={`text-xs font-bold uppercase tracking-wider mb-2 ${
                              c.confianza === 'ALTA'
                                ? 'text-neon-verde'
                                : c.confianza === 'MEDIA'
                                  ? 'text-neon-amarillo'
                                  : 'text-neon-rojo'
                            }`}>
                              {c.confianza}
                            </h5>
                            <div className="space-y-1 text-sm">
                              <div className="flex justify-between">
                                <span className="text-texto-secundario">Apuestas:</span>
                                <span className="text-texto-principal">{c.total}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-texto-secundario">Winrate:</span>
                                <span className="text-texto-principal">
                                  {c.win_rate != null ? `${(c.win_rate * 100).toFixed(1)}%` : '—'}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-texto-secundario">ROI:</span>
                                <span className={c.roi != null && c.roi >= 0 ? 'text-neon-verde' : 'text-neon-rojo'}>
                                  {c.roi != null ? `${(c.roi * 100).toFixed(2)}%` : '—'}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-texto-terciario">No hay datos por confianza aún.</p>
                    )}
                  </div>

                  {/* Tendencia mensual */}
                  {metricas.por_mes.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-semibold text-texto-principal uppercase tracking-wider">
                        Tendencia Mensual (últimos 12 meses)
                      </h4>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead className="text-xs uppercase tracking-wider text-texto-terciario">
                            <tr className="border-b border-neon-cyan/20">
                              <th className="py-2 text-left">Mes</th>
                              <th className="py-2 text-right">Apuestas</th>
                              <th className="py-2 text-right">Winrate</th>
                              <th className="py-2 text-right">Ganancia</th>
                              <th className="py-2 text-right">ROI</th>
                            </tr>
                          </thead>
                          <tbody>
                            {metricas.por_mes.map((m) => (
                              <tr key={m.periodo} className="border-b border-neon-cyan/10">
                                <td className="py-2 font-semibold text-texto-principal">{m.periodo}</td>
                                <td className="py-2 text-right text-texto-secundario">{m.total}</td>
                                <td className="py-2 text-right text-texto-secundario">
                                  {m.win_rate != null ? `${(m.win_rate * 100).toFixed(1)}%` : '—'}
                                </td>
                                <td className={`py-2 text-right font-mono ${m.ganancia >= 0 ? 'text-neon-verde' : 'text-neon-rojo'}`}>
                                  {m.ganancia.toFixed(2)}
                                </td>
                                <td className={`py-2 text-right ${m.roi != null && m.roi >= 0 ? 'text-neon-verde' : 'text-neon-rojo'}`}>
                                  {m.roi != null ? `${(m.roi * 100).toFixed(2)}%` : '—'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  <div className="pt-2">
                    <Boton variante="secundario" tamano="sm" onClick={cargarMetricas}>
                      Actualizar métricas
                    </Boton>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <FiltrosApuestas
          resultado={filtros.resultado}
          mercado={filtros.mercado}
          confianza={filtros.confianza}
          orden={filtros.orden}
          busqueda={busquedaInput}
          desde={filtros.desde}
          hasta={filtros.hasta}
          onChange={manejarFiltro}
          onLimpiar={limpiarFiltros}
        />

        <ListaApuestas
          apuestas={apuestas}
          estado={estado}
          mensajeVacio={total === 0 ? 'Aún no tienes apuestas guardadas.' : 'No hay apuestas con estos filtros.'}
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
    </div>
  );
}
