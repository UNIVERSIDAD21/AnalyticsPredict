import { useState } from 'react';
import type { InventarioElegibilidadFutbol, ElegibilidadObjetivoFutbol } from '../../tipos/futbol';

export const nombresMuestra: Record<string, string> = {
  h2h: 'H2H', local_home: 'Local en casa', visitante_away: 'Visitante fuera',
  local_global: 'Local · todas las sedes', visitante_global: 'Visitante · todas las sedes', liga: 'Competición',
};
const motivos: Record<string, string> = {
  CAMPO_NULL: 'Campo ausente (NULL)', PERIODOS_NO_CONCILIAN: 'Periodos incompatibles',
  VALOR_NO_ENTERO_NO_NEGATIVO_FINITO: 'Valor negativo, no entero o no finito',
  PARTIDO_NO_VALIDO_FINAL: 'Registro no válido/final', IDENTIDAD_CONFLICTIVA: 'Conflicto de identidad',
  REGULACION_NO_ACREDITADA: 'Regulación sin acreditar', GOLES_ET_NO_ACREDITADOS: 'Prórroga sin desglose de goles',
  FT_CON_ET_SIN_DESGLOSE_ESTADISTICO: 'Estadística FT con prórroga sin desglose',
  ET_MAYOR_FT: 'Prórroga mayor que marcador final', ARCO_MAYOR_DISPAROS: 'Tiros al arco mayores que tiros totales',
  REPARTO_HEURISTICO_DESDE_FT: 'Reparto por tiempo estimado desde FT',
};
const estado: Record<string, string> = { OBSERVADO: 'Datos observados utilizables', ESTIMADO: 'Estimación por tiempo desde FT', MUESTRA_LIMITADA: 'Muestra limitada', SIN_DATOS: 'N/D · sin soporte para este objetivo' };
const mercadoLegible = (m: string) => m.replace('disparos_arco', 'Tiros al arco').replace('disparos', 'Tiros totales').replace('goles', 'Goles').replace('corners', 'Córners').replace('_', ' · ').toUpperCase();

export function ElegibilidadObjetivo({ datos }: { datos: ElegibilidadObjetivoFutbol }) {
  return <section className="mt-3 space-y-2 text-xs" aria-label="Elegibilidad del mercado">
    <p className="font-semibold">{datos.mercado}: {estado[datos.estado]}</p>
    {datos.advertencias.map((a) => <p key={a} className="text-amber-300">{a}</p>)}
    <div className="max-w-full overflow-x-auto"><table className="w-full text-left" aria-label="Muestras utilizables por objetivo">
      <thead><tr>{['Contexto', 'Utilizables / registros', 'Observados', 'Estimados', 'Ausentes', 'Inválidos'].map(t => <th key={t} className="p-1">{t}</th>)}</tr></thead>
      <tbody>{Object.entries(datos.muestras).map(([nombre,m]) => <tr key={nombre}>
        <th className="p-1">{nombresMuestra[nombre] ?? nombre}</th><td>{m.utilizables} / {m.denominador}</td>
        <td>{m.observados}</td><td>{m.estimados}</td><td>{m.ausentes}</td><td>{m.invalidos}</td>
      </tr>)}</tbody>
    </table></div>
    <details><summary>Motivos y reglas de muestra</summary>
      <ul>{Object.entries(datos.muestras).flatMap(([nombre,m]) => Object.entries(m.motivos).map(([motivo,n]) =>
        <li key={`${nombre}-${motivo}`}>{nombresMuestra[nombre] ?? nombre}: {motivos[motivo] ?? motivo} · {n}</li>))}</ul>
      <p>Mínimos contextuales orientativos: H2H {datos.minimos_contexto.h2h}, local en casa {datos.minimos_contexto.local_home}, visitante fuera {datos.minimos_contexto.visitante_away}. No bloquean otros mercados ni certifican precisión.</p>
    </details>
    <p>Cero observado sí cuenta. Un total histórico requiere ambos lados; las muestras de equipo usan su propio lado. Identidad agrupada por código guardado, sin recertificación externa.</p>
  </section>;
}

export function InventarioElegibilidad({ datos }: { datos: InventarioElegibilidadFutbol }) {
  const [temporada, setTemporada] = useState('');
  const seleccion = datos.por_temporada.find(t => t.temporada_id === temporada);
  const mercados = seleccion?.mercados ?? datos.mercados;
  return <details className="min-w-0 max-w-full mt-3 text-xs"><summary className="cursor-pointer">Elegibilidad por mercado y periodo</summary>
    <p>{datos.finales_validos} finales válidos · {datos.finales_sin_ft} sin ambos goles FT.</p>
    <p>{datos.criterio} Agrupado por código guardado; identidad de competición no recertificada.</p><p>Corte exclusivo: {datos.corte}. No acredita cobertura oficial ni precisión.</p>
    <label>Temporada <select className="bg-fondo-secundario p-1" value={temporada} onChange={e => setTemporada(e.target.value)}>
      <option value="">Todas las temporadas</option>{datos.por_temporada.map(t => <option key={t.temporada_id} value={t.temporada_id}>{t.temporada}</option>)}
    </select></label>
    <div className="max-w-full overflow-x-auto"><table className="w-full text-left" aria-label="Cobertura de objetivos de fútbol">
      <thead><tr>{['Objetivo', 'Registros', 'Observados', 'Estimados', 'Ausentes', 'Inválidos', 'Ceros observados'].map(t => <th key={t} className="p-1">{t}</th>)}</tr></thead>
      <tbody>{Object.entries(mercados).map(([nombre,m]) => <tr key={nombre}>
        <th className="p-1 whitespace-nowrap">{mercadoLegible(nombre)}</th><td>{m.denominador}</td><td>{m.observados}</td><td>{m.estimados}</td><td>{m.ausentes}</td><td>{m.invalidos}</td><td>{m.ceros}</td>
      </tr>)}</tbody>
    </table></div>
    <p>Ausente no equivale a cero; puede faltar el campo o el desglose de regulación. Tiros 1T/2T son estimados: no se cuentan como observaciones por mitad.</p>
  </details>;
}
