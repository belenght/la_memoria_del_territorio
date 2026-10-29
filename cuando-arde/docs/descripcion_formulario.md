# Descripción metodológica para el formulario 

Datos: detecciones satelitales de calor VIIRS 375 m de NASA FIRMS (NOAA-20, 2019–2025; Suomi NPP
como control, con correlación de rangos 0,997 por provincia y año) y lluvia mensual GPM IMERG de
NASA (hasta agosto de 2025), en la misma grilla de 0,1°, con límites provinciales del IGN. Una
detección es un píxel con calor anómalo, no un incendio: no contamos incendios ni superficie
quemada. Filtramos fuegos de vegetación con confianza nominal o alta y excluimos 90
celdas de actividad casi permanente. "Lo habitual" es la mediana de los otros años, para no
comparar un año consigo mismo. La relación entre lluvia y fuego se presenta como coincidencia
temporal, no como causa.

Diseño: un mapa 3D donde cada columna es una celda de 11 km en un mes, para que el calendario se
vea como movimiento. Un selector alterna los calendarios del fuego y del agua sobre la misma
grilla; un relato de diez capítulos guía la lectura y luego libera la exploración.

Uso de IA: Claude (Anthropic) asistió en los aspectos técnicos relacionados a la codificación y la estructura del proyecto, bajo total supervisión del equipo.