"""
Visualización 4 – Estacionalidad: mapa de calor año × mes.

Pregunta de gestión (P4): ¿en qué meses se concentra la demanda?

Interacción:
- Medida: "Cantidad de visitantes" (valores absolutos) o "% del año" (qué parte de
  los visitantes de cada año llegó en cada mes). La segunda quita el efecto del
  crecimiento entre años y deja ver solo el patrón estacional.
- Tooltip con el valor exacto de cada celda; el rango de años se controla desde la
  barra lateral.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import paleta

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MEDIDAS = ["Cantidad de visitantes", "% del año"]
# Años con un patrón atípico (cierre de fronteras) que no se usan para el resumen estacional
ANIOS_ATIPICOS = {2020, 2021}


def _matriz(df: pd.DataFrame, medida: str) -> tuple[pd.DataFrame, set[int]]:
    tabla = df.pivot_table(index="anio", columns="mes", values="viajeros", aggfunc="sum")
    tabla = tabla.reindex(columns=range(1, 13))
    incompletos = set(tabla.index[tabla.isna().any(axis=1)])
    if medida == "% del año":
        # Un año incompleto no tiene 100 % que repartir: se deja fuera
        tabla = tabla.drop(index=list(incompletos))
        tabla = tabla.div(tabla.sum(axis=1), axis=0)
    return tabla, incompletos


def _figura(tabla: pd.DataFrame, medida: str) -> go.Figure:
    es_pct = medida == "% del año"
    # Texto corto en la celda (miles o %); el valor exacto va en el tooltip
    texto = tabla.map(lambda v: "" if pd.isna(v) else (f"{v:.0%}" if es_pct else f"{v / 1000:.0f}"))
    # La escala se ajusta a los años típicos; si no, 2020 (37 % en enero) aplana el resto
    tipicos = tabla.drop(index=[a for a in ANIOS_ATIPICOS if a in tabla.index])
    rango = tipicos if es_pct and not tipicos.empty else tabla
    fig = go.Figure(go.Heatmap(
        z=tabla.values, x=MESES, y=tabla.index.astype(str),
        colorscale=paleta.ESCALA_SECUENCIAL,
        zmin=rango.min().min(), zmax=rango.max().max(),
        text=texto.values, texttemplate="%{text}", textfont=dict(size=10),
        hovertemplate=(
            "<b>%{x} %{y}</b><br>"
            + ("%{z:.1%} de los visitantes del año" if es_pct else "%{z:,.0f} visitantes")
            + "<extra></extra>"
        ),
        colorbar=dict(title=None, tickformat=".0%" if es_pct else "~s", thickness=12),
        xgap=2, ygap=2, hoverongaps=False,
    ))
    fig.update_layout(
        height=max(340, 22 * len(tabla) + 70), margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor=paleta.FONDO, paper_bgcolor=paleta.FONDO,
        font=dict(color=paleta.TEXTO, size=13),
        xaxis=dict(side="top", title=None), yaxis=dict(title=None, autorange="reversed", dtick=1),
    )
    return fig


def participacion_mensual(df: pd.DataFrame) -> pd.Series | None:
    """Promedio, por mes, del % de visitantes del año (años completos, sin 2020–2021)."""
    pct, _ = _matriz(df, "% del año")
    pct = pct.drop(index=[a for a in ANIOS_ATIPICOS if a in pct.index])
    if pct.empty:
        return None
    promedio = pct.mean()
    promedio.attrs["anios"] = len(pct)
    return promedio


def render(df: pd.DataFrame, resumen: bool = True) -> None:
    """resumen=False omite las tarjetas de mes alto/bajo (cuando la pestaña ya las muestra como KPI)."""
    st.subheader("¿En qué meses se concentra la llegada de visitantes?")
    st.caption(
        "Cada fila es un año y cada columna un mes; **más oscuro = más visitantes**. "
        "Con «% del año» se compara la forma de la temporada entre años, sin el efecto del crecimiento."
    )

    medida = st.radio("Medida", MEDIDAS, horizontal=True, key="v4_medida")

    if df.empty:
        st.info("No hay datos para los filtros seleccionados. Amplíe el rango de años o quite algún filtro.")
        return

    tabla, incompletos = _matriz(df, medida)
    if tabla.empty:
        st.info("Ninguno de los años seleccionados está completo; elija «Cantidad de visitantes» o amplíe el rango.")
        return

    st.plotly_chart(_figura(tabla, medida), width="stretch",
                    config={"displayModeBar": False}, key="v4_mapa")
    if medida == "Cantidad de visitantes":
        st.caption("Valores de las celdas en **miles de visitantes**. Pase el cursor para ver la cifra exacta.")

    notas = []
    if incompletos and medida == "% del año":
        notas.append(f"Se omiten años incompletos ({', '.join(map(str, sorted(incompletos)))}).")
    elif incompletos:
        notas.append("Las celdas vacías son meses sin datos (la base llega a junio 2026).")
    if ANIOS_ATIPICOS & set(tabla.index):
        notas.append("2020 y 2021 muestran un patrón atípico por el cierre de fronteras.")

    # Resumen estacional: promedio de la participación mensual en años completos y típicos
    promedio = participacion_mensual(df)
    if promedio is not None:
        alto, bajo = promedio.idxmax(), promedio.idxmin()
        if resumen:
            k1, k2 = st.columns(2)
            k1.metric("Mes más alto en promedio", f"{MESES[alto - 1]} · {promedio[alto]:.1%}",
                      help="Porcentaje promedio de los visitantes del año que llegan en ese mes.")
            k2.metric("Mes más bajo en promedio", f"{MESES[bajo - 1]} · {promedio[bajo]:.1%}",
                      help="Porcentaje promedio de los visitantes del año que llegan en ese mes.")
        else:
            notas.append(
                f"En promedio, el mes más alto es **{MESES[alto - 1]}** ({promedio[alto]:.1%} del año) "
                f"y el más bajo **{MESES[bajo - 1]}** ({promedio[bajo]:.1%})."
            )
        notas.append(
            f"Promedio calculado con {promedio.attrs['anios']} año(s) completo(s), sin 2020–2021. "
            "Describe un patrón observado; no explica sus causas."
        )
    st.caption(" ".join(notas))
