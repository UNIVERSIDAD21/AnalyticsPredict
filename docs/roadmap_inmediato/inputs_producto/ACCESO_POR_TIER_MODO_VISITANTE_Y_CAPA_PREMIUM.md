
# ESPECIFICACIÓN DE PRODUCTO — ACCESO POR TIER, MODO VISITANTE Y CAPA PREMIUM
## Proyecto: AnalyticsPredict
## Documento para implementación y alineación con Borlty
## Fecha: 2026-03-27

> Actualización operativa (2026-03-27): el módulo Chat queda fuera de alcance de implementación inmediata. Debe permanecer inactivo y oculto en UI hasta nueva instrucción.

---

## 0. Propósito de este documento

Este documento define, de forma extensa y sin ambigüedades, cómo debe funcionar AnalyticsPredict a nivel de producto respecto a:

- acceso sin login,
- límites para visitante,
- límites para usuario registrado,
- definición real de premium,
- fronteras entre capas,
- reglas de negocio,
- copy funcional,
- gobernanza por deporte,
- implementación esperada para que Borlty no improvise.

Este documento no está escrito como una idea suelta ni como texto de marketing.  
Está escrito como especificación de producto para ejecución.

---

## 1. Aclaración inmediata: el término “seguimiento” NO debe usarse de forma vaga

Antes de seguir, hay que corregir una confusión importante.

En conversaciones previas se mencionó “seguimientos”, pero **ese término no debe usarse como eje principal del sistema si no está definido funcionalmente**.

### 1.1. Qué NO debe pasar
No se debe hablar de “seguimiento” como si fuera algo obvio si el producto todavía no lo tiene claramente materializado en UI, backend y reglas.

Porque entonces Borlty puede inventar cualquier cosa:
- favoritos,
- watchlist,
- alertas,
- historial,
- recordatorios,
- observados,
- tracked items,
- etc.

Eso genera entregables ambiguos.

### 1.2. Qué SÍ debe hacerse
En AnalyticsPredict hay que hablar con términos concretos y ya alineados al producto actual o a una evolución inmediata realista:

**Objetos y módulos concretos del sistema:**
- Centro analítico público
- Análisis NBA
- Módulo fútbol
- Bitácora
- Dashboard de usuario
- Onboarding
- Configuración
- Chat contextual
- Suscripción / estado de plan
- Notificaciones
- Gobernanza por deporte / competición

### 1.3. Si en algún momento se usa “seguimiento”, debe significar solo esto
**Seguimiento = un objeto guardado por el usuario para volver a revisarlo luego**, por ejemplo:
- un partido guardado,
- un mercado guardado,
- una alerta asociada a un partido/mercado,
- una observación persistente de una oportunidad.

Pero eso debe considerarse **fase posterior o feature explícita**, no el corazón de la primera definición de tiers.

### 1.4. Regla para Borlty
En esta etapa, el producto **NO se debe diseñar alrededor de la palabra “seguimiento”**.
Se debe diseñar alrededor de:
- exploración pública,
- análisis operativo autenticado,
- bitácora personal,
- dashboard,
- configuración,
- chat,
- premium como profundidad.

---

## 2. Qué es realmente AnalyticsPredict

AnalyticsPredict **no debe presentarse como una landing de picks** ni como una página comercial disfrazada de producto.

AnalyticsPredict es una:

# Plataforma de analítica deportiva con trazabilidad operativa, gobernanza por deporte y capas de acceso por nivel de usuario.

### 2.1. Identidad correcta del producto
No es:
- una promesa de “ganar fácil”,
- una vitrina de humo,
- una simple app de tips,
- una pantalla bloqueada hasta login.

Sí es:
- un sistema analítico,
- un entorno de lectura de señal,
- un producto con disciplina operativa,
- una experiencia donde el usuario entiende valor antes de comprometerse.

### 2.2. Núcleo conceptual del producto
El sistema gira alrededor de:
- análisis deportivo con enfoque operativo,
- trazabilidad de decisiones,
- diferencia de madurez entre deportes,
- continuidad personal del usuario,
- control de riesgo,
- capa de suscripción que agrega profundidad real.

