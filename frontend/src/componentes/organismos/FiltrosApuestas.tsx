/**
 * FiltrosApuestas.tsx — Controles de filtros para bitácora
 */

import { Input, Select } from '../atomos';
import { Boton } from '../atomos';

interface PropsFiltrosApuestas {
  resultado: string;
  mercado: string;
  confianza: string;
  orden: string;
  busqueda: string;
  desde: string;
  hasta: string;
  onChange: (campo: string, valor: string) => void;
  onLimpiar: () => void;
}

const opcionesResultado = [
  { valor: 'PENDIENTE', etiqueta: 'Pendiente' },
  { valor: 'GANADA', etiqueta: 'Ganada' },
  { valor: 'PERDIDA', etiqueta: 'Perdida' },
  { valor: 'PUSH', etiqueta: 'Push' },
  { valor: 'ANULADA', etiqueta: 'Anulada' },
];

const opcionesMercado = [
  { valor: 'Q1', etiqueta: 'Q1' },
  { valor: 'Q2', etiqueta: 'Q2' },
  { valor: 'Q3', etiqueta: 'Q3' },
  { valor: 'Q4', etiqueta: 'Q4' },
  { valor: 'COMPLETO', etiqueta: 'Completo' },
];

const opcionesConfianza = [
  { valor: 'ALTA', etiqueta: 'Alta' },
  { valor: 'MEDIA', etiqueta: 'Media' },
  { valor: 'BAJA', etiqueta: 'Baja' },
];

const opcionesOrden = [
  { valor: 'reciente', etiqueta: 'Más recientes' },
  { valor: 'antiguo', etiqueta: 'Más antiguas' },
];

export function FiltrosApuestas({
  resultado,
  mercado,
  confianza,
  orden,
  busqueda,
  desde,
  hasta,
  onChange,
  onLimpiar,
}: PropsFiltrosApuestas) {
  return (
    <div className="tarjeta space-y-4">
      <div className="flex flex-col lg:flex-row gap-4">
        <Input
          etiqueta="Buscar equipos"
          placeholder="Ej: Lakers"
          value={busqueda}
          onChange={(event) => onChange('busqueda', event.target.value)}
        />
        <Select
          etiqueta="Resultado"
          opciones={opcionesResultado}
          placeholder="Todos"
          value={resultado}
          onChange={(event) => onChange('resultado', event.target.value)}
        />
        <Select
          etiqueta="Mercado"
          opciones={opcionesMercado}
          placeholder="Todos"
          value={mercado}
          onChange={(event) => onChange('mercado', event.target.value)}
        />
        <Select
          etiqueta="Confianza"
          opciones={opcionesConfianza}
          placeholder="Todas"
          value={confianza}
          onChange={(event) => onChange('confianza', event.target.value)}
        />
      </div>
      <div className="flex flex-col lg:flex-row gap-4">
        <Input
          etiqueta="Desde"
          type="date"
          value={desde}
          onChange={(event) => onChange('desde', event.target.value)}
        />
        <Input
          etiqueta="Hasta"
          type="date"
          value={hasta}
          onChange={(event) => onChange('hasta', event.target.value)}
        />
        <Select
          etiqueta="Orden"
          opciones={opcionesOrden}
          placeholder="Selecciona orden"
          value={orden}
          onChange={(event) => onChange('orden', event.target.value)}
        />
        <div className="flex items-end">
          <Boton variante="secundario" tamano="md" onClick={onLimpiar}>
            Limpiar filtros
          </Boton>
        </div>
      </div>
    </div>
  );
}
