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
  type ResultadoWnba,
} from "../../servicios/wnba";
import {
  obtenerTemporadasEquipos,
  obtenerPartidosProximos,
} from "../../servicios";

vi.mock("../../servicios/wnba", () => ({
  analizarWnba: vi.fn(),
  cargarWnba: vi.fn(),
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
    pasados: [],
    historial: [],
  };
}
async function preparar(disponible = true) {
  vi.mocked(cargarWnba).mockResolvedValue(datos(disponible));
  vi.mocked(analizarWnba).mockResolvedValue(resultado);
  const view = render(<ModuloWnba />);
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

describe("WNBA con formulario real compartido", () => {
  it("envía temporadas, UUID propios, corte, fases y línea sin consultas NBA ni modo en vivo", async () => {
    await preparar();
    completar();
    expect(
      screen.queryByRole("combobox", { name: "Modo de análisis" }),
    ).toBeNull();
    expect(
      screen.getByText(/No hay próximos encuentros WNBA/),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("2025 (200 REG)"));
    fireEvent.change(screen.getByLabelText("Corte WNBA"), {
      target: { value: "2026-09-01" },
    });
    fireEvent.click(
      screen.getByLabelText(/Identificar como análisis de prueba/),
    );
    fireEvent.click(screen.getByRole("button", { name: "Analizar Partido" }));
    await screen.findByRole("region", { name: "Resultado WNBA" });
    expect(analizarWnba).toHaveBeenCalledWith(
      expect.objectContaining({
        equipo_local_id: "liberty",
        equipo_visitante_id: "aces",
        temporadas: ["2026"],
        corte: "2026-09-01",
        fases: ["REG"],
        linea: 160,
        mercado: "COMPLETO",
        es_prueba: true,
      }),
      expect.any(AbortSignal),
    );
    expect(obtenerTemporadasEquipos).not.toHaveBeenCalled();
    expect(obtenerPartidosProximos).not.toHaveBeenCalled();
    expect(screen.getAllByText("68.00 %").length).toBeGreaterThan(0);
    expect(screen.getAllByText("2.00 %").length).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: /Guardar selección en Bitácora/ }),
    ).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Historial WNBA (1)" }));
    expect(
      screen.getByRole("region", { name: "Historial WNBA" }),
    ).toBeInTheDocument();
    expect(analizarWnba).toHaveBeenCalledTimes(1);
  });
  it("limpia resultados al cambiar temporadas y permite recuperar un modelo ausente", async () => {
    await preparar(false);
    expect(
      screen.getByRole("button", { name: "Analizar Partido" }),
    ).toBeDisabled();
    expect(screen.getByText(/Modelo WNBA no disponible/)).toBeInTheDocument();
    vi.mocked(cargarWnba).mockResolvedValue(datos());
    fireEvent.click(screen.getByRole("button", { name: /Actualizar estado/ }));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Analizar Partido" }),
      ).not.toBeDisabled(),
    );
    completar();
    fireEvent.click(screen.getByRole("button", { name: "Analizar Partido" }));
    await screen.findByRole("region", { name: "Resultado WNBA" });
    fireEvent.click(screen.getByLabelText("2025 (200 REG)"));
    expect(screen.queryByRole("region", { name: "Resultado WNBA" })).toBeNull();
  });
  it("aborta e ignora una respuesta tardía al desmontar y volver a la liga", async () => {
    const view = await preparar();
    let resolver!: (r: ResultadoWnba) => void;
    vi.mocked(analizarWnba).mockImplementationOnce(
      () =>
        new Promise((r) => {
          resolver = r;
        }),
    );
    completar();
    fireEvent.click(screen.getByRole("button", { name: "Analizar Partido" }));
    const signal = vi.mocked(analizarWnba).mock.calls[0][1]!;
    view.unmount();
    expect(signal.aborted).toBe(true);
    render(<ModuloWnba />);
    await screen.findByRole("combobox", { name: "Equipo Local" });
    await act(async () => resolver(resultado));
    expect(screen.queryByRole("region", { name: "Resultado WNBA" })).toBeNull();
    expect(screen.getByRole("combobox", { name: "Equipo Local" })).toHaveValue(
      "",
    );
  });
});
