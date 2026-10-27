import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ResultadoEuroliga } from './ResultadoEuroliga';
import { ResultadoAnalisis } from './ResultadoAnalisis';
import { adaptarResultadoEuroliga, formaEquipoEuroliga, h2hEuroliga } from '../../utilidades/resultadoEuroliga';
import type { ResultadoEuro } from '../../servicios/euroliga';
import { clienteAPI } from '../../servicios/api';

afterEach(()=>{cleanup();vi.restoreAllMocks();});
const p={media_local:80,media_visitante:81,media_total:161,desviacion_total:17,intervalo_predictivo_80_raw:[140,182] as [number,number],observado:false};
const euro:ResultadoEuro={analisis_id:'sintetico-euro',partido_id:null,fecha_partido:'2026-10-22',modelo_version:'euro-sintetico',dataset_sha256:'abc',fecha_analisis:'2026-10-21T20:00:00Z',corte_datos:'2026-10-20',equipo_local:'Real Madrid',equipo_visitante:'Maccabi',mercado:'COMPLETO',linea:170.5,modo:'PREPARTIDO',muestras:{local:200,visitante:6},predicciones:{Q1:p,Q2:p,Q3:p,Q4:p,COMPLETO:p},muestras_temporada:{local:6,visitante:6},temporada_reciente:'2026-2027',probabilidades:{over:0.3,under:0.7,push:0},ventaja_regulacion:{local:0.45,visitante:0.55,definicion:'No es moneyline con OT.'},advertencias:['Probabilidades RAW no calibradas.'],prospectiva_acreditada_por_fecha:true,contexto:{uso:'Descriptivo',equipos:{'real madrid':{n_historico:200,media_regulacion:75,recientes:[{id:'1',fecha:'2026-10-20',rival:'Otro',como_local:true,puntos_regulacion:70,puntos_rival_regulacion:65},{id:'2',fecha:'2026-10-18',rival:'Otro',como_local:false,puntos_regulacion:80,puntos_rival_regulacion:80}]}},h2h:[{fecha:'2026-10-01',local:'Maccabi',visitante:'Real Madrid',local_total:90,visitante_total:80}]}};
const temporada={nombre:'2026-2027',total:{partidos:6,victorias_regulacion:4,empates_regulacion:0,derrotas_regulacion:2,promedio_favor_regulacion:80,promedio_contra_regulacion:77,balance_regulacion:3},como_local:{partidos:3,victorias_regulacion:2,empates_regulacion:0,derrotas_regulacion:1,promedio_favor_regulacion:81,promedio_contra_regulacion:78,balance_regulacion:3},como_visitante:{partidos:3,victorias_regulacion:2,empates_regulacion:0,derrotas_regulacion:1,promedio_favor_regulacion:79,promedio_contra_regulacion:76,balance_regulacion:3}};
const juegoCasa={id:'1',fecha:'2026-10-20',rival:'Otro',como_local:true,puntos_regulacion:70,puntos_rival_regulacion:65,resultado_regulacion:'V' as const,cuartos:[{equipo:15,rival:14},{equipo:20,rival:18},{equipo:17,rival:16},{equipo:18,rival:17}],puntos_ot:0,puntos_rival_ot:0,puntos_finales:70,puntos_rival_finales:65};
const juegoProrroga={id:'2',fecha:'2026-10-18',rival:'Otro',como_local:false,puntos_regulacion:80,puntos_rival_regulacion:80,resultado_regulacion:'E' as const,cuartos:[{equipo:20,rival:20},{equipo:20,rival:20},{equipo:20,rival:20},{equipo:20,rival:20}],puntos_ot:5,puntos_rival_ot:4,puntos_finales:85,puntos_rival_finales:84};
const euroDetallado:ResultadoEuro={...euro,diagnostico_modelo:{partidos_entrenamiento:2591,fecha_min:'2018-10-11',fecha_max:'2026-10-20',alpha_ridge:5,ajuste_finalizado_en:'2026-10-21T20:00:00Z'},validacion_historica:{tipo:'retrospectiva_exploratoria_no_prospectiva',train_n:1000,cal_n:500,cal_util_n:480,prospectiva_n:0,calibrador_probabilistico:null,limitacion:'Evalúa candidato TRAIN, no refit final.',evaluacion:{partidos:463,evaluados:327,abstenciones:136,cobertura:327/463,mercados:{COMPLETO:{mae:15.98,mae_media_liga:15.67,brier_raw:0.258,brier_referencia_50:0.25,linea_referencia_train:160.5,cobertura_intervalo_80:0.718,n:327}}}},contexto:{...euro.contexto,corte_exclusivo:'2026-10-22',equipos:{'real madrid':{...euro.contexto.equipos['real madrid'],temporada_resumen:temporada,recientes:[juegoCasa,juegoProrroga]},maccabi:{n_historico:6,media_regulacion:79,temporada_resumen:temporada,recientes:[{...juegoCasa,id:'3',como_local:false}]}}}};

