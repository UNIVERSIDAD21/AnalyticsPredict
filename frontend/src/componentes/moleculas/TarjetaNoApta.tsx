/**
 * TarjetaNoApta.tsx — Estado dominante cuando no hay apuestas recomendables
 */

import { AlertTriangle, Info } from 'lucide-react';
import { CandidatoApuestaExtendido } from '../../tipos';

interface PropsTarjetaNoApta {
  mensaje?: string | null;
  candidatos?: CandidatoApuestaExtendido[];
}

function obtenerRazonCandidato(candidato: CandidatoApuestaExtendido): string {
  if (candidato.edge_real !== undefined && candidato.edge_real !== null && candidato.edge_real <= 0) {
    return 'Edge real insuficiente';
  }
  if (candidato.valor_esperado !== undefined && candidato.valor_esperado !== null && candidato.valor_esperado <= 0) {
    return 'Valor esperado negativo';
  }
  if (candidato.score_total !== undefined && candidato.score_total !== null && candidato.score_total < 0) {
    return 'Score insuficiente para pasar gates';
  }
  if (candidato.score_penalizaciones && candidato.score_penalizaciones.length > 0) {
    return `Penalizaciones: ${candidato.score_penalizaciones.join(', ')}`;
  }
  return 'No superó los filtros mínimos del motor';
}

function formatearLado(lado: string) {
  return lado === 'OVER' ? 'Over' : lado === 'UNDER' ? 'Under' : lado;
}

export function TarjetaNoApta({ mensaje, candidatos }: PropsTarjetaNoApta) {
  const textoPrincipal = mensaje?.trim() || 'No hay apuestas recomendables para este partido.';

  return (
    <div className="tarjeta border-advertencia-500/40 bg-advertencia-500/5">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-xl bg-advertencia-500/10 flex items-center justify-center border border-advertencia-500/30">
          <AlertTriangle className="w-6 h-6 text-advertencia-500" />
        </div>
        <div className="flex-1">
          <p className="text-advertencia-500 text-xs font-mono uppercase tracking-widest mb-2">
            No hay apuestas aptas
          </p>
          <h3 className="text-lg font-futurista text-texto-principal">
            {textoPrincipal}
          </h3>
          <p className="text-sm text-texto-secundario mt-2">
            El motor no encontró escenarios con valor y gates suficientes. Evita forzar una apuesta en estas condiciones.
          </p>
        </div>
      </div>

      {candidatos && candidatos.length > 0 && (
        <div className="mt-5">
          <div className="flex items-center gap-2 text-sm font-futurista text-neon-cyan uppercase tracking-wider mb-3">
            <Info size={16} />
            Candidatos evaluados
          </div>
          <div className="space-y-3">
            {candidatos.slice(0, 4).map((candidato, index) => (
              <div
                key={`${candidato.mercado}-${candidato.lado}-${index}`}
                className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 rounded-lg border border-white/5 bg-futurista-oscuro/40 px-4 py-3"
              >
                <div className="text-sm text-texto-secundario">
                  <span className="font-semibold text-texto-principal">
                    {formatearLado(candidato.lado)} {candidato.linea}
                  </span>
                  <span className="ml-2 text-xs text-texto-terciario">
                    {candidato.mercado}
                  </span>
                </div>
                <div className="text-xs text-texto-terciario">
                  {obtenerRazonCandidato(candidato)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-texto-secundario">
        <div className="rounded-lg border border-neon-cyan/20 bg-neon-cyan/5 px-3 py-2">
          Busca otra línea con mejor precio o menor margen.
        </div>
        <div className="rounded-lg border border-neon-magenta/20 bg-neon-magenta/5 px-3 py-2">
          Espera movimiento de cuota antes de volver a evaluar.
        </div>
        <div className="rounded-lg border border-neon-verde/20 bg-neon-verde/5 px-3 py-2">
          Cambia de mercado o cuarto para detectar valor.
        </div>
      </div>
    </div>
  );
}
