"""Exporta los límites provinciales del IGN simplificados para el mapa de la app.

Simplificación Douglas-Peucker con tolerancia de 0,01° y coordenadas con 3 decimales.
El sector antártico no se muestra: se descartan los anillos al sur de los 58° S.

Salida: app/public/datos/provincias.geojson
"""
import json

import numpy as np

from comun import DATOS_APP, carpeta, leer_provincias_ign

TOLERANCIA = 0.01
LAT_ANTARTIDA = -58


def douglas_peucker(pts: np.ndarray, tol: float) -> np.ndarray:
    """Simplificación Douglas-Peucker iterativa (sin recursión)."""
    if len(pts) < 4:
        return pts
    conservar = np.zeros(len(pts), dtype=bool)
    conservar[0] = conservar[-1] = True
    pila = [(0, len(pts) - 1)]
    while pila:
        a, z = pila.pop()
        if z <= a + 1:
            continue
        p, q = pts[a], pts[z]
        d = q - p
        nrm = np.hypot(*d)
        v = pts[a + 1:z] - p
        dist = np.abs(d[0] * v[:, 1] - d[1] * v[:, 0]) / nrm if nrm else np.hypot(v[:, 0], v[:, 1])
        k = int(np.argmax(dist))
        if dist[k] > tol:
            conservar[a + 1 + k] = True
            pila += [(a, a + 1 + k), (a + 1 + k, z)]
    return pts[conservar]


features = []
for r in leer_provincias_ign().itertuples():
    poligonos = []
    for anillos_ign in r.poligonos:
        anillos = []
        for pts in anillos_ign:
            if pts[:, 1].max() < LAT_ANTARTIDA:
                break
            s = douglas_peucker(pts, TOLERANCIA)
            if len(s) >= 4:
                anillos.append(np.round(s, 3).tolist())
        if anillos:
            poligonos.append(anillos)
    features.append({"type": "Feature", "properties": {"nombre": r.provincia, "cod": r.cod_indec},
                     "geometry": {"type": "MultiPolygon", "coordinates": poligonos}})

salida = carpeta(DATOS_APP) / "provincias.geojson"
salida.write_text(json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")),
                  encoding="utf-8")
print(f"{salida.name}: {len(features)} provincias, {salida.stat().st_size / 1e6:.2f} MB")
