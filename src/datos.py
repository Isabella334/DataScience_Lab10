"""Carga y filtrado de datos compartidos por todas las visualizaciones."""
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
PARQUET = RAIZ / "data" / "processed" / "viajeros.parquet"

# Etiquetas legibles para el usuario (nombre de columna -> texto en la interfaz)
ETIQUETAS = {
    "total": "Total",
    "region": "Región de residencia",
    "via": "Vía de ingreso",
    "tipo_viajero": "Tipo de viajero",
    "frontera": "Punto de ingreso",
}


@st.cache_data(show_spinner="Cargando datos…")
def cargar_datos() -> pd.DataFrame:
    if not PARQUET.exists():
        # Primera ejecución: genera el parquet desde el Excel original
        from data.procesar_datos import procesar  # noqa: WPS433
        PARQUET.parent.mkdir(parents=True, exist_ok=True)
        procesar().to_parquet(PARQUET, index=False)
    return pd.read_parquet(PARQUET)


def aplicar_filtros(df: pd.DataFrame, filtros: dict) -> pd.DataFrame:
    """Aplica los filtros globales de la barra lateral."""
    anio_ini, anio_fin = filtros["anios"]
    mask = df["anio"].between(anio_ini, anio_fin)
    for col in ("region", "via", "tipo_viajero"):
        seleccion = filtros.get(col)
        if seleccion:
            mask &= df[col].isin(seleccion)
    return df[mask]


def formato_num(n: float) -> str:
    """12345678 -> '12.3 M', 45200 -> '45.2 mil'."""
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f} M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:.1f} mil"
    return f"{n:,.0f}"
