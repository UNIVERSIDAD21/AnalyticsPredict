/**
 * PaginaHistorialEquipo.tsx — Página de historial de partidos por equipo
 */

import { useEffect, useMemo, useState } from 'react';
import { Encabezado } from '../organismos';
import { MensajeError } from '../moleculas';
import { Spinner } from '../atomos';
import { useEquipos, useHistorialEquipo } from '../../hooks';
import { PartidoHistorial } from '../../tipos';

interface PropsPaginaHistorialEquipo {
  equipoId: string;
}

const PARTIDOS_POR_PAGINA = 20;

const formatearFecha = (fechaISO: string) => {
  const fecha = new Date(fechaISO);
  if (Number.isNaN(fecha.getTime())) {
    return fechaISO;
  }
  return new Intl.DateTimeFormat('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(fecha);
};

const obtenerOponente = (partido: PartidoHistorial) => {
  if (partido.ubicacionEquipo === 'LOCAL') {
    return {
      nombre: partido.equipoVisitante,
      abreviatura: partido.visitanteAbr,
    };
  }
  return {
    nombre: partido.equipoLocal,
    abreviatura: partido.localAbr,
  };
};

export function PaginaHistorialEquipo({ equipoId }: PropsPaginaHistorialEquipo) {
  const { equipos } = useEquipos();
  const { partidos, equipo, cargando, error, filtrosDisponibles, aplicarFiltros } =
    useHistorialEquipo(equipoId);
  const [temporadaSeleccionada, setTemporadaSeleccionada] = useState('');
  const [ubicacionSeleccionada, setUbicacionSeleccionada] = useState('todas');
  const [oponenteSeleccionado, setOponenteSeleccionado] = useState('');
  const [paginaActual, setPaginaActual] = useState(1);

  useEffect(() => {
    const comoLocal =
      ubicacionSeleccionada === 'local'
        ? true
        : ubicacionSeleccionada === 'visitante'
          ? false
          : undefined;

    aplicarFiltros({
      temporadaId: temporadaSeleccionada || undefined,
      comoLocal,
      oponenteId: oponenteSeleccionado || undefined,
    });
    setPaginaActual(1);
  }, [temporadaSeleccionada, ubicacionSeleccionada, oponenteSeleccionado, aplicarFiltros]);

  const partidosVisibles = useMemo(() => {
    const total = paginaActual * PARTIDOS_POR_PAGINA;
    return partidos.slice(0, total);
  }, [partidos, paginaActual]);

  const resumen = useMemo(() => {
    const total = partidos.length;
    const victorias = partidos.filter((partido) => partido.resultado === 'VICTORIA').length;
    const derrotas = total - victorias;
    const puntosEquipo = partidos.reduce((acc, partido) => acc + partido.puntosEquipo.total, 0);
    const puntosRival = partidos.reduce((acc, partido) => acc + partido.puntosRival.total, 0);
    return {
      total,
      victorias,
      derrotas,
      ppg: total ? puntosEquipo / total : 0,
      opp: total ? puntosRival / total : 0,
    };
  }, [partidos]);

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl border border-neon-cyan/30 bg-futurista-oscuro/60 flex items-center justify-center text-neon-cyan font-futurista">
              {equipo?.logo_url ? (
                <img
                  src={equipo.logo_url}
                  alt={`Logo de ${equipo.nombre}`}
                  className="w-12 h-12 object-contain"
                />
              ) : (
                <span className="text-lg">{equipo?.abreviatura || 'NBA'}</span>
              )}
            </div>
            <div>
              <h1 className="text-2xl font-futurista text-texto-principal">
                {equipo?.nombre || 'Historial de equipo'}
              </h1>
              <p className="text-xs text-texto-terciario">
                Historial completo de partidos con filtros combinables
              </p>
            </div>
          </div>
          <button
            type="button"
            className="px-4 py-2 text-xs uppercase tracking-wider rounded-md border border-neon-cyan/30 text-neon-cyan hover:bg-neon-cyan/10"
            onClick={() => window.location.assign('/')}
          >
            Volver al análisis
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="tarjeta">
            <p className="text-xs text-texto-terciario uppercase tracking-wider">
              Record total
            </p>
            <p className="text-2xl font-futurista text-texto-principal mt-2">
              {resumen.victorias}-{resumen.derrotas}
            </p>
          </div>
          <div className="tarjeta">
            <p className="text-xs text-texto-terciario uppercase tracking-wider">PPG</p>
            <p className="text-2xl font-futurista text-texto-principal mt-2">
              {resumen.ppg.toFixed(1)}
            </p>
          </div>
          <div className="tarjeta">
            <p className="text-xs text-texto-terciario uppercase tracking-wider">OPP</p>
            <p className="text-2xl font-futurista text-texto-principal mt-2">
              {resumen.opp.toFixed(1)}
            </p>
          </div>
        </div>

        <div className="tarjeta space-y-4">
          <div className="flex flex-col lg:flex-row gap-3">
            <div className="flex-1">
              <label className="text-xs text-texto-terciario uppercase tracking-wider">
                Temporada
              </label>
              <select
                value={temporadaSeleccionada}
                onChange={(event) => setTemporadaSeleccionada(event.target.value)}
                className="mt-2 w-full px-3 py-2 text-sm rounded-md bg-futurista-oscuro/60 border border-neon-cyan/20 text-texto-principal"
              >
                <option value="">Todas las temporadas</option>
                {filtrosDisponibles.temporadas.map((temporada) => (
                  <option key={temporada.id} value={temporada.id}>
                    {temporada.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <label className="text-xs text-texto-terciario uppercase tracking-wider">
                Ubicación
              </label>
              <select
                value={ubicacionSeleccionada}
                onChange={(event) => setUbicacionSeleccionada(event.target.value)}
                className="mt-2 w-full px-3 py-2 text-sm rounded-md bg-futurista-oscuro/60 border border-neon-cyan/20 text-texto-principal"
              >
                <option value="todas">Todos los partidos</option>
                <option value="local">Solo como Local</option>
                <option value="visitante">Solo como Visitante</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="text-xs text-texto-terciario uppercase tracking-wider">
                Oponente
              </label>
              <select
                value={oponenteSeleccionado}
                onChange={(event) => setOponenteSeleccionado(event.target.value)}
                className="mt-2 w-full px-3 py-2 text-sm rounded-md bg-futurista-oscuro/60 border border-neon-cyan/20 text-texto-principal"
              >
                <option value="">Todos los equipos</option>
                {equipos.map((equipoOponente) => (
                  <option key={equipoOponente.id} value={equipoOponente.id}>
                    {equipoOponente.nombre} ({equipoOponente.abreviatura})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {error && (
          <MensajeError
            titulo="Error al cargar historial"
            mensaje={error}
            onCerrar={() => window.location.reload()}
          />
        )}

        {cargando && (
          <div className="tarjeta flex items-center justify-center min-h-[280px]">
            <Spinner tamano="lg" texto="Cargando historial..." centrado />
          </div>
        )}

        {!cargando && !error && (
          <div className="tarjeta">
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs text-texto-secundario border-collapse">
                <thead className="text-[11px] uppercase text-texto-terciario">
                  <tr>
                    <th className="p-2 text-left">Fecha</th>
                    <th className="p-2 text-left">Temporada</th>
                    <th className="p-2 text-left">Ubicación</th>
                    <th className="p-2 text-left">Oponente</th>
                    <th className="p-2 text-right">Q1</th>
                    <th className="p-2 text-right">Q2</th>
                    <th className="p-2 text-right">Q3</th>
                    <th className="p-2 text-right">Q4</th>
                    <th className="p-2 text-right">Total</th>
                    <th className="p-2 text-right">Rival Q1</th>
                    <th className="p-2 text-right">Rival Q2</th>
                    <th className="p-2 text-right">Rival Q3</th>
                    <th className="p-2 text-right">Rival Q4</th>
                    <th className="p-2 text-right">Rival Total</th>
                    <th className="p-2 text-center">Resultado</th>
                  </tr>
                </thead>
                <tbody>
                  {partidosVisibles.map((partido) => {
                    const oponente = obtenerOponente(partido);
                    const esVictoria = partido.resultado === 'VICTORIA';
                    return (
                      <tr key={partido.id} className="border-t border-neon-cyan/10">
                        <td className="p-2 whitespace-nowrap">
                          {formatearFecha(partido.fecha)}
                        </td>
                        <td className="p-2 whitespace-nowrap">{partido.temporada || '—'}</td>
                        <td className="p-2 whitespace-nowrap">
                          {partido.ubicacionEquipo === 'LOCAL' ? '🏠 Local' : '✈️ Visitante'}
                        </td>
                        <td className="p-2 whitespace-nowrap">
                          {oponente.nombre} ({oponente.abreviatura})
                        </td>
                        <td className="p-2 text-right">{partido.puntosEquipo.q1}</td>
                        <td className="p-2 text-right">{partido.puntosEquipo.q2}</td>
                        <td className="p-2 text-right">{partido.puntosEquipo.q3}</td>
                        <td className="p-2 text-right">{partido.puntosEquipo.q4}</td>
                        <td className="p-2 text-right font-semibold text-texto-principal">
                          {partido.puntosEquipo.total}
                        </td>
                        <td className="p-2 text-right">{partido.puntosRival.q1}</td>
                        <td className="p-2 text-right">{partido.puntosRival.q2}</td>
                        <td className="p-2 text-right">{partido.puntosRival.q3}</td>
                        <td className="p-2 text-right">{partido.puntosRival.q4}</td>
                        <td className="p-2 text-right font-semibold text-texto-principal">
                          {partido.puntosRival.total}
                        </td>
                        <td className="p-2 text-center">
                          <span
                            className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase ${
                              esVictoria
                                ? 'bg-neon-verde/20 text-neon-verde'
                                : 'bg-neon-rojo/20 text-neon-rojo'
                            }`}
                          >
                            {esVictoria ? 'W' : 'L'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {partidosVisibles.length === 0 && (
              <div className="text-center text-texto-terciario text-sm py-8">
                No hay partidos con los filtros seleccionados.
              </div>
            )}

            {partidosVisibles.length < partidos.length && (
              <div className="flex justify-center mt-4">
                <button
                  type="button"
                  className="px-4 py-2 text-xs uppercase tracking-wider rounded-md border border-neon-cyan/30 text-neon-cyan hover:bg-neon-cyan/10"
                  onClick={() => setPaginaActual((prev) => prev + 1)}
                >
                  Mostrar más partidos
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
