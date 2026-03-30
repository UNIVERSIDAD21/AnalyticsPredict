# 06_ESPECIFICACION_FUNCIONAL_TIERS_VISITANTE_BASE_PREMIUM

## 1. Propósito del documento

Este documento define la **especificación funcional vigente** del sistema de tiers de AnalyticsPredict.

Su propósito es reemplazar la ambigüedad natural del documento anterior de ejecución por una especificación operativa, funcional y de UX que describa con precisión:

- qué significa cada tier del producto,
- qué puede hacer cada usuario,
- qué ve cada usuario aunque no lo tenga activo,
- cómo deben comportarse los bloqueos,
- qué CTA debe aparecer según el tipo de restricción,
- cómo se expresa Premium dentro del sistema,
- y cómo debe implementarse todo esto sin romper la lógica actual del producto.

Este documento pasa a ser la referencia principal para decisiones de producto, UX, implementación y validación relacionadas con:

- Visitante,
- Base,
- Premium,
- acceso por capacidad,
- visibilidad de funciones bloqueadas,
- capas premium dentro de módulos existentes.

El documento anterior `05_PLAN_EJECUCION_TIERS_VISITANTE_PREMIUM.md` se mantiene como referencia histórica del plan de implementación inicial. Este documento nuevo define el **contrato funcional vigente**.

---

## 2. Alcance vigente del sistema

Esta especificación cubre:

- shell público del sistema en `/`,
- comportamiento del modo visitante,
- comportamiento del usuario Base,
- comportamiento del usuario Premium,
- navegación global y gates por acción,
- visibilidad de funciones activas y bloqueadas,
- lógica de CTA por tipo de bloqueo,
- onboarding como parte del flujo operativo del usuario Base,
- capas premium dentro de módulos ya existentes,
- reglas de copy y comunicación relacionadas con tiers,
- criterios de aceptación funcional por vista.

Esta especificación **no cubre**:

- chat contextual de IA,
- nuevas rutas separadas para Premium,
- nuevos tiers distintos a Visitante / Base / Premium,
- rediseños visuales ajenos al sistema de acceso y progresión.

Capacidades explícitamente fuera de alcance en la fase actual:

- chat,
- cualquier módulo que implique conversación contextual como parte obligatoria de la propuesta de valor,
- cualquier redefinición del producto donde Base deje de ser útil por sí mismo.

---

## 3. Principios rectores del modelo de tiers

### 3.1 Visitante descubre

El usuario visitante debe poder entrar al producto real sin login forzado, explorar el sistema, entender la propuesta de valor y visualizar la progresión natural hacia Base y Premium.

Visitante no entra al sistema solo para ver una landing publicitaria. Entra a un **shell público real**.

### 3.2 Base usa

El usuario Base debe poder usar AnalyticsPredict de verdad.

Base no puede ser una demo disfrazada ni una versión recortada al punto de perder valor. Debe incluir el flujo operativo esencial:

- análisis,
- bitácora,
- dashboard,
- configuración,
- continuidad personal.

### 3.3 Premium profundiza

Premium no se define por permitir el uso básico del producto. Premium se define por **profundidad operativa superior**.

Premium debe aportar:

- más contexto,
- más histórico,
- mejores comparativas,
- mayor capacidad de lectura,
- capas extendidas de continuidad operativa.

### 3.4 El login aparece por acción protegida

La exploración pública no debe romperse con rebotes arbitrarios a login.

El login debe aparecer cuando el usuario intenta una acción protegida propia de Base.

### 3.5 El bloqueo debe educar, no frustrar

Las funciones bloqueadas no deben presentarse como castigo. Deben presentarse como progresión natural del producto.

### 3.6 Lo siguiente debe verse

El usuario debe poder entender qué gana al subir de nivel.

- Visitante debe ver funciones Base y Premium relevantes, aunque bloqueadas.
- Base debe ver funciones Premium relevantes, aunque bloqueadas.

### 3.7 Base no se mutila para vender Premium

Premium no debe venderse quitando lo esencial al usuario Base.

Si una función es parte del flujo operativo central, debe pertenecer a Base.

### 3.8 Premium se construye dentro del sistema actual

La capa Premium debe vivir dentro de los módulos ya existentes siempre que sea posible, en lugar de crear rutas paralelas innecesarias o duplicar lógica.

---

## 4. Definición oficial de tiers

### 4.1 Tier Visitante

El visitante es el usuario que entra sin cuenta.

#### Objetivo del tier

Permitir descubrimiento real del producto:

- entender la propuesta de valor,
- explorar el centro público,
- visualizar madurez por deporte,
- comprender qué desbloquea crear cuenta,
- comprender qué añade Premium.

#### Valor que recibe

- acceso al shell público,
- snapshots públicos,
- gobernanza visible,
- lectura pública del sistema,
- entrada sin login forzado.

#### Restricciones

No puede usar continuidad personal ni funciones operativas de cuenta:

- no puede abrir análisis operativo protegido,
- no puede guardar en bitácora,
- no puede abrir dashboard personal,
- no puede guardar configuración,
- no puede activar profundidad premium.

### 4.2 Tier Base

Base es el usuario con cuenta autenticada que puede operar el sistema sin mensualidad activa.

#### Objetivo del tier

Permitir uso real del producto con continuidad personal.

#### Valor que recibe

- análisis base,
- bitácora personal,
- dashboard,
- configuración,
- flujo principal del sistema,
- continuidad y trazabilidad de uso.

#### Restricciones

No accede a la profundidad extendida Premium.

### 4.3 Tier Premium

Premium es el usuario con mensualidad o suscripción activa.

#### Objetivo del tier

Entregar profundidad operativa superior.

#### Valor que recibe

- todo lo Base,
- capas depth activas,
- contexto histórico extendido,
- comparativas avanzadas,
- priorización operativa avanzada,
- seguimiento superior dentro de módulos existentes.

#### Restricciones

No existen restricciones funcionales adicionales dentro del sistema de tiers vigente, salvo las capacidades globales explícitamente fuera de alcance.

---

## 5. Subestado operativo del tier Base

El tier Base no debe entenderse como un estado único simplificado. Debe contemplarse en subestados funcionales.

### 5.1 Base autenticado sin onboarding completo

Es un usuario que ya creó cuenta pero aún no completó onboarding.

#### Estado funcional

- pertenece a Base,
- ya salió del mundo Visitante,
- pero todavía no tiene la experiencia operativa personalizada lista.

#### Regla

Este usuario debe ser guiado a completar onboarding antes de operar con normalidad en rutas protegidas que dependan de su contexto personal.

### 5.2 Base autenticado con onboarding completo

Es el estado operativo ideal del usuario Base.

#### Estado funcional

- puede usar el sistema con continuidad,
- puede consumir dashboard y experiencias personalizadas,
- reduce fricción operativa,
- ya puede consolidar hábito dentro del producto.

### 5.3 Importancia del onboarding

Onboarding no es un adorno visual ni una simple encuesta. Forma parte de la activación real del usuario Base.

Debe entenderse como una fase de personalización inicial que mejora:

- dashboard,
- continuidad de uso,
- recomendaciones,
- lectura operativa del sistema.

---

## 6. Catálogo oficial de capabilities

### 6.1 Capacidades vigentes

- `public.shell`
- `public.center`
- `public.governance`
- `dashboard.personal`
- `bitacora.personal`
- `configuracion.base`
- `analisis.nba.base`
- `futbol.base`
- `premium.depth`
- `chat.contextual`

### 6.2 Significado funcional

#### `public.shell`
Permite entrar al shell público del sistema.

#### `public.center`
Permite consumir el centro público y su narrativa general.

#### `public.governance`
Permite ver gobernanza, madurez y lectura pública del sistema.

#### `dashboard.personal`
Permite usar dashboard personal.

#### `bitacora.personal`
Permite guardar y consultar bitácora personal.

#### `configuracion.base`
Permite usar configuración personal.

#### `analisis.nba.base`
Permite entrar al análisis operativo de NBA.

#### `futbol.base`
Permite entrar al módulo operativo de fútbol.

#### `premium.depth`
Permite acceder a la capa premium de profundidad operativa.

#### `chat.contextual`
Capacidad bloqueada y fuera de alcance en la fase actual.

### 6.3 Tier mínimo por capability

#### Visitante
- `public.shell`
- `public.center`
- `public.governance`

#### Base
- `dashboard.personal`
- `bitacora.personal`
- `configuracion.base`
- `analisis.nba.base`
- `futbol.base`

#### Premium
- `premium.depth`

#### Fuera de alcance
- `chat.contextual`

### 6.4 Regla de implementación

Ninguna lógica de acceso debe definirse de manera dispersa fuera de este sistema conceptual.

Toda capacidad debe responder a:

- tier mínimo,
- visibilidad adecuada,
- CTA correcto,
- gate correcto.

---

## 7. Política oficial de visibilidad por tier

### 7.1 Regla general

El sistema debe mostrar progresión.

No debe ocultar por completo todo lo que el usuario aún no tiene, salvo cuando mostrarlo genere ruido irrelevante o complejidad innecesaria.

### 7.2 Visitante

Debe ver:

- funciones públicas activas,
- funciones Base relevantes visibles pero bloqueadas,
- funciones Premium relevantes visibles pero bloqueadas.

### 7.3 Base

Debe ver:

- funciones Base activas,
- funciones Premium relevantes visibles pero bloqueadas.

### 7.4 Premium

Debe ver:

- todo lo Base activo,
- todo lo Premium activo.

### 7.5 Qué sí debe mostrarse bloqueado

- funciones claramente valiosas para progresión,
- funciones que ayudan a explicar el producto,
- capas superiores relevantes al contexto actual de la vista,
- módulos personales cuando el usuario aún es visitante,
- módulos de profundidad cuando el usuario aún es Base.

### 7.6 Qué no debe mostrarse bloqueado sin necesidad

- elementos demasiado técnicos si no aportan comprensión,
- capas futuras que aún no tienen identidad clara,
- componentes que llenen la vista de ruido visual sin ayudar a convertir.

### 7.7 Límite de saturación

Cada vista debería mostrar solo las capas bloqueadas más relevantes.

Regla práctica:

- no más de 1 a 3 puntos bloqueados importantes por pantalla principal,
- no saturar interfaces con candados repetidos,
- no convertir la UX en una lista interminable de negaciones.

### 7.8 Diferenciación visual

Debe existir diferencia visual entre:

- bloqueo de Base para Visitante,
- bloqueo de Premium para Base.

No deben verse como el mismo tipo de bloqueo genérico.

---

## 8. Política oficial de CTAs y mensajes

### 8.1 CTA para bloqueo Base

Usar cuando el usuario Visitante intenta una función de cuenta.

Mensajes permitidos:

- Crea tu cuenta
- Esta función requiere cuenta
- Crea tu cuenta para continuar
- Regístrate para desbloquear esta función
- Crea tu cuenta para guardar y seguir tu operación

### 8.2 CTA para bloqueo Premium

Usar cuando el usuario Base intenta una capa depth.

Mensajes permitidos:

- Activa Premium
- Compra mensualidad
- Mejora tu plan
- Desbloquea esta capa premium
- Activa Premium para más profundidad

### 8.3 Regla de copy explicativo

No usar solo “Bloqueado”.

Toda función bloqueada debe explicar el valor del desbloqueo.

Ejemplo correcto Base:

“Crea tu cuenta para guardar tus análisis y acceder a tu bitácora personal.”

Ejemplo correcto Premium:

“Activa Premium para ver comparativas avanzadas, contexto histórico extendido y priorización operativa superior.”

### 8.4 CTA principal y texto secundario

Regla sugerida:

- CTA principal corto,
- texto secundario explicando el valor.

Ejemplo:

- CTA: `Activa Premium`
- Texto secundario: `Compra mensualidad para desbloquear profundidad extendida y comparativas avanzadas.`

---

## 9. Promesa funcional del registro y autenticación

### 9.1 Qué promete crear cuenta

Crear cuenta permite:

- pasar de exploración pública a uso personal,
- abrir análisis base,
- guardar en bitácora,
- usar dashboard,
- usar configuración,
- construir trazabilidad operativa.

### 9.2 Qué no promete crear cuenta

Crear cuenta **no** promete:

- acceso Premium,
- profundidad extendida automática,
- equivalencia total con una suscripción de pago,
- acceso a capacidades fuera de alcance.

### 9.3 Regla de comunicación

El registro debe venderse como entrada al uso personal real del sistema, no como compra encubierta.

---

## 10. Papel del onboarding dentro del producto

### 10.1 Función del onboarding

Onboarding personaliza el arranque operativo del usuario Base.

### 10.2 Qué debe lograr

- recoger perfil inicial,
- orientar el dashboard,
- reducir fricción,
- ayudar a estructurar el uso posterior,
- reforzar continuidad de uso.

### 10.3 Regla de producto

Onboarding forma parte del flujo operativo del usuario Base y debe mantenerse como etapa formal de activación.

### 10.4 Relación con tiers

- Visitante no usa onboarding.
- Base sí debe atravesarlo.
- Premium lo hereda como parte del flujo Base ya consolidado.

---

## 11. Definición oficial de Premium y sus depth layers

### 11.1 Significado de Premium en AnalyticsPredict

Premium significa **profundidad operativa superior**.

No significa simplemente eliminar bloqueos básicos.

### 11.2 Depth layers oficiales

Las capas premium oficiales del sistema son:

- `comparativas_multi_mercado`
- `contexto_historico_extendido`
- `priorizacion_operativa_avanzada`

### 11.3 Traducción funcional de las depth layers

#### comparativas_multi_mercado
Comparar señales, mercados o lecturas de forma más profunda que en Base.

#### contexto_historico_extendido
Acceder a más profundidad histórica y contexto ampliado.

#### priorizacion_operativa_avanzada
Añadir una capa superior de lectura, priorización o interpretación operativa.

### 11.4 Regla de implementación

Estas capas deben vivir dentro de módulos actuales siempre que sea posible, en lugar de depender de rutas premium separadas.

### 11.5 Regla de comunicación

Premium debe presentarse como:

- más contexto,
- más histórico,
- más comparativa,
- más continuidad,
- más lectura,

no como simple acceso básico tardío.

---

## 12. Capacidades explícitamente fuera de alcance

### 12.1 Chat

El chat contextual queda fuera de alcance en la fase actual.

### 12.2 Regla estructural

El chat no forma parte del sistema de tiers vigente.

- no pertenece a Visitante,
- no pertenece a Base,
- no pertenece al Premium actual.

### 12.3 Regla de futuro

Si el chat se considera más adelante, deberá entrar mediante una nueva especificación funcional y no por reactivación informal.

---

## 13. Reglas del encabezado y navegación global

### 13.1 El encabezado es parte del sistema de tiers

El header no es solo navegación visual. Debe responder al modelo de acceso del producto.

### 13.2 Visitante

Debe poder ver:

- centro,
- referencia a análisis,
- referencia a bitácora,
- desbloqueo con cuenta,
- estado demo/bankroll según corresponda.

Si pulsa una función Base, debe activarse el gate correspondiente.

### 13.3 Base

Debe poder usar navegación real a:

- análisis,
- bitácora,
- dashboard,
- configuración,
- centro.

### 13.4 Premium

Mantiene la navegación Base, pero con acceso activo a capas premium dentro de módulos.

### 13.5 Regla del botón de desbloqueo

Cuando no hay sesión, el header debe usar un CTA de desbloqueo con cuenta y no una redirección agresiva a login sin contexto.

### 13.6 Indicador Demo / Bankroll

El estado Demo/Bankroll debe mantenerse como parte visible del estado operativo del usuario, no como mero adorno visual.

---

## 14. Matriz funcional por vista

## 14.1 Centro Analítico (`/`)

### Visitante
Activo:

- shell público,
- KPIs públicos,
- selector de deporte,
- confianza operativa pública,
- madurez visible,
- gobernanza,
- narrativa de tiers,
- definición pública de capa premium.

Visible pero bloqueado:

- abrir análisis completo,
- guardar en bitácora,
- análisis específico,
- bitácora específica,
- capa premium.

CTA:

- Base: `Crea tu cuenta`
- Premium: `Activa Premium`

### Base
Activo:

- todo lo público,
- navegación a análisis específico,
- navegación a bitácora,
- consumo de datos reales personales cuando aplique.

Visible pero bloqueado:

- capa premium,
- profundidad extendida mostrada dentro del centro.

CTA:

