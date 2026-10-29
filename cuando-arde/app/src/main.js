// Arranque: comprueba el navegador, carga los datos y conecta los módulos.
//
// Flujo: los controles y el relato cambian el estado con fijar(); cada cambio redibuja,
// en este orden, las animaciones (vigilar), la apariencia, los controles, la leyenda,
// el mapa, el indicador superior y el gráfico del relato.

import "./estilos.css";
import { crearControles } from "./controles.js";
import { cargarModelo } from "./datos.js";
import { crearEstado } from "./estado.js";
import { crearIndicador, renderApariencia, renderLeyenda } from "./indicadores.js";
import { crearMapa } from "./mapa.js";
import { crearRelato } from "./relato.js";
import { crearReproduccion } from "./reproduccion.js";
import { $ } from "./util.js";
import { crearVideo } from "./video.js";

function fallar(mensaje) {
  $("aviso").innerHTML = `<span>${mensaje}</span>`;
}

function navegadorCompatible() {
  const lienzo = document.createElement("canvas");
  if (!(lienzo.getContext("webgl2") || lienzo.getContext("webgl"))) {
    fallar("Este navegador no puede mostrar gráficos 3D (WebGL desactivado).<br>Probá con Chrome, Firefox o Safari actualizados.");
    return false;
  }
  if (!("DecompressionStream" in window)) {
    fallar("Este navegador es demasiado antiguo para abrir los datos.<br>Actualizalo o probá con otro.");
    return false;
  }
  return true;
}

async function arrancar() {
  if (!navegadorCompatible()) return;
  let modelo;
  try {
    modelo = await cargarModelo();
  } catch (error) {
    console.error(error);
    return fallar("No se pudieron cargar los datos.<br>Revisá la conexión y recargá la página.");
  }
  $("aviso-texto").textContent = "Armando el mapa…";

  const { estado, fijar, alCambiar } = crearEstado();
  const mapa = crearMapa(modelo, estado);
  const reproduccion = crearReproduccion({ estado, fijar, modelo });
  const relato = crearRelato({ estado, fijar, modelo, mapa, reproduccion });
  const video = crearVideo({ estado, fijar, modelo, mapa, reproduccion, irAlInicio: () => relato.irA(0) });
  const renderControles = crearControles({ estado, fijar, modelo, mapa, reproduccion, relato, video });
  const renderIndicador = crearIndicador(modelo);

  alCambiar(reproduccion.vigilar);
  alCambiar(renderApariencia);
  alCambiar(renderControles);
  alCambiar(renderLeyenda);
  alCambiar(mapa.render);
  alCambiar(renderIndicador);
  alCambiar(relato.renderGrafico);

  $("aviso").hidden = true;
  fijar();
  video.iniciar(); // cada visita empieza con el video; "Saltar" lleva al relato
}

arrancar();
