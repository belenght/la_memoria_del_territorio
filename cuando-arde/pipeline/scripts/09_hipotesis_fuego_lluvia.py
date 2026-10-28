"""Hipótesis del calendario del agua (se prueban, no se afirman).

HA. El calendario del fuego es el negativo del de la lluvia, por región y provincia.
    Medida: correlación de Spearman entre los 12 meses de fuego habitual (mediana de
    detecciones 2019–2025) y lluvia habitual (mediana de mm con dato). Se mira también
    la lluvia del mes anterior (desfase de 1 mes) y si el mes pico del fuego está entre
    los 3 meses más secos.
HB. En 2020 y 2022 llovió menos de lo habitual donde y cuando más se excedió el fuego.
    Medida: qué parte del exceso de detecciones (sobre lo habitual leave-one-out) cayó en
    provincia-meses con lluvia por debajo de lo habitual, en el mismo mes y en los
    3 meses previos. CONTROL: la misma medida en los años no anómalos (2019, 2021,
    2023, 2024). Si el control da parecido, la coincidencia no es propia de 2020/2022.

Unidad del fuego: detecciones VIIRS NOAA-20 de la base analítica (04).
Coincidencia temporal, no causa. n = 12 meses por región: las correlaciones son descriptivas.

Salidas en outputs/lluvia/: informe_hipotesis_lluvia.txt, ha_calendario_*.csv,
hb_provincia_mes.csv, hb_resumen.csv.
"""
import numpy as np
import pandas as pd

from comun import ANIOS, PROC, SALIDAS, SENSOR_PRINCIPAL

SAL = SALIDAS / "lluvia"
ANOMALOS = [2020, 2022]
CONTROL = [2019, 2021, 2023, 2024]

informe = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    informe.append(s)


# ---------- Fuego: serie base de 04 (filtro base, sin celdas persistentes) ----------
det = pd.read_pickle(PROC / "base_analitica.pkl")
det = det[det["sensor"] == SENSOR_PRINCIPAL]
p(f"Detecciones serie base: {len(det):,}".replace(",", "."))

idx = pd.MultiIndex.from_product([sorted(det["provincia"].unique()), ANIOS, range(1, 13)],
                                 names=["provincia", "anio", "mes"])
fp = det.groupby(["provincia", "anio", "mes"]).size().reindex(idx, fill_value=0).rename("det").reset_index()
prov_reg = det.drop_duplicates("provincia").set_index("provincia")["region"]
fp["region"] = fp["provincia"].map(prov_reg)

# Lo habitual del fuego: mediana de los otros seis años (como 05)
piv = fp.pivot_table(index=["provincia", "mes"], columns="anio", values="det")
hab = {a: piv.drop(columns=a).median(axis=1) for a in ANIOS}
fp["det_habitual"] = [hab[a].loc[(pr, m)] for pr, a, m in zip(fp["provincia"], fp["anio"], fp["mes"])]
fp["exceso"] = fp["det"] - fp["det_habitual"]

# ---------- Lluvia (de 08) ----------
lp = pd.read_csv(SAL / "lluvia_provincia_mes.csv")
lr = pd.read_csv(SAL / "lluvia_region_mes.csv")
faltan = set(fp["provincia"]) - set(lp["provincia"])
if faltan:
    raise SystemExit(f"Provincias del fuego sin lluvia: {faltan}")


# ================= HA =================
p("\n## HA. ¿El calendario del fuego es el negativo del de la lluvia?")
p("Spearman entre 12 meses: fuego habitual vs lluvia habitual (mismo mes y mes anterior).")
p("Negativo = más fuego en meses más secos. n=12, descriptivo.\n")


def calendario(fuego, lluvia, clave):
    f = fuego.groupby([clave, "anio", "mes"])["det"].sum().groupby([clave, "mes"]).median().unstack("mes")
    ll = lluvia.dropna(subset=["mm"]).groupby([clave, "mes"])["mm"].median().unstack("mes")
    filas = []
    for k in f.index:
        fz, lz = f.loc[k], ll.loc[k]
        lz_ant = lz.reindex([(m - 2) % 12 + 1 for m in range(1, 13)]).set_axis(range(1, 13))
        secos = lz.nsmallest(3).index
        filas.append({
            clave: k,
            "rho_mismo_mes": round(fz.corr(lz, method="spearman"), 2),
            "rho_mes_anterior": round(fz.corr(lz_ant, method="spearman"), 2),
            "mes_pico_fuego": int(fz.idxmax()),
            "mes_mas_seco": int(lz.idxmin()),
            "meses_mas_secos": ",".join(str(m) for m in sorted(secos)),
            "pico_en_3_mas_secos": bool(fz.idxmax() in secos),
            "det_habitual_anual": int(fz.sum()),
        })
    return pd.DataFrame(filas), f, ll


ha_reg, f_reg, l_reg = calendario(fp, lr, "region")
p(ha_reg.drop(columns="det_habitual_anual").to_string(index=False))
ha_reg.to_csv(SAL / "ha_calendario_region.csv", index=False)

ha_prov, _, _ = calendario(fp, lp, "provincia")
ha_prov.to_csv(SAL / "ha_calendario_provincia.csv", index=False)
neg = ha_prov[ha_prov["rho_mismo_mes"] < 0]
p(f"\nProvincias con rho < 0 (mismo mes): {len(neg)} de {len(ha_prov)}; "
  f"rho <= -0,5: {int((ha_prov['rho_mismo_mes'] <= -0.5).sum())}")
