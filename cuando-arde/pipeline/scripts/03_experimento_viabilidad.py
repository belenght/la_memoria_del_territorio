"""Primer experimento de viabilidad.

Preguntas:
  E1. ¿NOAA-20 y Suomi NPP cuentan lo mismo, año a año y provincia por provincia?
  E2. ¿Cuánto cambia el resultado al aplicar el filtro base (tipo 0 + confianza n/h)?
  E3. ¿La estacionalidad es igual en todo el país o cambia por región?
  E4. ¿Quedan puntos fijos que se repiten todo el año (posible fuente no vegetal)?
  E5. ¿Qué días faltan en cada sensor y cuándo caen?
  E6. Ranking de provincias: total y densidad (detecciones por 1.000 km²).

Unidad: detección VIIRS 375 m (no incendios). Años completos comparables: 2019-2025.
Salidas en outputs/experimento/.
"""
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from comun import ANIOS, PROC, REGION, SALIDAS, carpeta

OUT = carpeta(SALIDAS / "experimento")

det = pd.read_pickle(PROC / "detecciones.pkl")
meta = pd.read_csv(PROC / "provincias_meta.csv")

det["region"] = det["cod_indec"].map(REGION)

completos = det[det["anio"].isin(ANIOS)]
base = completos[completos["filtro_base"]]
informe = []
p = informe.append

# ---------- E1. Consistencia entre sensores ----------
p("## E1. NOAA-20 vs Suomi NPP (filtro base, 2019-2025)")
anual = base.pivot_table(index="anio", columns="sensor", values="latitude", aggfunc="size")
anual["ratio_N20_SNPP"] = (anual["NOAA-20"] / anual["Suomi NPP"]).round(3)
p(anual.to_string())
anual.to_csv(OUT / "e1_anual_por_sensor.csv")

pa = base.groupby(["anio", "provincia", "sensor"]).size().unstack("sensor").fillna(0)
pa = pa[(pa.sum(axis=1) > 0)]
r_log, _ = pearsonr(np.log1p(pa["NOAA-20"]), np.log1p(pa["Suomi NPP"]))
rho, _ = spearmanr(pa["NOAA-20"], pa["Suomi NPP"])
p(f"\nProvincia-año (n={len(pa)}): Pearson en log = {r_log:.4f}; Spearman = {rho:.4f}")
pa["dif_rel"] = (pa["NOAA-20"] - pa["Suomi NPP"]) / pa[["NOAA-20", "Suomi NPP"]].mean(axis=1)
grandes = pa[pa[["NOAA-20", "Suomi NPP"]].min(axis=1) >= 500]
p(f"Provincia-año con >=500 detecciones en ambos (n={len(grandes)}): "
  f"diferencia relativa mediana {grandes['dif_rel'].median():+.3f}, "
  f"P5 {grandes['dif_rel'].quantile(.05):+.3f}, P95 {grandes['dif_rel'].quantile(.95):+.3f}")
pa.to_csv(OUT / "e1_provincia_anio_por_sensor.csv")

pm = base.groupby(["anio", "mes", "sensor"]).size().unstack("sensor")
r_mes, _ = pearsonr(np.log1p(pm["NOAA-20"]), np.log1p(pm["Suomi NPP"]))
p(f"Mes-año nacional (n={len(pm)}): Pearson en log = {r_mes:.4f}")

# Ranking interanual: ¿mismo orden de años en ambos sensores?
for s in ["NOAA-20", "Suomi NPP"]:
    p(f"Orden de años de mayor a menor ({s}): {list(anual[s].sort_values(ascending=False).index)}")

# ---------- E2. Efecto del filtro ----------
p("\n## E2. Efecto del filtro base (NOAA-20, 2019-2025)")
n20 = completos[completos["sensor"] == "NOAA-20"]
tot = len(n20)
p(f"Total: {tot:,}")
p(f"  tipo != 0 (fuentes no vegetales/costa afuera): {(~n20['es_vegetacion']).sum():,} ({(~n20['es_vegetacion']).mean():.1%})")
p(f"  confianza baja (entre tipo 0): {((n20['es_vegetacion']) & (~n20['conf_nom_alta'])).sum():,}")
p(f"  quedan con filtro base: {n20['filtro_base'].sum():,} ({n20['filtro_base'].mean():.1%})")
r_todas = n20.groupby("provincia").size()
r_base = n20[n20["filtro_base"]].groupby("provincia").size()
rho_f, _ = spearmanr(r_todas, r_base.reindex(r_todas.index).fillna(0))
p(f"Spearman ranking provincias (todas vs filtro base): {rho_f:.4f}")
t2 = n20[~n20["es_vegetacion"]].groupby("provincia").size().sort_values(ascending=False).head(6)
p("Provincias con más detecciones tipo 2/3 (no vegetación):\n" + t2.to_string())

# ---------- E3. Estacionalidad por región ----------
p("\n## E3. Estacionalidad por región (NOAA-20, filtro base, promedio 2019-2025)")
b20 = base[base["sensor"] == "NOAA-20"]
est = b20.groupby(["region", "mes"]).size().unstack("mes").fillna(0) / len(ANIOS)
est_pct = est.div(est.sum(axis=1), axis=0)
p((est_pct * 100).round(1).to_string())
p("\nMes pico por región: " + str(est_pct.idxmax(axis=1).to_dict()))
p("Peso de cada región en el total: " + str((est.sum(axis=1) / est.sum().sum()).round(3).to_dict()))
est.round(0).to_csv(OUT / "e3_estacionalidad_region_promedio.csv")

