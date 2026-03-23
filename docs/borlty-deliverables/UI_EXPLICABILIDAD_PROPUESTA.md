# UI_EXPLICABILIDAD_PROPUESTA.md

Versión: v1  
Ámbito: UI Web/Mobile para explicabilidad de predicciones (Bloque 07.2)  
Base contractual: `CONTRATO_DE_EXPLICACION_DE_PREDICCION.md`

---

## 1. ARQUITECTURA DE COMPONENTES

### 1.1 Atomic Design

#### Átomos
- **QualityBadge (A/B/C):** estado de calidad con color/glow por nivel.
- **ConfidenceIndicator:** nivel cualitativo + barra + valor numérico.
- **FactorBar:** barra de contribución de factor explicativo.
- **WarningIcon:** iconografía por severidad (`info`, `warning`, `critical`).
- **DataPoint:** etiqueta + valor breve para KPIs de contexto.

#### Moléculas
- **PredictionCard:** resumen rápido de predicción (valor, recomendación, línea).
- **FactorsList:** lista top 5 factores con barras y tooltips.
- **WarningPanel:** bloque de advertencias agrupadas por severidad.
- **HistoricalContext:** módulo de precisión histórica y muestra.
- **ConfidenceRange:** rango de predicción + intervalo de confianza.

#### Organismos
- **ExplanationView:** composición principal para lectura rápida.
- **PredictionDetail:** detalle expandido de contexto y metadatos.
- **QualityDashboard:** estado de calidad y alertas activas del dominio.

#### Páginas
- **PredictionExplanationPage:** página única de decisión rápida + transparencia.

### 1.2 Jerarquía de Componentes

```tsx
<PredictionExplanationPage>
  <PredictionHeader>
    <QualityBadge level={AorBorC} />
    <ConfidenceIndicator level={highOrMediumOrLow} />
  </PredictionHeader>

  <PredictionValue>
    <Recommendation />
    <PredictionRange />
  </PredictionValue>

  <ExplanationSection>
    <FactorsList factors={top5} />
  </ExplanationSection>

  <WarningsSection visible={hasWarnings}>
    <WarningPanel warnings={dataQualityWarnings} />
  </WarningsSection>

  <HistoricalContextSection optional>
    <SimilarPredictions />
    <AccuracyStats />
  </HistoricalContextSection>

  <DisclaimerFooter>
    <LegalDisclaimer />
  </DisclaimerFooter>
</PredictionExplanationPage>
```

---

## 2. WIREFRAMES Y LAYOUTS

### 2.1 Vista Principal - Calidad A

```text
┌─────────────────────────────────────────┐
│ [BADGE: A] [CONFIDENCE: Alta] ⓘ        │
├─────────────────────────────────────────┤
│ PREDICCIÓN: 112 puntos                  │
│ RECOMENDACIÓN: OVER 108.5               │
│ RANGO: 109 - 115 puntos                 │
├─────────────────────────────────────────┤
│ TOP FACTORES EXPLICATIVOS:              │
│ ██████████████████ 45% Ofensiva LAL     │
│ ████████████       30% Últimos 5 juegos │
│ ████████           15% Head-to-head     │
│ ███                 7% Home court       │
│ ██                  3% Pace             │
├─────────────────────────────────────────┤
│ ⓘ 150 juegos similares                  │
│ Precisión histórica: 74%                │
└─────────────────────────────────────────┘
│ Disclaimer legal...                     │
└─────────────────────────────────────────┘
```

### 2.2 Vista con Advertencias - Calidad B

```text
┌─────────────────────────────────────────┐
│ [BADGE: B] [CONFIDENCE: Moderada] ⚠️    │
├─────────────────────────────────────────┤
│ ⚠️ PRECAUCIÓN: Algunos datos limitados  │
├─────────────────────────────────────────┤
│ PREDICCIÓN: 2.5 goles                   │
│ RECOMENDACIÓN: UNDER 3.0                │
│ RANGO: 2.2 - 2.8 goles                  │
├─────────────────────────────────────────┤
│ [... factores ...]                      │
├─────────────────────────────────────────┤
│ ⚠️ ADVERTENCIAS                          │
│ • Cobertura: 75%                        │
│ • Datos parciales recientes             │
└─────────────────────────────────────────┘
```

### 2.3 Vista de Alerta - Calidad C

