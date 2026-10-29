# Registro de uso de IA (para el Formulario de Inscripción, Anexo A)

| Fecha | Herramienta | Etapa | Finalidad |
|---|---|---|---|
| 2026-10-24 | Claude (Anthropic) | Etapa A: diagnóstico | Revisión de bases del concurso y documentación de NASA FIRMS |
| 2026-10-24 | Claude (Anthropic) | Etapa A: procesamiento | Scripts de auditoría, limpieza y unión espacial con provincias (revisados por el equipo) |
| 2026-10-24 | Claude (Anthropic) | Etapa A: exploración | Primer análisis exploratorio de viabilidad |
| 2026-10-24 | Claude (Anthropic) | Etapa B: investigación | Scripts 04-05 (base analítica, eventos aproximados, pruebas de hipótesis) y comparación de enfoques |
| 2026-10-24 | Claude (Anthropic) | Etapa C: diseño | Propuesta de experiencia 3D y prototipo de trabajo con deck.gl (decisiones visuales finales a cargo del equipo) |
| 2026-10-24 | Claude (Anthropic) | Prototipo v2-v3 | Relato ocultable, filtro por provincia, capítulo del caso Corrientes, selector de satélite, modo video y modo liviano |
| 2026-10-27 | Claude (Anthropic) | Extensión lluvia | Evaluación de fuentes de precipitación (IMERG, CHIRPS) y de sus licencias |
| 2026-10-27 | Claude (Anthropic) | Extensión lluvia | Verificación de unidades y grilla de IMERG y script 08 de procesamiento (mm/mes por provincia y región, lo habitual leave-one-out); revisado por el equipo |
| 2026-10-27 | Claude (Anthropic) | Extensión lluvia | Script 09: prueba de hipótesis fuego vs lluvia (calendarios por región/provincia, exceso de 2020/2022 vs lluvia, con años de control); interpretación revisada por el equipo |
| 2026-10-27 | Claude (Anthropic) | Extensión lluvia | Script 10 (export de lluvia para la app) y propuesta de integración en el prototipo: calendario fuego/lluvia en los capítulos de regiones, 2020 y 2022, capítulo nuevo sobre los 3 meses previos y textos con cifras verificadas; diseño final a cargo del equipo |
| 2026-10-27 | Claude (Anthropic) | Prototipo | Corrección de la plantilla para hosting propio (charset, regla [hidden]) y alto máximo del relato en celular |
| 2026-10-27 | Claude (Anthropic) | Prototipo | Modo "calendario del agua": export de lluvia por celda (script 10), selector Fuego/Agua que cambia capa del mapa, colores, título, indicador, leyenda y tooltip; propuesta a revisar por el equipo |
| 2026-10-27 | Claude (Anthropic) | Prototipo | Versión "agua" de los textos del relato (cifras calculadas por el script 10) y cambio de relato al alternar Fuego/Agua; textos a revisar por el equipo |
| 2026-10-27 | Claude (Anthropic) | Orden para la entrega | Reorganización del código bajo supervisión: módulo común del pipeline (comun.py) y limpieza de los scripts 01-10; app reescrita en módulos con Vite a partir del prototipo, con los mismos textos, datos y diseño; README, metodología, fuentes y borrador de la descripción del formulario para revisión del equipo |
| 2026-10-28 | Claude (Anthropic) | Modo video | Guion del recorrido automático en cuatro actos (el fuego tiene calendario, la lluvia lo explica, 2020 y 2022 lo rompen, lo que se repite) que alterna agua y fuego, con fundidos entre frases y frases y mapa sincronizados; cifras ya verificadas; se quitaron los tramos del punto de Corrientes y del satélite de control por tiempo; a revisar por el equipo |
| 2026-10-28 | Claude (Anthropic) | Modo video | El video se reproduce al entrar a la web, con botón «Saltar video»; botón «▶ Ver el video» en la barra superior (antes estaba dentro de «Cómo leer esto»); la tecla V lo inicia sin el botón Saltar visible, para grabar |
| 2026-10-28 | Claude (Anthropic) | Cómo leer esto | Guía de lectura propia para el calendario del agua (qué es un milímetro, estimación satelital, lo habitual, límites y método de IMERG), separada de la del fuego; el diálogo abre desde el título; textos a revisar por el equipo |
