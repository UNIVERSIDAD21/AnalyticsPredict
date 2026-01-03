/**
 * ModalResultado.tsx — Modal para actualizar el resultado de una apuesta
 */

import { useEffect, useState } from 'react';
import { Boton, Input, Select } from '../atomos';
import { ResultadoApuesta } from '../../tipos';

interface PropsModalResultado {
  abierto: boolean;
  onCerrar: () => void;
  onGuardar: (resultado: ResultadoApuesta, puntosReales?: number) => void;
}

const opcionesResultado = [
  { valor: 'GANADA', etiqueta: 'Ganada' },
  { valor: 'PERDIDA', etiqueta: 'Perdida' },
  { valor: 'PUSH', etiqueta: 'Push' },
  { valor: 'ANULADA', etiqueta: 'Anulada' },
];

export function ModalResultado({ abierto, onCerrar, onGuardar }: PropsModalResultado) {
  const [resultado, setResultado] = useState<ResultadoApuesta>('GANADA');
  const [puntos, setPuntos] = useState('');

  useEffect(() => {
    if (abierto) {
      setResultado('GANADA');
      setPuntos('');
    }
  }, [abierto]);

  if (!abierto) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-xl border border-neon-cyan/30 bg-futurista-oscuro p-6">
        <h3 className="text-lg font-futurista text-texto-principal mb-4">Actualizar resultado</h3>
        <div className="space-y-4">
          <Select
            etiqueta="Resultado"
            opciones={opcionesResultado}
            value={resultado}
            onChange={(event) => setResultado(event.target.value as ResultadoApuesta)}
          />
          <Input
            etiqueta="Puntos reales (opcional)"
            type="number"
            min="0"
            value={puntos}
            onChange={(event) => setPuntos(event.target.value)}
          />
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Boton variante="fantasma" onClick={onCerrar}>
            Cancelar
          </Boton>
          <Boton
            variante="primario"
            onClick={() => {
              const puntosNumero = puntos ? Number(puntos) : undefined;
              onGuardar(resultado, puntosNumero);
            }}
          >
            Guardar
          </Boton>
        </div>
      </div>
    </div>
  );
}