```text
┌─────────────────────────────────────────┐
│ [BADGE: C] [CONFIDENCE: Baja] 🛑         │
├─────────────────────────────────────────┤
│ 🛑 ADVERTENCIA CRÍTICA                   │
│ Calidad de datos insuficiente           │
│ NO SE RECOMIENDA APOSTAR                │
├─────────────────────────────────────────┤
│ PREDICCIÓN: 105 puntos (poco confiable) │
│ RECOMENDACIÓN: SKIP                     │
├─────────────────────────────────────────┤
│ PROBLEMAS DETECTADOS                    │
│ • Drift en datos recientes              │
│ • Cobertura <50%                        │
│ • Freshness fuera de umbral             │
└─────────────────────────────────────────┘
```

---

## 3. SISTEMA DE DISEÑO

### 3.1 Paleta de Colores (Cyberpunk)

- Background: `#0a0e27`
- Surface: `#1a1f3a`
- Text Primary: `#e0e6ed`
- Text Secondary: `#8892a6`

Acentos:
- Cyan (info): `#00d9ff`
- Magenta (highlight): `#ff00aa`
- Green (success/A): `#00ff88`
- Yellow (warning/B): `#ffaa00`
- Red (error/C): `#ff3366`

Niveles calidad:
- A: borde/glow verde
- B: borde/glow amarillo
- C: borde/glow rojo + pulso suave

### 3.2 Tipografía

- Headings: **Orbitron**
- Body: **Inter**
- Mono/Data: **Fira Code**

Escalas:
- H1: `2rem`
- H2: `1.5rem`
- Body: `1rem`
- Small: `0.875rem`

### 3.3 Componentes Visuales

**QualityBadge**
```jsx
<div className={`quality-badge quality-${level}`}>
  <span className="badge-letter">{level}</span>
  <div className="glow-effect" />
</div>
```

**ConfidenceIndicator**
- barra horizontal con gradiente
- icono: Alta 🔥 / Moderada ⚡ / Baja ❄️
- tooltip con intervalo numérico

**FactorBar**
- barra horizontal proporcional al impacto
- tooltip: valor feature + contribución + descripción

**WarningPanel**
- fondo translúcido por severidad
- borde lateral izquierdo
- icono ⚠️ / 🛑

---

## 4. FLUJOS DE INTERACCIÓN

### 4.1 Flujo Normal (Calidad A)
1. Usuario ve predicción en lista.
2. Click en detalle.
3. Ve badge A + confianza alta.
4. Revisa top factores (rápido).
5. Toma decisión.

### 4.2 Flujo con Advertencias (Calidad B)
1. Badge B en listado (amarillo).
2. Click abre panel de warnings.
3. Usuario lee limitaciones.
4. Decide “Apostar con cautela” o “Skip”.

### 4.3 Flujo Bloqueado (Calidad C)
1. Badge C + SKIP visible desde listado.
2. Detalle muestra alerta crítica primero.
3. CTA de apuesta oculto/deshabilitado.
4. Usuario recibe motivo técnico resumido.

### 4.4 Interacciones Opcionales
- Hover/click en factores -> tooltip detallado.
- Expandir contexto histórico.
- Click en disclaimer -> modal legal completo.

---

## 5. RESPONSIVIDAD

### 5.1 Desktop (>1024px)
- Grid 2 columnas: resumen + explicación.
- barras largas para factores.

### 5.2 Tablet (768-1024px)
- 1 columna principal + bloques apilados.
- factores horizontales conservados.

### 5.3 Mobile (<768px)
- stack vertical completo.
- warning panel colapsable.
- detalle en bottom sheet.

---

## 6. ESTADOS Y ANIMACIONES

### 6.1 Estados de Carga
- skeleton por bloque
- shimmer suave

### 6.2 Estados de Error
- mensaje genérico + detalle técnico opcional
- botón `Reintentar`

### 6.3 Animaciones
- glow badge (pulse 2s)
- factor bars (stagger-in)
- warnings (fade + slide-down)
- transiciones globales 200ms ease-out

---

## 7. ACCESIBILIDAD

### 7.1 Semántica HTML
- usar `section`, `article`, `aside`, `header`, `footer`
- ARIA labels en iconos y controles

### 7.2 Contraste
- mínimo WCAG AA (4.5:1)
- no depender del glow como única señal

