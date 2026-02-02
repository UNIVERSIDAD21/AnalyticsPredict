/**
 * PanelAnalisisMercadoFutbol.tsx — Analizador de líneas con H2H e historial individual.
 */

import { useMemo, useState } from 'react';
import { TrendingUp, Target, LineChart } from 'lucide-react';
import { clsx } from 'clsx';
import { Tarjeta, Boton } from '../atomos';
import type { PartidoFutbolEstadistico } from '../../tipos/futbol';

type MercadoAnalisis = 'GOLES' | 'CORNERS' | 'DISPAROS';

interface PropsPanelAnalisisMercadoFutbol {
  equipoLocalId: string;
  equipoVisitanteId: string;
  equipoLocalNombre: string;
  equipoVisitanteNombre: string;
  h2h: PartidoFutbolEstadistico[];
  historialLocal: PartidoFutbolEstadistico[];
  historialVisitante: PartidoFutbolEstadistico[];
}

interface ResumenProbabilidad {
  total: number;
  over: number;
  under: number;
  promedio: number;
}

const mercadosDisponibles: { id: MercadoAnalisis; label: string }[] = [
  { id: 'CORNERS', label: 'Corners' },
  { id: 'GOLES', label: 'Goles' },
  { id: 'DISPAROS', label: 'Disparos' },
];

function obtenerValorTotal(partido: PartidoFutbolEstadistico, mercado: MercadoAnalisis) {
  switch (mercado) {
    case 'GOLES':
      return partido.golesLocal + partido.golesVisitante;
    case 'CORNERS':
      return partido.cornersLocal + partido.cornersVisitante;
    case 'DISPAROS':
      return partido.disparosLocal + partido.disparosVisitante;
    default:
      return 0;
  }
}

function obtenerValorEquipo(
  partido: PartidoFutbolEstadistico,
  equipoId: string,
  mercado: MercadoAnalisis
) {
  const esLocal = partido.equipoLocalId === equipoId;
  switch (mercado) {
    case 'GOLES':
      return esLocal ? partido.golesLocal : partido.golesVisitante;
    case 'CORNERS':
      return esLocal ? partido.cornersLocal : partido.cornersVisitante;
    case 'DISPAROS':
      return esLocal ? partido.disparosLocal : partido.disparosVisitante;
    default:
      return 0;
  }
}

function calcularResumen(valores: number[], linea: number): ResumenProbabilidad {
  const total = valores.length;
  const over = valores.filter((valor) => valor > linea).length;
  const under = valores.filter((valor) => valor < linea).length;
  const promedio = total > 0 ? valores.reduce((acc, v) => acc + v, 0) / total : 0;
  return { total, over, under, promedio };
}

function formatearPorcentaje(valor: number | null): string {
  if (valor === null) return '—';
  return `${(valor * 100).toFixed(1)}%`;
}

