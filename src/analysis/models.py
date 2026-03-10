"""
src/analysis/models.py

Modelos preditivos para previsão do Dólar (USD/BRL):

    1. linear_regression_model → Regressão Linear Múltipla (scikit-learn)
    2. arima_model             → Modelo ARIMA de série temporal (statsmodels)
    3. random_forest_model     → Random Forest Regressor (scikit-learn)

Todos retornam um dicionário padronizado com: model, predictions, metrics.
"""

from __future__ import annotations

import warnings
import numpy as np
import pandas as pd
from typing import Any

warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _split(df: pd.DataFrame, target: str, test_size: float = 0.2):
    """Divide features e target em treino/teste cronológico."""
    features = [c for c in df.columns if c != target]
    X = df[features].dropna()
    y = df[target].loc[X.index]

    split_idx = int(len(X) * (1 - test_size))
    return (
        X.iloc[:split_idx], X.iloc[split_idx:],
        y.iloc[:split_idx], y.iloc[split_idx:],
    )


def _regression_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict:
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return {
        "MAE":  round(mean_absolute_error(y_true, y_pred), 4),
        "RMSE": round(rmse, 4),
        "R2":   round(r2_score(y_true, y_pred), 4),
    }


# ---------------------------------------------------------------------------
# 1. Regressão Linear Múltipla
# ---------------------------------------------------------------------------

def linear_regression_model(
    df: pd.DataFrame,
    target: str = "dolar_brl",
    test_size: float = 0.2,
) -> dict[str, Any]:
    """Regressão Linear Múltipla.

    Args:
        df:        DataFrame com variáveis preditoras + target.
        target:    Coluna alvo.
        test_size: Proporção do conjunto de teste.

    Returns:
        dict com: model, X_test, y_test, predictions, metrics, coef.
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline

    X_train, X_test, y_train, y_test = _split(df, target, test_size)

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LinearRegression()),
    ])
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_test)

    coef = dict(zip(X_train.columns, pipe.named_steps["lr"].coef_))

    return {
        "model": pipe,
        "X_test": X_test,
        "y_test": y_test,
        "predictions": pd.Series(preds, index=X_test.index),
        "metrics": _regression_metrics(y_test, preds),
        "coef": coef,
    }


# ---------------------------------------------------------------------------
# 2. ARIMA
# ---------------------------------------------------------------------------

def arima_model(
    series: pd.Series,
    order: tuple[int, int, int] = (1, 1, 1),
    n_forecast: int = 30,
) -> dict[str, Any]:
    """Modelo ARIMA univariado.

    Args:
        series:     Série temporal do target (ex.: dólar).
        order:      (p, d, q) do ARIMA.
        n_forecast: Quantos dias projetar à frente.

    Returns:
        dict com: model_fit, forecast, conf_int, aic, bic.
    """
    from statsmodels.tsa.arima.model import ARIMA

    series = series.dropna().asfreq("B").ffill()   # freq business day
    model = ARIMA(series, order=order)
    fit = model.fit()

    forecast_result = fit.get_forecast(steps=n_forecast)
    forecast_df = forecast_result.summary_frame(alpha=0.05)

    return {
        "model_fit": fit,
        "forecast": forecast_df["mean"],
        "conf_int": forecast_df[["mean_ci_lower", "mean_ci_upper"]],
        "aic": round(fit.aic, 2),
        "bic": round(fit.bic, 2),
        "summary": fit.summary(),
    }


# ---------------------------------------------------------------------------
# 3. Random Forest
# ---------------------------------------------------------------------------

def random_forest_model(
    df: pd.DataFrame,
    target: str = "dolar_brl",
    test_size: float = 0.2,
    n_estimators: int = 200,
    random_state: int = 42,
) -> dict[str, Any]:
    """Random Forest Regressor.

    Args:
        df:            DataFrame com variáveis preditoras + target.
        target:        Coluna alvo.
        test_size:     Proporção do conjunto de teste.
        n_estimators:  Número de árvores.
        random_state:  Semente para reprodutibilidade.

    Returns:
        dict com: model, X_test, y_test, predictions, metrics, feature_importance.
    """
    from sklearn.ensemble import RandomForestRegressor

    X_train, X_test, y_train, y_test = _split(df, target, test_size)

    rf = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    preds = rf.predict(X_test)

    importance = pd.Series(
        rf.feature_importances_, index=X_train.columns
    ).sort_values(ascending=False)

    return {
        "model": rf,
        "X_test": X_test,
        "y_test": y_test,
        "predictions": pd.Series(preds, index=X_test.index),
        "metrics": _regression_metrics(y_test, preds),
        "feature_importance": importance,
    }