### 2.3. Diferencial clave
AnalyticsPredict no debe competir diciendo:
“tenemos picks”.

Debe competir diciendo:
- mostramos criterio,
- mostramos evidencia,
- mostramos gobernanza,
- mostramos madurez por deporte,
- mostramos cómo pensar, no solo qué escoger.

---

## 3. Lectura del estado actual del proyecto

A nivel de producto, el proyecto ya da señales claras de su dirección y eso debe respetarse.

### 3.1. El sistema ya tiene separación entre público y protegido
Hoy ya existe una estructura donde:
- hay puntos de entrada públicos,
- hay rutas protegidas,
- el visitante ya puede ver una parte del producto,
- premium ya aparece mencionado,
- pero todavía no existe una matriz funcional completamente cerrada.

### 3.2. Qué ya existe conceptualmente en el sistema
El producto ya sugiere estas capas:
- Visitante
- Registrado
- Premium

Pero todavía están descritas de forma amplia:
- “visitante puede explorar”
- “registrado tiene análisis completo”
- “premium tiene más profundidad”

Eso es insuficiente.

### 3.3. Qué falta definir
Falta cerrar:
- qué puede ver exactamente cada tier,
- qué acciones puede ejecutar,
- qué datos puede consultar,
- qué módulos abre o no abre,
- qué límite numérico existe,
- qué gatilla el registro,
- qué gatilla la subida a premium,
- qué cosas son demo y qué cosas son reales,
- qué partes se mantienen públicas por credibilidad,
- qué jamás se deben regalar.

---

## 4. Regla madre del producto

# AnalyticsPredict debe dejarse conocer antes de exigir cuenta, pero sin regalar el corazón operativo.

Esa frase resume toda la estrategia.

### 4.1. Traducción práctica
- El visitante debe poder entrar al sistema.
- El visitante debe sentir que entró a un producto real.
- Pero el visitante no debe poder usar el motor operativo completo ni construir historial personal.

### 4.2. Qué significa “corazón operativo”
El corazón operativo del producto es:
- análisis profundo accionable,
- persistencia personal,
- bitácora propia,
- personalización,
- continuidad,
- lectura extendida,
- herramientas avanzadas.

Eso no se regala completamente al visitante.

### 4.3. Qué sí se debe regalar
Se debe regalar:
- credibilidad,
- visibilidad,
- exploración,
- comprensión del producto,
- muestra de método,
- experiencia suficiente para despertar deseo de continuar.

---

## 5. Decisión estratégica: NO una landing; SÍ un sistema público controlado

Esto es crítico y no se debe deformar.

## 5.1. Ruta principal correcta
La entrada principal del producto no debe sentirse como una landing de marketing.
Debe sentirse como una **versión pública del sistema**.

### 5.2. Decisión de UX / routing
La ruta `/` debe evolucionar a uno de estos dos escenarios:

### Opción recomendada A
`/` = Sistema público / shell visitante

y la antigua página pública de producto deja de ser una landing separada y se convierte en parte del shell del sistema.

### Opción alternativa B
`/` redirige al centro analítico público enriquecido

pero con una experiencia mucho más robusta que la actual.

### 5.3. Decisión recomendada
La mejor decisión es:

# `/` debe abrir el modo visitante del sistema.

No una landing.  
No una página comercial.  
No un “conoce más”.

Debe abrir una experiencia real de producto con límites.

---

## 6. Arquitectura de acceso correcta

La arquitectura correcta del producto debe ser esta:

### 6.1. Modo visitante
Puede entrar, explorar, comparar, entender y probar superficies controladas.

### 6.2. Modo registrado base
Puede usar el producto real con continuidad personal y herramientas esenciales.

### 6.3. Modo premium
Puede profundizar, extender su lectura, tener más contexto, más capacidad y más continuidad.

---

## 7. Definición exacta de cada tier

# 7.1. VISITANTE

