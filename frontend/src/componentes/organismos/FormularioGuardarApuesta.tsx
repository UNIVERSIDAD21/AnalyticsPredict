// hace parte del diseño de analisis
/**
 * FormularioGuardarApuesta.tsx — Modal para guardar una apuesta
 */

import { useEffect, useMemo, useState } from 'react';
import { Boton, Input } from '../atomos';
import { LadoApuesta, Mercado, PeticionCrearApuesta, ResultadoAnalisis } from '../../tipos';

interface PropsFormularioGuardarApuesta {
  abierto: boolean;
  resultado: ResultadoAnalisis;
  ladoSeleccionado: LadoApuesta;
  lineaSeleccionada: number;
  fechaPartido?: string;
  onCerrar: () => void;
  onGuardar: (apuesta: PeticionCrearApuesta) => void;
}

export function FormularioGuardarApuesta({
  abierto,
  resultado,
  ladoSeleccionado,
  lineaSeleccionada,
  fechaPartido,
  onCerrar,
  onGuardar,
}: PropsFormularioGuardarApuesta) {
  const [stake, setStake] = useState('');
  const [error, setError] = useState<string | null>(null);

  const mercado = (resultado.metadata?.mercado || 'COMPLETO') as Mercado;

  const cuotaAutoLlenada = useMemo(() => {
    const analisisMercado = resultado.analisis_mercado;

    if (analisisMercado) {
      if (ladoSeleccionado === 'OVER' && analisisMercado.cuota_over) {
        return analisisMercado.cuota_over;
      }
      if (ladoSeleccionado === 'UNDER' && analisisMercado.cuota_under) {
        return analisisMercado.cuota_under;
      }
    }

    return null;
  }, [resultado, ladoSeleccionado]);

  const fechaAutoLlenada = useMemo(() => {
    if (fechaPartido) {
      return fechaPartido;
    }

    const metadataFecha = resultado.metadata?.fecha_partido;
    if (typeof metadataFecha === 'string') {
      return metadataFecha;
    }

    return '';
  }, [fechaPartido, resultado]);

  const [cuotaManual, setCuotaManual] = useState('');
  const [fechaManual, setFechaManual] = useState('');

  useEffect(() => {
    if (abierto) {
      setStake('');
      setCuotaManual(cuotaAutoLlenada ? cuotaAutoLlenada.toFixed(2) : '');
      setFechaManual(fechaAutoLlenada);
      setError(null);
    }
  }, [abierto, cuotaAutoLlenada, fechaAutoLlenada]);

  const snapshot = useMemo(() => {
    const probabilidadSistema = ladoSeleccionado === 'OVER'
      ? resultado.probabilidad_over ?? 0
      : resultado.probabilidad_under ?? 0;

    const prediccion = mercado === 'COMPLETO'
      ? resultado.prediccion_juego_completo
      : resultado.predicciones[mercado];

    return {
      probabilidad: probabilidadSistema,
      media: prediccion?.media_total ?? null,
      desviacion: prediccion?.desviacion_total ?? null,
      valorEsperado: resultado.analisis_mercado?.valor_esperado ?? null,
    };
  }, [ladoSeleccionado, mercado, resultado]);

  if (!abierto) return null;

  const manejarGuardar = () => {
    const stakeNumero = Number(stake);
    const cuotaFinal = cuotaManual ? Number(cuotaManual) : cuotaAutoLlenada;
    const fechaFinal = fechaManual || fechaAutoLlenada;

    if (!stake || stakeNumero <= 0) {
      setError('Ingresa un stake válido.');
      return;
    }
    if (!cuotaFinal || cuotaFinal < 1.01) {
      setError('Cuota inválida. Ingresa una cuota >= 1.01');
      return;
    }

    setError(null);

    onGuardar({
      equipo_local: resultado.equipo_nombre_completo,
      equipo_visitante: resultado.rival_nombre_completo,
      fecha_partido: fechaFinal || undefined,
      mercado,
      lado: ladoSeleccionado,
      linea: lineaSeleccionada,
      cuota: cuotaFinal,
      cuota_over: resultado.analisis_mercado?.cuota_over || undefined,
      cuota_under: resultado.analisis_mercado?.cuota_under || undefined,
      stake: stakeNumero,
      probabilidad_sistema: snapshot.probabilidad,
      confianza_sistema: resultado.nivel_confianza,
      valor_esperado: snapshot.valorEsperado ?? undefined,
      prediccion_media: snapshot.media ?? undefined,
      prediccion_desviacion: snapshot.desviacion ?? undefined,
      razones: resultado.razones as unknown as Array<Record<string, unknown>>,
    });
  };

  const cuotaEsAutoLlenada = cuotaAutoLlenada !== null;
  const fechaEsAutoLlenada = fechaAutoLlenada !== '';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-lg rounded-xl border border-neon-cyan/30 bg-futurista-oscuro p-6">
        <h3 className="text-lg font-futurista text-texto-principal mb-4">
          Guardar en Bitácora
        </h3>
        <div className="space-y-4">
          <Input etiqueta="Equipo local" value={resultado.equipo_nombre_completo} disabled />
          <Input etiqueta="Equipo visitante" value={resultado.rival_nombre_completo} disabled />
          <Input etiqueta="Mercado" value={mercado} disabled />
          <Input etiqueta="Lado" value={ladoSeleccionado} disabled />
          <Input etiqueta="Línea" value={lineaSeleccionada.toString()} disabled />
          <div className="p-3 rounded-lg border-2 border-neon-cyan/50 bg-neon-cyan/5">
            <Input
              etiqueta="💰 Stake (obligatorio)"
              type="number"
              min="0"
              step="0.01"
              value={stake}
              onChange={(event) => setStake(event.target.value)}
              placeholder="Monto a apostar"
              autoFocus
            />
          </div>
          <div className="relative">
            <Input
              etiqueta={`Cuota ${cuotaEsAutoLlenada ? '(auto-llenada)' : ''}`}
              type="number"
              min="1.01"
              step="0.01"
              value={cuotaManual}
              onChange={(event) => setCuotaManual(event.target.value)}
              placeholder={cuotaEsAutoLlenada ? cuotaAutoLlenada.toFixed(2) : 'Ingresa cuota'}
            />
            {cuotaEsAutoLlenada && (
              <span className="absolute right-2 top-1 text-xs text-neon-verde">
                ✓ Del análisis
              </span>
            )}
          </div>
          <div className="relative">
            <Input
              etiqueta={`Fecha del partido ${fechaEsAutoLlenada ? '(auto-llenada)' : ''}`}
              type="date"
              value={fechaManual}
              onChange={(event) => setFechaManual(event.target.value)}
            />
            {fechaEsAutoLlenada && (
              <span className="absolute right-2 top-1 text-xs text-neon-verde">
                ✓ Del partido
              </span>
            )}
          </div>
          {error && <p className="texto-error">{error}</p>}
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Boton variante="fantasma" onClick={onCerrar}>
            Cancelar
          </Boton>
          <Boton variante="primario" onClick={manejarGuardar}>
            Guardar apuesta
          </Boton>
        </div>
      </div>
    </div>
  );
}
