#!/usr/bin/env python3
"""
corregir_dominio_publico.py — cuatro arreglos en dominio_publico.py.

  1. PAIS_A_ISO       falta «El Salvador», aunque SV sí está en PAISES: hoy la
                      nacionalidad de ese autor no se resuelve y el cotejo de
                      plazos no llega a aplicarse
  2. PAISES           añade Guatemala (75 años, Decreto 33-98 art. 43). Estaba
                      en PAIS_A_ISO apuntando a una entrada inexistente
  3. estado_en_pais   el plazo del país de ORIGEN también puede estar ampliado
                      por una transitoria. Para un autor español fallecido
                      antes de 1988 el plazo en España es 80, no 70; leer 70
                      sub-protege en Colombia, que tiene 80 y aplica el cotejo
  4. documentación    deja por escrito por qué los países fuera de la tabla no
                      se bloquean. Hoy es una asunción implícita en el código

Uso:
    python3 corregir_dominio_publico.py              # simula
    python3 corregir_dominio_publico.py --aplicar
"""
import os
import shutil
import sys

APLICAR = "--aplicar" in sys.argv
RUTA = "dominio_publico.py"
hechos, fallos = [], []


def editar(viejo, nuevo, etiqueta, marca):
    global contenido
    if marca in contenido:
        hechos.append(f"{etiqueta}: ya estaba aplicado")
        return
    if viejo not in contenido:
        fallos.append(f"{etiqueta}: no encontré el código esperado")
        return
    contenido = contenido.replace(viejo, nuevo, 1)
    hechos.append(f"{etiqueta}: {'aplicado' if APLICAR else 'listo para aplicar'}")


if not os.path.exists(RUTA):
    sys.exit(f"No existe {RUTA}. Ejecútalo desde la carpeta del proyecto.")
contenido = open(RUTA, encoding="utf-8").read()

# ---------------------------------------------------------------- 1
editar(
    '''    "Guatemala": "GT", "Paraguay": "PY", "Reino Unido": "GB", "Francia": "FR",''',
    '''    "Guatemala": "GT", "Paraguay": "PY", "Reino Unido": "GB", "Francia": "FR",
    "El Salvador": "SV",''',
    "1 mapeo de El Salvador", marca='"El Salvador": "SV"')

# ---------------------------------------------------------------- 2
editar(
    '''    "FR": {"nombre": "Francia",       "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta",  "fuente": "verificado con la calculadora del Cerlalc (2026)"},
}''',
    '''    "FR": {"nombre": "Francia",       "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta",  "fuente": "verificado con la calculadora del Cerlalc (2026)"},

    # corto=True no es una comodidad: el art. 7.8 de Berna establece el cotejo
    # de plazos como regla por defecto y solo decae si la legislación nacional
    # dispone otra cosa. Sin constancia de que Guatemala se haya apartado, se
    # aplica. PENDIENTE de pasar por la calculadora del Cerlalc.
    "GT": {"nombre": "Guatemala",     "plazo": 75,  "corto": True,  "trans80": False,
           "confianza": "media", "fuente": "Decreto 33-98, Ley de Derecho de Autor y Derechos Conexos, art. 43: 75 años post mortem. Falta confirmar con la calculadora del Cerlalc y comprobar si aplica el cotejo de plazos"},
}''',
    "2 entrada de Guatemala", marca='"GT": {"nombre": "Guatemala"')

# ---------------------------------------------------------------- 3
editar(
    '''        origen = PAISES.get(nac_autor)
        if origen and origen["plazo"]:
            plazo = min(plazo, origen["plazo"])''',
    '''        origen = PAISES.get(nac_autor)
        if origen and origen["plazo"]:
            # El plazo del país de origen también puede estar ampliado por una
            # transitoria. Un autor español fallecido antes de 1988 tiene 80
            # años en España: leer 70 daría min(80,70)=70 en Colombia, que
            # tiene 80 y aplica el cotejo, y la dejaría libre diez años antes.
            plazo_origen = origen["plazo"]
            if origen["trans80"] and anio_muerte < 1988:
                plazo_origen = 80
            plazo = min(plazo, plazo_origen)''',
    "3 transitoria en el país de origen", marca="plazo_origen")

# ---------------------------------------------------------------- 4
editar(
    "PAISES = {",
    '''# Por qué esta tabla no cubre el mundo entero
# ------------------------------------------------------------------
# Lo que no está aquí no se evalúa, no entra en el manifiesto y el Worker lo
# sirve. Eso descansa en el art. 7.8 del Convenio de Berna: salvo que la
# legislación nacional disponga otra cosa, la protección en el país donde se
# reclama no excede del plazo del país de origen. Como todas las obras del
# catálogo están en dominio público en su país de origen, en cualquier país
# que aplique ese cotejo también lo están, y no hay derecho que infringir.
#
# Solo necesitan evaluación los países que rompen esa regla:
#   - los que renuncian expresamente al cotejo  -> México (corto=False)
#   - los que usan otro sistema de cómputo      -> EE. UU. y Puerto Rico,
#     que cuentan desde la publicación y restauraron derechos extranjeros
#     mediante la URAA (plazo=None)
#
# Añadir aquí un país con corto=True no cambia ningún veredicto: min(local,
# origen) acaba siendo el plazo de origen, que es el que ya hace libre la
# obra. Por eso la tabla crece solo con países de origen del catálogo y con
# cualquier jurisdicción de la que se descubra que no aplica el cotejo.
#
# Revisados y descartados por aplicar el cotejo: Costa de Marfil (99 años) y
# Jamaica (95). Pendiente de confirmar: Guatemala y Guinea Ecuatorial.

PAISES = {''',
    "4 documentación del comportamiento por defecto",
    marca="Por qué esta tabla no cubre el mundo entero")

# ---------------------------------------------------------------- informe
print("CAMBIOS")
for h in hechos:
    print("  ok   ", h)
for f in fallos:
    print("  FALLA", f)
print()

if fallos:
    print("No escribo nada: revisa esas partes a mano.")
    sys.exit(1)

if APLICAR:
    shutil.copy(RUTA, RUTA + ".bak")
    open(RUTA, "w", encoding="utf-8").write(contenido)
    print(f"Escrito {RUTA} (copia previa en {RUTA}.bak)")
else:
    print("Simulación. Añade --aplicar para escribir.")
