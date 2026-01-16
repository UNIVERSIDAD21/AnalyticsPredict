/**
 * ListaSelecciones.tsx — Lista de selecciones de una combinada
 */

import { SeleccionCombinada } from '../../tipos';

interface PropsListaSelecciones {
  selecciones: SeleccionCombinada[];
}

const estilosResultado: Record<string, string> = {
  GANADA: 'text-neon-verde',
  PERDIDA: 'text-neon-rojo',
  PUSH: 'text-advertencia-500',
  PENDIENTE: 'text-neon-cyan',
};

export function ListaSelecciones({ selecciones }: PropsListaSelecciones) {
  if (!selecciones.length) {
    return <p className="text-sm text-texto-secundario">Sin selecciones cargadas.</p>;
  }

  return (
    <ul className="space-y-2">
      {selecciones.map((seleccion) => (
        <li key={seleccion.id} className="flex items-center justify-between text-sm">
          <div>
            <p className="text-texto-principal font-medium">
              {seleccion.equipo_local} vs {seleccion.equipo_visitante}
            </p>
            <p className="text-texto-secundario">
              {seleccion.mercado} · {seleccion.lado} {seleccion.linea} · @ {seleccion.cuota}
            </p>
          </div>
          <span className={estilosResultado[seleccion.resultado || 'PENDIENTE'] || 'text-texto-secundario'}>
            {seleccion.resultado || 'PENDIENTE'}
          </span>
        </li>
      ))}
    </ul>
  );
}
