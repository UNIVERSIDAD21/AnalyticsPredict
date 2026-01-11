/**
 * PaginaBitacora.tsx — Página de bitácora
 */

import { useEffect, useMemo, useState, useCallback } from 'react';
import { ChevronDown, ChevronUp, BarChart3, TrendingUp, Target, Calendar } from 'lucide-react';
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

  // Estado para métricas expandibles
  const [metricasExpandidas, setMetricasExpandidas] = useState(false);
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

  // Cargar métricas cuando se expanda la sección
  const cargarMetricas = useCallback(async () => {
    setCargandoMetricas(true);
    setErrorMetricas(null);
    try {
      const resultado = await obtenerMetricasBitacora({
        desde: filtros.desde || undefined,
        hasta: filtros.hasta || undefined,
        mercado: filtros.mercado || undefined,
      });
      setMetricas(resultado);
    } catch (err) {
      setErrorMetricas(err instanceof Error ? err.message : 'Error al cargar métricas');
    } finally {
      setCargandoMetricas(false);
    }
  }, [filtros.desde, filtros.hasta, filtros.mercado]);

  useEffect(() => {
    if (metricasExpandidas) {
      cargarMetricas();
    }
  }, [metricasExpandidas, cargarMetricas]);

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

        {/* Sección expandible de métricas detalladas */}
        <div className="tarjeta">
          <button
            type="button"
            onClick={() => setMetricasExpandidas(!metricasExpandidas)}
            className="w-full flex items-center justify-between p-4 hover:bg-futurista-medio/50 transition-colors rounded-lg"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-neon-cyan/10 border border-neon-cyan/30 flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-neon-cyan" />
              </div>
              <div className="text-left">
                <h3 className="text-lg font-futurista text-texto-principal">
                  Métricas Detalladas
                </h3>
                <p className="text-xs text-texto-secundario">
                  Win rate, ROI y ganancias por mercado, confianza y mes
                </p>
              </div>
            </div>
            {metricasExpandidas ? (
              <ChevronUp className="w-5 h-5 text-neon-cyan" />
            ) : (
              <ChevronDown className="w-5 h-5 text-neon-cyan" />
            )}
          </button>

          {metricasExpandidas && (
            <div className="border-t border-neon-cyan/10 p-4 space-y-6">
              {cargandoMetricas && (
                <div className="flex justify-center py-8">
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
                <>
                  {/* Advertencias */}
                  {metricas.advertencias.length > 0 && (
                    <div className="p-3 rounded-lg bg-neon-amarillo/10 border border-neon-amarillo/30">
                      <p className="text-xs text-neon-amarillo">
                        {metricas.advertencias.join(' ')}
                      </p>
                    </div>
                  )}

                  {/* Métricas por Mercado */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Target className="w-4 h-4 text-neon-cyan" />
                      <h4 className="text-sm font-semibold text-neon-cyan uppercase tracking-wider">
                        Por Mercado
                      </h4>
                    </div>
                    {metricas.por_mercado.length === 0 ? (
                      <p className="text-sm text-texto-terciario">Sin datos por mercado</p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
                        {metricas.por_mercado.map((m) => (
                          <div
                            key={m.mercado}
                            className="p-3 rounded-lg bg-futurista-medio/50 border border-neon-cyan/10"
                          >
                            <p className="text-xs font-bold text-neon-cyan mb-2">{m.mercado}</p>
                            <div className="space-y-1 text-xs">
                              <div className="flex justify-between">
                                <span className="text-texto-secundario">Apuestas:</span>
                                <span className="text-texto-principal">{m.total}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-texto-secundario">Win Rate:</span>
                                <span className={m.win_rate && m.win_rate >= 0.5 ? 'text-neon-verde' : 'text-neon-rojo'}>
                                  {m.win_rate != null ? `${(m.win_rate * 100).toFixed(1)}%` : 'N/A'}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-texto-secundario">ROI:</span>
                                <span className={m.roi && m.roi >= 0 ? 'text-neon-verde' : 'text-neon-rojo'}>
                                  {m.roi != null ? `${(m.roi * 100).toFixed(1)}%` : 'N/A'}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-texto-secundario">Ganancia:</span>
                                <span className={m.ganancia_total >= 0 ? 'text-neon-verde' : 'text-neon-rojo'}>
                                  ${m.ganancia_total.toFixed(2)}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Métricas por Confianza */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-neon-verde" />
                      <h4 className="text-sm font-semibold text-neon-verde uppercase tracking-wider">
                        Por Nivel de Confianza
                      </h4>
                    </div>
                    {metricas.por_confianza.length === 0 ? (
                      <p className="text-sm text-texto-terciario">Sin datos por confianza</p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {metricas.por_confianza.map((c) => (
                          <div
                            key={c.confianza}
                            className={`p-3 rounded-lg border ${
                              c.confianza === 'ALTA'
                                ? 'bg-neon-verde/5 border-neon-verde/30'
                                : c.confianza === 'MEDIA'
                                  ? 'bg-neon-amarillo/5 border-neon-amarillo/30'
                                  : 'bg-neon-rojo/5 border-neon-rojo/30'
                            }`}
                          >
                            <p
                              className={`text-xs font-bold mb-2 ${
                                c.confianza === 'ALTA'
                                  ? 'text-neon-verde'
                                  : c.confianza === 'MEDIA'
                                    ? 'text-neon-amarillo'
                                    : 'text-neon-rojo'
                              }`}
                            >
                              {c.confianza}
                            </p>
                            <div className="space-y-1 text-xs">
                              <div className="flex justify-between">
                                <span className="text-texto-secundario">Apuestas:</span>
                                <span className="text-texto-principal">{c.total}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-texto-secundario">Récord:</span>
                                <span className="text-texto-principal">{c.ganadas}W - {c.perdidas}L</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-texto-secundario">Win Rate:</span>
                                <span className={c.win_rate && c.win_rate >= 0.5 ? 'text-neon-verde' : 'text-neon-rojo'}>
                                  {c.win_rate != null ? `${(c.win_rate * 100).toFixed(1)}%` : 'N/A'}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-texto-secundario">ROI:</span>
                                <span className={c.roi && c.roi >= 0 ? 'text-neon-verde' : 'text-neon-rojo'}>
                                  {c.roi != null ? `${(c.roi * 100).toFixed(1)}%` : 'N/A'}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-texto-secundario">Ganancia:</span>
                                <span className={c.ganancia_total >= 0 ? 'text-neon-verde' : 'text-neon-rojo'}>
                                  ${c.ganancia_total.toFixed(2)}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Tendencia Mensual */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-neon-magenta" />
                      <h4 className="text-sm font-semibold text-neon-magenta uppercase tracking-wider">
                        Tendencia Mensual
                      </h4>
                    </div>
                    {metricas.por_mes.length === 0 ? (
                      <p className="text-sm text-texto-terciario">Sin datos mensuales</p>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="border-b border-neon-cyan/10">
                              <th className="text-left py-2 px-3 text-texto-secundario font-semibold">Mes</th>
                              <th className="text-right py-2 px-3 text-texto-secundario font-semibold">Apuestas</th>
                              <th className="text-right py-2 px-3 text-texto-secundario font-semibold">Récord</th>
                              <th className="text-right py-2 px-3 text-texto-secundario font-semibold">Win Rate</th>
                              <th className="text-right py-2 px-3 text-texto-secundario font-semibold">ROI</th>
                              <th className="text-right py-2 px-3 text-texto-secundario font-semibold">Ganancia</th>
                            </tr>
                          </thead>
                          <tbody>
                            {metricas.por_mes.map((m) => (
                              <tr key={m.periodo} className="border-b border-neon-cyan/5 hover:bg-futurista-medio/30">
                                <td className="py-2 px-3 text-texto-principal font-medium">{m.periodo}</td>
                                <td className="py-2 px-3 text-right text-texto-secundario">{m.total}</td>
                                <td className="py-2 px-3 text-right text-texto-secundario">{m.ganadas}W - {m.perdidas}L</td>
                                <td className={`py-2 px-3 text-right ${m.win_rate && m.win_rate >= 0.5 ? 'text-neon-verde' : 'text-neon-rojo'}`}>
                                  {m.win_rate != null ? `${(m.win_rate * 100).toFixed(1)}%` : 'N/A'}
                                </td>
                                <td className={`py-2 px-3 text-right ${m.roi && m.roi >= 0 ? 'text-neon-verde' : 'text-neon-rojo'}`}>
                                  {m.roi != null ? `${(m.roi * 100).toFixed(1)}%` : 'N/A'}
                                </td>
                                <td className={`py-2 px-3 text-right font-medium ${m.ganancia >= 0 ? 'text-neon-verde' : 'text-neon-rojo'}`}>
                                  ${m.ganancia.toFixed(2)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </>
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