describe('resultados completos compartidos',()=>{
 it.each([0,1,2,3])('conserva secciones y acciones NBA/WNBA en el mismo estado sin cuotas, corte%i',q=>{
  // Contrato puramente visual sintético: no se ejecuta ni sustituye ningún predictor.
  const base=adaptarResultadoEuroliga(euro);
  const forma={ultimos_n:10,victorias:6,derrotas:4,racha:'V2',ppg:80,opp_ppg:77,net_rating:3};
  const comun={...base,es_en_vivo:q>0,cuartos_reales:Object.fromEntries(Array.from({length:q},(_,i)=>[`Q${i+1}`,[20,21] as [number,number]])),
   contexto:{h2h:{...h2hEuroliga(euro),tendencia_over:0},forma_equipo:forma,forma_rival:forma,descanso_equipo:null,descanso_rival:null,stats_temporada_equipo:{},stats_temporada_rival:{}},
   metadata:{mercado:'COMPLETO',modo_analisis:q?`CIERRE_Q${q}`:'PREPARTIDO',probabilidad_push:0}};
  const props={seleccionUsuario:{lado:'OVER' as const,linea:170.5},onGuardar:q?undefined:vi.fn()};
  render(<ResultadoAnalisis resultado={{...comun,metadata:{...comun.metadata,liga:'nba'}}} {...props}/>);
  const campos=()=>({secciones:[...document.querySelectorAll('h3')].map(e=>e.textContent),acciones:screen.queryAllByRole('button').map(e=>e.textContent),tablas:[...document.querySelectorAll('th')].map(e=>e.textContent)});
  const nba=campos();cleanup();
  render(<ResultadoAnalisis resultado={{...comun,metadata:{...comun.metadata,liga:'wnba',incluye_ot:!q}}} {...props}/>);
  expect(campos()).toEqual(nba);
  expect(screen.queryByTestId('barra-push')).toBeNull();
  expect(screen.queryByRole('button',{name:'Guardar en Bitácora'})!==null).toBe(q===0);
 });
 it('conserva la masa push WNBA en líneas enteras sin crear una tarjeta vacía en medias líneas',()=>{
  const base=adaptarResultadoEuroliga(euro);
  render(<ResultadoAnalisis resultado={{...base,metadata:{mercado:'COMPLETO',liga:'wnba',probabilidad_push:.02}}} seleccionUsuario={{lado:'OVER',linea:170}}/>);
  expect(screen.getByTestId('barra-push')).toBeInTheDocument();
  expect(screen.getByRole('img').getAttribute('aria-label')).toContain('Push 2.0%');
 });
 it('Euroliga usa la presentación NBA conservando RAW, ventaja y confianza no certificada',()=>{
  const get=vi.spyOn(clienteAPI,'get');
  render(<ResultadoEuroliga r={euro} seleccionUsuario={{lado:'UNDER',linea:170.5}} />);
  expect(screen.getByText('70.00%')).toBeInTheDocument();
  expect(screen.getByText('55.0%')).toBeInTheDocument();
  expect(screen.queryByText('45.0%')).toBeNull();
  expect(screen.getByText('No certificada')).toBeInTheDocument();
  expect(screen.getByText('No es moneyline con OT.')).toBeInTheDocument();
  expect(screen.getByRole('heading',{name:'Proyección por periodo'})).toBeInTheDocument();
  expect(screen.getByRole('heading',{name:'Forma Reciente'})).toBeInTheDocument();
  expect(screen.getByRole('heading',{name:'Head-to-Head'})).toBeInTheDocument();
  expect(screen.getByText('Tu análisis:')).toBeInTheDocument();
  expect(screen.queryByRole('button',{name:'Guardar en Bitácora'})).toBeNull();
  expect(get).not.toHaveBeenCalled();
 });
 it('deriva solo descriptivos observados, reconoce claves normalizadas y no fabrica tendencia',()=>{
  const forma=formaEquipoEuroliga(euro,'Real Madrid');
  expect(forma).toMatchObject({ultimos_n:2,victorias:1,empates:1,derrotas:0,ppg:75,opp_ppg:72.5,net_rating:2.5});
  expect(forma).not.toHaveProperty('tendencia');expect(forma).not.toHaveProperty('ppg_temporada');
  expect(formaEquipoEuroliga(euro,'Maccabi')).toBeNull();
 expect(h2hEuroliga(euro)).toMatchObject({promedio_equipo:80,promedio_rival:90,victorias_equipo:0,victorias_rival:1});
  render(<ResultadoEuroliga r={euro} />);
  fireEvent.click(screen.getByRole('button',{name:/Head-to-Head/}));
  expect(screen.queryByText('vs Línea')).toBeNull();
  expect(screen.getByText('Sin finales recientes disponibles.')).toBeInTheDocument();
  expect(document.body.textContent).not.toContain('NaN');
 });
 it('muestra historial de 50 posibles con detalle por cuarto/OT, filtros y diagnóstico sin placeholders NBA',()=>{
  render(<ResultadoEuroliga r={euroDetallado} />);
  expect(screen.getByRole('heading',{name:'Historial detallado Euroliga'})).toBeInTheDocument();
  expect(screen.getAllByText(/15-14.*20-18.*17-16.*18-17/)).toHaveLength(2);
  expect(screen.getByText('5-4')).toBeInTheDocument();
  expect(screen.getAllByText(/2026-2027 · 6 finales previos/)).toHaveLength(2);
  expect(screen.queryByText('Tendencia')).toBeNull();
  expect(screen.queryByText('vs temporada')).toBeNull();
  expect(screen.queryByText(/Descanso: N\/D/)).toBeNull();
  fireEvent.change(screen.getByLabelText('Sede del equipo'),{target:{value:'VISITANTE'}});
  expect(screen.getAllByText(/1 partidos/).length).toBeGreaterThan(0);
  fireEvent.click(screen.getByText('Método, historial de validación y trazabilidad'));
  expect(screen.getByText(/TRAIN 1000/)).toBeInTheDocument();
  expect(screen.getByText('15.980')).toBeInTheDocument();
  expect(screen.getByText(/no este refit final/)).toBeInTheDocument();
 });
 it('el histórico de baloncesto es consulta RAW sin indicaciones de apostar ni botón de guardado',()=>{
  const base=adaptarResultadoEuroliga({...euro,modo:'HISTORICO_RECONSTRUIDO'});
  expect(base.es_en_vivo).toBe(false);
  render(<ResultadoAnalisis resultado={{...base,mensaje_apuesta:'NO_APTO: SIN_CANDIDATOS',metadata:{...base.metadata,liga:'nba',modo_analisis:'HISTORICO_RECONSTRUIDO'}}} seleccionUsuario={{lado:'OVER',linea:170.5}} onGuardar={vi.fn()}/>);
  expect(screen.getByText(/Consulta exploratoria RAW/)).toBeInTheDocument();
  expect(screen.getByText('Tu análisis:')).toBeInTheDocument();
  expect(screen.queryByText(/Busca otra línea/)).toBeNull();
  expect(screen.queryByRole('button',{name:'Guardar en Bitácora'})).toBeNull();
 });
 it('el mismo renderer informa corte, observados y ausencia de calibración en NBA',()=>{
  const vista={...adaptarResultadoEuroliga(euro),es_en_vivo:true,cuartos_reales:{Q1:[20,21] as [number,number]},metadata:{mercado:'COMPLETO',modo_analisis:'CIERRE_Q1',metodo_live:'Ajuste heurístico no calibrado'}};
  render(<ResultadoAnalisis resultado={vista} />);
  expect(screen.getAllByText(/Corte al cierre de Q1/).length).toBeGreaterThan(0);
  expect(screen.getByText('Q1 (observado)')).toBeInTheDocument();
  expect(screen.getByText('Ajuste heurístico no calibrado')).toBeInTheDocument();
  expect(screen.getByRole('heading',{name:'Proyección por periodo'})).toBeInTheDocument();
  expect(screen.queryByText('Tu predicción coincide con la recomendación del sistema')).toBeNull();
 });
});
