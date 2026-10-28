// Carga de los datos que genera el pipeline y cálculo de los valores que muestra el mapa.
// Formatos documentados en pipeline/scripts/07_exportar_fuego.py y 10_exportar_lluvia.py.

import { ARCHIVOS, MESES } from "./config.js";
import { mediana } from "./util.js";

const SIN_DATO = 65535; // marca de "sin datos" en la matriz de lluvia

async function bajar(ruta) {
  const r = await fetch(import.meta.env.BASE_URL + ruta);
  if (!r.ok) throw new Error(`No se pudo bajar ${ruta} (${r.status})`);
  return r;
}

// Los .gz se descomprimen acá, salvo que el servidor ya los haya entregado descomprimidos
async function bajarBytes(ruta) {
  const bytes = new Uint8Array(await (await bajar(ruta)).arrayBuffer());
  if (bytes[0] !== 0x1f || bytes[1] !== 0x8b) return bytes;
  const flujo = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
  return new Uint8Array(await new Response(flujo).arrayBuffer());
}

const bajarJson = async (ruta) => (ruta.endsWith(".gz")
  ? JSON.parse(new TextDecoder().decode(await bajarBytes(ruta)))
  : (await bajar(ruta)).json());

export async function cargarModelo() {
  const [fuego, lluvia, matriz, provincias] = await Promise.all([
    bajarJson(ARCHIVOS.fuego),
    bajarJson(ARCHIVOS.lluvia),
    bajarBytes(ARCHIVOS.lluviaCeldas),
    bajarJson(ARCHIVOS.provincias),
  ]);
  return crearModelo(fuego, lluvia, new Uint16Array(matriz.buffer, matriz.byteOffset, matriz.byteLength / 2), provincias);
}

// [lon*100, lat*100, índice de provincia, ...] -> [{i, pos, prov}]
function decodificarCeldas(plano, provincias) {
  const n = plano.length / 3;
  return Array.from({ length: n }, (_, i) => ({
    i, pos: [plano[3 * i] / 100, plano[3 * i + 1] / 100], prov: provincias[plano[3 * i + 2]],
  }));
}

function cajasPorProvincia(celdas) {
  const cajas = {};
  for (const { pos: [x, y], prov } of celdas) {
    const b = cajas[prov] || (cajas[prov] = [180, 90, -180, -90]);
    b[0] = Math.min(b[0], x); b[1] = Math.min(b[1], y);
    b[2] = Math.max(b[2], x); b[3] = Math.max(b[3], y);
  }
  return cajas;
}

// Caso "Cómo leer un punto": detecciones individuales y su acumulado día por día
function decodificarCaso(P) {
  const puntos = [];
  for (let k = 0; k < P.pts.length; k += 4) {
    puntos.push({ pos: [P.pts[k] / 1000, P.pts[k + 1] / 1000], dia: P.pts[k + 2], noche: P.pts[k + 3] });
  }
  const acumulado = new Array(P.dias).fill(0);
  puntos.forEach((p) => acumulado[p.dia]++);
  for (let d = 1; d < P.dias; d++) acumulado[d] += acumulado[d - 1];
  const fecha = (dia) => {
    const f = new Date(P.inicio + "T12:00:00");
    f.setDate(f.getDate() + dia);
    return `${f.getDate()} de ${MESES[f.getMonth()]} de ${f.getFullYear()}`;
  };
  return { ...P, puntos, acumulado, fecha };
}

function crearModelo(F, L, matrizLluvia, geo) {
  const anios = F.meta.anios;
  const celdasFuego = decodificarCeldas(F.cells, F.provincias);
  const celdasAgua = decodificarCeldas(L.mapa.celdas, L.mapa.provincias);
  const cache = new Map();

  function memo(clave, calcular) {
    if (!cache.has(clave)) cache.set(clave, calcular());
    return cache.get(clave);
  }

  // Fuego: listas dispersas [celda, valor, ...] -> arreglos densos v (valor) y h (habitual)
  function fuegoEn(sensor, modo, mes) {
    return memo(`fuego|${sensor}|${modo}|${mes}`, () => {
      const S = F.sensores[sensor], n = celdasFuego.length;
      const v = new Float32Array(n), h = new Float32Array(n);
      if (modo === "tipico") {
        const a = S.tipico[mes];
        for (let k = 0; k < a.length; k += 2) v[a[k]] = a[k + 1] / 10;
      } else {
        const a = S.years[modo][mes];
        for (let k = 0; k < a.length; k += 3) { v[a[k]] = a[k + 1]; h[a[k]] = a[k + 2] / 2; }
      }
      return { v, h, sinDatos: false };
    });
  }

  // Agua: lo habitual (y el año típico) se calcula acá, como mediana de los años con dato
  const n = celdasAgua.length;
  const fila = (anio, mes) => ((anio - anios[0]) * 12 + mes - 1) * n;
  const hayDato = (anio, mes) => matrizLluvia[fila(anio, mes)] !== SIN_DATO;

  function aguaEn(modo, mes) {
    return memo(`agua|${modo}|${mes}`, () => {
      const v = new Float32Array(n), h = new Float32Array(n);
      const anio = modo === "tipico" ? null : Number(modo);
      const sinDatos = anio !== null && !hayDato(anio, mes);
      const otras = anios.filter((a) => a !== anio && hayDato(a, mes)).map((a) => fila(a, mes));
      const propia = anio !== null && !sinDatos ? fila(anio, mes) : null;
      const tmp = [];
      for (let i = 0; i < n; i++) {
        tmp.length = 0;
        for (const f of otras) tmp.push(matrizLluvia[f + i]);
        const med = mediana(tmp);
        if (anio === null) v[i] = med;
        else { h[i] = med; if (propia !== null) v[i] = matrizLluvia[propia + i]; }
      }
      return { v, h, sinDatos };
    });
  }

  return {
    anios,
    provincias: geo,
    celdasFuego,
    celdasAgua,
    cajas: cajasPorProvincia(celdasFuego),
    caso: decodificarCaso(F.punto),
    fuego: F.sensores,       // series nacionales y provinciales por satélite
    lluvia: L,               // series de lluvia, regiones y resumen de la hipótesis
    valores: (calendario, sensor, modo, mes) => (calendario === "agua" ? aguaEn(modo, mes) : fuegoEn(sensor, modo, mes)),
  };
}
