/**
 * main.tsx — Punto de entrada de la aplicación
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';
import { ToastsProvider } from './contextos/Toasts';
import { ProveedorConfiguracionUsuario } from './contextos/ConfiguracionUsuario';
import { ProveedorDeporte } from './contextos/DeporteContext';

// Obtener elemento raíz
const contenedorRaiz = document.getElementById('root');

if (!contenedorRaiz) {
  throw new Error('No se encontró el elemento #root en el DOM');
}

// Renderizar aplicación
createRoot(contenedorRaiz).render(
  <StrictMode>
    <ToastsProvider>
      <ProveedorConfiguracionUsuario>
        <ProveedorDeporte>
          <App />
        </ProveedorDeporte>
      </ProveedorConfiguracionUsuario>
    </ToastsProvider>
  </StrictMode>
);
