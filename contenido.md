# Contenido del dashboard: Corales de Panamá y eventos de El Niño

> **Cómo usar este archivo (para Antigravity):**
> - El texto normal se copia **exactamente** como está.
> - Lo que está entre llaves, como `{anomalia_caribe_2020s}`, es un **número que se calcula desde los CSV** de `datos/limpios/`. Al final de cada sección se explica de dónde sale cada uno.
> - No se deben agregar datos, cifras ni afirmaciones que no estén en este archivo o en los CSV.

---

## 0. Menú

Inicio · Conceptos · Contexto · Análisis · Hoy · Conclusión

---

## 1. Portada

**Logo:** UIP (solo en esta sección)

**Título:** Corales de Panamá y eventos de El Niño: un análisis con datos abiertos

**Subtítulo:** Análisis con datos abiertos de GBIF y NOAA Coral Reef Watch

**Autores:**
- Angela Pérez 
- Edwin De Frías 

**Curso:** Introducción a la Programación para Ciencia de Datos · Maestría en Ciencias de los Datos, Universidad Interamericana de Panamá

**Profesor:** José Higuera

**Etiqueta:** Datos actualizados: `{fecha_generacion}`

> `{fecha_generacion}`: fecha y hora en que se generó el dashboard.

---

## 2. El mar hoy

**Título:** El mar hoy

**Subtítulo:** Temperatura y nivel de alerta de blanqueamiento en las dos costas, según el último dato publicado por NOAA.

**Una tarjeta por costa (Caribe y Pacífico), cada una con:**
- Temperatura del último día: `{temp_hoy}` °C
- Cambio frente al día anterior: `{cambio}` °C, con flecha ↑ si subió y ↓ si bajó
- Anomalía: `{anomalia_hoy}` °C sobre lo normal
- Nivel de alerta: "Nivel `{nivel}` · `{nombre_nivel}`", con el color de su nivel
- Pie: Dato del `{fecha_ultimo_dato}`

> **Cálculo** (desde `temperatura_limpio.csv`, columnas `fecha`, `costa`, `sst_90`, `anomalia`, `alerta`):
> - `{fecha_ultimo_dato}`: la fecha más reciente del archivo.
> - Para cada costa y día se usa el **valor máximo de sus 2 estaciones** (las zonas más calientes).
> - `{temp_hoy}`: `sst_90` del último día. `{cambio}`: `sst_90` del último día menos el del día anterior.
> - `{anomalia_hoy}`: `anomalia` del último día. `{nivel}`: `alerta` del último día.
> - `{nombre_nivel}`: según la tabla de niveles de la sección 4b.

---

## 3. Antes de sumergirnos: conceptos clave

**Subtítulo:** Nosotros tampoco somos biólogos marinos, así que empecemos por lo básico.

| Concepto | Definición |
|---|---|
| **Coral** | Un animal, no una planta ni una piedra. Son colonias de pólipos diminutos que construyen un esqueleto duro de calcio. |
| **Algas del coral** | Algas microscópicas (zooxantelas) que viven dentro del coral. Le dan su color y la mayor parte de su alimento, y necesitan luz para vivir. |
| **Arrecife** | La estructura que forman los esqueletos de coral acumulados durante siglos. Es el hogar y la "guardería" de cientos de especies de peces. |
| **Coral somero** | Vive en aguas poco profundas e iluminadas: en este proyecto, hasta 50 m. Son los que forman arrecifes y los que sienten el calentamiento del mar. |
| **Coral profundo** | Vive a más de 50 m, casi sin luz. No tiene algas ni forma arrecifes, y no lo afecta la temperatura de la superficie. Por eso no se incluyó en el análisis. |
| **Blanqueamiento** | Cuando el agua se calienta demasiado, el coral expulsa sus algas y se ve blanco. No está muerto todavía, pero si el calor dura mucho, muere de hambre. |
| **Anomalía de temperatura** | Cuántos grados más (o menos) caliente está el mar comparado con lo normal para esa época del año. |
| **Calor acumulado (DHW)** | Suma cuánto calor extra ha soportado el coral en las últimas 12 semanas. Por eso un día un poco más fresco no baja el riesgo. |
| **Nivel de alerta** | Escala de NOAA del 0 al 7, que va de "sin estrés" a "mortalidad casi total", según el calor acumulado. |
| **El Niño** | Fenómeno natural en el que el Pacífico se calienta. Llega cada 2 a 7 años y, con el calentamiento global, alcanza temperaturas cada vez más altas. |
| **Estación virtual** | Un área del mar que un satélite vigila todos los días. Usamos 4: dos en el Caribe y dos en el Pacífico. |
| **GBIF y NOAA** | GBIF: base de datos mundial de registros de especies (de aquí salen los corales). NOAA: agencia de EE. UU. que mide la temperatura del mar por satélite. |

