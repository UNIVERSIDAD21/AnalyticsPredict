# ROADMAP_DE_EXPANSIONES_FUTURAS

Versión: 1.0  
Fecha: 2026-03-09  
Estado: Firmable (plan técnico)

## 1) Expansión: Chatbot sobre datos analíticos

### 1.1 Prerequisitos

| Prerequisito | Estado |
|---|---|
| KPIs oficiales documentados | ✅ |
| Vistas canónicas bloque 06 estables | ✅ |
| Capa semántica | ✅ |
| Endpoints de consulta controlados | ✅ |
| Definiciones únicas backend/frontend/BD | ✅ |

### 1.2 Arquitectura propuesta

- Endpoint: `/api/chat`
- Modo: solo lectura sobre vistas canónicas (`analytics.vw_*`)
- Seguridad:
  - no SQL libre
  - validador de intención
  - catálogo de consultas permitidas

### 1.3 Fases

- MVP: respuestas sobre KPIs agregados.
- V1: contexto temporal (últimas semanas/mes).
- V2: alertas proactivas y explicaciones asistidas.

### 1.4 Criterio de inicio

Puede iniciar cuando endpoint de consulta segura y ACL de consultas estén implementados.

---

## 2) Expansión: Mejores modelos matemáticos

### 2.1 Estado real de prerequisitos

| Prerequisito | Estado |
|---|---|
| Baseline validado | ✅ |
| Criterios de promoción | ✅ |
| confidence cerrado | ❌ EN_PROCESO |
| datasets confiables NBA | ✅ |
| datasets confiables fútbol | ⚠️ condicionado por drift |

### 2.2 NBA — líneas priorizadas

1. Calibradores por rango odds/mercado (bloqueado parcialmente por B05).
2. Modelos especializados por cuarto.
3. Feature engineering temporal y contextual.

### 2.3 Fútbol — líneas priorizadas

1. Poisson / Dixon-Coles para goles (bloqueado mientras drift siga ACTIVO).
2. Modelos count-based corners/shots.
3. Segmentación por competición.

### 2.4 Criterio de inicio por línea

- Iniciar NBA avanzado: cuando baseline + promoción estén estables en staging.
- Iniciar fútbol avanzado: cuando `drift_futbol_parcial_alto` deje de estar ACTIVO y no haya DQ-CRIT-03 sostenido.

---

## 3) Prerequisitos del sistema (global)

| Prerequisito | Estado real |
|---|---|
| Gobernanza de modelos | ✅ |
| Contrato canónico + legacy en migración | ✅/⚠️ |
| Scorecard + alertas operativas | ✅ |
| Validación E2E por fases | ✅ |
| Deuda B05 cerrada | ❌ |

### Condición de deuda B05

Las expansiones de modelos **no** deben activarse como productivas en fútbol mientras confidence/drift no cumplan criterios de cierre.

> **Nota de gobernanza obligatoria:**
> "Las expansiones no deben activarse mientras haya deuda B05 activa
> que afecte la confiabilidad de los datos base del sistema.
> confidence_parcial y drift_futbol_parcial_alto bloquean la activación
> de expansiones de modelos de fútbol y calibración avanzada."
