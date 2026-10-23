/** Contrato de explicación propio de cada deporte; no presupone certificación. */
export interface AnalisisIntegral {
  version: string; deporte: 'euroliga' | 'futbol'; metodo: string; unidad: string;
  mercado: string; linea: number; lado: 'OVER' | 'UNDER';
  probabilidades: { over: number | null; under: number | null; push: number | null };
  cuotas: { over: number | null; under: number | null };
  ganador: { local: number | null; empate: number | null; visitante: number | null; marcador: string; definicion: string };
  periodos: { periodo: string; local: number | null; visitante: number | null; total: number | null; desviacion: number | null; observado: boolean }[];
  comparacion: { media_base: number | null; media_ajustada: number | null;
    probabilidades_base: AnalisisIntegral['probabilidades']; probabilidades_ajustadas: AnalisisIntegral['probabilidades'] };
  ajustes: { factor: string; delta: number | null; unidad: string; descripcion: string; aplicado: boolean }[];
  razones: string[]; muestras: Record<string, number>; nota_periodos: string;
}
