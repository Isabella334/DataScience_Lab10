"""
Visualización 1 – Evolución de la llegada de viajeros.

Pregunta de gestión: ¿cómo ha cambiado la llegada de viajeros en el tiempo y qué
segmentos explican esos cambios?

Interacción:
- Nivel de detalle temporal: mes / trimestre / año (aumentar o disminuir detalle).
- Desglose: total, región, vía o tipo de viajero.
- Vista: líneas (comparar tendencias) o área apilada (ver composición).
- Selección: clic o arrastre en la gráfica para elegir un periodo. Las cifras de abajo
  se calculan para ese periodo y se guarda en st.session_state["periodo_seleccionado"].
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import paleta
from src.datos import ETIQUETAS, formato_num, mes_es

FRECUENCIAS = {"Mes": "MS", "Trimestre": "QS", "Año": "YS"}
# Nombres que usa la barra lateral -> nombres internos
ALIAS_FRECUENCIA = {"Anual": "Año", "Mensual": "Mes", "Trimestral": "Trimestre"}
CLAVE_PERIODO = "periodo_seleccionado"
MAX_CATEGORIAS = 7  # el resto se agrupa en "Otros" para no saturar la gráfica
# Tramos de la fuente según la hoja "Notas" del Excel: 2009–2020 respaldos históricos,
# 2021–2022 entrega del IGM y desde 2023 conteos depurados del INGUAT
CAMBIOS_FUENTE = [
    ("2021-01-01", "Fuente: IGM", "Desde 2021 los datos provienen de la entrega del IGM.", 0.14),
    ("2023-01-01", "Fuente: INGUAT",
     "Desde 2023 se usan los conteos depurados del INGUAT y cambia la definición de «Viajero».", 0.02),
]


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
            color = paleta.OTROS
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
    # Cambios metodológicos de la fuente (Honey Bronze = advertencia), para no leerlos como caídas reales
    for fecha, texto, detalle, altura in CAMBIOS_FUENTE:
        fig.add_shape(type="line", x0=fecha, x1=fecha, y0=0, y1=1, yref="paper",
                      line=dict(color=paleta.REFERENCIA, width=1.5, dash="dot"))
        fig.add_annotation(x=fecha, y=altura, yref="paper", text=texto, hovertext=detalle,
                           showarrow=False, xanchor="left", yanchor="bottom", xshift=4,
                           font=dict(size=10, color=paleta.TEXTO_SUAVE), bgcolor=paleta.FONDO)
    # Referencia prepandemia (P1): nivel de 2019 en la vista anual del total
    if frecuencia == "Año" and desglose == "total":
        nivel_2019 = serie.loc[serie["fecha"].dt.year == 2019, "viajeros"].sum()
        if nivel_2019:
            fig.add_hline(
                y=nivel_2019, line_dash="dash", line_color=paleta.TEXTO_SUAVE, line_width=1.5,
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
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
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


def render(df: pd.DataFrame, frecuencia: str | None = None) -> None:
    """
    frecuencia: nivel de detalle elegido en la barra lateral ("Anual"/"Mensual", o
    "Año"/"Trimestre"/"Mes"). Si no se pasa, la gráfica muestra su propio selector.
    """
    st.subheader("¿Cómo ha evolucionado la llegada de visitantes y cuánto nos hemos recuperado respecto a 2019?")
    st.caption(
        "Cantidad de visitantes internacionales que ingresaron a Guatemala en cada periodo. "
        "Cambie el nivel de detalle o el desglose, y **arrastre sobre la gráfica (o haga clic en un punto)** "
        "para seleccionar un periodo: las cifras de abajo se calcularán solo para ese periodo."
    )

    c1, c2, c3 = st.columns([1, 1.3, 1.3])
    if frecuencia is None:
        frecuencia = c1.radio("Nivel de detalle", list(FRECUENCIAS), index=2, horizontal=True, key="v1_frec")
    else:
        frecuencia = ALIAS_FRECUENCIA.get(frecuencia, frecuencia)
        if frecuencia not in FRECUENCIAS:
            raise ValueError(f"Nivel de detalle no reconocido: {frecuencia!r}")
        c1.markdown(f"**Nivel de detalle:** {frecuencia.lower()}  \n"
                    "<small>Se cambia en la barra lateral.</small>", unsafe_allow_html=True)
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
        fig, width="stretch", on_select="rerun",
        selection_mode=("points", "box"), key="v1_grafica",
        config={"displaylogo": False, "locale": "es"},
    )

    seleccion = _leer_seleccion(evento, frecuencia)
    st.session_state[CLAVE_PERIODO] = seleccion

    # Resumen del periodo (seleccionado o completo)
    if seleccion:
        ini, fin = seleccion
        sub = df[df["fecha"].between(ini, fin)]
        etiqueta = f"Periodo seleccionado: {mes_es(ini)} – {mes_es(fin)}"
    else:
        sub = df
        etiqueta = f"Periodo completo filtrado: {mes_es(df['fecha'].min())} – {mes_es(df['fecha'].max())}"

    total_total = sub["viajeros"].sum()
    # La recuperación frente a 2019 ya está en los indicadores de la pestaña
    con_lider = desglose != "total" and not sub.empty
    columnas = st.columns(3 if con_lider else 2)
    columnas[0].metric("Visitantes en el periodo", formato_num(total_total))
    meses = sub["fecha"].nunique()
    columnas[1].metric("Promedio mensual", formato_num(total_total / meses) if meses else "—")
    if con_lider:
        lider = sub.groupby(desglose, observed=True)["viajeros"].sum().idxmax()
        columnas[2].metric(f"{ETIQUETAS[desglose]} con más visitantes", str(lider))
    st.caption(f"🔎 {etiqueta}. " + ("Haga doble clic en la gráfica para quitar la selección." if seleccion else ""))
    st.caption(
        "Las líneas punteadas marcan cambios en la fuente de datos (2021 y 2023): los saltos cerca de "
        "esas fechas pueden deberse a la forma de contar y no necesariamente a cambios reales en la llegada."
    )
