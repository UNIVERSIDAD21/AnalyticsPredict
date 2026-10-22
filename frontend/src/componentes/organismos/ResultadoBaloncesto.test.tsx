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

describe('resultados completos compartidos',()=>{
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
