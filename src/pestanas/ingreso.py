"""
Pestaña "Ingreso" – ¿por dónde, cuándo y quiénes llegan? (P3, P4 y P5)

Distribución:
    [ KPI ] [ KPI ] [ KPI ] [ KPI ]
    [ Visualización principal: mapa de calor de estacionalidad ]
    [ Vías de ingreso ]   [ Ranking de fronteras (enlazada) ]
    [ Tipo de visitante por vía ]

mostrar: claves de GRAFICAS que se dibujan; None dibuja todas.
"""
import importlib
import importlib.util

import pandas as pd
import streamlit as st

from src.datos import formato_num
from src.viz import estacionalidad, vias_fronteras

# Gráficas de esta pestaña, para el control "Mostrar" de la barra lateral
GRAFICAS = {
    "estacionalidad": "Estacionalidad (mapa de calor)",
    "vias": "Vías de ingreso",
    "fronteras": "Ranking de fronteras",
    "tipo_visitante": "Tipo de visitante por vía",
}


def _tipo_visitante(df: pd.DataFrame) -> None:
    """Tipo de visitante por vía (P5); si src/viz/tipo_visitante.py no existe, muestra un aviso."""
    if importlib.util.find_spec("src.viz.tipo_visitante") is None:
        st.markdown("**¿Qué tipo de visitante llega por cada vía?**")
        st.info("Gráfica en construcción: tipo de visitante por vía (barras apiladas).")
        return
    importlib.import_module("src.viz.tipo_visitante").render(df)


def _kpis(df: pd.DataFrame) -> None:
    k1, k2, k3, k4 = st.columns(4)
    if df.empty:
        for k, titulo in zip((k1, k2, k3, k4), ("Ingreso terrestre", "Ingreso aéreo",
                                                "Principal punto de ingreso", "Mes de mayor demanda")):
            k.metric(titulo, "—")
        return

    total = df["viajeros"].sum()
    por_via = df.groupby("via", observed=True)["viajeros"].sum()
    k1.metric("Ingreso terrestre", f"{por_via.get('Terrestre', 0) / total:.0%}",
              help="Porcentaje de los visitantes del periodo filtrado que entraron por tierra.")
    k2.metric("Ingreso aéreo", f"{por_via.get('Aérea', 0) / total:.0%}",
              help="Porcentaje de los visitantes del periodo filtrado que entraron por avión.")

    fronteras = df.groupby("frontera", observed=True)["viajeros"].sum()
    lider = fronteras.idxmax()
    k3.metric("Principal punto de ingreso", str(lider),
              help=f"{formato_num(fronteras[lider])} visitantes ({fronteras[lider] / total:.0%} del total filtrado).")

    pct = estacionalidad.participacion_mensual(df)
    if pct is None:
        k4.metric("Mes de mayor demanda", "—", help="Se necesita al menos un año completo y típico.")
    else:
        mes = pct.idxmax()
        k4.metric("Mes de mayor demanda", f"{estacionalidad.MESES[mes - 1]} · {pct[mes]:.1%}",
                  help="Mes que en promedio concentra más visitantes del año (años completos, sin 2020–2021).")


def render(df: pd.DataFrame, mostrar: set[str] | None = None) -> None:
    mostrar = set(GRAFICAS) if mostrar is None else set(mostrar)

    _kpis(df)

    if not mostrar & set(GRAFICAS):
        st.info("No hay gráficas seleccionadas. Elija al menos una en «Mostrar» de la barra lateral.")
        return

    if "estacionalidad" in mostrar:
        with st.container(border=True):
            estacionalidad.render(df, resumen=False)

    if "vias" not in mostrar:
        st.session_state[vias_fronteras.CLAVE_VIA] = None  # sin gráfica A, el ranking muestra todo

    abajo = [g for g in ("vias", "fronteras") if g in mostrar]
    if abajo:
        columnas = st.columns(len(abajo), gap="medium")
        for col, grafica in zip(columnas, abajo):
            with col, st.container(border=True):
                if grafica == "vias":
                    vias_fronteras.render_vias(df)
                else:
                    vias_fronteras.render_fronteras(df)

    if "tipo_visitante" in mostrar:
        with st.container(border=True):
            _tipo_visitante(df)
