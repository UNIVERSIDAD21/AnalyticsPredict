# C3 — Cumplimiento comercial mínimo (go-live)

Estado: VIGENTE
Fecha: 2026-03-24
Alcance: Capa comercial/legal mínima para flujos premium de AnalyticsPredict.

## Objetivo
Asegurar que cada flujo premium tenga cobertura legal/comercial explícita, trazable y consistente entre UI, backend y documentos rectores.

## Cobertura mínima obligatoria

### 1) Plan comercial
- Identidad de plan: `plan_id` único y trazable.
- Precio y moneda definidos por sesión de checkout (`amount_cents`, `currency`).
- Beneficios premium condicionados a `subscription.status=active`.
- Prohibido prometer rentabilidad o resultados garantizados.

### 2) Cancelación
- El usuario puede solicitar cancelación en cualquier momento por canal de soporte oficial.
- La cancelación no reescribe históricamente transacciones ya ejecutadas.
- La cancelación impacta el estado de suscripción y, por tanto, el feature gating.

### 3) Renovación
- La continuidad de acceso premium depende del estado de cobro actualizado por webhook.
- `pending/in_process` no habilitan premium.
- `approved` reactiva/habilita premium.

### 4) Reembolso
- Reembolsos siguen política comercial vigente y normativa aplicable.
- Estado de pago `refunded` o `charged_back` implica estado de suscripción no activo.
- Toda incidencia de cobro debe quedar registrada y trazable.

### 5) Incidencias de cobro
- Firma inválida -> rechazo del webhook.
- `external_reference` inexistente -> rechazo explícito.
- webhook repetido -> idempotencia (sin doble efecto).

## Restricciones de uso premium
- Premium no equivale a asesoría financiera personalizada ni promesa de ganancia.
- Uso permitido solo bajo términos y disclaimer vigentes.
- El sistema prioriza decisión con evidencia y control de riesgo.

## Referencias rectoras
- `docs/legal/TERMINOS_Y_CONDICIONES.md`
- `docs/legal/POLITICA_PRIVACIDAD.md`
- `docs/legal/DISCLAIMER_OPERATIVO.md`
- `docs/operacion/FLUJO_REAL_PAGOS_C1.md`
- `docs/operacion/C1_MATRIZ_ESTADOS_Y_FALLOS.md`
