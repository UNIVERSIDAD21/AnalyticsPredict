/**
 * TablaEstadisticasEquipos.tsx — Tabla interactiva de estadísticas de equipos
 */

import { useMemo, useState } from 'react';
import { ArrowUpDown, Search, Calendar } from 'lucide-react';
import { EstadisticasEquipo, Equipo, TemporadaDisponible } from '../../tipos';
import { buscarEquipo } from '../../servicios';

interface PropsTablaEstadisticasEquipos {
  equipos: EstadisticasEquipo[];
  equiposCatalogo: Equipo[];
  fechaActualizacion: string;
  temporadasDisponibles: TemporadaDisponible[];
  temporadaActual: string | null;
  onCambiarTemporada: (temporadaId: string | null) => void;
  onSeleccionarEquipo: (equipoId: string) => void;
}

type Orden = 'asc' | 'desc';

interface Columna {
  id: string;
  etiqueta: string;
  descripcion: string;
  obtenerValor: (equipo: EstadisticasEquipo) => string | number;
  formato?: (equipo: EstadisticasEquipo) => string;
}

const formatoPct = (valor: number) => {
  const texto = valor.toFixed(3);
  return texto.startsWith('0') ? texto.slice(1) : texto;
};

export function TablaEstadisticasEquipos({
  equipos,
  equiposCatalogo,
  fechaActualizacion,
  temporadasDisponibles,
  temporadaActual,
  onCambiarTemporada,
  onSeleccionarEquipo,
}: PropsTablaEstadisticasEquipos) {
  const [busqueda, setBusqueda] = useState('');
  const [conferencia, setConferencia] = useState('Todas');
  const [orden, setOrden] = useState<{ columna: string; direccion: Orden }>({
    columna: 'equipo',
    direccion: 'asc',
  });

  const columnas: Columna[] = [
    {
      id: 'equipo',
      etiqueta: 'Equipo',
      descripcion: 'Nombre del equipo listado en la tabla.',
      obtenerValor: (e) => e.nombre,
    },
    {
      id: 'racha',
      etiqueta: 'Racha',
      descripcion: 'Últimos resultados consecutivos del equipo.',
      obtenerValor: (e) => e.racha.join('-'),
    },
    {
      id: 'ppg_q1',
      etiqueta: 'PPG Q1',
      descripcion: 'Puntos por partido anotados en el 1er cuarto.',
      obtenerValor: (e) => e.promedios.anotados.q1,
    },
    {
      id: 'ppg_q2',
      etiqueta: 'PPG Q2',
      descripcion: 'Puntos por partido anotados en el 2do cuarto.',
      obtenerValor: (e) => e.promedios.anotados.q2,
    },
    {
      id: 'ppg_q3',
      etiqueta: 'PPG Q3',
      descripcion: 'Puntos por partido anotados en el 3er cuarto.',
      obtenerValor: (e) => e.promedios.anotados.q3,
    },
    {
      id: 'ppg_q4',
      etiqueta: 'PPG Q4',
      descripcion: 'Puntos por partido anotados en el 4to cuarto.',
      obtenerValor: (e) => e.promedios.anotados.q4,
    },
    {
      id: 'ppg_total',
      etiqueta: 'PPG Total',
      descripcion: 'Promedio total de puntos anotados por partido.',
      obtenerValor: (e) => e.promedios.anotados.total,
    },
    {
      id: 'opp_q1',
      etiqueta: 'OPP Q1',
      descripcion: 'Puntos recibidos por partido en el 1er cuarto.',
      obtenerValor: (e) => e.promedios.recibidos.q1,
    },
    {
      id: 'opp_q2',
      etiqueta: 'OPP Q2',
      descripcion: 'Puntos recibidos por partido en el 2do cuarto.',
      obtenerValor: (e) => e.promedios.recibidos.q2,
    },
    {
      id: 'opp_q3',
      etiqueta: 'OPP Q3',
      descripcion: 'Puntos recibidos por partido en el 3er cuarto.',
      obtenerValor: (e) => e.promedios.recibidos.q3,
    },
    {
      id: 'opp_q4',
      etiqueta: 'OPP Q4',
      descripcion: 'Puntos recibidos por partido en el 4to cuarto.',
      obtenerValor: (e) => e.promedios.recibidos.q4,
    },
    {
      id: 'opp_total',
      etiqueta: 'OPP Total',
      descripcion: 'Promedio total de puntos recibidos por partido.',
      obtenerValor: (e) => e.promedios.recibidos.total,
    },
    {
      id: 'over_q1',
      etiqueta: 'Over % Q1',
      descripcion: 'Porcentaje de overs en el 1er cuarto.',
      obtenerValor: (e) => e.tendencias_over.q1,
      formato: (e) => formatoPct(e.tendencias_over.q1),
    },
    {
      id: 'over_total',
      etiqueta: 'Over % Total',
      descripcion: 'Porcentaje de overs en el total del partido.',
      obtenerValor: (e) => e.tendencias_over.total,
      formato: (e) => formatoPct(e.tendencias_over.total),
    },
    {
      id: 'linea',
      etiqueta: 'Línea Promedio',
      descripcion: 'Media de la línea total publicada para el equipo.',
      obtenerValor: (e) => e.linea_promedio,
    },
    {
      id: 'ppg_casa',
      etiqueta: 'PPG Casa',
      descripcion: 'Puntos por partido anotados jugando como local.',
      obtenerValor: (e) => e.local.ppg,
    },
    {
      id: 'ppg_fuera',
      etiqueta: 'PPG Fuera',
      descripcion: 'Puntos por partido anotados jugando como visitante.',
      obtenerValor: (e) => e.visitante.ppg,
    },
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
    onSeleccionarEquipo(equipoCatalogo.id);
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
            <Calendar className="w-4 h-4 text-texto-terciario absolute left-3 top-3" />
            <select
              value={temporadaActual || ''}
              onChange={(event) => onCambiarTemporada(event.target.value || null)}
              className="pl-9 pr-3 py-2 text-sm rounded-md bg-futurista-oscuro/60 border border-neon-cyan/20 text-texto-principal min-w-[160px]"
            >
              {temporadasDisponibles.map((temporada) => (
                <option key={temporada.id} value={temporada.id}>
                  {temporada.nombre}
                </option>
              ))}
            </select>
          </div>
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
                  <div className="group relative inline-flex">
                    <button
                      type="button"
                      className="flex items-center gap-1 hover:text-neon-cyan"
                      onClick={() => alternarOrden(columna.id)}
                    >
                      {columna.etiqueta}
                      <ArrowUpDown size={12} />
                    </button>
                    <span className="pointer-events-none absolute left-0 bottom-full mb-2 w-48 rounded-md bg-futurista-oscuro/95 px-2 py-1 text-[10px] normal-case text-texto-principal opacity-0 shadow-lg transition-opacity duration-200 group-hover:opacity-100">
                      {columna.descripcion}
                    </span>
                  </div>
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
