"""
Paleta de colores del tablero (fuente única de verdad).

Paleta base (Coolors), justificada en el documento de diseño:
    Ghost White  #FEF9FF   (en pantalla se veía lila; el fondo usa el neutro #FAFAFA)
    Graphite     #2E2F2F   texto, ejes e íconos
    Sky Aqua     #56CBF9   primario: datos observados (rellenos)
    Amber Earth  #E8871E   acento: predicciones y selección (rellenos)
    Honey Bronze #EDB458   advertencias, datos preliminares y referencias (nivel 2019)

Los tres colores base son claros: como relleno con texto oscuro encima cumplen contraste
(5-7:1), pero como línea o texto sobre el fondo no. Para líneas y texto se usan sus
variantes oscuras (AZUL_LINEA 3.7:1, AZUL_TEXTO 7:1, AMBAR_LINEA 3.7:1).

Regla de significado (igual en todo el tablero):
    azul sólido  = dato observado / real
    ámbar punteado = predicción de un modelo
    honey        = advertencia o referencia
    gris         = otras categorías / sin datos

Cada color y cada categoría conservan su significado en todas las gráficas.
La fuente (Inter) y los colores por defecto de las gráficas (categórica y escala secuencial)
se configuran en .streamlit/config.toml, porque Streamlit aplica su propio tema a Plotly.
Para cambiar colores, editar SOLO este archivo y .streamlit/config.toml.
"""

# Colores base
GHOST_WHITE = "#FEF9FF"
GRAPHITE = "#2E2F2F"
SKY_AQUA = "#56CBF9"
HONEY_BRONZE = "#EDB458"
AMBER_EARTH = "#E8871E"

# Variantes oscuras para líneas y texto (mismo matiz, menor luminosidad)
AZUL_LINEA = "#1689C4"
AZUL_TEXTO = "#0B5C86"
AMBAR_LINEA = "#C56A10"

# Neutros
GRIS_TEXTO = "#5A5B5B"
GRIS_CLARO = "#C4C5C5"
GRIS_BORDE = "#E2E0E6"
GRIS_SIN_DATOS = "#9AA0A6"

# Colores de interfaz
PRIMARIO = AZUL_LINEA       # serie total y cifras clave en gráficas
TITULOS = AZUL_TEXTO        # títulos y valores de indicadores
SECUNDARIO = AMBER_EARTH    # resaltado / selección del usuario
REFERENCIA = HONEY_BRONZE   # líneas de referencia (nivel 2019, quiebres)
FONDO = "#FAFAFA"           # fondo de página: casi blanco neutro (Ghost White se veía lila en pantalla)
FONDO_SUAVE = "#F2F2F3"     # barra lateral y pestaña al pasar el cursor (gris neutro derivado de Graphite)
TARJETA = "#FFFFFF"         # fondo de tarjetas (indicadores y gráficas)
SOMBRA = "rgba(46, 47, 47, 0.08)"
TEXTO = GRAPHITE
TEXTO_SUAVE = GRIS_TEXTO
REJILLA = GRIS_BORDE
SIN_DATOS = GRIS_SIN_DATOS

# Semántica de modelos (observado vs. estimado)
OBSERVADO = AZUL_LINEA
PREDICCION = AMBAR_LINEA
ESTILO_PREDICCION = "dash"
ENTRENAMIENTO = GRIS_CLARO
OTROS_MODELOS = GRIS_CLARO
OTROS = GRIS_CLARO          # categoría "Otras" agrupada

# Categórica accesible para daltonismo (base Okabe-Ito anclada a la marca)
_CATEGORICA = ["#1689C4", "#E8871E", "#009E73", "#CC79A7", "#6A4C93", "#117733"]

# Magnitud (p. ej. mapa de calor): un solo matiz de claro a oscuro, como [posición, color] de Plotly.
# Se lee por luminosidad, así que funciona también con daltonismo.
ESCALA_SECUENCIAL = [
    [0.0, "#E3F4FD"],
    [0.25, "#9BDBF7"],
    [0.5, SKY_AQUA],
    [0.75, AZUL_LINEA],
    [1.0, AZUL_TEXTO],
]
# Bajo / promedio / alto: azul y ámbar con centro neutro
ESCALA_DIVERGENTE = [AZUL_TEXTO, "#F4F1F7", AMBAR_LINEA]

COLOR_VIA = {
    "Terrestre": _CATEGORICA[0],
    "Aérea": _CATEGORICA[1],
    "Marítima": _CATEGORICA[2],
}

COLOR_REGION = {
    "América Del Centro": _CATEGORICA[0],
    "América Del Norte": _CATEGORICA[1],
    "Europa": _CATEGORICA[2],
    "América Del Sur y el Caribe": _CATEGORICA[3],
    "Asia": _CATEGORICA[4],
    "Oceanía": _CATEGORICA[5],
    "Cruceros": GRIS_CLARO,
    "Oriente Medio": GRIS_CLARO,
    "Otros Países Del Mundo": GRIS_CLARO,
}

COLOR_TIPO_VIAJERO = {
    "Turista": _CATEGORICA[0],
    "Excursionista": _CATEGORICA[1],
    "Cruceristas": _CATEGORICA[2],
    "Viajero": GRIS_CLARO,
}

MAPAS_COLOR = {
    "via": COLOR_VIA,
    "region": COLOR_REGION,
    "tipo_viajero": COLOR_TIPO_VIAJERO,
}


def color_para(columna: str, valor: str, i: int = 0) -> str:
    """Color fijo de una categoría; si no está mapeada usa la secuencia categórica."""
    return MAPAS_COLOR.get(columna, {}).get(valor, _CATEGORICA[i % len(_CATEGORICA)])
