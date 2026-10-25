import { clienteAPI } from "./api";
import type { Mercado, PartidoResumen, Equipo, RespuestaEstadisticasEquipos } from "../tipos";

export interface FormularioWnba {
  equipo_local_id: string;
  equipo_visitante_id: string;
  mercado: Mercado;
  linea: number;
  partido_id?: string;
  temporadas?: string[];
  parciales?: [number, number][];
  modo?: "PREPARTIDO" | "CIERRE_Q1" | "CIERRE_Q2" | "CIERRE_Q3";
  lado?: "OVER" | "UNDER";
  cuota_over?: number;
  cuota_under?: number;
}
export interface PeticionWnba extends FormularioWnba {
  temporadas: string[];
  corte?: string;
  contrato?: "NBA_EQUIVALENTE_V2";
  fases: ("REG" | "POST")[];
  es_prueba: boolean;
  lado_solicitado?: "OVER" | "UNDER";
}
export interface PrediccionWnba {
  observado?: boolean;
  ganador?: { local: number; empate: number; visitante: number };
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
  final_rival?: number;
  ot_rival?: number;
  temporada?: string;
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
  fixture_revision_sha256?: string | null;
  fecha_analisis: string;
  modo: string;
  es_prueba: boolean;
  incluye_ot: boolean;
  calibracion: "SIN_CALIBRAR";
  modelo_version: string;
  lado_solicitado?: "OVER" | "UNDER";
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
  probabilidades: { over: number; under: number; push: number } | { over: null; under: null; push: null };
  mercados_no_disponibles?: Partial<Record<Mercado, string>>;
  politica_muestras?: string;
  base_descompuesta?: { prediccion: PrediccionWnba; probabilidades: { over: number; under: number; push: number }; definicion: string };
  parciales?: [number, number][];
  regulacion?: PrediccionWnba;
  condicionamiento?: { version: string; metodo: string; simulaciones: number; media_base: number[]; media_condicional: number[] };
  ot?: { n: number; metodo: string; media_local: number | null; media_visitante: number | null; hasta: string; partidos_sha256: string };
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
        temporada_resumen?: { nombre:string; n:number; medias_favor:Record<string,number>; media_regulacion:number };
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
      local_total: number; visitante_total: number; local_id: string; visitante_id: string;
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
  temporadas: { id: string; nombre: string; equipos?: string[]; fases: Record<string, number> }[];
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
  const [catalogo, proximos, historial, estadisticas] = await Promise.all([
    clienteAPI.get<CatalogoWnba>("/api/wnba/catalogo", { signal }),
    clienteAPI.get<{ partidos: PartidoResumen[]; comprobacion?: ComprobacionCalendario }>("/api/wnba/partidos", { signal }),
    clienteAPI.get<{ analisis: ResultadoWnba[] }>("/api/wnba/historial", { signal }),
    clienteAPI.get<RespuestaEstadisticasEquipos>("/api/wnba/estadisticas", { signal }),
  ]);
  return { catalogo: catalogo.data, proximos: proximos.data.partidos, comprobacion: proximos.data.comprobacion,
    historial: historial.data.analisis, estadisticas: estadisticas.data };
}
export interface ComprobacionCalendario {
  desde: string; hasta: string; comprobado_utc: string; estado: string; detalle: string; fuentes: { url: string; estado: string }[];
}
export async function obtenerTemporadasWnba(ids: string[]) {
  const { data } = await clienteAPI.get<CatalogoWnba>("/api/wnba/catalogo");
  return data.temporadas.filter(t => !t.equipos || ids.some(id => t.equipos!.includes(id)));
}
export async function obtenerEquiposWnba(): Promise<Equipo[]> {
  const { data } = await clienteAPI.get<CatalogoWnba>("/api/wnba/catalogo");
  return data.equipos.map(e => ({ ...e, nombre_corto: e.nombre, abreviatura: "WNBA" }));
}
export async function estadisticasWnba(temporada?: string | null, signal?: AbortSignal) {
  return (await clienteAPI.get<RespuestaEstadisticasEquipos>("/api/wnba/estadisticas", { params: { temporada_id: temporada }, signal })).data;
}
export async function sincronizarCalendarioWnba(signal?: AbortSignal) {
  return (await clienteAPI.post<{ comprobacion: ComprobacionCalendario }>("/api/wnba/calendario/sincronizar", {}, { signal, timeout: 300000 })).data;
}
export interface EvaluacionCombinadaWnba {
  probabilidad_independiente:number; probabilidad_ajustada:number; factor_correlacion:number;
  valor_esperado_unidad:number; tiene_mismo_partido:boolean; advertencias:string[];
}
export async function evaluarCombinadaWnba(selecciones: import('../tipos').SeleccionCombinadaInput[], signal?: AbortSignal) {
  return (await clienteAPI.post<EvaluacionCombinadaWnba>('/api/wnba/combinadas/evaluar',{selecciones},{signal})).data;
}

export async function analizarWnba(p: PeticionWnba, signal?: AbortSignal) {
  return (
    await clienteAPI.post<{ resultado: ResultadoWnba }>(
      "/api/wnba/analizar",
      { ...p, contrato: "NBA_EQUIVALENTE_V2" },
      { signal },
    )
  ).data.resultado;
}
