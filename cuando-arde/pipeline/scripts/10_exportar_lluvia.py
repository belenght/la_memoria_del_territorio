"""Exporta la lluvia de la app (calendario del agua). Requiere 08 y 09.

lluvia.json
  regiones[r]    = {provincias[], mm[12]}       mediana mensual de la región (años con dato)
  provincias[p]  = {tipico[12], anio: {mm[12], hab[12]}}   null = sin datos;
                   hab = mediana de los otros años con dato (como en 08)
  previos_secos[k], previos_secos_base[k]       % del exceso de fuego tras 3 meses secos y su
                                                línea de base (09); k = "2020", "2022", "control ..."
  mapa = {provincias[], celdas[lon*100, lat*100, pid, ...], nacional{anio: {mm, hab}, tipico}}
lluvia_celdas.bin.gz
  Uint16 little-endian [mes][celda], mm redondeados; 65535 = sin datos.
  Mes 0 = enero de 2019 ... mes 83 = diciembre de 2025.

El fuego no se repite acá: la app lo toma de fuego.json.gz (07).
Al final imprime las cifras que citan los textos de la app, para verificarlas.

Salidas: app/public/datos/lluvia.json y app/public/datos/lluvia_celdas.bin.gz
"""
import gzip
import json

import numpy as np
import pandas as pd

from comun import ANIOS, DATOS_APP, PROC, REGION, SALIDAS, carpeta, mediana_otros_anios

LL = SALIDAS / "lluvia"
SIN_DATO = 65535
MESES = [str(m) for m in range(1, 13)]


def r1(x):
    return None if pd.isna(x) else round(float(x), 1)


meta = pd.read_csv(PROC / "provincias_meta.csv")
meta["region"] = meta["cod_indec"].map(REGION)
lp = pd.read_csv(LL / "lluvia_provincia_mes.csv")
lr = pd.read_csv(LL / "lluvia_region_mes.csv")
clima = pd.read_csv(LL / "clima_region.csv", index_col="region")
hb = pd.read_csv(LL / "hb_provincia_mes.csv")
res = pd.read_csv(LL / "hb_resumen.csv", index_col="anios")
cel = pd.read_pickle(PROC / "lluvia_celdas.pkl")

# ---------- Calendarios por región y provincia ----------
regiones = {r: {"provincias": sorted(meta.loc[meta["region"] == r, "provincia"]),
                "mm": [r1(v) for v in clima.loc[r, MESES]]}
            for r in clima.index}
provincias = {}
for pr, g in lp.groupby("provincia"):
    provincias[pr] = {int(a): {"mm": [r1(v) for v in h["mm"]], "hab": [r1(v) for v in h["habitual_mm"]]}
                      for a, h in g.sort_values("mes").groupby("anio")}
    provincias[pr]["tipico"] = [r1(v) for v in g.dropna(subset=["mm"]).groupby("mes")["mm"].median().reindex(range(1, 13))]

# ---------- Mapa: matriz celda x mes ----------
pos = (cel[["lon", "lat", "provincia"]].drop_duplicates(["lon", "lat"])
       .sort_values(["lat", "lon"]).reset_index(drop=True))
provs = sorted(pos["provincia"].unique())
pos["pid"] = pos["provincia"].map({p: i for i, p in enumerate(provs)})
cel = cel.merge(pos.reset_index()[["lon", "lat", "index"]], on=["lon", "lat"])
matriz = np.full((len(ANIOS) * 12, len(pos)), SIN_DATO, dtype="<u2")
matriz[(cel["anio"] - ANIOS[0]) * 12 + cel["mes"] - 1, cel["index"]] = np.round(cel["mm"]).astype(int)

# Serie nacional: media de las celdas ponderada por cos(lat), como las provincias en 08
cel["peso"] = np.cos(np.deg2rad(cel["lat"]))
cel["mmp"] = cel["mm"] * cel["peso"]
suma = cel.groupby(["anio", "mes"])[["mmp", "peso"]].sum()
nac = (suma["mmp"] / suma["peso"]).unstack("mes").reindex(index=ANIOS, columns=range(1, 13)).to_numpy()
nac_hab = mediana_otros_anios(nac, eje=0)
nacional = {a: {"mm": [r1(v) for v in nac[i]], "hab": [r1(v) for v in nac_hab[i]]} for i, a in enumerate(ANIOS)}
nacional["tipico"] = [r1(v) for v in np.nanmedian(nac, axis=0)]

