import { act, renderHook, cleanup } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useAnalisis } from './useAnalisis';
import { analizarPartido, analizarPartidoEnVivo } from '../servicios';
import type { ResultadoAnalisis } from '../tipos';
vi.mock('../servicios',()=>({analizarPartido:vi.fn(),analizarPartidoEnVivo:vi.fn()}));
vi.mock('../contextos/ConfiguracionUsuario',()=>({useConfiguracionUsuario:()=>({configuracion:{modoDevig:'estricto'}})}));
vi.mock('../contextos/Toasts',()=>({useToasts:()=>({agregarToast:vi.fn()})}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
const peticion={equipo_local:'Local',equipo_visitante:'Visitante',mercado:'COMPLETO' as const,linea:220.5};
const datos:ResultadoAnalisis={equipo:'local',rival:'visitante',equipo_nombre_completo:'Local',rival_nombre_completo:'Visitante',ubicacion:'LOCAL',fecha_analisis:'2026-10-22T10:00:00Z',predicciones:{},prediccion_juego_completo:null,razones:[],nivel_confianza:'BAJA',factores_confianza:{tamano_muestra:'baja',volatilidad:'alta',frescura_datos:'baja',puntaje_total:0},analisis_mercado:null,mejor_apuesta:null,es_en_vivo:false,cuartos_reales:{},metadata:{mercado:'COMPLETO'}};
describe('despacho NBA por modo',()=>{
 it('elige una sola ruta y conserva exactamente los marcadores del corte',async()=>{
  vi.mocked(analizarPartido).mockResolvedValue({datos,advertencias:[]});
  vi.mocked(analizarPartidoEnVivo).mockResolvedValue({datos:{...datos,es_en_vivo:true},advertencias:['No calibrado live']});
  const {result}=renderHook(()=>useAnalisis());
  await act(async()=>result.current.analizar(peticion));
  expect(analizarPartido).toHaveBeenCalledTimes(1);expect(analizarPartidoEnVivo).not.toHaveBeenCalled();
  const live={...peticion,marcador_q1:'28-30',marcador_q2:'25-24'};
  await act(async()=>result.current.analizar(live));
  expect(analizarPartidoEnVivo).toHaveBeenCalledExactlyOnceWith(live);
  expect(analizarPartido).toHaveBeenCalledTimes(1);
  expect(result.current.resultado?.es_en_vivo).toBe(true);
  expect(result.current.advertencias).toContain('No calibrado live');
 });
 it('una respuesta anterior no reaparece después de limpiar o cambiar parámetros',async()=>{
  let resolver!:(r:{datos:ResultadoAnalisis;advertencias:string[]})=>void;
  vi.mocked(analizarPartidoEnVivo).mockImplementation(()=>new Promise(r=>{resolver=r;}));
  const {result}=renderHook(()=>useAnalisis());let pendiente!:Promise<void>;
  act(()=>{pendiente=result.current.analizar({...peticion,marcador_q1:'20-21'});});
  act(()=>result.current.limpiar());
  await act(async()=>{resolver({datos,advertencias:[]});await pendiente;});
  expect(result.current.resultado).toBeNull();expect(result.current.estado).toBe('inactivo');
 });
 it('un corte incompleto nunca cae silenciosamente en la ruta prepartido',async()=>{
  vi.mocked(analizarPartidoEnVivo).mockRejectedValue(new Error('Completa Q1'));
  const {result}=renderHook(()=>useAnalisis());
  await act(async()=>result.current.analizar({...peticion,marcador_q2:'20-21'}));
  expect(analizarPartido).not.toHaveBeenCalled();
  expect(analizarPartidoEnVivo).toHaveBeenCalledTimes(1);
  expect(result.current.error).toBe('Completa Q1');
 });

});
