// Modo video: recorrido automático de ~57 segundos para grabar el video de la entrega.
// Cuenta una sola historia en cuatro actos: el fuego tiene calendario, la lluvia también
// (al revés), hay años que lo rompen y lo que se repite. Cada escena cambia la frase y el
// mapa juntos, después de un fundido, y queda en pantalla al menos 4 segundos.
// Arranca solo al entrar; "Saltar video" o Esc lo cortan y llevan al relato.

import { SENSOR_PRINCIPAL, VISTA_PAIS } from "./config.js";
import { $, espera } from "./util.js";

const FUNDIDO = 450; // ms que tarda en irse una frase antes de que entre la siguiente

const VISTA_NORTE = { longitude: -61.5, latitude: -29.5, zoom: 4.3, pitch: 50, bearing: -12 };
const VISTA_SUR = { longitude: -68.5, latitude: -42.5, zoom: 4.0, pitch: 50, bearing: 10 };
const VISTA_2020 = { longitude: -60.2, latitude: -29.4, zoom: 5.0, pitch: 58, bearing: -18 };
const VISTA_2022 = { longitude: -58.6, latitude: -28.6, zoom: 5.3, pitch: 58, bearing: 10 };
const VISTA_CIERRE = { ...VISTA_PAIS, zoom: 3.4, bearing: 6 };