- `Activa Premium`

### Premium
Activo:

- todo lo Base,
- capa premium activa,
- acceso a lectura premium del centro.

---

## 14.2 Análisis NBA (`/app`)

### Visitante
No entra a la ruta. Debe ver la existencia del módulo representada desde el centro.

Visible pero bloqueado:

- análisis completo,
- resultados,
- combinada,
- estadísticas de equipos,
- continuidad del análisis.

CTA:

- `Crea tu cuenta para desbloquear análisis completo`

### Base
Activo:

- formulario de análisis,
- resultados,
- creador de combinada,
- guardado en bitácora,
- navegación a configuración,
- pestaña de estadísticas,
- historial de equipos.

Visible pero bloqueado:

- comparativas avanzadas,
- contexto histórico extendido,
- priorización avanzada,
- capa depth dentro de resultado y estadísticas.

CTA:

- `Activa Premium`

### Premium
Activo:

- todo lo Base,
- profundidad extendida dentro del resultado,
- comparativas avanzadas,
- capas extendidas sobre análisis y estadísticas.

---

## 14.3 Bitácora NBA (`/bitacora`)

### Visitante
No entra a la ruta. Debe ver su existencia desde el centro.

Visible pero bloqueado:

- guardado de decisiones,
- historial personal,
- trazabilidad,
- resolución y revisión.

CTA:

- `Crea tu cuenta para guardar y revisar tus decisiones`

### Base
Activo:

- resumen,
- filtros,
- lista,
- resolución,
- eliminación,
- paginación.

Visible pero bloqueado:

- patrones avanzados,
- comparativas temporales extendidas,
- análisis premium del historial,
- segmentación superior.

CTA:

- `Activa Premium para análisis avanzado de tu historial`

### Premium
Activo:

- todo lo Base,
- bloques extendidos de lectura de patrones,
- comparativas superiores,
- profundidad histórica personal.

---

## 14.4 Dashboard NBA (`/dashboard`)

### Visitante
No entra a la ruta. Debe ver su existencia desde el centro.

CTA:

- `Crea tu cuenta para abrir tu dashboard personal`

### Base
Activo:

- onboarding,
- rendimiento reciente,
- estado de plan,
- atajos operativos,
- KPIs reales,
- baseline técnico,
- guía operativa,
- bloque de evolución del plan.

Visible pero bloqueado:

- capas premium extendidas,
- profundidad adicional,
- comparativas superiores,
- lectura ampliada de continuidad.

CTA:

- `Activa Premium`

### Premium
Activo:

- todo lo Base,
- depth layers activas,
- detalle extendido de la evolución del plan,
- lectura operativa superior.

---

## 14.5 Configuración (`/configuracion`)

### Visitante
No entra a la ruta. Debe ver su existencia desde el sistema.

Visible pero bloqueado:

- bankroll,
- perfil de riesgo,
- modo devig,
- notificaciones,
- caps,
- gestión personal.

CTA:

- `Crea tu cuenta para guardar tu configuración personal`

### Base
Activo:

- bankroll,
- perfil de riesgo,
- modo devig,
- notificaciones,
- caps,
- contexto fútbol,
- lectura del estado de plan.

Visible pero bloqueado:

- controles premium avanzados,
- gestión depth extendida,
- configuraciones premium futuras dentro del mismo módulo.

CTA:

- `Activa Premium`

### Premium
Activo:

- todo lo Base,
- gestión plena del plan,
- controles avanzados de profundidad que se definan dentro del módulo.

---

## 14.6 Módulo Fútbol (`/futbol`)

### Visitante
No entra a la ruta. Debe ver su existencia desde el centro.

Visible pero bloqueado:

- partidos próximos,
- filtros,
- análisis por partido,
- dashboard fútbol,
- continuidad de módulo.

CTA:

- `Crea tu cuenta para desbloquear Fútbol`

### Base
Activo:

- lista de partidos,
- filtros,
- selección de partido,
- navegación a análisis,
- navegación a dashboard,
- flujo base del módulo.

Visible pero bloqueado:

- profundidad premium por competición,
- histórico ampliado,
- comparativas superiores,
- alertas o capas depth futuras dentro del módulo.

CTA:

- `Activa Premium para más profundidad por competición`

