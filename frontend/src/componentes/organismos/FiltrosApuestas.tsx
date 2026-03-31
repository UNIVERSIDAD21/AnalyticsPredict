/**
 * FiltrosApuestas.tsx — Controles de filtros para bitácora
 */

import { Input, Select } from '../atomos';
import { Boton } from '../atomos';

interface PropsFiltrosApuestas {
  resultado: string;
  deporte: string;
  mercado: string;
  confianza: string;
  orden: string;
  busqueda: string;
  desde: string;
  hasta: string;
  tipoApuesta: string;
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

const opcionesDeporte = [
  { valor: 'baloncesto', etiqueta: 'Baloncesto' },
  { valor: 'futbol', etiqueta: 'Fútbol' },
];

const opcionesMercado = [
  { valor: 'Q1', etiqueta: 'Q1 (NBA)' },
  { valor: 'Q2', etiqueta: 'Q2 (NBA)' },
  { valor: 'Q3', etiqueta: 'Q3 (NBA)' },
  { valor: 'Q4', etiqueta: 'Q4 (NBA)' },
  { valor: 'COMPLETO', etiqueta: 'Completo (NBA)' },
  { valor: 'GOLES_FT', etiqueta: 'Goles FT (Fútbol)' },
  { valor: 'GOLES_1T', etiqueta: 'Goles 1T (Fútbol)' },
  { valor: 'GOLES_2T', etiqueta: 'Goles 2T (Fútbol)' },
  { valor: 'CORNERS_FT', etiqueta: 'Corners FT (Fútbol)' },
  { valor: 'DISPAROS_FT', etiqueta: 'Disparos FT (Fútbol)' },
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

const opcionesTipo = [
  { valor: 'SIMPLE', etiqueta: 'Simple' },
  { valor: 'COMBINADA', etiqueta: 'Combinada' },
];

export function FiltrosApuestas({
  resultado,
  deporte,
  mercado,
  confianza,
  orden,
  busqueda,
  desde,
  hasta,
  tipoApuesta,
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
          etiqueta="Deporte"
          opciones={opcionesDeporte}
          placeholder="Todos"
          value={deporte}
          onChange={(event) => onChange('deporte', event.target.value)}
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
        <Select
          etiqueta="Tipo"
          opciones={opcionesTipo}
          placeholder="Todos"
          value={tipoApuesta}
          onChange={(event) => onChange('tipo_apuesta', event.target.value)}
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
