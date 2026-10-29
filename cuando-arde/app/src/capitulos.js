// Contenido del relato. Toda cifra de estos textos sale de un script del pipeline:
// fuego en 03-05 y 07, lluvia en 08-10 (este último imprime las que se citan acá).
//
// Campos de cada capítulo:
//   paso, titulo, texto, nota   textos de la tarjeta
//   modo, mes, comparar, vista  estado del mapa y cámara al entrar
//   tipo: "punto"               muestra el caso "Cómo leer un punto" en lugar de las columnas
//   play / alternar             reproduce los meses / alterna los dos satélites al entrar
//   grafico                     gráfico chico de la tarjeta: {regiones: [...]},
//                               {prov, desde: [año, mes]} o {previosSecos: true}
//   agua                        lo que cambia en el calendario del agua (textos, mes, vista)

import { VISTA_PAIS } from "./config.js";

export const CAPITULOS = [
  {
    paso: "Inicio", titulo: "Cada luz es un lugar donde un satélite vio calor",
    texto: "Entre 2019 y 2025, el satélite NOAA-20 registró 1.390.126 detecciones de calor sobre Argentina. Cada columna reúne las de una celda de unos 11 km en un mes: cuanto más alta y más clara, más detecciones.",
    nota: "Una detección no es un incendio. El próximo capítulo muestra por qué.",
    modo: "tipico", mes: 8, vista: VISTA_PAIS, play: true,
    agua: {
      titulo: "Cada columna es la lluvia de un mes",
      texto: "La misma grilla, ahora con agua: cada columna es la lluvia que estimaron los satélites en una celda de unos 11 km durante un mes. Entre provincias, la diferencia es enorme: Misiones recibe en promedio unos 1.950 mm por año; San Juan, 150.",
      nota: "Lluvia: GPM IMERG (NASA), de enero de 2019 a agosto de 2025. Con «Fuego», arriba, volvés a las detecciones de calor.",
    },
  },
  {
    paso: "Cómo leer un punto", titulo: "Un punto no es un incendio", tipo: "punto",
    texto: "Estos son los 7.864 puntos que el satélite registró en el centro de Corrientes entre el 4 y el 28 de febrero de 2022, día por día. Se tocan en el espacio y en el tiempo: lo más probable es que sean el rastro de unos pocos frentes de fuego que avanzaron durante semanas, no de miles de incendios.",
    nota: "Casi la mitad (3.562) se detectó de noche. En todo el país, el 1% de los grupos de puntos más grandes reúne entre un tercio y dos tercios de todas las detecciones.",
  },
  {
    paso: "Un país, varios calendarios", titulo: "El norte y el centro arden a fines del invierno",
    texto: "En la región pampeana y en el NEA, agosto concentra casi una de cada cuatro detecciones del año (24% y 22%). Santa Fe, Formosa, Corrientes y Chaco reúnen la mitad de su año en apenas tres meses. Y llega al final de lo más seco: en las dos regiones, junio, julio y agosto son los meses con menos lluvia.",
    nota: "Año típico: promedio de 2019 a 2025.",
    modo: "tipico", mes: 8, vista: { longitude: -59.6, latitude: -28.6, zoom: 5.2, pitch: 58, bearing: -28 },
    grafico: { regiones: ["NEA", "Pampeana"] },
    agua: {
      titulo: "En el norte y el centro, el invierno es seco",
      texto: "En el NEA y la región pampeana, junio, julio y agosto son los meses con menos lluvia. El NEA recibe en julio unos 33 mm, contra 178 en noviembre. El fuego llega a su pico en agosto, al final de esa temporada seca.",
      nota: "Año típico: mediana de 2019 a 2025.",
    },
  },
  {
    paso: "Un país, varios calendarios", titulo: "En el NOA, la temporada va de agosto a octubre",
    texto: "Agosto, septiembre y octubre suman alrededor del 20% cada uno. Noviembre aparece con el 16%, pero casi el 60% de lo que se acumula ese mes en siete años es de 2022: Salta tuvo 20.881 detecciones, cuando lo habitual ronda las 1.100. Sin 2022, noviembre baja al 9%. Es la región con el invierno más seco: de junio a septiembre llueven menos de 10 mm por mes.",
    nota: "Año típico: promedio de 2019 a 2025, con 2020 y 2022 incluidos.",
    modo: "tipico", mes: 10, vista: { longitude: -64.6, latitude: -25.2, zoom: 5.3, pitch: 60, bearing: 18 },
    grafico: { regiones: ["NOA"] },
    agua: {
      titulo: "En el NOA, el invierno casi no tiene lluvia",
      texto: "De junio a septiembre llueven menos de 10 mm por mes; en agosto, apenas 2. En enero, en cambio, caen unos 117. La temporada de fuego, de agosto a octubre, cae en esos meses secos, y las lluvias vuelven recién en noviembre.",
      nota: "Año típico: mediana de 2019 a 2025.",
    },
  },
  {
    paso: "Un país, varios calendarios", titulo: "En Patagonia, el fuego es de verano",
    texto: "Diciembre, enero y febrero reúnen el 52% de las detecciones patagónicas, justo cuando el resto del país está en su punto más bajo. Son pocas en número: Patagonia aporta el 4% del total nacional. También la lluvia va al revés: llueve más en otoño e invierno y menos entre octubre y febrero.",
    nota: "Año típico: promedio de 2019 a 2025.",
    modo: "tipico", mes: 1, vista: { longitude: -69.4, latitude: -41.2, zoom: 5.0, pitch: 58, bearing: -8 },
    grafico: { regiones: ["Patagonia"] },
    agua: {
      titulo: "En Patagonia, la lluvia también va al revés",
      texto: "Al revés que en el norte, en Patagonia llueve más en otoño e invierno: unos 46 mm en junio, contra 14 en octubre. El verano, cuando se concentran sus detecciones de calor, está entre los meses más secos del año.",
      nota: "Año típico: mediana de 2019 a 2025.",
    },
  },
  {
    paso: "Cuando el calendario se rompe", titulo: "2020: la temporada de siempre, multiplicada",
    texto: "2020 tuvo 388.942 detecciones, 2,9 veces lo habitual. El exceso no cambió de época: el 77% cayó dentro de la temporada normal de cada provincia. En agosto, los mayores excesos se dieron en Formosa, Santa Fe y Entre Ríos. Ese mes, Formosa recibió el 30% de su lluvia habitual.",
    nota: "Columna llena: 2020. Contorno: lo habitual (mediana de los otros seis años).",
    modo: "2020", mes: 8, comparar: true, vista: { longitude: -59.8, latitude: -29.4, zoom: 5.4, pitch: 60, bearing: -22 },
    grafico: { prov: "Formosa", desde: [2020, 1] },
    agua: {
      titulo: "2020: un invierno más seco que lo habitual",
      texto: "En agosto de 2020 llovió en el país la mitad de lo habitual: 14 mm en promedio, contra 25. En el NEA, el 47%; en Chaco, el 11%. Es el mismo mes en que el fuego se multiplicó en esa región.",
      nota: "Gris: más seco que lo habitual. Celeste: más húmedo. Contorno: lo habitual (mediana de los otros años).",
    },
  },
  {
    paso: "Cuando el calendario se rompe", titulo: "2022: el fuego se adelantó al verano",
    texto: "En 2022 el exceso se concentró en enero, febrero y noviembre. Corrientes registró 33.527 detecciones entre enero y febrero, más de lo que suele acumular en un año entero. En noviembre, Salta tuvo 20.881, cuando lo habitual para ese mes ronda las 1.100. Antes del fuego faltó el agua: en diciembre de 2021 y enero de 2022, Corrientes recibió menos del 20% de su lluvia habitual.",
    nota: "No siempre coincide: en Salta, los tres meses previos a noviembre llovió más de lo habitual.",
    modo: "2022", mes: 2, comparar: true, vista: { longitude: -57.9, latitude: -28.3, zoom: 6.0, pitch: 60, bearing: 12 },
    grafico: { prov: "Corrientes", desde: [2021, 9] },
    agua: {
      titulo: "2022: el NEA se quedó sin agua en pleno verano", mes: 1,
      texto: "En diciembre de 2021 el NEA recibió el 22% de su lluvia habitual, y en enero de 2022, el 40%. Corrientes, menos del 20% en los dos meses. No fue todo el país: en enero, el promedio nacional superó lo habitual (81 mm contra 77).",
      nota: "No siempre coincide: en Salta, los tres meses previos al pico de fuego de noviembre llovió más de lo habitual.",
      vista: { longitude: -61.0, latitude: -29.5, zoom: 4.7, pitch: 55, bearing: 8 },
    },
  },
  {
    paso: "Cuando el calendario se rompe", titulo: "El fuego de más llegó después de lluvia de menos",
    texto: "En 2020, el 84% del exceso de detecciones se dio en provincias y meses que venían de tres meses con menos lluvia que lo habitual; en 2022, el 71%. Es más de lo esperable en años ya secos (62% y 56%). En los años normales casi no hay diferencia: 53% contra 47%.",
    nota: "Es una coincidencia en el tiempo, no la prueba de una causa. Lluvia: estimación satelital GPM IMERG (NASA).",
    modo: "2020", mes: 8, comparar: true, vista: { longitude: -61.5, latitude: -31.5, zoom: 4.4, pitch: 55, bearing: -18 },
    grafico: { previosSecos: true },
  },
  {
    paso: "¿Y si es el satélite?", titulo: "Otro satélite, el mismo calendario", alternar: true,
    texto: "Para descartar un defecto del instrumento, repetimos todo con Suomi NPP, un satélite con un sensor gemelo que pasa a otra hora. Por provincia y año, los dos coinciden casi exactamente (correlación de rangos 0,997), y 2020 y 2022 se destacan igual en ambos.",
    nota: "El mapa alterna entre los dos satélites cada pocos segundos. Suomi NPP tiene algunos días sin datos, por ejemplo del 27 de julio al 10 de agosto de 2022.",
    modo: "tipico", mes: 8, vista: { longitude: -61.5, latitude: -31.5, zoom: 4.4, pitch: 55, bearing: -18 },
    agua: {
      titulo: "La lluvia también se mide desde el espacio",
      texto: "IMERG combina mediciones de microondas e infrarrojo de varios satélites y las ajusta cada mes con datos de pluviómetros. Así cubre todo el país, Tierra del Fuego incluida, con la misma grilla de 11 km que usamos para el fuego.",
      nota: "Donde hay pocos pluviómetros, la estimación puede ser menos precisa. Los datos llegan hasta agosto de 2025.",
    },
  },
  {
    paso: "Explorá", titulo: "Ahora, el mapa es tuyo",
    texto: "Elegí un año, un mes, una provincia o el satélite en la barra de abajo, o reproducí los meses con ▶. Arrastrá para mover, usá clic derecho o dos dedos para inclinar y girar, y pasá sobre una columna para ver sus cifras.",
    nota: "Con un año elegido, activá «comparar con lo habitual» para ver dónde se apartó de su calendario.",
    modo: "tipico", mes: 9, vista: VISTA_PAIS,
    agua: {
      texto: "Elegí un año, un mes o una provincia en la barra de abajo, o reproducí los meses con ▶. Con «Fuego» y «Agua», arriba, cambiás de calendario sin perder el momento elegido.",
      nota: "Con un año elegido, activá «comparar con lo habitual»: en celeste, lo más húmedo; en gris, lo más seco.",
    },
  },
];

export const ULTIMO = CAPITULOS.length - 1;

// El capítulo tal como se muestra en el calendario elegido
export const versionDe = (capitulo, calendario) =>
  (calendario === "agua" && capitulo.agua ? { ...capitulo, ...capitulo.agua } : capitulo);