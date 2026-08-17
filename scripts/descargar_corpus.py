# -*- coding: utf-8 -*-
"""
descargar_corpus.py — baja a disco un corpus de PDF desde una lista.

    python descargar_corpus.py --lista pdfs.tsv --destino "C:\\ruta\\Corpus"

La lista es un TSV de dos columnas, título y URL (absoluta, o ruta que se
resuelve contra --base). El script descarga, verifica que el archivo empiece
por %PDF, cuenta páginas y deja un índice en CSV.

Nota sobre la OCDE. Sus páginas HTML están detrás de Cloudflare y responden 403
a un cliente de Python, pero los PDF bajo /content/dam/ se sirven sin bloqueo.
Por eso la resolución de enlaces se hace desde un navegador y la descarga desde
aquí. Si algún día el dominio de contenido también se protege, no hay que
buscar el error en este script.
"""

import argparse
import csv
import os
import re
import time
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
HDR = {"User-Agent": UA, "Accept": "application/pdf,*/*",
       "Accept-Language": "en-US,en;q=0.9", "Referer": "https://www.oecd.org/"}


def bajar(url, intentos=3, espera=2.0):
    ult = None
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers=HDR)
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            ult = e
            time.sleep(espera * (i + 1))
    raise ult


def limpiar(nombre):
    nombre = re.sub(r"[\\/:*?\"<>|]", "-", nombre or "")
    nombre = re.sub(r"\s+", " ", nombre).strip()
    return nombre[:110] or "sin-titulo"


def paginas(ruta):
    try:
        import fitz
        with fitz.open(ruta) as d:
            return d.page_count
    except Exception:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lista", required=True)
    ap.add_argument("--destino", required=True)
    ap.add_argument("--base", default="https://www.oecd.org")
    ap.add_argument("--pausa", type=float, default=0.5)
    args = ap.parse_args()

    os.makedirs(args.destino, exist_ok=True)
    pares = []
    with open(args.lista, encoding="utf-8") as f:
        for linea in f:
            if not linea.strip():
                continue
            partes = linea.rstrip("\n").split("\t")
            if len(partes) >= 2:
                pares.append((partes[0].strip(), partes[1].strip()))

    filas, fallos = [], []
    for i, (titulo, url) in enumerate(pares, start=1):
        if url.startswith("/"):
            url = args.base + url
        destino = os.path.join(args.destino, limpiar(titulo) + ".pdf")
        if os.path.exists(destino) and os.path.getsize(destino) > 1000:
            print(f"[{i:>2}/{len(pares)}] ya estaba  {titulo[:58]}")
            filas.append({"titulo": titulo, "paginas": paginas(destino),
                          "kb": os.path.getsize(destino) // 1024,
                          "archivo": os.path.basename(destino), "url": url})
            continue
        try:
            datos = bajar(url)
        except Exception as e:
            print(f"[{i:>2}/{len(pares)}] FALLO  {titulo[:50]}  {e}")
            fallos.append((titulo, str(e)))
            continue
        if not datos.startswith(b"%PDF"):
            print(f"[{i:>2}/{len(pares)}] no es PDF  {titulo[:50]}")
            fallos.append((titulo, "la respuesta no es un PDF"))
            continue
        with open(destino, "wb") as f:
            f.write(datos)
        p = paginas(destino)
        filas.append({"titulo": titulo, "paginas": p, "kb": len(datos) // 1024,
                      "archivo": os.path.basename(destino), "url": url})
        print(f"[{i:>2}/{len(pares)}] ok {len(datos)//1024:>6} KB  {str(p):>4} p  {titulo[:52]}")
        time.sleep(args.pausa)

    indice = os.path.join(args.destino, "_indice.csv")
    with open(indice, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["titulo", "paginas", "kb", "archivo", "url"])
        w.writeheader()
        w.writerows(filas)

    cortos = [r for r in filas if isinstance(r["paginas"], int) and r["paginas"] <= 20]
    largos = [r for r in filas if isinstance(r["paginas"], int) and r["paginas"] > 20]
    print("\n" + "=" * 64)
    print(f"  Descargados        {len(filas):>3} de {len(pares)}")
    print(f"  Fallidos           {len(fallos):>3}")
    print(f"  Peso total      {sum(r['kb'] for r in filas)/1024:>6.1f} MB")
    print(f"  Notas cortas (<=20 p)  {len(cortos):>3}")
    print(f"  Documentos largos      {len(largos):>3}")
    print("=" * 64)
    for t, c in fallos:
        print(f"  ! {t[:50]}  {c}")
    print(f"\nÍndice en {indice}")


if __name__ == "__main__":
    main()
