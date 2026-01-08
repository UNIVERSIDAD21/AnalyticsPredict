/**
 * TablaEstadisticasEquipos.tsx – Tabla interactiva de estadísticas de equipos
 */

import { useMemo, useState } from 'react';
import { ArrowUpDown, Search, Calendar, TrendingUp, TrendingDown, Info } from 'lucide-react';
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
  colorear?: (valor: number) => string;
}

const formatoPct = (valor: number): string => {
  const texto = valor.toFixed(3);
  return texto.startsWith('0') ? texto.slice(1) : texto;
};

const obtenerColorPorcentaje = (valor: number): string => {
  if (valor >= 0.600) return 'text-green-400';
  if (valor >= 0.500) return 'text-yellow-400';
  return 'text-red-400';
};

const obtenerColorPPG = (valor: number): string => {
  if (valor >= 30) return 'text-green-400';
  if (valor >= 25) return 'text-cyan-400';
  return 'text-texto-secundario';
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
  const [columnaHover, setColumnaHover] = useState<string | null>(null);
  const [orden, setOrden] = useState<{ columna: string; direccion: Orden }>({
    columna: 'equipo',
    direccion: 'asc',
  });

  const columnas: Columna[] = [
    {
      id: 'equipo',
      etiqueta: 'Equipo',
      descripcion: 'Nombre del equipo listado en la tabla',
      obtenerValor: (e) => e.nombre,
    },
    {
      id: 'racha',
      etiqueta: 'Racha',
      descripcion: 'Últimos resultados consecutivos del equipo (W = Victoria, L = Derrota)',
      obtenerValor: (e) => e.racha.join('-'),
    },
    {
      id: 'ppg_q1',
      etiqueta: 'PPG Q1',
      descripcion: 'Puntos por partido anotados en el primer cuarto',
      obtenerValor: (e) => e.promedios.anotados.q1,
      colorear: obtenerColorPPG,
    },
    {
      id: 'ppg_q2',
      etiqueta: 'PPG Q2',
      descripcion: 'Puntos por partido anotados en el segundo cuarto',
      obtenerValor: (e) => e.promedios.anotados.q2,
      colorear: obtenerColorPPG,
    },
    {
      id: 'ppg_q3',
      etiqueta: 'PPG Q3',
      descripcion: 'Puntos por partido anotados en el tercer cuarto',
      obtenerValor: (e) => e.promedios.anotados.q3,
      colorear: obtenerColorPPG,
    },
    {
      id: 'ppg_q4',
      etiqueta: 'PPG Q4',
      descripcion: 'Puntos por partido anotados en el cuarto cuarto',
      obtenerValor: (e) => e.promedios.anotados.q4,
      colorear: obtenerColorPPG,
    },
    {
      id: 'ppg_total',
      etiqueta: 'PPG Total',
      descripcion: 'Promedio total de puntos anotados por partido',
      obtenerValor: (e) => e.promedios.anotados.total,
      colorear: (v) => v >= 115 ? 'text-green-400 font-bold' : v >= 110 ? 'text-cyan-400' : 'text-texto-secundario',
    },
    {
      id: 'opp_q1',
      etiqueta: 'OPP Q1',
      descripcion: 'Puntos recibidos por partido en el primer cuarto',
      obtenerValor: (e) => e.promedios.recibidos.q1,
    },
    {
      id: 'opp_q2',
      etiqueta: 'OPP Q2',
      descripcion: 'Puntos recibidos por partido en el segundo cuarto',
      obtenerValor: (e) => e.promedios.recibidos.q2,
    },
    {
      id: 'opp_q3',
      etiqueta: 'OPP Q3',
      descripcion: 'Puntos recibidos por partido en el tercer cuarto',
      obtenerValor: (e) => e.promedios.recibidos.q3,
    },
    {
      id: 'opp_q4',
      etiqueta: 'OPP Q4',
      descripcion: 'Puntos recibidos por partido en el cuarto cuarto',
      obtenerValor: (e) => e.promedios.recibidos.q4,
    },
    {
      id: 'opp_total',
      etiqueta: 'OPP Total',
      descripcion: 'Promedio total de puntos recibidos por partido',
      obtenerValor: (e) => e.promedios.recibidos.total,
    },
    {
      id: 'linea',
      etiqueta: 'Línea Promedio',
      descripcion: 'Media de la línea total de puntos publicada para el equipo',
      obtenerValor: (e) => e.linea_promedio,
    },
    {
      id: 'ppg_casa',
      etiqueta: 'PPG Casa',
      descripcion: 'Puntos por partido anotados cuando juega como local',
      obtenerValor: (e) => e.local.ppg,
      colorear: obtenerColorPPG,
    },
    {
      id: 'ppg_fuera',
      etiqueta: 'PPG Fuera',
      descripcion: 'Puntos por partido anotados cuando juega como visitante',
      obtenerValor: (e) => e.visitante.ppg,
      colorear: obtenerColorPPG,
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
  }, [equiposFiltrados, orden]);

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

  const obtenerValorFormateado = (columna: Columna, equipo: EstadisticasEquipo): string => {
    if (columna.formato) {
      return columna.formato(equipo);
    }
    const valor = columna.obtenerValor(equipo);
    if (typeof valor === 'number') {
      return valor.toFixed(1);
    }
    return String(valor);
  };

  const obtenerClaseColor = (columna: Columna, equipo: EstadisticasEquipo): string => {
    if (!columna.colorear) return '';
    const valor = columna.obtenerValor(equipo);
    if (typeof valor === 'number') {
      return columna.colorear(valor);
    }
    return '';
  };

  return (
    <div className="relative min-h-screen">
      {/* Efectos de fondo futurista */}
      <div className="fixed inset-0 bg-gradient-to-br from-cyan-500/5 via-transparent to-purple-500/5 pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,rgba(0,255,255,0.15),transparent_50%)] pointer-events-none" />
      
      <div className="relative max-w-[98vw] mx-auto p-4">
        <div className="backdrop-blur-xl bg-slate-900/90 border-2 border-cyan-400/30 rounded-2xl shadow-2xl shadow-cyan-500/20 overflow-hidden">
          
          {/* Header principal */}
          <div className="relative bg-gradient-to-r from-cyan-500/20 via-purple-500/20 to-cyan-500/20 border-b-2 border-cyan-400/30 p-6">
            <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent_0%,rgba(0,255,255,0.1)_50%,transparent_100%)] animate-pulse" />
            
            <div className="relative flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
              <div className="space-y-3">
                <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-purple-400 to-cyan-400">
                  ESTADÍSTICAS DE EQUIPOS
                </h2>
                <div className="flex items-center gap-3 text-sm text-slate-400">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-lg shadow-emerald-400/50" />
                    <span className="font-medium">En Vivo</span>
                  </div>
                  <span className="text-slate-600">•</span>
                  <span>Última actualización: {fechaActualizacion || 'No disponible'}</span>
                </div>
              </div>

              {/* Controles */}
              <div className="flex flex-col sm:flex-row gap-3 flex-wrap">
                {/* Selector de temporada */}
                <div className="relative group">
                  <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-lg opacity-30 group-hover:opacity-50 blur transition duration-300" />
                  <div className="relative flex items-center">
                    <Calendar className="w-4 h-4 text-cyan-400 absolute left-3 pointer-events-none z-10" />
                    <select
                      value={temporadaActual || ''}
                      onChange={(event) => onCambiarTemporada(event.target.value || null)}
                      className="relative pl-10 pr-4 py-2.5 text-sm rounded-lg bg-slate-800/90 border-2 border-cyan-400/30 text-white min-w-[180px] hover:border-cyan-400/60 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/30 transition-all cursor-pointer font-medium"
                    >
                      {temporadasDisponibles.map((temporada) => (
                        <option key={temporada.id} value={temporada.id} className="bg-slate-800">
                          {temporada.nombre}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Búsqueda */}
                <div className="relative group">
                  <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-lg opacity-30 group-hover:opacity-50 blur transition duration-300" />
                  <div className="relative flex items-center">
                    <Search className="w-4 h-4 text-cyan-400 absolute left-3 pointer-events-none z-10" />
                    <input
                      value={busqueda}
                      onChange={(event) => setBusqueda(event.target.value)}
                      placeholder="Buscar equipo..."
                      className="relative pl-10 pr-4 py-2.5 text-sm rounded-lg bg-slate-800/90 border-2 border-cyan-400/30 text-white min-w-[220px] hover:border-cyan-400/60 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/30 transition-all placeholder:text-slate-500"
                    />
                  </div>
                </div>

                {/* Conferencia */}
                <div className="relative group">
                  <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-lg opacity-30 group-hover:opacity-50 blur transition duration-300" />
                  <select
                    value={conferencia}
                    onChange={(event) => setConferencia(event.target.value)}
                    className="relative px-4 py-2.5 text-sm rounded-lg bg-slate-800/90 border-2 border-cyan-400/30 text-white hover:border-cyan-400/60 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/30 transition-all cursor-pointer font-medium"
                  >
                    <option value="Todas" className="bg-slate-800">📊 Todas las Conferencias</option>
                    <option value="Este" className="bg-slate-800">🌅 Conferencia Este</option>
                    <option value="Oeste" className="bg-slate-800">🌄 Conferencia Oeste</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Contador de resultados */}
          <div className="px-6 py-4 border-b border-cyan-400/20">
            <div className="inline-flex items-center gap-3 px-4 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border border-cyan-400/30">
              <TrendingUp className="w-5 h-5 text-cyan-400" />
              <span className="text-sm text-slate-300">
                Mostrando <span className="font-bold text-cyan-400 text-lg mx-1">{equiposOrdenados.length}</span> equipos
              </span>
            </div>
          </div>

          {/* Tabla */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-cyan-500/10 border-b-2 border-cyan-400/30">
                  {columnas.map((columna) => (
                    <th
                      key={columna.id}
                      className="p-4 text-left relative group"
                      onMouseEnter={() => setColumnaHover(columna.id)}
                      onMouseLeave={() => setColumnaHover(null)}
                    >
                      <button
                        type="button"
                        className="flex items-center gap-2 font-bold uppercase tracking-wider text-xs text-slate-400 hover:text-cyan-400 transition-all duration-300"
                        onClick={() => alternarOrden(columna.id)}
                      >
                        <span className="relative">
                          {columna.etiqueta}
                          {orden.columna === columna.id && (
                            <span className="absolute inset-x-0 -bottom-1 h-0.5 bg-cyan-400" />
                          )}
                        </span>
                        <ArrowUpDown 
                          size={14} 
                          className={`transition-all duration-300 ${
                            orden.columna === columna.id 
                              ? 'text-cyan-400' 
                              : 'text-slate-600 group-hover:text-cyan-400'
                          }`}
                        />
                      </button>

                      {/* Tooltip mejorado y visible */}
                      {columnaHover === columna.id && (
                        <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                          <div className="relative">
                            {/* Glow effect */}
                            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/40 to-purple-500/40 rounded-lg blur-xl" />
                            
                            {/* Contenido */}
                            <div className="relative w-64 bg-slate-900/95 backdrop-blur-xl border-2 border-cyan-400/60 rounded-lg shadow-2xl overflow-hidden">
                              {/* Borde superior animado */}
                              <div className="h-1 bg-gradient-to-r from-cyan-400 via-purple-400 to-cyan-400 animate-pulse" />
                              
                              <div className="p-4 space-y-2">
                                {/* Título con icono */}
                                <div className="flex items-center gap-2 pb-2 border-b border-cyan-400/30">
                                  <Info className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                                  <p className="font-bold text-sm text-cyan-400 uppercase tracking-wide">
                                    {columna.etiqueta}
                                  </p>
                                </div>
                                
                                {/* Descripción */}
                                <p className="text-xs text-slate-300 leading-relaxed">
                                  {columna.descripcion}
                                </p>
                              </div>
                              
                              {/* Borde inferior */}
                              <div className="h-1 bg-gradient-to-r from-purple-400 via-cyan-400 to-purple-400" />
                            </div>
                            
                            {/* Flecha */}
                            <div className="absolute left-1/2 -translate-x-1/2 -top-2">
                              <div className="w-4 h-4 rotate-45 bg-slate-900 border-l-2 border-t-2 border-cyan-400/60" />
                            </div>
                          </div>
                        </div>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody className="divide-y divide-cyan-400/10">
                {equiposOrdenados.length > 0 ? (
                  equiposOrdenados.map((equipo, index) => (
                    <tr
                      key={`${equipo.nombre}-${index}`}
                      className="group bg-slate-900/40 hover:bg-gradient-to-r hover:from-cyan-500/10 hover:to-purple-500/10 cursor-pointer transition-all duration-300 border-l-2 border-transparent hover:border-cyan-400"
                      onClick={() => abrirDetalleEquipo(equipo)}
                    >
                      {columnas.map((columna, colIndex) => {
                        const claseColor = obtenerClaseColor(columna, equipo);
                        return (
                          <td 
                            key={`${columna.id}-${index}`}
                            className={`p-4 whitespace-nowrap transition-all duration-300 ${
                              colIndex === 0 ? 'font-semibold text-white text-base' : ''
                            } ${claseColor || 'text-slate-400'}`}
                          >
                            {obtenerValorFormateado(columna, equipo)}
                          </td>
                        );
                      })}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={columnas.length} className="p-12 text-center">
                      <div className="flex flex-col items-center gap-4">
                        <TrendingDown className="w-16 h-16 text-cyan-400/40" />
                        <p className="text-slate-400 text-lg">
                          No se encontraron equipos con los filtros aplicados
                        </p>
                        <button
                          onClick={() => {
                            setBusqueda('');
                            setConferencia('Todas');
                          }}
                          className="px-6 py-2 rounded-lg bg-cyan-500/20 border border-cyan-400/30 text-cyan-400 hover:bg-cyan-500/30 transition-all"
                        >
                          Limpiar filtros
                        </button>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}