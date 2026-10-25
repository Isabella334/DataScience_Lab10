import importlib
from pathlib import Path

import streamlit as st

from src import paleta
from src.datos import (
    MODELOS, ORDEN_VIAS, SERIES_MODELO, VISITANTES, aplicar_filtros, cargar_datos, cargar_metricas,
    formato_num, mes_es, ultimo_anio_completo,
)
from src.pestanas import ingreso as pestana_ingreso

st.set_page_config(
    page_title="Observatorio de Turismo · Guatemala",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
      h1, h2, h3 {{ color: {paleta.TITULOS}; }}
      [data-testid="stMetricValue"] {{ color: {paleta.TITULOS}; }}
      [data-testid="stCaptionContainer"] {{ color: {paleta.TEXTO_SUAVE}; font-size: 0.95rem; }}
      /* Menos espacio arriba: la barra de pestañas mide 60 px; se deja un margen para que no tape nada */
      [data-testid="stMainBlockContainer"] {{ padding-top: 4.75rem; }}
      [data-testid="stSidebarHeader"] {{ height: 2.75rem; }}
      /* Tarjetas: cada indicador y cada gráfica va en un contenedor con key "tarjeta_..." */
      [class*="st-key-tarjeta"] {{
        background-color: {paleta.TARJETA}; border: 1px solid {paleta.REJILLA};
        border-radius: 0.75rem; box-shadow: 0 1px 3px {paleta.SOMBRA}; padding: 1.25rem 1.5rem;
      }}
      [class*="st-key-tarjeta_kpi"] {{ padding: 1rem 1.25rem; }}
      /* Ancho mínimo en el elemento que se acomoda en la fila: las 3 tarjetas caben en una fila */
      [data-testid="stLayoutWrapper"]:has(> [class*="st-key-tarjeta_kpi"]) {{ min-width: 150px; flex: 1 1 0; }}
      /* Pestaña activa: subrayado ámbar (selección) en lugar del fondo lila por defecto de Streamlit */
      [data-testid="stTopNavLink"][aria-current="page"] {{
        background-color: transparent; border-radius: 0; font-weight: 600; color: {paleta.TEXTO};
        box-shadow: inset 0 -3px 0 {paleta.AMBER_EARTH};
      }}
      [data-testid="stTopNavLink"]:not([aria-current="page"]):hover {{ background-color: {paleta.FONDO_SUAVE}; }}
      [class*="st-key-tarjeta_kpi"] [data-testid="stMetricValue"] {{ font-size: 1.9rem; }}
      /* Que etiquetas y valores largos bajen de línea por palabras en vez de cortarse con "..." */
      [class*="st-key-tarjeta_kpi"] [data-testid="stMetricLabel"] *,
      [class*="st-key-tarjeta_kpi"] [data-testid="stMetricValue"] * {{
        white-space: normal !important; overflow: visible !important; text-overflow: clip !important;
        word-break: normal !important; overflow-wrap: normal !important;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Gráficas de cada pestaña: (módulo en src/viz/, nombre que ve el usuario).
# Cada módulo expone render(df). Si el archivo aún no existe se muestra un aviso en su lugar,
# así cada visualización se agrega creando su archivo, sin modificar app.py.
GRAFICAS = {
    "Panorama": [("serie_temporal", "Evolución de visitantes")],
    "Mercados": [("regiones", "Visitantes por región"), ("paises", "Países de la región elegida")],
    # Ingreso tiene su propio acomodo en src/pestanas/ingreso.py; aquí solo se listan sus gráficas para "Mostrar"
    "Ingreso": list(pestana_ingreso.GRAFICAS.items()),
    "Pronóstico": [("pronostico_real", "Pronóstico frente a lo real"), ("error_modelos", "Error por modelo")],
}
TIPOS_VISITANTE = {"Todos": list(VISITANTES), "Turista": ["Turista"], "Excursionista": ["Excursionista"]}
LOGO = Path(__file__).parent / "logo_uvg_horizontal.png"


# Persistencia de filtros entre pestañas
# Streamlit borra el valor de un widget cuando no se dibuja (por ejemplo, al pasar por Pronóstico).
# El widget usa la clave "_x" y su valor se copia a "x", que sí se conserva.
def _guardar(clave: str, al_cambiar=None) -> None:
    st.session_state[clave] = st.session_state[f"_{clave}"]
    if al_cambiar:
        al_cambiar()


def _persistente(widget, clave: str, inicial, *args, al_cambiar=None, **kwargs):
    if clave not in st.session_state:
        st.session_state[clave] = inicial
    st.session_state[f"_{clave}"] = st.session_state[clave]
    return widget(*args, key=f"_{clave}", on_change=_guardar, args=(clave, al_cambiar), **kwargs)


def _mejor_modelo(serie: str) -> str:
    """Modelo con menor MAE para la serie; Prophet si aún no hay métricas."""
    metricas = cargar_metricas()
    if metricas is not None:
        fila = metricas[metricas["serie"] == serie]
        if not fila.empty:
            return str(fila.loc[fila["mae"].idxmin(), "modelo"])
    return "Prophet"


def _al_cambiar_serie() -> None:
    st.session_state["pronostico_modelo"] = _mejor_modelo(st.session_state["pronostico_serie"])


def _casillas_mostrar(pagina: str) -> None:
    st.markdown("**Mostrar**")
    for modulo, titulo in GRAFICAS[pagina]:
        _persistente(st.checkbox, f"mostrar_{modulo}", True, titulo)


def _barra_filtros(df, pagina: str) -> dict:
    anio_min, anio_max = int(df["anio"].min()), int(df["anio"].max())
    anios = _persistente(st.slider, "anios", (anio_min, anio_max), "Año / rango", anio_min, anio_max)
    st.caption(f"Los datos de {anio_max} llegan hasta {mes_es(df['fecha'].max(), largo=True)}.")

    detalle = _persistente(st.radio, "detalle", "Anual", "Anual / mensual", ["Anual", "Mensual"], horizontal=True)

    st.markdown("**Vía**")
    vias = [via for via in ORDEN_VIAS if _persistente(st.checkbox, f"via_{via}", True, via)]

    tipo = _persistente(st.selectbox, "tipo_visitante", "Todos", "Tipo de visitante", list(TIPOS_VISITANTE),
                        help="Turista: pernocta en el país. Excursionista: entra y sale el mismo día. "
                             "«Viajero» no se incluye porque no es visitante y cambió de definición entre 2022 y 2023.")
    st.divider()
    _casillas_mostrar(pagina)
    return {"anios": anios, "detalle": detalle, "via": vias, "tipo_viajero": TIPOS_VISITANTE[tipo]}


def _barra_pronostico() -> None:
    _persistente(st.selectbox, "pronostico_serie", SERIES_MODELO[0], "Serie", list(SERIES_MODELO),
                 al_cambiar=_al_cambiar_serie,
                 help="Solo las series para las que se entrenaron modelos.")
    _persistente(st.selectbox, "pronostico_modelo", _mejor_modelo(st.session_state.get("pronostico_serie", SERIES_MODELO[0])),
                 "Modelo", list(MODELOS), help="Por defecto se elige el de menor error para la serie.")
    _persistente(st.checkbox, "pronostico_comparar", False, "Comparar con los demás modelos")
    st.divider()
    _casillas_mostrar("Pronóstico")


def _dibujar(modulo: str, titulo: str, datos) -> None:
    """Dibuja la gráfica dentro de su tarjeta."""
    with st.container(key=f"tarjeta_{modulo}"):
        try:
            viz = importlib.import_module(f"src.viz.{modulo}")
        except ModuleNotFoundError as error:
            if error.name != f"src.viz.{modulo}":
                raise  # el módulo existe pero falla al importar algo: mostrar el error real
            st.subheader(titulo)
            st.info("Esta gráfica estará disponible próximamente.")
            return
        if modulo == "serie_temporal" and filtros:
            viz.render(datos, frecuencia=filtros["detalle"])  # nivel de detalle de la barra lateral
        else:
            viz.render(datos)


def _graficas(pagina: str, datos) -> None:
    """Primera gráfica a todo el ancho y las siguientes en pares, como en el wireframe."""
    visibles = [g for g in GRAFICAS[pagina] if st.session_state.get(f"mostrar_{g[0]}", True)]
    if not visibles:
        st.info("Todas las gráficas de esta pestaña están ocultas. Actívelas en «Mostrar», en la barra lateral.")
        return
    primera, *resto = visibles
    _dibujar(*primera, datos)
    for i in range(0, len(resto), 2):
        par = resto[i:i + 2]
        if len(par) == 1:
            _dibujar(*par[0], datos)
            continue
        for columna, grafica in zip(st.columns(2, gap="large"), par):
            with columna:
                _dibujar(*grafica, datos)


def _indicadores() -> None:
    # Con la vía y el tipo elegidos, pero sobre toda la historia (comparan años fijos)
    base = aplicar_filtros(df, {**filtros, "anios": (int(df["anio"].min()), int(df["anio"].max()))})
    anual = base.groupby("anio")["viajeros"].sum()
    ultimo = ultimo_anio_completo(df)
    actual, previo, ref_2019 = anual.get(ultimo, 0), anual.get(ultimo - 1, 0), anual.get(2019, 0)

    indicadores = [
        (f"Visitantes {ultimo}", formato_num(actual) if actual else "—",
         f"Último año completo en la base ({df['anio'].max()} solo llega a junio)."),
        ("Recuperación vs. 2019", f"{actual / ref_2019:.0%}" if ref_2019 else "—",
         f"Visitantes de {ultimo} como porcentaje de los de 2019, el último año antes de la pandemia."),
        ("Variación anual", f"{actual / previo - 1:+.1%}" if previo else "—",
         f"Cambio de {ultimo} frente a {ultimo - 1}."),
    ]
    # Fila horizontal: con height="stretch" cada tarjeta toma la altura de la fila (todas iguales)
    with st.container(horizontal=True, gap="medium"):
        for i, (etiqueta, valor, ayuda) in enumerate(indicadores):
            with st.container(key=f"tarjeta_kpi_{i}", height="stretch"):
                st.metric(etiqueta, valor, help=ayuda)
    st.caption("Indicadores calculados con la vía y el tipo de visitante elegidos en la barra lateral.")


# Pestañas
def panorama() -> None:
    _indicadores()
    _graficas("Panorama", datos)


def mercados() -> None:
    st.caption("De qué regiones y países vienen los visitantes. Haga clic en una región para ver sus países.")
    _graficas("Mercados", datos)


def ingreso() -> None:
    st.caption("Por qué vías y fronteras ingresan los visitantes, en qué meses y de qué tipo son.")
    visibles = {clave for clave, _ in GRAFICAS["Ingreso"] if st.session_state.get(f"mostrar_{clave}", True)}
    pestana_ingreso.render(datos, mostrar=visibles)


def pronostico() -> None:
    st.caption(
        "Compara lo que estimó cada modelo con lo que ocurrió en el periodo de prueba. "
        "La línea continua es el dato real y la punteada, la estimación del modelo elegido."
    )
    _graficas("Pronóstico", df)


def metodologia() -> None:
    st.header("Cómo leer este tablero")
    st.markdown(
        """
        **Términos**
        - **Visitante:** persona que ingresa al país por turismo. Incluye al **turista**, que pasa al menos
          una noche en Guatemala, y al **excursionista**, que entra y sale el mismo día.
        - **Estacionalidad:** patrón que se repite cada año, como el aumento de visitantes en diciembre.
        - **Conjunto de entrenamiento y de prueba:** los modelos aprenden con los datos más antiguos
          (entrenamiento) y se evalúan comparando su estimación con lo que ocurrió después (prueba).
        - **MAE (error absoluto medio):** en promedio, cuántos visitantes por mes se equivoca el modelo.
        - **RMSE (raíz del error cuadrático medio):** parecido al MAE, pero da más peso a los errores grandes.

        **Colores**
        - El azul representa datos observados y el ámbar, estimaciones de los modelos. El dato real se
          dibuja con línea continua y la estimación con línea punteada.
        - Cada región, vía y tipo de visitante conserva el mismo color en todas las gráficas.

        **Cambios en la fuente de datos**
        - Entre 2022 y 2023 cambió la definición de "Tipo de Viajero": la categoría "Viajero" deja de
          incluir viajeros no turísticos de alta frecuencia y cae de forma artificial. Por eso el tablero
          muestra solo turistas y excursionistas.
        - Desde 2023 la fuente agrupa los países pequeños en mercados, así que su detalle individual
          termina en 2022.
        - La vía marítima tiene años sin reportes.
        - 2026 solo tiene datos hasta junio.

        **Limitaciones**
        - Los modelos se entrenaron con datos hasta el inicio de la recuperación tras la pandemia, un
          periodo muy atípico, lo que reduce su precisión.
        - Cada modelo da un solo valor por mes, sin un rango de posibles valores; el margen de error se
          comunica con el MAE.
        - Las gráficas describen patrones: no permiten afirmar las causas de los cambios.
        """
    )
    st.caption(
        "Fuente: registros de ingreso de viajeros internacionales 2009 a junio de 2026 (IGM / INGUAT), "
        "base del Laboratorio 1. Uso exclusivamente académico; no son cifras oficiales."
    )


df = cargar_datos()

pagina = st.navigation(
    [
        st.Page(panorama, title="Panorama", url_path="panorama", default=True),
        st.Page(mercados, title="Mercados", url_path="mercados"),
        st.Page(ingreso, title="Ingreso", url_path="ingreso"),
        st.Page(pronostico, title="Pronóstico", url_path="pronostico"),
        st.Page(metodologia, title="Metodología", url_path="metodologia"),
    ],
    position="top",
)

with st.sidebar:
    with st.container(horizontal_alignment="center"):
        st.image(LOGO, width=190)
    if pagina.title in ("Panorama", "Mercados", "Ingreso"):
        st.header("Filtros")
        filtros = _barra_filtros(df, pagina.title)
    else:
        filtros = None
        if pagina.title == "Pronóstico":
            st.header("Controles")
            _barra_pronostico()
    st.divider()
    st.caption("Fuente: IGM / INGUAT, 2009 a junio de 2026. Uso académico, no son cifras oficiales.")

datos = aplicar_filtros(df, filtros) if filtros else df
pagina.run()
