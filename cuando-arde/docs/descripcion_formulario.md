# Descripción metodológica para el formulario (borrador, máx. 200 palabras)

> Borrador para que el equipo lo revise y ajuste. Las cifras están verificadas en
> `docs/metodologia.md`. Contar las palabras después de editar.

---

Usamos detecciones satelitales de calor VIIRS 375 m de NASA FIRMS (procesamiento estándar), con
NOAA-20 como serie principal (2019–2025) y Suomi NPP como control: por provincia y año, ambos
coinciden (correlación de rangos 0,997). Una detección es un píxel con calor anómalo, no un
incendio: no contamos incendios ni superficie quemada. Filtramos presuntos fuegos de vegetación
con confianza nominal o alta y excluimos 90 celdas con actividad casi permanente (probables
fuentes industriales). Cada detección se asigna a su provincia con los límites del IGN.

"Lo habitual" de cada celda, provincia y mes es la mediana de los otros años, para no comparar un
año consigo mismo. Así medimos cuándo arde cada región y cuánto se apartaron 2020 y 2022.

Sumamos la lluvia mensual de GPM IMERG Final (NASA), en la misma grilla de 0,1°, hasta agosto de
2025. Probamos si el fuego de más llegó tras meses secos, comparando con años normales como
control. Lo presentamos como coincidencia temporal, no como causa. Siete años no alcanzan para
hablar de tendencias.

Todo el procesamiento es reproducible con scripts en Python publicados en el repositorio.
