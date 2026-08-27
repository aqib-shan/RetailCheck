import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.config import get_engine


TEST_WEEKS = 10
MIN_ACTIVE_WEEKS = 40
TOP_PRODUCTS = 20


def load_products():
    """Load high-volume products with sufficient sales history."""

    engine = get_engine()

    query = f"""
        SELECT
            stock_code,
            MAX(description) AS product,
            COUNT(DISTINCT DATE_TRUNC('week', invoice_date)) AS active_weeks,
            SUM(quantity) AS total_units
        FROM transactions
        WHERE is_valid_sale = TRUE
          AND stock_code NOT IN ('DOT', 'POST', 'M')
        GROUP BY stock_code
        HAVING COUNT(
            DISTINCT DATE_TRUNC('week', invoice_date)
        ) >= {MIN_ACTIVE_WEEKS}
        ORDER BY total_units DESC
        LIMIT {TOP_PRODUCTS};
    """

    return pd.read_sql(query, engine)


def load_weekly_demand(stock_code):
    """Load weekly demand for one product."""

    engine = get_engine()

    query = """
        SELECT
            DATE_TRUNC('week', invoice_date)::date AS week_start,
            SUM(quantity) AS units_sold
        FROM transactions
        WHERE is_valid_sale = TRUE
          AND stock_code = %(stock_code)s
        GROUP BY DATE_TRUNC('week', invoice_date)::date
        ORDER BY week_start;
    """

    return pd.read_sql(
        query,
        engine,
        params={"stock_code": stock_code},
    )


def prepare_series(df):
    """Create continuous weekly time series."""

    df["week_start"] = pd.to_datetime(df["week_start"])

    df = df.set_index("week_start")

    full_weeks = pd.date_range(
        df.index.min(),
        df.index.max(),
        freq="W-MON",
    )

    df = df.reindex(full_weeks)

    df["units_sold"] = df["units_sold"].fillna(0)

    df.index.name = "week_start"

    return df.reset_index()


def create_features(df):
    """Create historical demand features."""

    df = df.copy()

    df["lag_1"] = df["units_sold"].shift(1)
    df["lag_2"] = df["units_sold"].shift(2)
    df["lag_4"] = df["units_sold"].shift(4)

    df["rolling_mean_4"] = (
        df["units_sold"]
        .shift(1)
        .rolling(4)
        .mean()
    )

    df["rolling_mean_8"] = (
        df["units_sold"]
        .shift(1)
        .rolling(8)
        .mean()
    )

    df["month"] = df["week_start"].dt.month

    df["week_of_year"] = (
        df["week_start"]
        .dt.isocalendar()
        .week
        .astype(int)
    )

    return df.dropna().reset_index(drop=True)


def rmse(actual, predicted):
    return np.sqrt(
        mean_squared_error(actual, predicted)
    )


def evaluate_product(stock_code):
    """Evaluate forecasting approaches for one SKU."""

    df = load_weekly_demand(stock_code)
    df = prepare_series(df)
    df = create_features(df)

    if len(df) <= TEST_WEEKS:
        return None

    train = df.iloc[:-TEST_WEEKS]
    test = df.iloc[-TEST_WEEKS:].copy()

    target = "units_sold"

    features = [
        "lag_1",
        "lag_2",
        "lag_4",
        "rolling_mean_4",
        "rolling_mean_8",
        "month",
        "week_of_year",
    ]

    # -------------------------
    # Baselines
    # -------------------------

    naive = test["lag_1"]
    moving_4 = test["rolling_mean_4"]
    moving_8 = test["rolling_mean_8"]

    # -------------------------
    # Random Forest
    # -------------------------

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=5,
        random_state=42,
    )

    model.fit(
        train[features],
        train[target],
    )

    rf_predictions = model.predict(
        test[features]
    )

    # -------------------------
    # Metrics
    # -------------------------

    predictions = {
        "Naive": naive,
        "Moving Average 4": moving_4,
        "Moving Average 8": moving_8,
        "Random Forest": rf_predictions,
    }

    metrics = {}

    for name, prediction in predictions.items():

        metrics[name] = {
            "mae": mean_absolute_error(
                test[target],
                prediction,
            ),
            "rmse": rmse(
                test[target],
                prediction,
            ),
        }

    best_model = min(
        metrics,
        key=lambda name: metrics[name]["mae"],
    )

    return {
        "stock_code": stock_code,
        "naive_mae": metrics["Naive"]["mae"],
        "ma4_mae": metrics["Moving Average 4"]["mae"],
        "ma8_mae": metrics["Moving Average 8"]["mae"],
        "rf_mae": metrics["Random Forest"]["mae"],
        "best_model": best_model,
        "best_mae": metrics[best_model]["mae"],
    }


def main():

    print("Loading forecastable products...")

    products = load_products()

    print(f"Products selected: {len(products)}")

    results = []

    for _, product in products.iterrows():

        stock_code = product["stock_code"]

        print(
            f"Evaluating {stock_code} - "
            f"{product['product']}"
        )

        result = evaluate_product(stock_code)

        if result:
            result["product"] = product["product"]
            results.append(result)

    results_df = pd.DataFrame(results)

    print("\n" + "=" * 70)
    print("MULTI-PRODUCT FORECAST EVALUATION")
    print("=" * 70)

    print(
        results_df[
            [
                "stock_code",
                "product",
                "naive_mae",
                "ma4_mae",
                "ma8_mae",
                "rf_mae",
                "best_model",
            ]
        ].to_string(index=False)
    )

    print("\nBest-model counts:")

    print(
        results_df["best_model"]
        .value_counts()
    )

    # Save for later Power BI/reporting
    output_path = (
        "data/processed/"
        "forecast_model_evaluation.csv"
    )

    results_df.to_csv(
        output_path,
        index=False,
    )

    print(
        f"\nEvaluation saved to {output_path}"
    )


if __name__ == "__main__":
    main()