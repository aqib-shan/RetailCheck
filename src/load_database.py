import pandas as pd
from sqlalchemy import text

from src.config import get_engine


DATA_PATH = "data/processed/clean_transactions.csv"


def load_transactions():
    print("Reading cleaned transaction data...")

    # Load cleaned transaction data
    df = pd.read_csv(
        DATA_PATH,
        parse_dates=["invoice_date"]
    )

    print(f"Rows ready for database: {len(df):,}")

    # Create PostgreSQL connection
    engine = get_engine()

    # Verify database connection
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    print("Database connection successful.")

    # Clear existing transaction data before reloading.
    # This prevents duplicate rows when the script is run again.
    print("Clearing existing transactions...")

    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE TABLE transactions RESTART IDENTITY")
        )

    print("Existing transactions cleared.")

    # Load cleaned data into PostgreSQL
    # transaction_id is generated automatically by PostgreSQL.
    print("Loading transactions into PostgreSQL...")

    df.to_sql(
        name="transactions",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi"
    )

    print(f"Successfully loaded {len(df):,} transactions.")

    # Verify final database row count
    with engine.connect() as connection:
        count = connection.execute(
            text("SELECT COUNT(*) FROM transactions")
        ).scalar()

    print(f"PostgreSQL transaction count: {count:,}")

    # Confirm the database contains exactly the expected rows
    if count == len(df):
        print("Database load verification successful.")
    else:
        print(
            f"WARNING: Expected {len(df):,} rows "
            f"but PostgreSQL contains {count:,} rows."
        )


if __name__ == "__main__":
    load_transactions()