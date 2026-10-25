import { clienteAPI } from "./api";
import type { Mercado, PartidoResumen } from "../tipos";

export interface FormularioWnba {
  equipo_local_id: string;
  equipo_visitante_id: string;
  mercado: Mercado;
  linea: number;
  partido_id?: string;
  cuota_over?: number;
  cuota_under?: number;
}
export interface PeticionWnba extends FormularioWnba {
  temporadas: string[];
  corte: string;
  fases: ("REG" | "POST")[];
  es_prueba: boolean;
}
export interface PrediccionWnba {
  media_local: number;
  media_visitante: number;
  media_total: number;
  desviacion_total: number;
  varianza_total: number;
  intervalo_80_raw: [number, number];
}
export interface PartidoWnbaContexto {
  id: string;
  fecha: string;
  rival: string;
  como_local: boolean;
  cuartos: number[];
  cuartos_rival: number[];
  regulacion: number;
  regulacion_rival: number;
  ot: number;
  final: number;
  resultado: string;
}
export interface EvaluacionWnba {
  candidato_version: string;
  limitacion: string;
  train: { n: number; desde: string; hasta: string };
  cal_seleccion: { n: number };
  cal_dispersion: { n: number };
  evaluacion: {
    partidos: number;
    analizados: number;
    abstenciones: number;
    cobertura: number;
    desde: string;
    hasta: string;
    mercados: Record<
      string,
      {
        n: number;
        mae: number;
        mae_referencia: number;
        brier_multiclase: number;
        brier_referencia: number;
        log_loss: number;
        brier_con_push: number;
        linea_entera: number;
        push_observados: number;
        cobertura_intervalo80: number;
        calibracion_bins: {
          desde: number;
          hasta: number;
          n: number;
          probabilidad_media: number | null;
          frecuencia_observada: number | null;
        }[];
      }
    >;
  };
}
export interface ResultadoWnba {
  analisis_id: string;
  dominio: "wnba";
  equipo_local: string;
  equipo_visitante: string;
  equipo_local_id: string;
  equipo_visitante_id: string;
  partido_id: string | null;
  fecha_partido: string | null;
  fixture_fuente: string | null;
  fecha_analisis: string;
  modo: string;
  es_prueba: boolean;
  incluye_ot: false;
  calibracion: "SIN_CALIBRAR";
  modelo_version: string;
  publicacion_version: string;
  dataset_sha256: string;
  corte_exclusivo: string;
  politica_corte: string;
  temporadas_solicitadas: { id: string; nombre: string }[];
  temporadas_utilizadas: string[];
  fases_utilizadas: string[];
  ultimo_final_bd: string | null;
  ultimo_dato_utilizado: string;
  mercado: Mercado;
  linea: number;
  semivida_dias: number | null;
  muestras: {
    local: number;
    visitante: number;
    efectivas_local: number;
    efectivas_visitante: number;
    partidos: number;
  };
  dispersion: {
    origen: string;
    train_n: number;
    seleccion_n: number;
    dispersión_n: number;
    desde: string;
  };
  predicciones: Record<string, PrediccionWnba>;
  probabilidades: { over: number; under: number; push: number };
  ganador_regulacion: { local: number; empate: number; visitante: number };
  advertencias: string[];
  guardar_bitacora_habilitado: boolean;
  motivo_bitacora: string;
  valor: Record<
    "over" | "under",
    { cuota: number | null; ev_sin_calibrar: number | null }
  >;
  contexto: {
    uso: string;
    equipos: Record<
      string,
      {
        n: number;
        media_regulacion: number | null;
        recientes: PartidoWnbaContexto[];
      }
    >;
    h2h: {
      id: string;
      fecha: string;
      local: string;
      visitante: string;
      y: number[];
    }[];
  };
}
export interface CatalogoWnba {
  equipos: {
    id: string;
    nombre: string;
    muestras: number;
    elegible: boolean;
  }[];
  temporadas: { id: string; nombre: string; fases: Record<string, number> }[];
  ultimo_final_bd: string | null;
  fuente_n: number;
  finales_n: number;
  elegibles_n: number;
  cobertura: string;
  modelo: {
    disponible: boolean;
    desactualizado?: boolean;
    motivo?: string;
    version?: string;
    ultimo_snapshot?: string;
    validacion?: EvaluacionWnba;
  };
}

export async function cargarWnba(signal?: AbortSignal) {
  const [catalogo, proximos, pasados, historial] = await Promise.all([
    clienteAPI.get<CatalogoWnba>("/api/wnba/catalogo", { signal }),
    clienteAPI.get<{ partidos: PartidoResumen[] }>("/api/wnba/partidos", {
      signal,
    }),
    clienteAPI.get<{ partidos: PartidoResumen[] }>(
      "/api/wnba/partidos?historicos=true&limite=50",
      { signal },
    ),
    clienteAPI.get<{ analisis: ResultadoWnba[] }>("/api/wnba/historial", {
      signal,
    }),
  ]);
  return {
    catalogo: catalogo.data,
    proximos: proximos.data.partidos,
    pasados: pasados.data.partidos,
    historial: historial.data.analisis,
  };
}
export async function analizarWnba(p: PeticionWnba, signal?: AbortSignal) {
  return (
    await clienteAPI.post<{ resultado: ResultadoWnba }>(
      "/api/wnba/analizar",
      p,
      { signal },
    )
  ).data.resultado;
}
