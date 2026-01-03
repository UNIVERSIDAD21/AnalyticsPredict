/**
 * Boton.tsx — Componente de botón reutilizable
 */

import { ButtonHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

type VarianteBoton = 'primario' | 'secundario' | 'fantasma' | 'peligro';
type TamanoBoton = 'sm' | 'md' | 'lg';

interface PropsBoton extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Variante visual del botón */
  variante?: VarianteBoton;
  /** Tamaño del botón */
  tamano?: TamanoBoton;
  /** Muestra spinner de carga */
  cargando?: boolean;
  /** Texto a mostrar durante carga */
  textoCargando?: string;
  /** Icono a mostrar antes del texto */
  iconoInicio?: React.ReactNode;
  /** Icono a mostrar después del texto */
  iconoFin?: React.ReactNode;
  /** Ocupa todo el ancho disponible */
  anchoCompleto?: boolean;
}

// ══════════════════════════════════════════════════════════════
// ESTILOS
// ══════════════════════════════════════════════════════════════

const estilosBase = `
  inline-flex items-center justify-center font-semibold rounded-lg
  transition-all duration-200
  focus:outline-none focus:ring-2 focus:ring-offset-2
  disabled:opacity-50 disabled:cursor-not-allowed
`;

const estilosVariante: Record<VarianteBoton, string> = {
  primario: `
    bg-nba-azul text-white
    hover:bg-nba-azul/90
    focus:ring-nba-azul
  `,
  secundario: `
    bg-white text-nba-gris-700 border border-nba-gris-300
    hover:bg-nba-gris-50
    focus:ring-nba-azul
  `,
  fantasma: `
    bg-transparent text-nba-gris-700
    hover:bg-nba-gris-100
    focus:ring-nba-azul
  `,
  peligro: `
    bg-error-500 text-white
    hover:bg-error-600
    focus:ring-error-500
  `,
};

const estilosTamano: Record<TamanoBoton, string> = {
  sm: 'px-3 py-1.5 text-sm gap-1.5',
  md: 'px-4 py-2.5 text-base gap-2',
  lg: 'px-6 py-3 text-lg gap-2.5',
};

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Botón reutilizable con múltiples variantes y estados
 */
export const Boton = forwardRef<HTMLButtonElement, PropsBoton>(
  (
    {
      variante = 'primario',
      tamano = 'md',
      cargando = false,
      textoCargando,
      iconoInicio,
      iconoFin,
      anchoCompleto = false,
      className,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const estaDeshabilitado = disabled || cargando;

    return (
      <button
        ref={ref}
        className={clsx(
          estilosBase,
          estilosVariante[variante],
          estilosTamano[tamano],
          anchoCompleto && 'w-full',
          className
        )}
        disabled={estaDeshabilitado}
        {...props}
      >
        {cargando ? (
          <>
            <Loader2 className="animate-spin" size={tamano === 'sm' ? 16 : tamano === 'lg' ? 24 : 20} />
            {textoCargando || children}
          </>
        ) : (
          <>
            {iconoInicio}
            {children}
            {iconoFin}
          </>
        )}
      </button>
    );
  }
);

Boton.displayName = 'Boton';
