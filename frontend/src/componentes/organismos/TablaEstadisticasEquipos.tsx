/**
 * TablaEstadisticasEquipos.tsx — Tabla interactiva de estadísticas de equipos
 */

import { useMemo, useState } from 'react';
import { ArrowUpDown, Search } from 'lucide-react';
import { EstadisticasEquipo, Equipo } from '../../tipos';
import { buscarEquipo } from '../../servicios';

interface PropsTablaEstadisticasEquipos {
  equipos: EstadisticasEquipo[];
  equiposCatalogo: Equipo[];
  fechaActualizacion: string;
}

type Orden = 'asc' | 'desc';

interface Columna {
  id: string;
  etiqueta: string;
  obtenerValor: (equipo: EstadisticasEquipo) => string | number;
  formato?: (equipo: EstadisticasEquipo) => string;
}

const formatoPct = (valor: number) => `${(valor * 100).toFixed(1)}%`;

export function TablaEstadisticasEquipos({
  equipos,
  equiposCatalogo,
  fechaActualizacion,
}: PropsTablaEstadisticasEquipos) {
  const [busqueda, setBusqueda] = useState('');
  const [conferencia, setConferencia] = useState('Todas');
  const [orden, setOrden] = useState<{ columna: string; direccion: Orden }>({
    columna: 'pct',
    direccion: 'desc',
  });

  const columnas: Columna[] = [
    { id: 'equipo', etiqueta: 'Equipo', obtenerValor: (e) => e.nombre },
    { id: 'conf', etiqueta: 'Conf', obtenerValor: (e) => e.conferencia },
    { id: 'pos', etiqueta: 'Pos', obtenerValor: (e) => e.posicion },
    {
      id: 'record',
      etiqueta: 'Record',
      obtenerValor: (e) => `${e.record.victorias}-${e.record.derrotas}`,
    },
    {
      id: 'pct',
      etiqueta: '% Victorias',
      obtenerValor: (e) =>
        e.record.victorias / Math.max(1, e.record.victorias + e.record.derrotas),
      formato: (e) =>
        formatoPct(e.record.victorias / Math.max(1, e.record.victorias + e.record.derrotas)),
    },
    { id: 'racha', etiqueta: 'Racha', obtenerValor: (e) => e.racha.join('-') },
    { id: 'ppg_q1', etiqueta: 'PPG Q1', obtenerValor: (e) => e.promedios.anotados.q1 },
    { id: 'ppg_q2', etiqueta: 'PPG Q2', obtenerValor: (e) => e.promedios.anotados.q2 },
    { id: 'ppg_q3', etiqueta: 'PPG Q3', obtenerValor: (e) => e.promedios.anotados.q3 },
    { id: 'ppg_q4', etiqueta: 'PPG Q4', obtenerValor: (e) => e.promedios.anotados.q4 },
    { id: 'ppg_total', etiqueta: 'PPG Total', obtenerValor: (e) => e.promedios.anotados.total },
    { id: 'opp_q1', etiqueta: 'OPP Q1', obtenerValor: (e) => e.promedios.recibidos.q1 },
    { id: 'opp_q2', etiqueta: 'OPP Q2', obtenerValor: (e) => e.promedios.recibidos.q2 },
    { id: 'opp_q3', etiqueta: 'OPP Q3', obtenerValor: (e) => e.promedios.recibidos.q3 },
    { id: 'opp_q4', etiqueta: 'OPP Q4', obtenerValor: (e) => e.promedios.recibidos.q4 },
    { id: 'opp_total', etiqueta: 'OPP Total', obtenerValor: (e) => e.promedios.recibidos.total },
    {
      id: 'over_q1',
      etiqueta: 'Over % Q1',
      obtenerValor: (e) => e.tendencias_over.q1,
      formato: (e) => formatoPct(e.tendencias_over.q1),
    },
    {
      id: 'over_total',
      etiqueta: 'Over % Total',
      obtenerValor: (e) => e.tendencias_over.total,
      formato: (e) => formatoPct(e.tendencias_over.total),
    },
    {
      id: 'linea',
      etiqueta: 'Línea Promedio',
      obtenerValor: (e) => e.linea_promedio,
    },
    {
      id: 'record_casa',
      etiqueta: 'Record Casa',
      obtenerValor: (e) => `${e.local.victorias}-${e.local.derrotas}`,
    },
    {
      id: 'record_fuera',
      etiqueta: 'Record Fuera',
      obtenerValor: (e) => `${e.visitante.victorias}-${e.visitante.derrotas}`,
    },
    { id: 'ppg_casa', etiqueta: 'PPG Casa', obtenerValor: (e) => e.local.ppg },
    { id: 'ppg_fuera', etiqueta: 'PPG Fuera', obtenerValor: (e) => e.visitante.ppg },
  ];

  const equiposFiltrados = useMemo(() => {
    const termino = busqueda.trim().toLowerCase();
    return equipos
      .filter((equipo) =>
        conferencia === 'Todas' ? true : equipo.conferencia === conferencia
      )
      .filter((equipo) =>
        termino
          ? equipo.nombre.toLowerCase().includes(termino) ||
            equipo.abreviatura.toLowerCase().includes(termino)
          : true
      );
  }, [equipos, conferencia, busqueda]);

  const equiposOrdenados = useMemo(() => {
    const columna = columnas.find((col) => col.id === orden.columna);
    if (!columna) return equiposFiltrados;

    const ordenados = [...equiposFiltrados].sort((a, b) => {
      const va = columna.obtenerValor(a);
      const vb = columna.obtenerValor(b);
      if (typeof va === 'number' && typeof vb === 'number') {
        return orden.direccion === 'asc' ? va - vb : vb - va;
      }
      return orden.direccion === 'asc'
        ? String(va).localeCompare(String(vb))
        : String(vb).localeCompare(String(va));
    });
    return ordenados;
  }, [equiposFiltrados, columnas, orden]);

  const alternarOrden = (columnaId: string) => {
    setOrden((prev) => {
      if (prev.columna === columnaId) {
        return { columna: columnaId, direccion: prev.direccion === 'asc' ? 'desc' : 'asc' };
      }
      return { columna: columnaId, direccion: 'desc' };
    });
  };

  const abrirDetalleEquipo = (equipo: EstadisticasEquipo) => {
    const equipoCatalogo =
      buscarEquipo(equiposCatalogo, equipo.nombre) ||
      buscarEquipo(equiposCatalogo, equipo.abreviatura);
    if (!equipoCatalogo) {
      return;
    }
    window.open(`/equipo/${equipoCatalogo.id}/historial`, '_blank');
  };

  return (
    <div className="tarjeta space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-xl font-futurista text-texto-principal">
            Estadísticas de Equipos
          </h2>
          <p className="text-xs text-texto-terciario">
            Última actualización: {fechaActualizacion || 'No disponible'}
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-texto-terciario absolute left-3 top-3" />
            <input
              value={busqueda}
              onChange={(event) => setBusqueda(event.target.value)}
              placeholder="Buscar equipo..."
              className="pl-9 pr-3 py-2 text-sm rounded-md bg-futurista-oscuro/60 border border-neon-cyan/20 text-texto-principal"
            />
          </div>
          <select
            value={conferencia}
            onChange={(event) => setConferencia(event.target.value)}
            className="px-3 py-2 text-sm rounded-md bg-futurista-oscuro/60 border border-neon-cyan/20 text-texto-principal"
          >
            <option value="Todas">Todas</option>
            <option value="Este">Este</option>
            <option value="Oeste">Oeste</option>
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-xs text-texto-secundario border-collapse">
          <thead className="text-[11px] uppercase text-texto-terciario">
            <tr>
              {columnas.map((columna) => (
                <th key={columna.id} className="p-2 text-left">
                  <button
                    type="button"
                    className="flex items-center gap-1 hover:text-neon-cyan"
                    onClick={() => alternarOrden(columna.id)}
                  >
                    {columna.etiqueta}
                    <ArrowUpDown size={12} />
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {equiposOrdenados.map((equipo) => (
              <tr
                key={equipo.nombre}
                className="border-t border-neon-cyan/10 hover:bg-futurista-oscuro/50 cursor-pointer"
                onClick={() => abrirDetalleEquipo(equipo)}
              >
                {columnas.map((columna) => (
                  <td key={columna.id} className="p-2 whitespace-nowrap">
                    {columna.formato
                      ? columna.formato(equipo)
                      : typeof columna.obtenerValor(equipo) === 'number'
                        ? Number(columna.obtenerValor(equipo)).toFixed(1)
                        : String(columna.obtenerValor(equipo))}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
