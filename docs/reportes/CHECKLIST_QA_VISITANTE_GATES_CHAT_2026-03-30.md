# CHECKLIST QA — Visitante real + Gate por acción + Chat fuera de alcance

Fecha: 2026-03-30  
Responsable: UNIVERSIDAD21  
Contexto: verificación manual rápida posterior al ajuste de runtime alineado con `05_PLAN_EJECUCION_TIERS_VISITANTE_PREMIUM.md`.

---

## Objetivo de validación

Confirmar en runtime que:

1. `/` funciona como modo visitante real (sin login forzado al entrar).  
2. El login aparece solo al intentar una acción protegida (gate por acción).  
3. Chat está fuera de alcance (oculto/deshabilitado).

---

## Precondiciones

- Frontend en la versión con commit `409c4bd`.
- Navegador en ventana incógnita (sin sesión) para pruebas de visitante.
- Backend con `CHAT_ENABLED=false` (si se valida también API).

---

## Checklist A — Flujo visitante en `/`

### A1. Entrada pública sin rebote a login
- [ ] Abrir `/` en incógnito.
- [ ] Verificar que carga el **Centro Analítico**.
- [ ] Verificar que **NO** redirige automáticamente a `/login`.

**Resultado esperado:** visitante permanece en `/` y puede explorar contenido público.

---

## Checklist B — Gate por acción protegida (sin login inmediato)

### B1. CTA de análisis protegido
- [ ] En `/`, pulsar CTA de análisis (p.ej. “Abrir análisis completo” / “Intentar análisis completo”).
- [ ] Verificar aparición de modal/prompt de gate.
- [ ] Verificar que no hay navegación directa automática sin interacción del usuario.

**Resultado esperado:** se muestra gate y solo luego (si usuario decide) se va a login.

### B2. CTA de bitácora protegida
- [ ] En `/`, pulsar CTA de bitácora (p.ej. “Guardar en bitácora personal” / “Intentar bitácora personal”).
- [ ] Verificar gate por acción.

**Resultado esperado:** gate activo para acción protegida de bitácora.

### B3. CTA invitado en encabezado
- [ ] En encabezado, pulsar “Desbloquear con cuenta”.
- [ ] Verificar que se activa flujo de gate por capacidad protegida.

**Resultado esperado:** login no aparece “porque sí” al entrar; aparece por intento de acción protegida.

---

## Checklist C — Chat fuera de alcance

### C1. UI/Navegación
- [ ] Verificar que no existe botón de chat en navegación principal.
- [ ] Ir manualmente a `/chat`.
- [ ] Confirmar redirección a `/`.

**Resultado esperado:** chat no visible ni navegable como módulo activo.

### C2. API (opcional, hardening)
- [ ] Consultar endpoints `/api/chat/*` en entorno objetivo.
- [ ] Confirmar no exposición cuando `CHAT_ENABLED=false`.

**Resultado esperado:** endpoints de chat no operativos en fase actual.

---

## Criterio de aceptación final

Se considera **OK** si:

- [ ] A = 100% cumplido
- [ ] B = 100% cumplido
- [ ] C = 100% cumplido

Si algún punto falla:
- documentar evidencia (ruta exacta + captura/log),
- abrir corrección puntual,
- repetir checklist completo.

---

## Registro de ejecución (para próxima sesión)

### Ejecución #1
- Fecha/hora:
- Entorno:
- Resultado A:
- Resultado B:
- Resultado C:
- Hallazgos:
- Acción tomada:

### Ejecución #2
- Fecha/hora:
- Entorno:
- Resultado A:
- Resultado B:
- Resultado C:
- Hallazgos:
- Acción tomada:
