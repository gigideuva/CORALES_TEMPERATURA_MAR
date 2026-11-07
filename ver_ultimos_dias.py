import pandas as pd

temperatura = pd.read_csv("datos/limpios/temperatura_limpio.csv", parse_dates=["fecha"])

ultima_fecha = temperatura["fecha"].max()
print("Último dato de NOAA:", ultima_fecha.date())

# Los últimos 3 días
ultimos = temperatura[temperatura["fecha"] > ultima_fecha - pd.Timedelta(days=3)]

# Por día y costa: la temperatura y la alerta más altas de sus 2 estaciones
tabla = ultimos.pivot_table(index="fecha", columns="costa",
                            values=["sst_90", "alerta"], aggfunc="max")
print(tabla)
