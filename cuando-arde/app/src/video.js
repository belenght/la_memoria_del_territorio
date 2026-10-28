// Modo video: recorrido automático de ~55 segundos para grabar el video de la entrega.
// Tecla V para empezar, Esc para salir.

import { MESES, SENSOR_CONTROL, SENSOR_PRINCIPAL, VISTA_PAIS } from "./config.js";
import { $, espera } from "./util.js";

// Subtítulos del recorrido del año típico, por mes
const SUBTITULOS_ANIO = {
  7: "Cada columna: lo que el satélite detectó en un mes",
  8: "El norte y el centro arden a fines del invierno",
  10: "En el NOA, la temporada se estira",
  12: "En verano, el fuego se va al sur",
  2: "Patagonia arde cuando el resto del país descansa",
};

export function crearVideo({ fijar, modelo, mapa, reproduccion, irAlInicio }) {
  const sub = $("subtitulo-video"), salirBtn = $("btn-salir-video");
  let corrida = 0; // cada recorrido tiene su número; salir lo invalida

  function subtitulo(texto, chico) {
    sub.innerHTML = texto + (chico ? `<small>${chico}</small>` : "");
    sub.hidden = false;
  }

  function salir() {
    corrida++;
    reproduccion.detenerTodo();
    document.body.classList.remove("modo-video");
    sub.hidden = true;
    salirBtn.hidden = true;
    irAlInicio();
  }
  salirBtn.addEventListener("click", salir);

  async function iniciar() {
    const id = ++corrida;
    const sigue = async (ms) => { await espera(ms); return corrida === id; };
    reproduccion.detenerTodo();
    document.body.classList.add("modo-video");
    salirBtn.hidden = false;

    // 1. Llegada al país (5 s)
    fijar({ vista: "grilla", calendario: "fuego", modo: "tipico", mes: 6, comparar: false, prov: "", sensor: SENSOR_PRINCIPAL });
    mapa.saltarA({ ...VISTA_PAIS, zoom: 2.0, pitch: 0, bearing: 0 });
    await espera(300);
    mapa.volar(VISTA_PAIS, 4200);
    subtitulo("Siete años de calor visto desde el espacio", "Argentina · 2019–2025 · satélite NOAA-20");
    if (!(await sigue(5000))) return;

    // 2. Año típico mes a mes (13 s)
    for (const mes of [7, 8, 9, 10, 11, 12, 1, 2, 3, 4]) {
      fijar({ mes });
      if (SUBTITULOS_ANIO[mes]) subtitulo(SUBTITULOS_ANIO[mes], "año típico · " + MESES[mes - 1]);
      if (!(await sigue(1300))) return;
    }

    // 3. Cómo leer un punto (9 s)
    subtitulo("Un punto no es un incendio", "Corrientes · febrero de 2022 · 7.864 detecciones en 25 días");
    fijar({ vista: "punto", prov: "" });
    mapa.volar(mapa.encuadre(modelo.caso.caja, 0.15, { pitch: 40, bearing: -10 }), 2000);
    if (!(await sigue(1800))) return;
    reproduccion.animarCaso(260);
    if (!(await sigue(7200))) return;

    // 4. 2020 (7 s)
    fijar({ vista: "grilla", modo: "2020", mes: 8, comparar: true });
    mapa.volar({ longitude: -59.8, latitude: -29.4, zoom: 5.2, pitch: 60, bearing: -22 }, 2200);
    subtitulo("2020: la temporada de siempre, 2,9 veces más intensa", "columna llena: 2020 · contorno: lo habitual");
    if (!(await sigue(7000))) return;

    // 5. 2022 (7 s)
    fijar({ modo: "2022", mes: 2, comparar: true });
    mapa.volar({ longitude: -57.9, latitude: -28.3, zoom: 5.8, pitch: 60, bearing: 12 }, 2200);
    subtitulo("2022: el fuego se adelantó al verano", "Corrientes registró en dos meses más que en un año típico");
    if (!(await sigue(7000))) return;

    // 6. Otro satélite (6 s)
    fijar({ modo: "tipico", mes: 8, comparar: false });
    mapa.volar({ longitude: -61.5, latitude: -31.5, zoom: 4.4, pitch: 55, bearing: -18 }, 2000);
    subtitulo("Otro satélite, el mismo calendario", "NOAA-20 ↔ Suomi NPP · correlación 0,997");
    if (!(await sigue(1600))) return;
    for (let k = 0; k < 3; k++) {
      fijar({ sensor: k % 2 === 0 ? SENSOR_CONTROL : SENSOR_PRINCIPAL });
      if (!(await sigue(1500))) return;
    }

    // 7. Cierre (6 s)
    fijar({ sensor: SENSOR_PRINCIPAL, mes: 9 });
    mapa.volar({ ...VISTA_PAIS, zoom: 3.3, bearing: 8 }, 3000);
    subtitulo("El calendario del fuego", "Datos: NASA FIRMS (VIIRS 375 m) · límites: IGN");
    if (!(await sigue(6000))) return;
    salir();
  }

  return { iniciar, salir, activo: () => document.body.classList.contains("modo-video") };
}
