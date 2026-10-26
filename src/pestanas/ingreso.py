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
    terrestre = aerea = lider = mes = "—"
    ayuda_lider = "Frontera, aeropuerto o puerto con más visitantes en el periodo filtrado."
    if not df.empty:
        total = df["viajeros"].sum()
        por_via = df.groupby("via", observed=True)["viajeros"].sum()
        terrestre = f"{por_via.get('Terrestre', 0) / total:.0%}"
        aerea = f"{por_via.get('Aérea', 0) / total:.0%}"
        fronteras = df.groupby("frontera", observed=True)["viajeros"].sum()
        lider = str(fronteras.idxmax())
        ayuda_lider = f"{formato_num(fronteras.max())} visitantes ({fronteras.max() / total:.0%} del total filtrado)."
        pct = estacionalidad.participacion_mensual(df)
        if pct is not None:
            mes = f"{estacionalidad.MESES[pct.idxmax() - 1]} · {pct.max():.1%}"

    indicadores = [
        ("Ingreso terrestre", terrestre, "Porcentaje de los visitantes del periodo filtrado que entraron por tierra."),
        ("Ingreso aéreo", aerea, "Porcentaje de los visitantes del periodo filtrado que entraron por avión."),
        ("Principal punto de ingreso", lider, ayuda_lider),
        ("Mes de mayor demanda", mes,
         "Mes que en promedio concentra más visitantes del año (años completos, sin 2020–2021)."),
    ]
    # Mismas tarjetas que los indicadores de Panorama (estilo definido en app.py)
    with st.container(horizontal=True, gap="medium"):
        for i, (etiqueta, valor, ayuda) in enumerate(indicadores):
            with st.container(key=f"tarjeta_kpi_ingreso_{i}", height="stretch"):
                st.metric(etiqueta, valor, help=ayuda)


def render(df: pd.DataFrame, mostrar: set[str] | None = None) -> None:
    mostrar = set(GRAFICAS) if mostrar is None else set(mostrar)

    _kpis(df)

    if not mostrar & set(GRAFICAS):
        st.info("Todas las gráficas de esta pestaña están ocultas. Actívelas en «Mostrar», en la barra lateral.")
        return

    if "estacionalidad" in mostrar:
        with st.container(key="tarjeta_estacionalidad"):
            estacionalidad.render(df, resumen=False)

    if "vias" not in mostrar:
        st.session_state[vias_fronteras.CLAVE_VIA] = None  # sin gráfica A, el ranking muestra todo

    abajo = [g for g in ("vias", "fronteras") if g in mostrar]
    if abajo:
        columnas = st.columns(len(abajo), gap="large")
        for col, grafica in zip(columnas, abajo):
            with col, st.container(key=f"tarjeta_{grafica}"):
                if grafica == "vias":
                    vias_fronteras.render_vias(df)
                else:
                    vias_fronteras.render_fronteras(df)

    if "tipo_visitante" in mostrar:
        with st.container(key="tarjeta_tipo_visitante"):
            _tipo_visitante(df)