## Objetivo del visitante
Que un usuario nuevo diga:
- “esto sí es un sistema real”,
- “entiendo qué hace”,
- “se ve serio”,
- “quiero entrar más”.

## El visitante NO es un usuario inútil
El visitante no debe ver una pantalla bloqueada.
Debe ver producto real, pero controlado.

## Qué sí puede hacer el visitante

### Acceso general
- Entrar al sistema sin login.
- Navegar por el shell público.
- Cambiar entre deportes visibles.
- Entender la diferencia entre NBA y fútbol.
- Ver la gobernanza de madurez por deporte y por competición.

### Centro analítico público
- Ver KPIs públicos o demostrativos.
- Ver estado de madurez por deporte.
- Ver confianza operativa resumida en formato público.
- Ver tablas o cards de lectura general del sistema.
- Ver copy operativo serio, no comercial.

### Exploración pública de contenido
- Ver partidos próximos en vista pública simplificada.
- Ver análisis de muestra precomputados.
- Ver comparativas públicas resumidas.
- Ver ejemplos de lectura por mercado sin acceso al motor completo.

### Comprensión del producto
- Entender qué comparten NBA y fútbol.
- Entender qué se mantiene específico por deporte.
- Ver qué significa “maduro”, “beta”, “lab”.
- Ver que premium es profundidad, no humo.

### Chat público (estado actual)
- No disponible en esta fase.
- Debe permanecer oculto en la UI pública.
- Se retoma en fase futura cuando exista alcance explícito.

## Qué NO puede hacer el visitante

### Nada personal
- No puede tener bitácora propia.
- No puede guardar decisiones.
- No puede tener dashboard personal.
- No puede configurar bankroll.
- No puede personalizar perfil.
- No puede completar onboarding.
- No puede modificar preferencias.
- No puede tener historial propio persistente de uso operativo.
- No puede acceder a notificaciones personales reales.

### Nada operativo profundo
- No puede ejecutar el flujo completo del análisis NBA.
- No puede usar sin restricción el motor operativo completo.
- No puede guardar apuestas.
- No puede resolver o editar bitácora.
- No puede usar capas profundas del análisis.
- No puede acceder a vistas privadas por usuario.

## Límite exacto recomendado para visitante

### Sistema público
- acceso libre al shell visitante: **sí**
- acceso al centro analítico público: **sí**
- acceso a métricas reales privadas: **no**
- acceso a métricas demo / agregadas / curadas: **sí**

### Análisis público
- análisis operativos completos ejecutables: **no**
- análisis de muestra precomputados: **sí**
- cantidad de análisis de muestra visibles por sesión: **2 a 4**
- si se habilita acción “ver más”: debe pedir registro

### Fútbol público
- lista pública de partidos: **sí**
- detalle analítico profundo por partido: **no**
- acceso a “Analizar partido”: **bloqueado con CTA a cuenta**

### NBA público
- mostrar capacidad del módulo: **sí**
- ejecutar formulario completo real del motor: **no**
- permitir demo controlada: **sí, solo si está precomputada o muy limitada**

### Chat público
- disponible: **no (fase futura)**
- límite diario: **0 mensajes/día mientras esté inactivo**
- la UI no debe mostrar CTA ni entrada al chat

## Qué debe gatillar el registro
El visitante debe ver el login solo cuando intente algo de alto interés, por ejemplo:
- abrir análisis completo,
- guardar una decisión,
- entrar a bitácora,
- entrar a dashboard,
- usar configuración,
- ver la capa extendida de un análisis.

## Mensaje correcto de gate para visitante
No usar:
- “Debes iniciar sesión para continuar” como mensaje frío y seco.

Sí usar:
- “Crea tu cuenta para continuar este análisis con trazabilidad personal.”
- “Regístrate para guardar esta decisión en tu bitácora.”
- “Inicia sesión para desbloquear el flujo operativo completo.”
- “Esta capa es personal y requiere cuenta.”

---

# 7.2. USUARIO REGISTRADO BASE

