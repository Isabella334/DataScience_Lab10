"""
Limpieza base del dataset de ingreso de viajeros (Labs 1 y 2).

Lee el Excel original y genera data/processed/viajeros.parquet con nombres de
columna sin tildes ni espacios. La Persona 4 puede ampliar esta limpieza; la app
solo depende de las columnas listadas en COLUMNAS.

Uso:  python data/procesar_datos.py
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent
ORIGEN = RAIZ / "raw" / "base_migracion_2009_2026jun.xlsx"
DESTINO = RAIZ / "processed" / "viajeros.parquet"

COLUMNAS = {
    "Año": "anio",
    "Mes cod": "mes",
    "Mes": "mes_nombre",
    "Vía": "via",
    "Frontera": "frontera",
    "País": "pais",
    "Región": "region_detalle",
    "Región dos": "region",
    "Regiones OMT": "region_omt",
    "MCEO": "mceo",
    "Agrupación Residencia": "agrupacion_residencia",
    "Tipo de Viajero": "tipo_viajero",
    "Viajero": "viajeros",
}


def procesar() -> pd.DataFrame:
    df = pd.read_excel(ORIGEN, sheet_name="Datos").rename(columns=COLUMNAS)

    # Regiones: unificar cruceros y marcar los registros sin región
    df["region"] = (
        df["region"].astype(str).str.strip()
        .replace({"Cruceristas": "Cruceros", "0": "Sin dato"})
        .str.replace("Paises", "Países")
    )
    df["frontera"] = df["frontera"].astype(str).str.replace(r"^\d+\s+", "", regex=True)
    df["fecha"] = pd.to_datetime(dict(year=df["anio"], month=df["mes"], day=1))
    df["viajeros"] = pd.to_numeric(df["viajeros"], errors="coerce").fillna(0).astype("int64")

    for col in ["via", "frontera", "pais", "region", "region_omt", "tipo_viajero", "agrupacion_residencia"]:
        df[col] = df[col].astype("category")
    return df


if __name__ == "__main__":
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    datos = procesar()
    datos.to_parquet(DESTINO, index=False)
    print(f"{len(datos):,} filas -> {DESTINO}")
