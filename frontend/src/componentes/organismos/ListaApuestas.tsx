/**
 * ListaApuestas.tsx — Wrapper que usa TablaApuestas
 */

import { Apuesta } from '../../tipos';
import { TablaApuestas } from './TablaApuestas';

interface PropsListaApuestas {
  apuestas: Apuesta[];
  estado: 'idle' | 'cargando' | 'exito' | 'error';
  mensajeVacio: string;
  onResolver: (apuesta: Apuesta) => void;
  onEliminar: (apuesta: Apuesta) => void;
  onVerDetalle?: (apuesta: Apuesta) => void;
}

export function ListaApuestas(props: PropsListaApuestas) {
  return <TablaApuestas {...props} />;
}
