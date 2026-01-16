/**
 * SelectorSeleccion.tsx — Ítem de selección para combinadas
 */

import { Trash2 } from 'lucide-react';
import { SeleccionCombinadaInput } from '../../tipos';
import { Boton } from '../atomos';

interface PropsSelectorSeleccion {
  seleccion: SeleccionCombinadaInput;
  onEliminar: () => void;
}

export function SelectorSeleccion({ seleccion, onEliminar }: PropsSelectorSeleccion) {
  return (
    <div className="flex items-center justify-between gap-3 bg-futurista-medio/40 border border-neon-cyan/20 rounded-lg p-3">
      <div>
        <p className="text-sm text-texto-principal font-medium">
          {seleccion.equipo_local} vs {seleccion.equipo_visitante}
        </p>
        <p className="text-xs text-texto-secundario">
          {seleccion.mercado} · {seleccion.lado} {seleccion.linea} · @ {seleccion.cuota}
        </p>
      </div>
      <Boton variante="fantasma" tamano="sm" onClick={onEliminar}>
        <Trash2 className="w-4 h-4" />
      </Boton>
    </div>
  );
}
