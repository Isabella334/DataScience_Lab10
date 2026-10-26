"""
Visualización – Pronóstico frente a lo real (modelos del Lab 1).

Pregunta de gestión: ¿qué tan cerca estuvo cada modelo de lo que realmente ocurrió y
se puede usar su estimación para planificar?

Interacción:
- Serie, modelo y "Comparar con los demás modelos" se eligen en la barra lateral
  (st.session_state["pronostico_serie"], ["pronostico_modelo"], ["pronostico_comparar"]).
- Rango: toda la historia o solo el periodo de prueba (aumentar o disminuir detalle),
  más el rangeslider de Plotly para hacer zoom.
- Enlazada con error_modelos.py: un clic en una barra de error cambia el modelo que se dibuja aquí.

Azul continuo = dato observado; ámbar punteado = estimación del modelo elegido;
gris punteado = los demás modelos (solo al comparar).
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import paleta
from src.datos import MODELOS, SERIES_MODELO, cargar_metricas, cargar_predicciones, formato_num, mes_es

RANGOS = ("Toda la historia", "Solo el periodo de prueba")


def serie_y_modelo() -> tuple[str, str]:
    """Serie y modelo elegidos en la barra lateral."""
    serie = st.session_state.get("pronostico_serie", SERIES_MODELO[0])
    return serie, st.session_state.get("pronostico_modelo", MODELOS[0])


def datos_de_serie(serie: str) -> pd.DataFrame | None:
    """Predicciones de la serie; si no hay modelos para ella, muestra un aviso y devuelve None."""
    predicciones = cargar_predicciones()
    if predicciones is None:
        st.info("Todavía no se han calculado los modelos. Ejecute `python data/entrenar_modelos.py` "
                "para generar las predicciones.")
        return None
    datos = predicciones[predicciones["serie"] == serie]
    if datos.empty:
        st.info(f"La serie «{serie}» no tiene modelos de pronóstico. Elija otra serie en la barra lateral.")
        return None
    return datos


def _figura(datos: pd.DataFrame, modelo: str, comparar: bool, rango: str) -> go.Figure:
    real = datos[datos["modelo"] == datos["modelo"].iloc[0]]  # el dato real es el mismo en todos los modelos
    prueba = datos[datos["conjunto"] == "prueba"]
    inicio_prueba = prueba["fecha"].min()

    fig = go.Figure()
    if comparar:
        for i, otro in enumerate(m for m in MODELOS if m != modelo):
            tramo = prueba[prueba["modelo"] == otro]
            if tramo.empty:
                continue
            fig.add_trace(go.Scatter(
                x=tramo["fecha"], y=tramo["prediccion"], name="Otros modelos", legendgroup="otros",
                showlegend=i == 0, mode="lines",
                line=dict(color=paleta.OTROS_MODELOS, width=1.5, dash=paleta.ESTILO_PREDICCION),
                hovertemplate=f"<b>{otro}</b><br>%{{x|%b %Y}}<br>%{{y:,.0f}} visitantes estimados<extra></extra>",
            ))
    fig.add_trace(go.Scatter(
        x=real["fecha"], y=real["real"], name="Real (observado)", mode="lines",
        line=dict(color=paleta.OBSERVADO, width=2.5),
        hovertemplate="<b>Real</b><br>%{x|%b %Y}<br>%{y:,.0f} visitantes<extra></extra>",
    ))
    elegido = prueba[prueba["modelo"] == modelo]
    fig.add_trace(go.Scatter(
        x=elegido["fecha"], y=elegido["prediccion"], name=f"Estimación: {modelo}", mode="lines",
        line=dict(color=paleta.PREDICCION, width=2.5, dash=paleta.ESTILO_PREDICCION),
        hovertemplate=f"<b>{modelo}</b><br>%{{x|%b %Y}}<br>%{{y:,.0f}} visitantes estimados<extra></extra>",
    ))

    # Periodo de prueba sombreado: el modelo no vio estos datos al entrenarse
    fig.add_vrect(
        x0=inicio_prueba, x1=prueba["fecha"].max(), fillcolor=paleta.REJILLA, opacity=0.35,
        line_width=0, layer="below",
        annotation_text="Periodo de prueba: datos que el modelo no conoció",
        annotation_position="top left", annotation_font=dict(size=11, color=paleta.TEXTO_SUAVE),
    )
    inicio_x = inicio_prueba - pd.DateOffset(months=3) if rango == RANGOS[1] else real["fecha"].min()
    fig.update_layout(
        height=470, margin=dict(l=10, r=10, t=60, b=10),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.06, x=0, title=None),
        plot_bgcolor=paleta.FONDO, paper_bgcolor=paleta.FONDO,
        font=dict(color=paleta.TEXTO, size=13),
        xaxis=dict(title=None, gridcolor=paleta.REJILLA, range=[inicio_x, real["fecha"].max()],
                   rangeslider=dict(visible=True, thickness=0.06)),
        yaxis=dict(title="Visitantes por mes", gridcolor=paleta.REJILLA, tickformat=",.0f", rangemode="tozero"),
    )
    return fig


def _resumen(datos: pd.DataFrame, modelo: str) -> None:
    """Cifras del periodo de prueba para el modelo elegido."""
    prueba = datos[(datos["conjunto"] == "prueba") & (datos["modelo"] == modelo)]
    real, estimado = prueba["real"].sum(), prueba["prediccion"].sum()
    k1, k2, k3 = st.columns(3)
    k1.metric("Visitantes reales en la prueba", formato_num(real),
              help=f"Suma de {mes_es(prueba['fecha'].min())} a {mes_es(prueba['fecha'].max())}.")
    k2.metric("Estimados por el modelo", formato_num(estimado),
              delta=f"{estimado / real - 1:+.0%} frente a lo real" if real else None, delta_color="off")

    metricas = cargar_metricas()
    if metricas is not None:
        de_serie = metricas[metricas["serie"] == datos["serie"].iloc[0]].sort_values("mae").reset_index(drop=True)
        posicion = de_serie.index[de_serie["modelo"] == modelo]
        if len(posicion):
            mae = de_serie.loc[posicion[0], "mae"]
            k3.metric("Error promedio por mes (MAE)", formato_num(mae),
                      help=f"Puesto {posicion[0] + 1} de {len(de_serie)} modelos (1 = el que menos se equivoca). "
                           f"Equivale al {mae / prueba['real'].mean():.0%} de un mes promedio real.")


def render(df: pd.DataFrame) -> None:
    serie, modelo = serie_y_modelo()
    st.subheader("¿Qué tan cerca estuvo el pronóstico de lo que realmente ocurrió?")
    st.caption(
        f"Visitantes por mes de la serie **{serie}**. La línea azul es lo que se observó; la ámbar punteada, "
        "lo que estimó el modelo entrenado solo con datos anteriores al periodo sombreado. "
        "Cambie la serie o el modelo en la barra lateral, o haga clic en una barra de la gráfica de error."
    )
    datos = datos_de_serie(serie)
    if datos is None:
        return
    if modelo not in set(datos["modelo"]):
        st.info(f"El modelo «{modelo}» no está disponible para la serie «{serie}». Elija otro en la barra lateral.")
        return

    rango = st.radio("Rango de fechas", RANGOS, horizontal=True, key="pronostico_rango")
    comparar = st.session_state.get("pronostico_comparar", False)
    st.plotly_chart(_figura(datos, modelo, comparar, rango), width="stretch",
                    config={"displaylogo": False, "locale": "es"})
    _resumen(datos, modelo)
    st.caption(
        "⚠️ **Limitación:** los modelos se entrenaron con datos hasta marzo de 2021, en el punto más bajo de la "
        "pandemia, y la recuperación posterior no estaba en sus datos. Las diferencias muestran qué tan lejos "
        "quedó cada estimación, no explican por qué cambió la llegada de visitantes. Cada modelo da un solo "
        "valor por mes, sin rango de incertidumbre."
    )
