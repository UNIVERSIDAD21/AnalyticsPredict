import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { FormularioAnalisis } from './FormularioAnalisis';
import { TarjetaScore } from '../moleculas/TarjetaScore';
import { TarjetaSizing } from '../moleculas/TarjetaSizing';
import { TarjetaDeVig } from '../moleculas/TarjetaDeVig';
import type { Equipo } from '../../tipos';

vi.mock('../../servicios',async original=>({...await original<typeof import('../../servicios')>(),obtenerTemporadasEquipos:vi.fn().mockResolvedValue([{id:'s',nombre:'2026'}])}));
vi.mock('../../servicios/wnba',()=>({obtenerTemporadasWnba:vi.fn().mockResolvedValue([{id:'w',nombre:'2026'}])}));
afterEach(cleanup);
const equipos:Equipo[]=[{id:'h',nombre:'Casa sintética',nombre_corto:'Casa',abreviatura:'CAS'},{id:'v',nombre:'Visita sintética',nombre_corto:'Visita',abreviatura:'VIS'}];
function controles() {
  const form=document.querySelector('form')!;
  return Array.from(form.querySelectorAll('button,input,select')).filter(e => !e.closest('[data-alcance-temporadas]')).map(e=>({
    tag:e.tagName,tipo:e.getAttribute('type'),label:e.getAttribute('aria-label')||e.closest('label')?.childNodes[0]?.textContent?.trim()||e.textContent?.trim(),
    disabled:e.hasAttribute('disabled'),clase:e.className,
  }));
}
async function abrir(liga:'NBA'|'WNBA',q:number,cuotas:number,elegidos:boolean,cargando=false) {
  if(liga==='WNBA')render(<FormularioAnalisis deporte="WNBA" equipos={equipos} partidosDisponibles={[]} onAnalizar={vi.fn()} />);
  else render(<FormularioAnalisis equipos={equipos} partidosDisponibles={[]} onAnalizar={vi.fn()} />);
  if(elegidos) {
    fireEvent.change(screen.getByRole('combobox',{name:'Equipo Local'}),{target:{value:'casa sintética'}});
    fireEvent.change(screen.getByRole('combobox',{name:'Equipo Visitante'}),{target:{value:'visita sintética'}});
    if (liga === 'WNBA') await screen.findByRole('button',{name:'2026'});
    else expect(screen.queryByText('Temporadas para el análisis')).toBeNull();
  }
  fireEvent.change(screen.getByRole('combobox',{name:'Modo de análisis'}),{target:{value:String(q)}});
  if(q)await waitFor(()=>expect(screen.queryByText('Temporadas para el análisis')).toBeNull());
  if(!q&&cuotas)fireEvent.change(screen.getByLabelText('Cuota Over'),{target:{value:'1.91'}});
  if(!q&&cuotas===2)fireEvent.change(screen.getByLabelText('Cuota Under'),{target:{value:'1.91'}});
  if(cargando) {
    cleanup();
    if(liga==='WNBA')render(<FormularioAnalisis deporte="WNBA" equipos={equipos} partidosDisponibles={[]} cargando onAnalizar={vi.fn()} />);
    else render(<FormularioAnalisis equipos={equipos} partidosDisponibles={[]} cargando onAnalizar={vi.fn()} />);
  }
}

describe('controles comunes NBA/WNBA; alcance propio sin ajuste NBA implícito',()=>{
  it.each([0,1,2,3].flatMap(q=>[0,1,2].map(c=>[q,c])))('mismos controles comunes NBA/WNBA modo%i cuotas%i',async(q,c)=>{
    await abrir('NBA',q,c,true);const nba=controles();cleanup();await abrir('WNBA',q,c,true);
    expect(controles()).toEqual(nba);
    expect(document.querySelectorAll('input[type=date],input[type=checkbox]')).toHaveLength(0);
  });
  it.each([false,true])('mismos controles sin equipos; cargando=%s',async cargando=>{
    await abrir('NBA',0,0,false,cargando);const nba=controles();cleanup();await abrir('WNBA',0,0,false,cargando);expect(controles()).toEqual(nba);
  });
});

describe('campos avanzados conservados sin inventar política WNBA',()=>{
  it('conserva el desglose NBA de score y dispersión, con pesos N/D',()=>{
    render(<TarjetaScore conservarCampos scoreTotal={null} valorEsperado={0.1}
      componentes={{ev:null,edge_real:null,riesgo_valor:17,riesgo_referencia:null,riesgo_normalizado:null,penalizacion_riesgo:null,penalizacion_devig:null}}
      explicacion="N/D: sin política WNBA validada" penalizaciones={[]} />);
    for(const label of ['Desglose del Score','Valor Esperado (EV)','Edge Real','Riesgo (σ = 17.0)','Penalización De-Vig'])expect(screen.getByText(label)).toBeInTheDocument();
    expect(screen.getAllByText('N/D').length).toBeGreaterThanOrEqual(4);
    expect(screen.queryByText('APUESTA APTA')).toBeNull();
    expect(screen.getAllByText(/sin política WNBA validada/).length).toBeGreaterThan(0);
  });
  it('conserva stake, bankroll y todas las fracciones sin asumir perfil ni Kelly NBA',()=>{
    render(<TarjetaSizing conservarCampos kellyFull={null} kellyFraccional={null} fraccionKelly={null}
      stake={null} stakePorcentaje={null} bankroll={null} perfilRiesgo={null}
      advertencias={['N/D: sin política WNBA validada']} penalizaciones={null}/>);
    for(const label of ['Stake Recomendado','Bankroll','Kelly Full','Fracción','Kelly Frac.'])expect(screen.getByText(label)).toBeInTheDocument();
    expect(screen.getAllByText('N/D').length).toBeGreaterThanOrEqual(5);
    expect(screen.queryByText('SIZING RECOMENDADO')).toBeNull();
    expect(screen.getByText(/sin política WNBA validada/)).toBeInTheDocument();
  });
  it('no etiqueta el edge RAW como calibrado ni como recomendación',()=>{
    render(<TarjetaDeVig calibrado={false} metodo="exacto" overround={1.04} pMktRaw={.52} pMktFair={.5} edgeRaw={.08} edgeReal={.1}/>);
    expect(screen.getByText('RAW + de-vig')).toBeInTheDocument();
    expect(screen.queryByText('Calibrado + de-vig')).toBeNull();
    expect(screen.queryByText('USAR ESTE')).toBeNull();
  });
});
