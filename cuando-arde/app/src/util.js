// Ayudas chicas que usan varios módulos.

export const $ = (id) => document.getElementById(id);
export const espera = (ms) => new Promise((ok) => setTimeout(ok, ms));
export const movimientoReducido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export const fmt = new Intl.NumberFormat("es-AR");
export const fmt1 = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 1, minimumFractionDigits: 1 });

// localStorage puede fallar (modo privado, datos bloqueados): nunca debe romper la app
export function leerPreferencia(clave) {
  try { return localStorage.getItem(clave); } catch { return null; }
}
export function guardarPreferencia(clave, valor) {
  try { localStorage.setItem(clave, valor); } catch { /* sin preferencias guardadas */ }
}

export function mediana(valores) {
  if (!valores.length) return 0;
  valores.sort((a, b) => a - b);
  const m = valores.length >> 1;
  return valores.length % 2 ? valores[m] : (valores[m - 1] + valores[m]) / 2;
}