---

## 4. Contexto

### Los arrecifes de Panamá y por qué importan

Panamá tiene unos 800 km² de arrecifes de coral, más del 97 % en el Caribe. Los arrecifes sostienen la pesca, porque cientos de especies de peces dependen de ellos; atraen turismo y protegen las costas de las olas. Con el calentamiento del mar, los corales pueden blanquearse y morir si el calor dura demasiado.

En 2026, además, se discutió en la Asamblea un proyecto de ley que modificaba la protección de los arrecifes (Ley 304 de 2022); el proyecto fue vetado por el Ejecutivo.

### El blanqueamiento

**Fotos lado a lado:**
- `coral_sano` · etiqueta: **Coral sano** · crédito: emilytrytten, iNaturalist (CC BY-NC 4.0), Bocas del Toro, Panamá, 17 de enero de 2026. https://www.inaturalist.org/observations/403333743
- `coral_blanqueado` · etiqueta: **Coral blanqueado** · crédito: hubertszcz, iNaturalist (CC BY-NC 4.0), Bocas del Toro, Panamá, abril de 2022. https://www.inaturalist.org/observations/116020823

**Texto:** Cuando el mar se calienta más de lo normal durante semanas, el coral expulsa las algas que le dan color y alimento. Un coral blanqueado puede recuperarse si la temperatura vuelve a la normalidad, pero si el calor se prolonga, muere. NOAA mide este riesgo con una escala de 8 niveles:

| Nivel | Nombre | Color |
|---|---|---|
| 0 | Sin estrés | #1FA7A6 |
| 1 | Vigilancia | #FFC857 |
| 2 | Advertencia | #FF8A5B |
| 3 | Blanqueamiento probable | #E75480 |
| 4 | Mortalidad probable | #6C2E7B |
| 5 | Mortalidad de varias especies | #4A1F5C |
| 6 | Mortalidad severa | #2A0A4A |
| 7 | Mortalidad casi total | #000000 |

### El Niño y el calentamiento global: una ola sobre la marea alta

El Niño es un fenómeno natural: cada 2 a 7 años, el agua del Pacífico se calienta más de lo normal. El calentamiento global sube la temperatura base del mar, como una marea que sube. Por eso, cada El Niño ocurre sobre un mar más caliente que el anterior y llega más lejos, como una ola sobre la marea alta.

---

## 5. La pregunta

**Pregunta de investigación (recuadro destacado):**
¿Cómo ha cambiado el estrés térmico en el Caribe y el Pacífico de Panamá desde 1985, y qué tan expuestos están los corales registrados en cada costa a un riesgo potencial de blanqueamiento?

**Fuentes de datos (dos tarjetas):**
- **GBIF:** registros de corales en Panamá: especie, ubicación, profundidad y fecha.
- **NOAA Coral Reef Watch:** temperatura diaria del mar desde 1985 en 4 estaciones virtuales (2 en el Caribe y 2 en el Pacífico).

**Cómo lo analizamos:** Al principio quisimos comparar los corales con la temperatura año por año, pero los registros de corales no lo permiten: casi todos son de un solo año (2002) y no hay registros con profundidad durante los El Niño más fuertes. Por eso unimos los datos **por costa**: la temperatura muestra cómo cambió el estrés térmico en cada costa, y los corales muestran qué especies viven ahí.

---

## 6. Análisis: 

### Hallazgo 1 · El mar de Panamá se ha calentado

**Gráfica:** líneas de la anomalía promedio por año, una para el Caribe y otra para el Pacífico, con una línea punteada en 0 (lo normal). **Tabla pequeña:** anomalía promedio por década y costa.

