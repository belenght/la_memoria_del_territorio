"""Rutas, constantes y funciones que comparten los scripts del pipeline.

Cualquier decisión metodológica que use más de un script vive acá (años, sensores,
regiones, cómo se calcula "lo habitual"), para que no pueda quedar distinta en dos lugares.
"""
import csv
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------- Rutas ----------
PIPELINE = Path(__file__).resolve().parents[1]
REPO = PIPELINE.parent
DATA = PIPELINE / "data"                 # no se sube al repositorio (ver docs/fuentes.md)
CRUDOS_FIRMS = DATA / "raw" / "firms"
IGN_PROVINCIAS = DATA / "raw" / "ign" / "provincia.csv"
CRUDOS_IMERG = DATA / "raw" / "imerg"
PROC = DATA / "processed"
SALIDAS = PIPELINE / "outputs"           # tablas e informes de análisis
DATOS_APP = REPO / "app" / "public" / "datos"  # lo que consume la app web

# ---------- Decisiones metodológicas ----------
ANIOS = list(range(2019, 2026))          # años completos de NOAA-20
SENSOR_PRINCIPAL = "NOAA-20"
SENSORES = ["NOAA-20", "Suomi NPP"]      # Suomi NPP es el control

# Regiones estadísticas del INDEC por código de provincia (GBA se une a Pampeana)
REGION = {
    2: "Pampeana", 6: "Pampeana", 14: "Pampeana", 30: "Pampeana", 42: "Pampeana", 82: "Pampeana",
    10: "NOA", 38: "NOA", 46: "NOA", 66: "NOA", 86: "NOA", 90: "NOA",
    18: "NEA", 22: "NEA", 34: "NEA", 54: "NEA",
    50: "Cuyo", 70: "Cuyo", 74: "Cuyo",
    26: "Patagonia", 58: "Patagonia", 62: "Patagonia", 78: "Patagonia", 94: "Patagonia",
}


def carpeta(ruta: Path) -> Path:
    """Crea la carpeta si no existe y la devuelve."""
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def requerir(ruta: Path, ayuda: str) -> None:
    """Corta con un mensaje claro si falta un insumo."""
    if not ruta.exists() or (ruta.is_dir() and not any(ruta.iterdir())):
        raise SystemExit(f"No se encontró {ruta}\n{ayuda}")


# ---------- Límites del IGN ----------
def parse_multipolygon(wkt: str) -> list:
    """WKT MULTIPOLYGON -> lista de polígonos; cada uno = [anillo_exterior, *huecos] como arrays (n, 2)."""
    cuerpo = re.sub(r"\)\s*,\s*\(", "),(", wkt.strip())
    cuerpo = cuerpo[cuerpo.index("("):]
    poligonos = []
    for bloque in re.findall(r"\(\((.*?)\)\)", cuerpo, flags=re.S):
        anillos = []
        for anillo in bloque.split("),("):
            anillo = anillo.replace("(", "").replace(")", "")
            anillos.append(np.array([list(map(float, p.split())) for p in anillo.split(",") if p.strip()]))
        poligonos.append(anillos)
    return poligonos


def leer_provincias_ign() -> pd.DataFrame:
    """Provincias del IGN: cod_indec, provincia y poligonos (parseados)."""
    requerir(IGN_PROVINCIAS, "Copiá provincia.csv del IGN en pipeline/data/raw/ign/. Ver docs/fuentes.md.")
    try:
        csv.field_size_limit(sys.maxsize)
    except OverflowError:  # Windows: el límite de C long es 32 bits
        csv.field_size_limit(2**31 - 1)
    prov = pd.read_csv(IGN_PROVINCIAS, engine="python")
    return pd.DataFrame({
        "cod_indec": prov["in1"].astype(int),
        "provincia": prov["nam"],
        "poligonos": [parse_multipolygon(g) for g in prov["geom"]],
    })


# ---------- Lo habitual ----------
def mediana_otros_anios(arr: np.ndarray, eje: int) -> np.ndarray:
    """"Lo habitual" leave-one-out: para cada año del `eje`, la mediana de los demás años.

    Devuelve un array con la misma forma que `arr`. Ignora NaN (años sin dato).
    """
    salida = np.empty(arr.shape, dtype=float)
    for i in range(arr.shape[eje]):
        otros = np.delete(arr, i, axis=eje)
        idx = [slice(None)] * arr.ndim
        idx[eje] = i
        salida[tuple(idx)] = np.nanmedian(otros, axis=eje) if np.isnan(otros).any() else np.median(otros, axis=eje)
    return salida
