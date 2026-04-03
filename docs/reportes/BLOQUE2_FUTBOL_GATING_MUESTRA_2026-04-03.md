# BLOQUE 2 — Gating de estado_mercados + robustez de muestra (fútbol)

## Comportamiento anterior (resumen)
- Si `estado_mercados` venía `{}`, en varios puntos se asumía `verde` por defecto y podían sobrevivir recomendaciones.
- Si el mercado objetivo no aparecía en `estado_mercados`, no se forzaba degradación explícita a nivel objetivo.
- No había una regla central explícita de mínimos por bloque contextual para degradar confianza del objetivo (H2H, local/home, visitante/away).

## Comportamiento corregido
1. `estado_mercados` vacío/no disponible:
   - objetivo canónico pasa a `datos_insuficientes`;
   - se marca degradación `estado_mercados_vacio`.
2. mercado objetivo ausente en `estado_mercados`:
   - objetivo canónico pasa a `datos_insuficientes`;
   - se marca degradación `mercado_objetivo_fuera_estado_mercados`.
3. mínimos de muestra contextual (objetivo):
   - H2H >= 5
   - local/home >= 25
   - visitante/away >= 25
   - si falla cualquier bloque: `muestra_insuficiente` y degradación explícita.
4. recomendaciones con muestra insuficiente:
   - se degrada un nivel de confianza (`MUY_ALTA->ALTA->MEDIA->BAJA->MUY_BAJA`);
   - se agrega advertencia `muestra_insuficiente_contexto` con bloques afectados;
   - se deja marca en `metadata_ensemble`.
5. trazabilidad:
   - `objetivo.trazabilidad.temporal` incluye reglas mínimas, evaluación de muestra, disponibilidad real de `estado_mercados` y presencia del mercado objetivo en ese mapa.

## Dependencias y riesgos
- Si `estado_mercados` no puede calcularse por calidad/volumen en `predicciones_futbol`, el sistema ahora degrada de forma honesta (sin defaults silenciosos).
- La robustez sigue dependiendo de calidad de datos históricos y resolución de outcomes en predicciones.
