"""
Paleta de colores del tablero (fuente única de verdad).

Paleta base definida por la Persona 2 (Coolors):
    Ghost White  #FEF9FF   fondo
    Graphite     #2E2F2F   texto y datos observados
    Sky Aqua     #56CBF9   acento frío: predicciones, vía aérea
    Honey Bronze #EDB458   acento cálido suave: referencias (p. ej. nivel 2019)
    Amber Earth  #E8871E   acento cálido fuerte: selección / resaltado

Azul vs. naranja es el par de contraste más seguro para daltonismo (protanopia y
deuteranopia los siguen distinguiendo). Los dos tonos cálidos se diferencian por
luminosidad, no solo por tono.

Sky Aqua sobre el fondo claro tiene poco contraste (~1.8:1), así que para textos y
líneas finas se usa un tono oscuro del mismo matiz (AQUA_OSCURO, 5.3:1, cumple WCAG AA). Los tonos
derivados son variaciones de luminosidad de los 5 colores base, no colores nuevos.

Regla de significado: cada categoría conserva su color en TODAS las gráficas.
Para cambiar la paleta, editar SOLO este archivo y .streamlit/config.toml.
"""

# Colores base (Persona 2)
GHOST_WHITE = "#FEF9FF"
GRAPHITE = "#2E2F2F"
SKY_AQUA = "#56CBF9"
HONEY_BRONZE = "#EDB458"
AMBER_EARTH = "#E8871E"

# Tonos derivados (misma tonalidad, distinta luminosidad)
AQUA_OSCURO = "#1B6F98"
AQUA_CLARO = "#B9E9FC"
AMBER_OSCURO = "#9A5A12"
GRIS_MEDIO = "#6B6D6D"
GRIS_CLARO = "#C4C5C5"

# Colores de interfaz
PRIMARIO = AQUA_OSCURO      # títulos, cifras clave, serie total
SECUNDARIO = AMBER_EARTH    # resaltado / selección del usuario
REFERENCIA = HONEY_BRONZE   # líneas de referencia (nivel 2019, metas)
FONDO = GHOST_WHITE
FONDO_SUAVE = "#F3EEF4"     # tarjetas y barra lateral (Ghost White un poco más oscuro)
TEXTO = GRAPHITE
TEXTO_SUAVE = GRIS_MEDIO
REJILLA = "#ECE7ED"

# Semántica fija para modelos (observado vs. estimado)
OBSERVADO = GRAPHITE
PREDICCION = AQUA_OSCURO
INTERVALO = "rgba(86, 203, 249, 0.25)"  # Sky Aqua translúcido
OTROS = GRIS_CLARO

_CATEGORICA = [AQUA_OSCURO, AMBER_EARTH, SKY_AQUA, HONEY_BRONZE, GRAPHITE, AMBER_OSCURO, AQUA_CLARO, GRIS_MEDIO]

COLOR_VIA = {
    "Aérea": AQUA_OSCURO,
    "Terrestre": AMBER_EARTH,
    "Marítima": SKY_AQUA,
}

COLOR_REGION = {
    "América Del Centro": AQUA_OSCURO,
    "América Del Norte": AMBER_EARTH,
    "Europa": SKY_AQUA,
    "América Del Sur y el Caribe": HONEY_BRONZE,
    "Asia": GRAPHITE,
    "Cruceros": AQUA_CLARO,
    "Oceanía": AMBER_OSCURO,
    "Oriente Medio": GRIS_MEDIO,
    "Otros Países Del Mundo": GRIS_CLARO,
}

COLOR_TIPO_VIAJERO = {
    "Turista": AQUA_OSCURO,
    "Excursionista": AMBER_EARTH,
    "Cruceristas": SKY_AQUA,
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
