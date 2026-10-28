# El calendario del fuego

**¿Cuándo arde cada región de Argentina, y qué pasa cuando un año rompe ese calendario?**

Exploración interactiva de las detecciones satelitales de calor (NASA FIRMS, VIIRS 375 m) y de
la lluvia estimada por satélite (GPM IMERG) en Argentina, 2019–2025. Proyecto para el Concurso
Nacional de Visualización de Datos *Contar con Datos* 2026, categoría Exploración interactiva.

> Una **detección** no es un incendio: un mismo incendio puede dejar cientos de detecciones.
> La app cuenta detecciones, no incendios ni superficie quemada.

## Estructura

```
├── app/                    Aplicación web (Vite + JavaScript, deck.gl)
│   ├── index.html
│   ├── src/                Código, un módulo por responsabilidad (ver app/README.md)
│   └── public/datos/       Datos que genera el pipeline (se versionan: la app los necesita)
├── pipeline/               Descarga, limpieza y análisis en Python
│   ├── scripts/            01–10, en orden; comun.py tiene rutas y decisiones compartidas
│   ├── outputs/            Tablas e informes de análisis (se versionan)
│   └── data/               Datos crudos y procesados (NO se versionan, ~800 MB)
└── docs/                   Fuentes, metodología y declaración de uso de IA
```

## Ver la app en local

Requiere Node.js 20.19 o superior.

```bash
cd app
npm install
npm run dev
```

Para generar el sitio estático (carpeta `app/dist/`, lista para cualquier hosting):

```bash
npm run build
```

`npm run preview` sirve esa carpeta para revisarla antes de publicar.

## Publicar

El sitio es estático: alcanza con subir `app/dist/` a cualquier hosting. El repositorio incluye
un flujo de GitHub Actions (`.github/workflows/publicar.yml`) que compila y publica en GitHub
Pages en cada push a `main`. Para activarlo: *Settings → Pages → Source: GitHub Actions*.

Por la evaluación anónima del concurso, publicar desde una cuenta con seudónimo.

## Reproducir los datos

Ver [`pipeline/README.md`](pipeline/README.md). Los datos crudos se descargan de las fuentes
listadas en [`docs/fuentes.md`](docs/fuentes.md); el pipeline regenera todo lo que hay en
`app/public/datos/` y `pipeline/outputs/`.

## Documentación

- [`docs/metodologia.md`](docs/metodologia.md): decisiones metodológicas, hallazgos y límites.
- [`docs/fuentes.md`](docs/fuentes.md): fuentes de datos, licencias y citas.
- [`docs/descripcion_formulario.md`](docs/descripcion_formulario.md): descripción metodológica para el formulario (máx. 200 palabras).
- [`docs/declaracion_ia.md`](docs/declaracion_ia.md): registro de uso de inteligencia artificial.
