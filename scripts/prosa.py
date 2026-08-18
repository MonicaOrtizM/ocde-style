# -*- coding: utf-8 -*-
"""
prosa.py — criterio único de qué bloque de texto cuenta como prosa.

Vive aparte porque lo usan el analizador y el auditor, y si cada uno aplica el
suyo miden poblaciones distintas del mismo corpus. Eso ya pasó una vez. El perfil
descriptivo veía 1.173 párrafos y la línea base 1.915, así que el mismo corpus
daba 36% de párrafos de una sola oración en un archivo y 55% en el otro.
"""

import re

RE_PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][\wÁÉÍÓÚÜÑáéíóúüñ'\-]*", re.UNICODE)

# Texto legal y de créditos que las publicaciones repiten en cada documento.
# Sin este filtro un PDF institucional parece lleno de párrafos sin dato que en
# realidad son el aviso de derechos.
BOILERPLATE = [
    "you must not use this work", "third-party material", "any dispute",
    "attribution 4.0", "creative commons", "cc by", "© oecd", "(c) oecd",
    "please cite this publication", "statlink", "rights and permissions",
    "the statistical data for israel", "note by türkiye", "note by turkey",
    "this document, as well as any data and map", "you must",
    "the opinions expressed and arguments employed", "corrigenda", "disclaimer",
    "the use of this work, whether digital or print",
    "translations", "adaptations", "questions can be", "for more information",
    "todos los derechos reservados", "queda prohibida", "cite esta publicación",
]

RE_ROTULO = re.compile(
    r"^\s*(Source|Note|StatLink|Figure|Table|Chart|Box|Panel|"
    r"Fuente|Nota|Gráfico|Tabla|Cuadro|Recuadro)\b", re.I)

MIN_PALABRAS = 12
MIN_CARACTERES = 60
MAX_DENSIDAD_DIGITOS = 0.16


def es_boilerplate(p):
    bajo = p.lower()
    return any(b in bajo for b in BOILERPLATE)


def es_prosa(p):
    """Un bloque cuenta como prosa si pasa las cinco condiciones.

    Tiene doce palabras y sesenta caracteres, no es mayoría dígitos, no abre con
    un rótulo de figura o fuente, no es texto legal, y termina en puntuación.
    """
    if len(RE_PALABRA.findall(p)) < MIN_PALABRAS or len(p) < MIN_CARACTERES:
        return False
    if sum(c.isdigit() for c in p) / max(1, len(p)) > MAX_DENSIDAD_DIGITOS:
        return False
    if RE_ROTULO.match(p):
        return False
    if es_boilerplate(p):
        return False
    return bool(re.search(r"[.!?]\s*$", p))
