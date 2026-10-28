// Mapa 3D con deck.gl: provincias, columnas (fuego o lluvia), contorno de lo habitual
// y las detecciones del caso "Cómo leer un punto".

import { AmbientLight, Deck, DirectionalLight, FlyToInterpolator, LightingEffect, MapView, WebMercatorViewport } from "@deck.gl/core";
import { ColumnLayer, GeoJsonLayer, ScatterplotLayer } from "@deck.gl/layers";

import { CELDA_FUERA_DE_FILTRO, CONTORNO_HABITUAL, colorAgua, colorAguaVsHabitual, colorDeteccionCaso, colorFuego, colorFuegoVsHabitual } from "./colores.js";
import { ELEVACION, MESES, RADIO_COLUMNA, SENSOR_PRINCIPAL, VISTA_PAIS } from "./config.js";
import { comparando, enAgua, enPunto } from "./estado.js";
import { $, fmt, fmt1, guardarPreferencia, leerPreferencia, movimientoReducido } from "./util.js";

const PROVINCIA_CASO = "Corrientes";

const luz = new LightingEffect({
  ambiente: new AmbientLight({ color: [255, 255, 255], intensity: 1.1 }),
  sol: new DirectionalLight({ color: [255, 236, 210], intensity: 1.6, direction: [-2, -6, -3] }),
});

// Modo liviano: sin luces ni alta resolución, para celulares y equipos modestos
function livianoInicial() {
  const guardado = leerPreferencia("modoLiviano");
  if (guardado !== null) return guardado === "1";
  return window.matchMedia("(max-width: 760px)").matches
    || (navigator.hardwareConcurrency || 8) <= 4 || (navigator.deviceMemory || 8) <= 4;
}