## Objetivo del usuario base
Que pueda usar el producto de verdad.
No mirar. Usar.

El usuario base debe poder completar el ciclo principal:
- entrar,
- analizar,
- decidir,
- guardar,
- revisar después,
- aprender del propio historial.

Si no puede hacer eso, el plan base está roto.

## Qué sí puede hacer el usuario base

### Cuenta y acceso
- registrarse,
- iniciar sesión,
- recuperar contraseña,
- aceptar legal,
- persistir sesión,
- tener identidad trazable.

### Onboarding
- completar onboarding,
- definir nombre,
- objetivo principal,
- deporte preferido,
- frecuencia,
- bankroll referencial.

### Dashboard personal
- ver estado de onboarding,
- ver KPIs básicos personales,
- ver resumen reciente,
- ver estado del plan,
- ver lectura operativa base,
- ver atajos a módulos principales.

### Módulo NBA
- acceder al flujo completo de análisis.
- usar formulario real.
- ver resultados completos base.
- usar estadísticas de equipos.
- navegar entre análisis y estadísticas.
- guardar apuestas derivadas del análisis.
- crear combinadas si el producto ya lo permite.

### Módulo fútbol
- acceder al flujo completo del módulo.
- ver partidos,
- filtrar,
- seleccionar partido,
- abrir análisis de partido,
- usar dashboard fútbol base,
- operar bajo la gobernanza real de madurez por competición.

### Bitácora
- ver su propia bitácora,
- filtrar,
- paginar,
- resolver,
- eliminar,
- revisar rendimiento personal base.

### Configuración
- configurar bankroll,
- perfil de riesgo,
- modo de de-vig,
- caps de seguridad,
- notificaciones base,
- preferencias simples.

### Chat contextual base (estado actual)
- no disponible en esta fase.
- debe permanecer oculto en UI para usuario base.
- la capacidad de chat se define para fase futura.

### Notificaciones
- gestionar email habilitado,
- alertas de partidos,
- alertas de suscripción,
- resumen semanal base.

## Qué NO debe tener el usuario base

### No debe tener toda la profundidad premium
No se le debe quitar lo esencial, pero sí reservarle al premium:
- capas extendidas de lectura,
- comparativas avanzadas,
- mayor profundidad histórica,
- alertas inteligentes avanzadas,
- herramientas especiales,
- resúmenes premium,
- futuras exportaciones o automatizaciones avanzadas.

## Límite exacto recomendado para usuario base

### Acceso general
- análisis NBA completo: **sí**
- módulo fútbol completo base: **sí**
- dashboard personal: **sí**
- bitácora personal: **sí**
- configuración: **sí**
- onboarding: **sí**
- chat contextual: **no (fase futura)**

### Chat base
- disponible: **no (fase futura)**
- límite actual: **0 mensajes/día**

### Bitácora
- acceso completo a la bitácora propia: **sí**
- filtros y resolución base: **sí**
- exportaciones avanzadas: **no**
- comparativas premium: **no**

### Dashboard
- KPIs básicos: **sí**
- resumen personal: **sí**
- estado de plan: **sí**
- vistas comparativas profundas multi-capa: **no**

### Notificaciones
- preferencias básicas: **sí**
- reglas avanzadas personalizadas: **no**

### Premium teasers visibles desde base
- sí, pero sin fastidiar
- deben aparecer en lugares de alta intención
- no deben romper el uso normal del plan base

## Regla clave del plan base
El usuario base debe sentir:
“el producto me sirve de verdad”

No:
“esto está mutilado hasta que pague”

---

# 7.3. USUARIO PREMIUM

## Objetivo del premium
El premium no debe ser “ahora sí funciona”.
Debe ser:
“ahora lo llevo en serio”

## Premium = profundidad, continuidad y ventaja operativa superior

Eso significa que premium debe aportar:
- más contexto,
- más lectura,
- más memoria,
- más comparación,
- más capacidad,
- más priorización,
- más sofisticación.

## Qué sí debe tener premium

### Capas analíticas extendidas
- lectura más profunda del análisis,
- más contexto comparativo,
- capas extendidas por mercado,
- comparaciones adicionales,
- lectura de riesgo más rica,
- señales enriquecidas.

### Dashboard premium
- panel más profundo,
- comparativas históricas,
- segmentación más fina,
- vistas avanzadas por deporte/mercado,
- mayor lectura de consistencia y calidad.

### Chat premium (futuro)
- capacidad extendida cuando el módulo se reactive.
- no debe aparecer en UI mientras el chat esté inactivo.

### Bitácora premium
- filtros avanzados,
- profundidad histórica extendida,
- futuras exportaciones,
- lectura comparativa superior,
- resúmenes avanzados.

### Notificaciones premium
- reglas más inteligentes,
- más granularidad,
- mayor prioridad,
- futuros canales o automatizaciones premium.

### Configuración premium
- presets avanzados,
- herramientas de lectura superior,
- opciones extendidas cuando se implementen.

## Qué NO debe hacer premium
Premium no debe:
- contradecir la gobernanza del producto,
- vender como maduro lo que sigue en laboratorio,
- desbloquear “magia” falsa,
- hacer parecer que pagar reemplaza evidencia.

### Regla importantísima
Si una competición de fútbol está en LAB o EN VALIDACIÓN:
- el premium puede tener más contexto,
- pero NO puede reetiquetar eso como si fuera equivalente a NBA madura.

La suscripción no debe romper la honestidad del producto.

## Límite exacto recomendado para premium

### Chat
- **no disponible en fase actual**
- objetivo futuro premium: **sin límite práctico**

### Capas extendidas
- **sí**

### Dashboard profundo
- **sí**

### Bitácora avanzada
- **sí**

### Notificaciones avanzadas
- **sí**

### Comparativas enriquecidas
- **sí**

### Futuros exportes / automatizaciones premium
- **sí**, cuando se implementen

---

## 8. Matriz funcional exacta por módulo

| Módulo | Visitante | Registrado Base | Premium |
|---|---|---|---|
| Entrada al sistema | Sí | Sí | Sí |
| Shell público del sistema | Sí | Sí | Sí |
| Centro analítico público | Sí | Sí | Sí |
| Selector de deporte | Sí | Sí | Sí |
| Gobernanza por deporte | Sí | Sí | Sí |
| KPIs públicos/demo | Sí | Sí | Sí |
| KPIs personales | No | Sí | Sí |
| Onboarding | No | Sí | Sí |
| Dashboard personal | No | Sí | Sí |
| Análisis NBA completo | No | Sí | Sí |
| Análisis demo NBA | Sí | Sí | Sí |
| Módulo fútbol público resumido | Sí | Sí | Sí |
| Módulo fútbol operativo base | No | Sí | Sí |
| Bitácora personal | No | Sí | Sí |
| Resolución/edición de bitácora | No | Sí | Sí |
| Configuración de bankroll/riesgo | No | Sí | Sí |
| Notificaciones base | No | Sí | Sí |
| Notificaciones avanzadas | No | No | Sí |
| Chat contextual | No (fase futura) | No (fase futura) | No (fase futura) |
| Comparativas avanzadas | No | No | Sí |
| Lectura extendida de análisis | No | Parcial o base | Sí |
| Exportaciones futuras | No | No | Sí |
| Estado de plan/suscripción | No | Sí | Sí |

---

## 9. Fronteras correctas entre tiers

## 9.1. Frontera visitante → registrado
Esta frontera debe activarse cuando el visitante intenta una acción que ya implica continuidad personal.

### Gatiladores correctos
- entrar al análisis operativo real,
- guardar algo,
- entrar a bitácora,
- entrar a dashboard,
- entrar a configuración,
- abrir una capa privada/personal.

### Gatiladores incorrectos
- entrar al sistema,
- abrir la portada,
- cambiar de deporte,
- ver madurez,
- ver KPIs públicos,
- ver el producto.

## 9.2. Frontera registrado → premium
Esta frontera debe aparecer cuando el usuario ya encontró valor y empieza a necesitar más profundidad.

