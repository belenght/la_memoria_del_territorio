"""Exporta los datos de fuego de la app: ambos satélites y el caso "Cómo leer un punto".

Grilla común de 0,1° para NOAA-20 y Suomi NPP (mismos índices de celda, así la app
puede alternar entre satélites). Por satélite:
  tipico[m]      = [cid, promedio*10, ...]
  years[a][m]    = [cid, observado, habitual*2, ...]   (habitual = mediana de los otros 6 años)
  nacional[a]    = {obs[12], hab[12]};  nacional.tipico[12]
  serie_prov[p]  = {tipico[12], anios[a]: {obs[12], hab[12]}}  (contado desde cada detección)
Caso "Cómo leer un punto": detecciones del evento aproximado más grande de Corrientes
en febrero de 2022 (NOAA-20): pts = [lon*1000, lat*1000, día desde el inicio, noche(0/1), ...].

Salida: app/public/datos/fuego.json.gz
"""
import gzip
import json

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from comun import ANIOS, DATOS_APP, PROC, SENSOR_PRINCIPAL, SENSORES, carpeta, mediana_otros_anios

TAM = 0.1

b = pd.read_pickle(PROC / "base_analitica.pkl")
b["ix"] = np.floor(b["longitude"] / TAM).astype(int)
b["iy"] = np.floor(b["latitude"] / TAM).astype(int)

# Celdas con al menos una detección en algún satélite; provincia = la más frecuente
celdas = (b.groupby(["ix", "iy"])["provincia"].agg(lambda s: s.mode().iat[0])
           .reset_index().reset_index().rename(columns={"index": "cid"}))
provs = sorted(celdas["provincia"].unique())
celdas["pid"] = celdas["provincia"].map({p: i for i, p in enumerate(provs)})
b = b.merge(celdas[["ix", "iy", "cid"]], on=["ix", "iy"])
cells = np.column_stack([np.round((celdas["ix"] + 0.5) * TAM * 100), np.round((celdas["iy"] + 0.5) * TAM * 100),
                         celdas["pid"]]).astype(int).ravel().tolist()


def conteo(df: pd.DataFrame, clave: str, n: int) -> np.ndarray:
    """Matriz (n, años, 12) de detecciones por `clave` (entero 0..n-1), año y mes."""
    cnt = np.zeros((n, len(ANIOS), 12), dtype=np.int32)
    g = df.groupby([clave, "anio", "mes"]).size()
    cnt[g.index.get_level_values(0), g.index.get_level_values(1) - ANIOS[0], g.index.get_level_values(2) - 1] = g.to_numpy()
    return cnt


def bloque_sensor(n: pd.DataFrame) -> dict:
    cnt = conteo(n, "cid", len(celdas))
    hab = mediana_otros_anios(cnt, eje=1)
    tip = cnt.mean(axis=1)
    tipico = {}
    for m in range(12):
        idx = np.where(tip[:, m] > 0)[0]
        tipico[m + 1] = np.column_stack([idx, np.round(tip[idx, m] * 10).astype(int)]).ravel().tolist()
    years = {}
    for yi, anio in enumerate(ANIOS):
        years[anio] = {}
        for m in range(12):
            obs, h = cnt[:, yi, m], hab[:, yi, m]
            idx = np.where((obs > 0) | (h > 0))[0]
            years[anio][m + 1] = np.column_stack([idx, obs[idx], np.round(h[idx] * 2).astype(int)]).ravel().tolist()

    nat = cnt.sum(axis=0)
    nat_hab = mediana_otros_anios(nat, eje=0)
    nacional = {a: {"obs": nat[yi].tolist(), "hab": nat_hab[yi].round(1).tolist()} for yi, a in enumerate(ANIOS)}
    nacional["tipico"] = nat.mean(axis=0).round(1).tolist()

    # Por provincia se cuenta desde cada detección (no desde celdas): exacto para el indicador
    con_pid = n.assign(pid=n["provincia"].map({p: i for i, p in enumerate(provs)})).dropna(subset=["pid"])
    prov = conteo(con_pid.astype({"pid": int}), "pid", len(provs)).astype(float)
    prov_hab = mediana_otros_anios(prov, eje=1)
    serie = {p: {"tipico": prov[i].mean(axis=0).round(1).tolist(),
                 "anios": {a: {"obs": prov[i, yi].astype(int).tolist(), "hab": prov_hab[i, yi].round(1).tolist()}
                           for yi, a in enumerate(ANIOS)}}
             for i, p in enumerate(provs)}
    return {"tipico": tipico, "years": years, "nacional": nacional, "serie_prov": serie}


sensores = {s: bloque_sensor(b[b["sensor"] == s]) for s in SENSORES}

# ---------- Caso "Cómo leer un punto": Corrientes, febrero de 2022 ----------
n20 = b[b["sensor"] == SENSOR_PRINCIPAL]
cand = n20[(n20["provincia"] == "Corrientes") & (n20["anio"] == 2022) & (n20["mes"] == 2)]
ev = n20[n20["evento_id"] == cand.groupby("evento_id").size().idxmax()].sort_values("dt_local")
inicio, fin = ev["fecha_local"].min(), ev["fecha_local"].max()
punto = {
    "inicio": str(inicio.date()), "fin": str(fin.date()), "dias": int((fin - inicio).days) + 1, "n": len(ev),
    "provincias": sorted(ev["provincia"].unique().tolist()),
    "pts": np.column_stack([np.round(ev["longitude"] * 1000), np.round(ev["latitude"] * 1000),
                            (ev["fecha_local"] - inicio).dt.days, ev["daynight"] == "N"]).astype(int).ravel().tolist(),
    "caja": [float(ev["longitude"].min()), float(ev["latitude"].min()),
             float(ev["longitude"].max()), float(ev["latitude"].max())],
}

datos = {
    "meta": {"grilla_grados": TAM, "anios": ANIOS, "sensores": SENSORES,
             "filtro": "type 0, confianza nominal/alta, sin celdas persistentes"},
    "provincias": provs, "cells": cells, "sensores": sensores, "punto": punto,
}
crudo = json.dumps(datos, separators=(",", ":")).encode("utf-8")
salida = carpeta(DATOS_APP) / "fuego.json.gz"
salida.write_bytes(gzip.compress(crudo, 9))

# ---------- Cifras de control para los textos ----------
print("celdas comunes:", len(celdas))
print("JSON MB:", round(len(crudo) / 1e6, 2), "| gzip MB:", round(salida.stat().st_size / 1e6, 2))
print("caso Corrientes:", punto["inicio"], "->", punto["fin"], punto["dias"], "días,", punto["n"], "detecciones,", punto["provincias"])
print("  noches:", int(ev["daynight"].eq("N").sum()), "| días con detecciones:", ev["fecha_local"].nunique())
pa = b.groupby(["anio", "provincia", "sensor"]).size().unstack("sensor").fillna(0)
print("provincia-año: Spearman", round(spearmanr(pa["NOAA-20"], pa["Suomi NPP"])[0], 4),
      "| Pearson log", round(pearsonr(np.log1p(pa["NOAA-20"]), np.log1p(pa["Suomi NPP"]))[0], 4))
for s in SENSORES:
    nat = sensores[s]["nacional"]
    print(s, "total 2020:", sum(nat[2020]["obs"]), "| 2022:", sum(nat[2022]["obs"]), "| ago-2022:", nat[2022]["obs"][7])
