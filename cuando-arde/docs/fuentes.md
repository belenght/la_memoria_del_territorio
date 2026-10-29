# Fuentes de datos

## NASA FIRMS — VIIRS 375 m Active Fire (estándar, colección 2)
- NOAA-20 (`viirs-jpss1`) y Suomi NPP (`viirs-snpp`), archivos anuales por país:
  https://firms.modaps.eosdis.nasa.gov/country/
- Atributos: https://earthdata.nasa.gov/data/tools/firms/active-fire-data-attributes-modis-viirs
- FAQ: https://www.earthdata.nasa.gov/faq/firms-faq
- Descargo LANCE: https://www.earthdata.nasa.gov/data/projects/lance/disclaimer
- Algoritmo: Schroeder, W. et al. (2014). DOI 10.1016/j.rse.2013.12.008
- Uso: datos abiertos, compartidos sin restricción según la guía de EOSDIS; citar con DOI.
- Productos estándar de origen (colección 2, LP DAAC): NOAA-20 VJ114IMG v002,
  DOI 10.5067/VIIRS/VJ114IMG.002 (desde 2018-01-01); Suomi NPP VNP14IMG v002,
  DOI 10.5067/VIIRS/VNP14IMG.002 (desde 2012-01-17). Fichas:
  https://www.earthdata.nasa.gov/data/catalog/lpcloud-vj114img-002 y
  https://www.earthdata.nasa.gov/data/catalog/lpcloud-vnp14img-002
  (la columna `version` = 2 de los CSV coincide con la colección 2; que FIRMS derive sus archivos
  estándar de estos productos es una inferencia razonable, no verificada en la documentación de FIRMS).
  La DOI del producto NRT es 10.5067/FIRMS/VIIRS/VJ114IMGT_NRT.002.
- El FAQ de FIRMS indica archivo NOAA-20 desde 2020-01-01, pero el CSV por país trae datos desde
  2018-04-01; la colección 2 estándar (VJ114IMG v002) cubre desde 2018. Igual se usa 2019-2025.

## NASA GES DISC — GPM IMERG Final, mensual (lluvia)
- Producto: GPM_3IMERGM V07, precipitación mensual, grilla de 0,1°.
  https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary
- Cita: Huffman, G.J., Stocker, E.F., Bolvin, D.T., Nelkin, E.J. y Tan, J. (2019). GPM IMERG
  Final Precipitation L3 1 month 0.1 degree x 0.1 degree V07. Greenbelt, MD: Goddard Earth
  Sciences Data and Information Services Center (GES DISC). DOI 10.5067/GPM/IMERG/3B-MONTH/07.
  Fecha de acceso: 27/10/2026.
- Licencia: datos abiertos sin restricción (CC0) según la política de datos de NASA Earthdata.
  Política: https://www.earthdata.nasa.gov/learn/use-data/data-use-policy ("NASA data are freely
  accessible"; misiones lideradas por NASA: CC0; pide citar el dataset y reconocer a NASA).
- Descarga: servicio Harmony de Earthdata (requiere cuenta gratuita de Earthdata Login), con
  recorte -74, -56, -53, -21 (oeste, sur, este, norte), variable `precipitation`, formato
  NetCDF4, enero 2019 – agosto 2025. Harmony genera un script de descarga por pedido; los
  archivos van en `pipeline/data/raw/imerg/`.
- Unidad en el archivo: mm/hr (tasa media del mes), verificada en el atributo `units`. El
  pipeline la convierte a mm/mes multiplicando por las horas de cada mes.
- Disponible hasta agosto de 2025 al momento de la descarga: septiembre–diciembre de 2025 se
  muestran como "sin datos". No se completa con IMERG Late (otro producto).
- PENDIENTE: captura o PDF de la política de datos de GES DISC.

## IGN — Límites provinciales
- Capa "provincia" (CSV con WKT), descargada del IGN.
- PENDIENTE: registrar licencia y fecha de descarga.
- PENDIENTE: fuente oficial de la superficie de Tierra del Fuego sin Antártida (se usa 21.571 km²).

## Decisiones metodológicas vigentes
- APROBADO (24/10): serie principal NOAA-20 2019-2025; Suomi NPP como control.
- APROBADO (24/10): exclusión de celdas persistentes (>= 24 de 84 meses).
- Reproducibilidad verificada en una segunda máquina (Windows) el 24/10: cifras idénticas.
- Referencia 'habitual' para anomalías: mediana de los otros seis años (leave-one-out).
- No se afirman tendencias (7 años es poco), causas, cantidad de incendios ni superficie quemada.
- Filtro base: type 0 + confianza n/h.
- Hora local: UTC-3 (acq_time viene en UTC).
