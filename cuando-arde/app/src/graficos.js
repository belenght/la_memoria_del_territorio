// Gráficos SVG chicos que acompañan al relato: calendario doble (fuego arriba, lluvia
// abajo) por región o provincia, y barras de la hipótesis "3 meses previos secos".

import { INICIALES, MES_CORTO, SENSOR_PRINCIPAL } from "./config.js";
import { fmt } from "./util.js";

const SVGNS = "http://www.w3.org/2000/svg";
const FUENTE = "IBM Plex Mono, ui-monospace, monospace";
const C = { fuego: "#f2a33a", agua: "#59c3e6", texto: "#e8e4da", tenue: "#8d96a6", linea: "#2b3a52" };

function el(tag, attrs, padre) {
  const e = document.createElementNS(SVGNS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (padre) padre.appendChild(e);
  return e;
}

function texto(padre, contenido, attrs) {
  el("text", { "font-family": FUENTE, ...attrs }, padre).textContent = contenido;
}

// Agrega un bloque con título y un SVG del ancho disponible (medido en el momento)
function nuevoSvg(contenedor, tituloHtml, alto) {
  const caja = document.createElement("div");
  caja.innerHTML = `<div class="nombre">${tituloHtml}</div>`;
  contenedor.appendChild(caja);
  const ancho = Math.max(160, caja.clientWidth || 360);
  const svg = el("svg", { viewBox: `0 0 ${ancho} ${alto}`, role: "img", "aria-label": caja.textContent }, caja);
  svg.style.height = alto + "px";
  return { svg, ancho };
}

// cols: [{ini, fuego, fuegoHab, lluvia, lluviaHab, activo, previo, enero}]
function calendarioDoble(contenedor, tituloHtml, cols) {
  const H = 84, { svg, ancho } = nuevoSvg(contenedor, tituloHtml, H);
  const cw = ancho / cols.length, bw = Math.max(3, cw * 0.56);
  const base1 = 36, alto1 = 34, yIni = 47, base2 = 53, alto2 = 30;
  const maxF = Math.max(1, ...cols.map((c) => Math.max(c.fuego || 0, c.fuegoHab || 0)));
  const maxL = Math.max(1, ...cols.map((c) => Math.max(c.lluvia || 0, c.lluviaHab || 0)));
  const hayActivo = cols.some((c) => c.activo);
  const rayaHabitual = (x, y) => el("line", { x1: x - 2, x2: x + bw + 2, y1: y, y2: y, stroke: C.texto, "stroke-width": 1.5, "stroke-opacity": 0.85 }, svg);

  cols.forEach((c, i) => {
    const x = i * cw + (cw - bw) / 2, centro = i * cw + cw / 2, op = c.activo || !hayActivo ? 1 : 0.45;
    if (c.previo) el("rect", { x: i * cw, y: base2 - 2, width: cw, height: alto2 + 4, fill: C.agua, "fill-opacity": 0.16 }, svg);
    if (c.enero && i > 0) el("line", { x1: i * cw, x2: i * cw, y1: 0, y2: H, stroke: C.tenue, "stroke-opacity": 0.5, "stroke-dasharray": "2 3" }, svg);

    const hf = alto1 * (c.fuego || 0) / maxF;
    el("rect", { x, y: base1 - hf, width: bw, height: hf, fill: C.fuego, "fill-opacity": op }, svg);
    if (c.fuegoHab != null) rayaHabitual(x, base1 - alto1 * c.fuegoHab / maxF);

    texto(svg, c.ini, { x: centro, y: yIni, "text-anchor": "middle", "font-size": 9, fill: c.activo ? C.texto : C.tenue });

    if (c.lluvia == null) texto(svg, "s/d", { x: centro, y: base2 + 10, "text-anchor": "middle", "font-size": 8, fill: C.tenue });
    else el("rect", { x, y: base2, width: bw, height: alto2 * c.lluvia / maxL, fill: C.agua, "fill-opacity": op }, svg);
    if (c.lluviaHab != null) rayaHabitual(x, base2 + alto2 * c.lluviaHab / maxL);
  });
  el("line", { x1: 0, x2: ancho, y1: base1 + 0.5, y2: base1 + 0.5, stroke: C.linea }, svg);
  el("line", { x1: 0, x2: ancho, y1: base2 - 0.5, y2: base2 - 0.5, stroke: C.linea }, svg);
}

// Año típico de una región: % de las detecciones del año y mediana de lluvia por mes
export function calendarioRegion(contenedor, modelo, region, mes) {
  const S = modelo.fuego[SENSOR_PRINCIPAL].serie_prov, R = modelo.lluvia.regiones[region];
  const fuego = new Array(12).fill(0);
  for (const p of R.provincias) if (S[p]) S[p].tipico.forEach((v, m) => { fuego[m] += v; });
  const total = fuego.reduce((a, b) => a + b, 0) || 1;
  const pct = fuego.map((v) => (100 * v) / total), m = mes - 1;
  calendarioDoble(contenedor,
    `<b>${region}</b> ${MES_CORTO[m]} · ${Math.round(pct[m])}% · ${fmt.format(Math.round(R.mm[m]))} mm`,
    pct.map((v, k) => ({ ini: INICIALES[k], fuego: v, lluvia: R.mm[k], activo: k === m })));
}

// 12 meses de una provincia desde [año, mes], comparados con lo habitual
export function calendarioProvincia(contenedor, modelo, prov, desde, estado) {
  const S = modelo.fuego[SENSOR_PRINCIPAL].serie_prov[prov], P = modelo.lluvia.provincias[prov];
  const meses = Array.from({ length: 12 }, (_, k) => {
    const t = desde[1] - 1 + k;
    return { a: desde[0] + Math.floor(t / 12), m: (t % 12) + 1 };
  });
  const iAct = meses.findIndex((x) => String(x.a) === estado.modo && x.m === estado.mes);
  const cols = meses.map(({ a, m }, k) => {
    const f = S.anios[a], l = P[a];
    return {
      ini: INICIALES[m - 1], enero: m === 1, activo: k === iAct, previo: iAct >= 0 && k < iAct && k >= iAct - 3,
      fuego: f ? f.obs[m - 1] : 0, fuegoHab: f ? f.hab[m - 1] : null,
      lluvia: l ? l.mm[m - 1] : null, lluviaHab: l ? l.hab[m - 1] : null,
    };
  });
  const ult = meses[11];
  let titulo = `<b>${prov}</b> ${MES_CORTO[desde[1] - 1]} ${desde[0]} – ${MES_CORTO[ult.m - 1]} ${ult.a}`;
  if (iAct >= 0) {
    const c = cols[iAct], { a, m } = meses[iAct];
    titulo = `<b>${prov}</b> ${MES_CORTO[m - 1]} ${a}: ${fmt.format(c.fuego)} det. (hab. ${fmt.format(Math.round(c.fuegoHab))})`
      + (c.lluvia == null ? "" : ` · ${fmt.format(Math.round(c.lluvia))} mm (hab. ${fmt.format(Math.round(c.lluviaHab))})`);
  }
  calendarioDoble(contenedor, titulo, cols);
}

// % del exceso de fuego que llegó tras 3 meses secos, con su línea de base (raya)
export function barrasPreviosSecos(contenedor, modelo) {
  const L = modelo.lluvia;
  const filas = Object.keys(L.previos_secos).map((k) => {
    const control = k.startsWith("control");
    return { etq: control ? "años normales" : k, v: L.previos_secos[k], base: L.previos_secos_base[k], destacado: !control };
  });
  const H = 22 * filas.length + 4, { svg, ancho } = nuevoSvg(contenedor, "<b>Exceso de fuego tras 3 meses secos</b>", H);
  const x0 = 92, largo = ancho - x0 - 40;
  filas.forEach((f, i) => {
    const y = 4 + i * 22, xb = x0 + (largo * f.base) / 100;
    texto(svg, f.etq, { x: 0, y: y + 11, "font-size": 10, fill: f.destacado ? C.texto : C.tenue });
    el("rect", { x: x0, y, width: largo, height: 14, fill: C.linea, "fill-opacity": 0.5 }, svg);
    el("rect", { x: x0, y, width: (largo * f.v) / 100, height: 14, fill: f.destacado ? C.fuego : C.tenue }, svg);
    el("line", { x1: xb, x2: xb, y1: y - 2, y2: y + 16, stroke: C.texto, "stroke-width": 2 }, svg);
    texto(svg, Math.round(f.v) + "%", { x: x0 + largo + 6, y: y + 11, "font-size": 10, fill: C.texto });
  });
}
