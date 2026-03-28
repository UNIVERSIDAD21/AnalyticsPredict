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
import { ProveedorAuth } from './contextos/AuthContext';
import { ProveedorAccessPolicy } from './contextos/AccessPolicyContext';
import { ProveedorGatePrompt } from './contextos/GatePromptContext';

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
        <ProveedorAuth>
          <ProveedorAccessPolicy>
            <ProveedorGatePrompt>
              <ProveedorDeporte>
                <App />
              </ProveedorDeporte>
            </ProveedorGatePrompt>
          </ProveedorAccessPolicy>
        </ProveedorAuth>
      </ProveedorConfiguracionUsuario>
    </ToastsProvider>
  </StrictMode>
);
