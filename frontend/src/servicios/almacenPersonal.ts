import { isAxiosError } from 'axios';
import { clienteAPI, extraerMensajeError } from './api';
import { cachePersonal, recibirPersonal, type DatosPersonalesPC, type EstadoPersonalPC } from './personalCache';
import { leerCuadernoNavegador, validarCuaderno, type EntradaCuaderno } from './cuadernoLocal';
import { identidadFavorito, leerFavoritosNavegador, validarFavoritos, type FavoritoLocal } from './favoritosLocales';
import { aplicarPreferencias, CLAVE_VISUAL, validarPreferencias } from './preferenciasVisuales';
import type { PlanRestauracion } from './respaldoPersonal';

const endpoint = '/api/personal';
const config = { headers: { 'X-AP-Personal': '1' } };
export function canonico(v: unknown): string {
  if (Array.isArray(v)) return '[' + v.map(canonico).join(',') + ']';
  if (v !== null && typeof v === 'object') return '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + canonico((v as Record<string, unknown>)[k])).join(',') + '}';
  return JSON.stringify(v);
}
function validar(datos: DatosPersonalesPC) {
  validarCuaderno(datos.cuaderno); validarFavoritos(datos.favoritos);
  if (datos.apariencia !== null) validarPreferencias(datos.apariencia);
}
function estado(v: EstadoPersonalPC): EstadoPersonalPC {
  if (v?.formato !== 'almacen-personal-v1' || !Number.isSafeInteger(v.revision) || v.revision < 0 || typeof v.existe !== 'boolean') throw new Error('Respuesta del almacén no compatible. Tus copias no se modificaron.');
  validar(v.datos); return v;
}
let lectura: Promise<EstadoPersonalPC> | null = null;
async function fetchPersonal() {
  const r = estado((await clienteAPI.get<EstadoPersonalPC>(endpoint)).data);
  recibirPersonal(r); return r;
}
export function cargarPersonal() {
  if (!lectura) lectura = fetchPersonal().finally(() => { lectura = null; });
  return lectura;
}
export async function conservarPersonal(datos: DatosPersonalesPC, revision: number) {
  validar(datos);
  const body = { revision, operacion: crypto.randomUUID(), datos };
  try {
    const { data } = await clienteAPI.post<{ estado: EstadoPersonalPC; revision_guardada: number }>(endpoint, body, config);
    const saved = estado(data.estado);
    const confirmed = await fetchPersonal();
    if (confirmed.revision !== saved.revision || confirmed.sha256 !== saved.sha256 || canonico(confirmed.datos) !== canonico(datos)) {
      throw new Error('El almacén cambió después del guardado. Revisa la versión actual antes de continuar.');
    }
    return confirmed;
  } catch (err) {
    if (isAxiosError(err) && err.response?.status === 409) throw new Error('Tus datos cambiaron en otra pestaña. Recarga antes de guardar; no se sobrescribió.');
    // Resultado HTTP incierto: una lectura puede confirmar el commit, nunca se repite el POST.
    if (isAxiosError(err) && (!err.response || err.response.status >= 500)) {
      try {
        const r = await fetchPersonal();
        if (r.revision > revision && canonico(r.datos) === canonico(datos)) return r;
      } catch { /* La confirmación sigue siendo desconocida. */ }
    }
    throw new Error(err instanceof Error && !isAxiosError(err) ? err.message : extraerMensajeError(err));
  }
}
export async function guardarConsultaDuradera(datos: Pick<EntradaCuaderno, 'titulo' | 'liga' | 'snapshot' | 'tipo'>) {
  const current = await cargarPersonal();
  const entrada: EntradaCuaderno = { ...datos, snapshot: JSON.parse(JSON.stringify(datos.snapshot)), id: crypto.randomUUID(), guardadoEn: new Date().toISOString(), notas: '', etiquetas: [], favorito: false };
  await conservarPersonal({ ...current.datos, cuaderno: [entrada, ...current.datos.cuaderno] }, current.revision);
  return entrada;
}
export async function editarEntradaDuradera(original: EntradaCuaderno, cambios: Pick<EntradaCuaderno, 'notas' | 'etiquetas' | 'favorito'>) {
  const current = await cargarPersonal();
  const previa = current.datos.cuaderno.find(e => e.id === original.id);
  if (!previa) throw new Error('Conserva primero esta copia del navegador en el almacén de este PC.');
  if (canonico(previa) !== canonico(original)) throw new Error('Esta consulta cambió en otra pestaña. Recarga antes de editarla.');
  return conservarPersonal({ ...current.datos, cuaderno: current.datos.cuaderno.map(e => e.id === original.id ? { ...e, ...cambios } : e) }, current.revision);
}
export async function quitarEntradaDuradera(original: EntradaCuaderno) {
  const current = await cargarPersonal();
  if (canonico(current.datos.cuaderno.find(e => e.id === original.id)) !== canonico(original)) throw new Error('La consulta cambió o sigue solo en el navegador. Revisa el almacén antes de quitarla.');
  return conservarPersonal({ ...current.datos, cuaderno: current.datos.cuaderno.filter(e => e.id !== original.id) }, current.revision);
}
export async function cambiarFavoritoDuradero(f: FavoritoLocal, activo: boolean) {
  const current = await cargarPersonal(), key = identidadFavorito(f);
  const siguientes = current.datos.favoritos.filter(v => identidadFavorito(v) !== key);
  if (activo) siguientes.push(f);
  return conservarPersonal({ ...current.datos, favoritos: siguientes }, current.revision);
}
export interface PlanNavegador {
  anterior: EstadoPersonalPC; baseNavegador: string; siguientes: DatosPersonalesPC; nuevas: number; conflictos: number; favoritosNuevos: number;
}
function leerOriginales() { return { cuaderno: leerCuadernoNavegador(), favoritos: leerFavoritosNavegador() }; }
export async function prepararImportacionNavegador(): Promise<PlanNavegador> {
  const anterior = await cargarPersonal(), originales = leerOriginales();
  const existing = new Map(anterior.datos.cuaderno.map(e => [e.id, e]));
  const nuevas = originales.cuaderno.filter(e => !existing.has(e.id));
  const conflictos = originales.cuaderno.filter(e => existing.has(e.id) && canonico(e) !== canonico(existing.get(e.id))).length;
  const favs = new Set(anterior.datos.favoritos.map(identidadFavorito));
  const nuevos = originales.favoritos.filter(f => !favs.has(identidadFavorito(f)));
  const siguientes = { ...anterior.datos, cuaderno: [...nuevas, ...anterior.datos.cuaderno], favoritos: [...anterior.datos.favoritos, ...nuevos] };
  validar(siguientes);
  return { anterior, baseNavegador: canonico(originales), siguientes, nuevas: nuevas.length, conflictos, favoritosNuevos: nuevos.length };
}
export async function respaldarPersonal() {
  return (await clienteAPI.post<{ creadoEn: string; revision: number; archivo_sha256: string }>(endpoint + '/respaldo', {}, config)).data;
}
export async function importarNavegador(plan: PlanNavegador) {
  if (canonico(leerOriginales()) !== plan.baseNavegador) throw new Error('Las copias del navegador cambiaron después de la vista previa. Prepárala de nuevo.');
  if (plan.anterior.existe) await respaldarPersonal();
  return conservarPersonal(plan.siguientes, plan.anterior.revision);
}
export async function restaurarArchivoPersonal(plan: PlanRestauracion) {
  if (plan.revisionServidor === undefined || cachePersonal()?.revision !== plan.revisionServidor) throw new Error('Recarga el almacén y actualiza la vista previa antes de restaurar.');
  if (cachePersonal()?.existe) await respaldarPersonal();
  const result = await conservarPersonal(plan.siguientes, plan.revisionServidor);
  if (plan.aplicarApariencia && plan.siguientes.apariencia) {
    try { localStorage.setItem(CLAVE_VISUAL, JSON.stringify(plan.siguientes.apariencia)); aplicarPreferencias(plan.siguientes.apariencia); }
    catch { throw new Error('El respaldo quedó guardado en el PC, pero este navegador no permitió conservar la apariencia. Las consultas están a salvo.'); }
  }
  return result;
}
export async function recuperarPersonal() {
  const r = estado((await clienteAPI.post<EstadoPersonalPC>(endpoint + '/recuperar', {}, config)).data);
  recibirPersonal(r); return r;
}
