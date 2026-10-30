import { useState } from 'react';
import { compararMasa, validarMasa, validarTablaLineas } from '../../servicios/comparacionGuardada';
const porcentaje = (p: number | null) => p == null ? 'N/D' : `${(p * 100).toFixed(4)}%`;
export function ComparadorGuardado({ datos, mercado, original }: { datos: unknown; mercado: string; original: number }) {
  const [linea, setLinea] = useState(String(original));
  const masa = validarMasa(datos), tabla = validarTablaLineas(datos);
  if ((!masa || masa.mercado !== mercado) && (!tabla || tabla.mercado !== mercado)) return <details className="my-4"><summary className="text-sm cursor-pointer">Comparar otra línea</summary><p className="text-sm mt-3">N/D: esta copia no conserva una distribución o tabla compatible. No se reconstruye a partir de medias redondeadas. Cambiar la selección principal requiere una nueva consulta explícita.</p></details>;
  const n = linea.trim() ? Number(linea) : Number.NaN;
  const p = masa ? compararMasa(masa, n) : tabla?.lineas.find(l => l.linea === n);
  const sinMasaEntera = !masa && p && Number.isInteger(n) && p.push === null;
  return <details className="my-4 border-t border-white/10 pt-3"><summary className="cursor-pointer text-sm text-neon-cyan">Comparar líneas · misma corrida guardada</summary><div className="space-y-3 mt-3 text-sm">
    {masa ? <><p>{mercado} · {masa.incluye_ot ? 'Incluye OT' : 'Sin OT'} · Misma masa de {masa.simulaciones} puntos de integración WNBA. SIN_CALIBRAR.</p><label className="block">Otra línea entera o .5<input className="input-base mt-2 max-w-48 block" type="number" step="0.5" min="0" max="600" value={linea} onChange={e => setLinea(e.target.value)} /></label></> : <><p>{mercado} · Solo líneas ya calculadas en este análisis de fútbol. Se conserva la fuente de cada porcentaje; no se interpola.</p><label className="block">Línea ya calculada<select className="input-base mt-2 max-w-48 block" value={linea} onChange={e => setLinea(e.target.value)}><option value="">Selecciona línea</option>{tabla!.lineas.map(l => <option key={l.linea} value={l.linea}>{l.linea}</option>)}</select></label></>}
    <p>{p ? `Over ${porcentaje(sinMasaEntera ? null : p.over)} · Under ${porcentaje(sinMasaEntera ? null : p.under)} · Push ${porcentaje(p.push)}` : 'N/D para esa línea en esta copia.'}</p>
    {sinMasaEntera && <p>Evento discreto N/D: los porcentajes legacy de esta línea entera no separan el push. Se conservan en el snapshot original, no se reinterpretan como liquidación.</p>}
    {p && 'fuente' in p && <p>Fuente conservada: {p.fuente}{p.calibrador ? ` · Calibrador ${p.calibrador}` : ''}. Un identificador no acredita calibración independiente.</p>}
    <p className="text-texto-secundario">No cambia la línea ni el resultado original, no vuelve a entrenar, registrar o llamar a la API. En fútbol el push entero no conservado permanece N/D.</p>
  </div></details>;
}
