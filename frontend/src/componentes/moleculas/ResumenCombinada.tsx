/**
 * ResumenCombinada.tsx — Resumen numérico de la combinada
 */

interface PropsResumenCombinada {
  cuotaTotal: number;
  probabilidadIndependiente: number;
  probabilidadAjustada: number;
  edge: number | null;
}

export function ResumenCombinada({
  cuotaTotal,
  probabilidadIndependiente,
  probabilidadAjustada,
  edge,
}: PropsResumenCombinada) {
  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="bg-futurista-medio/40 border border-neon-cyan/20 rounded-lg p-3">
        <p className="text-xs uppercase tracking-widest text-texto-terciario">Cuota total</p>
        <p className="text-lg text-texto-principal font-semibold">@ {cuotaTotal.toFixed(2)}</p>
      </div>
      <div className="bg-futurista-medio/40 border border-neon-cyan/20 rounded-lg p-3">
        <p className="text-xs uppercase tracking-widest text-texto-terciario">Edge</p>
        <p className="text-lg text-neon-verde font-semibold">
          {edge !== null ? `${(edge * 100).toFixed(1)}%` : '—'}
        </p>
      </div>
      <div className="bg-futurista-medio/40 border border-neon-cyan/20 rounded-lg p-3">
        <p className="text-xs uppercase tracking-widest text-texto-terciario">Prob. indep.</p>
        <p className="text-lg text-texto-principal font-semibold">
          {(probabilidadIndependiente * 100).toFixed(1)}%
        </p>
      </div>
      <div className="bg-futurista-medio/40 border border-neon-cyan/20 rounded-lg p-3">
        <p className="text-xs uppercase tracking-widest text-texto-terciario">Prob. ajustada</p>
        <p className="text-lg text-texto-principal font-semibold">
          {(probabilidadAjustada * 100).toFixed(1)}%
        </p>
      </div>
    </div>
  );
}
