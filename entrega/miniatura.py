"""Miniatura de YouTube (1280x720) para La Memoria del Territorio.

Dos mapas de Argentina con los datos de la app: lluvia anual (IMERG, promedio 2019-2024)
y detecciones de calor por año (NOAA-20, año típico). Se dibuja al doble y se reduce.
Uso: python miniatura.py <carpeta app/public/datos> <salida.png>
"""
import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

DATOS, SALIDA = Path(sys.argv[1]), Path(sys.argv[2])
E = 2                                   # escala de dibujo
W, H = 1280 * E, 720 * E
NOCHE = (7, 11, 18)
FUEGO_C = (242, 163, 58)
AGUA_C = (89, 195, 230)
TEXTO = (236, 232, 222)
TENUE = (138, 150, 168)
RAMPA_FUEGO = [(90, 29, 12), (196, 82, 26), (242, 163, 58), (255, 231, 168), (255, 248, 232)]
RAMPA_AGUA = [(12, 30, 58), (24, 78, 140), (58, 148, 210), (150, 214, 240), (236, 250, 255)]
FUENTE = "C:/Windows/Fonts/bahnschrift.ttf"


def fuente(tam, variante):
    f = ImageFont.truetype(FUENTE, tam * E)
    f.set_variation_by_name(variante)
    return f


def rampa(colores, t):
    t = min(max(t, 0.0), 1.0) * (len(colores) - 1)
    i = min(int(t), len(colores) - 2)
    a, b, u = colores[i], colores[i + 1], t - i
    return tuple(round(a[k] + (b[k] - a[k]) * u) for k in range(3))


# ---- Datos ----
F = json.loads(gzip.decompress((DATOS / "fuego.json.gz").read_bytes()))
cf = np.array(F["cells"]).reshape(-1, 3)
fuego = np.zeros(len(cf))
for mes, a in F["sensores"]["NOAA-20"]["tipico"].items():
    a = np.array(a).reshape(-1, 2)
    fuego[a[:, 0].astype(int)] += a[:, 1] / 10          # detecciones por año (año típico)

L = json.loads((DATOS / "lluvia.json").read_text(encoding="utf-8"))
ca = np.array(L["mapa"]["celdas"]).reshape(-1, 3)
m = np.frombuffer(gzip.decompress((DATOS / "lluvia_celdas.bin.gz").read_bytes()), dtype="<u2")
m = m.reshape(-1, len(ca)).astype(float)
anios = m[: 6 * 12].reshape(6, 12, len(ca))               # 2019-2024: años completos
lluvia = anios.sum(axis=1).mean(axis=0)                    # mm por año

geo = json.loads((DATOS / "provincias.geojson").read_text(encoding="utf-8"))

# ---- Proyección: lon/lat -> píxeles, con el coseno de la latitud media ----
LAT_N, LAT_S, LON_O, LON_E = -21.6, -55.2, -73.8, -53.4
K = (H - 150 * E) / (LAT_N - LAT_S)
COS = math.cos(math.radians(-38))
ANCHO_MAPA = (LON_E - LON_O) * COS * K
ARRIBA = 84 * E


def proyectar(x0):
    return lambda lon, lat: (x0 + (lon - LON_O) * COS * K, ARRIBA + (LAT_N - lat) * K)


def lineas_provincias(dib, p, color, ancho):
    for f in geo["features"]:
        g = f["geometry"]
        polis = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poli in polis:
            for anillo in poli:
                dib.line([p(x, y) for x, y in anillo], fill=color, width=ancho, joint="curve")


def mapa(x0, celdas, valores, tope, colores, minimo, curva=0.5):
    """Capa RGBA con un cuadrado por celda (0,1°); el color sigue (valor / tope) ** curva."""
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dib = ImageDraw.Draw(capa)
    p = proyectar(x0)
    lado = 0.1 * K * 0.92
    orden = np.argsort(valores)                            # lo más intenso queda arriba
    for i in orden:
        v = valores[i]
        if v < minimo:
            continue
        x, y = p(celdas[i, 0] / 100, celdas[i, 1] / 100)
        c = rampa(colores, (v / tope) ** curva)
        dib.rectangle([x - lado / 2, y - lado / 2, x + lado / 2, y + lado / 2], fill=c + (255,))
    return capa, p


lienzo = Image.new("RGB", (W, H), NOCHE)

