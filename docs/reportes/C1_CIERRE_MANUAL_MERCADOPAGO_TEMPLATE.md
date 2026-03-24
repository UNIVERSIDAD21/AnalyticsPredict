# C1_CIERRE_MANUAL_MERCADOPAGO_TEMPLATE.md

Estado: PENDIENTE DE EJECUCIÓN MANUAL
Fecha de creación: 2026-03-24
Responsable de ejecución manual: UNIVERSIDAD21

## Propósito
Este documento sirve para cerrar formalmente el bloque C1 cuando se complete la conexión manual real con MercadoPago y se ejecute la validación operativa del primer cobro.

## Condición previa
Este template solo debe completarse cuando:
- la capa técnica de C1 ya esté implementada en el repo,
- el backend esté desplegado en una URL pública segura,
- las credenciales reales de MercadoPago estén configuradas,
- y exista intención de ejecutar validación manual (homologada o real).

## Tipos de validación manual (definición oficial)
1. **Validación manual homologada**
   - Ejecución manual en entorno homologado/sandbox oficial.
   - Sirve para prevalidar operación manual y checklist humano.
   - **No habilita por sí sola el cierre total de C1 ni apertura de C7.**

2. **Validación manual real**
   - Ejecución manual con cobro real en entorno final de lanzamiento.
   - Es la única validación manual que habilita cierre total de C1.
   - **Solo esta habilita apertura de C7.**

## Regla de gobierno C1/C7 (sin ambigüedad)
- Validación equivalente reproducible (pytest): valida readiness técnico.
- Validación manual homologada: valida readiness operativo manual (prevalidación).
- Validación manual real: valida readiness comercial real.
- C1 se considera CERRADO únicamente con validación manual real evidenciada.
- C7 solo puede abrirse después de C1=CERRADO por validación manual real.

## 1. Datos del entorno usado
- URL pública del backend:
- Endpoint webhook configurado:
- Ambiente utilizado (real / homologado oficial):
- Usuario de prueba/controlado:
- Plan o producto probado:
- Monto de la transacción:
- Fecha y hora de ejecución:

## 2. Credenciales/configuración manual aplicada
- Access Token configurado: [sí/no]
- Webhook secret configurado: [sí/no]
- URL webhook configurada en panel MercadoPago: [sí/no]
- Eventos habilitados en panel MercadoPago:
- Observaciones:

## 3. Ejecución del flujo manual
### Paso 1 — Generación de checkout
- Resultado:
- Evidencia/log:
- Observaciones:

### Paso 2 — Ejecución del pago
- Resultado:
- Evidencia/log:
- Observaciones:

### Paso 3 — Recepción del webhook
- Firma válida recibida: [sí/no]
- Evento recibido:
- Idempotencia validada: [sí/no]
- Evidencia/log:
- Observaciones:

### Paso 4 — Actualización de suscripción
- Estado final de suscripción:
- Evidencia/log:
- Observaciones:

### Paso 5 — Validación de feature gate
- Premium habilitado correctamente: [sí/no]
- Endpoint verificado:
- Evidencia/log:
- Observaciones:

## 4. Matriz de verificación final
- Checkout generado correctamente: [sí/no]
- Pago ejecutado correctamente: [sí/no]
- Webhook recibido y validado: [sí/no]
- Evento no duplicó efectos: [sí/no]
- Suscripción quedó en estado correcto: [sí/no]
- Feature gate quedó consistente: [sí/no]
- Evidencia operativa archivada: [sí/no]

## 5. Incidencias detectadas
- Incidencia 1:
- Incidencia 2:
- Incidencia 3:

## 6. Riesgos remanentes que pasan a C2
- Riesgo 1:
- Riesgo 2:
- Riesgo 3:

## 7. Decisión de cierre de C1
- Estado final propuesto: [CERRADO / EN_CURSO]
- Motivo:
- ¿Se puede considerar validado el primer cobro real?: [sí/no]
- ¿Se actualizó `docs/arquitectura/ESTADO_PROYECTO.md`?: [sí/no]
- ¿Se actualizó `CHANGELOG.md`?: [sí/no]

## 8. Firma operativa
- Responsable:
- Fecha:
- Confirmación final:
