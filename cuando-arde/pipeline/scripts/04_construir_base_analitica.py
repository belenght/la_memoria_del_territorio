"""Base analítica con las decisiones aprobadas en la Etapa A.

Decisiones:
  - Años completos 2019-2025. Serie principal NOAA-20; Suomi NPP como control.
  - Filtro base: type 0 + confianza n/h.
  - Exclusión de celdas persistentes: celdas de 0,01° (~1 km) con detecciones en
    >= 24 de los 84 meses de NOAA-20 (probables fuentes no vegetales: industria,
    antorchas). La lista se calcula con NOAA-20 y se aplica a ambos sensores.

Además agrupa las detecciones en EVENTOS APROXIMADOS (proxy, no incendios confirmados):
  dos detecciones pertenecen al mismo evento si caen en celdas de una grilla de
  `TAM` grados vecinas (3x3) y en días locales separados por <= `GAP` días.
  Se corre un análisis de sensibilidad con varios TAM y GAP.

Salidas:
  data/processed/base_analitica.pkl
  outputs/base/celdas_persistentes.csv
  outputs/base/sensibilidad_eventos.csv
"""
import numpy as np
import pandas as pd

from comun import ANIOS, PROC, REGION, SALIDAS, SENSORES, carpeta

OUT = carpeta(SALIDAS / "base")
UMBRAL_MESES = 24
TAM_DEFECTO, GAP_DEFECTO = 0.05, 1

det = pd.read_pickle(PROC / "detecciones.pkl")
det = det[det["anio"].isin(ANIOS) & det["filtro_base"]].copy()
det["region"] = det["cod_indec"].map(REGION)
det["cx1"] = np.round(det["longitude"] / 0.01).astype(int)
det["cy1"] = np.round(det["latitude"] / 0.01).astype(int)

# ---------- Celdas persistentes ----------
n20 = det[det["sensor"] == "NOAA-20"]
meses = (n20.assign(am=n20["anio"] * 100 + n20["mes"])
            .groupby(["cx1", "cy1"])
            .agg(meses_activos=("am", "nunique"), detecciones=("latitude", "size"),
                 provincia=("provincia", "first")).reset_index())
pers = meses[meses["meses_activos"] >= UMBRAL_MESES].copy()
pers["lat"] = pers["cy1"] * 0.01
pers["lon"] = pers["cx1"] * 0.01
pers.sort_values(["meses_activos", "detecciones"], ascending=False).to_csv(OUT / "celdas_persistentes.csv", index=False)
clave_pers = set(zip(pers["cx1"], pers["cy1"]))
det["celda_persistente"] = [k in clave_pers for k in zip(det["cx1"], det["cy1"])]
print(f"Celdas persistentes (>= {UMBRAL_MESES} meses): {len(pers)}")
print(det.groupby("sensor")["celda_persistente"].agg(["sum", "mean"]).round(4).to_string())
det = det[~det["celda_persistente"]].copy()


# ---------- Eventos aproximados ----------
def agrupar_eventos(df: pd.DataFrame, tam: float, gap: int) -> np.ndarray:
    """Devuelve un id de evento por fila (union-find sobre nodos celda-día)."""
    cx = np.floor(df["longitude"].to_numpy() / tam).astype(np.int64)
    cy = np.floor(df["latitude"].to_numpy() / tam).astype(np.int64)
    dia = (df["fecha_local"].to_numpy().astype("datetime64[D]").astype(np.int64))
    nodos = pd.DataFrame({"cx": cx, "cy": cy, "d": dia})
    unicos = nodos.drop_duplicates().reset_index(drop=True)
    indice = {k: i for i, k in enumerate(zip(unicos["cx"], unicos["cy"], unicos["d"]))}
    padre = np.arange(len(unicos))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    vecinos = [(dx, dy, dd) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dd in range(0, gap + 1)
               if (dd > 0) or (dx, dy) > (0, 0)]
    for i, (x, y, d) in enumerate(zip(unicos["cx"], unicos["cy"], unicos["d"])):
        for dx, dy, dd in vecinos:
            j = indice.get((x + dx, y + dy, d + dd))
            if j is not None:
                ri, rj = raiz(i), raiz(j)
                if ri != rj:
                    padre[rj] = ri
    raices = np.array([raiz(i) for i in range(len(unicos))])
    mapa = pd.Series(raices, index=pd.MultiIndex.from_frame(unicos))
    return mapa.reindex(pd.MultiIndex.from_frame(nodos)).to_numpy()


sens = []
for sensor in SENSORES:
    sub = det[det["sensor"] == sensor]
    for tam in (0.03, 0.05, 0.10):
        for gap in (1, 2):
            ev = agrupar_eventos(sub, tam, gap)
            tam_ev = pd.Series(ev).value_counts()
            sens.append({"sensor": sensor, "tam_grados": tam, "gap_dias": gap,
                         "detecciones": len(sub), "eventos": len(tam_ev),
                         "det_por_evento_media": round(tam_ev.mean(), 2),
                         "eventos_1_deteccion_pct": round((tam_ev == 1).mean() * 100, 1),
                         "pct_det_en_top1pct_eventos": round(
                             tam_ev.sort_values(ascending=False).head(max(1, len(tam_ev) // 100)).sum() / len(sub) * 100, 1)})
            if tam == TAM_DEFECTO and gap == GAP_DEFECTO:
                det.loc[sub.index, "evento_id"] = ev
sens = pd.DataFrame(sens)
sens.to_csv(OUT / "sensibilidad_eventos.csv", index=False)
print("\nSensibilidad de eventos aproximados:")
print(sens.to_string(index=False))

det["evento_id"] = det["evento_id"].astype(np.int64)
det.to_pickle(PROC / "base_analitica.pkl")
print(f"\nBase analítica: {len(det):,} detecciones guardadas.")
