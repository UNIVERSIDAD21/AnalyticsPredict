/**
 * PaginaHistorialPredicciones.tsx — Historial de predicciones del sistema
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Calendar, History } from 'lucide-react';
import { Encabezado } from '../organismos';
import { Boton, Spinner } from '../atomos';
import { MensajeError } from '../moleculas';
import { obtenerHistorialPredicciones } from '../../servicios/predicciones';
import type {
  EstadoPrediccion,
  MercadoMetricas,
  ParametrosHistorialPredicciones,
  PrediccionHistorial,
  RespuestaHistorialPredicciones,
} from '../../tipos';

type PeriodoSeleccion = '7' | '30' | '90' | 'rango';

const TAMANO_PAGINA = 10;
const MERCADOS: MercadoMetricas[] = ['Q1', 'Q2', 'Q3', 'Q4', 'COMPLETO'];

const ESTADOS: EstadoPrediccion[] = ['GANADA', 'PERDIDA', 'PUSH', 'PENDIENTE'];

function formatearFechaISO(fecha: Date): string {
  return fecha.toISOString().slice(0, 10);
}

function formatearFechaCorta(fechaISO: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatearPorcentaje(valor: number | null) {
  if (valor === null || !isFinite(valor)) return '—';
  return `${(valor * 100).toFixed(1)}%`;
}

const badgeEstado: Record<EstadoPrediccion, string> = {
  GANADA: 'text-neon-verde border-neon-verde/40',
  PERDIDA: 'text-neon-rojo border-neon-rojo/40',
  PUSH: 'text-advertencia-500 border-advertencia-500/40',
  PENDIENTE: 'text-texto-terciario border-neon-cyan/20',
};

export function PaginaHistorialPredicciones() {
  const [pagina, setPagina] = useState(1);
  const [periodo, setPeriodo] = useState<PeriodoSeleccion>('30');
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const [mercado, setMercado] = useState<string>('');
  const [estado, setEstado] = useState<string>('');
  const [respuesta, setRespuesta] = useState<RespuestaHistorialPredicciones | null>(null);
  const [estadoPeticion, setEstadoPeticion] = useState<'idle' | 'cargando' | 'exito' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  const rangoValido = periodo !== 'rango' || (Boolean(desde) && Boolean(hasta));

  const parametrosPeriodo = useMemo(() => {
    if (periodo === 'rango') {
      return {
        desde: desde || undefined,
        hasta: hasta || undefined,
      };
    }

    const dias = Number(periodo);
    const hoy = new Date();
    const inicio = new Date();
    inicio.setDate(hoy.getDate() - dias);

    return {
      desde: formatearFechaISO(inicio),
      hasta: formatearFechaISO(hoy),
    };
  }, [periodo, desde, hasta]);

  const cargarHistorial = useCallback(async () => {
    if (!rangoValido) return;
    setEstadoPeticion('cargando');
    setError(null);

    const filtros: ParametrosHistorialPredicciones = {
      pagina,
      tamano: TAMANO_PAGINA,
      desde: parametrosPeriodo.desde,
      hasta: parametrosPeriodo.hasta,
      mercado: mercado ? (mercado as MercadoMetricas) : undefined,
      estado: estado ? (estado as EstadoPrediccion) : undefined,
    };

    try {
      const data = await obtenerHistorialPredicciones(filtros);
      setRespuesta(data);
      setEstadoPeticion('exito');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cargar el historial.');
      setEstadoPeticion('error');
    }
  }, [estado, mercado, pagina, parametrosPeriodo, rangoValido]);

  useEffect(() => {
    void cargarHistorial();
  }, [cargarHistorial]);

  const predicciones = respuesta?.predicciones ?? [];
  const resumen = respuesta?.resumen;

  const totalPaginas = respuesta?.total_paginas ?? 1;

  const cambiarPagina = (nuevaPagina: number) => {
    if (nuevaPagina < 1 || nuevaPagina > totalPaginas) return;
    setPagina(nuevaPagina);
  };

  const limpiarFiltros = () => {
    setMercado('');
    setEstado('');
    setPeriodo('30');
    setDesde('');
    setHasta('');
    setPagina(1);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-futurista text-texto-principal flex items-center gap-2">
              <History className="w-5 h-5 text-neon-cyan" />
              Historial de predicciones
            </h2>
            <p className="text-sm text-texto-secundario">
              Trazabilidad completa de predicciones, resultados y estado por mercado.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Boton variante="secundario" onClick={cargarHistorial}>
              Actualizar
            </Boton>
          </div>
        </div>

        <div className="tarjeta p-4 flex flex-wrap items-end gap-4">
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-widest text-texto-secundario">Mercado</label>
            <select
              value={mercado}
              onChange={(event) => {
                setMercado(event.target.value);
                setPagina(1);
              }}
              className="w-40 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20 text-texto-principal"
            >
              <option value="">Todos</option>
              {MERCADOS.map((mercadoItem) => (
                <option key={mercadoItem} value={mercadoItem}>
                  {mercadoItem}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-widest text-texto-secundario">Estado</label>
            <select
              value={estado}
              onChange={(event) => {
                setEstado(event.target.value);
                setPagina(1);
              }}
              className="w-40 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20 text-texto-principal"
            >
              <option value="">Todos</option>
              {ESTADOS.map((estadoItem) => (
                <option key={estadoItem} value={estadoItem}>
                  {estadoItem}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-widest text-texto-secundario">Periodo</label>
            <select
              value={periodo}
              onChange={(event) => {
                setPeriodo(event.target.value as PeriodoSeleccion);
                setPagina(1);
              }}
              className="w-40 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20 text-texto-principal"
            >
              <option value="7">Últimos 7 días</option>
              <option value="30">Últimos 30 días</option>
              <option value="90">Últimos 90 días</option>
              <option value="rango">Rango</option>
            </select>
          </div>

          {periodo === 'rango' && (
            <div className="flex flex-wrap items-center gap-3">
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-widest text-texto-secundario">Desde</label>
                <div className="flex items-center gap-2 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20">
                  <Calendar className="w-4 h-4 text-neon-cyan" />
                  <input
                    type="date"
                    value={desde}
                    onChange={(event) => {
                      setDesde(event.target.value);
                      setPagina(1);
                    }}
                    className="bg-transparent text-sm text-texto-principal focus:outline-none"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-widest text-texto-secundario">Hasta</label>
                <div className="flex items-center gap-2 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20">
                  <Calendar className="w-4 h-4 text-neon-cyan" />
                  <input
                    type="date"
                    value={hasta}
                    onChange={(event) => {
                      setHasta(event.target.value);
                      setPagina(1);
                    }}
                    className="bg-transparent text-sm text-texto-principal focus:outline-none"
                  />
                </div>
              </div>
            </div>
          )}

          {!rangoValido && (
            <div className="flex items-center gap-2 text-xs text-advertencia-500">
              <Calendar className="w-4 h-4" />
              Selecciona ambas fechas para cargar historial.
            </div>
          )}

          <div className="flex items-center gap-2">
            <Boton variante="fantasma" tamano="sm" onClick={limpiarFiltros}>
              Limpiar filtros
            </Boton>
          </div>
        </div>

        {estadoPeticion === 'error' && error && (
          <MensajeError titulo="Error al cargar historial" mensaje={error} />
        )}

        {estadoPeticion === 'cargando' && (
          <div className="tarjeta flex items-center justify-center min-h-[240px]">
            <Spinner tamano="lg" texto="Cargando historial..." centrado />
          </div>
        )}

        {estadoPeticion === 'exito' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              <div className="tarjeta p-4 space-y-1">
                <p className="text-xs uppercase tracking-widest text-texto-secundario">Total</p>
                <p className="text-2xl font-mono text-neon-cyan">{resumen?.total ?? 0}</p>
              </div>
              <div className="tarjeta p-4 space-y-1">
                <p className="text-xs uppercase tracking-widest text-texto-secundario">Ganadas</p>
                <p className="text-2xl font-mono text-neon-verde">{resumen?.ganadas ?? 0}</p>
              </div>
              <div className="tarjeta p-4 space-y-1">
                <p className="text-xs uppercase tracking-widest text-texto-secundario">Perdidas</p>
                <p className="text-2xl font-mono text-neon-rojo">{resumen?.perdidas ?? 0}</p>
              </div>
              <div className="tarjeta p-4 space-y-1">
                <p className="text-xs uppercase tracking-widest text-texto-secundario">Pendientes</p>
                <p className="text-2xl font-mono text-advertencia-500">{resumen?.pendientes ?? 0}</p>
              </div>
              <div className="tarjeta p-4 space-y-1">
                <p className="text-xs uppercase tracking-widest text-texto-secundario">Win rate</p>
                <p className="text-2xl font-mono text-neon-magenta">
                  {formatearPorcentaje(resumen?.win_rate ?? null)}
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {predicciones.length === 0 && (
                <div className="tarjeta p-6 text-center text-sm text-texto-secundario">
                  No hay predicciones para los filtros seleccionados.
                </div>
              )}
              {predicciones.map((prediccion) => (
                <TarjetaPrediccion key={prediccion.id} prediccion={prediccion} />
              ))}
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-xs text-texto-terciario">
                Página {respuesta?.pagina ?? 1} de {totalPaginas}
              </div>
              <div className="flex items-center gap-2">
                <Boton
                  variante="secundario"
                  tamano="sm"
                  disabled={pagina <= 1}
                  onClick={() => cambiarPagina(pagina - 1)}
                >
                  Anterior
                </Boton>
                <Boton
                  variante="secundario"
                  tamano="sm"
                  disabled={pagina >= totalPaginas}
                  onClick={() => cambiarPagina(pagina + 1)}
                >
                  Siguiente
                </Boton>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function TarjetaPrediccion({ prediccion }: { prediccion: PrediccionHistorial }) {
  const probabilidad = prediccion.probabilidad_usada ?? prediccion.probabilidad_raw;
  const probabilidadTexto = probabilidad !== null ? `${(probabilidad * 100).toFixed(1)}%` : '—';
  const origenTexto = prediccion.probabilidad_calibrada ? 'Calibrada' : 'Raw';

  return (
    <div className="tarjeta p-4 space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-texto-principal">
            {prediccion.equipo_local} vs {prediccion.equipo_visitante}
          </h3>
          <p className="text-xs text-texto-terciario">
            {formatearFechaCorta(prediccion.fecha_partido)} · {prediccion.mercado} · {prediccion.lado}{' '}
            {prediccion.linea}
          </p>
        </div>
        <span className={`px-2 py-1 rounded-full text-[10px] uppercase border ${badgeEstado[prediccion.estado]}`}>
          {prediccion.estado}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-4 text-xs text-texto-secundario">
        <div>
          Probabilidad ({origenTexto}): <span className="text-texto-principal">{probabilidadTexto}</span>
        </div>
        <div>
          Resultado real:{' '}
          <span className="text-texto-principal">
            {prediccion.valor_real !== null ? prediccion.valor_real.toFixed(1) : 'Pendiente'}
          </span>
        </div>
      </div>
    </div>
  );
}