### 7.3 Keyboard Navigation
- tabulación completa
- focus visible cyan

### 7.4 Screen Readers
- anunciar nivel de calidad en header
- leer advertencias por severidad
- iconos con `aria-label`

---

## 8. DISCLAIMERS Y TEXTOS LEGALES

### 8.1 Disclaimer Footer (siempre visible)

> “Esta predicción es solo informativa y no constituye asesoría financiera.  
> Las apuestas deportivas implican riesgo. Solo debe apostar dinero que pueda permitirse perder.  
> [Juego responsable]”

### 8.2 Tooltip de Calidad
- A: “Datos de alta calidad. Predicción más confiable.”
- B: “Datos aceptables. Revise advertencias.”
- C: “Datos insuficientes. No recomendado para decisión de apuesta.”

### 8.3 Tooltip de Confianza

“Confianza estimada con base en calidad de datos, varianza del modelo y contexto histórico.  
Rango de predicción: {lower} – {upper}”

---

## 9. INTEGRACIÓN CON BACKEND

### 9.1 Consumo del Contrato

```typescript
const fetchExplanation = async (predictionId: string): Promise<PredictionExplanation> => {
  const response = await fetch(`/api/v2/predictions/${predictionId}/explanation`);
  const data = await response.json();

  // Validar schema
  if (!validateSchema(data)) throw new Error('Invalid schema');

  return data;
};
```

### 9.2 Manejo de Errores

```typescript
try {
  const explanation = await fetchExplanation(id);
  renderExplanation(explanation);
} catch (error) {
  showErrorState("No se pudo cargar la explicación");
}
```

### 9.3 Caching

- Cache de explicaciones por **5 minutos**.
- Invalidar cache si se detecta actualización de datos (`generated_at` nuevo o cambio de `data_quality.score`).
- Recomendación: estrategia `stale-while-revalidate` para UX fluida.

---

## 10. TESTING Y VALIDACIÓN

### 10.1 Test Cases UI

| Test | Descripción | Verificación |
|------|-------------|--------------|
| Render A | Calidad A sin warnings | Badge verde, warnings panel oculto |
| Render B | Calidad B con warnings | Badge amarillo, warnings visibles |
| Render C | Calidad C | Badge rojo, mensaje crítico prominente |
| Responsive | Mobile, tablet, desktop | Layout correcto en cada breakpoint |

### 10.2 Test de Accesibilidad

- Lighthouse score > 90.
- axe-core sin errores críticos.
- Navegación completa por teclado.

---

## 11. IMPLEMENTACIÓN FASEADA

### 11.1 Fase 1 (MVP)

- Componentes básicos: `QualityBadge`, `ConfidenceIndicator`, `FactorsList`.
- Vista principal sin interacciones avanzadas.
- Disclaimers obligatorios visibles.

### 11.2 Fase 2

- `WarningPanel` completo.
- Tooltips interactivos.
- Contexto histórico expandible.

### 11.3 Fase 3

- Animaciones y polish visual.
- Responsive completo.
- Accesibilidad optimizada.

---

## Mapeo rápido al contrato backend

Campos usados desde `PredictionExplanation`:
- Header: `data_quality.level`, `prediction.confidence.level`, `prediction.confidence.numeric`
- Valor principal: `prediction.value`, `prediction.line`, `prediction.recommendation`, `prediction.confidence.interval`
- Factores: `explanation.top_factors[]`
- Warnings: `data_quality.flags[]`, `explanation.warnings[]`
- Contexto: `explanation.historical_context`
- Estados especiales: `metadata.is_legacy_contract`, flags de drift/quality

---

## Validación de alcance de esta propuesta

- ✓ Wireframes para niveles A, B, C.
- ✓ Sistema de diseño (colores + tipografía) definido.
- ✓ Componentes organizados con Atomic Design.
- ✓ Flujos de interacción documentados.
- ✓ Plan de responsividad cubierto.
- ✓ Criterios de accesibilidad especificados.
- ✓ Disclaimers y textos legales incluidos.
- ✓ Plan de implementación faseada incluido.
- ✓ Sin implementación de código productivo (solo diseño/propuesta).

## Cierre

La propuesta prioriza lectura en segundos, transparencia con calidad real y disuasión fuerte cuando el riesgo es alto (nivel C), manteniendo consistencia con contrato v1 y estética cyberpunk del producto.
