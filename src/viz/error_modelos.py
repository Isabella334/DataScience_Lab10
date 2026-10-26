"""
Visualización – Error de cada modelo (MAE / RMSE) en el periodo de prueba.

Pregunta de gestión: ¿en qué modelo conviene confiar más para cada serie y cuánto se equivoca?

Interacción:
- Métrica: MAE o RMSE.
- Nivel de detalle: "Serie elegida" (barras con los 5 modelos) o "Todas las series"
  (matriz serie × modelo con el error relativo, para comparar series de distinto tamaño).
- Enlazada con pronostico_real.py: un clic en una barra elige ese modelo; un clic en una
  celda de la matriz elige la serie y el modelo. El cambio se refleja en la barra lateral.

Ámbar = modelo elegido (selección); gris = los demás.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import paleta
from src.datos import MODELOS, SERIES_MODELO, cargar_metricas, cargar_predicciones, formato_num
from src.viz.pronostico_real import datos_de_serie, serie_y_modelo

METRICAS = {
    "MAE": "Error absoluto medio: en promedio, cuántos visitantes por mes se equivoca el modelo.",
    "RMSE": "Raíz del error cuadrático medio: como el MAE, pero castiga más los meses con errores grandes.",
}
ALCANCES = ("Serie elegida", "Todas las series")
_KEY_BARRAS = "error_barras"
_KEY_MATRIZ = "error_matriz"


# Enlace con la barra lateral: los callbacks corren antes de redibujar, así el selector
# de modelo (que se dibuja primero) ya muestra la elección hecha en la gráfica.
def _puntos(clave: str) -> list:
    estado = st.session_state.get(clave)
    return (estado or {}).get("selection", {}).get("points", []) if estado else []


def _al_elegir_barra() -> None:
    puntos = _puntos(_KEY_BARRAS)
    if puntos:
        st.session_state["pronostico_modelo"] = puntos[0]["customdata"][0]


def _al_elegir_celda() -> None:
    puntos = _puntos(_KEY_MATRIZ)
    if puntos:
        serie, modelo = puntos[0]["customdata"][:2]
        st.session_state["pronostico_serie"] = serie
        st.session_state["pronostico_modelo"] = modelo


def _con_error_relativo(metricas: pd.DataFrame) -> pd.DataFrame:
    """Agrega el error como fracción de un mes promedio real del periodo de prueba."""
    predicciones = cargar_predicciones()
    prueba = predicciones[(predicciones["conjunto"] == "prueba") & (predicciones["modelo"] == MODELOS[0])]
    promedio = prueba.groupby("serie")["real"].mean().rename("promedio_real")
    return metricas.join(promedio, on="serie")


def _figura_barras(tabla: pd.DataFrame, columna: str, modelo: str) -> go.Figure:
    tabla = tabla.sort_values(columna)  # el que menos se equivoca, arriba
    relativo = tabla[columna] / tabla["promedio_real"]
    fig = go.Figure(go.Bar(
        x=tabla[columna], y=tabla["modelo"], orientation="h",
        marker_color=[paleta.SECUNDARIO if m == modelo else paleta.OTROS for m in tabla["modelo"]],
        customdata=pd.DataFrame({"modelo": tabla["modelo"], "relativo": relativo}),
        text=[f"{formato_num(v)}  ({r:.0%} de un mes)" for v, r in zip(tabla[columna], relativo)],
        textposition="outside", cliponaxis=False,
        selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1)),
        hovertemplate=(f"<b>%{{y}}</b><br>{columna}: %{{x:,.0f}} visitantes por mes"
                       "<br>%{customdata[1]:.0%} de un mes promedio real<extra></extra>"),
    ))
    fig.update_layout(
        height=330, margin=dict(l=10, r=170, t=10, b=10),
        plot_bgcolor=paleta.FONDO, paper_bgcolor=paleta.FONDO,
        font=dict(color=paleta.TEXTO, size=13), showlegend=False,
        xaxis=dict(visible=False), yaxis=dict(title=None, autorange="reversed"),
        clickmode="event+select", dragmode=False,
    )
    return fig


def _figura_matriz(tabla: pd.DataFrame, columna: str, serie: str, modelo: str) -> go.Figure:
    tabla = tabla.assign(relativo=tabla[columna] / tabla["promedio_real"])
    mejores = tabla.loc[tabla.groupby("serie")[columna].idxmin()].set_index("serie")["modelo"]
    elegida = (tabla["serie"] == serie) & (tabla["modelo"] == modelo)
    oscura = tabla["relativo"] > tabla["relativo"].quantile(0.6)  # texto blanco sobre las celdas oscuras
    fig = go.Figure(go.Scatter(
        x=tabla["modelo"], y=tabla["serie"], mode="markers+text",
        marker=dict(
            symbol="square", size=46, color=tabla["relativo"], colorscale=paleta.ESCALA_SECUENCIAL,
            colorbar=dict(title="Error<br>relativo", tickformat=".0%", thickness=12),
            line=dict(color=[paleta.SECUNDARIO if e else paleta.FONDO for e in elegida],
                      width=[4 if e else 1 for e in elegida]),
        ),
        text=[f"{'★ ' if mejores.get(s) == m else ''}{r:.0%}"
              for s, m, r in zip(tabla["serie"], tabla["modelo"], tabla["relativo"])],
        textfont=dict(size=12, color=[paleta.TARJETA if o else paleta.TEXTO for o in oscura]),
        customdata=tabla[["serie", "modelo", columna, "relativo"]],
        selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1)),
        hovertemplate=(f"<b>%{{customdata[0]}}</b> · %{{customdata[1]}}<br>{columna}: %{{customdata[2]:,.0f}} "
                       "visitantes por mes<br>%{customdata[3]:.0%} de un mes promedio real<extra></extra>"),
    ))
    fig.update_layout(
        height=430, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor=paleta.FONDO, paper_bgcolor=paleta.FONDO,
        font=dict(color=paleta.TEXTO, size=13), showlegend=False,
        xaxis=dict(title=None, side="top", categoryorder="array", categoryarray=list(MODELOS), showgrid=False),
        yaxis=dict(title=None, categoryorder="array", categoryarray=list(SERIES_MODELO)[::-1], showgrid=False),
        clickmode="event+select", dragmode=False,
    )
    return fig


def render(df: pd.DataFrame) -> None:
    serie, modelo = serie_y_modelo()
    st.subheader("¿Cuánto se equivoca cada modelo?")
    st.caption(
        "Error promedio de cada modelo en el periodo de prueba: **mientras más corta la barra, mejor**. "
        "Entre paréntesis, el error como porcentaje de lo que llega en un mes promedio. "
        "**Haga clic en una barra** para ver ese modelo en la gráfica de pronóstico."
    )
    if datos_de_serie(serie) is None:
        return
    metricas = cargar_metricas()
    if metricas is None:
        st.info("Todavía no se han calculado las métricas. Ejecute `python data/entrenar_modelos.py`.")
        return

    c1, c2 = st.columns(2)
    alcance = c1.radio("Nivel de detalle", ALCANCES, horizontal=True, key="error_alcance",
                       help="«Todas las series» compara los modelos en cada región y país a la vez.")
    metrica = c2.radio("Métrica", list(METRICAS), horizontal=True, key="error_metrica",
                       help=" ".join(f"{k}: {v}" for k, v in METRICAS.items()))
    columna = metrica.lower()
    tabla = _con_error_relativo(metricas)

    if alcance == ALCANCES[0]:
        de_serie = tabla[tabla["serie"] == serie]
        st.plotly_chart(_figura_barras(de_serie, columna, modelo), width="stretch",
                        on_select=_al_elegir_barra, selection_mode="points", key=_KEY_BARRAS,
                        config={"displayModeBar": False})
        mejor = de_serie.loc[de_serie[columna].idxmin()]
        st.caption(
            f"📊 **Observado:** en «{serie}», el modelo con menor {metrica} es **{mejor['modelo']}** "
            f"({formato_num(mejor[columna])} visitantes por mes, {mejor[columna] / mejor['promedio_real']:.0%} "
            "de un mes promedio). Un error menor en el pasado no garantiza el mismo desempeño en el futuro."
        )
    else:
        st.plotly_chart(_figura_matriz(tabla, columna, serie, modelo), width="stretch",
                        on_select=_al_elegir_celda, selection_mode="points", key=_KEY_MATRIZ,
                        config={"displayModeBar": False})
        st.caption(
            "Cada celda es el error como porcentaje de un mes promedio de esa serie, para poder comparar series "
            "de distinto tamaño. ★ marca el modelo con menor error en cada fila; el borde ámbar, la serie y "
            "el modelo elegidos. **Haga clic en una celda** para verla en la gráfica de pronóstico."
        )
