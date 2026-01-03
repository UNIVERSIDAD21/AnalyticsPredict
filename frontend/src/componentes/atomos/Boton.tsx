/**
 * Boton.tsx — Componente de botón futurista
 */

import { ButtonHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

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
  transition-all duration-300
  focus:outline-none
  disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
`;

const estilosTamano: Record<TamanoBoton, string> = {
  sm: 'px-3 py-1.5 text-sm gap-1.5',
  md: 'px-4 py-2.5 text-base gap-2',
  lg: 'px-6 py-3 text-lg gap-2.5',
};

// ══════════════════════════════════════════════════════════════
// COMPONENTE SPINNER
// ══════════════════════════════════════════════════════════════

function SpinnerBoton({ tamano }: { tamano: TamanoBoton }) {
  const sizes = { sm: 14, md: 18, lg: 22 };
  const size = sizes[tamano];

  return (
    <div
      className="relative animate-spin"
      style={{ width: size, height: size }}
    >
      <div
        className="absolute inset-0 rounded-full"
        style={{
          border: '2px solid transparent',
          borderTopColor: 'currentColor',
          borderRightColor: 'currentColor',
        }}
      />
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Botón reutilizable con estilo futurista neón
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

    // Estilos específicos por variante
    const estilosVariante = {
      primario: `
        bg-gradient-to-r from-neon-cyan to-neon-azul text-futurista-negro font-futurista uppercase tracking-wider
        hover:shadow-glow-cyan hover:-translate-y-0.5
      `,
      secundario: `
        bg-transparent text-neon-cyan border border-neon-cyan/30
        hover:bg-neon-cyan/10 hover:border-neon-cyan hover:shadow-glow-cyan
      `,
      fantasma: `
        bg-transparent text-texto-secundario
        hover:bg-futurista-medio hover:text-texto-principal
      `,
      peligro: `
        bg-gradient-to-r from-neon-rojo to-neon-rojo/80 text-white font-futurista uppercase tracking-wider
        hover:shadow-glow-rojo hover:-translate-y-0.5
      `,
    };

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
            <SpinnerBoton tamano={tamano} />
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
