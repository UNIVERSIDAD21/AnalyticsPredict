import { clienteAPI, extraerMensajeError } from './api';

interface SuscripcionRaw {
  status?: string;
  plan_id?: string;
  updated_at?: string;
}

export interface EstadoPlanUsuario {
  activo: boolean;
  planId: string | null;
  estado: string | null;
  actualizadoEn: string | null;
}

export async function obtenerEstadoPlan(): Promise<EstadoPlanUsuario> {
  try {
    const { data } = await clienteAPI.get('/api/pagos/suscripcion/mia');
    const raw = (data?.data?.subscription ?? null) as SuscripcionRaw | null;

    return {
      activo: !!data?.data?.active,
      planId: raw?.plan_id ?? null,
      estado: raw?.status ?? null,
      actualizadoEn: raw?.updated_at ?? null,
    };
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
