// Animaciones con reloj: recorrer los meses, avanzar el caso del punto día por día y
// alternar los dos satélites. Todas avanzan cambiando el estado con fijar().

import { SENSOR_CONTROL, SENSOR_PRINCIPAL } from "./config.js";
import { enPunto } from "./estado.js";
import { $, movimientoReducido } from "./util.js";

export function crearReproduccion({ estado, fijar, modelo }) {
  const relojes = { meses: null, caso: null, satelites: null };
  const boton = $("btn-play");

  function parar(nombre) {
    clearInterval(relojes[nombre]);
    relojes[nombre] = null;
  }

  function detenerMeses() {
    parar("meses");
    boton.textContent = "▶";
    boton.setAttribute("aria-label", "Reproducir los meses");
  }

  function animarCaso(paso = 420) {
    parar("caso");
    const ultimo = modelo.caso.dias - 1;
    if (movimientoReducido) return fijar({ dia: ultimo });
    fijar({ dia: 0 });
    relojes.caso = setInterval(() => {
      if (estado.dia >= ultimo) return parar("caso");
      fijar({ dia: estado.dia + 1 });
    }, paso);
  }

  // El botón ▶ reproduce los meses, o el caso del punto si está en pantalla
  function alternarReproduccion() {
    if (enPunto(estado)) return animarCaso();
    if (relojes.meses) return detenerMeses();
    boton.textContent = "❚❚";
    boton.setAttribute("aria-label", "Pausar");
    relojes.meses = setInterval(() => fijar({ mes: (estado.mes % 12) + 1 }), 1300);
  }
  boton.addEventListener("click", alternarReproduccion);

  function alternarSatelites(ms = 2600) {
    parar("satelites");
    if (estado.calendario === "agua") return;
    relojes.satelites = setInterval(() => fijar({
      sensor: estado.sensor === SENSOR_PRINCIPAL ? SENSOR_CONTROL : SENSOR_PRINCIPAL,
    }), ms);
  }

  return {
    alternarReproduccion,
    reproduciendoMeses: () => relojes.meses !== null,
    animarCaso,
    alternarSatelites,
    detenerMeses,
    detenerSatelites: () => parar("satelites"),
    detenerTodo() { detenerMeses(); parar("caso"); parar("satelites"); },
    // Suscriptor: corta las animaciones que dejaron de tener sentido
    vigilar(e) {
      if (!enPunto(e)) parar("caso");
      if (e.calendario === "agua") parar("satelites");
    },
  };
}