export function PanelAnalisisMercadoFutbol({
  equipoLocalId,
  equipoVisitanteId,
  equipoLocalNombre,
  equipoVisitanteNombre,
  h2h,
  historialLocal,
  historialVisitante,
}: PropsPanelAnalisisMercadoFutbol) {
  const [mercado, setMercado] = useState<MercadoAnalisis>('CORNERS');
  const [linea, setLinea] = useState('');
  const [cuota, setCuota] = useState('');
  const [lado, setLado] = useState<'OVER' | 'UNDER'>('OVER');
  const [mostrarResultado, setMostrarResultado] = useState(false);

  const lineaNumerica = linea ? Number(linea) : null;
  const cuotaNumerica = cuota ? Number(cuota) : null;

  const resumenes = useMemo(() => {
    if (!lineaNumerica) return null;
    const valoresH2H = h2h.map((partido) => obtenerValorTotal(partido, mercado));
    const valoresLocal = historialLocal.map((partido) =>
      obtenerValorEquipo(partido, equipoLocalId, mercado)
    );
    const valoresVisitante = historialVisitante.map((partido) =>
      obtenerValorEquipo(partido, equipoVisitanteId, mercado)
    );

    return {
      h2h: calcularResumen(valoresH2H, lineaNumerica),
      local: calcularResumen(valoresLocal, lineaNumerica),
      visitante: calcularResumen(valoresVisitante, lineaNumerica),
    };
  }, [h2h, historialLocal, historialVisitante, lineaNumerica, mercado, equipoLocalId, equipoVisitanteId]);

  const probOverCombinada = useMemo(() => {
    if (!resumenes) return null;
    const probabilidades = [
      resumenes.h2h.total > 0 ? resumenes.h2h.over / resumenes.h2h.total : null,
      resumenes.local.total > 0 ? resumenes.local.over / resumenes.local.total : null,
      resumenes.visitante.total > 0
        ? resumenes.visitante.over / resumenes.visitante.total
        : null,
    ].filter((valor): valor is number => valor !== null);

    if (probabilidades.length === 0) return null;
    return probabilidades.reduce((acc, value) => acc + value, 0) / probabilidades.length;
  }, [resumenes]);

  const probLado = useMemo(() => {
    if (probOverCombinada === null) return null;
    return lado === 'OVER' ? probOverCombinada : 1 - probOverCombinada;
  }, [probOverCombinada, lado]);

  const edge = useMemo(() => {
    if (!probLado || !cuotaNumerica || cuotaNumerica <= 1) return null;
    const implied = 1 / cuotaNumerica;
    return probLado - implied;
  }, [probLado, cuotaNumerica]);

  return (
    <Tarjeta className="space-y-6">
      <div className="flex items-center gap-2">
        <LineChart className="w-5 h-5 text-neon-cyan" />
        <h3 className="text-lg font-futurista text-texto-principal uppercase tracking-wider">
          Analizador de Línea
        </h3>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <label className="flex flex-col gap-2 text-sm text-texto-secundario">
          Mercado
          <select
            className="bg-futurista-negro/60 border border-neon-cyan/30 rounded px-3 py-2 text-sm text-texto-principal"
            value={mercado}
            onChange={(event) => setMercado(event.target.value as MercadoAnalisis)}
          >
            {mercadosDisponibles.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-2 text-sm text-texto-secundario">
          Línea
          <input
            type="number"
            step="0.5"
            className="bg-futurista-negro/60 border border-neon-cyan/30 rounded px-3 py-2 text-sm text-texto-principal"
            value={linea}
            onChange={(event) => setLinea(event.target.value)}
            placeholder="Ej: 9.5"
          />
        </label>
        <label className="flex flex-col gap-2 text-sm text-texto-secundario">
          Cuota decimal
          <input
            type="number"
            step="0.01"
            className="bg-futurista-negro/60 border border-neon-cyan/30 rounded px-3 py-2 text-sm text-texto-principal"
            value={cuota}
            onChange={(event) => setCuota(event.target.value)}
            placeholder="Ej: 1.85"
          />
        </label>
        <div className="flex flex-col gap-2 text-sm text-texto-secundario">
          Lado
          <div className="flex gap-2">
            {(['OVER', 'UNDER'] as const).map((opcion) => (
              <button
                key={opcion}
                type="button"
                className={clsx(
                  'flex-1 px-3 py-2 rounded border text-sm font-medium transition-all',
                  opcion === lado
                    ? 'border-neon-verde/60 bg-neon-verde/10 text-neon-verde'
                    : 'border-neon-cyan/30 bg-futurista-negro/40 text-texto-secundario'
                )}
                onClick={() => setLado(opcion)}
              >
                {opcion}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <Boton
          variante="primario"
          tamano="sm"
          iconoInicio={<Target size={16} />}
          onClick={() => setMostrarResultado(true)}
          disabled={!lineaNumerica}
        >
          Analizar
        </Boton>
      </div>

      {mostrarResultado && lineaNumerica && resumenes && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {[
              { titulo: 'H2H', datos: resumenes.h2h },
              { titulo: equipoLocalNombre, datos: resumenes.local },
              { titulo: equipoVisitanteNombre, datos: resumenes.visitante },
            ].map(({ titulo, datos }) => (
              <div
                key={titulo}
                className="rounded-lg border border-neon-cyan/20 bg-futurista-negro/40 p-4 space-y-2"
              >
                <p className="text-xs text-texto-terciario uppercase tracking-wider">
                  {titulo}
                </p>
                <p className="text-sm text-texto-secundario">
                  Muestra: <span className="text-texto-principal">{datos.total}</span>
                </p>
                <p className="text-sm text-texto-secundario">
                  Promedio: <span className="text-neon-cyan">{datos.promedio.toFixed(2)}</span>
                </p>
                <p className="text-sm text-texto-secundario">
                  Over: <span className="text-neon-verde">{datos.over}</span> · Under:{' '}
                  <span className="text-neon-rojo">{datos.under}</span>
                </p>
              </div>
            ))}
          </div>

          <div className="rounded-lg border border-neon-magenta/30 bg-futurista-negro/40 p-4 space-y-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-neon-magenta" />
              <p className="text-sm text-texto-principal font-semibold">
                Probabilidad combinada ({lado} {lineaNumerica})
              </p>
            </div>
            <div className="flex flex-wrap gap-6 text-sm">
              <div>
                <p className="text-xs text-texto-terciario">P(Over)</p>
                <p className="text-neon-verde font-mono">
                  {formatearPorcentaje(probOverCombinada)}
                </p>
              </div>
              <div>
                <p className="text-xs text-texto-terciario">P(Lado seleccionado)</p>
                <p className="text-neon-cyan font-mono">{formatearPorcentaje(probLado)}</p>
              </div>
              <div>
                <p className="text-xs text-texto-terciario">Edge estimado</p>
                <p
                  className={clsx(
                    'font-mono',
                    edge !== null && edge >= 0 ? 'text-neon-verde' : 'text-neon-rojo'
                  )}
                >
                  {edge === null ? '—' : `${(edge * 100).toFixed(2)}%`}
                </p>
              </div>
            </div>
            <p className="text-xs text-texto-terciario">
              El edge compara la probabilidad combinada con la probabilidad implícita de la
              cuota seleccionada.
            </p>
          </div>
        </div>
      )}
    </Tarjeta>
  );
}
