/**
 * IndicadorCorrelacion.tsx — Badge para correlaciones detectadas
 */

interface PropsIndicadorCorrelacion {
  factor: number;
  tieneCorrelacion: boolean;
}

export function IndicadorCorrelacion({ factor, tieneCorrelacion }: PropsIndicadorCorrelacion) {
  if (!tieneCorrelacion) {
    return (
      <span className="text-xs px-2 py-1 rounded-full bg-neon-verde/20 text-neon-verde border border-neon-verde/30">
        Sin correlación
      </span>
    );
  }

  return (
    <span className="text-xs px-2 py-1 rounded-full bg-advertencia-500/20 text-advertencia-500 border border-advertencia-500/30">
      ⚠️ Correlación (factor {factor.toFixed(2)})
    </span>
  );
}
