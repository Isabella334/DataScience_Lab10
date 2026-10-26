"""
Visualizaciones 5 y 6 – Mercados de origen: regiones y países (enlazadas).

Pregunta de gestión (P2): ¿de qué regiones y países vienen los visitantes?

Interacción:
- Gráfica A (regiones): barras con las 5 regiones principales y el resto agrupado en
  "Otras". Un clic en una barra elige la región; doble clic quita la selección.
- Gráfica B (países): ranking de países de la región elegida en A, o de todas si no
  hay selección (gráficas enlazadas, la pareja principal del tablero).
- Selector Top 5 / 10 / 15 / Todos: cuántos países ver (más o menos detalle).

render_regiones() debe llamarse antes que render_paises() porque guarda la región elegida.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import paleta
from src.datos import formato_num

CLAVE_REGION = "region_seleccionada"
_KEY_GRAFICA = "v5_regiones"
TOP_REGIONES = 5
OTRAS = "Otras"


def _region_desde_estado() -> str | None:
    """Lee la región elegida en la gráfica A (el estado existe antes de volver a dibujarla)."""
    estado = st.session_state.get(_KEY_GRAFICA)
    puntos = (estado or {}).get("selection", {}).get("points", []) if estado else []
    return puntos[0]["customdata"][0] if puntos else None


def _agrupar_regiones(df: pd.DataFrame) -> pd.Series:
    """Región de cada fila con las que no están en el top 5 renombradas como "Otras"."""
    totales = df.groupby("region", observed=True)["viajeros"].sum()
    top = totales[totales > 0].nlargest(TOP_REGIONES).index
    region = df["region"].astype(str)
    return region.where(df["region"].isin(top), OTRAS)


def _por_region(df: pd.DataFrame) -> pd.DataFrame:
    por_region = (
        df.assign(grupo=_agrupar_regiones(df)).groupby("grupo")["viajeros"].sum().reset_index()
        .query("viajeros > 0").sort_values("viajeros", ascending=False)
    )
    # "Otras" siempre al final
    por_region = pd.concat([por_region[por_region["grupo"] != OTRAS], por_region[por_region["grupo"] == OTRAS]])
    por_region["porcentaje"] = por_region["viajeros"] / por_region["viajeros"].sum()
    return por_region


def _figura_regiones(por_region: pd.DataFrame, elegida: str | None) -> go.Figure:
    # Azul = dato observado, ámbar = selección del usuario, gris = no seleccionado / "Otras"
    if elegida is None:
        colores = [paleta.OTROS if r == OTRAS else paleta.PRIMARIO for r in por_region["grupo"]]
    else:
        colores = [paleta.SECUNDARIO if r == elegida else paleta.OTROS for r in por_region["grupo"]]
    fig = go.Figure(go.Bar(
        x=por_region["viajeros"], y=por_region["grupo"], orientation="h",
        marker_color=colores,
        customdata=por_region[["grupo", "porcentaje"]],
        text=[f"{formato_num(v)}  ({p:.1%})" for v, p in zip(por_region["viajeros"], por_region["porcentaje"])],
        textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} visitantes<br>%{customdata[1]:.1%} del total<extra></extra>",
    ))
    fig.update_layout(
        height=360, margin=dict(l=10, r=100, t=10, b=10),
        plot_bgcolor=paleta.FONDO, paper_bgcolor=paleta.FONDO,
        font=dict(color=paleta.TEXTO, size=13), showlegend=False,
        xaxis=dict(visible=False), yaxis=dict(title=None, autorange="reversed", automargin=True),
        clickmode="event+select", dragmode=False,
    )
    return fig


def _figura_paises(ranking: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=ranking["viajeros"], y=ranking["pais"], orientation="h",
        marker_color=paleta.PRIMARIO,  # datos observados
        customdata=ranking[["region", "porcentaje"]],
        text=[formato_num(v) for v in ranking["viajeros"]],
        textposition="outside", cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b> (%{customdata[0]})<br>%{x:,.0f} visitantes<br>"
            "%{customdata[1]:.1%} de la selección<extra></extra>"
        ),
    ))
    fig.update_layout(
        height=max(360, 30 * len(ranking) + 40), margin=dict(l=10, r=70, t=10, b=10),
        plot_bgcolor=paleta.FONDO, paper_bgcolor=paleta.FONDO,
        font=dict(color=paleta.TEXTO, size=13), showlegend=False,
        xaxis=dict(visible=False), yaxis=dict(title=None, autorange="reversed", automargin=True),
    )
    return fig


def render_regiones(df: pd.DataFrame) -> None:
    """Gráfica A: visitantes por región. Un clic elige la región que filtra la gráfica de países."""
    st.subheader("¿De qué regiones vienen los visitantes?")
    st.caption(f"Visitantes por región de residencia: las {TOP_REGIONES} principales y el resto en «{OTRAS}». "
               "**Haga clic en una barra** para ver sus países abajo; doble clic para quitar la selección.")
    if df.empty:
        st.session_state[CLAVE_REGION] = None
        st.info("No hay datos para los filtros seleccionados. Amplíe el rango de años o quite algún filtro.")
        return

    por_region = _por_region(df)
    elegida = _region_desde_estado()
    if elegida not in set(por_region["grupo"]):
        elegida = None  # la región elegida desapareció por los filtros de la barra lateral
    st.session_state[CLAVE_REGION] = elegida

    st.plotly_chart(
        _figura_regiones(por_region, elegida), width="stretch",
        on_select="rerun", selection_mode="points", key=_KEY_GRAFICA,
        config={"displayModeBar": False},
    )
    lider = por_region.iloc[0]
    st.caption(f"🔎 **{lider['grupo']}** aporta el {lider['porcentaje']:.0%} de los visitantes del periodo filtrado.")


def render_paises(df: pd.DataFrame) -> None:
    """Gráfica B (enlazada): ranking de países de la región elegida en la gráfica A."""
    # La gráfica A se dibuja antes y deja aquí la región elegida (None si está oculta)
    elegida = st.session_state.get(CLAVE_REGION)
    c1, c2 = st.columns([3, 1])
    c1.subheader(f"Países de {'«' + elegida + '»' if elegida == OTRAS else elegida}" if elegida
                 else "Países de todas las regiones")
    cantidad = c2.selectbox("Países a mostrar", [5, 10, 15, "Todos"], index=1, key="v6_cantidad",
                            label_visibility="collapsed",
                            format_func=lambda n: n if n == "Todos" else f"Top {n}")
    st.caption("Ranking de países de residencia por cantidad de visitantes. Desde 2023 la fuente agrupa "
               "los países pequeños (por ejemplo, «Otros Países de Europa»).")

    if df.empty:
        st.info("No hay datos para los filtros seleccionados.")
        return
    sub = df if elegida is None else df[_agrupar_regiones(df) == elegida]
    ranking = (
        sub.groupby(["pais", "region"], observed=True)["viajeros"].sum().reset_index()
        .query("viajeros > 0").sort_values("viajeros", ascending=False)
    )
    if ranking.empty:
        st.info("No hay países con visitantes para esta selección.")
        return
    ranking["porcentaje"] = ranking["viajeros"] / ranking["viajeros"].sum()
    if cantidad != "Todos":
        ranking = ranking.head(cantidad)

    st.plotly_chart(_figura_paises(ranking), width="stretch",
                    config={"displayModeBar": False}, key="v6_paises")

    lider = ranking.iloc[0]
    st.caption(
        f"🔎 **{lider['pais']}** concentra el {lider['porcentaje']:.0%} de los visitantes "
        f"de {'esta región' if elegida else 'todas las regiones'} en el periodo filtrado."
    )