### Gatiladores correctos
- querer más contexto comparativo,
- querer más lectura histórica,
- querer más profundidad de análisis,
- querer filtros o paneles avanzados,
- querer alertas inteligentes,
- querer herramientas “serias” de continuidad superior.

### Gatiladores incorrectos
- bloquear funciones básicas,
- cobrar por completar el flujo mínimo,
- meter popups premium en cada clic,
- usar premium como castigo.

---

## 10. Arquitectura recomendada de navegación

## 10.1. Ruta principal
`/` debe ser el modo visitante del sistema.

## 10.2. Rutas públicas
- `/` → shell público del sistema
- `/login` → autenticación
- `/legal/*` → legal
- opcional mantener `/centro-analitico`, pero idealmente absorbido dentro del shell principal

## 10.3. Rutas protegidas base
- `/onboarding`
- `/dashboard`
- `/app`
- `/bitacora`
- `/configuracion`
- `/futbol`
- `/futbol/partidos/:id`
- `/futbol/dashboard`
- `/futbol/bitacora`

## 10.4. Rutas premium
No necesariamente deben ser rutas separadas.
En muchos casos deben ser:
- capas internas,
- cards,
- paneles,
- tabs,
- overlays,
- bloques extendidos dentro de rutas ya existentes.

Eso es mejor que crear un “mundo aparte” premium.

---

## 11. Qué debe pasar con la página pública actual

Actualmente existe una página pública de producto con tono más cercano a una landing.

### Decisión correcta
Esa pieza no debe seguir siendo una landing separada como eje principal.

### Debe transformarse en uno de estos usos
- bloque introductorio dentro del sistema público,
- cabecera del shell visitante,
- panel de contexto del centro analítico,
- o desaparecer como landing aislada.

### Lo que NO debe quedar
No debe quedar un producto así:
- home comercial,
- login,
- recién después sistema.

Eso no es lo que se quiere para AnalyticsPredict.

---

## 12. Definición funcional exacta del “modo visitante”

El modo visitante debe tener estas secciones mínimas:

### 12.1. Encabezado real de producto
Con acceso a:
- entrar,
- crear cuenta,
- cambiar deporte,
- volver al centro público,
- ver qué es premium sin exageración.

### 12.2. Centro analítico público enriquecido
Debe incluir:
- madurez visible por deporte,
- KPIs públicos/demo,
- contexto de confianza operativa,
- diferencias entre NBA y fútbol,
- tabla de competiciones y su estado.

### 12.3. Superficies públicas de exploración
Debe incluir al menos una o varias de estas:
- lista pública de partidos próximos,
- tarjetas de análisis de muestra,
- comparativas públicas resumidas,
- snapshots curados.

### 12.4. Gating elegante
Cuando el visitante intente algo privado, mostrar:
- beneficio concreto de la cuenta,
- botón de crear cuenta,
- botón de login,
- y si aplica, una mención del beneficio premium posterior.

### 12.5. Persistencia mínima del visitante
Se puede conservar:
- identificador invitado,
- conteo de vistas,
- conteo de ingresos,
- eventos públicos.

Pero eso no debe confundirse con cuenta real.

---

## 13. Definición funcional exacta del plan base

El plan base debe ser el corazón del onboarding y activación.

### Debe permitir:
- cuenta real,
- perfil real,
- continuidad real,
- bitácora real,
- dashboard real,
- configuración real,
- análisis real,
- capacidades de chat definidas para fase futura (sin UI activa hoy).

### No debe depender de premium para:
- analizar,
- guardar en bitácora,
- revisar resultados,
- configurar bankroll y riesgo,
- usar el módulo fútbol base,
- ver dashboard base.

### Debe ser suficiente para que el usuario vuelva por decisión propia.

---

## 14. Definición funcional exacta del premium

Premium debe ser una evolución del uso serio del producto.

## 14.1. Premium no es:
- pagar para que el sistema “por fin sirva”,
- quitar candados absurdos,
- vender humo.

