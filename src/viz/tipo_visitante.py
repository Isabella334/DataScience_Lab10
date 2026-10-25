"""
Visualización 7 – Tipo de visitante por vía de ingreso (barras apiladas).

Pregunta de gestión (P5): ¿qué tipo de visitante llega (turista o excursionista) y por qué vía?

Interacción:
- Medida: "Cantidad" (visitantes) o "% de la vía" (composición de cada vía, todas al 100 %).
- Clic en la leyenda para ocultar o mostrar un tipo; tooltip con el valor exacto.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import paleta
from src.datos import ORDEN_VIAS, VISITANTES, formato_num

MEDIDAS = ["Cantidad", "% de la vía"]


def _tabla(df: pd.DataFrame) -> pd.DataFrame:
    """Visitantes por vía (filas) y tipo (columnas), solo turistas y excursionistas."""
    sub = df[df["tipo_viajero"].isin(VISITANTES)]
    tabla = sub.pivot_table(index="via", columns="tipo_viajero", values="viajeros",
                            aggfunc="sum", observed=True, fill_value=0)
    tabla = tabla.reindex(index=[v for v in ORDEN_VIAS if v in tabla.index],
                          columns=[t for t in VISITANTES if t in tabla.columns])
    return tabla[tabla.sum(axis=1) > 0]


def _figura(tabla: pd.DataFrame, medida: str) -> go.Figure:
    es_pct = medida == "% de la vía"
    valores = tabla.div(tabla.sum(axis=1), axis=0) if es_pct else tabla
    fig = go.Figure()
    for tipo in tabla.columns:
        fig.add_trace(go.Bar(
            name=tipo, x=valores[tipo], y=tabla.index, orientation="h",
            marker_color=paleta.color_para("tipo_viajero", tipo),
            customdata=tabla[tipo],
            text=[f"{v:.0%}" if es_pct else formato_num(v) for v in valores[tipo]],
            textposition="inside", insidetextanchor="middle",
            hovertemplate=(f"<b>%{{y}} · {tipo}</b><br>%{{customdata:,.0f}} visitantes"
                           + ("<br>%{x:.1%} de la vía" if es_pct else "") + "<extra></extra>"),
        ))
    fig.update_layout(
        barmode="stack", height=300, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor=paleta.FONDO, paper_bgcolor=paleta.FONDO,
        font=dict(color=paleta.TEXTO, size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None, traceorder="normal"),
        xaxis=dict(title=None, tickformat=".0%" if es_pct else "~s", gridcolor=paleta.REJILLA, automargin=True),
        yaxis=dict(title=None, autorange="reversed", automargin=True),
        uniformtext=dict(minsize=10, mode="hide"),
    )
    return fig


def render(df: pd.DataFrame) -> None:
    c1, c2 = st.columns([3, 1])
    c1.subheader("¿Qué tipo de visitante llega por cada vía?")
    medida = c2.radio("Medida", MEDIDAS, horizontal=True, key="v7_medida", label_visibility="collapsed")
    st.caption("Turistas (pasan al menos una noche) y excursionistas (entran y salen el mismo día) "
               "por vía de ingreso. Use «% de la vía» para comparar la composición de cada vía.")

    tabla = _tabla(df)
    if tabla.empty:
        st.info("No hay datos para los filtros seleccionados. Amplíe el rango de años o quite algún filtro.")
        return

    st.plotly_chart(_figura(tabla, medida), width="stretch", config={"displayModeBar": False}, key="v7_tipo")

    if "Excursionista" in tabla.columns and "Terrestre" in tabla.index:
        pct = tabla.loc["Terrestre", "Excursionista"] / tabla.loc["Terrestre"].sum()
        st.caption(f"🔎 El {pct:.0%} de quienes entran por tierra son excursionistas: llegan y se van el mismo día.")
