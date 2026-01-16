/**
 * ListaBitacoraUnificada.tsx — Tabla unificada para apuestas simples y combinadas
 */

import { Fragment, useState } from 'react';
import { CheckCircle, ChevronDown, ChevronUp, Eye, Trash2 } from 'lucide-react';
import { RegistroBitacoraUnificada } from '../../tipos';

interface PropsListaBitacoraUnificada {
  apuestas: RegistroBitacoraUnificada[];
  estado: 'idle' | 'cargando' | 'exito' | 'error';
  mensajeVacio: string;
  onResolver: (apuesta: RegistroBitacoraUnificada) => void;
  onEliminar: (apuesta: RegistroBitacoraUnificada) => void;
}

type OrdenColumna = 'fecha' | 'stake' | 'ganancia' | 'cuota';
type DireccionOrden = 'asc' | 'desc';

const estilosEstado: Record<string, { badge: string; fila: string }> = {
  GANADA: {
    badge: 'bg-neon-verde/20 text-neon-verde border-neon-verde/30',
    fila: 'hover:bg-neon-verde/5',
  },
  PERDIDA: {
    badge: 'bg-neon-rojo/20 text-neon-rojo border-neon-rojo/30',
    fila: 'hover:bg-neon-rojo/5',
  },
  PUSH: {
    badge: 'bg-advertencia-500/20 text-advertencia-500 border-advertencia-500/30',
    fila: 'hover:bg-advertencia-500/5',
  },
  PENDIENTE: {
    badge: 'bg-neon-cyan/20 text-neon-cyan border-neon-cyan/30',
    fila: 'hover:bg-neon-cyan/5',
  },
  ANULADA: {
    badge: 'bg-texto-terciario/20 text-texto-terciario border-texto-terciario/30',
    fila: 'hover:bg-texto-terciario/5',
  },
};

const estilosConfianza: Record<string, string> = {
  ALTA: 'text-neon-verde',
  MEDIA: 'text-advertencia-500',
  BAJA: 'text-neon-rojo',
};

function formatearFechaCorta(fecha: string | Date | null | undefined): string {
  if (!fecha) return '—';
  const d = typeof fecha === 'string' ? new Date(fecha) : fecha;
  return d.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  });
}

function formatearDinero(valor: number | null | undefined, mostrarSigno = false): string {
  if (valor === null || valor === undefined) return '—';
  const signo = mostrarSigno && valor > 0 ? '+' : '';
  return `${signo}$${valor.toFixed(2)}`;
}

function formatearPorcentaje(valor: number | null | undefined): string {
  if (valor === null || valor === undefined) return '—';
  const signo = valor > 0 ? '+' : '';
  return `${signo}${(valor * 100).toFixed(1)}%`;
}

function formatearEquipo(nombre?: string | null): string {
  return nombre ? nombre.toUpperCase() : '—';
}

function formatearLinea(valor?: number | string | null): string {
  if (valor === null || valor === undefined) return '—';
  const numero = typeof valor === 'string' ? parseFloat(valor) : valor;
  return Number.isNaN(numero) ? '—' : numero.toFixed(1);
}

function formatearCuota(valor?: number | string | null): string {
  if (valor === null || valor === undefined) return '—';
  const numero = typeof valor === 'string' ? parseFloat(valor) : valor;
  return Number.isNaN(numero) ? '—' : numero.toFixed(2);
}

function obtenerFechaRegistro(apuesta: RegistroBitacoraUnificada): string | null | undefined {
  return apuesta.fecha_partido ?? apuesta.creado_en ?? null;
}

