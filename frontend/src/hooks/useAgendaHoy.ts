import { useCallback, useEffect, useRef, useState } from 'react';
import { extraerMensajeError } from '../servicios/api';

interface Partido { id: string }
interface Pagina { total: number; partidos: Partido[]; pagina?: number }
interface Vista<P> { clave: string; datos: P | null; paginas: Map<string, number>; cargando: boolean; cargandoMas: boolean; error: string; errorMas: string }
interface Contexto<P> { clave: string; ctl: AbortController; operacion: AbortController | null; datos: P | null; pagina: number; paginas: Map<string, number>; ocupado: boolean }
const inicial = <P,>(clave: string, cargando: boolean): Vista<P> => ({ clave, datos: null, paginas: new Map(), cargando, cargandoMas: false, error: '', errorMas: '' });
function validarPagina(datos: Pagina, pagina: number) {
  if (!Number.isSafeInteger(datos.total) || datos.total < 0 || !Array.isArray(datos.partidos) || datos.partidos.some(p => !p || typeof p.id !== 'string' || !p.id) ||
    datos.partidos.length > datos.total || new Set(datos.partidos.map(p => p.id)).size !== datos.partidos.length || (datos.pagina !== undefined && datos.pagina !== pagina)) {
    throw new Error('La agenda devolvió una página incompatible. Actualiza la consulta para continuar.');
  }
  if (datos.total > 0 && !datos.partidos.length) throw new Error('La agenda devolvió una página vacía antes de completar sus registros. Actualiza la consulta.');
}
/** GET paginados; mantiene los datos leídos si falla una página posterior. */
export function useAgendaHoy<P extends Pagina>(clave: string, activa: boolean,
  consultar: (pagina: number, signal: AbortSignal) => Promise<P>, marca: (datos: P) => string | null) {
  const [estado, setEstado] = useState<Vista<P>>(() => inicial(clave, activa));
  const contexto = useRef<Contexto<P> | null>(null);
  useEffect(() => {
    const ctx: Contexto<P> = { clave, ctl: new AbortController(), operacion: null, datos: null, pagina: 1, paginas: new Map(), ocupado: false };
    contexto.current = ctx;
    setEstado(inicial(clave, activa));
    if (activa) {
      consultar(1, ctx.ctl.signal).then(datos => {
        if (ctx.ctl.signal.aborted) return;
        validarPagina(datos, 1);
        ctx.datos = datos; ctx.paginas = new Map(datos.partidos.map(p => [p.id, 1]));
        setEstado({ ...inicial<P>(clave, false), datos, paginas: ctx.paginas });
      }).catch(error => { if (!ctx.ctl.signal.aborted) setEstado({ ...inicial<P>(clave, false), error: extraerMensajeError(error) }); });
    }
    return () => { ctx.ctl.abort(); ctx.operacion?.abort(); };
  }, [clave, activa, consultar]);
  const detener = useCallback(() => contexto.current?.operacion?.abort(), []);
  const cargarMas = useCallback(async (limite = 1) => {
    const ctx = contexto.current;
    if (!activa || !ctx || ctx.clave !== clave || ctx.ctl.signal.aborted || ctx.ocupado || !ctx.datos || ctx.datos.partidos.length >= ctx.datos.total) return;
    const ctl = new AbortController(); ctx.operacion = ctl; ctx.ocupado = true;
    setEstado(anterior => ({ ...anterior, cargandoMas: true, errorMas: '' }));
    try {
      // Diez páginas como máximo por acción para acotar lectura y trabajo local.
      for (let i = 0; i < Math.min(10, Math.max(1, limite)); i++) {
        if (ctl.signal.aborted || ctx.ctl.signal.aborted || ctx.datos.partidos.length >= ctx.datos.total) break;
        const numero = ctx.pagina + 1;
        const datos = await consultar(numero, ctl.signal);
        if (ctl.signal.aborted || ctx.ctl.signal.aborted) break;
        validarPagina(datos, numero);
        if (datos.total !== ctx.datos.total || (marca(datos) !== null && marca(ctx.datos) !== null && marca(datos) !== marca(ctx.datos))) {
          throw new Error('La agenda cambió entre páginas. Conservamos lo leído; actualiza la consulta antes de continuar.');
        }
        if (datos.partidos.some(p => ctx.paginas.has(p.id))) throw new Error('La agenda repitió encuentros entre páginas. Conservamos lo leído; actualiza la consulta.');
        const partidos: Partido[] = [...ctx.datos.partidos, ...datos.partidos];
        if (partidos.length > datos.total) throw new Error('El total de registros no coincide con las páginas recibidas. Actualiza la consulta.');
        ctx.paginas = new Map([...ctx.paginas, ...datos.partidos.map(p => [p.id, numero] as const)]);
        ctx.datos = { ...datos, partidos }; ctx.pagina = numero;
        setEstado({ ...inicial<P>(clave, false), datos: ctx.datos, paginas: ctx.paginas, cargandoMas: true });
      }
    } catch (error) {
      if (!ctl.signal.aborted && !ctx.ctl.signal.aborted) setEstado(anterior => ({ ...anterior, errorMas: extraerMensajeError(error) }));
    } finally {
      ctx.ocupado = false; ctx.operacion = null;
      if (!ctx.ctl.signal.aborted) setEstado(anterior => ({ ...anterior, cargandoMas: false }));
    }
  }, [activa, clave, consultar, marca]);
  return { ...(activa && estado.clave === clave ? estado : inicial<P>(clave, activa)), cargarMas, detener };
}
