import { QualityLevel } from '../../tipos/explicabilidad';

interface Props {
  level: QualityLevel;
}

const styleByLevel: Record<QualityLevel, { border: string; bg: string; text: string }> = {
  A: { border: '#00ff88', bg: 'rgba(0,255,136,0.10)', text: '#00ff88' },
  B: { border: '#ffaa00', bg: 'rgba(255,170,0,0.10)', text: '#ffaa00' },
  C: { border: '#ff3333', bg: 'rgba(255,51,51,0.12)', text: '#ff3333' },
};

export default function BadgeCalidad({ level }: Props) {
  const s = styleByLevel[level];
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-sm font-bold ${
        level === 'C' ? 'animate-pulse' : ''
      }`}
      style={{ borderColor: s.border, background: s.bg, color: s.text }}
      aria-label={`Nivel de calidad ${level}`}
    >
      Calidad {level}
    </span>
  );
}
