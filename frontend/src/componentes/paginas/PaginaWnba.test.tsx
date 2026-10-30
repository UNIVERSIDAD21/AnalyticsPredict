import { MemoryRouter } from 'react-router-dom';
import { ToastsProvider } from '../../contextos/Toasts';
import "@testing-library/jest-dom/vitest";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  act,
} from "@testing-library/react";
import { ModuloWnba } from "./PaginaWnba";
import {
  analizarWnba,
  cargarWnba,
  obtenerTemporadasWnba,
  sincronizarCalendarioWnba,
  type ResultadoWnba,
} from "../../servicios/wnba";
import {
  obtenerTemporadasEquipos,
  obtenerPartidosProximos,
} from "../../servicios";

vi.mock("../../servicios/wnba", () => ({
  analizarWnba: vi.fn(),
  cargarWnba: vi.fn(),
  obtenerTemporadasWnba: vi.fn(),
  sincronizarCalendarioWnba: vi.fn(),
}));
vi.mock("../../servicios", async (original) => ({
  ...(await original<typeof import("../../servicios")>()),
  obtenerTemporadasEquipos: vi.fn(),
  obtenerPartidosProximos: vi.fn(),
}));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const pred = {
  media_local: 80,
  media_visitante: 81,
  media_total: 161,
  desviacion_total: 17,
  varianza_total: 289,
  intervalo_80_raw: [140, 182] as [number, number],
};
const resultado: ResultadoWnba = {
  analisis_id: "prueba-wnba",
  dominio: "wnba",
  equipo_local: "New York Liberty",
  equipo_visitante: "Las Vegas Aces",
  equipo_local_id: "liberty",
  equipo_visitante_id: "aces",
  partido_id: null,
  fecha_partido: null,
  fixture_fuente: null,
  fecha_analisis: "2026-10-25T20:00:00Z",
  modo: "MANUAL",
  es_prueba: true,
  incluye_ot: false,
  calibracion: "SIN_CALIBRAR",
  modelo_version: "wnba-ajuste",
  publicacion_version: "wnba-v1",
  dataset_sha256: "abc",
  corte_exclusivo: "2026-10-25",
  politica_corte: "Día local anterior",
  temporadas_solicitadas: [{ id: "2026", nombre: "2026" }],
  temporadas_utilizadas: ["2026"],
  fases_utilizadas: ["REG"],
  ultimo_final_bd: "2026-10-20",
  ultimo_dato_utilizado: "2026-09-15",
  mercado: "COMPLETO",
  linea: 160,
  semivida_dias: 365,
  muestras: {
    local: 40,
    visitante: 40,
    efectivas_local: 30,
    efectivas_visitante: 30,
    partidos: 200,
  },
  dispersion: {
    origen: "Temporal RAW",
    train_n: 100,
    seleccion_n: 30,
    dispersión_n: 40,
    desde: "2026-06-01",
  },
  predicciones: { Q1: pred, Q2: pred, Q3: pred, Q4: pred, COMPLETO: pred },
  probabilidades: { over: 0.3, under: 0.68, push: 0.02 },
  ganador_regulacion: { local: 0.4, visitante: 0.58, empate: 0.02 },
  advertencias: ["Eficacia no certificada"],
  guardar_bitacora_habilitado: false,
  motivo_bitacora: "Manual sin fixture oficial",
  valor: {
    over: { cuota: null, ev_sin_calibrar: null },
    under: { cuota: null, ev_sin_calibrar: null },
  },
  contexto: {
    uso: "Descriptivo del alcance",
    equipos: {
      liberty: { n: 40, media_regulacion: 80, recientes: [] },
      aces: { n: 40, media_regulacion: 81, recientes: [] },
    },
    h2h: [],
  },
};
function datos(disponible = true) {
  return {
    catalogo: {
      equipos: [
        {
          id: "liberty",
          nombre: "New York Liberty",
          muestras: 40,
          elegible: true,
        },
        { id: "aces", nombre: "Las Vegas Aces", muestras: 40, elegible: true },
      ],
      temporadas: [
        { id: "2025", nombre: "2025", fases: { REG: 200 } },
        { id: "2026", nombre: "2026", fases: { REG: 200 } },
      ],
      ultimo_final_bd: "2026-10-20",
      fuente_n: 410,
      finales_n: 400,
      elegibles_n: 400,
      cobertura: "Sin certificación independiente",
      modelo: { disponible },
    },
    proximos: [],
    comprobacion: undefined,
    estadisticas: { exito:true, equipos:[], fecha_actualizacion:"2026-10-25",temporadas_disponibles:[],temporada_actual:null },
    historial: [],
  };
}
async function preparar(disponible = true) {
  vi.mocked(cargarWnba).mockResolvedValue(datos(disponible));
  vi.mocked(analizarWnba).mockResolvedValue(resultado);
  vi.mocked(obtenerTemporadasWnba).mockResolvedValue(datos().catalogo.temporadas);
  const view = render(<MemoryRouter initialEntries={["/baloncesto?liga=wnba&prueba=1"]}><ToastsProvider><ModuloWnba /></ToastsProvider></MemoryRouter>);
  await screen.findByRole("combobox", { name: "Equipo Local" });
  return view;
}
function completar() {
  fireEvent.change(screen.getByRole("combobox", { name: "Equipo Local" }), {
    target: { value: "new york liberty" },
  });
  fireEvent.change(screen.getByRole("combobox", { name: "Equipo Visitante" }), {
    target: { value: "las vegas aces" },
  });
  fireEvent.change(screen.getByRole("combobox", { name: "Mercado" }), {
    target: { value: "COMPLETO" },
  });
  fireEvent.change(
    screen.getByRole("spinbutton", { name: "Línea del análisis" }),
    { target: { value: "160" } },
  );
}

