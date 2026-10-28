// Relato guiado: tarjeta con los capítulos, su navegación y el gráfico chico de cada uno.

import { CAPITULOS, ULTIMO, versionDe } from "./capitulos.js";
import { SENSOR_PRINCIPAL } from "./config.js";
import { barrasPreviosSecos, calendarioProvincia, calendarioRegion } from "./graficos.js";
import { $, guardarPreferencia, leerPreferencia, movimientoReducido } from "./util.js";

const PIES = {
  regiones: "<span class='f'>▲ fuego</span>: % de las detecciones del año (año típico) · <span class='l'>▼ lluvia</span>: mm por mes (mediana 2019–2025). Cada calendario tiene su escala.",
  prov: "<span class='f'>▲ detecciones</span> y <span class='l'>▼ lluvia</span> de cada mes · rayita: lo habitual · franja celeste: los 3 meses previos al mes elegido",
  previosSecos: "Barra: % del exceso de detecciones (por provincia y mes) que llegó después de 3 meses con menos lluvia que lo habitual. Raya: el % de todos los provincia-meses de esos años en esa situación, lo esperable si no hubiera relación.",
};

export function crearRelato({ estado, fijar, modelo, mapa, reproduccion }) {
  const tarjeta = $("relato"), pastilla = $("btn-mostrar-relato"), btnOcultar = $("btn-ocultar-relato");
  const puntos = $("puntos");

  CAPITULOS.forEach((c, k) => {
    const b = document.createElement("button");
    b.type = "button";
    b.setAttribute("aria-label", `Capítulo ${k + 1}: ${c.titulo}`);
    b.addEventListener("click", () => irA(k));
    puntos.appendChild(b);
  });

  function mostrarTextos(c) {
    $("rel-titulo").textContent = c.titulo;
    $("rel-texto").textContent = c.texto;
    $("rel-nota").textContent = c.nota;
  }

  function irA(k) {
    reproduccion.detenerTodo();
    const c = versionDe(CAPITULOS[k], estado.calendario);
    const explorar = k === ULTIMO;
    $("rel-paso").textContent = `${k + 1} / ${CAPITULOS.length} · ${c.paso}`;
    $("pastilla-paso").textContent = `${k + 1}/${CAPITULOS.length}`;
    mostrarTextos(c);
    [...puntos.children].forEach((b, j) => b.setAttribute("aria-current", j === k ? "step" : "false"));
    $("btn-ant").disabled = k === 0;
    $("btn-sig").textContent = explorar ? "Volver al inicio" : "Siguiente →";
    $("btn-cenital").textContent = "Vista cenital";

    if (c.tipo === "punto") {
      fijar({ capitulo: k, vista: "punto", sensor: SENSOR_PRINCIPAL, prov: "" });
      mapa.volar(mapa.encuadre(modelo.caso.caja, 0.15, { pitch: 40, bearing: -10 }), 2400);
      setTimeout(() => { if (estado.capitulo === k) reproduccion.animarCaso(); }, movimientoReducido ? 0 : 2300);
      return;
    }
    // En "Explorá" se conservan la provincia y el satélite que eligió el lector
    const prov = explorar ? estado.prov : "";
    fijar({
      capitulo: k, vista: "grilla", modo: c.modo, mes: c.mes, comparar: !!c.comparar, prov,
      sensor: explorar ? estado.sensor : SENSOR_PRINCIPAL,
    });
    if (explorar && prov) mapa.volarAProvincia(prov); else mapa.volar(c.vista);
    if (movimientoReducido) return;
    if (c.play) setTimeout(() => { if (estado.capitulo === k && !reproduccion.reproduciendoMeses()) reproduccion.alternarReproduccion(); }, 2600);
    if (c.alternar) setTimeout(() => { if (estado.capitulo === k) reproduccion.alternarSatelites(); }, 2200);
  }

  $("btn-ant").addEventListener("click", () => irA(Math.max(0, estado.capitulo - 1)));
  $("btn-sig").addEventListener("click", () => irA(estado.capitulo === ULTIMO ? 0 : estado.capitulo + 1));

  // Fuego <-> agua: los capítulos se rearman con su versión; "Explorá" conserva lo elegido
  function cambiarCalendario(calendario) {
    if (calendario === estado.calendario) return;
    if (estado.capitulo !== ULTIMO) {
      estado.calendario = calendario;
      return irA(estado.capitulo);
    }
    mostrarTextos(versionDe(CAPITULOS[ULTIMO], calendario));
    fijar({ calendario });
  }

  function renderGrafico(e) {
    const g = CAPITULOS[e.capitulo].grafico, figura = $("grafico-relato");
    const visible = !!g && e.vista === "grilla" && !tarjeta.hidden;
    figura.hidden = !visible;
    if (!visible) return;
    const contenedor = $("graficos-relato");
    contenedor.innerHTML = "";
    if (g.regiones) g.regiones.forEach((r) => calendarioRegion(contenedor, modelo, r, e.mes));
    else if (g.prov) calendarioProvincia(contenedor, modelo, g.prov, g.desde, e);
    else if (g.previosSecos) barrasPreviosSecos(contenedor, modelo);
    $("grafico-pie").innerHTML = PIES[g.regiones ? "regiones" : g.prov ? "prov" : "previosSecos"];
  }
  window.addEventListener("resize", () => renderGrafico(estado));

  function mostrar(visible, recordar = true) {
    tarjeta.hidden = !visible;
    pastilla.hidden = visible;
    btnOcultar.setAttribute("aria-expanded", String(visible));
    pastilla.setAttribute("aria-expanded", String(visible));
    if (recordar) guardarPreferencia("relatoOculto", visible ? "0" : "1");
    renderGrafico(estado);
  }
  btnOcultar.addEventListener("click", () => { mostrar(false); pastilla.focus({ preventScroll: true }); });
  pastilla.addEventListener("click", () => { mostrar(true); btnOcultar.focus({ preventScroll: true }); });
  mostrar(leerPreferencia("relatoOculto") !== "1", false);

  return { irA, cambiarCalendario, renderGrafico };
}