datos = {
    "fuente": "GPM IMERG Final V07, mensual 0,1° (NASA GES DISC)",
    "con_datos": "2019-01/2025-08",
    "regiones": regiones,
    "provincias": provincias,
    "previos_secos": {a: float(res.loc[a, "pct_exceso_en_seco_3_meses_previos"]) for a in res.index},
    "previos_secos_base": {a: float(res.loc[a, "pct_provmes_seco_base_3_meses_previos"]) for a in res.index},
    "mapa": {
        "provincias": provs,
        "celdas": np.column_stack([np.round(pos["lon"] * 100), np.round(pos["lat"] * 100), pos["pid"]])
                    .astype(int).ravel().tolist(),
        "nacional": nacional,
    },
}
carpeta(DATOS_APP)
(DATOS_APP / "lluvia.json").write_text(json.dumps(datos, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
(DATOS_APP / "lluvia_celdas.bin.gz").write_bytes(gzip.compress(matriz.tobytes(), 9))
print("lluvia.json KB:", round((DATOS_APP / "lluvia.json").stat().st_size / 1e3, 1),
      "| lluvia_celdas.bin.gz MB:", round((DATOS_APP / "lluvia_celdas.bin.gz").stat().st_size / 1e6, 2),
      "| celdas:", len(pos))


# ---------- Cifras que citan los textos de la app ----------
def fila(tabla, **filtro):
    m = np.logical_and.reduce([tabla[k] == v for k, v in filtro.items()])
    return tabla[m].iloc[0]


def ratio_prov(pr, a, m, col="ratio_lluvia_mes"):
    return fila(hb, provincia=pr, anio=a, mes=m)[col]


print("\nMediana mensual por región (mm) y sus 3 meses más secos:")
for r in clima.index:
    f = clima.loc[r, MESES].astype(float)
    print(f"  {r:9s} {f.round(0).astype(int).tolist()}  secos: {', '.join(f.nsmallest(3).index)}")

anual = lp[lp["anio"] <= 2024].groupby(["provincia", "anio"])["mm"].sum().groupby("provincia").mean()
print(f"\nLluvia anual media 2019–2024: Misiones {anual['Misiones']:.0f} mm | San Juan {anual['San Juan']:.0f} mm")
for a, m in [(2020, 8), (2021, 12), (2022, 1)]:
    print(f"Nacional {a}-{m:02d}: {nacional[a]['mm'][m - 1]} mm (habitual {nacional[a]['hab'][m - 1]})")
for a, m in [(2020, 8), (2021, 12), (2022, 1)]:
    f = fila(lr, region="NEA", anio=a, mes=m)
    print(f"NEA {a}-{m:02d}: {f['mm']:.0f} mm (habitual {f['habitual_mm']:.0f}, ratio {f['ratio']:.2f})")
print("2020-08, lluvia / habitual: " + " | ".join(
    f"{p} {ratio_prov(p, 2020, 8):.2f}" for p in ["Formosa", "Chaco", "Santa Fe", "Entre Ríos"]))
print(f"Corrientes, lluvia / habitual: dic-2021 {ratio_prov('Corrientes', 2021, 12):.2f} | "
      f"ene-2022 {ratio_prov('Corrientes', 2022, 1):.2f} | feb-2022 {ratio_prov('Corrientes', 2022, 2):.2f}")
print(f"Salta nov-2022, 3 meses previos / habitual: {ratio_prov('Salta', 2022, 11, 'ratio_3prev'):.2f}")
for a in res.index:
    print(f"{a}: exceso tras 3 meses secos {res.loc[a, 'pct_exceso_en_seco_3_meses_previos']}%"
          f" | base {res.loc[a, 'pct_provmes_seco_base_3_meses_previos']}%")
