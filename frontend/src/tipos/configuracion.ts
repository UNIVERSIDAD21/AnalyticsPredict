// hace parte del diseño de analisis
/**
 * configuracion.ts — Tipos relacionados con configuración de usuario
 */

import type { ModoDevig, PerfilRiesgo } from './analisis';

export interface BankrollHistorialItem {
  timestamp: string;
  valor: number | null;
}

export interface ConfiguracionUsuario {
  bankroll: number | null;
  perfilRiesgo: PerfilRiesgo;
  modoDevig: ModoDevig;
  capPorApuesta: number;
  capDiario: number;
  stakeMinimo: number;
  bankrollHistorial: BankrollHistorialItem[];
}
