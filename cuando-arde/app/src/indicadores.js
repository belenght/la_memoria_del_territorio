// Partes de la interfaz que solo reflejan el estado: título y colores del calendario,
// indicador superior (período y cifras) y leyenda del mapa.

import { APARIENCIA, MESES, SENSOR_PRINCIPAL } from "./config.js";
import { comparando, enAgua, enPunto } from "./estado.js";
import { $, fmt, fmt1 } from "./util.js";

export function renderApariencia(estado) {
  const agua = enAgua(estado), textos = APARIENCIA[agua ? "agua" : "fuego"];
  document.body.classList.toggle("agua", agua);
  document.title = textos.documento;
  $("titulo-em").textContent = textos.titulo;
  $("bajada").textContent = textos.bajada;
  $("mapa").setAttribute("aria-label", textos.mapa);
}

export function renderLeyenda(estado) {
  const punto = enPunto(estado), agua = enAgua(estado), anom = comparando(estado);
  $("ley-fuego").hidden = punto || agua || anom;
  $("ley-fuego-habitual").hidden = punto || agua || !anom;
  $("ley-agua").hidden = !agua || anom;
  $("ley-agua-habitual").hidden = !agua || !anom;
  $("ley-punto").hidden = !punto;
}

// "1,3× lo habitual para ese mes (25 mm)"; por debajo de lo habitual se pinta gris
function razonHtml(valor, habitual, unidad = "") {
  if (!(habitual > 0)) return "";
  const r = valor / habitual;
  return `<b class="${r < 1 ? "menos" : ""}">${fmt1.format(r)}×</b> lo habitual para ese mes (${fmt.format(Math.round(habitual))}${unidad})`;
}

export function crearIndicador(modelo) {
  const periodo = $("hud-periodo"), cifra = $("hud-cifra"), razon = $("hud-razon");

  function caso(estado) {
    const C = modelo.caso;
    periodo.textContent = C.fecha(estado.dia);
    cifra.textContent = `${fmt.format(C.acumulado[estado.dia])} detecciones acumuladas`;
    razon.textContent = `día ${estado.dia + 1} de ${C.dias} · centro de Corrientes`;
  }

  function agua(estado, m, prov) {
    const donde = prov ? "en " + prov : "en promedio en el país";
    const L = modelo.lluvia;
    if (estado.modo === "tipico") {
      const t = prov ? L.provincias[prov].tipico[m] : L.mapa.nacional.tipico[m];
      cifra.textContent = `${fmt.format(Math.round(t))} mm de lluvia ${donde} (mediana 2019–2025)`;
      razon.textContent = "";
      return;
    }
    const serie = prov ? L.provincias[prov][estado.modo] : L.mapa.nacional[estado.modo];
    if (serie.mm[m] == null) {
      cifra.textContent = "Sin datos de lluvia para este mes";
      razon.textContent = "IMERG Final llega hasta agosto de 2025";
      return;
    }
    cifra.textContent = `${fmt.format(Math.round(serie.mm[m]))} mm de lluvia ${donde}`;
    razon.innerHTML = razonHtml(serie.mm[m], serie.hab[m], " mm");
  }

  function fuego(estado, m, prov) {
    const S = modelo.fuego[estado.sensor], donde = prov ? "en " + prov : "en el país";
    if (estado.modo === "tipico") {
      const t = prov ? S.serie_prov[prov].tipico[m] : S.nacional.tipico[m];
      cifra.textContent = `${fmt.format(Math.round(t))} detecciones ${donde} (promedio 2019–2025)`;
      razon.textContent = "";
      return;
    }
    const serie = prov ? S.serie_prov[prov].anios[estado.modo] : S.nacional[estado.modo];
    cifra.textContent = `${fmt.format(serie.obs[m])} detecciones ${donde}`;
    razon.innerHTML = razonHtml(serie.obs[m], serie.hab[m]);
  }

  return function render(estado) {
    $("hud-sat").hidden = estado.sensor === SENSOR_PRINCIPAL || enPunto(estado) || enAgua(estado);
    if (enPunto(estado)) return caso(estado);
    const m = estado.mes - 1, prov = estado.prov;
    periodo.textContent = (prov ? prov + " · " : "") + MESES[m] + (estado.modo === "tipico" ? " · año típico" : " " + estado.modo);
    (enAgua(estado) ? agua : fuego)(estado, m, prov);
  };
}
