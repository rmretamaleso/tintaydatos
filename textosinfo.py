"""
Descarga y parsea la versión /ebook de textos.info a un árbol para edicion.py.

Se usa /ebook y NO el PDF: el PDF del mismo sitio pierde los saltos de estrofa
(verso) y los límites de párrafo (prosa). Comprobado en Rimas y en Fortunata.

Uso típico:
    from textosinfo import descargar, inspeccionar, parsear
"""
import html as _html
import re
import sys
import unicodedata

ARTEFACTOS = [r"Arriba\s*Abajo\s*", r"\bArriba\b\s*$"]

# Pie del sitio: a partir de aquí ya no es texto de la obra.
FIN_CONTENIDO = [re.compile(p, re.I) for p in (
    r"^Publicado el .+ por ",
    r"^Leído .+ veces",
    r"^Biblioteca digital abierta",
    r"^Textos\.info es un proyecto",
    r"^Comparte tus lecturas",
)]


def descargar(url):
    try:
        import requests
    except ImportError:
        sys.exit("Falta requests:  pip install requests")
    r = requests.get(url, timeout=60, headers={"User-Agent": "TintaYDatos/1.0"})
    r.raise_for_status()
    if not r.encoding or r.encoding.lower() == "iso-8859-1":
        r.encoding = "utf-8"
    return r.text


