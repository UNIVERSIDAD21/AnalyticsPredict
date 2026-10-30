import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { clienteAPI, extraerMensajeError } from '../../servicios/api';
import { descargar, leerCuaderno } from '../../servicios/cuadernoLocal';
import { leerFavoritos } from '../../servicios/favoritosLocales';
import { priorizarCobertura, type CoberturaRegistrada } from '../../servicios/prioridadesCobertura';

export function PrioridadesCobertura({ modelos }: { modelos: Record<string, { corte_modelo?: string | null }> }) {
  const [prioridades, setPrioridades] = useState<ReturnType<typeof priorizarCobertura>>([]);
  const [errorLocal, setErrorLocal] = useState(''), [error, setError] = useState('');
  const [cobertura, setCobertura] = useState<CoberturaRegistrada | null>(null), [cargando, setCargando] = useState(false);
  const [dias, setDias] = useState(365);
  const peticion = useRef<AbortController | null>(null);
  useEffect(() => {
    const leer = () => {
      try { setPrioridades(priorizarCobertura(leerFavoritos(), leerCuaderno())); setErrorLocal(''); }
      catch { setPrioridades([]); setErrorLocal('Preferencias o cuaderno no legibles: prioridades N/D. No se sobrescribieron.'); }
    };
    leer();
    const eventos = ['favoritos-actualizados', 'cuaderno-actualizado', 'storage'];
    eventos.forEach(e => window.addEventListener(e, leer));
    return () => { eventos.forEach(e => window.removeEventListener(e, leer)); peticion.current?.abort(); };
  }, []);
  const consultar = async () => {
    peticion.current?.abort(); const c = new AbortController(); peticion.current = c;
    setCargando(true); setError('');
    try {
      const r = await clienteAPI.get<CoberturaRegistrada>('/api/local/cobertura', { params: { dias }, signal: c.signal });
      if (!c.signal.aborted) setCobertura(r.data);
    } catch (e) { if (!c.signal.aborted) setError(extraerMensajeError(e)); }
    finally { if (!c.signal.aborted) setCargando(false); }
  };
  return <section className="tarjeta space-y-4" aria-label="Prioridades de cobertura">
    <h2 className="text-lg font-semibold">Cobertura según tu uso</h2>
    <p className="text-sm text-texto-secundario">Orden: ligas favoritas, número de equipos/competiciones favoritos y copias guardadas. No mide frecuencia real de uso, calidad ni rentabilidad. Sin señales se conserva el orden del catálogo.</p>
    {errorLocal && <p role="alert">{errorLocal}</p>}
    <div className="overflow-x-auto"><table className="text-sm w-full text-left"><caption className="text-left mb-2">Prioridad personal y corte del artefacto · no cobertura de fuentes</caption><thead><tr><th className="p-2">Liga</th><th className="p-2">Favorita / entidades</th><th className="p-2">Copias</th><th className="p-2">Corte del modelo</th></tr></thead><tbody>{prioridades.map(p => <tr key={p.liga} className="border-t border-white/10"><th className="p-2">{p.liga.toUpperCase()}</th><td className="p-2">{p.favorita ? 'Sí' : 'No'} / {p.entidades}</td><td className="p-2">{p.copias}</td><td className="p-2">{modelos[p.liga]?.corte_modelo ?? 'N/D'}</td></tr>)}</tbody></table></div>
    <Link className="text-neon-cyan text-sm" to="/mis-analisis">Gestionar favoritos y copias</Link>
    <p className="text-sm">Cobertura actual de BD: {cobertura ? `observada ${cobertura.observado_en}` : 'N/D · aún no consultada'}. No se conecta al abrir esta sección.</p>
    <div className="flex flex-wrap items-end gap-4"><label className="text-sm">Ventana del inventario<select className="input-base mt-2 block" value={dias} disabled={cargando} onChange={e => setDias(Number(e.target.value))}><option value={30}>30 días</option><option value={90}>90 días</option><option value={365}>365 días</option></select></label><button className="boton-secundario" disabled={cargando} onClick={() => { void consultar(); }}>{cargando ? 'Consultando…' : 'Consultar cobertura de BD'}</button></div>
    <p className="text-xs text-texto-secundario">Solo lectura de registros existentes. No descarga partidos, rellena huecos, sincroniza agendas ni cambia modelos.</p>
    {error && <p role="alert">{error}{cobertura ? ' Se conserva la última lectura, no es una actualización exitosa.' : ' Conteos N/D, no cero.'}</p>}
    {cobertura && <div className="space-y-3"><p className="text-sm">Ventana conservada: {cobertura.ventana.dias} días · {cobertura.ventana.desde} → {cobertura.ventana.hasta}. Cambiar el selector no modifica esta lectura.</p><p className="text-xs text-texto-secundario">{cobertura.criterio}</p><p className="text-sm">Completitud frente al calendario oficial: N/D. No se conoce el denominador de encuentros ausentes.</p>
      {!cobertura.competiciones.length ? <p>No se recibieron competiciones; no acredita ausencia de actividad.</p> : <div className="overflow-x-auto"><table className="text-sm w-full text-left"><caption className="text-left mb-2">Inventario observado · presentes por campo sobre finales con marcador, no elegibilidad</caption><thead><tr><th className="p-2">Competición</th><th className="p-2">Registros / finales</th><th className="p-2">Campos presentes</th><th className="p-2">Último final</th></tr></thead><tbody>{[...cobertura.competiciones].sort((a,b) => prioridades.findIndex(p => p.liga === a.liga) - prioridades.findIndex(p => p.liga === b.liga)).map(c => <tr key={`${c.liga}-${c.competicion_id}`} className="border-t border-white/10"><th className="p-2">{c.liga.toUpperCase()} · {c.nombre}</th><td className="p-2">{c.registros} / {c.finales_con_marcador}</td><td className="p-2">{Object.entries(c.completos_por_campo).map(([campo, n]) => `${campo}: ${n}/${c.finales_con_marcador}`).join(' · ')}</td><td className="p-2">{c.ultimo_final ?? 'N/D'}</td></tr>)}</tbody></table></div>}
    </div>}
    <button className="boton-secundario" disabled={Boolean(errorLocal)} onClick={() => descargar('prioridades-cobertura.json', JSON.stringify({ generado_en: new Date().toISOString(), prioridades, artefactos: modelos, cobertura_bd: cobertura, ultima_lectura_fallida: Boolean(error) }, null, 2))}>Exportar plan y evidencia disponible</button>
  </section>;
}
