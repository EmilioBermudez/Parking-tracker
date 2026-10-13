import os
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

URL_OCC = "https://data.lacity.org/resource/e7h6-4a3e.json?$limit=5000"
URL_INV = "https://data.lacity.org/resource/s49e-q6j2.json?$limit=50000"

os.makedirs("data", exist_ok=True)

inv = pd.read_json(URL_INV)
inv['latitude'] = inv['latlng'].apply(lambda x: float(x['latitude']) if pd.notnull(x) else None)
inv['longitude'] = inv['latlng'].apply(lambda x: float(x['longitude']) if pd.notnull(x) else None)
inv = inv[['spaceid', 'blockface', 'latitude', 'longitude']].drop_duplicates('spaceid')

# Coordenadas de cada cuadra: se guardan una sola vez
if not os.path.exists("data/bloques.csv"):
    (inv.groupby('blockface')
        .agg(lat=('latitude', 'mean'), lng=('longitude', 'mean'))
        .reset_index()
        .to_csv("data/bloques.csv", index=False))

occ = pd.read_json(URL_OCC)
m = occ.merge(inv, on='spaceid', how='inner')
m = m[m['occupancystate'] != 'UNKNOWN']

resumen = m.groupby('blockface').agg(
    total=('spaceid', 'count'),
    ocupados=('occupancystate', lambda s: (s == 'OCCUPIED').sum())
).reset_index()
resumen['tasa_ocupacion'] = (resumen['ocupados'] / resumen['total']).round(3)

ahora = datetime.now(ZoneInfo("America/Los_Angeles"))
resumen['timestamp'] = ahora.strftime("%Y-%m-%d %H:%M")

archivo = f"data/historico_{ahora:%Y-%m-%d}.csv"
resumen.to_csv(archivo, mode='a', header=not os.path.exists(archivo), index=False)
print("Guardado:", archivo, "| cuadras:", len(resumen))
