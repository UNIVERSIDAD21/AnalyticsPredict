import { clienteAPI, extraerMensajeError } from './api';

export interface PreferenciasNotificaciones {
  email_habilitado: boolean;
  alertas_partidos: boolean;
  alertas_suscripcion: boolean;
  resumen_semanal: boolean;
}

export interface EstadoPreferenciasNotificaciones {
  preferencias: PreferenciasNotificaciones;
  updated_at: string | null;
}

const DEFAULT_PREFS: PreferenciasNotificaciones = {
  email_habilitado: true,
  alertas_partidos: true,
  alertas_suscripcion: true,
  resumen_semanal: false,
};

function normalizarPreferencias(raw: unknown): PreferenciasNotificaciones {
  const data = (raw ?? {}) as Record<string, unknown>;
  return {
    email_habilitado: typeof data.email_habilitado === 'boolean' ? data.email_habilitado : DEFAULT_PREFS.email_habilitado,
    alertas_partidos: typeof data.alertas_partidos === 'boolean' ? data.alertas_partidos : DEFAULT_PREFS.alertas_partidos,
    alertas_suscripcion:
      typeof data.alertas_suscripcion === 'boolean' ? data.alertas_suscripcion : DEFAULT_PREFS.alertas_suscripcion,
    resumen_semanal: typeof data.resumen_semanal === 'boolean' ? data.resumen_semanal : DEFAULT_PREFS.resumen_semanal,
  };
}

export async function obtenerPreferenciasNotificaciones(): Promise<EstadoPreferenciasNotificaciones> {
  try {
    const { data } = await clienteAPI.get('/api/notificaciones/preferencias');
    return {
      preferencias: normalizarPreferencias(data?.data?.preferencias),
      updated_at: (data?.data?.updated_at as string | null | undefined) ?? null,
    };
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function guardarPreferenciasNotificaciones(
  preferencias: PreferenciasNotificaciones
): Promise<EstadoPreferenciasNotificaciones> {
  try {
    const { data } = await clienteAPI.put('/api/notificaciones/preferencias', preferencias);
    return {
      preferencias: normalizarPreferencias(data?.data?.preferencias),
      updated_at: (data?.data?.updated_at as string | null | undefined) ?? null,
    };
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function enviarPruebaNotificacion(tipo: keyof PreferenciasNotificaciones = 'alertas_partidos') {
  try {
    const { data } = await clienteAPI.post('/api/notificaciones/enviar-prueba', { tipo });
    return data?.data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