## 14.2. Premium sí es:
- profundidad extra,
- continuidad superior,
- mejor soporte a decisiones,
- paneles más potentes,
- más lectura histórica,
- más herramientas de comparación,
- más capacidad en alertas y contexto operativo.

## 14.3. Regla de copy para premium
Nunca vender premium como:
- “desbloquea todo y gana mejor”

Sí venderlo como:
- “obtén lectura extendida y continuidad superior”
- “lleva tu operación a una capa más profunda”
- “accede a contexto analítico adicional”
- “mejora tu trazabilidad y lectura operativa”

---

## 15. Reglas de gobernanza que aplican a todos los tiers

Estas reglas no se negocian.

### 15.1. Honestidad por deporte
- NBA puede presentarse como frente más maduro.
- Fútbol debe mostrarse con su estado real.
- Ningún tier debe falsear esa realidad.

### 15.2. No promesas fáciles
No usar copy de:
- “gana seguro”
- “apuesta sin perder”
- “el sistema sabe qué va a pasar”

### 15.3. Credibilidad primero
La credibilidad del producto es un activo comercial.
No sacrificarla por captar clics.

### 15.4. Premium no rompe la verdad operativa
Pagar no cambia la evidencia real del sistema.

---

## 16. Reglas de copy por tier

## 16.1. Visitante
Tono:
- claro,
- serio,
- atractivo,
- sin forzar,
- muy de producto.

Ejemplos:
- “Explora el sistema en modo visitante.”
- “Revisa madurez por deporte y capas públicas del producto.”
- “Crea tu cuenta para continuar con trazabilidad personal.”

## 16.2. Registrado base
Tono:
- operativo,
- útil,
- directo.

Ejemplos:
- “Tu dashboard ya está listo.”
- “Guarda esta decisión en tu bitácora.”
- “Completa tu onboarding para reducir fricción.”

## 16.3. Premium
Tono:
- profesional,
- profundo,
- aspiracional sin exagerar.

Ejemplos:
- “Activa profundidad analítica extendida.”
- “Desbloquea una capa superior de lectura operativa.”
- “Accede a comparativas y contexto avanzado.”

---

## 17. Recomendación numérica concreta de límites

Para que Borlty no improvise, se recomiendan estos límites iniciales.

## 17.1. Visitante
- acceso al shell público: **sí**
- acceso a centro analítico público: **sí**
- análisis demo visibles: **máximo 2 a 4 bloques/snapshots**
- chat invitado: **no disponible (fase futura)**
- bitácora: **no**
- dashboard personal: **no**
- configuración: **no**
- onboarding: **no**
- notificaciones personales: **no**

## 17.2. Registrado base
- análisis operativo completo: **sí**
- bitácora personal: **sí**
- dashboard personal: **sí**
- configuración: **sí**
- onboarding: **sí**
- chat contextual: **no disponible (fase futura)**
- capa extendida premium: **no**
- comparativas avanzadas: **no**
- alertas avanzadas: **no**

## 17.3. Premium
- análisis operativo completo: **sí**
- capas extendidas: **sí**
- dashboard profundo: **sí**
- bitácora avanzada: **sí**
- chat: **no disponible (fase futura)**
- alertas avanzadas: **sí**
- comparativas enriquecidas: **sí**
- exportes premium futuros: **sí**

---

## 18. Lo que debe implementarse primero (fase 1 obligatoria)

### Fase 1 = cerrar arquitectura, no inventar features nuevas masivas

#### Debe incluir:
1. convertir la entrada principal en sistema público real;
2. estandarizar tiers;
3. centralizar reglas de acceso;
4. definir gates correctos;
5. alinear copy y routing;
6. separar con claridad visitante / base / premium;
7. aterrizar premium como profundidad.

### Esta fase NO debe depender de:
- crear veinte features nuevas,
- rehacer todo el backend,
- vender un plan premium irreal.

---

## 19. Lo que puede quedar para fase 2

