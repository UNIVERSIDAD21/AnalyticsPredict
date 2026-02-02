/**
 * DeporteContext.tsx — Contexto para manejar el deporte activo (NBA o Fútbol)
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  type ReactNode,
} from 'react';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

/**
 * Deportes disponibles en la aplicación
 */
export type Deporte = 'NBA' | 'FUTBOL';

/**
 * Tipo del contexto de deporte
 */
interface DeporteContextType {
  /** Deporte actualmente seleccionado */
  deporteActivo: Deporte;

  /** Función para cambiar el deporte activo */
  cambiarDeporte: (deporte: Deporte) => void;

  /** Helper: ¿Es NBA el deporte activo? */
  esNBA: boolean;

  /** Helper: ¿Es Fútbol el deporte activo? */
  esFutbol: boolean;

  /** Ruta base según el deporte ('/' para NBA, '/futbol' para Fútbol) */
  rutaBase: string;
}

// ══════════════════════════════════════════════════════════════
// CONSTANTES
// ══════════════════════════════════════════════════════════════

const STORAGE_KEY = 'deporte_activo';

/**
 * Rutas base por deporte
 */
const RUTAS_BASE: Record<Deporte, string> = {
  NBA: '/',
  FUTBOL: '/futbol',
};

/**
 * Detecta el deporte desde la URL actual
 */
function detectarDeporteDesdeURL(): Deporte {
  const pathname = window.location.pathname;
  if (pathname.startsWith('/futbol')) {
    return 'FUTBOL';
  }
  return 'NBA';
}

/**
 * Obtiene el deporte guardado o detecta desde URL
 */
function obtenerDeporteInicial(): Deporte {
  // Primero verificar la URL
  const deporteURL = detectarDeporteDesdeURL();
  if (deporteURL === 'FUTBOL') {
    return 'FUTBOL';
  }

  // Si no está en ruta de fútbol, verificar localStorage
  try {
    const guardado = localStorage.getItem(STORAGE_KEY);
    if (guardado === 'NBA' || guardado === 'FUTBOL') {
      return guardado;
    }
  } catch {
    // localStorage no disponible
  }

  return 'NBA';
}

// ══════════════════════════════════════════════════════════════
// CONTEXTO
// ══════════════════════════════════════════════════════════════

const DeporteContext = createContext<DeporteContextType | undefined>(undefined);

// ══════════════════════════════════════════════════════════════
// PROVEEDOR
// ══════════════════════════════════════════════════════════════

interface ProveedorDeporteProps {
  children: ReactNode;
}

/**
 * Proveedor del contexto de deporte
 */
export function ProveedorDeporte({ children }: ProveedorDeporteProps) {
  const [deporteActivo, setDeporteActivo] = useState<Deporte>(obtenerDeporteInicial);

  // Escuchar cambios en la URL
  useEffect(() => {
    const manejarCambioRuta = () => {
      const deporteURL = detectarDeporteDesdeURL();
      setDeporteActivo(deporteURL);
    };

    window.addEventListener('popstate', manejarCambioRuta);
    return () => window.removeEventListener('popstate', manejarCambioRuta);
  }, []);

  // Persistir preferencia
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, deporteActivo);
    } catch {
      // localStorage no disponible
    }
  }, [deporteActivo]);

  /**
   * Cambia el deporte activo y navega a la ruta base correspondiente
   */
  const cambiarDeporte = useCallback((deporte: Deporte) => {
    if (deporte === deporteActivo) return;

    setDeporteActivo(deporte);

    // Navegar a la ruta base del deporte
    const rutaDestino = RUTAS_BASE[deporte];
    if (window.location.pathname !== rutaDestino) {
      window.history.pushState({}, '', rutaDestino);
      window.dispatchEvent(new PopStateEvent('popstate'));
    }
  }, [deporteActivo]);

  /**
   * Valores computados
   */
  const valor = useMemo<DeporteContextType>(
    () => ({
      deporteActivo,
      cambiarDeporte,
      esNBA: deporteActivo === 'NBA',
      esFutbol: deporteActivo === 'FUTBOL',
      rutaBase: RUTAS_BASE[deporteActivo],
    }),
    [deporteActivo, cambiarDeporte]
  );

  return (
    <DeporteContext.Provider value={valor}>{children}</DeporteContext.Provider>
  );
}

// ══════════════════════════════════════════════════════════════
// HOOK
// ══════════════════════════════════════════════════════════════

/**
 * Hook para acceder al contexto de deporte
 */
export function useDeporte(): DeporteContextType {
  const contexto = useContext(DeporteContext);

  if (!contexto) {
    throw new Error('useDeporte debe usarse dentro de un ProveedorDeporte');
  }

  return contexto;
}

/**
 * Hook para navegar dentro del deporte actual
 */
export function useNavegacionDeporte() {
  const { deporteActivo, rutaBase } = useDeporte();

  /**
   * Navega a una subruta del deporte actual
   */
  const navegar = useCallback(
    (subruta: string) => {
      let rutaCompleta: string;

      if (deporteActivo === 'NBA') {
        rutaCompleta = subruta.startsWith('/') ? subruta : `/${subruta}`;
      } else {
        // Para fútbol, agregar prefijo /futbol
        const subrutaLimpia = subruta.startsWith('/') ? subruta.slice(1) : subruta;
        rutaCompleta = subrutaLimpia ? `${rutaBase}/${subrutaLimpia}` : rutaBase;
      }

      if (window.location.pathname !== rutaCompleta) {
        window.history.pushState({}, '', rutaCompleta);
        window.dispatchEvent(new PopStateEvent('popstate'));
      }
    },
    [deporteActivo, rutaBase]
  );

  /**
   * Construye una URL completa para el deporte actual
   */
  const construirURL = useCallback(
    (subruta: string): string => {
      if (deporteActivo === 'NBA') {
        return subruta.startsWith('/') ? subruta : `/${subruta}`;
      }
      const subrutaLimpia = subruta.startsWith('/') ? subruta.slice(1) : subruta;
      return subrutaLimpia ? `${rutaBase}/${subrutaLimpia}` : rutaBase;
    },
    [deporteActivo, rutaBase]
  );

  return { navegar, construirURL };
}
