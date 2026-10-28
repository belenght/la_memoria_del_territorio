"""Pruebas exploratorias para elegir la pregunta central (Etapa B).

H1. El mes pico es distinto entre regiones y estable entre años.
H2. Los años anómalos (2020, 2022) se explican por pocas provincias y pocos meses.
H3. El exceso de los años anómalos ocurre DENTRO de la temporada habitual de cada
    provincia (más intensidad) o FUERA de ella (temporada desplazada).
H4. Contar detecciones vs eventos aproximados cambia el ranking de provincias.
H5. Las anomalías se ven igual con Suomi NPP (robustez).
Extra: proporción de detecciones nocturnas por región.

Referencia "habitual": mediana de los OTROS seis años (leave-one-out), para no
comparar un año consigo mismo. Unidad: detecciones VIIRS (no incendios).
"""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from comun import ANIOS, PROC, SALIDAS, carpeta

OUT = carpeta(SALIDAS / "etapa_b")

base = pd.read_pickle(PROC / "base_analitica.pkl")
n20 = base[base["sensor"] == "NOAA-20"]
informe = []
p = informe.append


def tabla_pam(df):
    """Detecciones por provincia x año x mes (completa con ceros)."""
    t = df.groupby(["provincia", "anio", "mes"]).size()
    idx = pd.MultiIndex.from_product([sorted(df["provincia"].unique()), ANIOS, range(1, 13)],
                                     names=["provincia", "anio", "mes"])
    return t.reindex(idx, fill_value=0)


def exceso_loo(t, anio):
    """Exceso de un año sobre la mediana de los otros años, por provincia y mes."""
    obs = t.xs(anio, level="anio")
    otros = t.drop(index=anio, level="anio").groupby(["provincia", "mes"]).median()
    return (obs - otros).rename("exceso"), otros


# ---------- H1 ----------
p("## H1. Mes pico por región: ¿distinto y estable?")
reg = n20.groupby(["region", "anio", "mes"]).size().unstack("mes").fillna(0)
clima = n20.groupby(["region", "mes"]).size().unstack("mes").fillna(0)
pico_clima = clima.idxmax(axis=1)
pico_anio = reg.idxmax(axis=1).unstack("anio")


def dist_circ(a, b):
    d = abs(a - b) % 12
    return min(d, 12 - d)


for r in pico_anio.index:
    difs = [dist_circ(m, pico_clima[r]) for m in pico_anio.loc[r]]
    p(f"{r}: pico habitual mes {pico_clima[r]}; años con pico a <=1 mes del habitual: "
      f"{sum(d <= 1 for d in difs)}/7; picos por año {list(pico_anio.loc[r])}")

# ---------- H2 y H3 ----------
t20 = tabla_pam(n20)
# Temporada habitual de cada provincia: meses que acumulan el 80% de la mediana mensual
clima_prov = t20.groupby(["provincia", "mes"]).median()
temporada = {}
for prov, s in clima_prov.groupby(level="provincia"):
    s = s.droplevel(0).sort_values(ascending=False)
    acum = s.cumsum() / s.sum() if s.sum() > 0 else s
    temporada[prov] = set(acum[acum.shift(fill_value=0) < 0.8].index)

filas_anom = []
for anio in ANIOS:
    exc, ref = exceso_loo(t20, anio)
    pos = exc.clip(lower=0)
    total_obs = t20.xs(anio, level="anio").sum()
    total_ref = ref.groupby("provincia").sum().sum()
    en_temp = sum(v for (prov, mes), v in pos.items() if mes in temporada[prov])
    por_prov = pos.groupby("provincia").sum().sort_values(ascending=False)
    por_mes = pos.groupby("mes").sum().sort_values(ascending=False)
    filas_anom.append({
        "anio": anio, "detecciones": int(total_obs), "referencia_otros_anios": int(total_ref),
        "razon_vs_referencia": round(total_obs / total_ref, 2),
        "exceso_positivo": int(pos.sum()),
        "pct_exceso_top3_prov": round(por_prov.head(3).sum() / pos.sum() * 100, 1) if pos.sum() else 0,
        "top3_prov": ", ".join(por_prov.head(3).index),
        "pct_exceso_top3_meses": round(por_mes.head(3).sum() / pos.sum() * 100, 1) if pos.sum() else 0,
        "top3_meses": ", ".join(map(str, por_mes.head(3).index)),
        "pct_exceso_en_temporada": round(en_temp / pos.sum() * 100, 1) if pos.sum() else 0,
    })
