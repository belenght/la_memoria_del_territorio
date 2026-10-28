"""Calendario del agua: lluvia mensual por provincia y región con GPM IMERG Final V07.

Fuente: GPM_3IMERGM V07 (mensual, 0,1°), recorte Harmony -74,-56,-53,-21, variable
`precipitation`. Huffman et al. (2019), DOI 10.5067/GPM/IMERG/3B-MONTH/07.

Pasos:
  1. Lee los NetCDF (grupo "Grid"). Unidad en el archivo: mm/hr (tasa media del mes).
     Se convierte a mm/mes multiplicando por las horas del mes.
  2. Asigna cada celda de 0,1° a una provincia por el CENTRO de la celda
     (punto-en-polígono sobre los límites del IGN, igual que 02). Las celdas cuyo
     centro cae en el mar o fuera del país se descartan.
  3. Lluvia provincial = media de las celdas ponderada por cos(lat) (área de la celda).
     Región = media de sus provincias ponderada por la misma área de celdas.
  4. "Lo habitual" = mediana de los OTROS años con dato para ese mes (leave-one-out),
     como en 05. Con datos ene 2019 – ago 2025: ene–ago usan 6 años de referencia;
     sep–dic usan 5 (2019–2024 menos el año comparado). Sep–dic 2025 = sin datos.

Salidas:
  data/processed/lluvia_celdas.pkl          (celda x mes, mm; para la app)
  outputs/lluvia/lluvia_provincia_mes.csv   (provincia, año, mes, mm, habitual, n_ref, ratio)
  outputs/lluvia/lluvia_region_mes.csv      (ídem por región)
  outputs/lluvia/clima_region.csv           (mediana por región y mes, todos los años)
"""
import calendar

import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.path import Path as MplPath

from comun import ANIOS, CRUDOS_IMERG, PROC, REGION, SALIDAS, carpeta, leer_provincias_ign, requerir

SAL = carpeta(SALIDAS / "lluvia")
requerir(CRUDOS_IMERG, "Descargá IMERG mensual con el script de Harmony. Ver docs/fuentes.md.")

archivos = sorted(CRUDOS_IMERG.rglob("*3IMERG*.nc4"))
if not archivos:
    raise SystemExit(f"No se encontraron NetCDF de IMERG en {CRUDOS_IMERG}. Ver docs/fuentes.md.")


# ---------- 1. Lluvia mensual en mm ----------
capas = []
for f in archivos:
    da = xr.open_dataset(f, group="Grid")["precipitation"]
    unidad = da.attrs.get("units", "")
    if unidad != "mm/hr":
        raise SystemExit(f"Unidad inesperada en {f.name}: {unidad!r}")
    t = da["time"].values[0]
    horas = calendar.monthrange(t.year, t.month)[1] * 24
    mm = (da.isel(time=0) * horas).transpose("lat", "lon")
    capas.append(mm.expand_dims(anio_mes=[t.year * 100 + t.month]))
lluvia = xr.concat(capas, "anio_mes")
if int(lluvia.isnull().sum()) or float(lluvia.min()) < 0:
    raise SystemExit("Hay valores faltantes o negativos en IMERG; revisar CodeMissingValue.")

lat = lluvia["lat"].values
lon = lluvia["lon"].values
LON, LAT = np.meshgrid(lon, lat)
pts = np.column_stack([LON.ravel(), LAT.ravel()])


# ---------- 2. Celda -> provincia (centro de la celda, como 02) ----------
meta = pd.read_csv(PROC / "provincias_meta.csv")
cod = np.zeros(len(pts), dtype=np.int64)
for r in leer_provincias_ign().itertuples():
    for poly in r.poligonos:
        ext = poly[0]
        bx = (pts[:, 0] >= ext[:, 0].min()) & (pts[:, 0] <= ext[:, 0].max()) &              (pts[:, 1] >= ext[:, 1].min()) & (pts[:, 1] <= ext[:, 1].max()) & (cod == 0)
        if not bx.any():
            continue
        idx = np.where(bx)[0]
        en = MplPath(ext).contains_points(pts[idx])
        for hueco in poly[1:]:
            en &= ~MplPath(hueco).contains_points(pts[idx])
        cod[idx[en]] = r.cod_indec

