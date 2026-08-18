# -*- coding: utf-8 -*-
"""
auditar_texto.py — mide un texto contra el perfil de arquitectura de párrafo.

    python auditar_texto.py --texto borrador.docx --idioma es
    python auditar_texto.py --texto nota.md --idioma en --salida auditoria.md

Solo mide. No reescribe. Devuelve cuántos párrafos cumplen, cuáles no y por qué,
para que la corrección sea una decisión y no una sugerencia difusa.

Umbrales en `PERFIL`, derivados de 69 notas de país de la OCDE. Los del español
son una conversión razonada sobre esa medición, no una medición propia.
"""

import argparse
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prosa import es_prosa                                   # noqa: E402

PERFIL = {
    "en": {"oraciones_max": 3, "palabras_max": 100, "primera_max": 35},
    "es": {"oraciones_max": 3, "palabras_max": 100, "primera_max": 40},
}

# Los umbrales se pueden subir, pero no sin límite. Pasado el techo la regla 1
# deja de significar algo, porque un párrafo de seis oraciones ya no es una
# unidad que se entienda por separado, que es de lo que trata toda la skill.
# Los techos salen de la medición. El p90 del corpus es de 3 oraciones y 98
# palabras, y solo el 9% de los párrafos pasa de cinco oraciones.
TECHOS = {
    "oraciones_max": (5, "Con más de cinco oraciones el párrafo deja de ser una "
                         "unidad autónoma y la regla 1 pierde sentido. En el "
                         "corpus solo el 9% de los párrafos llega a ese tamaño."),
    "palabras_max": (150, "El p90 del corpus es de 98 palabras. Por encima de "
                          "150 ya no se está midiendo este estilo."),
    "primera_max": (60, "El p90 de la apertura es de 35 palabras. Una apertura "
                        "de más de 60 no afirma, enumera."),
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


# Palabras frecuentes que sobreviven al filtro de longitud y, si no se quitan,
# hacen que dos párrafos cualesquiera parezcan hablar de lo mismo.
STOP = {
    "es": set("""puede pueden podría podrian todos todas estos estas mismo misma
    mismos mismas sobre entre porque cuando donde también ademas además desde
    hasta según mientras aunque durante mediante través cualquier algunos algunas
    otros otras tiene tienen tener hacer hecho parte partes forma formas manera
    mayor menor mejor peor nivel niveles caso casos decir cada esta este esto
    para como muy sino solo sólo debe deben debería siendo fueron estaba estaban
    haber habia había siempre nunca luego antes despues después primero segundo
    tercero cuarto quinto general generales especifico específico principal
    principales nuevo nueva nuevos nuevas gran grande grandes pequeno pequeño
    total totales""".split()),
    "en": set("""which their there these those other others about would could
    should being where while after before between through during however
    therefore because though since still than then they them with from that this
    have been more most some such only also into over under both each when what
    will does term terms first second third fourth general specific main major
    minor level levels case cases part parts form forms same different large
    small total overall""".split()),
}


def tokens_contenido(texto, idioma):
    """Palabras con carga semántica, reducidas a su raíz aproximada.

    El truncamiento a seis caracteres hace de lematizador pobre y es
    imprescindible en español, que es muy flexivo. Sin él, designados y designa,
    o reunión y reuniones, cuentan como palabras distintas, y dos párrafos casi
    idénticos se quedan por debajo de cualquier umbral razonable.
    """
    salida = set()
    for w in RE_PALABRA.findall(texto):
        if len(w) < 5:
            continue
        raiz = sin_tildes(w)
        if raiz in STOP[idioma]:
            continue
        salida.add(raiz[:6])
    return salida


def cifras_de(texto):
    return set(re.findall(r"\d+(?:[.,]\d+)*", texto))


def similitud(a, b):
    """Cuánto se solapan dos párrafos, entre 0 y 1.

    Se usa el coeficiente de solapamiento y no Jaccard, porque un párrafo corto
    contenido dentro de uno largo es justamente el caso que interesa, y Jaccard
    lo castiga por la diferencia de tamaño.

    Compartir una cifra exacta suma, porque dos párrafos que citan el mismo
    número casi siempre están diciendo lo mismo dos veces.
    """
    ta, tb = a["tokens"], b["tokens"]
    if len(ta) < 4 or len(tb) < 4:
        return 0.0, set(), set()
    comunes = ta & tb
    base = len(comunes) / min(len(ta), len(tb))
    cifras = a["cifras"] & b["cifras"]
    return min(1.0, base + (0.15 if cifras else 0.0)), comunes, cifras


def pares_redundantes(filas, umbral):
    """Pares de párrafos que probablemente dicen lo mismo.

    Compara todos contra todos, no solo los contiguos, porque la repetición que
    de verdad estorba suele estar a varias páginas de distancia.
    """
    salida = []
    for i in range(len(filas)):
        for j in range(i + 1, len(filas)):
            s, comunes, cifras = similitud(filas[i], filas[j])
            if s >= umbral:
                salida.append({
                    "a": filas[i], "b": filas[j], "similitud": round(s, 2),
                    "comunes": sorted(comunes, key=len, reverse=True)[:8],
                    "cifras": sorted(cifras)[:5],
                    "distancia": filas[j]["n"] - filas[i]["n"],
                    "juntos_palabras": filas[i]["palabras"] + filas[j]["palabras"],
                    "juntos_oraciones": filas[i]["oraciones"] + filas[j]["oraciones"],
                })
    return sorted(salida, key=lambda x: -x["similitud"])


IDENTICO = 0.90   # por encima de esto los dos párrafos dicen lo mismo


def sugerencia(p, u):
    """Qué hacer con un par repetido. Tres casos, no uno.

    Fusionar no siempre es la respuesta. Si los dos párrafos dicen exactamente lo
    mismo no hay nada que combinar, sobra uno. Y si al juntarlos se pasa de los
    umbrales, entonces no eran una idea repetida sino dos ideas que comparten
    vocabulario.
    """
    cabe = (p["juntos_oraciones"] <= u["oraciones_max"]
            and p["juntos_palabras"] <= u["palabras_max"])
    tamaño = (f"Juntos dan {p['juntos_oraciones']} oraciones y "
              f"{p['juntos_palabras']} palabras")
    if p["similitud"] >= IDENTICO:
        return ("**Eliminar uno.** Con este solapamiento los dos afirman lo "
                "mismo y no hay nada que combinar. Conservar el que traiga el "
                "dato más preciso o la fuente más fuerte, y borrar el otro.")
    if cabe:
        return (f"**Fusionar.** Tratan la misma idea con aportes distintos. "
                f"{tamaño}, así que caben en un párrafo. La afirmación común va "
                f"en la primera oración y los dos datos en la segunda.")
    return (f"**Depurar, no fusionar.** {tamaño}, y no caben en un párrafo. "
            f"Revisar si de verdad es una idea repetida o son dos ideas que "
            f"comparten vocabulario. Si es lo primero, dejar una sola "
            f"afirmación con el mejor dato.")


REGLAS = [
    ("parrafo_largo", "Párrafo de más de {oraciones_max} oraciones"),
    ("parrafo_pesado", "Párrafo de más de {palabras_max} palabras"),
    ("apertura_larga", "Apertura de más de {primera_max} palabras"),
    ("sin_dato", "Párrafo sin ninguna cifra"),
    ("sin_referente", "Párrafo sin referente de comparación"),
    ("apertura_debil", "Apertura que retrasa la afirmación"),
]


def auditar(parrafos, idioma, u=None):
    """Marca cada párrafo regla por regla. No emite un veredicto binario.

    Un párrafo puede pasar de tres oraciones y estar bien escrito. Lo que
    importa no es si un párrafo incumple una regla, sino con qué frecuencia lo
    hace el texto comparado con el corpus de referencia.
    """
    u = u or PERFIL[idioma]
    debiles = [re.compile(p, re.I) for p in DEBILES[idioma]]
    refs = REFERENTE[idioma]
    filas, descartados = [], 0
    for i, p in enumerate(parrafos, start=1):
        if not es_prosa(p):        # títulos, rótulos, tablas, pies, texto legal
            descartados += 1
            continue
        ors = oraciones_de(p)
        palabras = len(RE_PALABRA.findall(p))
        if not ors:
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
                      "tokens": tokens_contenido(p, idioma),
                      "cifras": cifras_de(p),
                      "texto": p[:150]})
    return filas, descartados