anom = pd.DataFrame(filas_anom)
anom.to_csv(OUT / "h2_h3_anios_anomalos.csv", index=False)
p("\n## H2/H3. Cada año vs la mediana de los otros seis (NOAA-20)")
p(anom.to_string(index=False))

# Detalle 2020 y 2022: provincias con mayor exceso, y si fue en temporada
for anio in (2020, 2022):
    exc, _ = exceso_loo(t20, anio)
    pos = exc.clip(lower=0).reset_index()
    pos["en_temporada"] = [m in temporada[pr] for pr, m in zip(pos["provincia"], pos["mes"])]
    top = pos.sort_values("exceso", ascending=False).head(10)
    p(f"\nTop 10 provincia-mes por exceso en {anio}:\n" + top.to_string(index=False))
    pos.to_csv(OUT / f"exceso_provincia_mes_{anio}.csv", index=False)

# ---------- H4 ----------
p("\n## H4. Ranking de provincias: detecciones vs eventos aproximados (grilla 0,05°, 1 día)")
ev_prov = n20.groupby("evento_id").agg(provincia=("provincia", lambda s: s.mode().iat[0]),
                                       n=("latitude", "size"))
rk = pd.DataFrame({
    "detecciones": n20.groupby("provincia").size(),
    "eventos": ev_prov.groupby("provincia").size(),
})
rk["det_por_evento"] = (rk["detecciones"] / rk["eventos"]).round(2)
rk["rank_det"] = rk["detecciones"].rank(ascending=False).astype(int)
rk["rank_ev"] = rk["eventos"].rank(ascending=False).astype(int)
rho, _ = spearmanr(rk["detecciones"], rk["eventos"])
rk = rk.sort_values("detecciones", ascending=False)
p(f"Spearman (detecciones vs eventos): {rho:.3f}")
p(rk.to_string())
rk.to_csv(OUT / "h4_ranking_det_vs_eventos.csv")
ev_reg = n20.groupby(["region", "evento_id"]).size()
p("\nDetecciones por evento, por región (mediana / media / P99):")
p(ev_reg.groupby("region").agg(["median", "mean", lambda s: s.quantile(.99)]).round(1).to_string())

# ---------- H5 ----------
p("\n## H5. Robustez: exceso por provincia con Suomi NPP vs NOAA-20")
tsn = tabla_pam(base[base["sensor"] == "Suomi NPP"])
for anio in (2020, 2022):
    a = exceso_loo(t20, anio)[0].groupby("provincia").sum()
    b = exceso_loo(tsn, anio)[0].groupby("provincia").sum()
    rho, _ = spearmanr(a, b.reindex(a.index).fillna(0))
    p(f"{anio}: Spearman exceso por provincia N20 vs SNPP = {rho:.3f}; "
      f"exceso nacional N20 {int(a.sum()):,} vs SNPP {int(b.sum()):,}")

# ---------- Extra: noche ----------
p("\n## Extra. Proporción de detecciones nocturnas por región (NOAA-20)")
p((n20.groupby("region")["daynight"].apply(lambda s: (s == "N").mean()) * 100).round(1).to_string())

texto = "\n".join(informe)
(OUT / "informe_hipotesis.txt").write_text(texto, encoding="utf-8")
print(texto)
