# -*- coding: utf-8 -*-
"""
analizar_estilo.py — mide la arquitectura del párrafo en un corpus de PDF.

    python analizar_estilo.py --corpus "C:\\ruta\\Corpus OCDE" --salida perfil.md

Lo que se mide no es el tema ni el género, es la forma. La hipótesis a contrastar
es que cada párrafo abre con una afirmación que se sostiene sola y que el resto
del párrafo la respalda con evidencia. Si es cierta, tres cosas deben aparecer
en los números.

  · La primera oración es más corta que las que la siguen.
  · La primera oración afirma sin cifras y las siguientes cuantifican.
  · Los párrafos son cortos, de dos a cuatro oraciones.

El script mide cada una y reporta el resultado, incluso si contradice la
hipótesis. Un perfil de estilo que solo confirma lo que ya se creía no sirve
para calibrar nada.

La extracción de PDF mezcla tablas con prosa, así que se filtra a bloques que
parecen prosa y se reporta cuánto se descartó, para que el sesgo quede visible.
"""

import argparse
import json
import os
import re
import statistics as st
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prosa import es_prosa                                   # noqa: E402

ABREV = (r"(?<!\b[A-Z])(?<!\be\.g)(?<!\bi\.e)(?<!\betc)(?<!\bvs)(?<!\bFig)"
         r"(?<!\bNo)(?<!\bDr)(?<!\bp)(?<!\bpp)(?<!\bapprox)(?<!\bUS)")
RE_ORACION = re.compile(ABREV + r"(?<=[.!?])\s+(?=[A-Z(“\"])")
RE_PALABRA = re.compile(r"[A-Za-z][A-Za-z'\-]+")
RE_CIFRA = re.compile(r"\d")
RE_FIGURA = re.compile(r"\b(Figure|Table|Chart|Box|Panel)\s+[A-Z]?\.?\d", re.I)

# Aperturas que retrasan la afirmación. Se cuentan para saber si el corpus
# las evita, no porque se den por malas de antemano.
DEBILES = [r"^there (is|are|was|were|has|have)\b", r"^it (is|was|has|should)\b",
           r"^this (is|was|section|note|paper|chapter)\b", r"^in this\b",
           r"^the purpose of\b", r"^as (mentioned|noted|discussed)\b",
           r"^one of the\b", r"^according to\b"]
RE_DEBILES = [re.compile(p, re.I) for p in DEBILES]

MODALES = ["should", "could", "must", "needs to", "need to", "requires",
           "would benefit", "is needed", "are needed"]
CONECTORES = ["however", "moreover", "in addition", "nevertheless", "while",
              "whereas", "although", "by contrast", "in particular", "overall",
              "at the same time", "as a result", "therefore", "furthermore",
              "yet", "still", "meanwhile", "conversely"]
COMPARACION = ["oecd average", "compared with", "compared to", "above the",
               "below the", "highest among", "lowest among", "ranks",
               "relative to", "in line with", "one of the highest",
               "one of the lowest", "latin america", "peer countries",
               "than in", "twice", "half of", "three times"]


def bloques_de(ruta):
    """Párrafos según los bloques de maquetación del PDF, no según líneas en blanco.

    Un PDF maquetado a dos columnas no separa párrafos con línea en blanco, así
    que dividir por \\n\\n devuelve un solo bloque de veinte oraciones o ninguno.
    fitz entrega bloques con coordenadas, que sí corresponden a párrafos
    visuales. Es la diferencia entre medir la escritura y medir el PDF.
    """
    import fitz
    salida = []
    with fitz.open(ruta) as doc:
        n = doc.page_count
        for pagina in doc:
            for b in pagina.get_text("blocks", sort=True):
                if len(b) >= 7 and b[6] != 0:          # 1 es imagen
                    continue
                t = b[4] or ""
                t = re.sub(r"-\n(?=[a-z])", "", t)     # une palabras cortadas
                t = re.sub(r"\s*\n\s*", " ", t).strip()
                t = re.sub(r"\s{2,}", " ", t)
                if t:
                    salida.append(t)
    return salida, n




def es_encabezado(p):
    palabras = RE_PALABRA.findall(p)
    return (2 <= len(palabras) <= 14 and len(p) < 95
            and not re.search(r"[.;:]\s*$", p)
            and not re.match(r"^\s*(Source|Note|Figure|Table|Chart)\b", p, re.I))


def oraciones_de(p):
    return [o.strip() for o in RE_ORACION.split(p) if len(RE_PALABRA.findall(o)) >= 3]


def anatomia(p):
    """Radiografía de un párrafo. Es el corazón del análisis."""
    ors = oraciones_de(p)
    if not ors:
        return None
    largos = [len(RE_PALABRA.findall(o)) for o in ors]
    primera, resto = ors[0], ors[1:]
    largos_resto = largos[1:]
    return {
        "n_oraciones": len(ors),
        "palabras": sum(largos),
        "primera_palabras": largos[0],
        "resto_media": round(st.mean(largos_resto), 1) if largos_resto else None,
        "primera_con_cifra": bool(RE_CIFRA.search(primera)),
        "resto_con_cifra": any(RE_CIFRA.search(o) for o in resto),
        "primera_debil": any(r.search(primera.strip()) for r in RE_DEBILES),
        "apertura": " ".join(RE_PALABRA.findall(primera)[:2]).lower(),
        "primera_texto_len": len(primera),
    }