**Texto:** Hasta inicios de los 2000, la temperatura del mar estaba cerca de lo normal, e incluso hubo años más fríos. Desde 2002, todos los años han estado por encima de lo normal. Los picos coinciden con eventos de El Niño, pero cada pico es más alto que el anterior. En el Caribe, la anomalía promedio pasó de `{anomalia_caribe_1980s}` °C en los años 80 a `{anomalia_caribe_2020s}` °C en los años 2020; en el Pacífico, de `{anomalia_pacifico_1980s}` °C a `{anomalia_pacifico_2020s}` °C.

> **Cálculo:** `anomalia_por_anio.csv` (columnas `anio`, `costa`, `anomalia`, `decada`). Solo años completos. La década 2020 incluye de 2020 al último año completo.

### Hallazgo 2 · El estrés extremo pasó de ser una excepción a ser lo normal

**Gráfica:** mapa de calor (semáforo) con los años en columnas y dos filas (Caribe y Pacífico); cada cuadro tiene el color del nivel de alerta más alto de ese año. Leyenda con los 8 niveles.

**Texto:** Durante las primeras tres décadas predomina el nivel 2 (Advertencia), y los años con niveles altos son pocos y coinciden con eventos de El Niño, como 1997-98. Desde 2015 el patrón cambia: los niveles 4 o superiores aparecen casi todos los años en al menos una costa. De los `{casos_nivel5}` casos (costa-año) con nivel 5 o superior, `{casos_nivel5_desde_2016}` ocurrieron desde 2016. En 2023, el Caribe llegó al nivel 7 (mortalidad casi total), el máximo de la escala.

> **Cálculo:** `semaforo_por_anio.csv` (columnas `costa`, `anio`, `alerta_max`). `{casos_nivel5}`: filas con `alerta_max` ≥ 5. `{casos_nivel5_desde_2016}`: las mismas, con `anio` ≥ 2016.

### Hallazgo 3 · Cada costa tiene corales únicos

