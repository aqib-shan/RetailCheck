import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from src.config import get_engine
from src.forecast_products import (
    load_products,
    load_weekly_demand,
    prepare_series,
    create_features,
    evaluate_product,
)


FORECAST_HORIZON = 4


FEATURES = [
    "lag_1",
    "lag_2",
    "lag_4",
    "rolling_mean_4",
    "rolling_mean_8",
    "month",
    "week_of_year",
]


def train_random_forest(history):
    """Train Random Forest using all available historical data."""

    feature_df = create_features(history)

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=5,
        random_state=42,
    )

    model.fit(
        feature_df[FEATURES],
        feature_df["units_sold"],
    )

    return model


def build_future_features(history, future_date):
    """Build features for the next forecast week."""

    units = history["units_sold"]

    features = pd.DataFrame(
        {
            "lag_1": [units.iloc[-1]],
            "lag_2": [units.iloc[-2]],
            "lag_4": [units.iloc[-4]],
            "rolling_mean_4": [
                units.iloc[-4:].mean()
            ],
            "rolling_mean_8": [
                units.iloc[-8:].mean()
            ],
            "month": [future_date.month],
            "week_of_year": [
                future_date.isocalendar().week
            ],
        }
    )

    return features


def forecast_product(stock_code, model_name):
    """Generate recursive 4-week forecast for one product."""

    history = load_weekly_demand(stock_code)
    history = prepare_series(history)

    history["week_start"] = pd.to_datetime(
        history["week_start"]
    )

    model = None

    if model_name == "Random Forest":
        model = train_random_forest(history)

    forecasts = []

    for _ in range(FORECAST_HORIZON):

        future_date = (
            history["week_start"].max()
            + pd.Timedelta(weeks=1)
        )

        if model_name == "Naive":

            prediction = history[
                "units_sold"
            ].iloc[-1]

        elif model_name == "Moving Average 4":

            prediction = history[
                "units_sold"
            ].iloc[-4:].mean()

        elif model_name == "Moving Average 8":

            prediction = history[
                "units_sold"
            ].iloc[-8:].mean()

        elif model_name == "Random Forest":

            future_features = build_future_features(
                history,
                future_date,
            )

            prediction = model.predict(
                future_features[FEATURES]
            )[0]

        else:
            raise ValueError(
                f"Unknown model: {model_name}"
            )

        # Demand cannot be negative
        prediction = max(0, prediction)

        forecasts.append(
            {
                "stock_code": stock_code,
                "forecast_week": future_date,
                "forecast_units": round(
                    prediction,
                    2,
                ),
                "model": model_name,
            }
        )

        # Add prediction to history so next forecast
        # can use it as a lag value.
        new_row = pd.DataFrame(
            {
                "week_start": [future_date],
                "units_sold": [prediction],
            }
        )

        history = pd.concat(
            [history, new_row],
            ignore_index=True,
        )

    return forecasts


def main():

    print("Loading products...")

    products = load_products()

    all_forecasts = []

    for _, product in products.iterrows():

        stock_code = product["stock_code"]

        evaluation = evaluate_product(stock_code)

        if evaluation is None:
            continue

        best_model = evaluation["best_model"]

        print(
            f"Forecasting {stock_code} "
            f"using {best_model}"
        )

        forecasts = forecast_product(
            stock_code,
            best_model,
        )

        for forecast in forecasts:
            forecast["product"] = product["product"]

        all_forecasts.extend(forecasts)

    forecast_df = pd.DataFrame(all_forecasts)

    forecast_df = forecast_df[
        [
            "stock_code",
            "product",
            "forecast_week",
            "forecast_units",
            "model",
        ]
    ]

    output_path = (
        "data/processed/"
        "product_demand_forecasts.csv"
    )

    forecast_df.to_csv(
        output_path,
        index=False,
    )

    print("\n" + "=" * 70)
    print("4-WEEK PRODUCT DEMAND FORECAST")
    print("=" * 70)

    print(forecast_df.to_string(index=False))

    print(
        f"\nForecasts saved to {output_path}"
    )


if __name__ == "__main__":
    main()