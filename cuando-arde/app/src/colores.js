// Colores de las columnas del mapa ([r, g, b, a] para deck.gl).
// Comparando con lo habitual: por encima, el color de cada calendario (ámbar el fuego,
// celeste el agua); por debajo, gris en los dos, para que el fuego de menos no parezca agua.

import { VALOR_TOPE_COLOR } from "./config.js";

const RAMPA_FUEGO = [[90, 29, 12], [196, 82, 26], [242, 163, 58], [255, 231, 168], [255, 248, 232]];
const RAMPA_AGUA = [[12, 30, 58], [24, 78, 140], [58, 148, 210], [150, 214, 240], [236, 250, 255]];
const TRANSPARENTE = [0, 0, 0, 0];
const ESCALA = Math.sqrt(VALOR_TOPE_COLOR);

export function mezcla(t, rampa = RAMPA_FUEGO) {
  t = Math.max(0, Math.min(1, t)) * (rampa.length - 1);
  const i = Math.min(rampa.length - 2, Math.floor(t)), f = t - i, a = rampa[i], b = rampa[i + 1];
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
}

const enRampa = (rampa) => (v) => (v <= 0 ? TRANSPARENTE : [...mezcla(Math.sqrt(v) / ESCALA, rampa), 235]);
export const colorFuego = enRampa(RAMPA_FUEGO);
export const colorAgua = enRampa(RAMPA_AGUA);

const tonoFuego = (t) => [58 + 184 * t, 42 + 121 * t, 28 + 30 * t, 240];
const tonoAgua = (t) => [42 + 47 * t, 74 + 121 * t, 99 + 131 * t, 240];
const tonoGris = (t) => [58 + 102 * t, 62 + 106 * t, 70 + 112 * t, 240];

// Fuego: diferencia absoluta en escala logarítmica (satura en ±300 detecciones)
export function colorFuegoVsHabitual(v, h) {
  if (v <= 0 && h <= 0) return TRANSPARENTE;
  const d = v - h, t = Math.min(1, Math.log1p(Math.abs(d)) / Math.log1p(300));
  return d >= 0 ? tonoFuego(t) : tonoGris(t);
}

// Lluvia: cociente con lo habitual (satura en ×4 o ÷4); +5 mm evita que los meses
// casi sin lluvia exageren el contraste
export function colorAguaVsHabitual(v, h) {
  if (v <= 0 && h <= 0) return TRANSPARENTE;
  const r = Math.log((v + 5) / (h + 5)), t = Math.min(1, Math.abs(r) / Math.log(4));
  return r >= 0 ? tonoAgua(t) : tonoGris(t);
}

// Caso del punto: el día actual en blanco, los anteriores se apagan con la edad
export function colorDeteccionCaso(diaPunto, diaActual) {
  if (diaPunto > diaActual) return TRANSPARENTE;
  const edad = diaActual - diaPunto;
  if (edad === 0) return [255, 248, 232, 255];
  return [...mezcla(Math.max(0.12, 0.62 - edad * 0.05)), 215];
}

export const CONTORNO_HABITUAL = [232, 228, 218, 150];
export const CELDA_FUERA_DE_FILTRO = [141, 150, 166, 38];
