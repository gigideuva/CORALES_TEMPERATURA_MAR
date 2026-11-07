import os
import subprocess
import sys
from datetime import datetime

# Trabajar siempre desde la carpeta del proyecto (donde está este archivo)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=== Actualización iniciada:", datetime.now().strftime("%d/%m/%Y %H:%M"))

pasos = [
    [sys.executable, "descargar_temperatura.py"],
    [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute",
     "--inplace", "notebooks/2_limpieza_temperatura.ipynb"],
    [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute",
     "--inplace", "notebooks/3_analisis.ipynb"],
    [sys.executable, "generar_dashboard.py"],
]

for paso in pasos:
    print("\n>> Ejecutando:", paso[-1])
    resultado = subprocess.run(paso)
    if resultado.returncode != 0:
        print("Hubo un error en", paso[-1], "- se detiene la actualización")
        sys.exit(1)

print("\n=== Todo actualizado:", datetime.now().strftime("%d/%m/%Y %H:%M"))