export function crearMapa(modelo, estado) {
  let liviano = livianoInicial();
  let vista = { ...VISTA_PAIS, zoom: 2.2, pitch: 0, bearing: 0 };
  let actual = modelo.valores("fuego", SENSOR_PRINCIPAL, "tipico", 8);

  const pixeles = () => (liviano ? 1 : Math.min(window.devicePixelRatio || 1, 2));
  const transicion = () => (movimientoReducido ? 0 : liviano ? 450 : 700);

  function capas() {
    const punto = enPunto(estado), agua = enAgua(estado), anom = comparando(estado);
    const prov = punto ? PROVINCIA_CASO : estado.prov;
    const fuera = (d) => prov && d.prov !== prov;
    const clave = [estado.sensor, estado.modo, estado.mes, anom, prov, punto, agua].join("|");
    const celdas = agua ? modelo.celdasAgua : modelo.celdasFuego, sufijo = agua ? "-agua" : "";
    const color = agua ? (anom ? colorAguaVsHabitual : colorAgua) : (anom ? colorFuegoVsHabitual : colorFuego);
    const resaltada = (f) => prov && f.properties.nombre === prov;

    const lista = [
      new GeoJsonLayer({
        id: "provincias", data: modelo.provincias, stroked: true, filled: true, pickable: false,
        getFillColor: (f) => (resaltada(f) ? [24, 34, 51, 255] : [15, 23, 36, 255]),
        getLineColor: (f) => (resaltada(f) ? [242, 163, 58, 255] : [43, 58, 82, 255]),
        getLineWidth: (f) => (resaltada(f) ? 2.5 : 1),
        lineWidthUnits: "pixels", lineWidthMinPixels: 1,
        updateTriggers: { getFillColor: prov, getLineColor: prov, getLineWidth: prov },
      }),
      new ColumnLayer({
        id: "columnas" + sufijo, data: celdas, diskResolution: 4, angle: 45, radius: RADIO_COLUMNA,
        extruded: true, elevationScale: ELEVACION, pickable: !punto, visible: !punto,
        getPosition: (d) => d.pos,
        getElevation: (d) => {
          if (fuera(d)) return 0;
          const v = actual.v[d.i];
          return anom && v <= 0 && actual.h[d.i] > 0 ? 0.3 : Math.sqrt(v); // marca mínima si hubo 0
        },
        getFillColor: (d) => (fuera(d)
          ? (actual.v[d.i] > 0 ? CELDA_FUERA_DE_FILTRO : [0, 0, 0, 0])
          : color(actual.v[d.i], actual.h[d.i])),
        material: liviano ? false : { ambient: 0.55, diffuse: 0.6, shininess: 24, specularColor: agua ? [200, 230, 255] : [255, 220, 170] },
        updateTriggers: { getElevation: clave, getFillColor: clave },
        transitions: { getElevation: transicion(), getFillColor: transicion() },
      }),
    ];
    if (anom) {
      lista.push(new ColumnLayer({
        id: "habitual" + sufijo, data: celdas, diskResolution: 4, angle: 45, radius: RADIO_COLUMNA,
        extruded: true, filled: false, wireframe: true, elevationScale: ELEVACION,
        getPosition: (d) => d.pos,
        getElevation: (d) => (fuera(d) ? 0 : Math.sqrt(actual.h[d.i])),
        getLineColor: (d) => (!fuera(d) && actual.h[d.i] > 0 ? CONTORNO_HABITUAL : [0, 0, 0, 0]),
        updateTriggers: { getElevation: clave, getLineColor: clave },
        transitions: { getElevation: transicion() },
      }));
    }
    if (punto) {
      lista.push(new ScatterplotLayer({
        id: "caso", data: modelo.caso.puntos, radiusUnits: "meters", getRadius: 190, radiusMinPixels: 1.6, pickable: false,
        getPosition: (p) => p.pos,
        getFillColor: (p) => colorDeteccionCaso(p.dia, estado.dia),
        updateTriggers: { getFillColor: estado.dia },
      }));
    }
    return lista;
  }

  function tooltip({ object }) {
    if (!object || enPunto(estado)) return null;
    const v = actual.v[object.i], h = actual.h[object.i];
    if (v <= 0 && h <= 0) return null;
    const tipico = estado.modo === "tipico";
    const periodo = MESES[estado.mes - 1] + (tipico ? " · año típico" : " " + estado.modo);
    if (enAgua(estado)) {
      let html = `<b>${object.prov}</b><br>${periodo}<br>`;
      if (actual.sinDatos) return { html: html + "sin datos de lluvia" };
      html += `${fmt.format(Math.round(v))} mm de lluvia${tipico ? " (mediana)" : ""}`;
      if (!tipico) html += `<br><span style="opacity:.75">habitual: ${fmt.format(Math.round(h))} mm</span>`;
      return { html };
    }
    const satelite = estado.sensor !== SENSOR_PRINCIPAL ? " · " + estado.sensor : "";
    let html = `<b>${object.prov}</b><br>${periodo}${satelite}<br>`;
    html += tipico ? `${fmt1.format(v)} detecciones (promedio)` : `${fmt.format(v)} detecciones`;
    if (!tipico) html += `<br><span style="opacity:.75">habitual: ${fmt1.format(h)}</span>`;
    return { html };
  }

  const deck = new Deck({
    parent: $("mapa"),
    views: new MapView({ repeat: false }),
    initialViewState: vista,
    controller: { dragRotate: true, touchRotate: true, inertia: true },
    useDevicePixels: pixeles(),
    effects: liviano ? [] : [luz],
    layers: capas(),
    onViewStateChange: ({ viewState }) => { vista = viewState; return viewState; },
    getTooltip: tooltip,
  });

  function volar(destino, ms = 2200) {
    vista = { ...destino, transitionDuration: movimientoReducido ? 0 : ms, transitionInterpolator: new FlyToInterpolator() };
    deck.setProps({ initialViewState: vista });
  }

  // Vista que encuadra una caja [oeste, sur, este, norte] con un margen en grados
  function encuadre(caja, margen, extra) {
    const [o, s, e, n] = caja;
    let destino = { longitude: (o + e) / 2, latitude: (s + n) / 2, zoom: 6 };
    try {
      const vp = new WebMercatorViewport({ width: window.innerWidth, height: window.innerHeight });
      const a = vp.fitBounds([[o - margen, s - margen], [e + margen, n + margen]],
        { padding: Math.round(Math.min(window.innerWidth, window.innerHeight) * 0.15) });
      destino = { longitude: a.longitude, latitude: a.latitude, zoom: a.zoom };
    } catch { /* sin ajuste automático: se usa el centro de la caja */ }
    return { ...destino, zoom: Math.min(destino.zoom - 0.35, 8.5), ...extra };
  }

  return {
    render() {
      actual = modelo.valores(enAgua(estado) ? "agua" : "fuego", estado.sensor, estado.modo, estado.mes);
      deck.setProps({ layers: capas() });
    },
    volar,
    encuadre,
    volarAProvincia(prov) {
      if (!prov) return volar(VISTA_PAIS, 1400);
      volar(encuadre(modelo.cajas[prov], 0.3, { pitch: 55, bearing: -12 }), 1600);
    },
    alternarCenital() {
      const cenital = vista.pitch > 5;
      volar({ ...vista, pitch: cenital ? 0 : 55, bearing: cenital ? 0 : -14 }, 900);
      return cenital;
    },
    saltarA(destino) { vista = destino; deck.setProps({ initialViewState: vista }); },
    get liviano() { return liviano; },
    set liviano(valor) {
      liviano = valor;
      guardarPreferencia("modoLiviano", valor ? "1" : "0");
      deck.setProps({ useDevicePixels: pixeles(), effects: liviano ? [] : [luz], layers: capas() });
    },
  };
}
