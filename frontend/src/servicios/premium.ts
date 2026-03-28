import { clienteAPI, extraerMensajeError } from './api';

export interface CapasPremiumDepth {
  tier: 'PREMIUM';
  depth_layers: string[];
  message: string;
}

export async function obtenerCapasPremiumDepth(): Promise<CapasPremiumDepth> {
  try {
    const { data } = await clienteAPI.get('/api/premium/capas-depth');
    return data?.data as CapasPremiumDepth;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