**Gráfica:** mapa de Panamá con un punto por registro de coral somero (Caribe en #1FA7A6, Pacífico en #E75480) y las 4 estaciones de NOAA como estrellas:

| Estación | Longitud | Latitud |
|---|---|---|
| Atlantic East | -78.700 | 9.200 |
| Atlantic West | -81.650 | 9.200 |
| Pacific East | -79.325 | 8.175 |
| Pacific West | -82.250 | 7.725 |

**Tres tarjetas KPI:** Especies en el Caribe: `{especies_caribe}` · Especies en el Pacífico: `{especies_pacifico}` · Especies compartidas: `{especies_compartidas}`

**Texto:** Las `{especies_caribe}` especies de coral registradas en el Caribe y las `{especies_pacifico}` del Pacífico no se comparten entre sí. Desde que el istmo de Panamá se cerró, hace unos 3 millones de años, los corales de cada océano evolucionaron por separado. Por eso, si se pierde un arrecife, sus especies no se encuentran en la otra costa.

> **Cálculo:** `corales_someros_por_costa.csv` (columnas `costa`, `species`, `latitud`, `longitud`). Especies = valores distintos de `species` por costa. Compartidas = especies que aparecen en las dos costas.

### Hallazgo 4 · Los corales pasan casi dos meses al año en riesgo

**Gráfica:** barras agrupadas por costa: días al año en nivel 4 o superior, promedio de 1985-2014 (color #FF8A5B) frente a 2015-2025 (color #6C2E7B), con el número sobre cada barra.

**Texto:** Los días al año en nivel 4 de alerta o superior (mortalidad probable) aumentaron en ambas costas. En el Caribe pasaron de `{dias_caribe_antes}` a `{dias_caribe_ahora}` días al año; en el Pacífico, de `{dias_pacifico_antes}` a `{dias_pacifico_ahora}`. Lo que antes era un par de días hoy dura casi dos meses, y un coral blanqueado no suele resistir tanto tiempo.

> **Cálculo:** `exposicion_por_costa.csv` (columnas `costa`, `dias_n4_1985_2014`, `dias_n4_2015_2025`).

---

## 7. ¿Cómo va 2026?

**Tres tarjetas KPI por costa** (o seis tarjetas en dos filas):
- Anomalía promedio de 2026: `{anomalia_2026}` °C
- Días en nivel 4 o superior en 2026: `{dias_2026}`
- Nivel máximo alcanzado en 2026: `{nivel_max_2026}` · `{nombre_nivel}`

**Texto:** Hasta la fecha de la última descarga (`{fecha_ultimo_dato}`), 2026 ya es un año de estrés térmico extremo, sobre todo en el Pacífico. Según NOAA (actualización del 8 de octubre de 2026), El Niño sigue fortaleciéndose, con un 83 % de probabilidad de ser el más fuerte desde 1950 entre octubre y diciembre, y se espera que dure hasta inicios de 2027. Como los meses que faltan coinciden con el pico de El Niño, es poco probable que la situación mejore antes de terminar el año. Además, en los datos el Caribe suele tener su peor año justo después de un El Niño, por lo que 2027 podría ser también un año de alto riesgo para sus corales.

> **Cálculo:** `{anomalia_2026}`: promedio de `anomalia` de 2026 por costa, desde `temperatura_limpio.csv`. `{dias_2026}` y `{nivel_max_2026}`: fila de 2026 de cada costa en `semaforo_por_anio.csv` (`dias_nivel_4` y `alerta_max`).

---

## 8. Conclusión

Los datos muestran una vulnerabilidad clara en nuestros océanos. El calentamiento del mar en Panamá es evidente y avanza con o sin El Niño: desde 2002, ningún año ha estado por debajo de lo normal, y cada evento llega a temperaturas más altas que el anterior.

El estrés térmico ya no es una excepción. En los últimos años, ambas costas alcanzan cada año el nivel 4 de alerta o superior, y los días en riesgo pasaron de un par a casi dos meses al año. Un coral blanqueado puede recuperarse si el calor baja a tiempo, pero el estrés prolongado puede causar su muerte. Además, cada costa tiene corales únicos: lo que se pierde en una no se recupera con la otra.

Lo positivo es que cada vez más personas, entre científicos y aficionados, registran corales en plataformas abiertas. Estas iniciativas podrían ampliarse, por ejemplo anotando la profundidad, para medir el impacto del El Niño actual y de los que vengan.

Aunque este estudio se enfoca en los corales, todo está conectado: los arrecifes son el hogar y la zona de crianza de cientos de especies de peces, sostienen la pesca y el turismo de comunidades costeras, y protegen nuestras costas del oleaje. Por eso, como ciudadanos, debemos estar atentos a cómo se toman las decisiones sobre la protección de nuestros océanos.

**Frase final destacada:** Los datos abiertos nos permiten ver lo que está pasando; lo que hagamos con esa información depende de todos.

---

## 9. Pie: limitaciones y fuentes

### Limitaciones

- **Presencia, no abundancia:** los registros de GBIF indican que un coral fue visto en un lugar, no cuántos corales hay ni si están sanos.
- **Sesgo de muestreo:** el 95 % de los registros con año corresponde a 2002 (monitoreo de AGRRA en el Caribe), y no hay registros con profundidad anotada durante los El Niño más fuertes. Por eso no se pudo comparar año por año.
- **Pocos datos del Pacífico:** el 61 % de sus registros no tiene profundidad y se excluyó; su diversidad podría estar subestimada.
- **NOAA estima el riesgo, no lo mide:** los niveles de alerta indican la probabilidad de blanqueamiento según la temperatura, no observaciones reales de corales blanqueados.
- **Las estaciones son áreas grandes:** cada costa se representa con 2 estaciones virtuales, que pueden no reflejar las condiciones exactas de cada arrecife.
- **El año actual está incompleto:** se excluye de los promedios anuales y por década.

### Fuentes

- Corales: GBIF, descarga 0041553-260928105237408.
- Temperatura: NOAA Coral Reef Watch, 5 km Regional Virtual Stations v3.1.
- Estado de El Niño: NOAA Climate Prediction Center, ENSO Diagnostic Discussion (8 de octubre de 2026).
- Arrecifes de Panamá y proyecto de ley: La Prensa, La Estrella de Panamá y Panamá América (2025-2026).
- Contorno de Panamá: geoBoundaries (gbOpen, ADM0), con la licencia indicada por su API.
- Foto de coral blanqueado: hubertszcz, iNaturalist (CC BY-NC 4.0), Bocas del Toro, Panamá, abril de 2022. https://www.inaturalist.org/observations/116020823
- Foto de coral sano: emilytrytten, iNaturalist (CC BY-NC 4.0), Bocas del Toro, Panamá, 17 de enero de 2026. https://www.inaturalist.org/observations/403333743
