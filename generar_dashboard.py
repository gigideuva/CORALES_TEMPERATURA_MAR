"""Script para generar el dashboard web interactivo del proyecto Corales de Panamá.

Lee los datos limpios en formato CSV, calcula dinámicamente todos los indicadores
estadísticos, genera las visualizaciones en formato SVG usando matplotlib (Agg)
e incrusta las imágenes codificadas en Base64 dentro de un único archivo HTML
autónomo (dashboard/index.html) sin dependencias externas de JavaScript ni servidor.
Funciona 100% sin conexión a internet utilizando CSS embebido e íconos SVG incrustados.
"""

import base64
from datetime import datetime
import io
import json
import os
from pathlib import Path
import re
import sys

# Configurar salida de consola a UTF-8 para caracteres especiales y flechas en Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Configurar matplotlib en backend no interactivo antes de importar pyplot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch, Polygon
import pandas as pd

# Asegurar que el directorio de trabajo sea la raíz del proyecto
DIRECTORIO_RAIZ = Path(__file__).resolve().parent
os.chdir(DIRECTORIO_RAIZ)

# Nombres de meses en español para formatear fechas
MESES_ESPANOL = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

# Escala de alerta de blanqueamiento de NOAA (0 al 7) según contenido.md
ESCALA_ALERTAS = {
    0: {"nombre": "Sin estrés", "color": "#1FA7A6"},
    1: {"nombre": "Vigilancia", "color": "#FFC857"},
    2: {"nombre": "Advertencia", "color": "#FF8A5B"},
    3: {"nombre": "Blanqueamiento probable", "color": "#E75480"},
    4: {"nombre": "Mortalidad probable", "color": "#6C2E7B"},
    5: {"nombre": "Mortalidad de varias especies", "color": "#4A1F5C"},
    6: {"nombre": "Mortalidad severa", "color": "#2A0A4A"},
    7: {"nombre": "Mortalidad casi total", "color": "#000000"},
}

# Nombre que usa NOAA en su página para cada nivel de la escala 0 a 7
NOMBRES_NOAA = {
    0: "No Stress",
    1: "Bleaching Watch",
    2: "Bleaching Warning",
    3: "Alert Level 1",
    4: "Alert Level 2",
    5: "Alert Level 3",
    6: "Alert Level 4",
    7: "Alert Level 5",
}

# Zona de Panamá que cubre cada estación virtual
ZONAS_ESTACIONES = {
    "panama_atlantic_east": "Guna Yala",
    "panama_atlantic_west": "Bocas del Toro",
    "panama_pacific_east": "golfo de Panamá",
    "panama_pacific_west": "golfo de Chiriquí",
}

# Nombre legible de cada estación virtual
NOMBRES_ESTACIONES = {
    "panama_atlantic_east": "Atlantic East",
    "panama_atlantic_west": "Atlantic West",
    "panama_pacific_east": "Pacific East",
    "panama_pacific_west": "Pacific West",
}

# Diccionario de íconos vectoriales SVG incrustados (funciona offline sin librerías externas)
ICONOS_SVG = {
    "waves": '<svg class="icon-svg" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/></svg>',
    "tsunami": '<svg class="icon-svg" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 20c2-2 3-3 5-3s3 1 5 1 3-2 5-2 3 2 5 2"/><path d="M2 15c2-2 3-3 5-3s3 1 5 1 3-2 5-2 3 2 5 2"/><path d="M2 10c2-3 4-5 7-5 4 0 5 4 8 4 3 0 3-2 5-2"/></svg>',
    "arrow_down": '<svg class="icon-svg" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>',
    "sensors": '<svg class="icon-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12a10 10 0 0 1 20 0"/><path d="M6 12a6 6 0 0 1 12 0"/><circle cx="12" cy="12" r="2" fill="currentColor"/></svg>',
    "bubble_chart": '<svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="7.5" r="2.5"/><circle cx="6.5" cy="8.5" r="2"/><circle cx="7" cy="16.5" r="2.5"/><circle cx="16.5" cy="16.5" r="2"/></svg>',
    "spa": '<svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v8"/><path d="M12 12c2-1 3-2 4-2"/></svg>',
    "foundation": '<svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"/><path d="M5 21V9l7-5 7 5v12"/><path d="M9 21v-6h6v6"/></svg>',
    "wb_sunny": '<svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
    "arrow_downward": '<svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>',
    "water_loss": '<svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/><path d="M12 11v6"/></svg>',
    "thermostat": '<svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>',
    "local_fire_department": '<svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>',
    "warning": '<svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "cyclone": '<svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 2a10 10 0 0 1 8.66 15L12 12"/><path d="M12 22a10 10 0 0 1-8.66-15L12 12"/></svg>',
    "satellite_alt": '<svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 10.5L9 6l4.5 4.5-4.5 4.5z"/><path d="M14.5 15.5l3-3"/><path d="M17.5 18.5l3-3"/><path d="M9 15l-4 4"/></svg>',
    "dataset": '<svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    "help": '<svg class="icon-svg" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "tune": '<svg class="icon-svg" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>',
    "info": '<svg class="icon-svg" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    "menu_book": '<svg class="icon-svg" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>',
}


def formatear_fecha_espanol(fecha_dt, incluir_hora=False):
    """Formatea un objeto datetime o fecha a texto en español."""
    dia = fecha_dt.day
    mes = MESES_ESPANOL[fecha_dt.month]
    anio = fecha_dt.year
    if incluir_hora:
        return f"{dia} de {mes} de {anio}, {fecha_dt.strftime('%H:%M')}"
    return f"{dia} de {mes} de {anio}"


def obtener_ruta_recurso(nombre_archivo):
    """Busca un archivo de recurso en las posibles carpetas de diseño del proyecto."""
    posibles_carpetas = [
        DIRECTORIO_RAIZ / "imagenes",
        DIRECTORIO_RAIZ / "Diseño",
        DIRECTORIO_RAIZ / "dashboard" / "stitch_panam_coral_watch_dashboard",
        DIRECTORIO_RAIZ / "dashboard",
        DIRECTORIO_RAIZ,
    ]
    variaciones = [nombre_archivo, nombre_archivo.replace(" ", "_"), nombre_archivo.replace("_", " ")]
    for carpeta in posibles_carpetas:
        for var in variaciones:
            candidato = carpeta / var
            if candidato.exists():
                return candidato
    return None


def codificar_imagen_base64(nombre_archivo):
    """Carga una imagen y retorna su representación como Data URI en Base64."""
    ruta = obtener_ruta_recurso(nombre_archivo)
    if not ruta or not ruta.exists():
        print(f"Advertencia: No se encontró la imagen '{nombre_archivo}'", file=sys.stderr)
        return ""
    extension = ruta.suffix.lower()
    tipo_mime = "image/png" if extension == ".png" else "image/jpeg"
    with open(ruta, "rb") as archivo:
        datos_base64 = base64.b64encode(archivo.read()).decode("utf-8")
    return f"data:{tipo_mime};base64,{datos_base64}"


def limpiar_svg(figura):
    """Convierte una figura de matplotlib a código SVG limpio y responsivo para incrustar."""
    buffer = io.StringIO()
    figura.savefig(buffer, format="svg", bbox_inches="tight", transparent=True)
    plt.close(figura)
    contenido = buffer.getvalue()
    coincidencia = re.search(r"<svg[^>]*>.*?</svg>", contenido, re.DOTALL)
    if not coincidencia:
        return ""
    svg_limpio = coincidencia.group(0)
    svg_limpio = re.sub(r'width="[^"]+"', 'width="100%"', svg_limpio, count=1)
    svg_limpio = re.sub(r'height="[^"]+"', 'height="auto"', svg_limpio, count=1)
    svg_limpio = svg_limpio.replace(
        "<svg ", '<svg style="max-width: 100%; height: auto; display: block;" '
    )
    return svg_limpio


def leer_contorno_panama():
    """Lee el contorno de Panamá (GeoJSON de geoBoundaries) si fue descargado con descargar_contorno.py.
    Devuelve una lista de anillos de coordenadas [(lon, lat), ...] o una lista vacía si no existe."""
    ruta = DIRECTORIO_RAIZ / "datos" / "originales" / "panama_contorno.geojson"
    if not ruta.exists():
        return []
    try:
        with open(ruta, encoding="utf-8") as archivo:
            geo = json.load(archivo)
        anillos = []
        # El archivo puede traer una FeatureCollection, un Feature o solo la geometría
        if geo.get("type") == "FeatureCollection":
            geometrias = [f["geometry"] for f in geo["features"]]
        elif geo.get("type") == "Feature":
            geometrias = [geo["geometry"]]
        else:
            geometrias = [geo]
        for geom in geometrias:
            if geom["type"] == "Polygon":
                anillos.append(geom["coordinates"][0])          # solo el borde exterior
            elif geom["type"] == "MultiPolygon":
                for poligono in geom["coordinates"]:            # tierra firme e islas
                    anillos.append(poligono[0])
        return anillos
    except Exception as error:
        print("Aviso: no se pudo leer el contorno de Panamá ->", error)
        return []


def leer_fuente_contorno():
    """Devuelve el texto de la fuente del contorno (con su licencia), o None si no hay contorno."""
    ruta_info = DIRECTORIO_RAIZ / "datos" / "originales" / "panama_contorno_info.json"
    if not (DIRECTORIO_RAIZ / "datos" / "originales" / "panama_contorno.geojson").exists():
        return None
    licencia = ""
    if ruta_info.exists():
        try:
            with open(ruta_info, encoding="utf-8") as archivo:
                info = json.load(archivo)
            licencia = info.get("licencia", "")
        except Exception:
            licencia = ""
    texto = "Contorno de Panamá: geoBoundaries (gbOpen, ADM0)"
    if licencia:
        texto += f", licencia {licencia}"
    return texto + "."


def calcular_frase_nivel7(df_temperatura):
    """Busca en los datos la primera vez que una costa llegó al nivel 7 y arma la frase del Hallazgo 2.
    Devuelve texto vacío si el nivel 7 nunca se alcanzó."""
    dias_nivel7 = df_temperatura[df_temperatura["alerta"] == 7].copy()
    if dias_nivel7.empty:
        return ""
    dias_nivel7["fecha_dt"] = pd.to_datetime(dias_nivel7["fecha"])
    primer_anio = dias_nivel7["fecha_dt"].dt.year.min()
    del_anio = dias_nivel7[dias_nivel7["fecha_dt"].dt.year == primer_anio]
    costa = del_anio.iloc[0]["costa_norm"]
    partes = []
    for estacion, grupo in del_anio.groupby("estacion"):
        inicio = MESES_ESPANOL[grupo["fecha_dt"].min().month]
        fin = MESES_ESPANOL[grupo["fecha_dt"].max().month]
        periodo = f"en {inicio}" if inicio == fin else f"entre {inicio} y {fin}"
        nombre = NOMBRES_ESTACIONES.get(estacion, estacion)
        zona = ZONAS_ESTACIONES.get(estacion, "")
        partes.append(f"la estación {nombre} ({zona}) lo alcanzó {periodo}")
    return (f"En {primer_anio}, el {costa} llegó al nivel 7 (mortalidad casi total), el máximo de la escala: "
            + "; ".join(partes) + ".")


