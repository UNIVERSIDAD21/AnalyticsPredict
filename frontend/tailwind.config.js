/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Paleta Futurista
        futurista: {
          negro: 'var(--ap-fondo)',
          oscuro: 'var(--ap-superficie)',
          medio: 'var(--ap-elevado)',
          claro: '#415a77',
        },
        // Acentos Neón
        neon: {
          cyan: 'var(--ap-acento)',
          magenta: '#ff00ff',
          purpura: '#7b2cbf',
          verde: 'var(--ap-exito)',
          rojo: 'var(--ap-peligro)',
          azul: 'var(--ap-acento)',
          amarillo: 'var(--ap-aviso)',
        },
        // Texto
        texto: {
          principal: 'var(--ap-texto)',
          secundario: 'var(--ap-secundario)',
          terciario: 'var(--ap-terciario)',
        },
        // Over/Under Neón
        over: {
          claro: 'rgba(0, 255, 136, 0.15)',
          medio: 'var(--ap-exito)',
          oscuro: '#00cc6a',
          glow: 'rgba(0, 255, 136, 0.4)',
        },
        under: {
          claro: 'rgba(255, 0, 85, 0.15)',
          medio: 'var(--ap-peligro)',
          oscuro: '#cc0044',
          glow: 'rgba(255, 0, 85, 0.4)',
        },
        // Estados
        exito: {
          50: 'rgba(0, 255, 136, 0.15)',
          500: 'var(--ap-exito)',
          600: '#00cc6a',
        },
        advertencia: {
          50: 'rgba(255, 200, 0, 0.15)',
          500: 'var(--ap-aviso)',
          600: '#e6b400',
        },
        error: {
          50: 'rgba(255, 0, 85, 0.15)',
          500: 'var(--ap-peligro)',
          600: '#cc0044',
        },
        // Legacy (para compatibilidad)
        nba: {
          azul: 'var(--ap-acento)',
          rojo: 'var(--ap-peligro)',
          blanco: 'var(--ap-texto)',
          gris: {
            50: 'var(--ap-fondo)',
            100: 'var(--ap-superficie)',
            200: 'var(--ap-elevado)',
            300: '#415a77',
            400: 'var(--ap-terciario)',
            500: 'var(--ap-secundario)',
            600: '#a8b2d1',
            700: '#ccd6f6',
            800: '#e6f1ff',
            900: 'var(--ap-texto)',
          }
        },
      },
      fontFamily: {
        futurista: ['system-ui', 'sans-serif'],
        principal: ['system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'monospace'],
        sans: ['system-ui', 'sans-serif'],
      },
      boxShadow: {
        'tarjeta': '0 0 20px rgba(0, 245, 255, 0.1)',
        'tarjeta-hover': '0 0 30px rgba(0, 245, 255, 0.2)',
        'elevada': '0 0 40px rgba(0, 245, 255, 0.15)',
        'glow-cyan': '0 0 20px rgba(0, 245, 255, 0.5), 0 0 40px rgba(0, 245, 255, 0.3)',
        'glow-magenta': '0 0 20px rgba(255, 0, 255, 0.5), 0 0 40px rgba(255, 0, 255, 0.3)',
        'glow-verde': '0 0 20px rgba(0, 255, 136, 0.5), 0 0 40px rgba(0, 255, 136, 0.3)',
        'glow-rojo': '0 0 20px rgba(255, 0, 85, 0.5), 0 0 40px rgba(255, 0, 85, 0.3)',
        'inner-glow': 'inset 0 0 20px rgba(0, 245, 255, 0.1)',
      },
      backgroundImage: {
        'gradiente-principal': 'linear-gradient(135deg, #0a0a0f 0%, #0d1b2a 50%, #1b263b 100%)',
        'gradiente-tarjeta': 'linear-gradient(135deg, rgba(27, 38, 59, 0.8) 0%, rgba(13, 27, 42, 0.9) 100%)',
        'gradiente-boton': 'linear-gradient(135deg, #00f5ff 0%, #00d4ff 100%)',
        'gradiente-over': 'linear-gradient(135deg, rgba(0, 255, 136, 0.2) 0%, rgba(0, 255, 136, 0.05) 100%)',
        'gradiente-under': 'linear-gradient(135deg, rgba(255, 0, 85, 0.2) 0%, rgba(255, 0, 85, 0.05) 100%)',
      },
      animation: {
        'pulso-neon': 'pulsoNeon 2s ease-in-out infinite',
        'entrada': 'fadeInUp 0.5s ease-out',
        'deslizar-arriba': 'slideUp 0.4s ease-out',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
        'barra-carga': 'barraCarga 1.5s ease-out forwards',
        'scan-line': 'scanLine 3s linear infinite',
      },
      keyframes: {
        pulsoNeon: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(0, 245, 255, 0.5)' },
          '50%': { boxShadow: '0 0 40px rgba(0, 245, 255, 0.8), 0 0 60px rgba(0, 245, 255, 0.4)' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        glowPulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        barraCarga: {
          '0%': { width: '0%' },
          '100%': { width: 'var(--barra-width)' },
        },
        scanLine: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
};