p(f"Provincias con pico de fuego en uno de sus 3 meses más secos: "
  f"{int(ha_prov['pico_en_3_mas_secos'].sum())} de {len(ha_prov)}")
peso = ha_prov["det_habitual_anual"]
p(f"Ponderado por detecciones habituales: rho medio mismo mes = "
  f"{np.average(ha_prov['rho_mismo_mes'], weights=peso):.2f}, "
  f"mes anterior = {np.average(ha_prov['rho_mes_anterior'], weights=peso):.2f}")
p("\nPor provincia (ordenado por detecciones habituales):")
p(ha_prov.sort_values("det_habitual_anual", ascending=False).to_string(index=False))


# ================= HB =================
p("\n## HB. ¿Llovió menos de lo habitual donde y cuando se excedió el fuego?")

# Lluvia de los 3 meses previos (m-3..m-1) y su habitual leave-one-out
lp = lp.sort_values(["provincia", "anio", "mes"]).copy()
lp["t"] = lp["anio"] * 12 + lp["mes"]
lp["mm_3prev"] = lp.groupby("provincia")["mm"].transform(
    lambda s: s.shift(1).rolling(3, min_periods=3).sum())
piv3 = lp.pivot_table(index=["provincia", "mes"], columns="anio", values="mm_3prev")
lp["hab_3prev"] = [piv3.loc[(pr, m)].drop(a, errors="ignore").median()
                   for pr, a, m in zip(lp["provincia"], lp["anio"], lp["mes"])]
lp["ratio_3prev"] = lp["mm_3prev"] / lp["hab_3prev"]

hb = fp.merge(lp[["provincia", "anio", "mes", "mm", "habitual_mm", "ratio", "mm_3prev", "hab_3prev",
                  "ratio_3prev"]], on=["provincia", "anio", "mes"], how="left")
hb = hb.rename(columns={"ratio": "ratio_lluvia_mes"})
hb.round(3).to_csv(SAL / "hb_provincia_mes.csv", index=False)

p("Exceso = detecciones por encima de lo habitual (solo provincia-meses con exceso > 0).")
p("'Seco' = lluvia por debajo de su habitual (ratio < 1). Por construcción (mediana),")
p("alrededor de la mitad de los provincia-meses son 'secos': esa es la línea de base.\n")

resumen = []
for etiqueta, anios in [*[(str(a), [a]) for a in ANOMALOS], ("control 2019/21/23/24", CONTROL)]:
    s = hb[hb["anio"].isin(anios)]
    pos = s[s["exceso"] > 0]
    fila = {"anios": etiqueta, "exceso_total": int(pos["exceso"].sum())}
    for col, nombre in [("ratio_lluvia_mes", "mismo_mes"), ("ratio_3prev", "3_meses_previos")]:
        v = pos.dropna(subset=[col])
        fila[f"pct_exceso_en_seco_{nombre}"] = round(100 * v.loc[v[col] < 1, "exceso"].sum() / v["exceso"].sum(), 1)
        fila[f"pct_provmes_seco_base_{nombre}"] = round(100 * (s[col].dropna() < 1).mean(), 1)
        w = v["exceso"]
        fila[f"ratio_lluvia_ponderado_{nombre}"] = round(np.exp(np.average(np.log(v[col].clip(lower=0.01)), weights=w)), 2)
    resumen.append(fila)
res = pd.DataFrame(resumen)
res.to_csv(SAL / "hb_resumen.csv", index=False)
p(res.T.to_string(header=False))
p("\n(ratio_lluvia_ponderado = media geométrica de lluvia/habitual pesada por el exceso;"
  " 1 = lo habitual)")

for a in ANOMALOS:
    p(f"\nTop 12 provincia-meses por exceso en {a}:")
    top = hb[hb["anio"] == a].nlargest(12, "exceso")
    p(top[["provincia", "mes", "det", "det_habitual", "exceso", "mm", "habitual_mm",
           "ratio_lluvia_mes", "ratio_3prev"]].round(2).to_string(index=False))
    t = hb[hb["anio"] == a]
    pos = t[t["exceso"] > 0]
    top10 = pos.nlargest(10, "exceso")["exceso"].sum() / pos["exceso"].sum() * 100
    p(f"  Esos 10 primeros concentran el {top10:.0f}% del exceso positivo de {a}.")

p("\nRelación general (todos los provincia-meses 2019–2024 con detecciones habituales >= 50):")
g = hb[(hb["anio"] <= 2024) & (hb["det_habitual"] >= 50)].dropna(subset=["ratio_lluvia_mes", "ratio_3prev"])
ratio_fuego = (g["det"] + 1) / (g["det_habitual"] + 1)
p(f"  n = {len(g)}; Spearman(fuego/habitual, lluvia mismo mes/habitual) = "
  f"{ratio_fuego.corr(g['ratio_lluvia_mes'], method='spearman'):.2f}; "
  f"con lluvia 3 meses previos = {ratio_fuego.corr(g['ratio_3prev'], method='spearman'):.2f}")

(SAL / "informe_hipotesis_lluvia.txt").write_text("\n".join(informe), encoding="utf-8")