def calcular_metricas():
    """Lee los archivos CSV en datos/limpios y calcula todos los valores necesarios."""
    carpeta_datos = DIRECTORIO_RAIZ / "datos" / "limpios"
    
    # 1. Leer temperatura_limpio.csv
    df_temperatura = pd.read_csv(carpeta_datos / "temperatura_limpio.csv")
    
    df_temperatura["costa_norm"] = df_temperatura["costa"].apply(
        lambda c: "Caribe" if "Car" in str(c) else "Pacífico"
    )
    
    ultima_fecha_str = df_temperatura["fecha"].max()
    ultima_fecha_dt = datetime.strptime(ultima_fecha_str, "%Y-%m-%d")
    fecha_ultimo_dato = formatear_fecha_espanol(ultima_fecha_dt)
    
    ahora = datetime.now()
    fecha_generacion = formatear_fecha_espanol(ahora, incluir_hora=True)
    
    fechas_ordenadas = sorted(df_temperatura["fecha"].unique())
    f_hoy = fechas_ordenadas[-1]
    f_ayer = fechas_ordenadas[-2]
    
    mar_hoy = {}
    for costa in ["Caribe", "Pacífico"]:
        sub_costa = df_temperatura[df_temperatura["costa_norm"] == costa]
        sub_hoy = sub_costa[sub_costa["fecha"] == f_hoy]
        sub_ayer = sub_costa[sub_costa["fecha"] == f_ayer]
        
        temp_hoy = float(sub_hoy["sst_90"].max())
        temp_ayer = float(sub_ayer["sst_90"].max())
        cambio_val = temp_hoy - temp_ayer
        
        flecha = "↑" if cambio_val > 0 else ("↓" if cambio_val < 0 else "=")
        signo = "+" if cambio_val > 0 else ""
        cambio_texto = f"{flecha} {signo}{cambio_val:.2f}"
        
        anomalia_hoy = float(sub_hoy["anomalia"].max())
        nivel_alerta = int(sub_hoy["alerta"].max())
        nombre_nivel = ESCALA_ALERTAS[nivel_alerta]["nombre"]
        color_nivel = ESCALA_ALERTAS[nivel_alerta]["color"]
        
        # Nivel de cada una de las 2 estaciones de la costa (el de la tarjeta es el más alto)
        estaciones_hoy = []
        for _, fila_est in sub_hoy.sort_values("estacion").iterrows():
            nivel_est = int(fila_est["alerta"])
            estaciones_hoy.append({
                "nombre": NOMBRES_ESTACIONES.get(fila_est["estacion"], fila_est["estacion"]),
                "nivel": nivel_est,
                "nombre_noaa": NOMBRES_NOAA[nivel_est],
                "color": ESCALA_ALERTAS[nivel_est]["color"],
            })

        mar_hoy[costa] = {
            "estaciones": estaciones_hoy,
            "nombre_noaa": NOMBRES_NOAA[nivel_alerta],
            "temp_hoy": f"{temp_hoy:.2f}",
            "cambio": cambio_texto,
            "cambio_num": cambio_val,
            "flecha": flecha,
            "anomalia_hoy": f"{anomalia_hoy:+.2f}",
            "nivel": nivel_alerta,
            "nombre_nivel": nombre_nivel,
            "color_nivel": color_nivel,
        }
        
    # 2. Leer anomalia_por_anio.csv (Hallazgo 1)
    df_anomalia = pd.read_csv(carpeta_datos / "anomalia_por_anio.csv")
    df_anomalia["costa_norm"] = df_anomalia["costa"].apply(
        lambda c: "Caribe" if "Car" in str(c) else "Pacífico"
    )
    
    resumen_decada = (
        df_anomalia.groupby(["decada", "costa_norm"])["anomalia"]
        .mean()
        .round(2)
        .unstack()
    )
    
    anomalia_caribe_1980s = f"{resumen_decada.loc[1980, 'Caribe']:+.2f}"
    anomalia_caribe_2020s = f"{resumen_decada.loc[2020, 'Caribe']:+.2f}"
    anomalia_pacifico_1980s = f"{resumen_decada.loc[1980, 'Pacífico']:+.2f}"
    anomalia_pacifico_2020s = f"{resumen_decada.loc[2020, 'Pacífico']:+.2f}"
    
    # 3. Leer semaforo_por_anio.csv (Hallazgo 2)
    df_semaforo = pd.read_csv(carpeta_datos / "semaforo_por_anio.csv")
    df_semaforo["costa_norm"] = df_semaforo["costa"].apply(
        lambda c: "Caribe" if "Car" in str(c) else "Pacífico"
    )
    
    casos_nivel5 = int((df_semaforo["alerta_max"] >= 5).sum())
    casos_nivel5_desde_2016 = int(
        ((df_semaforo["alerta_max"] >= 5) & (df_semaforo["anio"] >= 2016)).sum()
    )
    
    # 4. Leer corales_someros_por_costa.csv (Hallazgo 3)
    df_corales = pd.read_csv(carpeta_datos / "corales_someros_por_costa.csv")
    df_corales["costa_norm"] = df_corales["costa"].apply(
        lambda c: "Caribe" if "Car" in str(c) else "Pacífico"
    )
    
    especies_caribe_set = set(
        df_corales[df_corales["costa_norm"] == "Caribe"]["species"].dropna().unique()
    )
    especies_pacifico_set = set(
        df_corales[df_corales["costa_norm"] == "Pacífico"]["species"].dropna().unique()
    )
    especies_compartidas_set = especies_caribe_set & especies_pacifico_set
    
    especies_caribe = len(especies_caribe_set)
    especies_pacifico = len(especies_pacifico_set)
    especies_compartidas = len(especies_compartidas_set)
    
    # 5. Leer exposicion_por_costa.csv (Hallazgo 4)
    df_exposicion = pd.read_csv(carpeta_datos / "exposicion_por_costa.csv")
    df_exposicion["costa_norm"] = df_exposicion["costa"].apply(
        lambda c: "Caribe" if "Car" in str(c) else "Pacífico"
    )
    
    exp_caribe = df_exposicion[df_exposicion["costa_norm"] == "Caribe"].iloc[0]
    exp_pacifico = df_exposicion[df_exposicion["costa_norm"] == "Pacífico"].iloc[0]
    
    dias_caribe_antes = f"{exp_caribe['dias_n4_1985_2014']:.1f}"
    dias_caribe_ahora = f"{exp_caribe['dias_n4_2015_2025']:.1f}"
    dias_pacifico_antes = f"{exp_pacifico['dias_n4_1985_2014']:.1f}"
    dias_pacifico_ahora = f"{exp_pacifico['dias_n4_2015_2025']:.1f}"
    
    # 6. Datos del año 2026 (Sección 7)
    df_2026_temp = df_temperatura[df_temperatura["anio"] == 2026]
    df_2026_sem = df_semaforo[df_semaforo["anio"] == 2026]
    
    datos_2026 = {}
    for costa in ["Caribe", "Pacífico"]:
        sub_t = df_2026_temp[df_2026_temp["costa_norm"] == costa]
        sub_s = df_2026_sem[df_2026_sem["costa_norm"] == costa].iloc[0]
        
        anomalia_2026_val = float(sub_t["anomalia"].mean())
        dias_2026_val = int(sub_s["dias_nivel_4"])
        nivel_max_val = int(sub_s["alerta_max"])
        
        datos_2026[costa] = {
            "anomalia_2026": f"{anomalia_2026_val:+.2f}",
            "dias_2026": dias_2026_val,
            "nivel_max_2026": nivel_max_val,
            "nombre_nivel": ESCALA_ALERTAS[nivel_max_val]["nombre"],
            "color_nivel": ESCALA_ALERTAS[nivel_max_val]["color"],
        }
        
    return {
        "fecha_generacion": fecha_generacion,
        "fecha_ultimo_dato": fecha_ultimo_dato,
        "mar_hoy": mar_hoy,
        "frase_nivel7": calcular_frase_nivel7(df_temperatura),
        "anomalia_caribe_1980s": anomalia_caribe_1980s,
        "anomalia_caribe_2020s": anomalia_caribe_2020s,
        "anomalia_pacifico_1980s": anomalia_pacifico_1980s,
        "anomalia_pacifico_2020s": anomalia_pacifico_2020s,
        "resumen_decada": resumen_decada,
        "casos_nivel5": casos_nivel5,
        "casos_nivel5_desde_2016": casos_nivel5_desde_2016,
        "especies_caribe": especies_caribe,
        "especies_pacifico": especies_pacifico,
        "especies_compartidas": especies_compartidas,
        "dias_caribe_antes": dias_caribe_antes,
        "dias_caribe_ahora": dias_caribe_ahora,
        "dias_pacifico_antes": dias_pacifico_antes,
        "dias_pacifico_ahora": dias_pacifico_ahora,
        "datos_2026": datos_2026,
        "df_temperatura": df_temperatura,
        "df_anomalia": df_anomalia,
        "df_semaforo": df_semaforo,
        "df_corales": df_corales,
        "df_exposicion": df_exposicion,
    }


def generar_graficas_svg(metricas):
    """Genera las 4 figuras de matplotlib y las exporta como cadenas SVG limpias."""
    plt.rcParams["font.sans-serif"] = ["Inter", "Plus Jakarta Sans", "DejaVu Sans", "sans-serif"]
    plt.rcParams["axes.edgecolor"] = "#c3c6d0"
    plt.rcParams["axes.linewidth"] = 0.8
    plt.rcParams["text.color"] = "#171c1e"
    plt.rcParams["axes.labelcolor"] = "#42474f"
    plt.rcParams["xtick.color"] = "#42474f"
    plt.rcParams["ytick.color"] = "#42474f"
    
    # 1. Gráfica 1: Anomalía promedio por año (Hallazgo 1)
    df_anom = metricas["df_anomalia"]
    tabla_anual = df_anom.pivot(index="anio", columns="costa_norm", values="anomalia")
    
    fig1, ax1 = plt.subplots(figsize=(10, 4.2), facecolor="none")
    ax1.set_facecolor("none")
    
    ax1.plot(
        tabla_anual.index, tabla_anual["Caribe"],
        marker="o", markersize=4.5, linewidth=2.2, color="#1FA7A6", label="Mar Caribe"
    )
    ax1.plot(
        tabla_anual.index, tabla_anual["Pacífico"],
        marker="o", markersize=4.5, linewidth=2.2, color="#E75480", label="Océano Pacífico"
    )
    ax1.axhline(0, color="#737780", linestyle="--", linewidth=1.2, label="Normal (0 °C)")
    
    ax1.set_title("Anomalía promedio anual de temperatura del mar (NOAA)", fontsize=11, fontweight="bold", color="#0D3B66", pad=12)
    ax1.set_xlabel("Año", fontsize=9.5, fontweight="bold", color="#0D3B66")
    ax1.set_ylabel("Anomalía (°C)", fontsize=9.5, fontweight="bold", color="#0D3B66")
    ax1.tick_params(labelsize=8.5)
    ax1.grid(axis="y", linestyle=":", alpha=0.6, color="#737780")
    ax1.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#dee3e5", fontsize=8.5)
    svg_grafica1 = limpiar_svg(fig1)
    
    # 2. Gráfica 2: Semáforo de estrés térmico (Hallazgo 2)
    df_sem = metricas["df_semaforo"]
    tabla_sem = df_sem.pivot(index="costa_norm", columns="anio", values="alerta_max")
    tabla_sem = tabla_sem.reindex(["Caribe", "Pacífico"])
    
    colores_alerta = [ESCALA_ALERTAS[i]["color"] for i in range(8)]
    nombres_alerta = [f"{i} · {ESCALA_ALERTAS[i]['nombre']}" for i in range(8)]
    
    fig2, ax2 = plt.subplots(figsize=(13, 2.7), facecolor="none")
    ax2.set_facecolor("none")
    
    ax2.imshow(
        tabla_sem,
        cmap=ListedColormap(colores_alerta),
        vmin=-0.5,
        vmax=7.5,
        aspect="auto"
    )
    
    ax2.set_yticks(range(len(tabla_sem.index)))
    ax2.set_yticklabels(tabla_sem.index, fontsize=10, fontweight="bold", color="#0D3B66")
    ax2.set_xticks(range(len(tabla_sem.columns)))
    ax2.set_xticklabels(tabla_sem.columns, rotation=90, fontsize=7.5, color="#42474f")
    ax2.set_title("Semáforo: nivel máximo de alerta por año (NOAA)", fontsize=11, fontweight="bold", color="#0D3B66", pad=12)
    
    ax2.set_xticks([x - 0.5 for x in range(1, len(tabla_sem.columns))], minor=True)
    ax2.set_yticks([y - 0.5 for y in range(1, len(tabla_sem.index))], minor=True)
    ax2.grid(which="minor", color="white", linestyle="-", linewidth=1.5)
    ax2.tick_params(which="minor", bottom=False, left=False)
    
    parches_leyenda = [Patch(facecolor=c, edgecolor="none", label=n) for c, n in zip(colores_alerta, nombres_alerta)]
    ax2.legend(
        handles=parches_leyenda,
        ncol=4,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.42),
        frameon=False,
        fontsize=8
    )
    svg_grafica2 = limpiar_svg(fig2)
    
    # 3. Gráfica 3: Mapa de corales someros y estaciones NOAA (Hallazgo 3)
    df_cor = metricas["df_corales"]
    estaciones_noaa = pd.DataFrame({
        "estacion": ["Atlantic East", "Atlantic West", "Pacific East", "Pacific West"],
        "longitud": [-78.700, -81.650, -79.325, -82.250],
        "latitud": [9.200, 9.200, 8.175, 7.725],
    })
    
    fig3, ax3 = plt.subplots(figsize=(10.5, 5.2), facecolor="none")
    ax3.set_facecolor("none")

    # Contorno de Panamá (si existe el archivo descargado), dibujado DEBAJO de los puntos
    anillos_panama = leer_contorno_panama()
    for anillo in anillos_panama:
        ax3.add_patch(Polygon(anillo, closed=True, facecolor="#DCE8EF", edgecolor="#9DB7C7",
                              linewidth=1.0, alpha=0.6, zorder=1))
    if anillos_panama:
        # Etiquetas de los océanos, en el mar
        ax3.text(-80.35, 9.68, "Mar Caribe", fontsize=10, color="#5E8299",
                 fontweight="bold", ha="center", style="italic", zorder=2)
        ax3.text(-79.2, 7.35, "Océano Pacífico", fontsize=10, color="#5E8299",
                 fontweight="bold", ha="center", style="italic", zorder=2)
    
    corales_caribe = df_cor[df_cor["costa_norm"] == "Caribe"]
    corales_pacifico = df_cor[df_cor["costa_norm"] == "Pacífico"]
    
    ax3.scatter(
        corales_caribe["longitud"], corales_caribe["latitud"],
        s=15, alpha=0.55, color="#1FA7A6", label=f"Caribe ({len(corales_caribe):,} registros)",
        edgecolors="none"
    )
    ax3.scatter(
        corales_pacifico["longitud"], corales_pacifico["latitud"],
        s=28, alpha=0.8, color="#E75480", label=f"Pacífico ({len(corales_pacifico):,} registros)",
        edgecolors="none"
    )
    
    ax3.scatter(
        estaciones_noaa["longitud"], estaciones_noaa["latitud"],
        marker="*", s=320, color="#0D3B66", edgecolor="white", linewidth=1.2,
        label="Estaciones NOAA", zorder=5
    )
    
    for _, fila in estaciones_noaa.iterrows():
        ax3.annotate(
            fila["estacion"],
            (fila["longitud"], fila["latitud"]),
            textcoords="offset points",
            xytext=(7, 7),
            fontsize=8,
            fontweight="bold",
            color="#0D3B66",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", alpha=0.9, edgecolor="#dee3e5", linewidth=0.6)
        )
        
    ax3.set_title("Corales someros registrados y 4 estaciones virtuales de NOAA en Panamá", fontsize=11, fontweight="bold", color="#0D3B66", pad=12)
    ax3.set_xlabel("Longitud (°)", fontsize=9.5, fontweight="bold", color="#0D3B66")
    ax3.set_ylabel("Latitud (°)", fontsize=9.5, fontweight="bold", color="#0D3B66")
    ax3.tick_params(labelsize=8.5)
    ax3.set_aspect("equal")
    if anillos_panama:
        ax3.set_xlim(-83.2, -77.1)   # todo el país, de Costa Rica a Colombia
        ax3.set_ylim(7.0, 9.85)
    ax3.grid(True, linestyle=":", alpha=0.5, color="#737780")
    ax3.legend(loc="lower left", frameon=True, facecolor="white", edgecolor="#dee3e5", fontsize=8.5)
    svg_grafica3 = limpiar_svg(fig3)
    
    # 4. Gráfica 4: Comparativa de días en nivel 4+ antes vs ahora (Hallazgo 4)
    df_exp = metricas["df_exposicion"]
    df_exp_ordenado = df_exp.sort_values("costa_norm", ascending=True)
    
    posiciones = range(len(df_exp_ordenado))
    pos_izq = [i - 0.18 for i in posiciones]
    pos_der = [i + 0.18 for i in posiciones]
    
    fig4, ax4 = plt.subplots(figsize=(7.5, 4.5), facecolor="none")
    ax4.set_facecolor("none")
    
    barras_antes = ax4.bar(
        pos_izq, df_exp_ordenado["dias_n4_1985_2014"],
        width=0.34, label="1985-2014", color="#FF8A5B", edgecolor="white", linewidth=0.8, zorder=3
    )
    barras_ahora = ax4.bar(
        pos_der, df_exp_ordenado["dias_n4_2015_2025"],
        width=0.34, label="2015-2025", color="#6C2E7B", edgecolor="white", linewidth=0.8, zorder=3
    )
    
    ax4.bar_label(barras_antes, fmt="%.1f", padding=4, fontsize=9.5, fontweight="bold", color="#FF8A5B")
    ax4.bar_label(barras_ahora, fmt="%.1f", padding=4, fontsize=9.5, fontweight="bold", color="#6C2E7B")
    
    ax4.set_xticks(list(posiciones))
    ax4.set_xticklabels(df_exp_ordenado["costa_norm"], fontsize=10.5, fontweight="bold", color="#0D3B66")
    ax4.set_title("Días al año en nivel 4 o superior de alerta (promedio)", fontsize=11, fontweight="bold", color="#0D3B66", pad=12)
    ax4.set_ylabel("Días al año (promedio)", fontsize=9.5, fontweight="bold", color="#0D3B66")
    ax4.tick_params(labelsize=8.5)
    ax4.grid(axis="y", linestyle=":", alpha=0.6, color="#737780", zorder=0)
    ax4.legend(frameon=True, facecolor="white", edgecolor="#dee3e5", fontsize=9)
    svg_grafica4 = limpiar_svg(fig4)
    
    return {
        "svg_grafica1": svg_grafica1,
        "svg_grafica2": svg_grafica2,
        "svg_grafica3": svg_grafica3,
        "svg_grafica4": svg_grafica4,
    }