def aplicar_umbrales(u, args):
    """Deja subir los umbrales, pero no hasta romper la regla 1.

    Un techo no es paternalismo. Si se admite un párrafo de ocho oraciones, la
    skill sigue midiendo algo, pero ya no mide el estilo que dice medir.
    """
    avisos = []
    for arg, clave in (("max_oraciones", "oraciones_max"),
                       ("max_palabras", "palabras_max"),
                       ("max_apertura", "primera_max")):
        v = getattr(args, arg)
        if v is None:
            continue
        techo, razon = TECHOS[clave]
        if v > techo:
            sys.exit(f"--{arg.replace('_', '-')} no puede pasar de {techo}. {razon}")
        if v != u[clave]:
            avisos.append(f"{clave} de {u[clave]} a {v}")
            u[clave] = v
    return avisos


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
    ap.add_argument("--max-oraciones", type=int,
                    help=f"Oraciones por párrafo. Techo {TECHOS['oraciones_max'][0]}")
    ap.add_argument("--max-palabras", type=int,
                    help=f"Palabras por párrafo. Techo {TECHOS['palabras_max'][0]}")
    ap.add_argument("--max-apertura", type=int,
                    help=f"Palabras de la apertura. Techo {TECHOS['primera_max'][0]}")
    ap.add_argument("--umbral-redundancia", type=float, default=0.75,
                    help="Solapamiento mínimo para señalar un par. Por defecto 0.75")
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

    umbrales = dict(PERFIL[idioma])
    avisos = aplicar_umbrales(umbrales, args)
    filas, descartados = auditar(parrafos, idioma, umbrales)
    if not filas:
        sys.exit("No se encontró prosa que auditar.")

    mias = tasas(filas)
    base = cargar_base(idioma)
    u = umbrales

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

    pares = pares_redundantes(filas, args.umbral_redundancia)
    a("## Ideas que se repiten\n")
    a(f"Pares de párrafos con un solapamiento de contenido igual o mayor a "
      f"{args.umbral_redundancia}. Se comparan todos contra todos, no solo los "
      f"contiguos.\n")
    if not pares:
        a("Ninguno. No hay párrafos que digan lo mismo dos veces.\n")
    for p in pares[:10]:
        accion = sugerencia(p, u)
        vecinos = ("contiguos" if p["distancia"] == 1
                   else f"separados por {p['distancia'] - 1} párrafos")
        a(f"**Párrafos {p['a']['n']} y {p['b']['n']}**, solapamiento "
          f"{p['similitud']}, {vecinos}.")
        a(f"  Comparten. {', '.join(p['comunes'])}"
          + (f". Misma cifra, {', '.join(p['cifras'])}" if p["cifras"] else ""))
        a(f"  {accion}")
        a(f"  > {p['a']['texto']}...")
        a(f"  > {p['b']['texto']}...\n")
    if len(pares) > 10:
        a(f"Y {len(pares) - 10} pares más por debajo de estos.\n")

    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            f.write("\n".join(L))

    print("=" * 70)
    print(f"  Perfil aplicado      {aviso}")
    if avisos:
        print(f"  Umbrales ajustados   {'; '.join(avisos)}")
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
    print(f"  Pares que se repiten       {len(pares):>3}"
          f"   (solapamiento >= {args.umbral_redundancia})")
    for p in pares[:6]:
        if p["similitud"] >= IDENTICO:
            que = "eliminar uno"
        elif (p["juntos_oraciones"] <= u["oraciones_max"]
              and p["juntos_palabras"] <= u["palabras_max"]):
            que = "fusionar"
        else:
            que = "depurar"
        print(f"    {p['a']['n']:>3} y {p['b']['n']:<3} sol. {p['similitud']:<5}"
              f" {que:<13} {', '.join(p['comunes'][:4])}")
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
