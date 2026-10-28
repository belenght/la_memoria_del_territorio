# Pipeline de datos

Python 3.11+ (sin geopandas: los límites del IGN se leen como WKT y la prueba
punto-en-polígono usa `matplotlib.path`).

```bash
pip install -r requirements.txt
```

## Datos de entrada (no se versionan)

Van en `pipeline/data/raw/`; cómo conseguirlos está en [`../docs/fuentes.md`](../docs/fuentes.md).

| Carpeta | Contenido |
|---|---|
| `firms/` | `viirs-jpss1_AAAA_Argentina.csv` (NOAA-20) y `viirs-snpp_AAAA_Argentina.csv` (Suomi NPP), 2018–2025 |
| `ign/` | `provincia.csv`: límites provinciales del IGN con geometría WKT |
| `imerg/` | NetCDF mensuales de GPM IMERG Final V07 (enero 2019 – agosto 2025) |

No se editan a mano: toda corrección se hace en los scripts.

## Ejecución

Desde `pipeline/`, en orden:

| Script | Qué hace | Tiempo aprox. |
|---|---|---|
| `01_auditar_crudos.py` | Audita los CSV de FIRMS (filas, fechas, tipos, confianza) | 10 s |
| `02_unificar_y_asignar_provincia.py` | Une los CSV, hora local y provincia de cada detección → `data/processed/detecciones.pkl` | 5 min |
| `03_experimento_viabilidad.py` | Consistencia entre satélites, estacionalidad, celdas persistentes | 1 min |
| `04_construir_base_analitica.py` | Filtro base, celdas persistentes y eventos aproximados → `base_analitica.pkl` | 3 min |
| `05_hipotesis_etapa_b.py` | Hipótesis del calendario del fuego (picos, años anómalos, robustez) | 30 s |
| `06_exportar_limites.py` | Límites provinciales simplificados → `app/public/datos/provincias.geojson` | 20 s |
| `07_exportar_fuego.py` | Datos de fuego de la app → `app/public/datos/fuego.json.gz` | 1 min |
| `08_lluvia_imerg.py` | Lluvia mensual por celda, provincia y región; lo habitual | 1 min |
| `09_hipotesis_fuego_lluvia.py` | Hipótesis fuego vs. lluvia, con años de control | 1 min |
| `10_exportar_lluvia.py` | Datos de lluvia de la app → `app/public/datos/lluvia.json` y `lluvia_celdas.bin.gz`; imprime las cifras del relato | 30 s |

`comun.py` reúne las rutas y las decisiones que comparten los scripts (años, satélites,
regiones, lectura del IGN y el cálculo de "lo habitual").

Los `.pkl` dependen de la versión de pandas: conviene regenerarlos en cada máquina con 02 y 04.

## Controles de reproducibilidad

Si todo está bien, los scripts imprimen, entre otras:

- 02: 3.530.047 detecciones totales; 6.628 asignadas a provincia por cercanía.
- 04: base analítica con 2.799.000 detecciones (ambos satélites, 2019–2025); 90 celdas persistentes.
- 07: NOAA-20 total 2020 = 388.942; 2022 = 267.210; caso Corrientes: 7.864 detecciones en 25 días.
- 09: 1.390.126 detecciones NOAA-20 en la serie base.
- 10: exceso de fuego tras 3 meses secos: 2020 84,0%, 2022 71,3%, años de control 52,9%.

## Salidas de análisis (`outputs/`)

| Carpeta | Script | Contenido |
|---|---|---|
| `auditoria_crudos.csv` | 01 | Resumen de cada archivo crudo |
| `experimento/` | 03 | Tablas e1–e6 e informe de viabilidad |
| `base/` | 04 | Celdas persistentes y sensibilidad de los eventos aproximados |
| `etapa_b/` | 05 | Hipótesis del fuego |
| `lluvia/` | 08, 09 | Lluvia por provincia y región, hipótesis fuego vs. lluvia |
