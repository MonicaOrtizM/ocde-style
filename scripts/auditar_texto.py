# -*- coding: utf-8 -*-
"""
auditar_texto.py — mide un texto contra el perfil de arquitectura de párrafo.

    python auditar_texto.py --texto borrador.docx --idioma es
    python auditar_texto.py --texto nota.md --idioma en --salida auditoria.md

Solo mide. No reescribe. Devuelve cuántos párrafos cumplen, cuáles no y por qué,
para que la corrección sea una decisión y no una sugerencia difusa.

Umbrales en `PERFIL`, derivados de 48 notas de país de la OCDE. Los del español
son una conversión razonada sobre esa medición, no una medición propia.
"""

import argparse
import json
import os
import re
import sys
import unicodedata

PERFIL = {
    "en": {"oraciones_max": 3, "palabras_max": 100, "primera_max": 35,
           "palabras_min": 15, "primera_min": 8},
    "es": {"oraciones_max": 3, "palabras_max": 100, "primera_max": 40,
           "palabras_min": 18, "primera_min": 10},
}

RE_PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][\wÁÉÍÓÚÜÑáéíóúüñ'\-]*", re.UNICODE)
RE_CIFRA = re.compile(r"\d")
ABREV = (r"(?<!\b[A-Z])(?<!\be\.g)(?<!\bi\.e)(?<!\betc)(?<!\bvs)(?<!\bFig)"
         r"(?<!\bNo)(?<!\bDr)(?<!\bSr)(?<!\bSra)(?<!\bp)(?<!\bpp)(?<!\bart)"
         r"(?<!\bnúm)(?<!\bcap)(?<!\bEE)(?<!\bUU)")
RE_ORACION = re.compile(ABREV + r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ(¿¡\"“])")

DEBILES = {
    "es": [r"^hay\b", r"^existen?\b", r"^es (importante|necesario|clave|fundamental)\b",
           r"^este (documento|informe|apartado|capítulo|texto)\b",
           r"^en (el marco de|este sentido|este contexto|lo que respecta)\b",
           r"^cabe (señalar|destacar|mencionar|resaltar)\b",
           r"^se (puede|debe|observa que|evidencia que)\b",
           r"^a continuación\b", r"^como se (mencionó|señaló|indicó)\b",
           r"^uno de los\b", r"^el objetivo de\b", r"^por su parte\b",
           r"^de acuerdo con\b", r"^según\b", r"^resulta\b"],
    "en": [r"^there (is|are|was|were|has|have)\b", r"^it (is|was|has|should)\b",
           r"^this (is|was|section|note|paper|chapter|document)\b",
           r"^in this\b", r"^the purpose of\b", r"^as (mentioned|noted|discussed)\b",
           r"^one of the\b", r"^according to\b", r"^in terms of\b"],
}

REFERENTE = {
    "es": ["promedio", "frente a", "comparad", "respecto", "mientras que",
           "por encima", "por debajo", "más que", "menos que", "veces",
           "ocde", "américa latina", "la región", "el país", "en contraste",
           "a diferencia", "supera", "inferior a", "superior a", "del total",
           "puntos porcentuales", "entre 20", "pasó de", "creció", "cayó"],
    "en": ["average", "compared", "relative to", "while", "whereas",
           "above the", "below the", "more than", "less than", "times",
           "oecd", "latin america", "the region", "in contrast", "exceeds",
           "higher than", "lower than", "of the total", "percentage points",
           "rose from", "fell", "ranks"],
}


def sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", t or "")
                   if unicodedata.category(c) != "Mn").lower()


def parrafos_docx(ruta):
    import docx
    d = docx.Document(ruta)
    salida = []
    for p in d.paragraphs:
        t = (p.text or "").strip()
        estilo = (p.style.name or "").lower() if p.style else ""
        if not t:
            continue
        if "heading" in estilo or "título" in estilo or "titulo" in estilo:
            continue
        salida.append(t)
    return salida


# Texto legal y de créditos que se repite en las publicaciones y no es prosa
# del documento. Sin este filtro un PDF institucional parece lleno de párrafos
# sin dato que en realidad son el aviso de derechos.
BOILERPLATE = [
    "you must not use this work", "third-party material", "any dispute",
    "attribution 4.0", "creative commons", "cc by", "© oecd", "(c) oecd",
    "please cite this publication", "statlink", "rights and permissions",
    "the statistical data for israel", "note by türkiye", "note by turkey",
    "this document, as well as any data and map", "you must",
    "the opinions expressed and arguments employed", "corrigenda", "disclaimer",
    "translations", "adaptations", "questions can be", "for more information",
    "todos los derechos reservados", "queda prohibida", "cite esta publicación",
]


def parrafos_pdf(ruta):
    """Párrafos según los bloques de maquetación, no según líneas en blanco.

    Un PDF a dos columnas no separa párrafos con línea en blanco. Dividir por
    saltos dobles devuelve un solo bloque enorme o ninguno.
    """
    import fitz
    salida = []
    with fitz.open(ruta) as doc:
        for pagina in doc:
            for b in pagina.get_text("blocks", sort=True):
                if len(b) >= 7 and b[6] != 0:            # 1 es imagen
                    continue
                t = b[4] or ""
                t = re.sub(r"-\n(?=[a-zá-ú])", "", t)
                t = re.sub(r"\s*\n\s*", " ", t).strip()
                t = re.sub(r"\s{2,}", " ", t)
                if not t:
                    continue
                bajo = t.lower()
                if any(x in bajo for x in BOILERPLATE):
                    continue
                if re.match(r"^\s*(Source|Note|Fuente|Nota|Figure|Table|Chart|"
                            r"Box|Gráfico|Tabla|Cuadro)\b", t, re.I):
                    continue
                if sum(c.isdigit() for c in t) / max(1, len(t)) > 0.16:
                    continue                              # fila de tabla
                salida.append(t)
    return salida


def parrafos_texto(ruta):
    with open(ruta, encoding="utf-8") as f:
        crudo = f.read()
    crudo = re.sub(r"```.*?```", "", crudo, flags=re.S)      # bloques de código
    salida = []
    for b in re.split(r"\n\s*\n", crudo):
        b = re.sub(r"\s*\n\s*", " ", b).strip()
        if not b or b.startswith("#") or b.startswith("|"):
            continue
        if re.match(r"^\s*([-*+]|\d+\.)\s", b):              # listas
            continue
        if re.match(r"^(---|===)", b):
            continue
        salida.append(b)
    return salida


def leer(ruta):
    ext = os.path.splitext(ruta)[1].lower()
    if ext == ".docx":
        return parrafos_docx(ruta)
    if ext == ".pdf":
        return parrafos_pdf(ruta)
    if ext in (".md", ".txt", ".markdown"):
        return parrafos_texto(ruta)
    raise SystemExit(f"Formato no soportado: {ext}. Use .docx, .pdf, .md o .txt")


# Palabras funcionales, las que ningún texto largo puede evitar. Sirven para
# reconocer el idioma sin depender del vocabulario técnico, que suele ser
# parecido en los dos.
FUNCIONALES = {
    "es": ["de", "la", "que", "el", "en", "los", "del", "se", "por", "con",
           "las", "una", "para", "es", "al", "su", "como", "más", "este"],
    "en": ["the", "of", "and", "to", "in", "is", "that", "for", "with", "as",
           "on", "by", "are", "this", "from", "at", "has", "been", "its"],
}


def detectar_idioma(parrafos):
    palabras = [p.lower() for p in RE_PALABRA.findall(" ".join(parrafos))]
    if not palabras:
        return "es", 0, 0
    conteo = {}
    for idioma, lista in FUNCIONALES.items():
        marcas = set(lista)
        conteo[idioma] = sum(1 for p in palabras if p in marcas)
    ganador = max(conteo, key=conteo.get)
    return ganador, conteo["es"], conteo["en"]


def oraciones_de(p):
    return [o.strip() for o in RE_ORACION.split(p) if len(RE_PALABRA.findall(o)) >= 3]


REGLAS = [
    ("parrafo_largo", "Párrafo de más de {oraciones_max} oraciones"),
    ("parrafo_pesado", "Párrafo de más de {palabras_max} palabras"),
    ("apertura_larga", "Apertura de más de {primera_max} palabras"),
    ("sin_dato", "Párrafo sin ninguna cifra"),
    ("sin_referente", "Párrafo sin referente de comparación"),
    ("apertura_debil", "Apertura que retrasa la afirmación"),
]


def auditar(parrafos, idioma):
    """Marca cada párrafo regla por regla. No emite un veredicto binario.

    Un párrafo puede pasar de tres oraciones y estar bien escrito. Lo que
    importa no es si un párrafo incumple una regla, sino con qué frecuencia lo
    hace el texto comparado con el corpus de referencia.
    """
    u = PERFIL[idioma]
    debiles = [re.compile(p, re.I) for p in DEBILES[idioma]]
    refs = REFERENTE[idioma]
    filas, descartados = [], 0
    for i, p in enumerate(parrafos, start=1):
        ors = oraciones_de(p)
        palabras = len(RE_PALABRA.findall(p))
        if not ors or palabras < 12:         # títulos, rótulos, firmas, pies
            descartados += 1
            continue
        primera = len(RE_PALABRA.findall(ors[0]))
        bajo = sin_tildes(p)
        marcas = {
            "parrafo_largo": len(ors) > u["oraciones_max"],
            "parrafo_pesado": palabras > u["palabras_max"],
            "apertura_larga": primera > u["primera_max"],
            "sin_dato": not RE_CIFRA.search(p),
            "sin_referente": not any(r in bajo for r in refs),
            "apertura_debil": any(d.search(ors[0].strip()) for d in debiles),
        }
        filas.append({"n": i, "oraciones": len(ors), "palabras": palabras,
                      "primera": primera, "marcas": marcas,
                      "estructural": marcas["parrafo_largo"] or marcas["parrafo_pesado"],
                      "texto": p[:150]})
    return filas, descartados


def tasas(filas):
    n = max(1, len(filas))
    return {k: round(100 * sum(1 for f in filas if f["marcas"][k]) / n)
            for k, _ in REGLAS}


def calcular_base(carpeta, idioma):
    """Línea base con las mismas reglas, medida sobre el corpus de referencia.

    Sin esto los umbrales son opiniones. Con esto se puede decir que un texto
    tiene el triple de párrafos largos que el corpus, que es una afirmación
    verificable.
    """
    todas, docs = [], 0
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.lower().endswith((".pdf", ".docx", ".md", ".txt")):
            continue
        ruta = os.path.join(carpeta, nombre)
        try:
            ps = leer(ruta)
            if ruta.lower().endswith(".pdf"):
                import fitz
                with fitz.open(ruta) as d:
                    if d.page_count > 20:      # publicaciones largas fuera
                        continue
            filas, _ = auditar(ps, idioma)
        except Exception as e:
            print(f"  ! {nombre}  {e}")
            continue
        if filas:
            todas.extend(filas)
            docs += 1
    return {"documentos": docs, "parrafos": len(todas), "idioma": idioma,
            "tasas": tasas(todas)}


DIR_REF = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "referencias")


