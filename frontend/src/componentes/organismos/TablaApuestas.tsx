/**
 * TablaApuestas.tsx — Tabla profesional de apuestas para bitácora
 *
 * Diseño compacto estilo libro de trading con:
 * - Columnas ordenables
 * - Colores por estado
 * - Acciones rápidas
 * - Responsive con scroll horizontal
 */

import { useState } from 'react';
import { ChevronUp, ChevronDown, Trash2, CheckCircle, Eye } from 'lucide-react';
import { Apuesta } from '../../tipos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsTablaApuestas {
  apuestas: Apuesta[];
  estado: 'idle' | 'cargando' | 'exito' | 'error';
  mensajeVacio: string;
  onResolver: (apuesta: Apuesta) => void;
  onEliminar: (apuesta: Apuesta) => void;
  onVerDetalle?: (apuesta: Apuesta) => void;
}

type OrdenColumna = 'fecha' | 'stake' | 'ganancia' | 'cuota';
type DireccionOrden = 'asc' | 'desc';

// ══════════════════════════════════════════════════════════════
// ESTILOS POR ESTADO
// ══════════════════════════════════════════════════════════════

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

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

function formatearFechaCorta(fecha: string | Date | null | undefined): string {
  if (!fecha) return '—';
  const d = typeof fecha === 'string' ? new Date(fecha) : fecha;
  return d.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  });
}

function formatearDinero(valor: number | null, mostrarSigno = false): string {
  if (valor === null || valor === undefined) return '—';
  const signo = mostrarSigno && valor > 0 ? '+' : '';
  return `${signo}$${valor.toFixed(2)}`;
}

function formatearPorcentaje(valor: number | null): string {
  if (valor === null || valor === undefined) return '—';
  const signo = valor > 0 ? '+' : '';
  return `${signo}${(valor * 100).toFixed(1)}%`;
}

function formatearEquipo(nombre: string): string {
  return nombre.toUpperCase();
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

export function TablaApuestas({
  apuestas,
  estado,
  mensajeVacio,
  onResolver,
  onEliminar,
  onVerDetalle,
}: PropsTablaApuestas) {
  const [ordenColumna, setOrdenColumna] = useState<OrdenColumna>('fecha');
  const [direccionOrden, setDireccionOrden] = useState<DireccionOrden>('desc');

  const apuestasOrdenadas = [...apuestas].sort((a, b) => {
    let comparacion = 0;

    switch (ordenColumna) {
      case 'fecha': {
        const fechaA = a.fecha_partido ? new Date(a.fecha_partido).getTime() : 0;
        const fechaB = b.fecha_partido ? new Date(b.fecha_partido).getTime() : 0;
        comparacion = fechaA - fechaB;
        break;
      }
      case 'stake':
        comparacion = (a.stake || 0) - (b.stake || 0);
        break;
      case 'ganancia':
        comparacion = (a.ganancia || 0) - (b.ganancia || 0);
        break;
      case 'cuota':
        comparacion = (a.cuota || 0) - (b.cuota || 0);
        break;
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
        <table className="w-full min-w-[900px]">
          <thead className="bg-futurista-medio/50 border-b border-neon-cyan/20">
            <tr>
              <th
                className="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-texto-terciario cursor-pointer hover:text-neon-cyan transition-colors"
                onClick={() => cambiarOrden('fecha')}
              >
                Fecha <IconoOrden columna="fecha" />
              </th>
              <th className="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-texto-terciario">
                Partido
              </th>
              <th className="px-2 py-3 text-center text-xs font-semibold uppercase tracking-wider text-texto-terciario">
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

              return (
                <tr
                  key={apuesta.id}
                  className={`transition-colors ${estiloEstado.fila}`}
                >
                  <td className="px-3 py-2.5 text-sm text-texto-secundario whitespace-nowrap">
                    {formatearFechaCorta(apuesta.fecha_partido)}
                  </td>

                  <td className="px-3 py-2.5">
                    <div className="flex items-center gap-1">
                      <span
                        className="text-sm font-medium text-texto-principal"
                        title={apuesta.equipo_local}
                      >
                        {formatearEquipo(apuesta.equipo_local)}
                      </span>
                      <span className="text-xs text-texto-terciario">vs</span>
                      <span
                        className="text-sm font-medium text-texto-principal"
                        title={apuesta.equipo_visitante}
                      >
                        {formatearEquipo(apuesta.equipo_visitante)}
                      </span>
                    </div>
                  </td>

                  <td className="px-2 py-2.5 text-center">
                    <span className="text-xs font-mono text-neon-cyan">
                      {apuesta.mercado === 'COMPLETO' ? 'FG' : apuesta.mercado}
                    </span>
                  </td>

                  <td className="px-2 py-2.5 text-center">
                    <span
                      className={`text-xs font-semibold ${
                        apuesta.lado === 'OVER'
                          ? 'text-neon-verde'
                          : 'text-neon-magenta'
                      }`}
                    >
                      {apuesta.lado === 'OVER' ? 'O' : 'U'}
                    </span>
                  </td>

                  <td className="px-2 py-2.5 text-right">
                    <span className="text-sm font-mono text-texto-principal">
                      {apuesta.linea?.toFixed(1)}
                    </span>
                  </td>

                  <td className="px-2 py-2.5 text-right">
                    <span className="text-sm font-mono text-texto-secundario">
                      {apuesta.cuota?.toFixed(2)}
                    </span>
                  </td>

                  <td className="px-3 py-2.5 text-right">
                    <span className="text-sm font-mono text-texto-principal">
                      {formatearDinero(apuesta.stake)}
                    </span>
                  </td>

                  <td className="px-3 py-2.5 text-right">
                    <span
                      className={`text-sm font-mono font-semibold ${
                        apuesta.ganancia === null
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
                      {onVerDetalle && (
                        <button
                          onClick={() => onVerDetalle(apuesta)}
                          className="p-1.5 rounded hover:bg-neon-cyan/10 text-texto-terciario hover:text-neon-cyan transition-colors"
                          title="Ver detalle"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      )}
                      {esPendiente && (
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
