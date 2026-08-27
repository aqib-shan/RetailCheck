import pandas as pd
from sqlalchemy import text

from src.config import get_engine


FORECAST_PATH = (
    "data/processed/product_demand_forecasts.csv"
)


def load_forecasts():
    """Load product demand forecasts into PostgreSQL."""

    print("Reading forecast data...")

    df = pd.read_csv(
        FORECAST_PATH,
        parse_dates=["forecast_week"],
    )

    print(f"Forecast rows: {len(df):,}")

    engine = get_engine()

    with engine.begin() as connection:

        connection.execute(
            text("""
                DROP TABLE IF EXISTS demand_forecasts;
            """)
        )

        connection.execute(
            text("""
                CREATE TABLE demand_forecasts (

                    forecast_id BIGSERIAL PRIMARY KEY,

                    stock_code VARCHAR(30) NOT NULL,

                    product TEXT,

                    forecast_week DATE NOT NULL,

                    forecast_units NUMERIC(12, 2),

                    model VARCHAR(50)

                );
            """)
        )

    print("Forecast table created.")

    df.to_sql(
        name="demand_forecasts",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=1000,
        method="multi",
    )

    with engine.connect() as connection:

        count = connection.execute(
            text(
                "SELECT COUNT(*) "
                "FROM demand_forecasts"
            )
        ).scalar()

    print(
        f"Successfully loaded "
        f"{count:,} forecast rows."
    )


if __name__ == "__main__":
    load_forecasts()