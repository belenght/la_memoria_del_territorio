"""Auditoría de los CSV anuales por país de NASA FIRMS (VIIRS 375 m).

Para cada archivo informa: filas, columnas, satélite, versión, rango de fechas,
días con datos, tipos de detección y niveles de confianza.
Uso (desde pipeline/): python scripts/01_auditar_crudos.py
"""
import pandas as pd

from comun import CRUDOS_FIRMS as CRUDOS, SALIDAS, carpeta

SALIDA = carpeta(SALIDAS) / "auditoria_crudos.csv"

archivos = sorted(CRUDOS.glob("*.csv"))
if not archivos:
    raise SystemExit(
        f"No se encontraron CSV en {CRUDOS}\n"
        "Creá la carpeta data/raw/firms y copiá ahí los archivos anuales de FIRMS "
        "(viirs-jpss1_AAAA_Argentina.csv, viirs-snpp_AAAA_Argentina.csv). Ver docs/fuentes.md."
    )

filas = []
for f in archivos:
    d = pd.read_csv(f)
    fechas = pd.to_datetime(d["acq_date"])
    filas.append({
        "archivo": f.name,
        "filas": len(d),
        "columnas": "|".join(d.columns),
        "satelite": "|".join(sorted(d["satellite"].astype(str).unique())),
        "version": "|".join(sorted(d["version"].astype(str).unique())),
        "fecha_min": fechas.min().date(),
        "fecha_max": fechas.max().date(),
        "dias_con_datos": fechas.dt.date.nunique(),
        **{f"type_{t}": int((d["type"] == t).sum()) for t in (0, 1, 2, 3)},
        **{f"conf_{c}": int((d["confidence"] == c).sum()) for c in ("l", "n", "h")},
        "noche_conf_l": int(((d["daynight"] == "N") & (d["confidence"] == "l")).sum()),
        "duplicados_exactos": int(d.duplicated().sum()),
    })

res = pd.DataFrame(filas)
res.to_csv(SALIDA, index=False)
pd.set_option("display.width", 250, "display.max_columns", 30)
print(res.drop(columns="columnas"))
print("\nEsquemas distintos de columnas:", res["columnas"].nunique())
for c in res["columnas"].unique():
    print(" -", c)
