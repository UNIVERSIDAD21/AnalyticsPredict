import { ExplanationWarning } from '../../tipos/explicabilidad';

interface Props {
  warnings: ExplanationWarning[];
}

function styles(severity: ExplanationWarning['severity']) {
  if (severity === 'high') return 'border-[#ff3366] bg-[#ff3366]/10 text-[#ff9fb6]';
  if (severity === 'medium') return 'border-[#ffaa00] bg-[#ffaa00]/10 text-[#ffd98a]';
  return 'border-[#00d9ff] bg-[#00d9ff]/10 text-[#9befff]';
}

export default function PanelWarnings({ warnings }: Props) {
  if (!warnings || warnings.length === 0) return null;

  return (
    <section className="rounded-xl border border-[#ff3366]/40 bg-[#1a1f3a] p-4">
      <h3 className="mb-3 text-sm font-semibold text-[#ff9fb6]">Advertencias</h3>
      <ul className="space-y-2">
        {warnings.map((w, idx) => (
          <li key={`${w.type}-${idx}`} className={`rounded border p-2 text-xs ${styles(w.severity)}`}>
            <span className="mr-2 font-bold">{w.severity.toUpperCase()}</span>
            {w.message}
          </li>
        ))}
      </ul>
    </section>
  );
}
