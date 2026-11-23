"""Gráfica de lenguajes del perfil, contando también los repos privados.

Solo lee (token fine-grained: Contents y Metadata en solo lectura) y solo publica
porcentajes: ni nombres de repos ni código. Biblioteca estándar, sin dependencias.
Uso: METRICS_TOKEN=... python3 lenguajes.py > lenguajes.svg
"""
import json
import os
import sys
import urllib.request
from xml.sax.saxutils import escape

API = "https://api.github.com"
COLORES = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#2ec4b6", "HTML": "#e34c26",
    "CSS": "#663399", "Shell": "#89e051", "PowerShell": "#012456", "SQL": "#e38c00",
    "PLpgSQL": "#336790", "Vue": "#41b883", "Kotlin": "#A97BFF", "Swift": "#F05138",
    "Go": "#00ADD8", "Rust": "#dea584", "Dockerfile": "#384d54", "Astro": "#ff5a03",
    "MDX": "#fcb32c", "Svelte": "#ff3e00", "Java": "#b07219", "C#": "#178600",
}
OTROS = "#6e7681"
MAX = 7


def pide(ruta):
    req = urllib.request.Request(API + ruta, headers={
        "Authorization": "Bearer " + os.environ["METRICS_TOKEN"],
        "Accept": "application/vnd.github+json", "User-Agent": "perfil-lenguajes"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def repos():
    pagina = 1
    while True:
        lote = pide(f"/user/repos?affiliation=owner&per_page=100&page={pagina}")
        if not lote:
            return
        yield from lote
        pagina += 1


def main():
    total = {}
    for r in repos():
        if r.get("fork"):
            continue
        for lang, n in pide(f"/repos/{r['full_name']}/languages").items():
            total[lang] = total.get(lang, 0) + n
    suma = sum(total.values())
    if not suma:
        sys.exit("No hay lenguajes que contar: no escribo nada.")
    orden = sorted(total.items(), key=lambda x: -x[1])
    filas = [(l, n / suma) for l, n in orden[:MAX]]
    resto = 1 - sum(p for _, p in filas)
    if resto >= 0.005:
        filas.append(("Otros", resto))

    ancho, x0, y_barra = 480, 25, 58
    partes, x = [], x0
    util = ancho - 2 * x0
    for l, p in filas:
        w = max(util * p, 1)
        partes.append(f'<rect x="{x:.1f}" y="{y_barra}" width="{w:.1f}" height="10" fill="{COLORES.get(l, OTROS)}"/>')
        x += w
    leyenda = []
    for i, (l, p) in enumerate(filas):
        cx, cy = x0 + (i % 2) * 220, 98 + (i // 2) * 26
        leyenda.append(
            f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{COLORES.get(l, OTROS)}"/>'
            f'<text x="{cx + 18}" y="{cy}" class="l">{escape(l)}</text>'
            f'<text x="{cx + 200}" y="{cy}" class="p" text-anchor="end">{p * 100:.1f} %</text>')
    alto = 98 + ((len(filas) + 1) // 2) * 26
    print(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}" role="img" aria-label="Lenguajes más usados">
<style>.t{{font:600 16px -apple-system,Segoe UI,Helvetica,Arial,sans-serif;fill:#2F6BFF}}.s{{font:12px -apple-system,Segoe UI,Helvetica,Arial,sans-serif;fill:#8b949e}}.l{{font:13px -apple-system,Segoe UI,Helvetica,Arial,sans-serif;fill:#e6edf3}}.p{{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;fill:#8b949e}}</style>
<rect x="0.5" y="0.5" width="{ancho - 1}" height="{alto - 1}" rx="8" fill="#0d1117" stroke="#30363d"/>
<text x="{x0}" y="32" class="t">Lenguajes más usados</text>
<text x="{ancho - x0}" y="32" class="s" text-anchor="end">repos públicos y privados</text>
<clipPath id="b"><rect x="{x0}" y="{y_barra}" width="{util}" height="10" rx="5"/></clipPath>
<g clip-path="url(#b)">{"".join(partes)}</g>
{"".join(leyenda)}
</svg>''')


if __name__ == "__main__":
    main()