def cuenta(frases, bajo):
    return {f: bajo.count(f) for f in frases if bajo.count(f)}


def analizar_doc(ruta):
    parrafos, paginas = bloques_de(ruta)
    texto = "\n".join(parrafos)
    prosa = [p for p in parrafos if es_prosa(p)]
    anas = [a for a in (anatomia(p) for p in prosa) if a]
    cuerpo = " ".join(prosa)
    bajo = cuerpo.lower()
    palabras = RE_PALABRA.findall(cuerpo)

    return {
        "archivo": os.path.basename(ruta),
        "paginas": paginas,
        "parrafos_totales": len(parrafos),
        "parrafos_prosa": len(prosa),
        "descartado_pct": round(100 * (1 - len(prosa) / max(1, len(parrafos)))),
        "palabras_prosa": len(palabras),
        "anatomias": anas,
        "encabezados": [p for p in parrafos if es_encabezado(p)],
        "llamados_figura": len(RE_FIGURA.findall(texto)),
        "modales": cuenta(MODALES, bajo),
        "conectores": cuenta(CONECTORES, bajo),
        "comparacion": cuenta(COMPARACION, bajo),
    }


def pct(vals, q):
    if not vals:
        return 0
    vals = sorted(vals)
    return vals[min(len(vals) - 1, int(round(q * (len(vals) - 1))))]