def construir_css_autonomo():
    """Genera las reglas CSS necesarias directamente dentro del HTML para prescindir de CDN."""
    return """
    /* Reset y tipografía con fuentes del sistema como respaldo inmediato */
    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    
    html {
      scroll-behavior: smooth;
    }
    
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #171c1e;
      background-color: #e3f4f8;
      line-height: 1.55;
      -webkit-font-smoothing: antialiased;
    }
    
    h1, h2, h3, h4, h5, h6, .font-title {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Contenedores y espaciados */
    .container-base { width: 100%; margin-left: auto; margin-right: auto; }
    .max-w-7xl { max-width: 80rem; }
    .max-w-6xl { max-width: 72rem; }
    .max-w-4xl { max-width: 56rem; }
    .max-w-3xl { max-width: 48rem; }
    .max-w-2xl { max-width: 42rem; }
    
    .section-py { padding-top: 5rem; padding-bottom: 5rem; }
    .section-px { padding-left: 1.5rem; padding-right: 1.5rem; }
    @media (min-width: 768px) {
      .section-px { padding-left: 3rem; padding-right: 3rem; }
    }
    @media (min-width: 1024px) {
      .section-px { padding-left: 6rem; padding-right: 6rem; }
    }
    
    /* Sistema de tarjetas Glassmorphic del diseño Stitch */
    .glass-card {
      background: rgba(255, 255, 255, 0.90);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-radius: 20px;
      border: 1px solid rgba(255, 255, 255, 0.85);
      box-shadow: 0 8px 32px -4px rgba(13, 59, 102, 0.10);
      position: relative;
    }
    
    .glass-card-hover {
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .glass-card-hover:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 40px -4px rgba(13, 59, 102, 0.15);
    }
    
    /* Barra de navegación superior fija */
    header.nav-header {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      height: 4rem;
      z-index: 50;
      background: rgba(255, 255, 255, 0.85);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border-bottom: 1px solid rgba(255, 255, 255, 0.6);
      box-shadow: 0 1px 12px rgba(0, 37, 70, 0.06);
      display: flex;
      align-items: center;
      padding: 0 1.5rem;
      justify-content: space-between;
    }
    @media (min-width: 768px) {
      header.nav-header { padding: 0 2.5rem; }
    }
    
    /* Enlaces y botones estilo píldora */
    .nav-links { display: none; align-items: center; gap: 0.375rem; }
    @media (min-width: 1024px) { .nav-links { display: flex; } }
    
    .nav-link {
      padding: 0.375rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      color: #42474f;
      text-decoration: none;
      transition: all 0.2s ease;
    }
    .nav-link:hover {
      color: #0D3B66;
      background: rgba(224, 242, 254, 0.7);
    }
    
    /* Flexbox y cuadrículas */
    .flex { display: flex; }
    .flex-col { flex-direction: column; }
    .items-center { align-items: center; }
    .items-start { align-items: flex-start; }
    .items-baseline { align-items: baseline; }
    .items-stretch { align-items: stretch; }
    .justify-between { justify-content: space-between; }
    .justify-center { justify-content: center; }
    .flex-wrap { flex-wrap: wrap; }
    .shrink-0 { flex-shrink: 0; }
    .text-center { text-align: center; }
    .text-left { text-align: left; }
    .relative { position: relative; }
    .overflow-hidden { overflow: hidden; }
    .overflow-x-auto { overflow-x: auto; }
    
    .grid { display: grid; }
    .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
    
    @media (min-width: 640px) {
      .sm-grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .sm-grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .sm-grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    }
    @media (min-width: 768px) {
      .md-grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .md-grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    }
    @media (min-width: 1024px) {
      .lg-grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .lg-grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
      .lg-grid-cols-8 { grid-template-columns: repeat(8, minmax(0, 1fr)); }
      .lg-grid-cols-12 { grid-template-columns: repeat(12, minmax(0, 1fr)); }
      .lg-col-4 { grid-column: span 4 / span 12; }
      .lg-col-8 { grid-column: span 8 / span 12; }
    }
    
    /* Gaps */
    .gap-2 { gap: 0.5rem; }
    .gap-3 { gap: 0.75rem; }
    .gap-4 { gap: 1rem; }
    .gap-5 { gap: 1.25rem; }
    .gap-6 { gap: 1.5rem; }
    .gap-8 { gap: 2rem; }
    .gap-12 { gap: 3rem; }
    .space-y-4 > * + * { margin-top: 1rem; }
    .space-y-6 > * + * { margin-top: 1.5rem; }
    .space-y-8 > * + * { margin-top: 2rem; }
    .space-y-10 > * + * { margin-top: 2.5rem; }
    .space-y-12 > * + * { margin-top: 3rem; }
    .space-y-16 > * + * { margin-top: 4rem; }
    
    /* Paddings internos */
    .p-2 { padding: 0.5rem; }
    .p-3 { padding: 0.75rem; }
    .p-4 { padding: 1rem; }
    .p-5 { padding: 1.25rem; }
    .p-6 { padding: 1.5rem; }
    .p-8 { padding: 2rem; }
    .p-10 { padding: 2.5rem; }
    @media (max-width: 640px) {
      .p-8 { padding: 1.5rem; }
      .p-10 { padding: 1.5rem; }
    }
    
    /* Colores y tipografía */
    .text-primary { color: #0D3B66; }
    .text-secondary { color: #1FA7A6; }
    .text-tertiary { color: #E75480; }
    .text-muted { color: #737780; }
    .text-body { color: #42474f; }
    
    .gradient-text {
      background: linear-gradient(to right, #006a69, #e75480);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    
    .rounded-xl { border-radius: 0.75rem; }
    .rounded-2xl { border-radius: 1rem; }
    .rounded-full { border-radius: 9999px; }
    
    /* Animación flecha bounce */
    @keyframes bounce {
      0%, 100% { transform: translateY(-25%); animation-timing-function: cubic-bezier(0.8,0,1,1); }
      50% { transform: none; animation-timing-function: cubic-bezier(0,0,0.2,1); }
    }
    .animate-bounce { animation: bounce 1.2s infinite; }
    
    /* Íconos SVG */
    .icon-svg { display: inline-block; vertical-align: middle; }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(227, 244, 248, 0.5); }
    ::-webkit-scrollbar-thumb { background: #1FA7A6; border-radius: 3px; }
    """


def html_detalle_estaciones(datos_costa):
    """Devuelve el bloque HTML con el nivel de cada estación y la equivalencia con el nombre de NOAA."""
    filas = ""
    for est in datos_costa["estaciones"]:
        filas += f"""
              <div class="flex items-center justify-between" style="font-size: 0.75rem; color: #42474f; padding: 0.2rem 0;">
                <span class="flex items-center gap-2">
                  <span style="width: 0.6rem; height: 0.6rem; border-radius: 9999px; background: {est['color']}; display: inline-block;"></span>
                  {est['nombre']}
                </span>
                <span style="font-weight: 600;">Nivel {est['nivel']} <span style="font-weight: 400; color: #737780;">(NOAA: {est['nombre_noaa']})</span></span>
              </div>"""
    return f"""
            <div style="margin-top: 1rem; padding: 0.75rem 1rem; border-radius: 0.75rem; background: rgba(240, 249, 255, 0.75); border: 1px solid rgba(224, 242, 254, 0.9);">
              <div style="font-size: 0.7rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.06em; color: #0D3B66; margin-bottom: 0.35rem;">
                Nivel por estación · la tarjeta muestra el más alto
              </div>{filas}
            </div>"""