# Provincias más chicas que una celda (CABA): la celda más cercana a su centro.
# Esa celda queda duplicada (cuenta también para la provincia vecina).
idx_celda = np.arange(len(pts))
for _, m in meta.iterrows():
    if not (cod == m.cod_indec).any():
        cx, cy = (m.lon_min + m.lon_max) / 2, (m.lat_min + m.lat_max) / 2
        j = np.argmin((pts[:, 0] - cx) ** 2 + (pts[:, 1] - cy) ** 2)
        print(f"{m.provincia}: sin centro de celda dentro; se usa la celda más cercana "
              f"({pts[j, 1]:.2f}, {pts[j, 0]:.2f}), que también cuenta para {int(cod[j])}")
        idx_celda = np.append(idx_celda, j)
        cod = np.append(cod, m.cod_indec)
pts = pts[idx_celda]


# ---------- 3. Tabla larga celda x mes ----------
valores = lluvia.values.reshape(lluvia.sizes["anio_mes"], -1)  # (meses, celdas)
en_pais = cod > 0
celdas = pd.DataFrame({
    "celda": idx_celda[en_pais],
    "lat": np.round(pts[en_pais, 1], 2),
    "lon": np.round(pts[en_pais, 0], 2),
    "cod_indec": cod[en_pais],
})
celdas["peso"] = np.cos(np.deg2rad(celdas["lat"]))
celdas["region"] = celdas["cod_indec"].map(REGION)
celdas = celdas.merge(meta[["cod_indec", "provincia"]], on="cod_indec", how="left")

am = lluvia["anio_mes"].values
larga = pd.DataFrame(valores[:, celdas["celda"].to_numpy()], index=am, columns=celdas.index)
larga = larga.stack().rename("mm").reset_index()
larga.columns = ["anio_mes", "fila", "mm"]
larga = larga.join(celdas, on="fila").drop(columns="fila")
larga["anio"] = larga["anio_mes"] // 100
larga["mes"] = larga["anio_mes"] % 100
larga[["anio", "mes", "lat", "lon", "cod_indec", "provincia", "region", "mm"]] \
    .astype({"mm": "float32"}).to_pickle(PROC / "lluvia_celdas.pkl")


def media_ponderada(df, claves):
    g = df.assign(mmp=df["mm"] * df["peso"]).groupby(claves)
    return (g["mmp"].sum() / g["peso"].sum()).rename("mm").reset_index()


# ---------- 4. Lo habitual (leave-one-out) ----------
def con_habitual(tabla, clave):
    filas = []
    for (k, mes), g in tabla.groupby([clave, "mes"]):
        serie = g.set_index("anio")["mm"]
        for anio in ANIOS:
            otros = serie.drop(anio, errors="ignore")
            filas.append({
                clave: k, "anio": anio, "mes": mes,
                "mm": serie.get(anio, np.nan),
                "habitual_mm": otros.median(),
                "n_anios_ref": len(otros),
            })
    t = pd.DataFrame(filas)
    t["ratio"] = t["mm"] / t["habitual_mm"]
    t["sin_datos"] = t["mm"].isna()
    return t.sort_values([clave, "anio", "mes"])


tp = media_ponderada(larga, ["provincia", "anio", "mes"])
tr = media_ponderada(larga, ["region", "anio", "mes"])
prov_mes = con_habitual(tp, "provincia")
reg_mes = con_habitual(tr, "region")
prov_mes.round(3).to_csv(SAL / "lluvia_provincia_mes.csv", index=False)
reg_mes.round(3).to_csv(SAL / "lluvia_region_mes.csv", index=False)

clima = tr.groupby(["region", "mes"])["mm"].median().unstack("mes")
clima.round(1).to_csv(SAL / "clima_region.csv")


# ---------- Controles ----------
print(f"Archivos: {len(archivos)}  meses: {am.min()}–{am.max()}")
print(f"Celdas en el país: {len(celdas)} de {lat.size * lon.size}")
print("Celdas por provincia:")
print(celdas.groupby("provincia").size().sort_values().to_string())
anual = tp[tp["anio"] < 2025].groupby(["provincia", "anio"])["mm"].sum().groupby("provincia").mean()
print("\nLluvia anual media 2019–2024 (mm):")
print(anual.round(0).sort_values().to_string())
print("\nMediana mensual por región (mm):")
print(clima.round(0).to_string())
fila_pct = clima.div(clima.sum(axis=1), axis=0) * 100
print("\nMediana mensual por región (% del año):")
print(fila_pct.round(0).to_string())