### Premium
Activo:

- todo lo Base,
- profundidad extendida por competición y contexto premium.

---

## 14.7 Análisis de Partido Fútbol (`/futbol/partidos/:id`)

### Visitante
No entra. Debe ver su existencia desde el sistema.

Visible pero bloqueado:

- H2H,
- historial local y visitante,
- panel de mercados,
- guardar apuesta,
- profundidad del partido.

CTA:

- `Crea tu cuenta para analizar partidos`

### Base
Activo:

- header del partido,
- panel de análisis de mercado,
- H2H,
- historial individual,
- guardar apuesta.

Visible pero bloqueado:

- histórico extendido,
- contexto comparativo premium,
- profundidad multi-mercado superior,
- lectura avanzada del partido.

CTA:

- `Activa Premium para contexto histórico extendido`

### Premium
Activo:

- todo lo Base,
- capas premium sobre H2H,
- más profundidad histórica,
- comparativas avanzadas del partido.

---

## 14.8 Bitácora Fútbol (`/futbol/bitacora`)

### Visitante
No entra. Debe ver su existencia desde el sistema.

CTA:

- `Crea tu cuenta para registrar y revisar apuestas`

### Base
Activo:

- resumen,
- filtros,
- lista,
- ver partido,
- cancelar,
- paginación.

Visible pero bloqueado:

- profundidad avanzada del historial,
- patrones premium,
- comparativas por competición o mercado,
- lectura extendida.

CTA:

- `Activa Premium`

### Premium
Activo:

- todo lo Base,
- capas avanzadas de interpretación del historial.

---

## 14.9 Dashboard Fútbol (`/futbol/dashboard`)

### Visitante
No entra. Debe ver su existencia desde el sistema.

CTA:

- `Crea tu cuenta para abrir el dashboard técnico`

### Base
Activo:

- ROI,
- Win Rate,
- Brier,
- ECE,
- observabilidad,
- estado de modelos,
- gráfico temporal,
- resumen técnico.

Visible pero bloqueado:

- comparativas premium adicionales,
- capas superiores de lectura técnica,
- profundidad extendida del dashboard.

CTA:

- `Activa Premium`

### Premium
Activo:

- todo lo Base,
- capas extendidas de interpretación técnica y operativa.

---

## 14.10 Login / Registro (`/login`)

### Visitante
Activo:

- login,
- registro,
- recuperación,
- acceso a legal,
- recordatorio de que el centro puede seguir explorándose sin cuenta.

Regla:

Debe reforzar que crear cuenta desbloquea continuidad personal, no Premium.

### Base / Premium
No debe mostrarse cuando ya existe sesión activa; debe redirigir al flujo principal.

---

## 14.11 Onboarding (`/onboarding`)

### Visitante
No entra.

### Base
Activo:

- personalización inicial,
- frecuencia,
- objetivo,
- deporte preferido,
- bankroll referencial,
- activación del dashboard.

### Premium
Lo hereda como parte del flujo Base.

---

## 15. Reglas UX de implementación

### 15.1 No saturar con bloqueos

No llenar las vistas con elementos bloqueados sin jerarquía.

### 15.2 Siempre explicar el valor

Toda capa bloqueada debe explicar qué gana el usuario si desbloquea.

### 15.3 No ocultar toda la progresión

Debe existir suficiente visibilidad para que el usuario entienda el siguiente escalón.

### 15.4 No romper el flujo Base

El Base debe seguir siendo plenamente utilizable.

### 15.5 Premium vive dentro de módulos actuales

Implementar preferentemente capas premium internas antes que crear rutas paralelas innecesarias.

### 15.6 Diferenciar bloqueo Base de bloqueo Premium

No deben compartir exactamente el mismo tratamiento visual ni verbal.

---

## 16. Eventos de producto y analítica de conversión

### 16.1 Eventos mínimos esperados

- vista del centro público,
- gate bloqueado,
- gate permitido,
- onboarding iniciado,
- onboarding completado,
- interacción con capa premium,
- intento de activar Premium.

### 16.2 Regla

La analítica debe capturar la progresión del embudo:

- explorar,
- registrarse,
- completar onboarding,
- consumir Base,
- intentar Premium,
- activar Premium.