def limpiar(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = _html.unescape(s).replace("\u00a0", " ").replace("\u200b", "")
    for pat in ARTEFACTOS:
        s = re.sub(pat, "", s)
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip()


def _cuerpo(doc):
    """Recorta cabecera y pie del sitio para no contarlos como contenido."""
    m = re.search(r"<(?:article|main)\b[^>]*>", doc, re.I)
    if m:
        doc = doc[m.end():]
        f = re.search(r"</(?:article|main)>", doc, re.I)
        if f:
            doc = doc[:f.start()]
    return doc


def elementos(doc):
    """Lista ordenada de ('h2'|'h3'|..|'p', texto) tal como aparecen."""
    out = []
    for m in re.finditer(r"<(h[1-6]|p)\b[^>]*>(.*?)</\1>", _cuerpo(doc), re.S | re.I):
        etiqueta = m.group(1).lower()
        crudo = m.group(2)
        if etiqueta == "p":
            lineas = [limpiar(x) for x in re.split(r"<br\s*/?>", crudo, flags=re.I)]
            lineas = [x for x in lineas if x]
            if not lineas:
                continue
            # Acotación de voz solo si TODO el párrafo va en negrita
            # (<p><strong>PRIMERA VOZ</strong></p>). Un término destacado dentro
            # de un texto —una entrada de glosario— no lo es.
            voz = bool(re.fullmatch(r"\s*<(strong|b)\b[^>]*>.*?</\1>\s*",
                                    crudo, re.S | re.I))
            out.append((etiqueta, lineas, voz))
        else:
            t = limpiar(crudo)
            if t:
                out.append((etiqueta, [t], False))
    return out


def inspeccionar(doc, muestras=4):
    """Reporta la estructura encontrada SIN generar nada. No asume nada."""
    els = elementos(doc)
    print(f"Elementos de contenido: {len(els)}\n")

    porniveles = {}
    for etiqueta, lineas, _ in els:
        porniveles.setdefault(etiqueta, []).append(lineas[0])

    print(f"{'ETIQUETA':<10}{'CANTIDAD':>10}   PRIMERAS APARICIONES")
    for etiqueta in sorted(porniveles):
        vals = porniveles[etiqueta]
        if etiqueta.startswith("h") and len(vals) <= 60:
            print(f"{etiqueta:<10}{len(vals):>10}")
            for i, v in enumerate(vals, 1):
                print(f"{'':<10}{i:>10}   {v}")
        else:
            ej = " | ".join(v[:44] for v in vals[:muestras])
            print(f"{etiqueta:<10}{len(vals):>10}   {ej}")

    parrafos = [l for e, l, _ in els if e == "p"]
    solonum = [l[0] for l in parrafos if re.fullmatch(r"[0-9]{1,4}", l[0])]
    romanos = [l[0] for l in parrafos if re.fullmatch(r"[IVXLCDM]{1,7}", l[0])]
    multilinea = [l for l in parrafos if len(l) > 1]
    print(f"\nPárrafos <p>:                  {len(parrafos)}")
    print(f"  con varias líneas (<br>):    {len(multilinea)}   -> verso probable si es alto")
    print(f"  que son solo un número:      {len(solonum)}   -> secciones numeradas")
    print(f"  que son solo un romano:      {len(romanos)}")
    if solonum:
        print(f"    ejemplos: {', '.join(solonum[:12])}")

    art = [l[0] for e, l, _ in els for pat in ARTEFACTOS if re.search(pat, l[0])]
    if art:
        print(f"\nATENCIÓN: restos de navegación en {len(art)} elementos, ej.: «{art[0][:60]}»")

    print("\nPega esta salida para fijar la configuración de la obra.")
    return els


def parsear(doc, cfg):
    """
    cfg admite:
      tipo             'verso' | 'prosa'
      nivel_parte      'h2' o None
      nivel_capitulo   'h3'  (o 'h2' si no hay partes)
      patron_capitulo  regex con 1 o 2 grupos: (numero) y (titulo opcional)
      nivel_seccion    'h4', o una lista ['h3','h4'] si hay varios niveles
      preliminares     título para el texto previo al primer capítulo, o True
                       para incluirlo sin encabezado
      patron_seccion   regex con 1 grupo para extraer el número de la sección
      seccion_numerica True si un <p> que es solo un número abre sección
      esperados        dict opcional: {'partes':4,'capitulos':31,'secciones':201}
    """
    tipo = cfg.get("tipo", "prosa")
    n_parte = cfg.get("nivel_parte")
    n_cap = cfg.get("nivel_capitulo", "h2")
    pat = re.compile(cfg["patron_capitulo"]) if cfg.get("patron_capitulo") else None
    secnum = cfg.get("seccion_numerica", False)
    n_sec = cfg.get("nivel_seccion")
    niveles_sec = ([n_sec] if isinstance(n_sec, str) else list(n_sec or []))

    partes, cap, sec = [], None, None

    def nueva_parte(nombre):
        partes.append({"nombre": nombre, "capitulos": []})

    def nueva_seccion(numero):
        nonlocal sec
        sec = {"numero": numero, "bloques": []}
        cap["secciones"].append(sec)

    # El nombre del autor puede venir marcado como encabezado de portada dentro
    # del contenido. El título NO se descarta: hay obras cuya primera sección se
    # llama igual que el libro (Azul, El dulce daño).
    ignorar_autor = {str(cfg.get("autor", "")).strip().lower()} - {""}

    ignorados = {}
    preliminares = []

    for etiqueta, lineas, voz in elementos(doc):
        texto = lineas[0]

        if etiqueta == "p" and any(rx.match(texto) for rx in FIN_CONTENIDO):
            break                      # empezó el pie del sitio

        if etiqueta.startswith("h") and texto.strip().lower() in ignorar_autor:
            continue                   # portada, no capítulo

        if n_parte and etiqueta == n_parte:
            nueva_parte(texto); cap = sec = None
            continue

        if etiqueta == n_cap:
            numero, titulo = texto, None
            if pat:
                m = pat.match(texto)
                if m:
                    numero = m.group(1)
                    titulo = m.group(2).strip() if m.lastindex and m.lastindex >= 2 else None
            if not partes:
                nueva_parte(None)
            cap = {"numero": numero, "titulo": titulo or None, "secciones": []}
            partes[-1]["capitulos"].append(cap)
            sec = None
            continue

        if etiqueta in niveles_sec and cap is not None:
            m = re.match(cfg.get("patron_seccion", r"^\s*(\S+)"), texto)
            nueva_seccion(m.group(1) if m else texto)
            continue

        if etiqueta == "p" and cap is None:
            if partes:
                # Una parte con texto propio y sin capítulos (prólogos, declaraciones
                # al lector) necesita un capítulo implícito que lo sostenga.
                cap = {"numero": None, "titulo": None, "secciones": []}
                partes[-1]["capitulos"].append(cap)
                nueva_seccion(None)
                sec["bloques"].append(lineas if len(lineas) > 1 or tipo == "verso"
                                      else lineas[0])
                continue
            # Antes de cualquier parte: dedicatorias, prólogos, advertencias
            preliminares.append(lineas if len(lineas) > 1 else lineas[0])
            continue

        if etiqueta != "p" or cap is None:
            if etiqueta != "p":
                ignorados.setdefault(etiqueta, []).append(texto)
            continue

        if secnum and len(lineas) == 1 and re.fullmatch(r"[0-9]{1,4}", texto):
            nueva_seccion(texto)
            continue

        if sec is None:
            nueva_seccion(None)

        if tipo == "verso":
            sec["bloques"].append([">> " + lineas[0]] if (voz and len(lineas) == 1)
                                  else lineas)
        else:
            # varias líneas en prosa = cita en verso o dedicatoria: no unir
            sec["bloques"].append(lineas if len(lineas) > 1 else lineas[0])

    if preliminares:
        titulo_prel = cfg.get("preliminares")
        if titulo_prel:
            # True significa "incluirlos sin encabezado propio"
            numero_prel = None if titulo_prel is True else titulo_prel
            if not partes:
                partes.append({"nombre": None, "capitulos": []})
            partes[0]["capitulos"].insert(0, {
                "numero": numero_prel, "titulo": None,
                "secciones": [{"numero": None, "bloques": preliminares}]})
        else:
            print(f"AVISO: {len(preliminares)} párrafo(s) antes del primer capítulo "
                  f"se están descartando.")
            print(f"       Si son dedicatoria, prólogo o advertencia, añade al .json "
                  f"\"preliminares\": \"Dedicatoria\" (o el título que corresponda).")
            for b in preliminares[:3]:
                muestra = " / ".join(b) if isinstance(b, list) else b
                print(f"       «{muestra[:70]}»")

    if ignorados:
        print("AVISO: encabezados descartados por no estar declarados en el .json.")
        print("       Si son parte de la obra, se están perdiendo sin que la "
              "verificación lo note.")
        for tag, textos in sorted(ignorados.items()):
            muestra = " | ".join(t[:40] for t in textos[:5])
            print(f"       <{tag}> x{len(textos)}: {muestra}"
                  + (" …" if len(textos) > 5 else ""))

    renombrar = cfg.get("renombrar_capitulos") or {}
    if renombrar:
        vistos = {c["numero"] for p in partes for c in p["capitulos"]}
        sobran = [k for k in renombrar if k not in vistos]
        if sobran:
            sys.exit(f"'renombrar_capitulos' menciona títulos que no existen "
                     f"en la fuente: {sobran}")
        for p in partes:
            for c in p["capitulos"]:
                c["numero"] = renombrar.get(c["numero"], c["numero"])

    renombrar_sec = cfg.get("renombrar_secciones") or {}
    if renombrar_sec:
        vistas = {s["numero"] for p in partes for c in p["capitulos"]
                  for s in c["secciones"] if s["numero"] is not None}
        sobran = [k for k in renombrar_sec if k not in vistas]
        if sobran:
            sys.exit(f"'renombrar_secciones' menciona secciones que no existen "
                     f"en la fuente: {sobran}")
        for p in partes:
            for c in p["capitulos"]:
                for s in c["secciones"]:
                    if s["numero"] in renombrar_sec:
                        s["numero"] = renombrar_sec[s["numero"]]

    orden = cfg.get("orden_capitulos")
    if orden:
        if len(partes) != 1:
            sys.exit("'orden_capitulos' solo aplica a obras sin partes.")
        caps = {c["numero"]: c for c in partes[0]["capitulos"]}
        faltan = [t for t in orden if t not in caps]
        sobran = [t for t in caps if t not in orden]
        if faltan or sobran:
            sys.exit("'orden_capitulos' no coincide con lo encontrado.\n"
                     + (f"  no están en la fuente: {faltan}\n" if faltan else "")
                     + (f"  están y no los listaste: {sobran}\n" if sobran else ""))
        partes[0]["capitulos"] = [caps[t] for t in orden]

    obtenidos = {
        "partes": len([p for p in partes if p.get("nombre")]),
        # Solo los que tienen encabezado propio, para que el número coincida
        # con lo que muestra --inspeccionar. Los implícitos no se cuentan.
        "capitulos": sum(1 for p in partes for c in p["capitulos"]
                         if c["numero"] is not None),
        "secciones": sum(len(c["secciones"]) for p in partes for c in p["capitulos"]),
    }
    esp = cfg.get("esperados") or {}
    fallos = [f"{k}: esperaba {v}, encontré {obtenidos[k]}"
              for k, v in esp.items() if obtenidos.get(k) != v]
    if fallos:
        sys.exit("La estructura no coincide con lo esperado:\n  " + "\n  ".join(fallos)
                 + "\nAborto para no generar una edición incompleta.")
    return partes, obtenidos