describe("WNBA dentro del recorrido NBA compartido", () => {
  it("envía alcance propio y conserva temporadas sin controles adicionales", async () => {
    await preparar(); completar();
    await screen.findByRole('button',{name:'2025'});
    expect(screen.getByRole('combobox',{name:'Modo de análisis'})).toBeInTheDocument();
    expect(screen.queryByLabelText('Corte WNBA')).toBeNull();
    expect(screen.queryByRole('checkbox')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'2025'}));
    fireEvent.click(screen.getByRole('button',{name:'Analizar Partido'}));
    await waitFor(()=>expect(analizarWnba).toHaveBeenCalled());
    expect(analizarWnba).toHaveBeenCalledWith(expect.objectContaining({
      equipo_local_id:'liberty',equipo_visitante_id:'aces',temporadas:['2026'],fases:['REG'],es_prueba:true,linea:160,
      modo:'PREPARTIDO',parciales:[]
    }),expect.any(AbortSignal));
    await screen.findByText('Proyección por periodo');
    expect(obtenerTemporadasEquipos).not.toHaveBeenCalled();
    expect(obtenerPartidosProximos).not.toHaveBeenCalled();
    expect(screen.queryByRole('region',{name:'Resultado WNBA'})).toBeNull();
  });
  it.each([1,2,3])('envía cada cuarto terminado en cierre Q%i y no cuotas ni temporadas PRE',async q=>{
    await preparar(); completar();
    fireEvent.change(screen.getByRole('combobox',{name:'Modo de análisis'}),{target:{value:String(q)}});
    for(let i=1;i<=q;i++)for(const lado of ['local','visitante'])fireEvent.change(screen.getByLabelText(`Q${i} ${lado}`),{target:{value:'20'}});
    expect(screen.queryByLabelText('Cuota Over')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Analizar Partido'}));
    await waitFor(()=>expect(analizarWnba).toHaveBeenCalled());
    expect(analizarWnba).toHaveBeenCalledWith(expect.objectContaining({modo:`CIERRE_Q${q}`,parciales:Array.from({length:q},()=>[20,20]),cuota_over:undefined}),expect.any(AbortSignal));
  });
  it('aborta e ignora una respuesta tardía al desmontar',async()=>{
    const view=await preparar();let resolver!:(r:ResultadoWnba)=>void;
    vi.mocked(analizarWnba).mockImplementationOnce(()=>new Promise(r=>{resolver=r;}));
    completar();await screen.findByRole('button',{name:'2025'});
    fireEvent.click(screen.getByRole('button',{name:'Analizar Partido'}));
    await waitFor(()=>expect(analizarWnba).toHaveBeenCalled());
    const signal=vi.mocked(analizarWnba).mock.calls[0][1]!;view.unmount();expect(signal.aborted).toBe(true);
    await act(async()=>resolver(resultado));
  });
  it('Actualizar sincroniza la fuente, no el predictor',async()=>{
    await preparar();vi.mocked(sincronizarCalendarioWnba).mockResolvedValue({comprobacion:{desde:'2026-10-25',hasta:'2027-01-25',comprobado_utc:'2026-10-25',estado:'PARTIDOS_PUBLICADOS',detalle:'3 encuentros',fuentes:[]}});
    fireEvent.click(screen.getByRole('button',{name:'Actualizar'}));
    await waitFor(()=>expect(sincronizarCalendarioWnba).toHaveBeenCalledTimes(1));
    expect(analizarWnba).not.toHaveBeenCalled();
  });
  it.each(['Q1','COMPLETO'] as const)('2020 conserva cuartos y muestra solo total OT N/D al solicitar %s',async mercado=>{
    const parcial:ResultadoWnba={...resultado,mercado,linea:mercado==='Q1'?40.5:160.5,incluye_ot:true,
      temporadas_solicitadas:[{id:'2020',nombre:'2020'}],temporadas_utilizadas:['2020'],
      predicciones:Object.fromEntries(['Q1','Q2','Q3','Q4'].map(q=>[q,{...pred,media_local:20,media_visitante:21,media_total:41,desviacion_total:7}])),
      probabilidades:mercado==='Q1'?{over:.6,under:.4,push:0}:{over:null,under:null,push:null},
      mercados_no_disponibles:{COMPLETO:'Total con OT N/D: requiere 10 casos; disponibles 4. Q1–Q4 calculables.'},
      advertencias:['Total con OT N/D: requiere 10 casos; disponibles 4. Q1–Q4 calculables.']};
    const d=datos();d.catalogo.temporadas=[{id:'2020',nombre:'2020',fases:{REG:132}}];
    vi.mocked(cargarWnba).mockResolvedValue(d);
    vi.mocked(obtenerTemporadasWnba).mockResolvedValue(d.catalogo.temporadas);
    vi.mocked(analizarWnba).mockResolvedValue(parcial);
    render(<MemoryRouter initialEntries={['/baloncesto?liga=wnba&prueba=1']}><ToastsProvider><ModuloWnba/></ToastsProvider></MemoryRouter>);
    await screen.findByRole('combobox',{name:'Equipo Local'});completar();
    await screen.findByRole('button',{name:'2020'});
    fireEvent.change(screen.getByRole('combobox',{name:'Mercado'}),{target:{value:mercado}});
    fireEvent.click(screen.getByRole('button',{name:'Analizar Partido'}));
    await screen.findByRole('heading',{name:'Proyección por periodo'});
    expect(analizarWnba).toHaveBeenCalledWith(expect.objectContaining({temporadas:['2020'],mercado}),expect.any(AbortSignal));
    expect(screen.getByRole('row',{name:/^Q1 /})).toHaveTextContent('41.00');
    const total=screen.getByRole('row',{name:/^COMPLETO/});
    expect(total.querySelectorAll('td')).toHaveLength(4);
    expect([...total.querySelectorAll('td')].every(e=>e.textContent==='N/D')).toBe(true);
    if(mercado==='Q1')expect(screen.getByText('60.0%')).toBeInTheDocument();
    else {
      expect(screen.queryByRole('button',{name:'Guardar en Seguimiento'})).toBeNull();
      expect(screen.queryByRole('img')).toBeNull();
    }
    expect(document.body.textContent).not.toMatch(/NaN|undefined|Infinity/);
  });
});
