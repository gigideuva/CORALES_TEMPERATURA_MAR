"""Descarga UNA SOLA VEZ el contorno de Panamá desde geoBoundaries.

El contorno de un país no cambia, así que este script no forma parte de
ejecutar_todo.py: se corre una vez y el archivo queda guardado en datos/originales/.

Uso:  py -3.14 descargar_contorno.py
"""
import json
import os
import urllib.request

# Trabajar siempre desde la carpeta del proyecto (donde está este archivo)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

CARPETA = "datos/originales"
DESTINO = os.path.join(CARPETA, "panama_contorno.geojson")
DESTINO_INFO = os.path.join(CARPETA, "panama_contorno_info.json")

# API de geoBoundaries: PAN = Panamá, ADM0 = frontera del país completo
URL_API = "https://www.geoboundaries.org/api/current/gbOpen/PAN/ADM0/"

# 1. Pedimos la ficha del contorno: trae los enlaces de descarga y la licencia
with urllib.request.urlopen(URL_API, timeout=60) as respuesta:
    ficha = json.load(respuesta)

url_contorno = ficha["simplifiedGeometryGeoJSON"]   # versión simplificada: liviana y suficiente para un mapa
licencia = ficha.get("boundaryLicense", "")
print("Descargando:", url_contorno)
print("Licencia:", licencia)

# 2. Descargamos el GeoJSON a un archivo temporal y lo reemplazamos al final
temporal = DESTINO + ".tmp"
urllib.request.urlretrieve(url_contorno, temporal)
with open(temporal, encoding="utf-8") as archivo:
    json.load(archivo)                               # verificamos que sea un JSON válido
os.replace(temporal, DESTINO)

# 3. Guardamos la fuente y la licencia, para citarlas en el dashboard
with open(DESTINO_INFO, "w", encoding="utf-8") as archivo:
    json.dump({
        "fuente": "geoBoundaries (gbOpen, ADM0)",
        "licencia": licencia,
        "url_api": URL_API,
        "url_archivo": url_contorno,
    }, archivo, ensure_ascii=False, indent=2)

print("Contorno guardado en", DESTINO)
