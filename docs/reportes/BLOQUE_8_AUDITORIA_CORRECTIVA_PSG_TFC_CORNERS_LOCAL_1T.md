# BLOQUE 8 — Auditoría correctiva (caso canónico PSG vs Toulouse, `CORNERS_LOCAL_1T`, línea 5.0)

## Caso auditado
- Partido canónico: PSG vs Toulouse.
- Mercado objetivo: `CORNERS_LOCAL_1T`.
- Línea objetivo: `5.0`.

## Hallazgos de causa raíz (sin maquillaje)

### 1) Contradicción de muestra H2H (3 vs 10)
**Causa raíz:**
- El badge de calidad (`Muestras -> H2H`) venía del backend (`objetivo.calidadDatos.muestras.h2h`, muestra canónica del objetivo).
- La tarjeta H2H visible se alimentaba de un dataset frontend paralelo (`contexto.h2h` cargado por endpoint general), sin reconciliar con la muestra canónica.

**Impacto:** la UI mostraba dos verdades distintas en la misma pantalla.

### 2) Record H2H no cerraba con total
**Causa raíz:**
- La vista de récord mostraba solo `victorias_equipo-victorias_rival`, ocultando empates.
- Con empates, el total podía ser mayor que la suma visible, generando inconsistencia perceptual.

### 3) “Sin recomendación disponible” coexistiendo con “coincide con la recomendación del sistema”
**Causa raíz:**
- `mensaje_apuesta` en adaptador se decidía por `analisis.recomendaciones.length` global.
- El bloque de coincidencia de UI infería recomendación desde probabilidades over/under aun sin recomendación formal del mercado objetivo.

### 4) Base y ajustada idénticas con narrativa de ajuste
**Causa raíz:**
- El panel comparativo se renderizaba aunque no hubiera ajuste contextual real (valores idénticos).

### 5) Señales de mercado fuera de `estado_mercados` con UX demasiado “normal”
**Causa raíz:**
- Las penalizaciones llegaban, pero no se elevaban de forma suficientemente explícita en advertencias contextuales del resultado.

## Correcciones aplicadas

### A. Coherencia H2H canónica
- Se alineó `contexto.h2h` del adaptador con muestra canónica cuando backend la reporta (`objetivo.calidadDatos.muestras.h2h`).
- Se recorta dataset H2H renderizado a esa muestra para evitar contradicción de conteos.

### B. Récord H2H consistente
- En `SeccionH2H` el récord ahora se muestra como `G-E-P`.
- El total mostrado usa la misma base visible de partidos.

### C. Recomendación/no recomendación sin contradicción
- `mensaje_apuesta` ahora depende de recomendación formal del mercado objetivo (`recObjetivo`), no del largo global.
- En UI, el bloque “tu apuesta vs sistema” ya no afirma coincidencia si no hay recomendación formal.

### D. Base vs ajustada sin vender ajuste inexistente
- El panel comparativo solo se muestra cuando existe ajuste contextual real.
- Si base y ajustada son idénticas, se muestra advertencia explícita de no ajuste efectivo.

### E. Severidad de mercado fuera de cobertura
- Se elevaron advertencias contextuales cuando aparecen penalizaciones:
  - `estado_mercados_vacio`
  - `mercado_objetivo_fuera_estado_mercados`

### F. Profesionalización del texto de razones
- Se eliminó salida genérica `unid` en razones.
- Ahora usa unidad real del mercado en render (`unidadLabel`).

## Archivos tocados
- `frontend/src/utilidades/adaptadores/futbolToNbaAnalisis.ts`
- `frontend/src/componentes/organismos/ResultadoAnalisis.tsx`
- `frontend/src/componentes/organismos/SeccionH2H.tsx`
- `frontend/src/componentes/organismos/ListaRazones.tsx`
- `frontend/src/utilidades/adaptadores/futbolToNbaAnalisis.test.ts`
- `docs/reportes/BLOQUE_8_AUDITORIA_CORRECTIVA_PSG_TFC_CORNERS_LOCAL_1T.md`

## Pruebas de regresión
- `src/utilidades/adaptadores/futbolToNbaAnalisis.test.ts`
  - market-aware para corners/disparos,
  - no contradicción de “sin recomendación”,
  - alineación de total H2H con muestra canónica.
- `src/servicios/futbol/analisis.test.ts`

## Evidencia de ejecución
- `npm run test -- --run src/utilidades/adaptadores/futbolToNbaAnalisis.test.ts src/servicios/futbol/analisis.test.ts` ✅
- `npm run lint` ✅
- `npm run build` ✅

## Riesgos residuales
- El warning de chunk circular en build (reexport de `ResultadoAnalisis`) sigue siendo warning técnico de bundling; no bloquea CI pero conviene tratarlo en bloque de deuda técnica.
- El endpoint de contexto paralelo (H2H/historial) aún existe; esta corrección lo reconcilia visualmente con el canónico, pero la unificación definitiva de fuentes sigue siendo mejora estructural futura.
