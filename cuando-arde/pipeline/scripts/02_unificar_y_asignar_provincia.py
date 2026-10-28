"""Unifica los CSV de FIRMS y asigna a cada detección la provincia del IGN.

Pasos:
  1. Lee todos los CSV anuales (NOAA-20 = N20, Suomi NPP = N).
  2. Agrega fecha/hora local (UTC-3), año, mes y banderas de filtro.
  3. Asigna provincia con prueba punto-en-polígono sobre los límites del IGN
     (centro del píxel; un píxel en el límite puede caer en la provincia vecina).
  4. Las detecciones que no caen en ningún polígono (costa, ríos limítrofes)
     se asignan a la provincia más cercana y se marcan con `prov_por_cercania`.

Salidas:
  data/processed/detecciones.pkl     (todas las filas, para análisis)
  data/processed/provincias_meta.csv (código INDEC, nombre, superficie en km²)

No usa geopandas (no disponible en este entorno): parsea el WKT a mano y usa
matplotlib.path para la prueba punto-en-polígono.
"""
import numpy as np
import pandas as pd
from matplotlib.path import Path as MplPath
from scipy.spatial import cKDTree

from comun import CRUDOS_FIRMS, PROC, carpeta, leer_provincias_ign, requerir

carpeta(PROC)
requerir(CRUDOS_FIRMS, "Copiá los CSV anuales de FIRMS en pipeline/data/raw/firms/. Ver docs/fuentes.md.")


# ---------- Límites provinciales ----------
def area_km2(anillo: np.ndarray) -> float:
    """Área aproximada (km²) con proyección equirectangular local. Suficiente para densidades."""
    lon, lat = anillo[:, 0], anillo[:, 1]
    lat0 = np.deg2rad(lat.mean())
    x = np.deg2rad(lon) * 6371.0 * np.cos(lat0)
    y = np.deg2rad(lat) * 6371.0
    return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


ign = leer_provincias_ign()
geoms, meta = {}, []
for r in ign.itertuples():
    polys = r.poligonos
    geoms[r.cod_indec] = polys
    sup = sum(area_km2(p[0]) - sum(area_km2(h) for h in p[1:]) for p in polys)
    todos = np.vstack([p[0] for p in polys])
    meta.append({
        "cod_indec": r.cod_indec, "provincia": r.provincia, "superficie_km2_aprox": round(sup),
        "lon_min": todos[:, 0].min(), "lon_max": todos[:, 0].max(),
        "lat_min": todos[:, 1].min(), "lat_max": todos[:, 1].max(),
    })
meta = pd.DataFrame(meta).sort_values("cod_indec")
meta.to_csv(PROC / "provincias_meta.csv", index=False)


# ---------- Detecciones ----------
partes = []
for f in sorted(CRUDOS_FIRMS.glob("*.csv")):
    d = pd.read_csv(f)
    d["sensor"] = "NOAA-20" if "jpss1" in f.name else "Suomi NPP"
    partes.append(d)
det = pd.concat(partes, ignore_index=True)

hhmm = det["acq_time"].astype(int).astype(str).str.zfill(4)
det["dt_utc"] = pd.to_datetime(det["acq_date"] + " " + hhmm, format="%Y-%m-%d %H%M")
det["dt_local"] = det["dt_utc"] - pd.Timedelta(hours=3)  # Argentina, UTC-3 sin horario de verano
det["fecha_local"] = det["dt_local"].dt.normalize()
det["anio"] = det["dt_local"].dt.year
det["mes"] = det["dt_local"].dt.month
det["es_vegetacion"] = det["type"] == 0
det["conf_nom_alta"] = det["confidence"].isin(["n", "h"])
det["filtro_base"] = det["es_vegetacion"] & det["conf_nom_alta"]


# ---------- Punto en polígono ----------
lon = det["longitude"].to_numpy()
lat = det["latitude"].to_numpy()
pts = np.column_stack([lon, lat])
cod = np.zeros(len(det), dtype=np.int64)

for _, m in meta.iterrows():
    en_caja = (lon >= m.lon_min) & (lon <= m.lon_max) & (lat >= m.lat_min) & (lat <= m.lat_max) & (cod == 0)
    idx = np.where(en_caja)[0]
    if len(idx) == 0:
        continue
    dentro = np.zeros(len(idx), dtype=bool)
    for poly in geoms[m.cod_indec]:
        ext = poly[0]
        bx = (pts[idx, 0] >= ext[:, 0].min()) & (pts[idx, 0] <= ext[:, 0].max()) & \
             (pts[idx, 1] >= ext[:, 1].min()) & (pts[idx, 1] <= ext[:, 1].max())
        if not bx.any():
            continue
        sub = idx[bx]
        en = MplPath(ext).contains_points(pts[sub])
        for hueco in poly[1:]:
            en &= ~MplPath(hueco).contains_points(pts[sub])
        dentro[bx] |= en
    cod[idx[dentro]] = m.cod_indec

det["cod_indec"] = cod
det["prov_por_cercania"] = False

# Sin polígono: asignar la provincia cuyo vértice de límite está más cerca
sin = np.where(cod == 0)[0]
if len(sin):
    verts, etiquetas = [], []
    for c, polys in geoms.items():
        for p in polys:
            paso = max(1, len(p[0]) // 4000)
            verts.append(p[0][::paso])
            etiquetas.append(np.full(len(p[0][::paso]), c))
    arbol = cKDTree(np.vstack(verts))
    etiquetas = np.concatenate(etiquetas)
    dist, j = arbol.query(pts[sin])
    det.loc[sin, "cod_indec"] = etiquetas[j]
    det.loc[sin, "prov_por_cercania"] = True
    det.loc[sin, "dist_limite_grados"] = dist

det = det.merge(meta[["cod_indec", "provincia"]], on="cod_indec", how="left")
det.to_pickle(PROC / "detecciones.pkl")

print("Detecciones totales:", len(det))
print("Asignadas por polígono:", int((~det["prov_por_cercania"]).sum()))
print("Asignadas por cercanía:", int(det["prov_por_cercania"].sum()))
if det["prov_por_cercania"].any():
    print("  distancia máx. al límite (grados):", round(det["dist_limite_grados"].max(), 3))
print(meta[["cod_indec", "provincia", "superficie_km2_aprox"]].to_string(index=False))
