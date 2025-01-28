import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from models import Sale
import os


os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"


def preprocess_item_data(data):
    if data["sale_date"].dtype != "datetime64[ns]":
        data["sale_date"] = pd.to_datetime(data["sale_date"])

    if not data["sale_date"].is_monotonic_increasing:
        data.sort_values("sale_date", inplace=True)

    feature_columns = []

    month_angle = (2 * np.pi) / 12
    weekday_angle = (2 * np.pi) / 7

    month_rad = data["sale_date"].dt.month * month_angle
    data["month_sin"] = np.sin(month_rad)
    data["month_cos"] = np.cos(month_rad)
    feature_columns.extend(["month_sin", "month_cos"])

    weekday_rad = data["sale_date"].dt.weekday * weekday_angle
    data["weekday_sin"] = np.sin(weekday_rad)
    data["weekday_cos"] = np.cos(weekday_rad)
    feature_columns.extend(["weekday_sin", "weekday_cos"])

    n_samples = len(data)

    desired_lags = [1, 3, 7, 14]
    lag_features = []
    max_lag = 0
    for lag in desired_lags:
        if n_samples >= lag + 1:
            lag_col = f"lag_{lag}"
            data[lag_col] = data["quantity"].shift(lag)
            feature_columns.append(lag_col)
            lag_features.append(lag_col)
            max_lag = max(max_lag, lag)
        else:
            print(f"Недостаточно данных для лаг {lag}")

    if lag_features:
        data = data.iloc[max_lag:].copy()
    else:
        data = data.copy()

    X = data[feature_columns]
    y = data["quantity"]

    print("Размер X:", X.shape)
    print("Размер y:", y.shape)
    print("Используемые признаки:", feature_columns)

    return X, y, feature_columns


def forecast_item_sales(
    model, scaler, last_known_data, forecast_days, feature_columns
):
    last_date = last_known_data["sale_date"].max()
    future_dates = [
        last_date + timedelta(days=i) for i in range(1, forecast_days + 1)
    ]
    future_data = pd.DataFrame({"sale_date": future_dates})

    future_data["month_sin"] = np.sin(
        2 * np.pi * future_data["sale_date"].dt.month / 12
    )
    future_data["month_cos"] = np.cos(
        2 * np.pi * future_data["sale_date"].dt.month / 12
    )
    future_data["weekday_sin"] = np.sin(
        2 * np.pi * future_data["sale_date"].dt.weekday / 7
    )
    future_data["weekday_cos"] = np.cos(
        2 * np.pi * future_data["sale_date"].dt.weekday / 7
    )

    for col in feature_columns:
        if col.startswith("lag_"):
            lag = int(col.split("_")[1])
            if len(last_known_data) >= lag:
                lag_value = last_known_data["quantity"].iloc[-lag]
                future_data[col] = lag_value
            else:
                future_data[col] = 0

    X_future = future_data[feature_columns]
    X_future_scaled = scaler.transform(X_future)
    predictions = model.predict(X_future_scaled).flatten()

    adjusted_predictions = []
    for date, pred in zip(future_data["sale_date"], predictions):
        adjusted_pred = float(pred)
        month = date.month
        if month in [6, 7, 8]:
            adjusted_pred *= 1.3
        elif month in [12, 1, 2]:
            adjusted_pred *= 0.9
        adjusted_predictions.append(max(round(adjusted_pred, 2), 0))

    forecast_list = []
    for date, pred in zip(future_data["sale_date"], adjusted_predictions):
        forecast_list.append(
            {"date": date.strftime("%Y-%m-%d"), "predicted_quantity": pred}
        )

    print(type(pred))

    return forecast_list


def train_item_model(X, y):
    from sklearn.preprocessing import StandardScaler
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Input

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    input_dim = X_scaled.shape[1]
    model = Sequential()
    model.add(Input(shape=(input_dim,)))
    model.add(Dense(64, activation="relu"))
    model.add(Dense(32, activation="relu"))
    model.add(Dense(1))

    model.compile(optimizer="adam", loss="mean_squared_error")

    model.fit(X_scaled, y, epochs=50, verbose=0)

    return model, scaler


def forecast_with_dynamic_features(db_session):
    sales = db_session.query(Sale).all()
    if not sales:
        return []

    data = pd.DataFrame(
        {
            "sale_date": [sale.sale_date for sale in sales],
            "quantity": [sale.quantity for sale in sales],
            "item_id": [sale.item_id for sale in sales],
        }
    )

    unique_items = data["item_id"].unique()

    all_forecasts = []

    for item in unique_items:
        item_data = data[data["item_id"] == item].copy()
        X, y, feature_columns = preprocess_item_data(item_data)

        if len(X) < 1:
            continue

        model, scaler = train_item_model(X, y)

        forecast_days = 20
        forecast_list = forecast_item_sales(
            model, scaler, item_data, forecast_days, feature_columns
        )

        for forecast in forecast_list:
            forecast["item_id"] = item

        all_forecasts.extend(forecast_list)

    return all_forecasts
