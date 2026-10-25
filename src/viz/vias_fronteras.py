"""
Visualización 3 – Vías de ingreso y ranking de fronteras (enlazadas).

Pregunta de gestión (P3): ¿por qué vías y fronteras ingresan los visitantes?

Interacción:
- Gráfica A (vías): barras con la cantidad y el porcentaje de cada vía. Un clic en
  una barra elige la vía; otro clic en el fondo (o doble clic) quita la selección.
- Gráfica B (fronteras): ranking de puntos de ingreso. Muestra solo las fronteras
  de la vía elegida en A, o todas si no hay selección (gráficas enlazadas).
- Selector Top 5 / 10 / 15 / Todas: cuántas fronteras ver (más o menos detalle).

render_vias() y render_fronteras() se pueden colocar por separado (por ejemplo, en
dos columnas); render_vias() debe llamarse primero porque guarda la vía elegida.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import paleta
from src.datos import formato_num

CLAVE_VIA = "via_seleccionada"
_KEY_GRAFICA = "v3_vias"


def _via_desde_estado() -> str | None:
    """Lee la vía elegida en la gráfica A (el estado existe antes de volver a dibujarla)."""
    estado = st.session_state.get(_KEY_GRAFICA)
    puntos = (estado or {}).get("selection", {}).get("points", []) if estado else []
    return puntos[0]["customdata"][0] if puntos else None


def _figura_vias(por_via: pd.DataFrame, elegida: str | None) -> go.Figure:
    # Azul = dato observado, ámbar = selección del usuario, gris = no seleccionado
    if elegida is None:
        colores = [paleta.PRIMARIO] * len(por_via)
    else:
        colores = [paleta.SECUNDARIO if v == elegida else paleta.OTROS for v in por_via["via"]]
    fig = go.Figure(go.Bar(
        x=por_via["viajeros"], y=por_via["via"], orientation="h",
        marker_color=colores,
        customdata=por_via[["via", "porcentaje"]],
        text=[f"{formato_num(v)}  ({p:.1%})" for v, p in zip(por_via["viajeros"], por_via["porcentaje"])],
        textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} visitantes<br>%{customdata[1]:.1%} del total<extra></extra>",
    ))
    fig.update_layout(
        height=380, margin=dict(l=10, r=90, t=10, b=10),
        plot_bgcolor=paleta.FONDO, paper_bgcolor=paleta.FONDO,
        font=dict(color=paleta.TEXTO, size=13), showlegend=False,
        xaxis=dict(visible=False), yaxis=dict(title=None, autorange="reversed"),
        clickmode="event+select", dragmode=False,
    )
    return fig


def _figura_fronteras(ranking: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=ranking["viajeros"], y=ranking["frontera"], orientation="h",
        marker_color=paleta.PRIMARIO,  # datos observados
        customdata=ranking[["via", "porcentaje"]],
        text=[formato_num(v) for v in ranking["viajeros"]],
        textposition="outside", cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b> (%{customdata[0]})<br>%{x:,.0f} visitantes<br>"
            "%{customdata[1]:.1%} de la selección<extra></extra>"
        ),
    ))
    fig.update_layout(
        height=max(380, 34 * len(ranking) + 40), margin=dict(l=10, r=70, t=10, b=10),
        plot_bgcolor=paleta.FONDO, paper_bgcolor=paleta.FONDO,
        font=dict(color=paleta.TEXTO, size=13), showlegend=False,
        xaxis=dict(visible=False), yaxis=dict(title=None, autorange="reversed"),
    )
    return fig


def _por_via(df: pd.DataFrame) -> pd.DataFrame:
    por_via = df.groupby("via", observed=True)["viajeros"].sum().reset_index()
    por_via = por_via[por_via["viajeros"] > 0].sort_values("viajeros", ascending=False)
    por_via["porcentaje"] = por_via["viajeros"] / por_via["viajeros"].sum()
    return por_via


def render_vias(df: pd.DataFrame) -> None:
    """Gráfica A: visitantes por vía. Un clic elige la vía que filtra el ranking de fronteras."""
    st.markdown("**¿Por qué vía ingresan los visitantes?**")
    st.caption("Visitantes por vía de ingreso. **Haga clic en una barra** para ver solo sus fronteras; "
               "doble clic para quitar la selección.")
    if df.empty:
        st.session_state[CLAVE_VIA] = None
        st.info("No hay datos para los filtros seleccionados. Amplíe el rango de años o quite algún filtro.")
        return

    por_via = _por_via(df)
    elegida = _via_desde_estado()
    if elegida not in set(por_via["via"]):
        elegida = None  # la vía elegida desapareció por los filtros de la barra lateral
    st.session_state[CLAVE_VIA] = elegida

    st.plotly_chart(
        _figura_vias(por_via, elegida), width="stretch",
        on_select="rerun", selection_mode="points", key=_KEY_GRAFICA,
        config={"displayModeBar": False},
    )
    if "Marítima" in set(por_via["via"]):
        st.caption(
            "La vía marítima es marginal. Los pasajeros de crucero se registran aparte "
            "(tipo «Cruceristas») y no se suman aquí si solo se filtran turistas y excursionistas."
        )


def render_fronteras(df: pd.DataFrame) -> None:
    """Gráfica B (enlazada): ranking de puntos de ingreso de la vía elegida en la gráfica A."""
    # La gráfica A se dibuja antes y deja aquí la vía elegida (None si está oculta)
    elegida = st.session_state.get(CLAVE_VIA)
    titulo = f"Puntos de ingreso – vía {elegida.lower()}" if elegida else "Puntos de ingreso – todas las vías"
    c1, c2 = st.columns([2, 1])
    c1.markdown(f"**{titulo}**")
    cantidad = c2.selectbox("Fronteras a mostrar", [5, 10, 15, "Todas"], index=1, key="v3_cantidad",
                            label_visibility="collapsed",
                            format_func=lambda n: n if n == "Todas" else f"Top {n}")
    st.caption("Ranking de fronteras, aeropuertos y puertos por cantidad de visitantes.")

    sub = df if elegida is None else df[df["via"] == elegida]
    ranking = (
        sub.groupby(["frontera", "via"], observed=True)["viajeros"].sum().reset_index()
        .query("viajeros > 0").sort_values("viajeros", ascending=False)
    )
    if ranking.empty:
        st.info("No hay puntos de ingreso con visitantes para esta selección.")
        return
    ranking["porcentaje"] = ranking["viajeros"] / ranking["viajeros"].sum()
    if cantidad != "Todas":
        ranking = ranking.head(cantidad)

    st.plotly_chart(_figura_fronteras(ranking), width="stretch",
                    config={"displayModeBar": False}, key="v3_fronteras")

    lider = ranking.iloc[0]
    st.caption(
        f"🔎 **{lider['frontera']}** concentra el {lider['porcentaje']:.0%} de los visitantes "
        f"de {'la vía ' + elegida.lower() if elegida else 'todas las vías'} en el periodo filtrado."
    )


def render(df: pd.DataFrame) -> None:
    """Ambas gráficas lado a lado (vía a la izquierda, fronteras enlazadas a la derecha)."""
    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        render_vias(df)
    with col_b:
        render_fronteras(df)
