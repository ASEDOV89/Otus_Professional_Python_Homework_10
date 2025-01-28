import pandas as pd
import numpy as np
from forecasting import (
    preprocess_item_data,
    train_item_model,
    forecast_item_sales,
)


def test_preprocess_item_data():
    data = pd.DataFrame(
        {
            "sale_date": pd.date_range(
                start="2025-01-01", periods=10, freq="D"
            ),
            "quantity": np.random.randint(1, 10, size=10),
        }
    )
    X, y, features = preprocess_item_data(data)
    assert not X.empty
    assert len(X) == len(y)
    assert "month_sin" in X.columns
    assert "weekday_cos" in X.columns


def test_train_and_forecast():
    data = pd.DataFrame(
        {
            "sale_date": pd.date_range(
                start="2025-01-01", periods=20, freq="D"
            ),
            "quantity": np.random.randint(1, 10, size=20),
        }
    )
    X, y, features = preprocess_item_data(data)
    model, scaler = train_item_model(X, y)
    forecast_days = 5
    forecast = forecast_item_sales(
        model, scaler, data, forecast_days, features
    )
    assert len(forecast) == forecast_days
    for item in forecast:
        assert "date" in item
        assert "predicted_quantity" in item
        assert item["predicted_quantity"] >= 0