# Estacionalidad por provincia: mes pico y concentración (meses que acumulan 50%)
def meses_50(fila):
    s = fila.sort_values(ascending=False)
    return int((s.cumsum() / s.sum() < 0.5).sum() + 1)

ep = b20.groupby(["provincia", "mes"]).size().unstack("mes").fillna(0)
ep = ep[ep.sum(axis=1) >= 1000]
res_ep = pd.DataFrame({
    "total_2019_2025": ep.sum(axis=1).astype(int),
    "mes_pico": ep.idxmax(axis=1),
    "meses_para_50pct": ep.apply(meses_50, axis=1),
}).sort_values("total_2019_2025", ascending=False)
p("\nProvincias (>=1000 det.): mes pico y cuántos meses concentran la mitad\n" + res_ep.to_string())
res_ep.to_csv(OUT / "e3_estacionalidad_provincia.csv")

# Variabilidad interanual de la estacionalidad: mes pico por región y año
pico_anual = b20.groupby(["region", "anio", "mes"]).size().unstack("mes").fillna(0).idxmax(axis=1).unstack("anio")
p("\nMes pico por región y año:\n" + pico_anual.to_string())

# ---------- E4. Puntos persistentes ----------
p("\n## E4. Celdas persistentes (grilla 0,01°, NOAA-20, filtro base, 2019-2025)")
c = b20.assign(cx=(b20["longitude"] / 0.01).round().astype(int), cy=(b20["latitude"] / 0.01).round().astype(int))
c["anio_mes"] = c["anio"] * 100 + c["mes"]
pers = c.groupby(["cx", "cy"]).agg(meses=("anio_mes", "nunique"), det=("latitude", "size"),
                                    provincia=("provincia", "first")).reset_index()
total_meses = len(ANIOS) * 12
for umbral in (12, 24, 36):
    sel = pers[pers["meses"] >= umbral]
    p(f"Celdas activas en >= {umbral} de {total_meses} meses: {len(sel)} celdas, {sel['det'].sum():,} detecciones "
      f"({sel['det'].sum() / len(b20):.2%} del total)")
pers = pers.sort_values(["meses", "det", "cy", "cx"], ascending=[False, False, True, True], kind="mergesort")
top = pers.head(12).copy()
top["lon"] = top["cx"] * 0.01
top["lat"] = top["cy"] * 0.01
p(top[["lat", "lon", "provincia", "meses", "det"]].to_string(index=False))
pers.head(200).to_csv(OUT / "e4_celdas_persistentes_top200.csv", index=False)

# ---------- E5. Días faltantes ----------
p("\n## E5. Días sin ninguna detección por sensor (2019-2025)")
for s in ["NOAA-20", "Suomi NPP"]:
    dias = set(completos.loc[completos["sensor"] == s, "acq_date"].unique())
    todos = pd.date_range("2019-01-01", "2025-12-31").strftime("%Y-%m-%d")
    falt = [d for d in todos if d not in dias]
    otro = set(completos.loc[completos["sensor"] != s, "acq_date"].unique())
    con_otro = [d for d in falt if d in otro]
    p(f"{s}: {len(falt)} días sin datos; de esos, {len(con_otro)} SÍ tienen detecciones en el otro sensor "
      f"(probable falta de datos, no ausencia de fuego).")
    if con_otro:
        p("   ejemplos: " + ", ".join(con_otro[:15]))
    pd.Series(falt, name="fecha").to_csv(OUT / f"e5_dias_sin_datos_{s.replace(' ', '_')}.csv", index=False)

# ---------- E6. Ranking de provincias ----------
p("\n## E6. Provincias: total y densidad (NOAA-20, filtro base, promedio anual 2019-2025)")
# Superficie de Tierra del Fuego sin Antártida ni islas del Atlántico Sur: se usa el valor oficial INDEC (21.571 km²)
# para la Isla Grande y adyacentes. PENDIENTE: confirmar fuente oficial de la cifra antes de publicar.
sup = meta.set_index("provincia")["superficie_km2_aprox"].copy()
tdf = [n for n in sup.index if n.startswith("Tierra del Fuego")][0]
sup[tdf] = 21571
rk = (b20.groupby("provincia").size() / len(ANIOS)).rename("det_por_anio").to_frame()
rk["superficie_km2"] = sup
rk["det_por_1000km2_anio"] = rk["det_por_anio"] / rk["superficie_km2"] * 1000
rk["cv_interanual"] = b20.groupby(["provincia", "anio"]).size().unstack().std(axis=1) / \
                      b20.groupby(["provincia", "anio"]).size().unstack().mean(axis=1)
rk = rk.sort_values("det_por_anio", ascending=False).round(2)
p(rk.to_string())
rk.to_csv(OUT / "e6_ranking_provincias.csv")

texto = "\n".join(informe)
(OUT / "informe_experimento.txt").write_text(texto, encoding="utf-8")
print(texto)