### Fase 2 sí puede incluir:
- seguimiento explícito como feature formal,
- alertas más inteligentes,
- exportaciones,
- capas comparativas avanzadas,
- vistas premium adicionales,
- automatizaciones,
- canales de notificación extra,
- watchlists o seguimiento de mercados.

Pero eso debe venir **después** de cerrar la arquitectura de acceso.

---

## 20. Recomendación técnica de implementación para Borlty

Sin entrar en código, la implementación debe obedecer este criterio:

### 20.1. Debe existir una política central de acceso
No se debe dispersar la lógica por páginas sueltas.

Debe haber una fuente clara que responda:
- qué tier tiene el usuario,
- qué puede abrir,
- qué puede ejecutar,
- qué límite tiene,
- qué CTA mostrar si no tiene acceso.

### 20.2. No más copy ambiguo
Si en una pantalla se dice “premium = seguimiento y profundidad”, eso debe mapear a capacidades concretas.

### 20.3. Las rutas protegidas no bastan
No solo hay que proteger rutas.
Hay que proteger:
- acciones,
- capas,
- botones,
- secciones,
- paneles,
- profundidad.

### 20.4. Las capas premium no deben romper UX base
La UI debe seguir siendo limpia para base.
No llenarla de candados innecesarios.

---

## 21. Criterios de aceptación obligatorios

Borlty no puede dar por terminado esto si no cumple lo siguiente:

### 21.1. Entrada del producto
- La entrada ya no se siente como landing comercial.
- La entrada se siente como sistema público controlado.

### 21.2. Visitante
- Puede entrar sin login.
- Puede entender el producto.
- Puede explorar superficies reales.
- No puede acceder a lo personal ni al motor profundo.

### 21.3. Registrado base
- Puede usar el flujo real del producto.
- Puede analizar.
- Puede guardar en bitácora.
- Puede tener dashboard.
- Puede configurar.
- Chat queda fuera de alcance en fase actual (sin UI).

### 21.4. Premium
- Tiene capacidades superiores reales.
- No solo “menos límites”.
- Hay diferencia funcional clara y visible.

### 21.5. Gobernanza
- El sistema sigue mostrando madurez real por deporte.
- No maquilla fútbol por marketing.
- No promete ganancias fáciles.

---

## 22. Decisión final sobre el concepto del negocio

La idea de negocio correcta no es:

“hacer que entren al login”

La idea correcta es:

# hacer que entren al producto, entiendan el valor, y que el registro sea una continuación natural del interés.

Y la monetización correcta no es:

“cobrar lo básico”

La monetización correcta es:

# cobrar por profundidad, contexto, continuidad y potencia operativa superior.

---

## 23. Definición ejecutiva final

### Visitante
**Mira y entiende el sistema.**  
No construye nada personal.  
No opera profundo.  
Sí siente producto real.

### Registrado base
**Usa el sistema real y desarrolla continuidad personal.**  
Puede analizar, guardar, revisar, configurar y conversar con el producto.

### Premium
**Profundiza y opera con una capa superior de contexto y capacidad.**  
No rompe la verdad del sistema; la amplifica.

---

## 24. Orden de prioridad para ejecución

1. Replantear la entrada principal como sistema público.
2. Cerrar matriz funcional por tier.
3. Corregir términos ambiguos.
4. Centralizar policy de acceso.
5. Implementar gates por acción, no solo por ruta.
6. Definir premium por profundidad real.
7. Dejar fase 2 para seguimientos/watchlists/exportes/automatizaciones.

---

## 25. Instrucción final para Borlty

Borlty no debe interpretar esto como “poner una home bonita y ya”.

Debe entenderlo como:

- rediseño de arquitectura de acceso,
- definición de producto,
- cierre de límites por tier,
- alineación de UX con negocio,
- preservación de credibilidad,
- preparación real para monetización.

Si entrega algo donde:
- visitante sigue cayendo en landing,
- premium sigue siendo humo,
- base queda mutilado,
- o aparecen palabras vagas como “seguimiento” sin definición funcional,

entonces el entregable está mal.

---

# FIN DEL DOCUMENTO
