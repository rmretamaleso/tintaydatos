#!/usr/bin/env python3
"""Genera las primeras ediciones propias del dominio Ciencia.

Hasta ahora Ciencia solo tenía enlaces. Estas ocho son obras completas
tipografiadas por Tinta y Datos, con tema asignado para que la navegación
Ciencia -> tema -> autor funcione desde el primer día.
"""
import json, pathlib

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
OBRAS = [
 # id, archivo, título, autor, país, año, tema, nota
 (66373,"rc-reglasconsejos","Reglas y Consejos sobre Investigación Científica",
  "Santiago Ramón y Cajal","España",1898,"Metodología científica",
  "Lección inaugural del curso 1897-98, ampliada después en libro; sigue siendo "
  "lectura habitual en la formación de investigadores."),
 (58331,"rc-recuerdosi","Recuerdos de mi Vida, tomo I",
  "Santiago Ramón y Cajal","España",1901,"Neurociencia",None),
 (60675,"rc-recuerdosii","Recuerdos de mi Vida, tomo II",
  "Santiago Ramón y Cajal","España",1917,"Neurociencia",
  "El segundo tomo relata la investigación que le valió el Nobel de Medicina "
  "en 1906, compartido con Camillo Golgi."),
 (25255,"cl-cronicaperu","Segunda Parte de la Crónica del Perú",
  "Pedro Cieza de León","Perú",1553,"Etnografía",
  "Describe la organización del imperio incaico a partir de informantes "
  "indígenas, pocos años después de la conquista."),
 (59539,"dl-yucatan","Relación de las Cosas de Yucatán",
  "Diego de Landa","México",1566,"Etnografía",
  "Fuente principal sobre la escritura y la religión mayas, escrita por el "
  "mismo fraile que ordenó destruir los códices de Maní en 1562."),
 (30052,"fm-catamarca","Exploración Arqueológica de la Provincia de Catamarca",
  "Francisco Pascasio Moreno","Argentina",1890,"Arqueología",None),
 (13479,"ao-bolivia","Descripción Geográfica, Histórica y Estadística de Bolivia",
  "Alcide d'Orbigny","Bolivia",1845,"Geografía",None),
 (28542,"tf-patagonia","Descripción de la Patagonia y de las Partes Adyacentes",
  "Thomas Falkner","Argentina",1774,"Geografía",
  "Escrita por un jesuita inglés tras casi cuarenta años entre los pueblos "
  "de la Patagonia; fue durante décadas la principal fuente europea sobre la región."),
]
cid = 967
for libro, archivo, titulo, autor, pais, anio, tema, nota in OBRAS:
    fuente = {}
    if nota:
        fuente["nota"] = nota
    c = {"slug": archivo.split("-",1)[1], "titulo": titulo, "autor": autor,
         "anio": anio, "tipo": "prosa", "gutenberg": libro, "catalogo": CAT,
         "fuente": fuente, "catalogo_id": cid,
         "catalogo_campos": {"dominio":"Ciencia","titulo":titulo,"autor":autor,
            "anio":str(anio),"pais":pais,"genero":tema,"tema":tema,
            "tipo":"Dominio público","puede_alojarse":"si"},
         "nivel_capitulo":"h2",
         "opciones":{"salto_por_capitulo":True,"hyphenation":"es"}}
    pathlib.Path(f"obras/{archivo}.json").write_text(
        json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"  {archivo+'.json':<24} {titulo[:40]:<42} {tema:<24} {pais}")
    cid += 1
print(f"\n{len(OBRAS)} configuraciones, ids 967-{cid-1}")
