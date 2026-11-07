import os
import socket
import time
import urllib.request
from datetime import datetime

# Trabajar siempre desde la carpeta del proyecto (donde está este archivo)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Carpeta donde se guardan los datos originales
CARPETA = "datos/originales"

# Si el servidor de NOAA no responde en 60 segundos, se corta el intento (en vez de quedarse colgado)
socket.setdefaulttimeout(60)

# Cuántas veces se intenta cada descarga y cuántos segundos se espera entre intentos
INTENTOS = 3
ESPERA_SEGUNDOS = 20

# Las 4 estaciones virtuales de NOAA Coral Reef Watch
estaciones = [
    "panama_atlantic_east",
    "panama_atlantic_west",
    "panama_pacific_east",
    "panama_pacific_west",
]

print("Descarga iniciada:", datetime.now().strftime("%d/%m/%Y %H:%M"))

for estacion in estaciones:
    url = f"https://coralreefwatch.noaa.gov/product/vs/data/{estacion}.txt"
    destino = os.path.join(CARPETA, f"{estacion}.txt")
    temporal = destino + ".tmp"

    for intento in range(1, INTENTOS + 1):
        try:
            urllib.request.urlretrieve(url, temporal)
            os.replace(temporal, destino)
            print("  Descargado:", estacion)
            break   # salió bien: pasamos a la siguiente estación
        except Exception as error:
            print(f"  Intento {intento} de {INTENTOS} falló para {estacion} -> {error}")
            if os.path.exists(temporal):
                os.remove(temporal)
            if intento < INTENTOS:
                time.sleep(ESPERA_SEGUNDOS)
            else:
                # Se conserva el archivo anterior: el análisis sigue con los datos que ya había
                print("  No se pudo descargar", estacion, "- se usa el archivo anterior")

print("Descarga terminada")
