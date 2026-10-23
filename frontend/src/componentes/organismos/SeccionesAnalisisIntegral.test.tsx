import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { afterEach, describe, it, expect } from 'vitest';
import type { AnalisisIntegral } from '../../tipos/analisisIntegral';
import { SeccionesAnalisisIntegral } from './SeccionesAnalisisIntegral';

const datos: AnalisisIntegral = { version:'test',deporte:'futbol',metodo:'heuristico',unidad:'goles',mercado:'GOLES_FT',linea:2,lado:'UNDER',
  probabilidades:{over:.3,under:.4,push:.3},cuotas:{over:null,under:null},ganador:{local:.2,empate:.5,visitante:.3,marcador:'1 – 1',definicion:'90 min'},
  periodos:[{periodo:'1T',local:.5,visitante:.4,total:.9,desviacion:.6,observado:false}],
  comparacion:{media_base:2,media_ajustada:2.2,probabilidades_base:{over:null,under:null,push:null},probabilidades_ajustadas:{over:.3,under:.4,push:.3}},
  ajustes:[{factor:'Forma',delta:.2,unidad:'goles',descripcion:'Muestra reciente',aplicado:true}],razones:['Datos de la competición'],muestras:{local:20},nota_periodos:'Tiempos de fútbol' };
afterEach(cleanup);
describe('paridad de secciones',()=>{
  it('muestra empate ganador sin complementarlo como visitante',()=>{
    render(<SeccionesAnalisisIntegral datos={datos} seccion="ganador" local="Local" visitante="Visitante" />);
    expect(screen.getByText('50.00 %',{selector:'strong.text-sm'})).toBeTruthy();
    expect(screen.getByText('Empate',{selector:'strong'})).toBeTruthy();
  });
  it('renderiza periodos, impacto, ajustes y razones',()=>{
    for (const seccion of ['periodos','contexto','razones'] as const) render(<SeccionesAnalisisIntegral datos={datos} seccion={seccion} local="Local" visitante="Visitante" />);
    for(const titulo of ['Proyección por periodo','Impacto de ajustes contextuales','Ajustes aplicados','Razones del análisis']) expect(screen.getByRole('heading',{name:titulo})).toBeTruthy();
    expect(screen.getByText('Datos de la competición')).toBeTruthy();
  });
  it('calcula valor/riesgo con una sola cuota y push',()=>{
    render(<SeccionesAnalisisIntegral datos={datos} seccion="valor" local="Local" visitante="Visitante" />);
    fireEvent.change(screen.getByLabelText('Cuota Under del escenario'),{target:{value:'2'}});
    expect(screen.getByText('Saldo teórico positivo')).toBeTruthy();
    expect(screen.getByText('0.1000')).toBeTruthy();
    expect(screen.getByText('1.75')).toBeTruthy();
  });
});
