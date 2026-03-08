import { PredictionConfidence, QualityLevel } from '../../tipos/explicabilidad';

interface Props {
  confidence: PredictionConfidence;
  qualityLevel: QualityLevel;
}

function confidenceLabel(level: PredictionConfidence['level'], qualityLevel: QualityLevel): string {
  if (qualityLevel === 'C') return 'Baja / No confiable';
  if (qualityLevel === 'B') return 'Moderada';
  if (level === 'high') return 'Alta';
  if (level === 'medium') return 'Moderada';
  return 'Baja';
}

export default function PanelConfianza({ confidence, qualityLevel }: Props) {
  const visualNumeric = qualityLevel === 'C' ? Math.min(confidence.numeric, 49) : qualityLevel === 'B' ? Math.min(confidence.numeric, 69) : confidence.numeric;
  return (
    <section className="rounded-xl border border-cyan-400/30 bg-[#1a1f3a] p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-cyan-300">Confianza</h3>
        <span className="text-sm text-slate-200">{confidenceLabel(confidence.level, qualityLevel)}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded bg-slate-700">
        <div className="h-full bg-gradient-to-r from-cyan-400 to-fuchsia-500" style={{ width: `${Math.max(0, Math.min(100, visualNumeric))}%` }} />
      </div>
      <p className="mt-2 text-xs text-slate-300">
        {visualNumeric.toFixed(1)}% · Rango {confidence.interval.lower} - {confidence.interval.upper}
      </p>
    </section>
  );
}
