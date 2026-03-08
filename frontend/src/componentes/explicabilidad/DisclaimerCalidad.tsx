import { QualityLevel } from '../../tipos/explicabilidad';

interface Props {
  level: QualityLevel;
}

export default function DisclaimerCalidad({ level }: Props) {
  if (level === 'C') {
    return (
      <div className="rounded-xl border-2 border-[#ff3333] bg-[#ff3333]/20 p-4 text-sm text-[#ffd5dd]">
        <p className="text-base font-extrabold uppercase">NO RECOMENDADO</p>
        <p>ADVERTENCIA: Calidad de datos insuficiente para una decisión de apuesta confiable.</p>
      </div>
    );
  }

  if (level === 'B') {
    return (
      <div className="rounded-xl border border-[#ffaa00] bg-[#ffaa00]/10 p-3 text-sm text-[#ffdf9d]">
        Algunos datos presentan calidad reducida. Procede con precaución.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-cyan-500/40 bg-cyan-500/5 p-3 text-xs text-cyan-200">
      Predicción informativa con datos de buena calidad. Aun así, existe riesgo inherente.
    </div>
  );
}
