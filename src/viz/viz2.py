"""
Visualización 2 – Mercados de origen.

Recibe el periodo elegido en la visualización 1 desde
st.session_state[CLAVE_PERIODO] como (inicio, fin), o None si no hay selección.
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
