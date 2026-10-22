"""
Visualización 2 – (Persona 4)

Para enlazarla con la visualización 1, leer el periodo elegido por el usuario:

    periodo = st.session_state.get(serie_temporal.CLAVE_PERIODO)  # (inicio, fin) o None
    if periodo:
        df = df[df["fecha"].between(*periodo)]

Usar los colores de src/paleta.py (p. ej. paleta.color_para("region", valor)).
"""
import pandas as pd
import streamlit as st

from src.viz.serie_temporal import CLAVE_PERIODO


def render(df: pd.DataFrame) -> None:
    st.subheader("2. (Visualización 2 – en construcción)")
    periodo = st.session_state.get(CLAVE_PERIODO)
    if periodo:
        st.caption(f"Recibiendo el periodo seleccionado en la gráfica 1: {periodo[0]:%b %Y} – {periodo[1]:%b %Y}")
    else:
        st.caption("Seleccione un periodo en la gráfica 1 para filtrar esta gráfica.")
