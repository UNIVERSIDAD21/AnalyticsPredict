/**
 * PaginaBitacora.tsx — Página de bitácora
 */

import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Encabezado, FiltrosApuestas, ListaBitacoraUnificada } from '../organismos';
import { ModalResultado, MensajeError } from '../moleculas';
import { Boton } from '../atomos';
import { useBitacora } from '../../hooks';
import { actualizarResultadoApuesta, eliminarApuesta, eliminarCombinada, actualizarResultadoCombinada } from '../../servicios';
import { RegistroBitacoraUnificada, ResultadoApuesta } from '../../tipos';

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
  const [apuestaAEliminar, setApuestaAEliminar] = useState<RegistroBitacoraUnificada | null>(null);
  const [eliminando, setEliminando] = useState(false);

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
    total: resumen?.total_apuestas ?? 0,
    pendientes: resumen?.pendientes ?? 0,
    ganancia: resumen?.ganancia_total ?? 0,
    winrate: resumen?.winrate ?? 0,
    roi: resumen?.roi ?? 0,
  } as unknown as Record<string, number>;

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
