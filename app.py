import streamlit as st

from src import paleta
from src.datos import VISITANTES, aplicar_filtros, cargar_datos, formato_num
from src.viz import serie_temporal, viz2

st.set_page_config(
    page_title="Observatorio de Turismo · Guatemala",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
      h1, h2, h3 {{ color: {paleta.PRIMARIO}; }}
      [data-testid="stMetricValue"] {{ color: {paleta.PRIMARIO}; }}
      [data-testid="stCaptionContainer"] {{ color: {paleta.TEXTO_SUAVE}; font-size: 0.95rem; }}
      .block-container {{ padding-top: 2rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

df = cargar_datos()

# Barra lateral
with st.sidebar:
    st.header("Filtros generales")
    st.caption("Se aplican a todas las gráficas del tablero.")
    anio_min, anio_max = int(df["anio"].min()), int(df["anio"].max())
    filtros = {
        "anios": st.slider("Años", anio_min, anio_max, (anio_min, anio_max)),
        "region": st.multiselect("Región de residencia", sorted(df["region"].cat.categories),
                                 placeholder="Todas"),
        "via": st.multiselect("Vía de ingreso", sorted(df["via"].cat.categories), placeholder="Todas"),
        "tipo_viajero": st.multiselect(
            "Tipo de viajero", sorted(df["tipo_viajero"].cat.categories),
            default=list(VISITANTES), placeholder="Todos",
            help="Por defecto se muestran solo visitantes (Turista + Excursionista). "
                 "La categoría «Viajero» cambió de definición en 2023, así que no es comparable en el tiempo.",
        ),
    }
    st.divider()
    st.caption(
        "Fuente: registros de ingreso de viajeros internacionales 2009 – jun 2026 "
        "(IGM / INGUAT), base del Lab 1. Uso exclusivamente académico; no son cifras oficiales."
    )

datos = aplicar_filtros(df, filtros)

# Encabezado
st.title("Observatorio de Turismo Sostenible · Guatemala")
st.markdown(
    "Explore cómo llegan los viajeros internacionales al país, de dónde vienen y qué "
    "esperan los modelos de predicción para los próximos meses."
)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Visitantes (filtro actual)", formato_num(datos["viajeros"].sum()))
k2.metric("Países de residencia", f"{datos['pais'].nunique():,}")
k3.metric("Puntos de ingreso", f"{datos['frontera'].nunique():,}")
k4.metric("Último mes con datos", f"{df['fecha'].max():%b %Y}")

# Navegación
# Pestañas alineadas con las preguntas de gestión (P1–P6) del documento de alcance
tab_explorar, tab_origen, tab_modelos, tab_acerca = st.tabs(
    ["📈 Evolución y origen", "🛂 Vías, temporada y tipo de visitante", "🔮 Predicciones y modelos",
     "ℹ️ Acerca del tablero"]
)

with tab_explorar:
    serie_temporal.render(datos)  # P1
    st.divider()
    viz2.render(datos)  # P2

with tab_origen:
    st.info("Sección en construcción: vías y fronteras (P3), estacionalidad (P4) y tipo de visitante (P5).")

with tab_modelos:
    st.info(
        "Sección en construcción (P6): pronóstico vs. valor real y comparación de error (MAE/RMSE) "
        "de los modelos del Lab 1: Prophet, SARIMA, Holt-Winters, SES y Seasonal Naive."
    )

with tab_acerca:
    st.markdown(
        """
        **¿Para quién es?** Directivos y tomadores de decisiones del sector turístico.

        **¿Cómo leerlo?**
        - Los **datos observados** se muestran con línea continua; las **estimaciones** de los modelos
          con línea punteada y una banda de incertidumbre.
        - Los colores tienen un significado fijo en todo el tablero (por ejemplo, cada región conserva su color).
        - Las gráficas describen patrones; **no permiten afirmar causas**.
        """
    )
