"""Carga y filtrado de datos compartidos por todas las visualizaciones."""
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
PARQUET = RAIZ / "data" / "processed" / "viajeros.parquet"
PREDICCIONES = RAIZ / "data" / "processed" / "predicciones.parquet"
METRICAS = RAIZ / "data" / "processed" / "metricas.parquet"

# Visitantes comparables en toda la serie ("Viajero" cambia de definición entre 2022 y 2023)
VISITANTES = ("Turista", "Excursionista")
ORDEN_VIAS = ("Terrestre", "Aérea", "Marítima")

# Series con modelos del Lab 1 y nombres de los modelos (deben coincidir con los parquet de modelos)
SERIES_MODELO = (
    "Total", "América del Centro", "América del Norte", "Europa",
    "El Salvador", "Estados Unidos", "Honduras",
)
MODELOS = ("Prophet", "SARIMA", "Holt-Winters", "Suavizamiento exponencial simple", "Seasonal naive")

# Etiquetas legibles para el usuario (nombre de columna -> texto en la interfaz)
ETIQUETAS = {
    "total": "Total",
    "region": "Región de residencia",
    "via": "Vía de ingreso",
    "tipo_viajero": "Tipo de viajero",
    "frontera": "Punto de ingreso",
}

_MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
_MESES_LARGOS = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
                 "octubre", "noviembre", "diciembre")


@st.cache_data(show_spinner="Cargando datos…")
def cargar_datos() -> pd.DataFrame:
    if not PARQUET.exists():
        # Primera ejecución: genera el parquet desde el Excel original
        from data.procesar_datos import procesar  # noqa: WPS433
        PARQUET.parent.mkdir(parents=True, exist_ok=True)
        procesar().to_parquet(PARQUET, index=False)
    return pd.read_parquet(PARQUET)


@st.cache_data
def cargar_metricas() -> pd.DataFrame | None:
    """Métricas de los modelos (serie, modelo, mae, rmse) o None si aún no se exportaron."""
    return pd.read_parquet(METRICAS) if METRICAS.exists() else None


def aplicar_filtros(df: pd.DataFrame, filtros: dict) -> pd.DataFrame:
    """Aplica los filtros de la barra lateral. Una lista vacía deja la selección sin datos."""
    anio_ini, anio_fin = filtros["anios"]
    mask = df["anio"].between(anio_ini, anio_fin)
    for col in ("via", "tipo_viajero"):
        if col in filtros:
            mask &= df[col].isin(filtros[col])
    return df[mask]


def ultimo_anio_completo(df: pd.DataFrame) -> int:
    """Último año con los 12 meses en la base (2026 solo llega a junio)."""
    meses = df.groupby("anio")["fecha"].nunique()
    return int(meses[meses == 12].index.max())


def mes_es(fecha: pd.Timestamp, largo: bool = False) -> str:
    """Timestamp('2026-06-01') -> 'jun 2026' (o 'junio' con largo=True)."""
    if largo:
        return _MESES_LARGOS[fecha.month - 1]
    return f"{_MESES[fecha.month - 1]} {fecha.year}"


def formato_num(n: float) -> str:
    """12345678 -> '12.3 M', 45200 -> '45.2 mil'."""
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f} M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:.1f} mil"
    return f"{n:,.0f}"
