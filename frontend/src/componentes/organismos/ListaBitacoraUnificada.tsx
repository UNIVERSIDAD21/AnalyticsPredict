/**
 * ListaBitacoraUnificada.tsx — Lista de apuestas simples y combinadas
 */

import { RegistroBitacoraUnificada } from '../../tipos';
import { TarjetaCombinada } from './TarjetaCombinada';
import { TarjetaApuestaSimple } from './TarjetaApuestaSimple';

interface PropsListaBitacoraUnificada {
  apuestas: RegistroBitacoraUnificada[];
  estado: 'idle' | 'cargando' | 'exito' | 'error';
  mensajeVacio: string;
  onResolver: (apuesta: RegistroBitacoraUnificada) => void;
  onEliminar: (apuesta: RegistroBitacoraUnificada) => void;
}

export function ListaBitacoraUnificada({
  apuestas,
  estado,
  mensajeVacio,
  onResolver,
  onEliminar,
}: PropsListaBitacoraUnificada) {
  if (estado === 'cargando') {
    return (
      <div className="tarjeta p-8 text-center">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-neon-cyan/20 rounded w-3/4 mx-auto" />
          <div className="h-4 bg-neon-cyan/10 rounded w-1/2 mx-auto" />
        </div>
        <p className="text-texto-secundario mt-4">Cargando apuestas...</p>
      </div>
    );
  }

  if (estado === 'error') {
    return (
      <div className="tarjeta p-6 text-center text-neon-rojo border border-neon-rojo/30">
        No se pudieron cargar las apuestas.
      </div>
    );
  }

  if (apuestas.length === 0) {
    return (
      <div className="tarjeta p-8 text-center text-texto-secundario">
        {mensajeVacio}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {apuestas.map((apuesta) => (
        apuesta.tipo_apuesta === 'COMBINADA' ? (
          <TarjetaCombinada
            key={apuesta.id}
            combinada={apuesta}
            onEliminar={() => onEliminar(apuesta)}
          />
        ) : (
          <TarjetaApuestaSimple
            key={apuesta.id}
            apuesta={apuesta}
            onResolver={() => onResolver(apuesta)}
            onEliminar={() => onEliminar(apuesta)}
          />
        )
      ))}
    </div>
  );
}
