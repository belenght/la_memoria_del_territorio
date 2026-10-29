// Controles del lector: barra de tiempo (meses y años), satélite, provincia, comparar,
// selector Fuego/Agua, vista cenital, diálogo "Cómo leer esto" y modo liviano.

import { INICIALES, MESES } from "./config.js";
import { enAgua, enPunto } from "./estado.js";
import { $ } from "./util.js";

const nombreCorto = (p) => (p.startsWith("Tierra del Fuego") ? "Tierra del Fuego"
  : p.replace("Ciudad Autónoma de Buenos Aires", "CABA"));

export function crearControles({ estado, fijar, modelo, mapa, reproduccion, relato, video }) {
  // ---- Meses y años ----
  const meses = INICIALES.map((ini, k) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = ini;
    b.setAttribute("aria-label", MESES[k]);
    b.addEventListener("click", () => { reproduccion.detenerMeses(); fijar({ mes: k + 1, vista: "grilla" }); });
    $("meses").appendChild(b);
    return b;
  });
  const anios = ["tipico", ...modelo.anios.map(String)].map((modo) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "chip";
    b.dataset.modo = modo;
    b.textContent = modo === "tipico" ? "Año típico" : modo;
    b.addEventListener("click", () => fijar({ modo, vista: "grilla" }));
    $("anios").appendChild(b);
    return b;
  });

  // ---- Satélite, comparar y calendario ----
  const satelites = [...document.querySelectorAll("[data-sensor]")];
  satelites.forEach((b) => b.addEventListener("click", () => {
    reproduccion.detenerSatelites();
    fijar({ sensor: b.dataset.sensor, vista: "grilla" });
  }));
  const comparar = $("chk-comparar");
  comparar.addEventListener("change", () => fijar({ comparar: comparar.checked, vista: "grilla" }));
  const calendarios = [...document.querySelectorAll("[data-cal]")];
  calendarios.forEach((b) => b.addEventListener("click", () => relato.cambiarCalendario(b.dataset.cal)));

  // ---- Provincia ----
  const selector = $("sel-prov"), limpiar = $("btn-limpiar-prov");
  Object.keys(modelo.cajas).sort((a, b) => a.localeCompare(b, "es")).forEach((p) => {
    selector.add(new Option(nombreCorto(p), p));
  });
  selector.addEventListener("change", () => { fijar({ prov: selector.value, vista: "grilla" }); mapa.volarAProvincia(selector.value); });
  limpiar.addEventListener("click", () => { fijar({ prov: "" }); mapa.volarAProvincia(""); selector.focus(); });

  // ---- Vista, diálogo y modo liviano ----
  $("btn-cenital").addEventListener("click", () => {
    const estabaInclinada = mapa.alternarCenital();
    $("btn-cenital").textContent = estabaInclinada ? "Vista 3D" : "Vista cenital";
  });
  const dialogo = $("dlg-info"), liviano = $("chk-liviano");
  liviano.checked = mapa.liviano;
  liviano.addEventListener("change", () => { mapa.liviano = liviano.checked; });
  $("btn-info").addEventListener("click", () => dialogo.showModal());
  $("btn-cerrar").addEventListener("click", () => dialogo.close());
  $("btn-video").addEventListener("click", () => video.iniciar());

  // ---- Teclado: flechas para los meses, V para grabar el video (sin el botón Saltar) ----
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && video.activo()) return video.salir();
    if (dialogo.open || (ev.target instanceof Element && ev.target.closest("input, select"))) return;
    if (ev.key === "v" || ev.key === "V") return video.iniciar({ grabacion: true });
    if (enPunto(estado)) return;
    if (ev.key === "ArrowRight") { reproduccion.detenerMeses(); fijar({ mes: (estado.mes % 12) + 1 }); }
    if (ev.key === "ArrowLeft") { reproduccion.detenerMeses(); fijar({ mes: ((estado.mes + 10) % 12) + 1 }); }
  });

  // Refleja el estado en los controles
  return function render(e) {
    const punto = enPunto(e), hayAnio = e.modo !== "tipico";
    meses.forEach((b, k) => b.setAttribute("aria-pressed", String(!punto && k + 1 === e.mes)));
    anios.forEach((b) => b.setAttribute("aria-pressed", String(!punto && b.dataset.modo === e.modo)));
    satelites.forEach((b) => {
      b.setAttribute("aria-pressed", String(b.dataset.sensor === e.sensor));
      b.disabled = enAgua(e);
    });
    calendarios.forEach((b) => {
      b.setAttribute("aria-pressed", String(b.dataset.cal === e.calendario));
      b.disabled = punto;
    });
    comparar.disabled = !hayAnio;
    comparar.checked = hayAnio && e.comparar;
    $("lbl-comparar").setAttribute("aria-disabled", String(!hayAnio));
    selector.value = e.prov;
    selector.classList.toggle("activo", !!e.prov);
    limpiar.hidden = !e.prov;
  };
}
