/**
 * Toasts.tsx — Contexto global para notificaciones tipo toast
 */

import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { Toast, TipoToast } from '../componentes/atomos/Toast';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

export interface DatosToast {
  id: string;
  titulo: string;
  mensaje: string;
  tipo: TipoToast;
}

interface ToastsContexto {
  agregarToast: (toast: Omit<DatosToast, 'id'>) => void;
  quitarToast: (id: string) => void;
}

const ToastsContext = createContext<ToastsContexto | undefined>(undefined);

const DURACION_TOAST = 4500;

function generarIdToast() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

// ══════════════════════════════════════════════════════════════
// PROVIDER
// ══════════════════════════════════════════════════════════════

export function ToastsProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<DatosToast[]>([]);

  const quitarToast = useCallback((id: string) => {
    setToasts((previas) => previas.filter((toast) => toast.id !== id));
  }, []);

  const agregarToast = useCallback((toast: Omit<DatosToast, 'id'>) => {
    const id = generarIdToast();
    setToasts((previas) => [...previas, { ...toast, id }]);

    window.setTimeout(() => {
      setToasts((previas) => previas.filter((item) => item.id !== id));
    }, DURACION_TOAST);
  }, []);

  const valor = useMemo(
    () => ({
      agregarToast,
      quitarToast,
    }),
    [agregarToast, quitarToast]
  );

  return (
    <ToastsContext.Provider value={valor}>
      {children}
      <div className="fixed top-6 right-6 z-50 flex flex-col gap-3 w-[min(90vw,360px)]">
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            titulo={toast.titulo}
            mensaje={toast.mensaje}
            tipo={toast.tipo}
            onCerrar={() => quitarToast(toast.id)}
          />
        ))}
      </div>
    </ToastsContext.Provider>
  );
}

// ══════════════════════════════════════════════════════════════
// HOOK
// ══════════════════════════════════════════════════════════════

export function useToasts() {
  const contexto = useContext(ToastsContext);

  if (!contexto) {
    throw new Error('useToasts debe usarse dentro de un ToastsProvider');
  }

  return contexto;
}
