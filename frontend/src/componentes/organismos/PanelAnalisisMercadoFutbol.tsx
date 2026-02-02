/**
 * PanelAnalisisMercadoFutbol.tsx — Analizador de líneas con H2H e historial individual.
 */

import { useEffect, useMemo, useState } from 'react';
import { TrendingUp, Target, LineChart } from 'lucide-react';
import { clsx } from 'clsx';
import { Tarjeta, Boton } from '../atomos';
import type {
  PartidoFutbolEstadistico,
  TipoMercadoFutbol,
  NivelConfianza,
} from '../../tipos/futbol';

type MercadoAnalisis = 'GOLES' | 'CORNERS' | 'DISPAROS';
type SegmentoAnalisis = 'FT' | '1T' | '2T';
type AlcanceAnalisis = 'TOTAL' | 'LOCAL' | 'VISITANTE';
type TipoDisparo = 'TOTAL' | 'ARCO';

interface PropsPanelAnalisisMercadoFutbol {
  equipoLocalId: string;
  equipoVisitanteId: string;
  equipoLocalNombre: string;
  equipoVisitanteNombre: string;
  h2h: PartidoFutbolEstadistico[];
  historialLocal: PartidoFutbolEstadistico[];
  historialVisitante: PartidoFutbolEstadistico[];
  onGuardarApuesta?: (recomendacion: RecomendacionGuardado) => void;
}

interface ResumenProbabilidad {
  total: number;
  over: number;
  under: number;
  promedio: number;
}

interface RecomendacionGuardado {
  mercado: TipoMercadoFutbol;
  lado: 'OVER' | 'UNDER';
  linea: number;
  cuota?: number;
  probabilidad: number;
  confianza: NivelConfianza;
}

const mercadosDisponibles: { id: MercadoAnalisis; label: string }[] = [
  { id: 'CORNERS', label: 'Corners' },
  { id: 'GOLES', label: 'Goles' },
  { id: 'DISPAROS', label: 'Disparos' },
];

const segmentosCorners: { id: SegmentoAnalisis; label: string }[] = [
  { id: 'FT', label: 'Partido completo' },
  { id: '1T', label: 'Primer tiempo' },
  { id: '2T', label: 'Segundo tiempo' },
];

const alcancesDisponibles: { id: AlcanceAnalisis; label: string }[] = [
  { id: 'TOTAL', label: 'Total del partido' },
  { id: 'LOCAL', label: 'Equipo local' },
  { id: 'VISITANTE', label: 'Equipo visitante' },
];

const tiposDisparoDisponibles: { id: TipoDisparo; label: string }[] = [
  { id: 'TOTAL', label: 'Disparos totales' },
  { id: 'ARCO', label: 'Disparos a puerta' },
];

function obtenerCornersEquipo(
  partido: PartidoFutbolEstadistico,
  esLocal: boolean,
  segmento: SegmentoAnalisis
) {
  if (segmento === '1T') {
    return esLocal ? partido.cornersLocal1t ?? 0 : partido.cornersVisitante1t ?? 0;
  }
  if (segmento === '2T') {
    return esLocal ? partido.cornersLocal2t ?? 0 : partido.cornersVisitante2t ?? 0;
  }
  return esLocal ? partido.cornersLocal : partido.cornersVisitante;
}

function obtenerCornersTotal(partido: PartidoFutbolEstadistico, segmento: SegmentoAnalisis) {
  return (
    obtenerCornersEquipo(partido, true, segmento) +
    obtenerCornersEquipo(partido, false, segmento)
  );
}

function obtenerValorTotalPartido(
  partido: PartidoFutbolEstadistico,
  mercado: MercadoAnalisis,
  segmento: SegmentoAnalisis,
  tipoDisparo: TipoDisparo
) {
  if (mercado === 'CORNERS') {
    return obtenerCornersTotal(partido, segmento);
  }

  if (mercado === 'GOLES') {
    return partido.golesLocal + partido.golesVisitante;
  }

  const disparosLocal =
    tipoDisparo === 'ARCO' ? partido.disparosArcoLocal : partido.disparosLocal;
  const disparosVisitante =
    tipoDisparo === 'ARCO' ? partido.disparosArcoVisitante : partido.disparosVisitante;
  return disparosLocal + disparosVisitante;
}

