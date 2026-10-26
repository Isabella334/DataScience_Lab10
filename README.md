# Observatorio de Turismo Sostenible · Guatemala

Tablero interactivo para directivos del sector turístico (CC3066 Data Science · Lab 10, UVG 2026).
Reutiliza los datos y modelos del Laboratorio 1 (ingreso de viajeros internacionales 2009 – jun 2026).

## Cómo ejecutarlo

Se necesita Python 3.10 o superior. Desde la carpeta del repositorio:

```bash
python3 -m venv .venv            # solo la primera vez
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt  # solo la primera vez o si cambia requirements.txt
streamlit run app.py
```

La app se abre en http://localhost:8501. Si falta `data/processed/viajeros.parquet`, la app lo genera
sola desde el Excel (o se puede generar con `python data/procesar_datos.py`).

### Recalcular los modelos (solo si cambian los datos)

`predicciones.parquet` y `metricas.parquet` ya están en el repositorio, así que la app no necesita
Prophet. Para volver a calcularlos se usa un entorno aparte con Python 3.13 o anterior (Prophet aún no
es estable en 3.14):

```bash
py -3.13 -m venv .venv-modelos                   # en Mac/Linux: python3.13 -m venv .venv-modelos
.venv-modelos\Scripts\activate                   # en Mac/Linux: source .venv-modelos/bin/activate
pip install -r requirements-modelos.txt
python data/entrenar_modelos.py                  # tarda ~1 minuto: 7 series × 5 modelos
```

## Estructura

```
app.py                     # punto de entrada: navegación, barra lateral, indicadores y Metodología
.streamlit/config.toml     # tema (colores sincronizados con src/paleta.py y fuente Inter)
data/
  raw/                     # Excel original del Lab 1
  processed/               # viajeros.parquet (+ predicciones.parquet y metricas.parquet de los modelos)
  procesar_datos.py        # limpieza: Excel -> parquet
  entrenar_modelos.py      # 5 modelos del Lab 1 en 7 series -> predicciones.parquet y metricas.parquet
src/
  paleta.py                # ÚNICA fuente de colores del tablero y su significado
  datos.py                 # carga en caché, filtros, constantes de series y modelos, formato
  pestanas/
    ingreso.py             # pestaña Ingreso: indicadores y distribución de sus gráficas
  viz/                     # un archivo por gráfica (ver tabla abajo)
    serie_temporal.py      # evolución de visitantes (P1)
    mercados.py            # regiones y ranking de países, enlazadas (P2; regiones.py y paises.py la exponen)
    vias_fronteras.py      # vías de ingreso y ranking de fronteras, enlazadas (P3)
    estacionalidad.py      # mapa de calor año × mes (P4)
    tipo_visitante.py      # tipo de visitante por vía (P5)
    pronostico_real.py     # pronóstico frente a lo real, enlazada con error_modelos.py
    error_modelos.py       # MAE/RMSE por modelo (serie elegida o matriz de todas las series)
```

### Convenciones del código

- **Cada visualización es un módulo en `src/viz/`** con una función `render(df)`. `app.py` ya tiene
  registradas las gráficas; si un archivo todavía no existe, la pestaña muestra "Esta gráfica estará
  disponible próximamente". Al crear el archivo, la gráfica aparece sola. No hace falta editar `app.py`.

  | Pestaña | Archivo en `src/viz/` |
  |---|---|
  | Panorama | `serie_temporal.py` (lista; recibe el nivel de detalle de la barra lateral) |
  | Mercados | `regiones.py`, `paises.py` (la lógica de ambas está en `mercados.py`) |
  | Ingreso | `vias_fronteras.py`, `estacionalidad.py`, `tipo_visitante.py` (acomodadas por `src/pestanas/ingreso.py`) |
  | Pronóstico | `pronostico_real.py`, `error_modelos.py` |

- **Pestaña Ingreso:** su distribución y sus indicadores están en `src/pestanas/ingreso.py`, que recibe
  las gráficas marcadas en "Mostrar". Para agregar una gráfica a Ingreso, registrarla en su `GRAFICAS`.

- **`df` ya viene filtrado** por año, vía y tipo de visitante (en Pronóstico llega la base completa).
  Si queda vacío, mostrar `st.info("No hay datos para esta selección.")`.
