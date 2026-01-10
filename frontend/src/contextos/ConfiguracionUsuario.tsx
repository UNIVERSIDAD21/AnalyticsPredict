/**
 * ConfiguracionUsuario.tsx — Contexto global para configuración de usuario
 */

import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import type { ConfiguracionUsuario, BankrollHistorialItem } from '../tipos';

// ══════════════════════════════════════════════════════════════
// CONSTANTES
// ══════════════════════════════════════════════════════════════

const STORAGE_KEY = 'configuracionUsuario';

const CONFIGURACION_POR_DEFECTO: ConfiguracionUsuario = {
  bankroll: null,
  perfilRiesgo: 'MEDIO',
  modoDevig: 'estimado',
  capPorApuesta: 2,
  capDiario: 10,
  stakeMinimo: 0,
  bankrollHistorial: [],
};

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

function normalizarNumero(valor: unknown, fallback: number): number {
  if (typeof valor !== 'number' || !isFinite(valor)) {
    return fallback;
  }
  return valor;
}

function normalizarBankroll(valor: unknown): number | null {
  if (valor === null) return null;
  if (typeof valor === 'number' && isFinite(valor)) {
    return valor;
  }
  return null;
}

function normalizarHistorial(historial: unknown): BankrollHistorialItem[] {
  if (!Array.isArray(historial)) return [];
  return historial.filter((item): item is BankrollHistorialItem => {
    if (!item || typeof item !== 'object') return false;
    const registro = item as BankrollHistorialItem;
    const timestampValido = typeof registro.timestamp === 'string';
    const valorValido =
      registro.valor === null || (typeof registro.valor === 'number' && isFinite(registro.valor));
    return timestampValido && valorValido;
  });
}

function normalizarConfiguracion(datos: unknown): ConfiguracionUsuario {
  if (!datos || typeof datos !== 'object') {
    return CONFIGURACION_POR_DEFECTO;
  }

  const config = datos as Partial<ConfiguracionUsuario>;

  return {
    bankroll: normalizarBankroll(config.bankroll),
    perfilRiesgo:
      config.perfilRiesgo === 'CONSERVADOR' ||
      config.perfilRiesgo === 'MEDIO' ||
      config.perfilRiesgo === 'AGRESIVO'
        ? config.perfilRiesgo
        : CONFIGURACION_POR_DEFECTO.perfilRiesgo,
    modoDevig:
      config.modoDevig === 'estricto' || config.modoDevig === 'estimado'
        ? config.modoDevig
        : CONFIGURACION_POR_DEFECTO.modoDevig,
    capPorApuesta: normalizarNumero(config.capPorApuesta, CONFIGURACION_POR_DEFECTO.capPorApuesta),
    capDiario: normalizarNumero(config.capDiario, CONFIGURACION_POR_DEFECTO.capDiario),
    stakeMinimo: normalizarNumero(config.stakeMinimo, CONFIGURACION_POR_DEFECTO.stakeMinimo),
    bankrollHistorial: normalizarHistorial(config.bankrollHistorial),
  };
}

function leerConfiguracion(): ConfiguracionUsuario {
  if (typeof window === 'undefined') {
    return CONFIGURACION_POR_DEFECTO;
  }

  try {
    const data = window.localStorage.getItem(STORAGE_KEY);
    if (!data) return CONFIGURACION_POR_DEFECTO;
    const parsed = JSON.parse(data) as unknown;
    return normalizarConfiguracion(parsed);
  } catch (error) {
    return CONFIGURACION_POR_DEFECTO;
  }
}

function guardarConfiguracionLocal(configuracion: ConfiguracionUsuario) {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(configuracion));
  } catch (error) {
    // Silencio errores de storage (quota, modo privado)
  }
}

// ══════════════════════════════════════════════════════════════
// CONTEXTO
// ══════════════════════════════════════════════════════════════

interface ConfiguracionUsuarioContexto {
  configuracion: ConfiguracionUsuario;
  actualizarConfiguracion: (configuracion: ConfiguracionUsuario) => void;
}

const ConfiguracionUsuarioContext = createContext<ConfiguracionUsuarioContexto | undefined>(
  undefined
);

export function ProveedorConfiguracionUsuario({ children }: { children: ReactNode }) {
  const [configuracion, setConfiguracion] = useState<ConfiguracionUsuario>(() => leerConfiguracion());

  const actualizarConfiguracion = useCallback((nueva: ConfiguracionUsuario) => {
    setConfiguracion(nueva);
    guardarConfiguracionLocal(nueva);
  }, []);

  const valor = useMemo(
    () => ({
      configuracion,
      actualizarConfiguracion,
    }),
    [configuracion, actualizarConfiguracion]
  );

  return (
    <ConfiguracionUsuarioContext.Provider value={valor}>
      {children}
    </ConfiguracionUsuarioContext.Provider>
  );
}

export function useConfiguracionUsuario() {
  const contexto = useContext(ConfiguracionUsuarioContext);
  if (!contexto) {
    throw new Error('useConfiguracionUsuario debe usarse dentro de ProveedorConfiguracionUsuario');
  }
  return contexto;
}