function obtenerValorEquipo(
  partido: PartidoFutbolEstadistico,
  equipoId: string,
  mercado: MercadoAnalisis,
  segmento: SegmentoAnalisis,
  tipoDisparo: TipoDisparo
) {
  const esLocal = partido.equipoLocalId === equipoId;
  if (mercado === 'CORNERS') {
    return obtenerCornersEquipo(partido, esLocal, segmento);
  }
  if (mercado === 'GOLES') {
    return esLocal ? partido.golesLocal : partido.golesVisitante;
  }
  return tipoDisparo === 'ARCO'
    ? esLocal
      ? partido.disparosArcoLocal
      : partido.disparosArcoVisitante
    : esLocal
      ? partido.disparosLocal
      : partido.disparosVisitante;
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

function resolverTipoMercadoFutbol(
  mercado: MercadoAnalisis,
  segmento: SegmentoAnalisis,
  alcance: AlcanceAnalisis,
  tipoDisparo: TipoDisparo
): TipoMercadoFutbol {
  if (mercado === 'CORNERS') {
    if (alcance === 'TOTAL') {
      if (segmento === '1T') return 'CORNERS_1T';
      if (segmento === '2T') return 'CORNERS_2T';
      return 'CORNERS_FT';
    }
    if (alcance === 'LOCAL') {
      if (segmento === '1T') return 'CORNERS_LOCAL_1T';
      if (segmento === '2T') return 'CORNERS_LOCAL_2T';
      return 'CORNERS_LOCAL_FT';
    }
    if (segmento === '1T') return 'CORNERS_VISITANTE_1T';
    if (segmento === '2T') return 'CORNERS_VISITANTE_2T';
    return 'CORNERS_VISITANTE_FT';
  }

  if (mercado === 'GOLES') {
    if (alcance === 'TOTAL') {
      if (segmento === '1T') return 'GOLES_1T';
      if (segmento === '2T') return 'GOLES_2T';
      return 'GOLES_FT';
    }
    if (alcance === 'LOCAL') {
      if (segmento === '1T') return 'GOLES_LOCAL_1T';
      if (segmento === '2T') return 'GOLES_LOCAL_2T';
      return 'GOLES_LOCAL_FT';
    }
    if (segmento === '1T') return 'GOLES_VISITANTE_1T';
    if (segmento === '2T') return 'GOLES_VISITANTE_2T';
    return 'GOLES_VISITANTE_FT';
  }

  if (alcance === 'TOTAL') {
    return tipoDisparo === 'ARCO' ? 'DISPAROS_ARCO_FT' : 'DISPAROS_FT';
  }
  if (alcance === 'LOCAL') {
    return tipoDisparo === 'ARCO' ? 'DISPAROS_LOCAL_ARCO_FT' : 'DISPAROS_LOCAL_FT';
  }
  return tipoDisparo === 'ARCO'
    ? 'DISPAROS_VISITANTE_ARCO_FT'
    : 'DISPAROS_VISITANTE_FT';
}

function determinarConfianza(probabilidad: number): NivelConfianza {
  if (probabilidad >= 0.8) return 'ALTA';
  if (probabilidad >= 0.6) return 'MEDIA';
  return 'BAJA';
}


export function PanelAnalisisMercadoFutbol({
  equipoLocalId,
  equipoVisitanteId,
  equipoLocalNombre,
  equipoVisitanteNombre,
  h2h,
  historialLocal,
  historialVisitante,
  onGuardarApuesta,
}: PropsPanelAnalisisMercadoFutbol) {
  const [mercado, setMercado] = useState<MercadoAnalisis>('CORNERS');
  const [segmento, setSegmento] = useState<SegmentoAnalisis>('FT');
  const [alcance, setAlcance] = useState<AlcanceAnalisis>('TOTAL');
  const [tipoDisparo, setTipoDisparo] = useState<TipoDisparo>('TOTAL');
  const [linea, setLinea] = useState('');
  const [cuota, setCuota] = useState('');
  const [lado, setLado] = useState<'OVER' | 'UNDER'>('OVER');
  const [mostrarResultado, setMostrarResultado] = useState(false);

  const lineaNumerica = linea ? Number(linea) : null;
  const cuotaNumerica = cuota ? Number(cuota) : null;

  const segmentosDisponibles = useMemo(
    () => (mercado === 'CORNERS' ? segmentosCorners : segmentosCorners.slice(0, 1)),
    [mercado]
  );

  useEffect(() => {
    if (mercado !== 'CORNERS') {
      setSegmento('FT');
    }
    if (mercado !== 'DISPAROS') {
      setTipoDisparo('TOTAL');
    }
  }, [mercado]);

  const resumenes = useMemo(() => {
    if (!lineaNumerica) return null;
    const valoresH2H = h2h.map((partido) =>
      alcance === 'TOTAL'
        ? obtenerValorTotalPartido(partido, mercado, segmento, tipoDisparo)
        : obtenerValorEquipo(
            partido,
            alcance === 'LOCAL' ? equipoLocalId : equipoVisitanteId,
            mercado,
            segmento,
            tipoDisparo
          )
    );
    const valoresLocal = historialLocal.map((partido) =>
      alcance === 'TOTAL'
        ? obtenerValorTotalPartido(partido, mercado, segmento, tipoDisparo)
        : obtenerValorEquipo(partido, equipoLocalId, mercado, segmento, tipoDisparo)
    );
    const valoresVisitante = historialVisitante.map((partido) =>
      alcance === 'TOTAL'
        ? obtenerValorTotalPartido(partido, mercado, segmento, tipoDisparo)
        : obtenerValorEquipo(partido, equipoVisitanteId, mercado, segmento, tipoDisparo)
    );

    return {
      h2h: calcularResumen(valoresH2H, lineaNumerica),
      local: calcularResumen(valoresLocal, lineaNumerica),
      visitante: calcularResumen(valoresVisitante, lineaNumerica),
    };
  }, [
    h2h,
    historialLocal,
    historialVisitante,
    lineaNumerica,
    mercado,
    segmento,
    alcance,
    tipoDisparo,
    equipoLocalId,
    equipoVisitanteId,
  ]);

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

  const recomendacion = useMemo(() => {
    if (!lineaNumerica) return null;
    const probFinal = probLado ?? 0.5;
    return {
      mercado: resolverTipoMercadoFutbol(mercado, segmento, alcance, tipoDisparo),
      lado,
      linea: lineaNumerica,
      cuota: cuotaNumerica ?? undefined,
      probabilidad: probFinal,
      confianza: determinarConfianza(probFinal),
    };
  }, [alcance, cuotaNumerica, lado, lineaNumerica, mercado, probLado, segmento, tipoDisparo]);

  return (
    <Tarjeta className="space-y-6">
      <div className="flex items-center gap-2">
        <LineChart className="w-5 h-5 text-neon-cyan" />
        <h3 className="text-lg font-futurista text-texto-principal uppercase tracking-wider">
          Analizador de Línea
        </h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-6 gap-4">
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
        {mercado === 'CORNERS' && (
          <label className="flex flex-col gap-2 text-sm text-texto-secundario">
            Tramo
            <select
              className="bg-futurista-negro/60 border border-neon-cyan/30 rounded px-3 py-2 text-sm text-texto-principal"
              value={segmento}
              onChange={(event) => setSegmento(event.target.value as SegmentoAnalisis)}
            >
              {segmentosDisponibles.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
        )}
        {mercado === 'DISPAROS' && (
          <label className="flex flex-col gap-2 text-sm text-texto-secundario">
            Tipo de disparo
            <select
              className="bg-futurista-negro/60 border border-neon-cyan/30 rounded px-3 py-2 text-sm text-texto-principal"
              value={tipoDisparo}
              onChange={(event) => setTipoDisparo(event.target.value as TipoDisparo)}
            >
              {tiposDisparoDisponibles.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
        )}
        <label className="flex flex-col gap-2 text-sm text-texto-secundario">
          Alcance
          <select
            className="bg-futurista-negro/60 border border-neon-cyan/30 rounded px-3 py-2 text-sm text-texto-principal"
            value={alcance}
            onChange={(event) => setAlcance(event.target.value as AlcanceAnalisis)}
          >
            {alcancesDisponibles.map((item) => (
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

          {onGuardarApuesta && (
            <div className="flex justify-end">
              <Boton
                variante="primario"
                tamano="sm"
                onClick={() => {
                  if (recomendacion) {
                    onGuardarApuesta(recomendacion);
                  }
                }}
                disabled={!recomendacion}
              >
                Guardar en Bitacora
              </Boton>
            </div>
          )}
        </div>
      )}
    </Tarjeta>
  );
}