def ruta_base(idioma):
    return os.path.normpath(os.path.join(DIR_REF, f"base_{idioma}.json"))


def cargar_base(idioma):
    """Línea base del idioma pedido, o la del otro con aviso.

    El corpus de referencia está en inglés. Para un texto en español se usa esa
    misma base porque las reglas estructurales, oraciones por párrafo y presencia
    de dato, no dependen del idioma. Los umbrales de palabras sí están ajustados
    en PERFIL. La comparación queda marcada como prestada, no como propia.
    """
    for candidato, prestada in ((idioma, False),
                                ("en" if idioma == "es" else "es", True)):
        ruta = ruta_base(candidato)
        if os.path.isfile(ruta):
            try:
                with open(ruta, encoding="utf-8") as f:
                    base = json.load(f)
                base["prestada"] = prestada
                return base
            except Exception:
                continue
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--texto")
    ap.add_argument("--calcular-base", metavar="CARPETA",
                    help="Recalcula la línea base sobre un corpus y la guarda")
    ap.add_argument("--idioma", choices=["es", "en", "auto"], default="auto")
    ap.add_argument("--salida")
    args = ap.parse_args()

    if args.calcular_base:
        idioma = args.idioma if args.idioma != "auto" else "en"
        print(f"Midiendo la línea base en {args.calcular_base} (idioma {idioma})")
        base = calcular_base(args.calcular_base, idioma)
        os.makedirs(os.path.normpath(DIR_REF), exist_ok=True)
        with open(ruta_base(idioma), "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print(f"\n  {base['documentos']} documentos, {base['parrafos']} párrafos")
        for clave, etiqueta in REGLAS:
            print(f"  {etiqueta.format(**PERFIL[idioma]):<46}"
                  f"{base['tasas'][clave]:>4}%")
        print(f"\nLínea base en {ruta_base(idioma)}")
        return

    if not args.texto:
        sys.exit("Indique --texto o --calcular-base")
    if not os.path.isfile(args.texto):
        sys.exit(f"No existe: {args.texto}")

    parrafos = leer(args.texto)
    if not parrafos:
        sys.exit("No se extrajo texto del archivo.")
    idioma, n_es, n_en = detectar_idioma(parrafos)
    if args.idioma != "auto":
        idioma = args.idioma
        aviso = f"idioma {idioma} (indicado)"
    else:
        aviso = f"idioma {idioma} (detectado, {n_es} marcas es contra {n_en} en)"

    filas, descartados = auditar(parrafos, idioma)
    if not filas:
        sys.exit("No se encontró prosa que auditar.")

    mias = tasas(filas)
    base = cargar_base(idioma)
    u = PERFIL[idioma]

    # Un párrafo se señala cuando falla en lo estructural, que es lo que la
    # skill sabe corregir. Las demás marcas informan, no condenan.
    señalados = sorted([f for f in filas if f["estructural"]],
                       key=lambda f: (-f["oraciones"], -f["palabras"]))

    L = []
    a = L.append
    a(f"# Auditoría de estilo, {os.path.basename(args.texto)}\n")
    a(f"Perfil aplicado. {aviso}")
    a(f"Párrafos de prosa auditados. {len(filas)}")
    a(f"No auditados por ser títulos, rótulos o listas. {descartados}\n")
    a("## Frecuencia por regla\n")
    a("La columna de referencia es el corpus de notas de la OCDE medido con "
      "estas mismas reglas. No es un objetivo de cero, es la frecuencia con "
      "que la propia OCDE se sale de cada regla.\n")
    a("| Regla | Este texto | Corpus OCDE | Lectura |")
    a("|---|---|---|---|")
    for clave, etiqueta in REGLAS:
        mio = mias[clave]
        ref = base["tasas"].get(clave) if base else None
        if ref is None:
            lectura = "sin referencia"
            refs = "n.d."
        else:
            refs = f"{ref}%"
            if mio >= ref + 20:
                lectura = "**muy por encima**"
            elif mio >= ref + 10:
                lectura = "por encima"
            elif mio <= max(0, ref - 10):
                lectura = "por debajo"
            else:
                lectura = "en línea"
        a(f"| {etiqueta.format(**u)} | {mio}% | {refs} | {lectura} |")
    a("")
    a("## Párrafos señalados por estructura\n")
    a(f"{len(señalados)} de {len(filas)} párrafos pasan de "
      f"{u['oraciones_max']} oraciones o de {u['palabras_max']} palabras. "
      f"Son los que la skill puede partir sin tocar el contenido.\n")
    for f in señalados:
        marcas = [e.format(**u) for k, e in REGLAS if f["marcas"][k]]
        a(f"**Párrafo {f['n']}.** {f['oraciones']} oraciones, {f['palabras']} "
          f"palabras, apertura de {f['primera']}.")
        a(f"  {'; '.join(marcas)}")
        a(f"  > {f['texto']}...\n")
    if not señalados:
        a("Ninguno. La estructura de párrafo está dentro del perfil.\n")

    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            f.write("\n".join(L))

    print("=" * 70)
    print(f"  Perfil aplicado      {aviso}")
    print(f"  Párrafos de prosa    {len(filas):>4}")
    print(f"  No auditados         {descartados:>4}   (títulos, rótulos, listas)")
    print("=" * 70)
    print(f"  {'Regla':<44}{'texto':>7}{'OCDE':>7}")
    print("-" * 70)
    for clave, etiqueta in REGLAS:
        ref = base["tasas"].get(clave) if base else None
        marca = ""
        if ref is not None and mias[clave] >= ref + 20:
            marca = "  <<"
        print(f"  {etiqueta.format(**u):<44}{mias[clave]:>6}%"
              f"{(str(ref) + '%') if ref is not None else '  n.d.':>7}{marca}")
    print("=" * 70)
    print(f"  Señalados por estructura   {len(señalados):>3} de {len(filas)}")
    if señalados:
        print("  Párrafos " + ", ".join(str(f["n"]) for f in señalados[:25]) +
              (" …" if len(señalados) > 25 else ""))
    if base:
        nota = (" La base está en inglés y el texto no, así que las tasas de "
                "palabras se comparan con umbrales distintos."
                if base.get("prestada") else "")
        print(f"\n  Referencia. {base['documentos']} documentos, "
              f"{base['parrafos']} párrafos, idioma {base['idioma']}.{nota}")
    else:
        print("\n  Sin línea base para este idioma. Genérela con --calcular-base.")
    if args.salida:
        print(f"\nInforme en {args.salida}")


if __name__ == "__main__":
    main()