def porcentaje(cond, total):
    return round(100 * cond / max(1, total))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--json")
    ap.add_argument("--max-paginas", type=int, default=0,
                    help="Excluye documentos más largos. 0 los incluye todos.")
    args = ap.parse_args()

    rutas = sorted(os.path.join(args.corpus, n) for n in os.listdir(args.corpus)
                   if n.lower().endswith(".pdf"))
    if not rutas:
        raise SystemExit(f"No hay PDF en {args.corpus}")

    docs, excluidos = [], []
    for i, r in enumerate(rutas, start=1):
        try:
            d = analizar_doc(r)
        except Exception as e:
            print(f"[{i:>2}/{len(rutas)}] fallo  {os.path.basename(r)}  {e}")
            continue
        if args.max_paginas and d["paginas"] > args.max_paginas:
            excluidos.append((d["archivo"], d["paginas"]))
            print(f"[{i:>2}/{len(rutas)}] excluido por largo ({d['paginas']} p)  "
                  f"{d['archivo'][:52]}")
            continue
        docs.append(d)
        n = len(d["anatomias"])
        med = st.median([a["n_oraciones"] for a in d["anatomias"]]) if n else 0
        print(f"[{i:>2}/{len(rutas)}] {d['paginas']:>3} p  {n:>4} párr.  "
              f"mediana {med:.0f} or/párr  {d['archivo'][:48]}")

    A = [a for d in docs for a in d["anatomias"]]
    if not A:
        raise SystemExit("No se extrajo prosa. Revise el corpus.")

    n_ors = [a["n_oraciones"] for a in A]
    palabras_par = [a["palabras"] for a in A]
    primera = [a["primera_palabras"] for a in A]
    multi = [a for a in A if a["n_oraciones"] >= 2]
    resto = [a["resto_media"] for a in multi]
    afirma_luego_prueba = [a for a in multi
                           if not a["primera_con_cifra"] and a["resto_con_cifra"]]

    def agrega(clave):
        c = Counter()
        for d in docs:
            c.update(d[clave])
        return c

    resumen = {
        "documentos": len(docs),
        "excluidos_por_largo": excluidos,
        "paginas": sum(d["paginas"] for d in docs),
        "parrafos_analizados": len(A),
        "palabras_prosa": sum(d["palabras_prosa"] for d in docs),
        "descartado_pct_medio": round(st.mean(d["descartado_pct"] for d in docs)),
        "oraciones_por_parrafo": {
            "media": round(st.mean(n_ors), 1), "mediana": pct(n_ors, .5),
            "p25": pct(n_ors, .25), "p75": pct(n_ors, .75), "p90": pct(n_ors, .9),
            "dist": {f"{k} oración(es)": porcentaje(sum(1 for x in n_ors if x == k), len(n_ors))
                     for k in range(1, 7)},
            "pct_5_o_mas": porcentaje(sum(1 for x in n_ors if x >= 5), len(n_ors)),
        },
        "palabras_por_parrafo": {
            "media": round(st.mean(palabras_par), 1), "mediana": pct(palabras_par, .5),
            "p25": pct(palabras_par, .25), "p75": pct(palabras_par, .75),
            "p90": pct(palabras_par, .9),
        },
        "primera_oracion": {
            "media": round(st.mean(primera), 1), "mediana": pct(primera, .5),
            "p25": pct(primera, .25), "p75": pct(primera, .75), "p90": pct(primera, .9),
        },
        "resto_del_parrafo": {
            "media": round(st.mean(resto), 1) if resto else 0,
            "mediana": pct(resto, .5) if resto else 0,
        },
        "primera_mas_corta_que_resto_pct": porcentaje(
            sum(1 for a in multi if a["resto_media"] and a["primera_palabras"] < a["resto_media"]),
            len(multi)),
        "primera_con_cifra_pct": porcentaje(sum(1 for a in A if a["primera_con_cifra"]), len(A)),
        "resto_con_cifra_pct": porcentaje(sum(1 for a in multi if a["resto_con_cifra"]), len(multi)),
        "patron_afirmacion_luego_evidencia_pct": porcentaje(len(afirma_luego_prueba), len(multi)),
        "aperturas_debiles_pct": porcentaje(sum(1 for a in A if a["primera_debil"]), len(A)),
        "aperturas_frecuentes": Counter(a["apertura"] for a in A).most_common(25),
        "encabezados_frecuentes": Counter(
            h.strip() for d in docs for h in d["encabezados"]).most_common(25),
        "llamados_figura_por_doc": round(st.mean(d["llamados_figura"] for d in docs), 1),
        "modales": agrega("modales").most_common(12),
        "conectores": agrega("conectores").most_common(16),
        "comparacion": agrega("comparacion").most_common(16),
    }

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(resumen, f, ensure_ascii=False, indent=1)

    o = resumen["oraciones_por_parrafo"]
    pp = resumen["palabras_por_parrafo"]
    p1 = resumen["primera_oracion"]
    L = []
    a = L.append
    a("# Perfil de arquitectura de párrafo\n")
    a(f"Corpus. {resumen['documentos']} documentos, {resumen['paginas']} páginas, "
      f"{resumen['parrafos_analizados']} párrafos de prosa, "
      f"{resumen['palabras_prosa']:,} palabras.")
    a(f"Se descartó el {resumen['descartado_pct_medio']}% de los bloques por ser "
      f"tablas, leyendas o encabezados sueltos.\n")
    if excluidos:
        a(f"Excluidos por largo. {len(excluidos)} documentos.\n")

    a("## Las tres hipótesis\n")
    a(f"**1. El párrafo es corto.** Mediana de {o['mediana']} oraciones y "
      f"{pp['mediana']} palabras. El cuartil superior llega a {o['p75']} oraciones "
      f"y {pp['p75']} palabras. Solo el {o['pct_5_o_mas']}% de los párrafos tiene "
      f"cinco oraciones o más.\n")
    a(f"**2. La primera oración es más corta.** Mediana de {p1['mediana']} palabras "
      f"contra {resumen['resto_del_parrafo']['mediana']} del resto. Ocurre en el "
      f"{resumen['primera_mas_corta_que_resto_pct']}% de los párrafos de dos o más "
      f"oraciones.\n")
    a(f"**3. La primera afirma y el resto prueba.** El "
      f"{resumen['primera_con_cifra_pct']}% de las primeras oraciones contiene una "
      f"cifra, frente al {resumen['resto_con_cifra_pct']}% del resto del párrafo. "
      f"El patrón completo, abrir sin cifra y cuantificar después, aparece en el "
      f"{resumen['patron_afirmacion_luego_evidencia_pct']}% de los párrafos.\n")
    a(f"**Aperturas que retrasan la afirmación.** Solo el "
      f"{resumen['aperturas_debiles_pct']}% de los párrafos abre con there is, "
      f"it is, this is, in this o according to.\n")

    a("## Distribución de oraciones por párrafo\n")
    for k, v in o["dist"].items():
        a(f"- {k}. {v}%")
    a("")
    a("## Longitudes\n")
    a(f"- Párrafo. media {pp['media']} palabras, mediana {pp['mediana']}, "
      f"cuartiles {pp['p25']} y {pp['p75']}, p90 {pp['p90']}.")
    a(f"- Primera oración. media {p1['media']}, mediana {p1['mediana']}, "
      f"cuartiles {p1['p25']} y {p1['p75']}, p90 {p1['p90']}.")
    a(f"- Resto del párrafo. media {resumen['resto_del_parrafo']['media']}.")
    a(f"- Llamados a figura o tabla por documento. {resumen['llamados_figura_por_doc']}\n")

    for titulo, clave in [("Conectores", "conectores"),
                          ("Fórmulas de comparación", "comparacion"),
                          ("Verbos de recomendación", "modales")]:
        a(f"## {titulo}\n")
        for k, v in resumen[clave]:
            a(f"- {k}. {v}")
        a("")
    a("## Cómo abren los párrafos\n")
    for k, v in resumen["aperturas_frecuentes"]:
        if v > 2:
            a(f"- {k}. {v}")

    with open(args.salida, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"\nPerfil en {args.salida}")


if __name__ == "__main__":
    main()