export function ListaBitacoraUnificada({
  apuestas,
  estado,
  mensajeVacio,
  onResolver,
  onEliminar,
}: PropsListaBitacoraUnificada) {
  const [ordenColumna, setOrdenColumna] = useState<OrdenColumna>('fecha');
  const [direccionOrden, setDireccionOrden] = useState<DireccionOrden>('desc');

  const formatearProbabilidad = (valor?: number | null): string => {
    if (valor === null || valor === undefined) return '—';
    return `${(valor * 100).toFixed(1)}%`;
  };

  const apuestasOrdenadas = [...apuestas].sort((a, b) => {
    let comparacion = 0;

    switch (ordenColumna) {
      case 'fecha': {
        const fechaA = obtenerFechaRegistro(a) ? new Date(obtenerFechaRegistro(a)!).getTime() : 0;
        const fechaB = obtenerFechaRegistro(b) ? new Date(obtenerFechaRegistro(b)!).getTime() : 0;
        comparacion = fechaA - fechaB;
        break;
      }
      case 'stake':
        comparacion = (a.stake || 0) - (b.stake || 0);
        break;
      case 'ganancia':
        comparacion = (a.ganancia || 0) - (b.ganancia || 0);
        break;
      case 'cuota': {
        const cuotaA = a.tipo_apuesta === 'COMBINADA' ? a.cuota_total : a.cuota;
        const cuotaB = b.tipo_apuesta === 'COMBINADA' ? b.cuota_total : b.cuota;
        comparacion = (cuotaA || 0) - (cuotaB || 0);
        break;
      }
    }

    return direccionOrden === 'desc' ? -comparacion : comparacion;
  });

  const cambiarOrden = (columna: OrdenColumna) => {
    if (ordenColumna === columna) {
      setDireccionOrden((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setOrdenColumna(columna);
      setDireccionOrden('desc');
    }
  };

  const IconoOrden = ({ columna }: { columna: OrdenColumna }) => {
    if (ordenColumna !== columna) return null;
    return direccionOrden === 'desc' ? (
      <ChevronDown className="w-3 h-3 inline ml-1" />
    ) : (
      <ChevronUp className="w-3 h-3 inline ml-1" />
    );
  };

  if (estado === 'cargando') {
    return (
      <div className="tarjeta p-8 text-center">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-neon-cyan/20 rounded w-3/4 mx-auto" />
          <div className="h-4 bg-neon-cyan/10 rounded w-1/2 mx-auto" />
        </div>
        <p className="text-texto-secundario mt-4">Cargando apuestas...</p>
      </div>
    );
  }

  if (estado === 'error') {
    return (
      <div className="tarjeta p-6 text-center text-neon-rojo border border-neon-rojo/30">
        No se pudieron cargar las apuestas.
      </div>
    );
  }

  if (apuestas.length === 0) {
    return (
      <div className="tarjeta p-8 text-center text-texto-secundario">
        {mensajeVacio}
      </div>
    );
  }

  return (
    <div className="tarjeta overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px]">
          <thead className="bg-futurista-medio/50 border-b border-neon-cyan/20">
            <tr>
              <th
                className="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-texto-terciario cursor-pointer hover:text-neon-cyan transition-colors"
                onClick={() => cambiarOrden('fecha')}
              >
                Fecha <IconoOrden columna="fecha" />
              </th>
              <th className="px-3 py-3 pr-1 text-left text-xs font-semibold uppercase tracking-wider text-texto-terciario">
                Partido
              </th>
              <th className="px-2 py-3 pl-1 text-center text-xs font-semibold uppercase tracking-wider text-texto-terciario">
                Mdo
              </th>
              <th className="px-2 py-3 text-center text-xs font-semibold uppercase tracking-wider text-texto-terciario">
                Lado
              </th>
              <th className="px-2 py-3 text-right text-xs font-semibold uppercase tracking-wider text-texto-terciario">
                Línea
              </th>
              <th
                className="px-2 py-3 text-right text-xs font-semibold uppercase tracking-wider text-texto-terciario cursor-pointer hover:text-neon-cyan transition-colors"
                onClick={() => cambiarOrden('cuota')}
              >
                Cuota <IconoOrden columna="cuota" />
              </th>
              <th
                className="px-3 py-3 text-right text-xs font-semibold uppercase tracking-wider text-texto-terciario cursor-pointer hover:text-neon-cyan transition-colors"
                onClick={() => cambiarOrden('stake')}
              >
                Stake <IconoOrden columna="stake" />
              </th>
              <th className="px-2 py-3 text-right text-xs font-semibold uppercase tracking-wider text-texto-terciario">
                Prob
              </th>
              <th
                className="px-3 py-3 text-right text-xs font-semibold uppercase tracking-wider text-texto-terciario cursor-pointer hover:text-neon-cyan transition-colors"
                onClick={() => cambiarOrden('ganancia')}
              >
                Ganancia <IconoOrden columna="ganancia" />
              </th>
              <th className="px-2 py-3 text-center text-xs font-semibold uppercase tracking-wider text-texto-terciario">
                Conf
              </th>
              <th className="px-2 py-3 text-center text-xs font-semibold uppercase tracking-wider text-texto-terciario">
                EV
              </th>
              <th className="px-3 py-3 text-center text-xs font-semibold uppercase tracking-wider text-texto-terciario">
                Estado
              </th>
              <th className="px-2 py-3 text-center text-xs font-semibold uppercase tracking-wider text-texto-terciario">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neon-cyan/10">
            {apuestasOrdenadas.map((apuesta) => {
              const estiloEstado =
                estilosEstado[apuesta.resultado] || estilosEstado.PENDIENTE;
              const estiloConfianza =
                estilosConfianza[apuesta.confianza_sistema || ''] ||
                'text-texto-secundario';
              const esPendiente = apuesta.resultado === 'PENDIENTE';
              const esCombinada = apuesta.tipo_apuesta === 'COMBINADA';
              const cuotaMostrar = esCombinada ? apuesta.cuota_total : apuesta.cuota;
              const fechaRegistro = obtenerFechaRegistro(apuesta);

              return (
                <Fragment key={apuesta.id}>
                  <tr className={`transition-colors ${estiloEstado.fila}`}>
                    <td className="px-3 py-2.5 text-sm text-texto-secundario whitespace-nowrap">
                      {formatearFechaCorta(fechaRegistro)}
                    </td>
                    <td className="px-3 py-2.5 pr-1">
                      {esCombinada ? (
                        <div className="flex flex-col gap-1">
                          <div className="flex items-center gap-2">
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full border border-neon-cyan/30 bg-neon-cyan/10 text-[10px] uppercase tracking-widest text-neon-cyan">
                              Combinada
                            </span>
                            <span className="text-xs text-texto-terciario">
                              {apuesta.n_selecciones ?? 0} selecciones
                            </span>
                          </div>
                          <span className="text-sm font-medium text-texto-principal">
                            {apuesta.selecciones?.length
                              ? `${formatearEquipo(apuesta.selecciones[0].equipo_local)} vs ${formatearEquipo(apuesta.selecciones[0].equipo_visitante)}`
                              : 'Apuesta combinada'}
                          </span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1">
                          <span
                            className="text-sm font-medium text-texto-principal"
                            title={apuesta.equipo_local ?? undefined}
                          >
                            {formatearEquipo(apuesta.equipo_local)}
                          </span>
                          <span className="text-xs text-texto-terciario">vs</span>
                          <span
                            className="text-sm font-medium text-texto-principal"
                            title={apuesta.equipo_visitante ?? undefined}
                          >
                            {formatearEquipo(apuesta.equipo_visitante)}
                          </span>
                        </div>
                      )}
                    </td>
                    <td className="px-2 py-2.5 pl-1 text-center">
                      <span className={`text-xs font-mono ${esCombinada ? 'text-neon-magenta' : 'text-neon-cyan'}`}>
                        {esCombinada
                          ? 'CB'
                          : apuesta.mercado === 'COMPLETO'
                            ? 'FG'
                            : apuesta.mercado ?? '—'}
                      </span>
                    </td>
                    <td className="px-2 py-2.5 text-center">
                      <span
                        className={`text-xs font-semibold ${
                          apuesta.lado === 'OVER'
                            ? 'text-neon-verde'
                            : apuesta.lado === 'UNDER'
                              ? 'text-neon-magenta'
                              : 'text-texto-terciario'
                        }`}
                      >
                        {apuesta.lado === 'OVER'
                          ? 'O'
                          : apuesta.lado === 'UNDER'
                            ? 'U'
                            : '—'}
                      </span>
                    </td>
                    <td className="px-2 py-2.5 text-right">
                      <span className="text-sm font-mono text-texto-principal">
                        {formatearLinea(apuesta.linea)}
                      </span>
                    </td>
                    <td className="px-2 py-2.5 text-right">
                      <span className="text-sm font-mono text-texto-secundario">
                        {cuotaMostrar !== null && cuotaMostrar !== undefined
                          ? cuotaMostrar.toFixed(2)
                          : '—'}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      <span className="text-sm font-mono text-texto-principal">
                        {formatearDinero(apuesta.stake)}
                      </span>
                    </td>
                    <td className="px-2 py-2.5 text-right">
                      <span className="text-sm font-mono text-texto-secundario">
                        {formatearProbabilidad(apuesta.probabilidad_sistema)}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      <span
                        className={`text-sm font-mono font-semibold ${
                          apuesta.ganancia === null || apuesta.ganancia === undefined
                            ? 'text-texto-terciario'
                            : apuesta.ganancia > 0
                              ? 'text-neon-verde'
                              : apuesta.ganancia < 0
                                ? 'text-neon-rojo'
                                : 'text-texto-secundario'
                        }`}
                      >
                        {formatearDinero(apuesta.ganancia, true)}
                      </span>
                    </td>
                    <td className="px-2 py-2.5 text-center">
                      <span className={`text-xs font-semibold ${estiloConfianza}`}>
                        {apuesta.confianza_sistema?.[0] || '—'}
                      </span>
                    </td>
                    <td className="px-2 py-2.5 text-center">
                      <span
                        className={`text-xs font-mono ${
                          (apuesta.valor_esperado || 0) > 0
                            ? 'text-neon-verde'
                            : (apuesta.valor_esperado || 0) < 0
                              ? 'text-neon-rojo'
                              : 'text-texto-terciario'
                        }`}
                      >
                        {formatearPorcentaje(apuesta.valor_esperado ?? null)}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <span
                        className={`inline-flex px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-full border ${estiloEstado.badge}`}
                      >
                        {apuesta.resultado === 'PENDIENTE'
                          ? 'PEND'
                          : apuesta.resultado === 'GANADA'
                            ? 'WIN'
                            : apuesta.resultado === 'PERDIDA'
                              ? 'LOSS'
                              : apuesta.resultado}
                      </span>
                    </td>
                    <td className="px-2 py-2.5">
                      <div className="flex items-center justify-center gap-1">
                        {esCombinada && apuesta.selecciones?.length ? (
                          <span className="p-1.5 text-texto-terciario">
                            <Eye className="w-4 h-4" />
                          </span>
                        ) : null}
                        {!esCombinada && esPendiente && (
                          <button
                            onClick={() => onResolver(apuesta)}
                            className="p-1.5 rounded hover:bg-neon-verde/10 text-texto-terciario hover:text-neon-verde transition-colors"
                            title="Resolver"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => onEliminar(apuesta)}
                          className="p-1.5 rounded hover:bg-neon-rojo/10 text-texto-terciario hover:text-neon-rojo transition-colors"
                          title="Eliminar"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                  {esCombinada && apuesta.selecciones?.length ? (
                    <tr className="bg-neon-cyan/5">
                      <td colSpan={13} className="px-4 py-3">
                        <div className="rounded-lg border border-neon-cyan/20 bg-futurista-oscuro/40 p-3">
                          <div className="flex flex-wrap items-center gap-2 text-xs text-texto-terciario">
                            <span className="uppercase tracking-widest text-neon-cyan">Detalle combinada</span>
                            <span>Cuota total {cuotaMostrar?.toFixed(2) ?? '—'}</span>
                            <span>Stake {formatearDinero(apuesta.stake)}</span>
                            <span>Selecciones {apuesta.n_selecciones ?? apuesta.selecciones.length}</span>
                          </div>
                          <div className="mt-2 grid gap-2 md:grid-cols-2">
                            {apuesta.selecciones.map((seleccion) => (
                              <div
                                key={seleccion.id}
                                className="flex items-center justify-between rounded-md border border-neon-cyan/10 bg-futurista-medio/30 px-3 py-2"
                              >
                                <div>
                                  <p className="text-xs text-texto-terciario">
                                    {formatearEquipo(seleccion.equipo_local)} vs {formatearEquipo(seleccion.equipo_visitante)}
                                  </p>
                                  <p className="text-sm font-medium text-texto-principal">
                                    {seleccion.mercado === 'COMPLETO' ? 'FG' : seleccion.mercado} · {seleccion.lado === 'OVER' ? 'OVER' : 'UNDER'} {formatearLinea(seleccion.linea)}
                                  </p>
                                </div>
                                <div className="text-right">
                                  <p className="text-xs text-texto-terciario">Cuota</p>
                                  <p className="text-sm font-mono text-texto-secundario">
                                    {formatearCuota(seleccion.cuota)}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="px-4 py-3 bg-futurista-medio/30 border-t border-neon-cyan/10 flex items-center justify-between text-xs text-texto-terciario">
        <span>Mostrando {apuestas.length} apuestas</span>
        <span>Click en encabezados para ordenar</span>
      </div>
    </div>
  );
}
