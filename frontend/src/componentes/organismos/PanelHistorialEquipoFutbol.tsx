/**
 * PanelHistorialEquipoFutbol.tsx - Historial individual de un equipo con estadisticas clave.
 */

import { useEffect, useMemo, useState } from 'react';
import { Shield } from 'lucide-react';
import { Tarjeta } from '../atomos';
import type { PartidoFutbolEstadistico, UbicacionHistorialEquipo } from '../../tipos/futbol';

interface PropsPanelHistorialEquipoFutbol {
  equipoId: string;
  equipoNombre: string;
  partidos: PartidoFutbolEstadistico[];
  limite: number;
  onCambiarLimite: (limite: number) => void;
  ubicacion: UbicacionHistorialEquipo;
  onCambiarUbicacion: (ubicacion: UbicacionHistorialEquipo) => void;
}

const opcionesLimite = [0, 10, 20, 30, 40, 50, 75, 100, 150, 200, 300, 500];
const FILAS_INICIALES = 120;
const BLOQUE_FILAS = 120;

function formatearFecha(fechaISO: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: '2-digit',
  });
}

function obtenerValoresEquipo(partido: PartidoFutbolEstadistico, equipoId: string) {
  const esLocal = partido.equipoLocalId === equipoId;
  return {
    rival: esLocal ? partido.equipoVisitanteNombre : partido.equipoLocalNombre,
    condicion: esLocal ? 'Local' : 'Visitante',
    golesFavor: esLocal ? partido.golesLocal : partido.golesVisitante,
    golesContra: esLocal ? partido.golesVisitante : partido.golesLocal,
    cornersFavor: esLocal ? partido.cornersLocal : partido.cornersVisitante,
    cornersContra: esLocal ? partido.cornersVisitante : partido.cornersLocal,
    disparosFavor: esLocal ? partido.disparosLocal : partido.disparosVisitante,
    disparosContra: esLocal ? partido.disparosVisitante : partido.disparosLocal,
    disparosArcoFavor: esLocal ? partido.disparosArcoLocal : partido.disparosArcoVisitante,
    disparosArcoContra: esLocal ? partido.disparosArcoVisitante : partido.disparosArcoLocal,
  };
}

function calcularPromedio(valores: number[]): string {
  if (valores.length === 0) return '0.0';
  const total = valores.reduce((acc, value) => acc + value, 0);
  return (total / valores.length).toFixed(1);
}