- **Valores de la barra lateral en `st.session_state`:** `"detalle"` (`"Anual"` o `"Mensual"`); en
  Pronóstico, `"pronostico_serie"`, `"pronostico_modelo"` y `"pronostico_comparar"` (bool).
- **Gráficas enlazadas:** se comunican por `st.session_state`: `"region_seleccionada"` (regiones a
  países), `"via_seleccionada"` (vías a fronteras), `"periodo_seleccionado"` (V1, `(inicio, fin)` o `None`)
  y, en Pronóstico, un clic en el error de un modelo cambia `"pronostico_modelo"` (y `"pronostico_serie"`
  desde la matriz), que también actualiza la barra lateral.
- **Datos de modelos** en `data/processed/`, con los nombres de `SERIES_MODELO` y `MODELOS` de
  `src/datos.py`:
  - `predicciones.parquet`: `serie, modelo, fecha, real, prediccion, conjunto` (`"entrenamiento"` o `"prueba"`).
  - `metricas.parquet`: `serie, modelo, mae, rmse`.
  Los modelos se calculan una vez y se suben los parquet; Prophet no va en `requirements.txt`.
- **Colores:** nunca escribir un hex dentro de una gráfica; usar `src/paleta.py`
  (`paleta.color_para("region", valor)`, `paleta.OBSERVADO`, `paleta.PREDICCION`,
  `paleta.ESCALA_SECUENCIAL`). La fuente Inter y los colores por defecto de las gráficas ya vienen del
  tema en `.streamlit/config.toml`; usar `st.plotly_chart` con el tema por defecto (sin `theme=None`).
- Cada gráfica lleva un `st.subheader` con la pregunta que responde y un `st.caption` corto que explica
  qué muestra y para qué sirve.

## Justificación de la herramienta: Streamlit + Plotly (Python)

| Criterio | Streamlit | Dash | Shiny (R) |
|---|---|---|---|
| Lenguaje del Lab 1 (Python, pandas, statsmodels, Prophet) | ✅ mismo stack, se reutiliza código y resultados directamente | ✅ | ❌ habría que portar todo a R |
| Tiempo de desarrollo (avance en 1 día, final en 3) | ✅ muy rápido: un script, sin HTML/CSS ni callbacks | ⚠️ más código (layout + callbacks explícitos) | ⚠️ |
| Gráficas enlazadas (clic/arrastre en una filtra otra) | ✅ `st.plotly_chart(on_select=...)` + `session_state` | ✅ callbacks | ✅ |
| Aumentar/disminuir detalle | ✅ controles nativos + zoom/rangeslider de Plotly | ✅ | ✅ |
| Trabajo en paralelo de 4 personas | ✅ un módulo por visualización | ✅ | ⚠️ |
| Despliegue gratuito | ✅ Streamlit Community Cloud desde GitHub | ⚠️ requiere servidor propio (Render, etc.) | ⚠️ shinyapps.io con límite de horas |
| Código abierto y gratuito | ✅ Apache 2.0 | ✅ MIT | ✅ GPL |

**Conclusión.** Streamlit es la opción más adecuada porque: (1) todo el trabajo del Lab 1 (limpieza,
modelos SARIMA, Holt-Winters, Prophet, SES y Seasonal Naive) está en Python, así que las predicciones y métricas
se muestran sin reescribir nada; (2) permite construir rápido una interfaz limpia con pestañas, filtros
laterales y tarjetas, adecuada para directivos sin formación estadística; (3) con Plotly obtenemos
interactividad rica (tooltips, zoom, selección por arrastre) y, con `on_select`, gráficas enlazadas;
y (4) se publica gratis desde el repositorio. La principal limitación de Streamlit —que vuelve a ejecutar
el script en cada interacción— se mitiga con `st.cache_data` y con datos en formato parquet.

## Visualización 1 – Evolución de la llegada de viajeros

- **Pregunta de gestión:** ¿cómo ha cambiado la llegada de viajeros y qué segmentos explican los cambios?
- **Tipo de gráfica:** serie de tiempo (líneas), porque la variable principal es un conteo ordenado en el
  tiempo y lo que interesa es la tendencia, la estacionalidad y las rupturas (p. ej. 2020). Con desglose,
  se puede cambiar a área apilada para ver la composición del total.
- **Interacción:** nivel de detalle anual/mensual (barra lateral), desglose por región/vía/tipo de viajero,
  rangeslider para hacer zoom en el tiempo y selección por arrastre o clic que calcula las cifras de ese periodo.
