// Estado único de la app. Toda la interfaz se redibuja a partir de él:
// los módulos cambian el estado con fijar() y se suscriben con alCambiar().

import { SENSOR_PRINCIPAL } from "./config.js";

export function crearEstado() {
  const estado = {
    calendario: "fuego",       // "fuego" | "agua"
    modo: "tipico",            // "tipico" o un año como texto ("2020")
    mes: 8,                    // 1..12
    comparar: false,           // comparar el año elegido con lo habitual
    prov: "",                  // provincia filtrada ("" = todo el país)
    sensor: SENSOR_PRINCIPAL,
    vista: "grilla",           // "grilla" (columnas) | "punto" (caso de Corrientes)
    dia: 0,                    // día del caso "Cómo leer un punto"
    capitulo: 0,
  };
  const oyentes = [];
  return {
    estado,
    fijar(cambios = {}) {
      Object.assign(estado, cambios);
      for (const oyente of oyentes) oyente(estado);
    },
    alCambiar(oyente) { oyentes.push(oyente); },
  };
}

// Valores derivados que consultan varios módulos
export const enPunto = (e) => e.vista === "punto";
export const enAgua = (e) => e.calendario === "agua" && !enPunto(e);   // el caso del punto siempre es fuego
export const comparando = (e) => !enPunto(e) && e.comparar && e.modo !== "tipico";