# Halo suave detrás de cada mapa
SEPARACION = 26 * E
X_AGUA = W - 34 * E - 2 * ANCHO_MAPA - SEPARACION
X_FUEGO = X_AGUA + ANCHO_MAPA + SEPARACION
for x0, color in ((X_AGUA, AGUA_C), (X_FUEGO, FUEGO_C)):
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([x0 - 30 * E, 150 * E, x0 + ANCHO_MAPA + 30 * E, 520 * E], fill=color + (38,))
    lienzo.paste(halo.filter(ImageFilter.GaussianBlur(90 * E)), (0, 0), halo.filter(ImageFilter.GaussianBlur(90 * E)))

# Agua: todas las celdas tienen lluvia
capa_agua, p_agua = mapa(X_AGUA, ca, lluvia, 2000, RAMPA_AGUA, 1, curva=0.85)  # el oeste seco queda oscuro
lienzo.paste(capa_agua, (0, 0), capa_agua)

# Fuego: silueta del país y celdas con detecciones, con un brillo difuso por encima
base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
p_fuego = proyectar(X_FUEGO)
dib_base = ImageDraw.Draw(base)
for f in geo["features"]:
    g = f["geometry"]
    for poli in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        dib_base.polygon([p_fuego(x, y) for x, y in poli[0]], fill=(16, 24, 38, 255))
lienzo.paste(base, (0, 0), base)
capa_fuego, _ = mapa(X_FUEGO, cf, fuego, 260, RAMPA_FUEGO, 0.6)
brillo = capa_fuego.filter(ImageFilter.GaussianBlur(7 * E))
lienzo.paste(brillo, (0, 0), brillo)
lienzo.paste(capa_fuego, (0, 0), capa_fuego)

# Límites provinciales finos sobre los dos mapas
lineas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dib_l = ImageDraw.Draw(lineas)
lineas_provincias(dib_l, p_agua, (7, 11, 18, 120), 1 * E)
lineas_provincias(dib_l, p_fuego, (60, 74, 96, 150), 1 * E)
lienzo.paste(lineas, (0, 0), lineas)

# ---- Textos ----
d = ImageDraw.Draw(lienzo)
IZQ = 64 * E


def texto(xy, s, f, color, espaciado=0):
    if not espaciado:
        d.text(xy, s, font=f, fill=color)
        return d.textlength(s, font=f)
    x = xy[0]
    for ch in s:
        d.text((x, xy[1]), ch, font=f, fill=color)
        x += d.textlength(ch, font=f) + espaciado
    return x - xy[0]


etiqueta = fuente(22, "SemiBold SemiCondensed")
# Pastilla del concurso
s_et = "CONTAR CON DATOS 2026"
ancho_et = sum(d.textlength(ch, font=etiqueta) + 3 * E for ch in s_et) - 3 * E
d.rounded_rectangle([IZQ, 70 * E, IZQ + ancho_et + 28 * E, 70 * E + 44 * E], radius=4 * E, fill=TEXTO)
texto((IZQ + 14 * E, 77 * E), s_et, etiqueta, NOCHE, 3 * E)

titulo = fuente(112, "Bold Condensed")
y = 150 * E
for linea in ("LA MEMORIA", "DEL TERRITORIO"):
    d.text((IZQ - 4 * E, y), linea, font=titulo, fill=TEXTO)
    y += 106 * E

sub = fuente(48, "SemiBold SemiCondensed")
y += 34 * E
x = IZQ
x += texto((x, y), "Cuándo llueve.", sub, AGUA_C)
texto((x + 18 * E, y), "Cuándo arde.", sub, FUEGO_C)

pie = fuente(26, "SemiLight SemiCondensed")
texto((IZQ, y + 84 * E), "Argentina · 7 años de datos satelitales", pie, TENUE)

# Rótulos de los mapas (arriba, lejos de la marca de duración de YouTube)
rot = fuente(24, "Bold SemiCondensed")
for x0, s, color in ((X_AGUA, "AGUA", AGUA_C), (X_FUEGO, "FUEGO", FUEGO_C)):
    ancho = sum(d.textlength(ch, font=rot) + 4 * E for ch in s) - 4 * E
    texto((x0 + ANCHO_MAPA * 0.62 - ancho / 2, 44 * E), s, rot, color, 4 * E)

lienzo.resize((1280, 720), Image.LANCZOS).save(SALIDA, optimize=True)
print("ok", SALIDA, f"mapas desde {X_AGUA / E:.0f}px hasta {(X_FUEGO + ANCHO_MAPA) / E:.0f}px; titulo hasta {d.textlength('DEL TERRITORIO', font=titulo) / E + IZQ / E:.0f}px; sub hasta {(IZQ + d.textlength('Cuándo llueve.', font=sub) + 18 * E + d.textlength('Cuándo arde.', font=sub)) / E:.0f}px")