export function crearVideo({ estado, fijar, modelo, mapa, reproduccion, irAlInicio }) {
  const sub = $("subtitulo-video"), salirBtn = $("btn-salir-video");
  let corrida = 0;          // cada recorrido tiene su número; salir lo invalida
  let calendarioPrevio = "fuego";

  // Una escena: se va la frase anterior, y recién entonces cambian juntos el mapa y la frase
  async function escena({ cambios, vista, ms = 3000, texto, chico = "" }) {
    sub.classList.add("cambiando");
    if (!sub.hidden) await espera(FUNDIDO);
    if (cambios) fijar(cambios);
    if (vista) mapa.volar(vista, ms);
    sub.innerHTML = `<span class="frase">${texto}${chico ? `<small>${chico}</small>` : ""}</span>`;
    sub.hidden = false;
    sub.getBoundingClientRect(); // aplica el estado "cambiando" antes de quitarlo, para que el fundido de entrada se vea
    sub.classList.remove("cambiando");
  }

  function salir() {
    corrida++;
    reproduccion.detenerTodo();
    document.body.classList.remove("modo-video", "grabando");
    sub.hidden = true;
    salirBtn.hidden = true;
    estado.calendario = calendarioPrevio; // el relato vuelve en el calendario que tenía el lector
    irAlInicio();
  }
  salirBtn.addEventListener("click", salir);

  // Se reproduce al entrar a la web y con "Ver el video". Con { grabacion: true } (tecla V)
  // el botón "Saltar" queda invisible salvo al pasar el mouse, para grabar la pantalla limpia.
  async function iniciar({ grabacion = false } = {}) {
    const id = ++corrida;
    const sigue = async (ms) => { await espera(ms); return corrida === id; };
    // Avanza meses del año típico sin tocar la frase (el mes se lee arriba, en el indicador)
    const meses = async (lista, ms) => {
      for (const mes of lista) {
        fijar({ mes });
        if (!(await sigue(ms))) return false;
      }
      return true;
    };
    if (!document.body.classList.contains("modo-video")) calendarioPrevio = estado.calendario;
    reproduccion.detenerTodo();
    document.body.classList.add("modo-video");
    document.body.classList.toggle("grabando", grabacion);
    salirBtn.hidden = false;
    if (!grabacion) salirBtn.focus({ preventScroll: true }); // con teclado, Enter saltea
    sub.hidden = true;

    // ---- Acto 1: el fuego tiene calendario (15 s) ----
    mapa.saltarA({ ...VISTA_PAIS, zoom: 2.2, pitch: 0, bearing: 0 });
    await escena({
      cambios: { vista: "grilla", calendario: "fuego", modo: "tipico", mes: 8, comparar: false, prov: "", sensor: SENSOR_PRINCIPAL },
      vista: VISTA_PAIS, ms: 4000,
      texto: "Cada región de Argentina arde, año tras año, en las mismas fechas",
      chico: "detecciones de calor · satélite NOAA-20 · 2019–2025",
    });
    if (!(await sigue(5000))) return;

    await escena({ cambios: { mes: 8 }, vista: VISTA_NORTE, texto: "En el norte y el centro, a fines del invierno", chico: "año típico · agosto a octubre" });
    if (!(await sigue(1500)) || !(await meses([9, 10], 1500))) return;

    await escena({ cambios: { mes: 12 }, vista: VISTA_SUR, texto: "En la Patagonia, en pleno verano", chico: "año típico · diciembre a febrero" });
    if (!(await sigue(1500)) || !(await meses([1, 2], 1500))) return;

    // ---- Acto 2: la lluvia marca la fecha (13 s) ----
    await escena({
      cambios: { calendario: "agua", mes: 6 }, vista: VISTA_NORTE,
      texto: "¿Por qué en esas fechas? Miremos la lluvia",
      chico: "la misma grilla · lluvia estimada por satélite (GPM IMERG)",
    });
    if (!(await sigue(3800))) return;

    await escena({ texto: "En el norte, el invierno es la estación seca", chico: "año típico · junio a agosto" });
    if (!(await sigue(1000)) || !(await meses([7, 8], 1500))) return;

    await escena({
      cambios: { calendario: "fuego", mes: 8 },
      texto: "Primero se seca. Después, arde.",
      chico: "en las 5 regiones, el pico del fuego cae entre los meses más secos del año",
    });
    if (!(await sigue(4000))) return;

    // ---- Acto 3: cuando el calendario se rompe (18 s) ----
    await escena({
      cambios: { calendario: "agua", modo: "2020", mes: 8, comparar: true }, vista: VISTA_2020,
      texto: "Pero hay años que rompen el calendario",
      chico: "agosto de 2020 · en gris, menos lluvia que lo habitual",
    });
    if (!(await sigue(4000))) return;

    await escena({
      cambios: { calendario: "fuego" },
      texto: "En 2020, tras un invierno más seco, el fuego se multiplicó",
      chico: "el año cerró con 2,9 veces las detecciones habituales",
    });
    if (!(await sigue(4000))) return;

    await escena({
      cambios: { calendario: "agua", modo: "2022", mes: 1 }, vista: VISTA_2022,
      texto: "En 2022, el verano de Corrientes se quedó sin lluvia",
      chico: "diciembre y enero · menos del 20% de lo habitual",
    });
    if (!(await sigue(4000))) return;

    await escena({
      cambios: { calendario: "fuego", mes: 2 },
      texto: "Y el fuego llegó antes de tiempo",
      chico: "Corrientes: en dos meses, más detecciones que en un año típico",
    });
    if (!(await sigue(4000))) return;

    // ---- Acto 4: lo que se repite (11 s) ----
    await escena({
      cambios: { modo: "tipico", mes: 8, comparar: false }, vista: VISTA_CIERRE, ms: 3500,
      texto: "No es una ley, pero se repite",
      chico: "84% del fuego de más de 2020 y 71% del de 2022 llegó tras 3 meses más secos que lo habitual; lo esperable era 62% y 56%",
    });
    if (!(await sigue(5000))) return;

    await escena({
      texto: "Cuando el fuego se sale del calendario, antes suele haber llovido menos de lo habitual",
      chico: "El calendario del fuego y del agua · NASA FIRMS · GPM IMERG · IGN",
    });
    if (!(await sigue(5500))) return;
    salir();
  }

  return { iniciar, salir, activo: () => document.body.classList.contains("modo-video") };
}