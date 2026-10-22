# Observatorio de Turismo Sostenible · Guatemala

Tablero interactivo para directivos del sector turístico (CC3066 Data Science · Lab 10, UVG 2026).
Reutiliza los datos y modelos de los Laboratorios 1 y 2 (ingreso de viajeros internacionales 2009 – jun 2026).

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
python data/procesar_datos.py   # opcional: la app lo genera sola si falta el parquet
streamlit run app.py
```

## Estructura

```
app.py                     # punto de entrada: layout, filtros globales y pestañas
.streamlit/config.toml     # tema base (colores sincronizados con src/paleta.py)
data/
  raw/                     # Excel original de los Labs 1 y 2
  processed/               # viajeros.parquet (datos limpios que usa la app)
  procesar_datos.py        # limpieza: Excel -> parquet
src/
  paleta.py                # ÚNICA fuente de colores (Persona 2 actualiza los hex aquí)
  datos.py                 # carga en caché, filtros globales, formato de números
  viz/
    serie_temporal.py      # Visualización 1 – evolución de llegadas (Persona 3)
    viz2.py                # Visualización 2 (Persona 4)
docs/                      # documento de diseño y material del avance
```

### Convenciones para el equipo

- **Cada visualización es un módulo en `src/viz/`** con una función `render(df)`; `app.py` solo la llama
  dentro de la pestaña correspondiente. Así cada quien trabaja en su archivo sin conflictos.
- **Colores:** nunca escribir un hex dentro de una gráfica; usar `src/paleta.py`
  (`paleta.color_para("region", valor)`), para que cada categoría tenga el mismo color en todo el tablero.
- **Gráficas enlazadas:** la visualización 1 guarda el periodo seleccionado por el usuario en
  `st.session_state["periodo_seleccionado"]` como `(inicio, fin)` o `None`. Las demás gráficas pueden
  leerlo para filtrarse (ver `src/viz/viz2.py`).
- Si una selección deja la gráfica sin datos, mostrar `st.info(...)` con un mensaje claro.

## Justificación de la herramienta: Streamlit + Plotly (Python)

| Criterio | Streamlit | Dash | Shiny (R) |
|---|---|---|---|
| Lenguaje de los Labs 1 y 2 (Python, pandas, statsmodels, Prophet, Keras) | ✅ mismo stack, se reutiliza código y resultados directamente | ✅ | ❌ habría que portar todo a R |
| Tiempo de desarrollo (avance en 1 día, final en 3) | ✅ muy rápido: un script, sin HTML/CSS ni callbacks | ⚠️ más código (layout + callbacks explícitos) | ⚠️ |
| Gráficas enlazadas (clic/arrastre en una filtra otra) | ✅ `st.plotly_chart(on_select=...)` + `session_state` | ✅ callbacks | ✅ |
| Aumentar/disminuir detalle | ✅ controles nativos + zoom/rangeslider de Plotly | ✅ | ✅ |
| Trabajo en paralelo de 4 personas | ✅ un módulo por visualización | ✅ | ⚠️ |
| Despliegue gratuito | ✅ Streamlit Community Cloud desde GitHub | ⚠️ requiere servidor propio (Render, etc.) | ⚠️ shinyapps.io con límite de horas |
| Código abierto y gratuito | ✅ Apache 2.0 | ✅ MIT | ✅ GPL |

**Conclusión.** Streamlit es la opción más adecuada porque: (1) todo el trabajo previo (limpieza,
modelos ARIMA/SARIMA, Holt-Winters, Prophet y LSTM) está en Python, así que las predicciones y métricas
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
- **Interacción:** nivel de detalle mes/trimestre/año, desglose por región/vía/tipo de viajero,
  rangeslider para hacer zoom en el tiempo y selección por arrastre o clic que filtra la visualización 2.
