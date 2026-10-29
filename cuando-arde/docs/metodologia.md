# Metodología

## Pregunta
¿Cuándo arde cada región de Argentina, y qué pasa cuando un año rompe ese calendario?

## Unidad de análisis
**Detección VIIRS 375 m**: un píxel donde el sensor midió calor anómalo en una pasada. No es un
incendio (un incendio puede dejar cientos de detecciones) ni mide superficie quemada.

## Decisiones (fuego)
- Serie principal: **NOAA-20**, procesamiento estándar, **2019–2025** (2018 se excluye porque
  NOAA-20 empieza el 1/4/2018; 2026 por incompleto). Control: **Suomi NPP**.
- Filtro base: `type == 0` (presunto fuego de vegetación) y confianza nominal o alta. En
  Argentina FIRMS elimina las detecciones nocturnas de baja confianza (Anomalía Magnética del
  Atlántico Sur); usar solo n/h iguala el criterio entre día y noche.
- Se excluyen **90 celdas persistentes** de 0,01° (activas en ≥ 24 de los 84 meses de NOAA-20):
  probables fuentes no vegetales (industria, antorchas). ~0,6% de las detecciones.
- Hora local UTC−3 (`acq_time` viene en UTC). Provincia: punto-en-polígono con límites del IGN.
- **Lo habitual** = mediana de los **otros** años (leave-one-out), por celda o provincia y mes,
  para no comparar un año consigo mismo.
- **Eventos aproximados** (grilla 0,05°, vecinos 3×3, ≤ 1 día): un *proxy* para mostrar que muchas
  detecciones pertenecen a un mismo fuego. El conteo depende de los parámetros
  (`pipeline/outputs/base/sensibilidad_eventos.csv`); no se usa para contar incendios.

## Decisiones (lluvia)
- **GPM IMERG Final V07 mensual, 0,1°**: misma grilla que el fuego y cubre todo el país.
- Unidad del archivo: mm/hr → mm/mes con las horas de cada mes.
- Cada celda se asigna a la provincia que contiene su centro; provincia y región = media de sus
  celdas ponderada por cos(lat) (área de la celda).
- Datos hasta agosto de 2025: septiembre–diciembre de 2025 = sin datos. Lo habitual usa los años
  con dato (6 o 5 según el mes).

## Hallazgos verificados (NOAA-20, filtro base, sin celdas persistentes)
- 1.390.126 detecciones 2019–2025. Por provincia y año, NOAA-20 vs. Suomi NPP: Spearman 0,997.
- Picos: NEA y Pampeana en agosto (22% y 24% del año); NOA agosto–octubre (~20% cada uno;
  noviembre 16%, pero 9% sin 2022, que pesa el 59% de ese mes en el NOA); Patagonia diciembre–febrero (52%), y aporta el 4% del total nacional.
- 2020: 388.942 detecciones, 2,9× lo habitual; el 77% del exceso cayó dentro de la temporada
  habitual de cada provincia.
- 2022: 267.210 (1,9×); exceso en enero, febrero y noviembre. Corrientes enero + febrero:
  33.527. Salta noviembre: 20.881 (habitual ~1.093).

## Fuego y lluvia (hipótesis probadas, no afirmadas: `pipeline/scripts/09`)
- **Calendarios opuestos**: en las 5 regiones el pico del fuego cae entre los 3 meses más secos
  (fuego por mediana de los años, como en el script 09). Con el promedio que muestra la app, el
  pico del NOA pasa a septiembre (21% contra 20% en agosto), el cuarto mes más seco (7 mm): por
  eso el video dice "entre los meses más secos del año".
  La relación es más fuerte con la lluvia del mes anterior (Spearman ponderado −0,65) que con la
  del mismo mes (−0,40). 21 de 24 provincias dan correlación negativa. Son 12 meses por región:
  descriptivo, sin significancia estadística.
- **Años anómalos**: el 84% (2020) y el 71% (2022) del exceso de detecciones llegó tras 3 meses
  con lluvia por debajo de lo habitual, contra 62% y 56% esperables en esos años. En los años de
  control (2019, 2021, 2023, 2024): 53% contra 47%. La lluvia baja *en el mismo mes* del exceso,
  en cambio, aparece también en años normales (76%): no distingue a 2020 y 2022.
- Contraejemplos: Salta noviembre 2022 (los 3 meses previos llovió 1,4× lo habitual); Entre Ríos
  agosto 2022 (llovió 1,8× en el mes, aunque los 3 meses previos estuvieron en 0,4×).
- Es **coincidencia temporal, no causa**.

## Promedio y mediana: dónde se usa cada uno
- **Año típico del fuego = promedio 2019–2025** por celda y mes. Las detecciones son escasas y
  con muchos ceros: una celda que arde 3 de 7 años tiene mediana 0 y desaparecería del mapa. El
  promedio incluye 2020 y 2022 y los infla: el total anual promedio es ~199 mil detecciones contra
  ~147 mil de la mediana. La forma del calendario no cambia (mismos meses pico en NEA, Pampeana y
  Cuyo; Patagonia en verano con ambos), salvo noviembre en el NOA, que se aclara en el relato.
- **Año típico de la lluvia = mediana** de los años con dato: la lluvia es continua y la mediana
  resiste a meses extremos.
- **Lo habitual (fuego y lluvia) = mediana de los otros años**, siempre: es la vara con la que se
  mide si un año se apartó, y no debe dejarse arrastrar por los años extremos.

## Lo que no se afirma
Tendencias (7 años es poco), causas, cantidad de incendios, superficie quemada (FRP no es
superficie). Las detecciones no distinguen quemas agrícolas de incendios forestales, y los
fuegos breves, chicos o tapados por nubes pueden no aparecer.