def construir_html_dashboard(metricas, graficas, imagenes):
    """Construye el documento HTML completo y estilizado con todos los textos y datos calculados."""
    m = metricas
    g = graficas
    img = imagenes
    
    # Tabla pequeña de anomalía por década (Hallazgo 1)
    tabla_decada_html = """
    <div class="overflow-x-auto" style="padding-top: 0.5rem;">
      <table style="width: 100%; text-align: left; font-size: 0.75rem; border-collapse: collapse;">
        <thead>
          <tr style="border-bottom: 1px solid #e0f2fe; color: #0D3B66;">
            <th style="padding: 0.5rem; font-weight: bold;">Década</th>
            <th style="padding: 0.5rem; font-weight: bold; color: #1FA7A6;">Caribe</th>
            <th style="padding: 0.5rem; font-weight: bold; color: #E75480;">Pacífico</th>
          </tr>
        </thead>
        <tbody style="color: #42474f;">
    """
    for decada in [1980, 1990, 2000, 2010, 2020]:
        c_val = m["resumen_decada"].loc[decada, "Caribe"]
        p_val = m["resumen_decada"].loc[decada, "Pacífico"]
        es_resaltada = 'style="font-weight: bold; background-color: rgba(224, 242, 254, 0.3); border-bottom: 1px solid #e0f2fe;"' if decada in [1980, 2020] else 'style="border-bottom: 1px solid #f0f9ff;"'
        tabla_decada_html += f"""
          <tr {es_resaltada}>
            <td style="padding: 0.4rem 0.5rem; font-weight: 500;">{decada}s</td>
            <td style="padding: 0.4rem 0.5rem; font-weight: 600; color: #1FA7A6;">{c_val:+.2f} °C</td>
            <td style="padding: 0.4rem 0.5rem; font-weight: 600; color: #E75480;">{p_val:+.2f} °C</td>
          </tr>
        """
    tabla_decada_html += """
        </tbody>
      </table>
    </div>
    """
    
    # Escala de 8 niveles en formato visual de tarjetas
    escala_8_niveles_html = '<div class="grid grid-cols-1 sm-grid-cols-2 md-grid-cols-4 lg-grid-cols-8 gap-2" style="padding-top: 0.75rem;">'
    for lvl in range(8):
        c = ESCALA_ALERTAS[lvl]["color"]
        n = ESCALA_ALERTAS[lvl]["nombre"]
        escala_8_niveles_html += f"""
        <div class="flex flex-col items-center p-3 rounded-xl text-center" style="background: rgba(240, 249, 255, 0.75); border: 1px solid rgba(224, 242, 254, 0.8);">
          <span style="width: 100%; height: 0.75rem; border-radius: 9999px; margin-bottom: 0.4rem; background-color: {c}; display: block;"></span>
          <span style="font-size: 0.75rem; font-weight: bold; color: #0D3B66;">Nivel {lvl}</span>
          <span style="font-size: 0.65rem; color: #42474f; font-weight: 500; line-height: 1.2; margin-top: 0.15rem;">{n}</span>
          <span style="font-size: 0.6rem; color: #737780; line-height: 1.2; margin-top: 0.3rem;">NOAA: {NOMBRES_NOAA[lvl]}</span>
        </div>
        """
    escala_8_niveles_html += "</div>"
    escala_8_niveles_html += """
    <p style="font-size: 0.75rem; color: #737780; margin-top: 0.6rem;">
      En su página, NOAA llama "Alert Level 1" al nivel 3 de esta escala: los niveles 0, 1 y 2 tienen nombre propio
      (No Stress, Watch y Warning). Por eso, por ejemplo, el "Alert Level 4" de NOAA es el nivel 6 de este dashboard.
    </p>"""
    
    css_autonomo = construir_css_autonomo()

    # Fuente del contorno de Panamá (solo si el archivo existe)
    texto_contorno = leer_fuente_contorno()
    fuente_contorno_html = ""
    if texto_contorno:
        fuente_contorno_html = f"""
              <li class="flex items-start gap-2">
                <span style="width: 0.35rem; height: 0.35rem; border-radius: 9999px; background: #1FA7A6; margin-top: 0.45rem; shrink: 0;"></span>
                <span>{texto_contorno}</span>
              </li>"""
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Corales de Panamá y eventos de El Niño: un análisis con datos abiertos</title>
  
  <!-- Enlace a Google Fonts (opcional cuando hay internet; si no hay, el CSS usa respaldo local del sistema) -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
  
  <!-- Estilos embebidos autónomos: reemplaza dependencias de JavaScript y Tailwind CDN -->
  <style>
    {css_autonomo}
    body {{
      background-image: linear-gradient(rgba(240, 248, 250, 0.35), rgba(240, 248, 250, 0.35)), url("{img['fondo_burbujas']}");
      background-repeat: repeat;
      background-size: 380px auto;
      background-attachment: fixed;
    }}
  </style>
