/**
 * IndicadorCorrelacion.tsx — Badge para correlaciones detectadas
 */

interface PropsIndicadorCorrelacion {
  factor: number | null;
  tieneCorrelacion: boolean;
  independenciaAsumida?: boolean;
}

export function IndicadorCorrelacion({ factor, tieneCorrelacion, independenciaAsumida }: PropsIndicadorCorrelacion) {
  if (factor === null) return <span className="text-xs px-2 py-1 rounded-full bg-advertencia-500/20 text-advertencia-500 border border-advertencia-500/30">Correlación N/D</span>;
  if (!tieneCorrelacion) {
    return (
      <span className="text-xs px-2 py-1 rounded-full bg-neon-verde/20 text-neon-verde border border-neon-verde/30">
        {independenciaAsumida ? 'Independencia supuesta' : 'Sin correlación'}
      </span>
    );
  }

  return (
    <span className="text-xs px-2 py-1 rounded-full bg-advertencia-500/20 text-advertencia-500 border border-advertencia-500/30">
      ⚠️ Correlación (factor {factor.toFixed(2)})
    </span>
  );
}
