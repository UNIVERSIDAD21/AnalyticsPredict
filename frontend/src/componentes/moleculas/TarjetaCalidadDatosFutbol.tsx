import type { ObjetivoCalidadDatosFutbol } from '../../tipos/futbol';

interface Props {
  calidad: ObjetivoCalidadDatosFutbol;
}

export function TarjetaCalidadDatosFutbol({ calidad }: Props) {
  return (
    <div className="p-4 border border-neon-cyan/15 rounded-lg" data-testid="tarjeta-calidad-datos-futbol">
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <span className="text-xs uppercase tracking-wide text-texto-terciario">Calidad de datos</span>
        {calidad.muestraInsuficiente && (
          <span className="text-[11px] px-2 py-1 rounded border border-amber-400/40 text-amber-300">MUESTRA INSUFICIENTE</span>
        )}
        {calidad.datosIncompletos && (
          <span className="text-[11px] px-2 py-1 rounded border border-red-400/40 text-red-300">DATOS INCOMPLETOS</span>
        )}
      </div>
      <p className="text-xs text-texto-secundario">
        Muestras → H2H: {calidad.muestras.h2h} · Local(home): {calidad.muestras.localHome} · Visitante(away): {calidad.muestras.visitanteAway} · Liga: {calidad.muestras.liga}
      </p>
      <p className="text-xs text-texto-secundario mt-1">
        Rango temporal efectivo: {calidad.rangoTemporal.fechaMin ?? 'N/D'} → {calidad.rangoTemporal.fechaMax ?? 'N/D'}
      </p>
      <p className="text-xs text-texto-secundario mt-1">
        Temporadas: {calidad.temporadasIncluidas.length} · Competiciones: {calidad.competicionesIncluidas.length}
      </p>
      {calidad.penalizacionesAplicadas.length > 0 && (
        <p className="text-xs text-neon-magenta mt-2">
          Penalizaciones: {calidad.penalizacionesAplicadas.join(', ')}
        </p>
      )}
    </div>
  );
}
