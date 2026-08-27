
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
import pandas as pd
from sqlalchemy import text

from src.config import get_engine


STOCK_CODE = "22197"


def load_weekly_demand():
    """Load weekly product demand directly from PostgreSQL."""

    engine = get_engine()

    query = text("""
        SELECT
            DATE_TRUNC('week', invoice_date)::date AS week_start,
            SUM(quantity) AS units_sold
        FROM transactions
        WHERE is_valid_sale = TRUE
          AND stock_code = :stock_code
        GROUP BY DATE_TRUNC('week', invoice_date)::date
        ORDER BY week_start;
    """)

    df = pd.read_sql(
        query,
        engine,
        params={"stock_code": STOCK_CODE}
    )

    df["week_start"] = pd.to_datetime(df["week_start"])

    return df


def prepare_time_series(df):
    """Create a continuous weekly demand series."""

    df = df.set_index("week_start")

    # Create every week between first and last observation
    full_weeks = pd.date_range(
        start=df.index.min(),
        end=df.index.max(),
        freq="W-MON"
    )

    df = df.reindex(full_weeks)

    # No transaction during a week means zero units sold
    df["units_sold"] = df["units_sold"].fillna(0)

    df.index.name = "week_start"

    return df.reset_index()

def create_features(df):
    """Create lag and rolling-demand features."""

    df = df.copy()

    # Previous weekly demand
    df["lag_1"] = df["units_sold"].shift(1)
    df["lag_2"] = df["units_sold"].shift(2)
    df["lag_4"] = df["units_sold"].shift(4)

    # Rolling averages use only previous weeks
    df["rolling_mean_4"] = (
        df["units_sold"]
        .shift(1)
        .rolling(window=4)
        .mean()
    )

    df["rolling_mean_8"] = (
        df["units_sold"]
        .shift(1)
        .rolling(window=8)
        .mean()
    )

    # Calendar features
    df["month"] = df["week_start"].dt.month
    df["week_of_year"] = df["week_start"].dt.isocalendar().week.astype(int)

    # Remove rows that don't yet have enough history
    df = df.dropna().reset_index(drop=True)

    return df


def train_and_evaluate(df):
    """Train forecasting model using chronological split."""

    features = [
        "lag_1",
        "lag_2",
        "lag_4",
        "rolling_mean_4",
        "rolling_mean_8",
        "month",
        "week_of_year",
    ]

    target = "units_sold"

    # Last 10 weeks become our test period
    train = df.iloc[:-10].copy()
    test = df.iloc[-10:].copy()

    print(f"\nTraining weeks: {len(train)}")
    print(f"Testing weeks: {len(test)}")

    # --------------------------------------------------
    # Baseline
    # Predict this week using previous week's demand
    # --------------------------------------------------

    baseline_predictions = test["lag_1"]

        # Additional forecasting baselines
    moving_avg_4_predictions = test["rolling_mean_4"]
    moving_avg_8_predictions = test["rolling_mean_8"]

    moving_avg_4_mae = mean_absolute_error(
        test[target],
        moving_avg_4_predictions
    )

    moving_avg_4_rmse = np.sqrt(
        mean_squared_error(
            test[target],
            moving_avg_4_predictions
        )
    )

    moving_avg_8_mae = mean_absolute_error(
        test[target],
        moving_avg_8_predictions
    )

    moving_avg_8_rmse = np.sqrt(
        mean_squared_error(
            test[target],
            moving_avg_8_predictions
        )
    )

    baseline_mae = mean_absolute_error(
        test[target],
        baseline_predictions
    )

    baseline_rmse = np.sqrt(
        mean_squared_error(
            test[target],
            baseline_predictions
        )
    )

    # --------------------------------------------------
    # Random Forest
    # --------------------------------------------------

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=5,
        random_state=42
    )

    model.fit(
        train[features],
        train[target]
    )

    predictions = model.predict(test[features])

    model_mae = mean_absolute_error(
        test[target],
        predictions
    )

    model_rmse = np.sqrt(
        mean_squared_error(
            test[target],
            predictions
        )
    )

    # --------------------------------------------------
    # Results
    # --------------------------------------------------

    results = test[
        ["week_start", "units_sold"]
    ].copy()

    results["naive_forecast"] = baseline_predictions.values
    results["moving_avg_4"] = moving_avg_4_predictions.values
    results["moving_avg_8"] = moving_avg_8_predictions.values
    results["random_forest"] = predictions

    print("\n" + "=" * 50)
    print("FORECAST MODEL EVALUATION")
    print("=" * 50)

    print("\nNaive Baseline")
    print(f"MAE:  {baseline_mae:.2f}")
    print(f"RMSE: {baseline_rmse:.2f}")

    print("\n4-Week Moving Average")
    print(f"MAE:  {moving_avg_4_mae:.2f}")
    print(f"RMSE: {moving_avg_4_rmse:.2f}")

    print("\n8-Week Moving Average")
    print(f"MAE:  {moving_avg_8_mae:.2f}")
    print(f"RMSE: {moving_avg_8_rmse:.2f}")

    print("\nRandom Forest")
    print(f"MAE:  {model_mae:.2f}")
    print(f"RMSE: {model_rmse:.2f}")

    print("\nForecast comparison:")
    print(results.to_string(index=False))

    return model, results

def main():

    print("Loading weekly demand from PostgreSQL...")

    df = load_weekly_demand()

    print(f"Product: {STOCK_CODE}")
    print(f"Observed weeks: {len(df)}")

    df = prepare_time_series(df)

    print(f"Continuous weeks: {len(df)}")

    print("\nFirst weeks:")
    print(df.head())

    print("\nLast weeks:")
    print(df.tail())

    print("\nDemand statistics:")
    print(df["units_sold"].describe())

    print("\nCreating forecasting features...")

    feature_df = create_features(df)

    print(f"Rows available for modeling: {len(feature_df)}")

    model, results = train_and_evaluate(feature_df)


if __name__ == "__main__":
    main()