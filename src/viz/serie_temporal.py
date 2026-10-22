"""
Visualización 1 – Evolución de la llegada de viajeros.

Pregunta de gestión: ¿cómo ha cambiado la llegada de viajeros en el tiempo y qué
segmentos explican esos cambios?

Interacción:
- Nivel de detalle temporal: mes / trimestre / año (aumentar o disminuir detalle).
- Desglose: total, región, vía o tipo de viajero.
- Vista: líneas (comparar tendencias) o área apilada (ver composición).
- Selección: clic o arrastre en la gráfica para elegir un periodo. El periodo se
  guarda en st.session_state["periodo_seleccionado"] para que la visualización 2
  pueda filtrarse con él (gráficas enlazadas).
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import paleta
from src.datos import ETIQUETAS, formato_num

FRECUENCIAS = {"Mes": "MS", "Trimestre": "QS", "Año": "YS"}
CLAVE_PERIODO = "periodo_seleccionado"
MAX_CATEGORIAS = 7  # el resto se agrupa en "Otros" para no saturar la gráfica


def _agregar(df: pd.DataFrame, frecuencia: str, desglose: str) -> pd.DataFrame:
    grupo = [pd.Grouper(key="fecha", freq=FRECUENCIAS[frecuencia])]
    if desglose == "total":
        return df.groupby(grupo)["viajeros"].sum().reset_index().assign(categoria="Total")

    datos = df.copy()
    top = datos.groupby(desglose, observed=True)["viajeros"].sum().nlargest(MAX_CATEGORIAS).index
    datos["categoria"] = datos[desglose].astype(str).where(datos[desglose].isin(top), "Otros")
    return datos.groupby(grupo + ["categoria"])["viajeros"].sum().reset_index()


def _rango_de_periodo(inicio: pd.Timestamp, frecuencia: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    fin = inicio + pd.tseries.frequencies.to_offset(FRECUENCIAS[frecuencia]) - pd.Timedelta(days=1)
    return inicio.normalize(), fin.normalize()


def _construir_figura(serie: pd.DataFrame, desglose: str, vista: str, frecuencia: str) -> go.Figure:
    fig = go.Figure()
    categorias = (
        serie.groupby("categoria")["viajeros"].sum().sort_values(ascending=False).index.tolist()
    )
    if "Otros" in categorias:  # "Otros" siempre al final
        categorias.remove("Otros")
        categorias.append("Otros")

    formato_fecha = {"Mes": "%b %Y", "Trimestre": "T%q %Y", "Año": "%Y"}[frecuencia]
    for i, cat in enumerate(categorias):
        tramo = serie[serie["categoria"] == cat]
        if desglose == "total":
            color = paleta.PRIMARIO
        elif cat == "Otros":
            color = paleta.TEXTO_SUAVE
        else:
            color = paleta.color_para(desglose, cat, i)
        apilada = vista == "Composición (área apilada)"
        fig.add_trace(go.Scatter(
            x=tramo["fecha"], y=tramo["viajeros"], name=cat,
            mode="lines+markers" if frecuencia != "Mes" else "lines",
            line=dict(color=color, width=2.5 if desglose == "total" else 2),
            marker=dict(size=6),
            stackgroup="uno" if apilada else None,
            fillcolor=color if apilada else None,
            hovertemplate=f"<b>{cat}</b><br>%{{x|{formato_fecha}}}<br>%{{y:,.0f}} visitantes<extra></extra>",
        ))

    # Marcar el periodo de la pandemia como contexto (hecho observado, sin atribuir causas)
    fig.add_vrect(
        x0="2020-03-01", x1="2021-06-30", fillcolor=paleta.REJILLA, opacity=0.5,
        line_width=0, layer="below",
        annotation_text="Cierre de fronteras / COVID-19", annotation_position="top left",
        annotation_font=dict(size=11, color=paleta.TEXTO_SUAVE),
    )
    # Referencia prepandemia (P1): nivel de 2019 en la vista anual del total
    if frecuencia == "Año" and desglose == "total":
        nivel_2019 = serie.loc[serie["fecha"].dt.year == 2019, "viajeros"].sum()
        if nivel_2019:
            fig.add_hline(
                y=nivel_2019, line_dash="dash", line_color=paleta.SECUNDARIO, line_width=1.5,
                annotation_text="Nivel 2019 (prepandemia)", annotation_position="bottom left",
                annotation_font=dict(size=11, color=paleta.TEXTO_SUAVE),
            )

    # El último año/trimestre puede estar incompleto (la base llega a jun 2026)
    ultimo = serie["fecha"].max()
    if frecuencia != "Mes":
        fig.add_annotation(
            x=ultimo, y=serie.loc[serie["fecha"] == ultimo, "viajeros"].max(),
            text="Periodo incompleto<br>(datos hasta jun 2026)", showarrow=True, arrowhead=0,
            ax=-60, ay=-40, font=dict(size=11, color=paleta.TEXTO_SUAVE),
        )
    fig.update_layout(
        height=480,
        margin=dict(l=10, r=10, t=70, b=10),
        hovermode="x unified" if desglose != "total" else "closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.08, x=0, title=None),
        plot_bgcolor=paleta.FONDO, paper_bgcolor=paleta.FONDO,
        font=dict(color=paleta.TEXTO, size=13),
        dragmode="select",
        xaxis=dict(title=None, gridcolor=paleta.REJILLA, rangeslider=dict(visible=True, thickness=0.06)),
        yaxis=dict(title="Visitantes", gridcolor=paleta.REJILLA, tickformat=",.0f", rangemode="tozero"),
    )
    return fig


def _leer_seleccion(evento, frecuencia: str):
    """Convierte la selección de plotly (clic o caja) en un rango de fechas."""
    if not evento or not evento.selection:
        return None
    puntos = evento.selection.get("points", [])
    cajas = evento.selection.get("box", [])
    # Se prefieren los puntos para que el rango cubra periodos completos
    if puntos:
        fechas = pd.to_datetime([p["x"] for p in puntos])
        ini, _ = _rango_de_periodo(fechas.min(), frecuencia)
        _, fin = _rango_de_periodo(fechas.max(), frecuencia)
        return ini, fin
    if cajas:
        x0, x1 = sorted(pd.to_datetime(cajas[0]["x"]))
        return x0.normalize(), x1.normalize()
    return None


def render(df: pd.DataFrame) -> None:
    st.subheader("1. ¿Cómo ha evolucionado la llegada de visitantes y cuánto nos hemos recuperado respecto a 2019?")
    st.caption(
        "Cantidad de visitantes internacionales que ingresaron a Guatemala en cada periodo. "
        "Cambie el nivel de detalle o el desglose, y **arrastre sobre la gráfica (o haga clic en un punto)** "
        "para seleccionar un periodo: las demás gráficas se actualizarán con esa selección."
    )

    c1, c2, c3 = st.columns([1, 1.3, 1.3])
    frecuencia = c1.radio("Nivel de detalle", list(FRECUENCIAS), index=2, horizontal=True, key="v1_frec")
    desglose = c2.selectbox(
        "Desglosar por", ["total", "region", "via", "tipo_viajero"],
        format_func=ETIQUETAS.get, key="v1_desglose",
    )
    vista = c3.radio(
        "Vista", ["Tendencias (líneas)", "Composición (área apilada)"],
        horizontal=True, key="v1_vista", disabled=desglose == "total",
    )

    if df.empty:
        st.info("No hay datos para los filtros seleccionados. Amplíe el rango de años o quite algún filtro.")
        return

    serie = _agregar(df, frecuencia, desglose)
    fig = _construir_figura(serie, desglose, vista, frecuencia)
    evento = st.plotly_chart(
        fig, use_container_width=True, on_select="rerun",
        selection_mode=("points", "box"), key="v1_grafica",
        config={"displaylogo": False, "locale": "es"},
    )

    seleccion = _leer_seleccion(evento, frecuencia)
    st.session_state[CLAVE_PERIODO] = seleccion

    # Resumen del periodo (seleccionado o completo)
    if seleccion:
        ini, fin = seleccion
        sub = df[df["fecha"].between(ini, fin)]
        etiqueta = f"Periodo seleccionado: {ini:%b %Y} – {fin:%b %Y}"
    else:
        sub = df
        etiqueta = f"Periodo completo filtrado: {df['fecha'].min():%b %Y} – {df['fecha'].max():%b %Y}"

    total_total = sub["viajeros"].sum()
    k1, k2, k3 = st.columns(3)
    k1.metric("Visitantes en el periodo", formato_num(total_total))
    meses = sub["fecha"].nunique()
    k2.metric("Promedio mensual", formato_num(total_total / meses) if meses else "—")
    if desglose != "total" and not sub.empty:
        lider = sub.groupby(desglose, observed=True)["viajeros"].sum().idxmax()
        k3.metric(f"{ETIQUETAS[desglose]} con más visitantes", str(lider))
    else:
        anual = df.groupby("anio")["viajeros"].sum()
        if anual.get(2019) and anual.get(2025):
            k3.metric(
                "Recuperación 2025 vs. 2019", f"{anual[2025] / anual[2019]:.0%}",
                help="Visitantes de 2025 como porcentaje de los de 2019 (último año completo antes de la pandemia).",
            )
    st.caption(f"🔎 {etiqueta}. " + ("Haga doble clic en la gráfica para quitar la selección." if seleccion else ""))
