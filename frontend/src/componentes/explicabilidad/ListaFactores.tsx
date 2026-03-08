import { TopFactor } from '../../tipos/explicabilidad';

interface Props {
  factors: TopFactor[];
}

export default function ListaFactores({ factors }: Props) {
  const top5 = factors.slice(0, 5);

  return (
    <section className="rounded-xl border border-fuchsia-500/30 bg-[#1a1f3a] p-4">
      <h3 className="mb-3 text-sm font-semibold text-fuchsia-300">Top factores explicativos</h3>
      <div className="space-y-3">
        {top5.map((f) => {
          const width = Math.min(100, Math.max(2, Math.abs(f.contribution)));
          return (
            <div key={f.factor_name}>
              <div className="mb-1 flex items-center justify-between text-xs text-slate-300">
                <span>{f.factor_name}</span>
                <span>{f.contribution.toFixed(1)}%</span>
              </div>
              <div className="h-2 rounded bg-slate-700">
                <div className="h-2 rounded bg-gradient-to-r from-[#00d9ff] to-[#ff00aa]" style={{ width: `${width}%` }} title={f.description} />
              </div>
              <p className="mt-1 text-[11px] text-slate-400">{f.description}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