---

## 17. Embudo oficial de progresión

### 17.1 Flujo

Visitante → Cuenta Base → Base con onboarding → Premium

### 17.2 Sentido del embudo

#### Visitante
Explora y entiende el sistema.

#### Cuenta Base
Desbloquea trazabilidad personal y uso real.

#### Base con onboarding
Activa experiencia operativa personalizada.

#### Premium
Desbloquea profundidad superior.

---

## 18. Criterios de aceptación por tier y por vista

### 18.1 Visitante correcto si

- puede entrar sin login forzado,
- puede explorar el centro,
- ve progresión a Base y Premium,
- las acciones Base abren gate de cuenta,
- las acciones Premium abren gate de plan,
- no rebota arbitrariamente a login sin intento explícito.

### 18.2 Base correcto si

- puede usar análisis, bitácora, dashboard y configuración,
- no se siente en demo,
- ve capas Premium relevantes bloqueadas,
- entiende qué gana al pagar,
- el flujo no se rompe por ocultamientos innecesarios.

### 18.3 Premium correcto si

- mantiene todo lo Base,
- activa las depth layers,
- ve profundidad extendida,
- no depende de humo o copy vacío,
- muestra superioridad funcional real.

### 18.4 Regla de validación por vista

Cada vista deberá validar:

- activo por tier,
- visible pero bloqueado por tier,
- CTA correcto,
- copy correcto,
- no ocultamiento erróneo,
- no gate agresivo sin contexto.

---

## 19. Restricciones de implementación para Borlty

### 19.1 No inventar nuevos tiers

### 19.2 No convertir Base en pago

### 19.3 No mutilar Base para vender Premium

### 19.4 No reactivar chat

### 19.5 No duplicar lógica de acceso fuera del sistema de capabilities

### 19.6 No crear rutas premium separadas sin justificación fuerte

### 19.7 No ocultar la progresión si la vista debe mostrarla

### 19.8 No usar copy de promesa engañosa

Prohibido:

- “ganar fácil”
- “sistema infalible”
- “premium solo desbloquea el sistema”
- “regístrate para tenerlo todo”

---

## 20. Migración desde el documento anterior

El documento `05_PLAN_EJECUCION_TIERS_VISITANTE_PREMIUM.md` se considera:

- documento histórico de ejecución,
- referencia de implementación inicial,
- base conceptual ya parcialmente materializada.

El documento actual pasa a ser:

- especificación funcional vigente,
- contrato de comportamiento de tiers,
- referencia principal para decisiones futuras sobre acceso, visibilidad y progresión.

---

## 21. Anexos

### 21.1 Anexo A — Tabla capability → tier → CTA

Debe mantenerse una tabla operativa donde cada capability tenga:

- tier mínimo,
- pantallas donde aparece,
- CTA cuando está bloqueada,
- tipo de copy permitido.

### 21.2 Anexo B — Tabla de copies permitidos

#### Base
- Crea tu cuenta
- Esta función requiere cuenta
- Regístrate para desbloquear esta función
- Crea tu cuenta para continuar

#### Premium
- Activa Premium
- Compra mensualidad
- Mejora tu plan
- Desbloquea esta capa premium

### 21.3 Anexo C — Tabla de copies prohibidos

- Gana fácil
- Sistema infalible
- Acceso total al registrarte
- Premium solo para desbloquear lo básico
- Crea cuenta para usar el producto completo si eso borra la lógica Base vs Premium

### 21.4 Anexo D — Checklist QA por vista

Cada vista deberá revisar:

- activo por tier,
- visible pero bloqueado por tier,
- CTA correcto,
- gate correcto,
- copy correcto,
- ausencia de rebotes arbitrarios,
- coherencia con el sistema de capabilities.

### 21.5 Anexo E — Ejemplos de implementación correcta

Ejemplo correcto:

- Visitante ve Dashboard visible pero bloqueado con CTA `Crea tu cuenta`.
- Base ve profundidad extendida del Dashboard visible pero bloqueada con CTA `Activa Premium`.

Ejemplo incorrecto:

- Visitante no ve nada de la progresión.
- Base no puede usar funciones esenciales.
- Premium se vende solo por ocultar lo mínimo.