export function PanelHistorialEquipoFutbol({
  equipoId,
  equipoNombre,
  partidos,
  limite,
  onCambiarLimite,
  ubicacion,
  onCambiarUbicacion,
}: PropsPanelHistorialEquipoFutbol) {
  const [filasRenderizadas, setFilasRenderizadas] = useState(FILAS_INICIALES);

  const filas = useMemo(
    () =>
      partidos.map((partido) => ({
        partido,
        valores: obtenerValoresEquipo(partido, equipoId),
      })),
    [partidos, equipoId]
  );

  useEffect(() => {
    setFilasRenderizadas(FILAS_INICIALES);
  }, [equipoId, limite, ubicacion, partidos.length]);

  const filasVisibles = useMemo(
    () => filas.slice(0, filasRenderizadas),
    [filas, filasRenderizadas]
  );

  const goles = useMemo(() => filas.map((fila) => fila.valores.golesFavor), [filas]);
  const corners = useMemo(() => filas.map((fila) => fila.valores.cornersFavor), [filas]);
  const disparos = useMemo(() => filas.map((fila) => fila.valores.disparosFavor), [filas]);

  return (
    <Tarjeta className="space-y-4">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-neon-verde" />
          <h3 className="text-lg font-futurista text-texto-principal uppercase tracking-wider">
            {equipoNombre}
          </h3>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-texto-secundario">
          <label className="flex items-center gap-2">
            Muestra
            <select
              className="bg-futurista-negro/60 border border-neon-cyan/30 rounded px-2 py-1 text-xs text-texto-principal"
              value={limite}
              onChange={(event) => onCambiarLimite(Number(event.target.value))}
            >
              {opcionesLimite.map((opcion) => (
                <option key={opcion} value={opcion}>
                  {opcion === 0 ? 'Todos' : opcion}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2">
            Condicion
            <select
              className="bg-futurista-negro/60 border border-neon-cyan/30 rounded px-2 py-1 text-xs text-texto-principal"
              value={ubicacion}
              onChange={(event) =>
                onCambiarUbicacion(event.target.value as UbicacionHistorialEquipo)
              }
            >
              <option value="todos">Todos</option>
              <option value="local">Casa</option>
              <option value="visitante">Visitante</option>
            </select>
          </label>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
        <div className="rounded-lg border border-neon-cyan/20 bg-futurista-negro/40 p-3">
          <p className="text-xs text-texto-terciario uppercase tracking-wider">Prom. Goles</p>
          <p className="text-xl font-mono text-neon-verde">{calcularPromedio(goles)}</p>
        </div>
        <div className="rounded-lg border border-neon-magenta/20 bg-futurista-negro/40 p-3">
          <p className="text-xs text-texto-terciario uppercase tracking-wider">Prom. Corners</p>
          <p className="text-xl font-mono text-neon-magenta">{calcularPromedio(corners)}</p>
        </div>
        <div className="rounded-lg border border-neon-amarillo/20 bg-futurista-negro/40 p-3">
          <p className="text-xs text-texto-terciario uppercase tracking-wider">Prom. Disparos</p>
          <p className="text-xl font-mono text-neon-amarillo">{calcularPromedio(disparos)}</p>
        </div>
      </div>

      {partidos.length === 0 ? (
        <div className="text-sm text-texto-secundario">
          No hay historial reciente con estadisticas disponibles.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neon-cyan/20 text-xs uppercase tracking-wider text-texto-terciario">
                <th className="text-left py-2 px-2">Fecha</th>
                <th className="text-left py-2 px-2">Rival</th>
                <th className="text-left py-2 px-2">Condicion</th>
                <th className="text-center py-2 px-2">Goles</th>
                <th className="text-center py-2 px-2">Corners</th>
                <th className="text-center py-2 px-2">Disparos</th>
                <th className="text-center py-2 px-2">A Puerta</th>
              </tr>
            </thead>
            <tbody>
              {filasVisibles.map(({ partido, valores }) => {
                return (
                  <tr
                    key={partido.id}
                    className="border-b border-futurista-medio/30 hover:bg-futurista-medio/30 transition-colors"
                  >
                    <td className="py-2 px-2 text-texto-secundario font-mono text-xs">
                      {formatearFecha(partido.fechaPartido)}
                    </td>
                    <td className="py-2 px-2 text-texto-principal">{valores.rival}</td>
                    <td className="py-2 px-2 text-texto-secundario">{valores.condicion}</td>
                    <td className="py-2 px-2 text-center font-mono text-neon-verde">
                      {valores.golesFavor}-{valores.golesContra}
                    </td>
                    <td className="py-2 px-2 text-center font-mono text-neon-magenta">
                      {valores.cornersFavor}-{valores.cornersContra}
                    </td>
                    <td className="py-2 px-2 text-center font-mono text-neon-amarillo">
                      {valores.disparosFavor}-{valores.disparosContra}
                    </td>
                    <td className="py-2 px-2 text-center font-mono text-neon-cyan">
                      {valores.disparosArcoFavor}-{valores.disparosArcoContra}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filas.length > filasVisibles.length && (
            <div className="flex items-center justify-between pt-3">
              <p className="text-xs text-texto-terciario">
                Mostrando {filasVisibles.length} de {filas.length} partidos
              </p>
              <button
                type="button"
                className="px-3 py-1.5 text-xs rounded border border-neon-cyan/30 text-neon-cyan hover:bg-neon-cyan/10 transition-colors"
                onClick={() =>
                  setFilasRenderizadas((actual) =>
                    Math.min(actual + BLOQUE_FILAS, filas.length)
                  )
                }
              >
                Cargar mas
              </button>
            </div>
          )}
        </div>
      )}
    </Tarjeta>
  );
}