</head>
<body>

  <!-- ========================================== -->
  <!-- 0. MENÚ                                    -->
  <!-- ========================================== -->
  <header class="nav-header">
    <div class="flex items-center gap-3">
      <img alt="Logo Corales" class="rounded-full shadow-sm" style="width: 2.25rem; height: 2.25rem; object-fit: contain; border: 1px solid rgba(0, 106, 105, 0.2);" src="{img['logo_corales']}">
      <span class="font-title" style="font-size: 1.15rem; font-weight: bold; color: #0D3B66; letter-spacing: -0.02em;">Corales de Panamá</span>
    </div>
    
    <nav class="nav-links">
      <a class="nav-link" href="#inicio">Inicio</a>
      <a class="nav-link" href="#conceptos">Conceptos</a>
      <a class="nav-link" href="#contexto">Contexto</a>
      <a class="nav-link" href="#analisis">Análisis</a>
      <a class="nav-link" href="#hoy">Hoy</a>
      <a class="nav-link" href="#conclusion">Conclusión</a>
    </nav>
    
    <div class="flex items-center gap-3">
      <div class="rounded-full flex items-center justify-center text-white" style="width: 2rem; height: 2rem; background-color: #002546; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        {ICONOS_SVG['waves']}
      </div>
    </div>
  </header>

  <main style="width: 100%; padding-top: 4rem; min-height: 100vh;">
    <div class="flex flex-col" style="width: 100%;">

      <!-- ========================================== -->
      <!-- 1. PORTADA (#inicio)                       -->
      <!-- ========================================== -->
      <section class="section-px flex flex-col justify-between items-center text-center" style="min-height: 88vh; padding-top: 4rem; padding-bottom: 3rem;" id="inicio">
        <!-- Logo UIP (solo en esta sección) -->
        <div class="flex justify-center" style="width: 100%; margin-bottom: 2rem;">
          <div class="glass-card" style="padding: 0.6rem 1.5rem; display: inline-flex; align-items: center; justify-content: center;">
            <img alt="Logo UIP" style="max-height: 60px; width: auto; object-fit: contain;" src="{img['logo_uip']}">
          </div>
        </div>

        <!-- Título y Subtítulo -->
        <div class="max-w-4xl container-base flex flex-col items-center" style="margin-top: auto; margin-bottom: auto; padding: 1rem 0;">
          <h1 class="font-title text-primary" style="font-size: clamp(1.8rem, 4.5vw, 3.5rem); font-weight: 800; line-height: 1.15; margin-bottom: 1.5rem; letter-spacing: -0.025em;">
            Corales de Panamá y eventos de El Niño: <span class="gradient-text">un análisis con datos abiertos</span>
          </h1>

          <p class="text-primary font-title" style="font-size: clamp(1.1rem, 2vw, 1.4rem); font-weight: 600; line-height: 1.5; max-width: 48rem; margin-bottom: 2rem;">
            Análisis con datos abiertos de GBIF y NOAA Coral Reef Watch
          </p>

          <!-- Tarjeta de datos académicos -->
          <div class="glass-card text-left" style="width: 100%; max-width: 42rem; padding: 1.75rem;">
            <div class="flex flex-wrap items-center justify-between gap-3" style="border-bottom: 1px solid #e0f2fe; padding-bottom: 1rem; margin-bottom: 1rem;">
              <span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: bold; color: #0D3B66;">
                Datos actualizados: {m['fecha_generacion']}
              </span>
            </div>

            <div class="grid grid-cols-1 sm-grid-cols-2 gap-4" style="font-size: 0.875rem; color: #0D3B66;">
              <div>
                <p style="font-size: 0.75rem; color: #737780; font-weight: 600;">Autores</p>
                <p style="font-weight: bold; margin-top: 0.2rem; color: #002546;">Angela Pérez</p>
                <p style="font-weight: bold; color: #002546;">Edwin De Frías</p>
              </div>
              <div>
                <p style="font-size: 0.75rem; color: #737780; font-weight: 600;">Curso</p>
                <p style="font-weight: bold; margin-top: 0.2rem; color: #002546;">Introducción a la Programación para Ciencia de Datos · Maestría en Ciencias de los Datos, Universidad Interamericana de Panamá</p>
                <p style="font-size: 0.8rem; color: #42474f; margin-top: 0.4rem;">Profesor: <span style="font-weight: 600; color: #0D3B66;">José Higuera</span></p>
              </div>
            </div>
          </div>
        </div>

        <!-- Indicador de desplazamiento con flecha -->
        <div class="flex flex-col items-center" style="margin-top: 1.5rem;">
          <a class="glass-card animate-bounce flex items-center justify-center text-primary" style="width: 2.5rem; height: 2.5rem; border-radius: 9999px; text-decoration: none;" href="#hoy">
            {ICONOS_SVG['arrow_down']}
          </a>
        </div>
      </section>

      <!-- ========================================== -->
      <!-- 2. EL MAR HOY (#hoy)                       -->
      <!-- ========================================== -->
      <section class="section-py section-px" id="hoy">
        <div class="max-w-6xl container-base">
          <div class="text-center max-w-3xl container-base" style="margin-bottom: 3rem;">
            <h2 class="font-title text-primary" style="font-size: clamp(1.8rem, 3.5vw, 2.75rem); font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.75rem;">
              El mar hoy
            </h2>
            <p class="font-title text-primary" style="font-size: clamp(1rem, 1.75vw, 1.25rem); font-weight: 600; line-height: 1.5;">
              Temperatura y nivel de alerta de blanqueamiento en las dos costas, según el último dato publicado por NOAA.
            </p>
          </div>

          <!-- Dos tarjetas: Caribe y Pacífico -->
          <div class="grid grid-cols-1 lg-grid-cols-2 gap-8 items-stretch">
            
            <!-- Tarjeta Caribe -->
            <div class="glass-card glass-card-hover p-8 flex flex-col justify-between overflow-hidden">
              <div style="position: absolute; top: 0; left: 0; right: 0; height: 0.35rem; background-color: #1FA7A6;"></div>
              <div>
                <div class="flex items-center justify-between" style="margin-bottom: 1rem;">
                  <div class="flex items-center gap-2" style="color: #1FA7A6;">
                    {ICONOS_SVG['waves']}
                    <span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: bold;">Caribe</span>
                  </div>
                </div>
                
                <h3 class="font-title text-primary" style="font-size: 1.75rem; font-weight: 700; margin-bottom: 1rem;">
                  Caribe
                </h3>
                
                <div class="flex items-baseline gap-4" style="margin-bottom: 1.5rem;">
                  <span class="font-title text-primary" style="font-size: clamp(3rem, 5vw, 4.25rem); font-weight: 800; letter-spacing: -0.03em;">
                    {m['mar_hoy']['Caribe']['temp_hoy']}<span style="font-size: 2rem; font-weight: 600; color: #1FA7A6;">°C</span>
                  </span>
                  <div class="flex flex-col">
                    <span style="font-size: 0.75rem; font-weight: bold; padding: 0.2rem 0.5rem; border-radius: 0.25rem; background: {'#fef3c7; color: #92400e;' if m['mar_hoy']['Caribe']['cambio_num'] > 0 else '#e0f2fe; color: #0369a1;'}">
                      {m['mar_hoy']['Caribe']['cambio']} °C
                    </span>
                    <span style="font-size: 0.75rem; color: #42474f; margin-top: 0.35rem; font-weight: 600;">
                      Anomalía: {m['mar_hoy']['Caribe']['anomalia_hoy']} °C sobre lo normal
                    </span>
                  </div>
                </div>
              </div>
              
              <div class="flex flex-wrap items-center justify-between gap-3" style="padding-top: 1.25rem; border-top: 1px solid #e0f2fe;">
                <span style="padding: 0.4rem 1rem; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; color: white; background-color: {m['mar_hoy']['Caribe']['color_nivel']};">
                  Nivel {m['mar_hoy']['Caribe']['nivel']} · {m['mar_hoy']['Caribe']['nombre_nivel']}
                  <span style="font-weight: 500; opacity: 0.85;">(NOAA: {m['mar_hoy']['Caribe']['nombre_noaa']})</span>
                </span>
                <span class="flex items-center gap-1" style="font-size: 0.75rem; color: #737780; font-weight: 500;">
                  <span style="color: #1FA7A6;">{ICONOS_SVG['sensors']}</span> Dato del {m['fecha_ultimo_dato']}
                </span>
              </div>
              {html_detalle_estaciones(m['mar_hoy']['Caribe'])}
            </div>

            <!-- Tarjeta Pacífico -->
            <div class="glass-card glass-card-hover p-8 flex flex-col justify-between overflow-hidden">
              <div style="position: absolute; top: 0; left: 0; right: 0; height: 0.35rem; background-color: #E75480;"></div>
              <div>
                <div class="flex items-center justify-between" style="margin-bottom: 1rem;">
                  <div class="flex items-center gap-2" style="color: #E75480;">
                    {ICONOS_SVG['tsunami']}
                    <span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: bold;">Pacífico</span>
                  </div>
                </div>
                
                <h3 class="font-title text-primary" style="font-size: 1.75rem; font-weight: 700; margin-bottom: 1rem;">
                  Pacífico
                </h3>
                
                <div class="flex items-baseline gap-4" style="margin-bottom: 1.5rem;">
                  <span class="font-title text-primary" style="font-size: clamp(3rem, 5vw, 4.25rem); font-weight: 800; letter-spacing: -0.03em;">
                    {m['mar_hoy']['Pacífico']['temp_hoy']}<span style="font-size: 2rem; font-weight: 600; color: #E75480;">°C</span>
                  </span>
                  <div class="flex flex-col">
                    <span style="font-size: 0.75rem; font-weight: bold; padding: 0.2rem 0.5rem; border-radius: 0.25rem; background: {'#fef3c7; color: #92400e;' if m['mar_hoy']['Pacífico']['cambio_num'] > 0 else '#e0f2fe; color: #0369a1;'}">
                      {m['mar_hoy']['Pacífico']['cambio']} °C
                    </span>
                    <span style="font-size: 0.75rem; color: #42474f; margin-top: 0.35rem; font-weight: 600;">
                      Anomalía: {m['mar_hoy']['Pacífico']['anomalia_hoy']} °C sobre lo normal
                    </span>
                  </div>
                </div>
              </div>
              
              <div class="flex flex-wrap items-center justify-between gap-3" style="padding-top: 1.25rem; border-top: 1px solid #e0f2fe;">
                <span style="padding: 0.4rem 1rem; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; color: white; background-color: {m['mar_hoy']['Pacífico']['color_nivel']};">
                  Nivel {m['mar_hoy']['Pacífico']['nivel']} · {m['mar_hoy']['Pacífico']['nombre_nivel']}
                  <span style="font-weight: 500; opacity: 0.85;">(NOAA: {m['mar_hoy']['Pacífico']['nombre_noaa']})</span>
                </span>
                <span class="flex items-center gap-1" style="font-size: 0.75rem; color: #737780; font-weight: 500;">
                  <span style="color: #E75480;">{ICONOS_SVG['sensors']}</span> Dato del {m['fecha_ultimo_dato']}
                </span>
              </div>
              {html_detalle_estaciones(m['mar_hoy']['Pacífico'])}
            </div>

          </div>
        </div>
      </section>

      <!-- ========================================== -->
      <!-- 3. CONCEPTOS CLAVE (#conceptos)            -->
      <!-- ========================================== -->
      <section class="section-py section-px" id="conceptos">
        <div class="max-w-7xl container-base">
          <div class="text-center max-w-3xl container-base" style="margin-bottom: 3rem;">
            <h2 class="font-title text-primary" style="font-size: clamp(1.8rem, 3.5vw, 2.75rem); font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.5rem;">
              Antes de sumergirnos: conceptos clave
            </h2>
            <p class="font-title text-primary" style="font-size: clamp(1rem, 1.75vw, 1.25rem); font-weight: 600; line-height: 1.5;">
              Nosotros tampoco somos biólogos marinos, así que empecemos por lo básico.
            </p>
          </div>

          <!-- Cuadrícula de 12 conceptos -->
          <div class="grid grid-cols-1 sm-grid-cols-2 lg-grid-cols-4 gap-5">
            
            <div class="glass-card glass-card-hover p-5 flex flex-col">
              <div class="rounded-xl flex items-center justify-center" style="width: 2.5rem; height: 2.5rem; background: #e6f7f7; color: #1FA7A6; margin-bottom: 0.75rem;">
                {ICONOS_SVG['bubble_chart']}
              </div>
              <h4 class="font-title text-primary" style="font-size: 1rem; font-weight: bold; margin-bottom: 0.35rem;">Coral</h4>
              <p style="font-size: 0.78rem; color: #42474f; line-height: 1.45;">Un animal, no una planta ni una piedra. Son colonias de pólipos diminutos que construyen un esqueleto duro de calcio.</p>
            </div>

            <div class="glass-card glass-card-hover p-5 flex flex-col">
              <div class="rounded-xl flex items-center justify-center" style="width: 2.5rem; height: 2.5rem; background: #ecfdf5; color: #059669; margin-bottom: 0.75rem;">
                {ICONOS_SVG['spa']}
              </div>
              <h4 class="font-title text-primary" style="font-size: 1rem; font-weight: bold; margin-bottom: 0.35rem;">Algas del coral</h4>
              <p style="font-size: 0.78rem; color: #42474f; line-height: 1.45;">Algas microscópicas (zooxantelas) que viven dentro del coral. Le dan su color y la mayor parte de su alimento, y necesitan luz para vivir.</p>
            </div>

            <div class="glass-card glass-card-hover p-5 flex flex-col">
              <div class="rounded-xl flex items-center justify-center" style="width: 2.5rem; height: 2.5rem; background: #f0f9ff; color: #0284c7; margin-bottom: 0.75rem;">
                {ICONOS_SVG['foundation']}
              </div>
              <h4 class="font-title text-primary" style="font-size: 1rem; font-weight: bold; margin-bottom: 0.35rem;">Arrecife</h4>
              <p style="font-size: 0.78rem; color: #42474f; line-height: 1.45;">La estructura que forman los esqueletos de coral acumulados durante siglos. Es el hogar y la "guardería" de cientos de especies de peces.</p>
            </div>

            <div class="glass-card glass-card-hover p-5 flex flex-col">
              <div class="rounded-xl flex items-center justify-center" style="width: 2.5rem; height: 2.5rem; background: #fefce8; color: #ca8a04; margin-bottom: 0.75rem;">
                {ICONOS_SVG['wb_sunny']}
              </div>
              <h4 class="font-title text-primary" style="font-size: 1rem; font-weight: bold; margin-bottom: 0.35rem;">Coral somero</h4>
              <p style="font-size: 0.78rem; color: #42474f; line-height: 1.45;">Vive en aguas poco profundas e iluminadas: en este proyecto, hasta 50 m. Son los que forman arrecifes y los que sienten el calentamiento del mar.</p>
            </div>

            <div class="glass-card glass-card-hover p-5 flex flex-col">
              <div class="rounded-xl flex items-center justify-center" style="width: 2.5rem; height: 2.5rem; background: #eef2ff; color: #0D3B66; margin-bottom: 0.75rem;">
                {ICONOS_SVG['arrow_downward']}
              </div>
              <h4 class="font-title text-primary" style="font-size: 1rem; font-weight: bold; margin-bottom: 0.35rem;">Coral profundo</h4>
              <p style="font-size: 0.78rem; color: #42474f; line-height: 1.45;">Vive a más de 50 m, casi sin luz. No tiene algas ni forma arrecifes, y no lo afecta la temperatura de la superficie. Por eso no se incluyó en el análisis.</p>
            </div>

            <div class="glass-card glass-card-hover p-5 flex flex-col">
              <div class="rounded-xl flex items-center justify-center" style="width: 2.5rem; height: 2.5rem; background: #fff1f2; color: #E75480; margin-bottom: 0.75rem;">
                {ICONOS_SVG['water_loss']}
              </div>
              <h4 class="font-title text-primary" style="font-size: 1rem; font-weight: bold; margin-bottom: 0.35rem;">Blanqueamiento</h4>
              <p style="font-size: 0.78rem; color: #42474f; line-height: 1.45;">Cuando el agua se calienta demasiado, el coral expulsa sus algas y se ve blanco. No está muerto todavía, pero si el calor dura mucho, muere de hambre.</p>
            </div>

            <div class="glass-card glass-card-hover p-5 flex flex-col">
              <div class="rounded-xl flex items-center justify-center" style="width: 2.5rem; height: 2.5rem; background: #fff7ed; color: #ea580c; margin-bottom: 0.75rem;">
                {ICONOS_SVG['thermostat']}
              </div>
              <h4 class="font-title text-primary" style="font-size: 1rem; font-weight: bold; margin-bottom: 0.35rem;">Anomalía de temperatura</h4>
              <p style="font-size: 0.78rem; color: #42474f; line-height: 1.45;">Cuántos grados más (o menos) caliente está el mar comparado con lo normal para esa época del año.</p>
            </div>

            <div class="glass-card glass-card-hover p-5 flex flex-col">
              <div class="rounded-xl flex items-center justify-center" style="width: 2.5rem; height: 2.5rem; background: #fdf2f8; color: #E75480; margin-bottom: 0.75rem;">
                {ICONOS_SVG['local_fire_department']}
              </div>
              <h4 class="font-title text-primary" style="font-size: 1rem; font-weight: bold; margin-bottom: 0.35rem;">Calor acumulado (DHW)</h4>
              <p style="font-size: 0.78rem; color: #42474f; line-height: 1.45;">Suma cuánto calor extra ha soportado el coral en las últimas 12 semanas. Por eso un día un poco más fresco no baja el riesgo.</p>
            </div>

            <div class="glass-card glass-card-hover p-5 flex flex-col">
              <div class="rounded-xl flex items-center justify-center" style="width: 2.5rem; height: 2.5rem; background: #faf5ff; color: #6C2E7B; margin-bottom: 0.75rem;">
                {ICONOS_SVG['warning']}
              </div>
              <h4 class="font-title text-primary" style="font-size: 1rem; font-weight: bold; margin-bottom: 0.35rem;">Nivel de alerta</h4>
              <p style="font-size: 0.78rem; color: #42474f; line-height: 1.45;">Escala de NOAA del 0 al 7, que va de "sin estrés" a "mortalidad casi total", según el calor acumulado.</p>
            </div>

            <div class="glass-card glass-card-hover p-5 flex flex-col">
              <div class="rounded-xl flex items-center justify-center" style="width: 2.5rem; height: 2.5rem; background: #f3e8ff; color: #4A1F5C; margin-bottom: 0.75rem;">
                {ICONOS_SVG['cyclone']}
              </div>
              <h4 class="font-title text-primary" style="font-size: 1rem; font-weight: bold; margin-bottom: 0.35rem;">El Niño</h4>
              <p style="font-size: 0.78rem; color: #42474f; line-height: 1.45;">Fenómeno natural en el que el Pacífico se calienta. Llega cada 2 a 7 años y, con el calentamiento global, alcanza temperaturas cada vez más altas.</p>
            </div>

            <div class="glass-card glass-card-hover p-5 flex flex-col">
              <div class="rounded-xl flex items-center justify-center" style="width: 2.5rem; height: 2.5rem; background: #f1f5f9; color: #2A0A4A; margin-bottom: 0.75rem;">
                {ICONOS_SVG['satellite_alt']}
              </div>
              <h4 class="font-title text-primary" style="font-size: 1rem; font-weight: bold; margin-bottom: 0.35rem;">Estación virtual</h4>
              <p style="font-size: 0.78rem; color: #42474f; line-height: 1.45;">Un área del mar que un satélite vigila todos los días. Usamos 4: dos en el Caribe y dos en el Pacífico.</p>
            </div>

            <div class="glass-card glass-card-hover p-5 flex flex-col">
              <div class="rounded-xl flex items-center justify-center" style="width: 2.5rem; height: 2.5rem; background: #ecfeff; color: #006a69; margin-bottom: 0.75rem;">
                {ICONOS_SVG['dataset']}
              </div>
              <h4 class="font-title text-primary" style="font-size: 1rem; font-weight: bold; margin-bottom: 0.35rem;">GBIF y NOAA</h4>
              <p style="font-size: 0.78rem; color: #42474f; line-height: 1.45;">GBIF: base de datos mundial de registros de especies (de aquí salen los corales). NOAA: agencia de EE. UU. que mide la temperatura del mar por satélite.</p>
            </div>

          </div>
        </div>
      </section>

      <!-- ========================================== -->
      <!-- 4. CONTEXTO (#contexto)                    -->
      <!-- ========================================== -->
      <section class="section-py section-px" id="contexto">
        <div class="max-w-6xl container-base space-y-12">
          
          <div class="text-center max-w-3xl container-base">
            <h2 class="font-title text-primary" style="font-size: clamp(1.8rem, 3.5vw, 2.75rem); font-weight: 700; letter-spacing: -0.02em;">
              Contexto
            </h2>
          </div>

          <!-- 4a. Los arrecifes de Panamá y por qué importan -->
          <div class="glass-card p-8 md-p-10">
            <h3 class="font-title text-primary" style="font-size: clamp(1.3rem, 2.2vw, 1.75rem); font-weight: 700; margin-bottom: 1rem;">
              Los arrecifes de Panamá y por qué importan
            </h3>
            <p style="font-size: 0.95rem; color: #42474f; line-height: 1.65; margin-bottom: 1rem;">
              Panamá tiene unos 800 km² de arrecifes de coral, más del 97 % en el Caribe. Los arrecifes sostienen la pesca, porque cientos de especies de peces dependen de ellos; atraen turismo y protegen las costas de las olas. Con el calentamiento del mar, los corales pueden blanquearse y morir si el calor dura demasiado.
            </p>
            <p style="font-size: 0.95rem; color: #42474f; line-height: 1.65;">
              En 2026, además, se discutió en la Asamblea un proyecto de ley que modificaba la protección de los arrecifes (Ley 304 de 2022); el proyecto fue vetado por el Ejecutivo.
            </p>
          </div>

          <!-- 4b. El blanqueamiento -->
          <div class="glass-card p-8 md-p-10">
            <h3 class="font-title text-primary" style="font-size: clamp(1.3rem, 2.2vw, 1.75rem); font-weight: 700; margin-bottom: 1.25rem;">
              El blanqueamiento
            </h3>

            <!-- Fotos lado a lado -->
            <div class="grid grid-cols-1 md-grid-cols-2 gap-6" style="margin-bottom: 1.5rem;">
              <!-- Coral sano -->
              <div class="flex flex-col">
                <div class="relative rounded-2xl overflow-hidden" style="aspect-ratio: 4/3; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid rgba(255,255,255,0.7);">
                  <img alt="Coral sano" style="width: 100%; height: 100%; object-fit: cover;" src="{img['coral_sano']}">
                  <span style="position: absolute; top: 1rem; left: 1rem; padding: 0.3rem 0.85rem; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; background: #1FA7A6; color: white;">
                    Coral sano
                  </span>
                </div>
                <p style="font-size: 0.75rem; color: #737780; margin-top: 0.5rem; font-style: italic;">
                  Crédito: emilytrytten, iNaturalist (CC BY-NC 4.0), Bocas del Toro, Panamá, 17 de enero de 2026. <a style="color: #006a69; text-decoration: underline;" href="https://www.inaturalist.org/observations/403333743" target="_blank">ver observación</a>
                </p>
              </div>

              <!-- Coral blanqueado -->
              <div class="flex flex-col">
                <div class="relative rounded-2xl overflow-hidden" style="aspect-ratio: 4/3; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid rgba(255,255,255,0.7);">
                  <img alt="Coral blanqueado" style="width: 100%; height: 100%; object-fit: cover;" src="{img['coral_blanqueado']}">
                  <span style="position: absolute; top: 1rem; left: 1rem; padding: 0.3rem 0.85rem; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; background: #E75480; color: white;">
                    Coral blanqueado
                  </span>
                </div>
                <p style="font-size: 0.75rem; color: #737780; margin-top: 0.5rem; font-style: italic;">
                  Crédito: hubertszcz, iNaturalist (CC BY-NC 4.0), Bocas del Toro, Panamá, abril de 2022. <a style="color: #006a69; text-decoration: underline;" href="https://www.inaturalist.org/observations/116020823" target="_blank">ver observación</a>
                </p>
              </div>
            </div>

            <!-- Texto de 4b -->
            <p style="font-size: 0.95rem; color: #42474f; line-height: 1.65; margin-bottom: 1rem;">
              Cuando el mar se calienta más de lo normal durante semanas, el coral expulsa las algas que le dan color y alimento. Un coral blanqueado puede recuperarse si la temperatura vuelve a la normalidad, pero si el calor se prolonga, muere. NOAA mide este riesgo con una escala de 8 niveles:
            </p>

            <!-- Escala de 8 niveles de NOAA -->
            {escala_8_niveles_html}
          </div>

          <!-- 4c. El Niño y el calentamiento global -->
          <div class="glass-card p-8 md-p-10">
            <h3 class="font-title text-primary" style="font-size: clamp(1.3rem, 2.2vw, 1.75rem); font-weight: 700; margin-bottom: 1rem;">
              El Niño y el calentamiento global: una ola sobre la marea alta
            </h3>
            <p style="font-size: 0.95rem; color: #42474f; line-height: 1.65;">
              El Niño es un fenómeno natural: cada 2 a 7 años, el agua del Pacífico se calienta más de lo normal. El calentamiento global sube la temperatura base del mar, como una marea que sube. Por eso, cada El Niño ocurre sobre un mar más caliente que el anterior y llega más lejos, como una ola sobre la marea alta.
            </p>
          </div>

        </div>
      </section>

      <!-- ========================================== -->
      <!-- 5. LA PREGUNTA (#pregunta)                 -->
      <!-- ========================================== -->
      <section class="section-py section-px" id="pregunta">
        <div class="max-w-4xl container-base flex flex-col items-center text-center">
          
          <!-- Recuadro destacado con la pregunta -->
          <div class="glass-card text-center" style="width: 100%; padding: 2.5rem 2rem; margin-bottom: 2rem; border: 2px solid rgba(255,255,255,0.95); box-shadow: 0 16px 48px -8px rgba(14,21,94,0.14);">
            <div class="rounded-full flex items-center justify-center" style="width: 3rem; height: 3rem; background: #e0f2fe; color: #0D3B66; margin: 0 auto 1.25rem;">
              {ICONOS_SVG['help']}
            </div>
            <blockquote class="font-title text-primary" style="font-size: clamp(1.3rem, 2.5vw, 2rem); font-weight: 800; line-height: 1.35; letter-spacing: -0.015em;">
              “¿Cómo ha cambiado el estrés térmico en el Caribe y el Pacífico de Panamá desde 1985, y qué tan expuestos están los corales registrados en cada costa a un riesgo potencial de blanqueamiento?”
            </blockquote>
          </div>

          <!-- Dos tarjetas de fuentes de datos -->
          <div class="grid grid-cols-1 sm-grid-cols-2 gap-6" style="width: 100%; margin-bottom: 2rem;">
            <div class="glass-card p-6 text-left flex items-start gap-4">
              <div class="rounded-xl flex items-center justify-center shrink-0" style="width: 2.5rem; height: 2.5rem; background: #e6f7f7; color: #1FA7A6;">
                {ICONOS_SVG['bubble_chart']}
              </div>
              <div>
                <h4 class="font-title text-primary" style="font-size: 1.05rem; font-weight: bold;">GBIF</h4>
                <p style="font-size: 0.82rem; color: #42474f; margin-top: 0.35rem; line-height: 1.45;">
                  registros de corales en Panamá: especie, ubicación, profundidad y fecha.
                </p>
              </div>
            </div>

            <div class="glass-card p-6 text-left flex items-start gap-4">
              <div class="rounded-xl flex items-center justify-center shrink-0" style="width: 2.5rem; height: 2.5rem; background: #fff1f2; color: #E75480;">
                {ICONOS_SVG['satellite_alt']}
              </div>
              <div>
                <h4 class="font-title text-primary" style="font-size: 1.05rem; font-weight: bold;">NOAA Coral Reef Watch</h4>
                <p style="font-size: 0.82rem; color: #42474f; margin-top: 0.35rem; line-height: 1.45;">
                  temperatura diaria del mar desde 1985 en 4 estaciones virtuales (2 en el Caribe y 2 en el Pacífico).
                </p>
              </div>
            </div>
          </div>

          <!-- Cómo lo analizamos -->
          <div class="glass-card p-6 md-p-8 text-left" style="width: 100%;">
            <h4 class="font-title text-primary flex items-center gap-2" style="font-size: 1.05rem; font-weight: bold; margin-bottom: 0.5rem;">
              <span style="color: #006a69;">{ICONOS_SVG['tune']}</span>
              Cómo lo analizamos
            </h4>
            <p style="font-size: 0.9rem; color: #42474f; line-height: 1.6;">
              Al principio quisimos comparar los corales con la temperatura año por año, pero los registros de corales no lo permiten: casi todos son de un solo año (2002) y no hay registros con profundidad durante los El Niño más fuertes. Por eso unimos los datos <strong>por costa</strong>: la temperatura muestra cómo cambió el estrés térmico en cada costa, y los corales muestran qué especies viven ahí.
            </p>
          </div>

        </div>
      </section>

      <!-- ========================================== -->
      <!-- 6. ANÁLISIS: CUATRO HALLAZGOS (#analisis)  -->
      <!-- ========================================== -->
      <section class="section-py section-px" id="analisis">
        <div class="max-w-6xl container-base space-y-12">
          
          <div class="text-center max-w-3xl container-base" style="margin-bottom: 2.5rem;">
            <h2 class="font-title text-primary" style="font-size: clamp(1.8rem, 3.5vw, 2.75rem); font-weight: 700; letter-spacing: -0.02em;">
              Análisis: cuatro hallazgos
            </h2>
          </div>

          <!-- Hallazgo 1 -->
          <div class="glass-card p-8 md-p-10">
            <h3 class="font-title text-primary" style="font-size: clamp(1.2rem, 2vw, 1.6rem); font-weight: 700; margin-bottom: 1rem;">
              Hallazgo 1 · El mar de Panamá se ha calentado
            </h3>
            
            <p style="font-size: 0.95rem; color: #42474f; line-height: 1.65; margin-bottom: 1.5rem;">
              Hasta inicios de los 2000, la temperatura del mar estaba cerca de lo normal, e incluso hubo años más fríos. Desde 2002, todos los años han estado por encima de lo normal. Los picos coinciden con eventos de El Niño, pero cada pico es más alto que el anterior. En el Caribe, la anomalía promedio pasó de {m['anomalia_caribe_1980s']} °C en los años 80 a {m['anomalia_caribe_2020s']} °C en los años 2020; en el Pacífico, de {m['anomalia_pacifico_1980s']} °C a {m['anomalia_pacifico_2020s']} °C.
            </p>

            <div class="grid grid-cols-1 lg-grid-cols-12 gap-8 items-center">
              <div class="lg-col-4 rounded-2xl p-5" style="background: rgba(240, 249, 255, 0.7); border: 1px solid #e0f2fe;">
                <span class="font-title" style="font-size: 0.75rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.05em; color: #0D3B66; display: block; margin-bottom: 0.5rem;">
                  Anomalía promedio por década y costa
                </span>
                {tabla_decada_html}
              </div>
              <div class="lg-col-8 rounded-2xl p-4 flex items-center justify-center" style="background: rgba(247, 251, 253, 0.9); border: 1px solid rgba(224, 242, 254, 0.7);">
                {g['svg_grafica1']}
              </div>
            </div>
          </div>

          <!-- Hallazgo 2 -->
          <div class="glass-card p-8 md-p-10">
            <h3 class="font-title text-primary" style="font-size: clamp(1.2rem, 2vw, 1.6rem); font-weight: 700; margin-bottom: 1rem;">
              Hallazgo 2 · El estrés extremo pasó de ser una excepción a ser lo normal
            </h3>

            <p style="font-size: 0.95rem; color: #42474f; line-height: 1.65; margin-bottom: 1.5rem;">
              Durante las primeras tres décadas predomina el nivel 2 (Advertencia), y los años con niveles altos son pocos y coinciden con eventos de El Niño, como 1997-98. Desde 2015 el patrón cambia: los niveles 4 o superiores aparecen casi todos los años en al menos una costa. De los {m['casos_nivel5']} casos (costa-año) con nivel 5 o superior, {m['casos_nivel5_desde_2016']} ocurrieron desde 2016. {m['frase_nivel7']}
            </p>

            <div class="rounded-2xl p-5 overflow-x-auto" style="background: rgba(247, 251, 253, 0.9); border: 1px solid rgba(224, 242, 254, 0.7);">
              {g['svg_grafica2']}
            </div>
          </div>

          <!-- Hallazgo 3 -->
          <div class="glass-card p-8 md-p-10">
            <h3 class="font-title text-primary" style="font-size: clamp(1.2rem, 2vw, 1.6rem); font-weight: 700; margin-bottom: 1.25rem;">
              Hallazgo 3 · Cada costa tiene corales únicos
            </h3>

            <!-- Tres tarjetas KPI -->
            <div class="grid grid-cols-1 sm-grid-cols-3 gap-4" style="margin-bottom: 1.5rem;">
              <div class="rounded-xl p-4 text-center" style="background: rgba(230, 247, 247, 0.85); border: 1px solid rgba(31, 167, 166, 0.25);">
                <span style="font-size: 0.75rem; color: #737780; font-weight: 600; display: block;">Especies en el Caribe</span>
                <span class="font-title" style="font-size: 2rem; font-weight: 800; color: #1FA7A6;">{m['especies_caribe']}</span>
              </div>
              <div class="rounded-xl p-4 text-center" style="background: rgba(255, 241, 242, 0.85); border: 1px solid rgba(231, 84, 128, 0.25);">
                <span style="font-size: 0.75rem; color: #737780; font-weight: 600; display: block;">Especies en el Pacífico</span>
                <span class="font-title" style="font-size: 2rem; font-weight: 800; color: #E75480;">{m['especies_pacifico']}</span>
              </div>
              <div class="rounded-xl p-4 text-center" style="background: rgba(250, 245, 255, 0.85); border: 1px solid rgba(108, 46, 123, 0.25);">
                <span style="font-size: 0.75rem; color: #737780; font-weight: 600; display: block;">Especies compartidas</span>
                <span class="font-title" style="font-size: 2rem; font-weight: 800; color: #6C2E7B;">{m['especies_compartidas']}</span>
              </div>
            </div>

            <p style="font-size: 0.95rem; color: #42474f; line-height: 1.65; margin-bottom: 1.5rem;">
              Las {m['especies_caribe']} especies de coral registradas en el Caribe y las {m['especies_pacifico']} del Pacífico no se comparten entre sí. Desde que el istmo de Panamá se cerró, hace unos 3 millones de años, los corales de cada océano evolucionaron por separado. Por eso, si se pierde un arrecife, sus especies no se encuentran en la otra costa.
            </p>

            <div class="rounded-2xl p-5" style="background: rgba(247, 251, 253, 0.9); border: 1px solid rgba(224, 242, 254, 0.7);">
              {g['svg_grafica3']}
            </div>
          </div>

          <!-- Hallazgo 4 -->
          <div class="glass-card p-8 md-p-10">
            <h3 class="font-title text-primary" style="font-size: clamp(1.2rem, 2vw, 1.6rem); font-weight: 700; margin-bottom: 1rem;">
              Hallazgo 4 · Los corales pasan casi dos meses al año en riesgo
            </h3>

            <p style="font-size: 0.95rem; color: #42474f; line-height: 1.65; margin-bottom: 1.5rem;">
              Los días al año en nivel 4 de alerta o superior (mortalidad probable) aumentaron en ambas costas. En el Caribe pasaron de {m['dias_caribe_antes']} a {m['dias_caribe_ahora']} días al año; en el Pacífico, de {m['dias_pacifico_antes']} a {m['dias_pacifico_ahora']}. Lo que antes era un par de días hoy dura casi dos meses, y un coral blanqueado no suele resistir tanto tiempo.
            </p>

            <div class="rounded-2xl p-5" style="background: rgba(247, 251, 253, 0.9); border: 1px solid rgba(224, 242, 254, 0.7);">
              {g['svg_grafica4']}
            </div>
          </div>

        </div>
      </section>

      <!-- ========================================== -->
      <!-- 7. ¿CÓMO VA 2026?                          -->
      <!-- ========================================== -->
      <section class="section-py section-px" id="actual">
        <div class="max-w-6xl container-base space-y-8">
          
          <div class="text-center max-w-3xl container-base" style="margin-bottom: 2rem;">
            <h2 class="font-title text-primary" style="font-size: clamp(1.8rem, 3.5vw, 2.75rem); font-weight: 700; letter-spacing: -0.02em;">
              ¿Cómo va 2026?
            </h2>
          </div>

          <!-- Tarjetas KPI por costa -->
          <div class="space-y-6">
            
            <!-- Fila Caribe -->
            <div>
              <div class="flex items-center gap-2" style="margin-bottom: 0.75rem;">
                <span style="color: #1FA7A6;">{ICONOS_SVG['waves']}</span>
                <span class="font-title" style="font-size: 0.85rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.05em; color: #1FA7A6;">Mar Caribe</span>
              </div>
              <div class="grid grid-cols-1 md-grid-cols-3 gap-6">
                <div class="glass-card p-6 flex flex-col justify-between">
                  <div>
                    <p style="font-size: 0.75rem; text-transform: uppercase; font-weight: bold; letter-spacing: 0.05em; color: #737780;">Anomalía promedio de 2026</p>
                    <h3 class="font-title text-primary" style="font-size: 2.25rem; font-weight: 800; margin: 0.5rem 0;">{m['datos_2026']['Caribe']['anomalia_2026']} °C</h3>
                  </div>
                </div>

                <div class="glass-card p-6 flex flex-col justify-between">
                  <div>
                    <p style="font-size: 0.75rem; text-transform: uppercase; font-weight: bold; letter-spacing: 0.05em; color: #737780;">Días en nivel 4 o superior en 2026</p>
                    <h3 class="font-title text-primary" style="font-size: 2.25rem; font-weight: 800; margin: 0.5rem 0;">{m['datos_2026']['Caribe']['dias_2026']}</h3>
                  </div>
                  <p style="font-size: 0.75rem; color: #42474f; font-weight: 500; padding-top: 0.5rem; border-top: 1px solid #e0f2fe;">Días con riesgo de mortalidad probable o mayor</p>
                </div>

                <div class="glass-card p-6 flex flex-col justify-between">
                  <div>
                    <p style="font-size: 0.75rem; text-transform: uppercase; font-weight: bold; letter-spacing: 0.05em; color: #737780;">Nivel máximo alcanzado en 2026</p>
                    <div style="margin: 0.5rem 0;">
                      <span style="display: inline-block; padding: 0.35rem 0.85rem; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; color: white; background-color: {m['datos_2026']['Caribe']['color_nivel']};">
                        Nivel {m['datos_2026']['Caribe']['nivel_max_2026']} · {m['datos_2026']['Caribe']['nombre_nivel']}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Fila Pacífico -->
            <div>
              <div class="flex items-center gap-2" style="margin-bottom: 0.75rem;">
                <span style="color: #E75480;">{ICONOS_SVG['tsunami']}</span>
                <span class="font-title" style="font-size: 0.85rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.05em; color: #E75480;">Océano Pacífico</span>
              </div>
              <div class="grid grid-cols-1 md-grid-cols-3 gap-6">
                <div class="glass-card p-6 flex flex-col justify-between">
                  <div>
                    <p style="font-size: 0.75rem; text-transform: uppercase; font-weight: bold; letter-spacing: 0.05em; color: #737780;">Anomalía promedio de 2026</p>
                    <h3 class="font-title text-primary" style="font-size: 2.25rem; font-weight: 800; margin: 0.5rem 0;">{m['datos_2026']['Pacífico']['anomalia_2026']} °C</h3>
                  </div>
                </div>

                <div class="glass-card p-6 flex flex-col justify-between">
                  <div>
                    <p style="font-size: 0.75rem; text-transform: uppercase; font-weight: bold; letter-spacing: 0.05em; color: #737780;">Días en nivel 4 o superior en 2026</p>
                    <h3 class="font-title text-primary" style="font-size: 2.25rem; font-weight: 800; margin: 0.5rem 0;">{m['datos_2026']['Pacífico']['dias_2026']}</h3>
                  </div>
                  <p style="font-size: 0.75rem; color: #42474f; font-weight: 500; padding-top: 0.5rem; border-top: 1px solid #e0f2fe;">Días con riesgo de mortalidad probable o mayor</p>
                </div>

                <div class="glass-card p-6 flex flex-col justify-between">
                  <div>
                    <p style="font-size: 0.75rem; text-transform: uppercase; font-weight: bold; letter-spacing: 0.05em; color: #737780;">Nivel máximo alcanzado en 2026</p>
                    <div style="margin: 0.5rem 0;">
                      <span style="display: inline-block; padding: 0.35rem 0.85rem; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; color: white; background-color: {m['datos_2026']['Pacífico']['color_nivel']};">
                        Nivel {m['datos_2026']['Pacífico']['nivel_max_2026']} · {m['datos_2026']['Pacífico']['nombre_nivel']}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>

          <!-- Texto descriptivo de 2026 -->
          <div class="glass-card p-8 md-p-10">
            <p style="font-size: 0.95rem; color: #42474f; line-height: 1.65;">
              Con datos hasta el {m['fecha_ultimo_dato']} (último dato publicado por NOAA), 2026 ya es un año de estrés térmico extremo, sobre todo en el Pacífico. Según NOAA (actualización del 8 de octubre de 2026), El Niño sigue fortaleciéndose, con un 83 % de probabilidad de ser el más fuerte desde 1950 entre octubre y diciembre, y se espera que dure hasta inicios de 2027. Como los meses que faltan coinciden con el pico de El Niño, es poco probable que la situación mejore antes de terminar el año. Además, en los datos el Caribe suele tener su peor año justo después de un El Niño, por lo que 2027 podría ser también un año de alto riesgo para sus corales.
            </p>
          </div>

        </div>
      </section>

      <!-- ========================================== -->
      <!-- 8. CONCLUSIÓN (#conclusion)                -->
      <!-- ========================================== -->
      <section class="section-py section-px text-white relative overflow-hidden" id="conclusion" style="background: linear-gradient(180deg, rgba(227, 244, 248, 0.3) 0%, rgba(14, 21, 94, 0.9) 15%, rgba(14, 21, 94, 0.98) 100%);">
        
        <!-- Líneas batimétricas sutiles -->
        <div style="position: absolute; inset: 0; pointer-events: none; opacity: 0.15;">
          <svg style="width: 100%; height: 100%;" xmlns="http://www.w3.org/2000/svg">
            <path d="M 0 100 Q 300 180 600 80 T 1200 150 T 1800 100" fill="none" opacity="0.3" stroke="#80f5f3" stroke-width="1.5"></path>
            <path d="M 0 300 Q 400 240 800 350 T 1600 280" fill="none" opacity="0.2" stroke="#80f5f3" stroke-width="1"></path>
          </svg>
        </div>

        <div class="max-w-4xl container-base flex flex-col items-center text-center space-y-8 relative">
          <h2 class="font-title text-white" style="color: #FFFFFF; font-size: clamp(2rem, 4vw, 3rem); font-weight: 800; letter-spacing: -0.02em;">
            Conclusión
          </h2>

          <div class="glass-card text-left" style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(128, 245, 243, 0.2); box-shadow: 0 20px 48px rgba(0,0,0,0.4); padding: clamp(1.5rem, 3vw, 2.75rem); width: 100%;">
            <p style="font-size: 1rem; color: #e2e8f0; line-height: 1.7; margin-bottom: 1.25rem;">
              Los datos muestran una vulnerabilidad clara en nuestros océanos. El calentamiento del mar en Panamá es evidente y avanza con o sin El Niño: desde 2002, ningún año ha estado por debajo de lo normal, y cada evento llega a temperaturas más altas que el anterior.
            </p>
            <p style="font-size: 1rem; color: #e2e8f0; line-height: 1.7; margin-bottom: 1.25rem;">
              El estrés térmico ya no es una excepción. En los últimos años, ambas costas alcanzan cada año el nivel 4 de alerta o superior, y los días en riesgo pasaron de un par a casi dos meses al año. Un coral blanqueado puede recuperarse si el calor baja a tiempo, pero el estrés prolongado puede causar su muerte. Además, cada costa tiene corales únicos: lo que se pierde en una no se recupera con la otra.
            </p>
            <p style="font-size: 1rem; color: #e2e8f0; line-height: 1.7; margin-bottom: 1.25rem;">
              Lo positivo es que cada vez más personas, entre científicos y aficionados, registran corales en plataformas abiertas. Estas iniciativas podrían ampliarse, por ejemplo anotando la profundidad, para medir el impacto del El Niño actual y de los que vengan.
            </p>
            <p style="font-size: 1rem; color: #e2e8f0; line-height: 1.7; margin-bottom: 1.75rem;">
              Aunque este estudio se enfoca en los corales, todo está conectado: los arrecifes son el hogar y la zona de crianza de cientos de especies de peces, sostienen la pesca y el turismo de comunidades costeras, y protegen nuestras costas del oleaje. Por eso, como ciudadanos, debemos estar atentos a cómo se toman las decisiones sobre la protección de nuestros océanos.
            </p>

            <div class="text-center" style="padding-top: 1.5rem; border-top: 1px solid rgba(128, 245, 243, 0.25);">
              <blockquote class="font-title" style="font-size: clamp(1.2rem, 2.2vw, 1.75rem); font-weight: bold; color: #FF8A5B; line-height: 1.4;">
                “Los datos abiertos nos permiten ver lo que está pasando; lo que hagamos con esa información depende de todos.”
              </blockquote>
            </div>
          </div>
        </div>
      </section>

      <!-- ========================================== -->
      <!-- 9. PIE: LIMITACIONES Y FUENTES             -->
      <!-- ========================================== -->
      <footer class="section-px" style="padding-top: 4rem; padding-bottom: 4rem; background-color: rgba(14, 21, 94, 0.98); color: white;">
        <div class="max-w-6xl container-base grid grid-cols-1 md-grid-cols-2 gap-12" style="font-size: 0.85rem;">
          
          <!-- Limitaciones -->
          <div class="space-y-4">
            <div class="flex items-center gap-2" style="color: #FFC857;">
              {ICONOS_SVG['info']}
              <h4 class="font-title" style="font-weight: bold; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.05em;">Limitaciones</h4>
            </div>
            <ul style="list-style: none; padding-left: 0; display: flex; flex-direction: column; gap: 0.65rem; color: #cbd5e1; font-size: 0.78rem; line-height: 1.55;">
              <li class="flex items-start gap-2">
                <span style="width: 0.35rem; height: 0.35rem; border-radius: 9999px; background: #FF8A5B; margin-top: 0.45rem; shrink: 0;"></span>
                <span><strong>Presencia, no abundancia:</strong> los registros de GBIF indican que un coral fue visto en un lugar, no cuántos corales hay ni si están sanos.</span>
              </li>
              <li class="flex items-start gap-2">
                <span style="width: 0.35rem; height: 0.35rem; border-radius: 9999px; background: #FF8A5B; margin-top: 0.45rem; shrink: 0;"></span>
                <span><strong>Sesgo de muestreo:</strong> el 95 % de los registros con año corresponde a 2002 (monitoreo de AGRRA en el Caribe), y no hay registros con profundidad anotada durante los El Niño más fuertes. Por eso no se pudo comparar año por año.</span>
              </li>
              <li class="flex items-start gap-2">
                <span style="width: 0.35rem; height: 0.35rem; border-radius: 9999px; background: #FF8A5B; margin-top: 0.45rem; shrink: 0;"></span>
                <span><strong>Pocos datos del Pacífico:</strong> el 61 % de sus registros no tiene profundidad y se excluyó; su diversidad podría estar subestimada.</span>
              </li>
              <li class="flex items-start gap-2">
                <span style="width: 0.35rem; height: 0.35rem; border-radius: 9999px; background: #FF8A5B; margin-top: 0.45rem; shrink: 0;"></span>
                <span><strong>NOAA estima el riesgo, no lo mide:</strong> los niveles de alerta indican la probabilidad de blanqueamiento según la temperatura, no observaciones reales de corales blanqueados.</span>
              </li>
              <li class="flex items-start gap-2">
                <span style="width: 0.35rem; height: 0.35rem; border-radius: 9999px; background: #FF8A5B; margin-top: 0.45rem; shrink: 0;"></span>
                <span><strong>Las estaciones son áreas grandes:</strong> cada costa se representa con 2 estaciones virtuales, que pueden no reflejar las condiciones exactas de cada arrecife.</span>
              </li>
              <li class="flex items-start gap-2">
                <span style="width: 0.35rem; height: 0.35rem; border-radius: 9999px; background: #FF8A5B; margin-top: 0.45rem; shrink: 0;"></span>
                <span><strong>El año actual está incompleto:</strong> se excluye de los promedios anuales y por década.</span>
              </li>
            </ul>
          </div>

          <!-- Fuentes -->
          <div class="space-y-4">
            <div class="flex items-center gap-2" style="color: #80f5f3;">
              {ICONOS_SVG['menu_book']}
              <h4 class="font-title" style="font-weight: bold; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.05em;">Fuentes</h4>
            </div>
            <ul style="list-style: none; padding-left: 0; display: flex; flex-direction: column; gap: 0.65rem; color: #cbd5e1; font-size: 0.78rem; line-height: 1.55;">
              <li class="flex items-start gap-2">
                <span style="width: 0.35rem; height: 0.35rem; border-radius: 9999px; background: #1FA7A6; margin-top: 0.45rem; shrink: 0;"></span>
                <span>Corales: GBIF, descarga 0041553-260928105237408.</span>
              </li>{fuente_contorno_html}
              <li class="flex items-start gap-2">
                <span style="width: 0.35rem; height: 0.35rem; border-radius: 9999px; background: #1FA7A6; margin-top: 0.45rem; shrink: 0;"></span>
                <span>Temperatura: NOAA Coral Reef Watch, 5 km Regional Virtual Stations v3.1.</span>
              </li>
              <li class="flex items-start gap-2">
                <span style="width: 0.35rem; height: 0.35rem; border-radius: 9999px; background: #1FA7A6; margin-top: 0.45rem; shrink: 0;"></span>
                <span>Estado de El Niño: NOAA Climate Prediction Center, ENSO Diagnostic Discussion (8 de octubre de 2026).</span>
              </li>
              <li class="flex items-start gap-2">
                <span style="width: 0.35rem; height: 0.35rem; border-radius: 9999px; background: #1FA7A6; margin-top: 0.45rem; shrink: 0;"></span>
                <span>Arrecifes de Panamá y proyecto de ley: La Prensa, La Estrella de Panamá y Panamá América (2025-2026).</span>
              </li>
              <li class="flex items-start gap-2">
                <span style="width: 0.35rem; height: 0.35rem; border-radius: 9999px; background: #1FA7A6; margin-top: 0.45rem; shrink: 0;"></span>
                <span>Foto de coral blanqueado: hubertszcz, iNaturalist (CC BY-NC 4.0), Bocas del Toro, Panamá, abril de 2022. <a style="color: #80f5f3; text-decoration: underline;" href="https://www.inaturalist.org/observations/116020823" target="_blank">ver observación</a></span>
              </li>
              <li class="flex items-start gap-2">
                <span style="width: 0.35rem; height: 0.35rem; border-radius: 9999px; background: #1FA7A6; margin-top: 0.45rem; shrink: 0;"></span>
                <span>Foto de coral sano: emilytrytten, iNaturalist (CC BY-NC 4.0), Bocas del Toro, Panamá, 17 de enero de 2026. <a style="color: #80f5f3; text-decoration: underline;" href="https://www.inaturalist.org/observations/403333743" target="_blank">ver observación</a></span>
              </li>
            </ul>
          </div>

        </div>

        <!-- Copyright final -->
        <div class="max-w-6xl container-base flex flex-col sm-flex-row items-center justify-between gap-2" style="margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid rgba(71, 85, 105, 0.5); font-size: 0.72rem; color: #94a3b8;">
          <div class="flex items-center gap-2">
            <img alt="Logo Corales" class="rounded-full" style="width: 1rem; height: 1rem; opacity: 0.7;" src="{img['logo_corales']}">
            <p>© Corales de Panamá · Angela Pérez &amp; Edwin De Frías · UIP</p>
          </div>
        </div>
      </footer>

    </div>
  </main>

</body>
</html>
"""
    return html


def guardar_archivo_atomico(ruta_destino, contenido_texto):
    """Escribe el contenido primero en un archivo temporal y lo reemplaza atómicamente con os.replace."""
    ruta_destino = Path(ruta_destino)
    ruta_destino.parent.mkdir(parents=True, exist_ok=True)
    ruta_temporal = ruta_destino.with_suffix(ruta_destino.suffix + ".tmp")
    
    with open(ruta_temporal, "w", encoding="utf-8") as archivo:
        archivo.write(contenido_texto)
        
    os.replace(ruta_temporal, ruta_destino)
    print(f">> Dashboard generado con éxito en: {ruta_destino.resolve()}")


def imprimir_tabla_metricas(metricas):
    """Muestra una tabla con todos los números calculados dinámicamente."""
    m = metricas
    print("\n" + "=" * 80)
    print("TABLA DE VARIABLES CALCULADAS DESDE LOS CSV (contenido.md)")
    print("=" * 80)
    print(f"{'Variable en contenido.md':<32} | {'Costa / Contexto':<18} | {'Valor Calculado':<24}")
    print("-" * 80)
    print(f"{'{fecha_generacion}':<32} | {'General':<18} | {m['fecha_generacion']:<24}")
    print(f"{'{fecha_ultimo_dato}':<32} | {'General':<18} | {m['fecha_ultimo_dato']:<24}")
    print("-" * 80)
    print(f"{'{temp_hoy}':<32} | {'Caribe':<18} | {m['mar_hoy']['Caribe']['temp_hoy'] + ' °C':<24}")
    print(f"{'{cambio}':<32} | {'Caribe':<18} | {m['mar_hoy']['Caribe']['cambio'] + ' °C':<24}")
    print(f"{'{anomalia_hoy}':<32} | {'Caribe':<18} | {m['mar_hoy']['Caribe']['anomalia_hoy'] + ' °C':<24}")
    print(f"{'{nivel}':<32} | {'Caribe':<18} | {str(m['mar_hoy']['Caribe']['nivel']):<24}")
    print(f"{'{nombre_nivel}':<32} | {'Caribe':<18} | {m['mar_hoy']['Caribe']['nombre_nivel']:<24}")
    print("-" * 80)
    print(f"{'{temp_hoy}':<32} | {'Pacífico':<18} | {m['mar_hoy']['Pacífico']['temp_hoy'] + ' °C':<24}")
    print(f"{'{cambio}':<32} | {'Pacífico':<18} | {m['mar_hoy']['Pacífico']['cambio'] + ' °C':<24}")
    print(f"{'{anomalia_hoy}':<32} | {'Pacífico':<18} | {m['mar_hoy']['Pacífico']['anomalia_hoy'] + ' °C':<24}")
    print(f"{'{nivel}':<32} | {'Pacífico':<18} | {str(m['mar_hoy']['Pacífico']['nivel']):<24}")
    print(f"{'{nombre_nivel}':<32} | {'Pacífico':<18} | {m['mar_hoy']['Pacífico']['nombre_nivel']:<24}")
    print("-" * 80)
    print(f"{'{anomalia_caribe_1980s}':<32} | {'Caribe (1980s)':<18} | {m['anomalia_caribe_1980s'] + ' °C':<24}")
    print(f"{'{anomalia_caribe_2020s}':<32} | {'Caribe (2020s)':<18} | {m['anomalia_caribe_2020s'] + ' °C':<24}")
    print(f"{'{anomalia_pacifico_1980s}':<32} | {'Pacífico (1980s)':<18} | {m['anomalia_pacifico_1980s'] + ' °C':<24}")
    print(f"{'{anomalia_pacifico_2020s}':<32} | {'Pacífico (2020s)':<18} | {m['anomalia_pacifico_2020s'] + ' °C':<24}")
    print("-" * 80)
    print(f"{'{casos_nivel5}':<32} | {'Histórico':<18} | {str(m['casos_nivel5']):<24}")
    print(f"{'{casos_nivel5_desde_2016}':<32} | {'Desde 2016':<18} | {str(m['casos_nivel5_desde_2016']):<24}")
    print("-" * 80)
    print(f"{'{especies_caribe}':<32} | {'Caribe':<18} | {str(m['especies_caribe']):<24}")
    print(f"{'{especies_pacifico}':<32} | {'Pacífico':<18} | {str(m['especies_pacifico']):<24}")
    print(f"{'{especies_compartidas}':<32} | {'Ambas costas':<18} | {str(m['especies_compartidas']):<24}")
    print("-" * 80)
    print(f"{'{dias_caribe_antes}':<32} | {'Caribe (1985-2014)':<18} | {m['dias_caribe_antes'] + ' días':<24}")
    print(f"{'{dias_caribe_ahora}':<32} | {'Caribe (2015-2025)':<18} | {m['dias_caribe_ahora'] + ' días':<24}")
    print(f"{'{dias_pacifico_antes}':<32} | {'Pacífico (1985-2014)':<18} | {m['dias_pacifico_antes'] + ' días':<24}")
    print(f"{'{dias_pacifico_ahora}':<32} | {'Pacífico (2015-2025)':<18} | {m['dias_pacifico_ahora'] + ' días':<24}")
    print("-" * 80)
    print(f"{'{anomalia_2026}':<32} | {'Caribe (2026)':<18} | {m['datos_2026']['Caribe']['anomalia_2026'] + ' °C':<24}")
    print(f"{'{dias_2026}':<32} | {'Caribe (2026)':<18} | {str(m['datos_2026']['Caribe']['dias_2026']) + ' días':<24}")
    print(f"{'{nivel_max_2026}':<32} | {'Caribe (2026)':<18} | {str(m['datos_2026']['Caribe']['nivel_max_2026']) + ' · ' + m['datos_2026']['Caribe']['nombre_nivel']:<24}")
    print(f"{'{anomalia_2026}':<32} | {'Pacífico (2026)':<18} | {m['datos_2026']['Pacífico']['anomalia_2026'] + ' °C':<24}")
    print(f"{'{dias_2026}':<32} | {'Pacífico (2026)':<18} | {str(m['datos_2026']['Pacífico']['dias_2026']) + ' días':<24}")
    print(f"{'{nivel_max_2026}':<32} | {'Pacífico (2026)':<18} | {str(m['datos_2026']['Pacífico']['nivel_max_2026']) + ' · ' + m['datos_2026']['Pacífico']['nombre_nivel']:<24}")
    print("=" * 80 + "\n")


def main():
    print(">> Iniciando generación del dashboard de Corales de Panamá...")
    
    # 1. Calcular métricas desde los archivos CSV
    print(">> Leyendo archivos CSV y calculando métricas...")
    metricas = calcular_metricas()
    
    # 2. Generar gráficas en SVG con matplotlib
    print(">> Generando gráficas vectoriales en SVG con matplotlib...")
    graficas = generar_graficas_svg(metricas)
    
    # 3. Codificar imágenes en Base64
    print(">> Incrustando imágenes en Base64...")
    imagenes = {
        "logo_uip": codificar_imagen_base64("logo uip.png"),
        "logo_corales": codificar_imagen_base64("logo_corales.png"),
        "fondo_burbujas": codificar_imagen_base64("fondo_burbujas.jpg"),
        "fondo_agua": codificar_imagen_base64("fondo_agua.jpg"),
        "coral_sano": codificar_imagen_base64("coral_sano.jpg"),
        "coral_blanqueado": codificar_imagen_base64("coral_blanqueado.jpg"),
    }
    
    # 4. Construir HTML
    print(">> Ensamblando documento HTML con estilos y componentes...")
    contenido_html = construir_html_dashboard(metricas, graficas, imagenes)
    
    # 5. Guardar atómicamente en dashboard/index.html
    ruta_salida = DIRECTORIO_RAIZ / "dashboard" / "index.html"
    guardar_archivo_atomico(ruta_salida, contenido_html)
    
    # 6. Mostrar tabla de verificación
    imprimir_tabla_metricas(metricas)


if __name__ == "__main__":
    main()
