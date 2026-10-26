"""
Modelos de pronóstico del Lab 1 para el tablero.

Ajusta los 5 modelos del Laboratorio 1 en las 7 series de SERIES y guarda en data/processed/:
    predicciones.parquet: serie, modelo, fecha, real, prediccion, conjunto ("entrenamiento" o "prueba")
    metricas.parquet:     serie, modelo, mae, rmse  (calculadas en el conjunto de prueba)

No se construyen modelos nuevos: se repite la configuración de los notebooks del Lab 1
(corte 70/30, SARIMA(1,1,1)(1,1,1)[12] sobre log1p, Holt-Winters aditivo, SES, seasonal naive y Prophet
con estacionalidad anual) en todas las series, para que los errores sean comparables entre series.
El SARIMA se ajusta con las restricciones de estacionariedad e invertibilidad de serie_paises_residencia.ipynb:
sin ellas, en escala log la caída de 2020 hace que el pronóstico crezca sin límite en varias series.

Diferencias con los notebooks del Lab 1, para que las series coincidan con lo que muestra el tablero:
- Solo se cuentan turistas y excursionistas ("Viajero" cambia de definición entre 2022 y 2023).
- Las predicciones negativas se llevan a 0 (no puede haber visitantes negativos).
- En el conjunto de entrenamiento "prediccion" queda vacía: el tablero solo muestra el pronóstico de prueba.

Uso (requiere requirements-modelos.txt, Python <= 3.13):
    python data/entrenar_modelos.py
"""
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from prophet import Prophet
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

RAIZ = Path(__file__).resolve().parent
VIAJEROS = RAIZ / "processed" / "viajeros.parquet"
PREDICCIONES = RAIZ / "processed" / "predicciones.parquet"
METRICAS = RAIZ / "processed" / "metricas.parquet"

VISITANTES = ("Turista", "Excursionista")
PROPORCION_ENTRENAMIENTO = 0.7

# Nombre en el tablero -> (columna, valor en los datos). Los nombres deben coincidir con
# SERIES_MODELO de src/datos.py (no se importa porque src/datos.py depende de Streamlit).
SERIES = {
    "Total": None,
    "América del Centro": ("region", "América Del Centro"),
    "América del Norte": ("region", "América Del Norte"),
    "Europa": ("region", "Europa"),
    "El Salvador": ("pais", "El Salvador"),
    "Estados Unidos": ("pais", "Estados Unidos de América"),
    "Honduras": ("pais", "Honduras"),
}


def construir_serie(df: pd.DataFrame, filtro: tuple[str, str] | None) -> pd.Series:
    """Serie mensual de toda la base (meses sin registros = 0), así todas tienen el mismo corte."""
    meses = pd.date_range(df["fecha"].min(), df["fecha"].max(), freq="MS")
    if filtro:
        columna, valor = filtro
        df = df[df[columna] == valor]
    return df.groupby("fecha")["viajeros"].sum().reindex(meses, fill_value=0).astype(float)


def sarima(entrenamiento: pd.Series, h: int) -> np.ndarray:
    modelo = SARIMAX(np.log1p(entrenamiento), order=(1, 1, 1), seasonal_order=(1, 1, 1, 12),
                     enforce_stationarity=True, enforce_invertibility=True).fit(disp=False, method="lbfgs", maxiter=200)
    return np.expm1(modelo.get_forecast(steps=h).predicted_mean.to_numpy())


def holt_winters(entrenamiento: pd.Series, h: int) -> np.ndarray:
    modelo = ExponentialSmoothing(entrenamiento, trend="add", seasonal="add", seasonal_periods=12).fit()
    return modelo.forecast(h).to_numpy()


def ses(entrenamiento: pd.Series, h: int) -> np.ndarray:
    return SimpleExpSmoothing(entrenamiento, initialization_method="estimated").fit().forecast(h).to_numpy()


def seasonal_naive(entrenamiento: pd.Series, h: int) -> np.ndarray:
    """Repite los últimos 12 meses de entrenamiento."""
    ultimo_anio = entrenamiento.iloc[-12:].to_numpy()
    return np.tile(ultimo_anio, int(np.ceil(h / 12)))[:h]


def prophet(entrenamiento: pd.Series, h: int) -> np.ndarray:
    modelo = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    modelo.fit(pd.DataFrame({"ds": entrenamiento.index, "y": entrenamiento.to_numpy()}))
    futuro = modelo.make_future_dataframe(periods=h, freq="MS").iloc[-h:]
    return modelo.predict(futuro)["yhat"].to_numpy()


# Nombres deben coincidir con MODELOS de src/datos.py
MODELOS = {
    "Prophet": prophet,
    "SARIMA": sarima,
    "Holt-Winters": holt_winters,
    "Suavizamiento exponencial simple": ses,
    "Seasonal naive": seasonal_naive,
}


def main() -> None:
    warnings.filterwarnings("ignore")
    logging.getLogger("cmdstanpy").disabled = True
    logging.getLogger("prophet").setLevel(logging.WARNING)

    df = pd.read_parquet(VIAJEROS)
    df = df[df["tipo_viajero"].isin(VISITANTES)]

    predicciones, metricas = [], []
    for nombre_serie, filtro in SERIES.items():
        serie = construir_serie(df, filtro)
        corte = int(len(serie) * PROPORCION_ENTRENAMIENTO)  # mismo corte que el Lab 1 (último mes de entrenamiento: mar 2021)
        entrenamiento, prueba = serie.iloc[:corte], serie.iloc[corte:]

        for nombre_modelo, ajustar in MODELOS.items():
            pred = np.clip(ajustar(entrenamiento, len(prueba)), 0, None)
            error = prueba.to_numpy() - pred
            metricas.append({
                "serie": nombre_serie, "modelo": nombre_modelo,
                "mae": float(np.mean(np.abs(error))), "rmse": float(np.sqrt(np.mean(error ** 2))),
            })
            predicciones.append(pd.DataFrame({
                "serie": nombre_serie, "modelo": nombre_modelo, "fecha": serie.index,
                "real": serie.to_numpy(),
                "prediccion": np.concatenate([np.full(len(entrenamiento), np.nan), pred]),
                "conjunto": ["entrenamiento"] * len(entrenamiento) + ["prueba"] * len(prueba),
            }))
            print(f"{nombre_serie:<20} {nombre_modelo:<34} MAE = {metricas[-1]['mae']:>12,.0f}")

    pd.concat(predicciones, ignore_index=True).to_parquet(PREDICCIONES, index=False)
    pd.DataFrame(metricas).to_parquet(METRICAS, index=False)
    print(f"\nGuardado: {PREDICCIONES.name} y {METRICAS.name} en {PREDICCIONES.parent}")


if __name__ == "__main__":
    main()
