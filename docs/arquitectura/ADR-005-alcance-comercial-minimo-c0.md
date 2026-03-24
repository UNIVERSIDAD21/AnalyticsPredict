# ADR-005 — Alcance comercial mínimo (C0)

Estado: ACEPTADO
Fecha: 2026-03-24
Responsable: UNIVERSIDAD21

## Contexto
Existía contradicción formal entre el plan de ejecución vigente y la estrategia comercial actual:
- Plan anterior: B7 dependía de B1+B2+B3+B4+B5+B6.
- Estrategia vigente: B3/B4/B5 no deben bloquear primer peso.

Además, persistían piezas sensibles con soporte temporal (SQLite) sin decisión explícita de go-live.

## Decisión
Se redefine el alcance de salida comercial mínima en dos carriles:

### Carril de caja (bloqueante de go-live)
- C1 (pagos productivos)
- C2 (hardening y persistencia)
- C3 (cumplimiento comercial)
- C4 (activación y entrada de valor)
- C7 (gate comercial y cohorte)

### Carril paralelo (no bloqueante de primer peso)
- C5 (paridad operativa fútbol)
- C6 (centro analítico multideporte)

## Definiciones estratégicas obligatorias
- NBA: frente comercial principal.
- Fútbol: beta/laboratorio controlado hasta cumplir criterios de promoción.
- B3: maduración operativa, no bloqueo de caja.
- B4: retención/engagement, no bloqueo de primer peso.
- B5: fuera de alcance de go-live inicial si no se usa IA en salida comercial.

## Persistencias temporales
Se establece inventario obligatorio en C2 para cualquier pieza launch-critical apoyada en SQLite:
- clasificar en: migrar antes de go-live / aceptar temporalmente con mitigación / excluir del alcance comercial.

## Consecuencias
- Se elimina ambigüedad sobre qué bloquea primer peso.
- Se protege foco comercial sin maquillar madurez de fútbol.
- Se formaliza la transición de estrategia a ejecución documental y técnica.
