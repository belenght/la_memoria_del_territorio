# App: El calendario del fuego

Sitio estático con [Vite](https://vite.dev) y JavaScript sin framework. El mapa 3D usa
[deck.gl](https://deck.gl) 8.9 (licencia MIT), sin mapa base de terceros: solo los límites
del IGN.

```bash
npm install
npm run dev       # servidor de desarrollo con recarga
npm run build     # sitio estático en dist/
npm run preview   # sirve dist/ para revisarlo
```

## Cómo está organizado `src/`

La app tiene **un estado único** (`estado.js`). Los controles y el relato lo cambian con
`fijar(cambios)`; cada cambio redibuja todo lo que depende de él. Ningún módulo modifica la
interfaz de otro.

| Módulo | Qué hace |
|---|---|
| `main.js` | Arranque: comprueba el navegador, carga los datos y conecta los módulos. |
| `config.js` | Constantes: meses, rutas de datos, cámara, escalas y textos de cada calendario. |
| `datos.js` | Baja y decodifica los datos; calcula los valores del mapa (con caché). |
| `estado.js` | El estado y sus derivados (`enAgua`, `enPunto`, `comparando`). |
| `mapa.js` | deck.gl: capas, tooltip, cámara y modo liviano. |
| `colores.js` | Rampas y colores de las columnas. |
| `indicadores.js` | Título y colores del calendario, indicador superior y leyenda. |
| `controles.js` | Barra de tiempo, filtros, selector Fuego/Agua, diálogo y teclado. |
| `relato.js` | Tarjeta de capítulos, navegación y gráfico chico de cada capítulo. |
| `capitulos.js` | **Contenido** del relato (textos, cifras, cámara). Se edita sin tocar lógica. |
| `graficos.js` | Gráficos SVG del relato (calendario doble y barras). |
| `reproduccion.js` | Animaciones con reloj: meses, caso del punto, alternar satélites. |
| `video.js` | Modo video de ~55 s para grabar la entrega (tecla V; Esc para salir). |
| `util.js` | Ayudas: formato de números, preferencias guardadas, mediana. |

## Datos (`public/datos/`)

Los genera el pipeline (`pipeline/scripts/06`, `07` y `10`); no se editan a mano.

| Archivo | Contenido |
|---|---|
| `fuego.json.gz` | Detecciones por celda de 0,1° y mes, ambos satélites; series nacionales y provinciales; caso del punto. |
| `lluvia.json` | Calendarios de lluvia por región y provincia, serie nacional y resumen de la hipótesis. |
| `lluvia_celdas.bin.gz` | Lluvia por celda y mes (Uint16, mm; 65535 = sin datos). |
| `provincias.geojson` | Límites provinciales del IGN simplificados, sin el sector antártico. |

Los `.gz` se descomprimen en el navegador; si el servidor ya los entrega descomprimidos,
la app lo detecta y los usa tal cual.

## Para agregar algo

- **Un capítulo o un texto**: `capitulos.js`. Toda cifra nueva tiene que salir de un script
  del pipeline (el 10 imprime las que usa el relato).
- **Una capa o un modo de color**: `mapa.js` y `colores.js`.
- **Un control**: el HTML en `index.html`, el comportamiento en `controles.js`, y lo que
  cambia en el estado en `estado.js`.
