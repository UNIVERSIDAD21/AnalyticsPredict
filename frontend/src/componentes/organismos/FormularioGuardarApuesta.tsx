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
  onCerrar: () => void;
  onGuardar: (apuesta: PeticionCrearApuesta) => void;
}

export function FormularioGuardarApuesta({
  abierto,
  resultado,
  ladoSeleccionado,
  lineaSeleccionada,
  onCerrar,
  onGuardar,
}: PropsFormularioGuardarApuesta) {
  const [stake, setStake] = useState('');
  const [cuota, setCuota] = useState('');
  const [fecha, setFecha] = useState('');
  const [error, setError] = useState<string | null>(null);

  const mercado = (resultado.metadata?.mercado || 'COMPLETO') as Mercado;

  useEffect(() => {
    if (abierto) {
      setStake('');
      setCuota('');
      setFecha('');
      setError(null);
    }
  }, [abierto]);

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
    const cuotaNumero = Number(cuota);

    if (!stake || stakeNumero <= 0) {
      setError('Ingresa un stake válido.');
      return;
    }
    if (!cuota || cuotaNumero < 1.01) {
      setError('Ingresa una cuota válida (>= 1.01).');
      return;
    }

    setError(null);

    onGuardar({
      equipo_local: resultado.equipo_nombre_completo,
      equipo_visitante: resultado.rival_nombre_completo,
      fecha_partido: fecha || undefined,
      mercado,
      lado: ladoSeleccionado,
      linea: lineaSeleccionada,
      cuota: cuotaNumero,
      stake: stakeNumero,
      probabilidad_sistema: snapshot.probabilidad,
      confianza_sistema: resultado.nivel_confianza,
      valor_esperado: snapshot.valorEsperado ?? undefined,
      prediccion_media: snapshot.media ?? undefined,
      prediccion_desviacion: snapshot.desviacion ?? undefined,
      razones: resultado.razones as Array<Record<string, unknown>>,
    });
  };

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
          <Input
            etiqueta="Stake"
            type="number"
            min="0"
            value={stake}
            onChange={(event) => setStake(event.target.value)}
          />
          <Input
            etiqueta="Cuota"
            type="number"
            min="1.01"
            step="0.01"
            value={cuota}
            onChange={(event) => setCuota(event.target.value)}
          />
          <Input
            etiqueta="Fecha del partido (opcional)"
            type="date"
            value={fecha}
            onChange={(event) => setFecha(event.target.value)}
          />
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
