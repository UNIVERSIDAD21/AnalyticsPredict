/**
 * ListaApuestas.tsx — Lista de tarjetas de apuestas
 */

import { Apuesta } from '../../tipos';
import { TarjetaApuesta } from '../moleculas';

interface PropsListaApuestas {
  apuestas: Apuesta[];
  estado: 'idle' | 'cargando' | 'exito' | 'error';
  mensajeVacio: string;
  onResolver: (apuesta: Apuesta) => void;
  onEliminar: (apuesta: Apuesta) => void;
}

export function ListaApuestas({
  apuestas,
  estado,
  mensajeVacio,
  onResolver,
  onEliminar,
}: PropsListaApuestas) {
  if (estado === 'cargando') {
    return (
      <div className="tarjeta p-6 text-center text-texto-secundario">
        Cargando apuestas...
      </div>
    );
  }

  if (estado === 'error') {
    return (
      <div className="tarjeta p-6 text-center text-texto-secundario">
        No se pudieron cargar las apuestas.
      </div>
    );
  }

  if (apuestas.length === 0) {
    return (
      <div className="tarjeta p-6 text-center text-texto-secundario">
        {mensajeVacio}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {apuestas.map((apuesta) => (
        <TarjetaApuesta
          key={apuesta.id}
          apuesta={apuesta}
          onResolver={onResolver}
          onEliminar={onEliminar}
        />
      ))}
    </div>
  );
}
