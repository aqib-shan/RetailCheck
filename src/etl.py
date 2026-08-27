import pandas as pd
from pathlib import Path

# --------------------------------------------------
# File paths
# --------------------------------------------------

RAW_PATH = Path("data/raw/Online Retail.xlsx")
PROCESSED_PATH = Path("data/processed/clean_transactions.csv")


def load_data(path: Path) -> pd.DataFrame:
    """Load the raw retail dataset."""

    print("Loading raw dataset...")

    df = pd.read_excel(path)

    print(f"Loaded {len(df):,} rows.")

    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and transform retail transaction data."""

    df = df.copy()

    print("\nStarting data cleaning...")

    # --------------------------------------------------
    # 1. Standardize column names
    # --------------------------------------------------

    df.columns = [
        "invoice_no",
        "stock_code",
        "description",
        "quantity",
        "invoice_date",
        "unit_price",
        "customer_id",
        "country",
    ]

    # --------------------------------------------------
    # 2. Remove exact duplicate rows
    # --------------------------------------------------

    before = len(df)

    df = df.drop_duplicates()

    removed = before - len(df)

    print(f"Removed {removed:,} duplicate rows.")

    # --------------------------------------------------
    # 3. Standardize text columns
    # --------------------------------------------------

    df["description"] = (
        df["description"]
        .astype("string")
        .str.strip()
    )

    df["country"] = (
        df["country"]
        .astype("string")
        .str.strip()
    )

    # --------------------------------------------------
    # 4. Ensure correct data types
    # --------------------------------------------------

    df["invoice_date"] = pd.to_datetime(
        df["invoice_date"],
        errors="coerce"
    )

    df["quantity"] = pd.to_numeric(
        df["quantity"],
        errors="coerce"
    )

    df["unit_price"] = pd.to_numeric(
        df["unit_price"],
        errors="coerce"
    )

    # Customer IDs should not appear as 17850.0
    df["customer_id"] = (
        pd.to_numeric(df["customer_id"], errors="coerce")
        .astype("Int64")
    )

    # --------------------------------------------------
    # 5. Identify cancelled transactions
    # --------------------------------------------------

    df["is_cancelled"] = (
        df["invoice_no"]
        .astype(str)
        .str.upper()
        .str.startswith("C")
    )

    # --------------------------------------------------
    # 6. Create return flag
    # --------------------------------------------------

    df["is_return"] = df["quantity"] < 0

    # --------------------------------------------------
    # 7. Create transaction value
    # --------------------------------------------------

    df["line_total"] = (
        df["quantity"] * df["unit_price"]
    )

    # --------------------------------------------------
    # 8. Add useful date dimensions
    # --------------------------------------------------

    df["invoice_year"] = df["invoice_date"].dt.year

    df["invoice_month"] = df["invoice_date"].dt.month

    df["invoice_day"] = df["invoice_date"].dt.day

    df["day_of_week"] = df["invoice_date"].dt.day_name()

    df["year_month"] = (
        df["invoice_date"]
        .dt.to_period("M")
        .astype(str)
    )

    # --------------------------------------------------
    # 9. Flag records with customer information
    # --------------------------------------------------

    df["has_customer_id"] = df["customer_id"].notna()


    # --------------------------------------------------
    # 10. Flag valid revenue-generating sales
    # --------------------------------------------------
    df["is_valid_sale"] = (
        (df["quantity"] > 0)
        & (df["unit_price"] > 0)
        & (~df["is_cancelled"])
    )

    # --------------------------------------------------
    # 11. Classify transaction type
    # --------------------------------------------------

    df["transaction_type"] = "other"

    df.loc[df["is_valid_sale"], "transaction_type"] = "sale"

    df.loc[
        df["is_cancelled"] | df["is_return"],
    "transaction_type"
    ] = "return"

    df.loc[
        df["unit_price"] <= 0,
    "transaction_type"
    ] = "adjustment"

    print(f"Clean dataset contains {len(df):,} rows.")
    
    return df

def validate_data(df: pd.DataFrame) -> None:
    """Perform basic data-quality validation."""

    print("\n" + "=" * 60)
    print("ETL VALIDATION")
    print("=" * 60)

    print(f"Rows: {len(df):,}")

    print(
        f"Duplicate rows: "
        f"{df.duplicated().sum():,}"
    )

    print(
        f"Missing customer IDs: "
        f"{df['customer_id'].isna().sum():,}"
    )

    print(
        f"Cancelled transactions: "
        f"{df['is_cancelled'].sum():,}"
    )

    print(
        f"Return transactions: "
        f"{df['is_return'].sum():,}"
    )

    print(
        f"Missing descriptions: "
        f"{df['description'].isna().sum():,}"
    )

    print(
        f"Non-positive prices: "
        f"{(df['unit_price'] <= 0).sum():,}"
    )
    print(
    f"Valid sales: "
    f"{df['is_valid_sale'].sum():,}"
    )

    print("\nTransaction types:")
    print(df["transaction_type"].value_counts())


def save_data(df: pd.DataFrame, path: Path) -> None:
    """Save cleaned dataset."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        path,
        index=False
    )

    print(f"\nClean dataset saved to:")
    print(path)


def main():

    df = load_data(RAW_PATH)

    df = clean_data(df)

    validate_data(df)

    save_data(df, PROCESSED_PATH)


if __name__ == "__main__":
    main()