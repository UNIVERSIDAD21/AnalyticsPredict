/**
 * PanelH2HFutbol.tsx — Panel de enfrentamientos directos con estadísticas clave.
 */

import { Users } from 'lucide-react';
import { Tarjeta } from '../atomos';
import type { PartidoFutbolEstadistico } from '../../tipos/futbol';

interface PropsPanelH2HFutbol {
  partidos: PartidoFutbolEstadistico[];
  limite: number;
  onCambiarLimite: (limite: number) => void;
}

const opcionesLimite = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50];

function formatearFecha(fechaISO: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: '2-digit',
  });
}

export function PanelH2HFutbol({
  partidos,
  limite,
  onCambiarLimite,
}: PropsPanelH2HFutbol) {
  return (
    <Tarjeta className="space-y-4">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-neon-cyan" />
          <h3 className="text-lg font-futurista text-texto-principal uppercase tracking-wider">
            H2H - Enfrentamientos Directos
          </h3>
          <span className="text-xs text-texto-terciario">
            {partidos.length} partidos
          </span>
        </div>
        <label className="text-xs text-texto-secundario flex items-center gap-2">
          Últimos
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
          partidos
        </label>
      </div>

      {partidos.length === 0 ? (
        <div className="text-sm text-texto-secundario">
          No hay enfrentamientos directos con estadísticas disponibles.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neon-cyan/20 text-xs uppercase tracking-wider text-texto-terciario">
                <th className="text-left py-2 px-2">Fecha</th>
                <th className="text-left py-2 px-2">Local</th>
                <th className="text-left py-2 px-2">Visitante</th>
                <th className="text-center py-2 px-2">Goles</th>
                <th className="text-center py-2 px-2">Corners</th>
                <th className="text-center py-2 px-2">Disparos</th>
                <th className="text-center py-2 px-2">A Puerta</th>
              </tr>
            </thead>
            <tbody>
              {partidos.map((partido) => (
                <tr
                  key={partido.id}
                  className="border-b border-futurista-medio/30 hover:bg-futurista-medio/30 transition-colors"
                >
                  <td className="py-2 px-2 text-texto-secundario font-mono text-xs">
                    {formatearFecha(partido.fechaPartido)}
                  </td>
                  <td className="py-2 px-2 text-texto-principal">
                    {partido.equipoLocalNombre}
                  </td>
                  <td className="py-2 px-2 text-texto-principal">
                    {partido.equipoVisitanteNombre}
                  </td>
                  <td className="py-2 px-2 text-center font-mono text-neon-verde">
                    {partido.golesLocal}-{partido.golesVisitante}
                  </td>
                  <td className="py-2 px-2 text-center font-mono text-neon-cyan">
                    {partido.cornersLocal}-{partido.cornersVisitante}
                  </td>
                  <td className="py-2 px-2 text-center font-mono text-neon-amarillo">
                    {partido.disparosLocal}-{partido.disparosVisitante}
                  </td>
                  <td className="py-2 px-2 text-center font-mono text-neon-magenta">
                    {partido.disparosArcoLocal}-{partido.disparosArcoVisitante}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Tarjeta>
  );
}
