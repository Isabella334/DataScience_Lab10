"""
Paleta de colores del tablero (fuente única de verdad).

PROVISIONAL: basada en Okabe-Ito (segura para daltonismo) mientras la Persona 2
entrega los códigos hex definitivos. Para cambiarla, editar SOLO este archivo
(y los colores base de .streamlit/config.toml).

Regla de significado: cada categoría conserva su color en TODAS las gráficas.
"""

# Colores de interfaz
PRIMARIO = "#0B5C8A"      # acento principal: títulos, serie total, botones
SECUNDARIO = "#E69F00"    # resaltado / selección del usuario
FONDO = "#FFFFFF"
FONDO_SUAVE = "#F3F6F9"
TEXTO = "#1F2933"
TEXTO_SUAVE = "#5F6B7A"
REJILLA = "#E3E8EE"

# Semántica fija para modelos (observado vs. estimado)
OBSERVADO = "#1F2933"
PREDICCION = "#0072B2"
INTERVALO = "rgba(0, 114, 178, 0.15)"

# Categorías: Okabe-Ito + grises para lo residual
_CATEGORICA = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]

COLOR_VIA = {
    "Aérea": "#0072B2",
    "Terrestre": "#009E73",
    "Marítima": "#56B4E9",
}

COLOR_REGION = {
    "América Del Centro": "#0072B2",
    "América Del Norte": "#E69F00",
    "Europa": "#009E73",
    "América Del Sur y el Caribe": "#CC79A7",
    "Asia": "#D55E00",
    "Cruceros": "#56B4E9",
    "Oceanía": "#F0E442",
    "Oriente Medio": "#8C6D31",
    "Otros Países Del Mundo": "#9AA5B1",
}

COLOR_TIPO_VIAJERO = {
    "Turista": "#0072B2",
    "Excursionista": "#E69F00",
    "Cruceristas": "#56B4E9",
    "Viajero": "#9AA5B1",
}

MAPAS_COLOR = {
    "via": COLOR_VIA,
    "region": COLOR_REGION,
    "tipo_viajero": COLOR_TIPO_VIAJERO,
}


def color_para(columna: str, valor: str, i: int = 0) -> str:
    """Color fijo de una categoría; si no está mapeada usa la secuencia categórica."""
    return MAPAS_COLOR.get(columna, {}).get(valor, _CATEGORICA[i % len(_CATEGORICA)])
