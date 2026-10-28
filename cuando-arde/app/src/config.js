// Constantes de la app: textos de calendario, vistas de cámara y escalas del mapa.

export const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
  "septiembre", "octubre", "noviembre", "diciembre"];
export const MES_CORTO = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
export const INICIALES = ["E", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];

export const SENSOR_PRINCIPAL = "NOAA-20";
export const SENSOR_CONTROL = "Suomi NPP";

// Archivos que genera el pipeline (pipeline/scripts/06, 07 y 10) en public/datos/
export const ARCHIVOS = {
  fuego: "datos/fuego.json.gz",
  lluvia: "datos/lluvia.json",
  lluviaCeldas: "datos/lluvia_celdas.bin.gz",
  provincias: "datos/provincias.geojson",
};

export const VISTA_PAIS = { longitude: -63.8, latitude: -37.5, zoom: 3.55, pitch: 52, bearing: -14 };

// Columnas del mapa: la altura crece con la raíz cuadrada del valor
export const ELEVACION = 2600;
export const RADIO_COLUMNA = 4300;
export const VALOR_TOPE_COLOR = 400; // detecciones o mm a partir de los cuales el color satura

// Textos que cambian entre los dos calendarios
export const APARIENCIA = {
  fuego: {
    titulo: "del fuego",
    bajada: "Argentina · detecciones satelitales de calor · 2019–2025",
    documento: "El calendario del fuego",
    mapa: "Mapa 3D de Argentina con columnas que representan detecciones satelitales de calor por celda y mes",
  },
  agua: {
    titulo: "del agua",
    bajada: "Argentina · lluvia estimada por satélite · 2019–2025",
    documento: "El calendario del agua",
    mapa: "Mapa 3D de Argentina con columnas que representan la lluvia estimada por satélite por celda y mes",
  },
};
