import pandas as pd
from pathlib import Path

# Path to the raw dataset
DATA_PATH = Path("data/raw/Online Retail.xlsx")

# Load dataset
df = pd.read_excel(DATA_PATH)

print("=" * 60)
print("RETAIL DATASET PROFILE")
print("=" * 60)

# Dataset dimensions
print("\n1. DATASET SIZE")
print(f"Rows: {df.shape[0]:,}")
print(f"Columns: {df.shape[1]}")

# Column types
print("\n2. DATA TYPES")
print(df.dtypes)

# Missing values
print("\n3. MISSING VALUES")
print(df.isnull().sum())

# Duplicate rows
print("\n4. DUPLICATE ROWS")
print(f"Duplicates: {df.duplicated().sum():,}")

# Quantity analysis
print("\n5. QUANTITY")
print(df["Quantity"].describe())
print(f"Negative/zero quantities: {(df['Quantity'] <= 0).sum():,}")

# Price analysis
print("\n6. UNIT PRICE")
print(df["UnitPrice"].describe())
print(f"Zero/negative prices: {(df['UnitPrice'] <= 0).sum():,}")

# Cancelled invoices
cancelled = df["InvoiceNo"].astype(str).str.startswith("C")

print("\n7. CANCELLED TRANSACTIONS")
print(f"Cancelled rows: {cancelled.sum():,}")

# Date range
print("\n8. DATE RANGE")
print(f"First transaction: {df['InvoiceDate'].min()}")
print(f"Last transaction:  {df['InvoiceDate'].max()}")

# Unique customers
print("\n9. CUSTOMERS")
print(f"Unique customers: {df['CustomerID'].nunique():,}")

# Unique products
print("\n10. PRODUCTS")
print(f"Unique products: {df['StockCode'].nunique():,}")

# Countries
print("\n11. COUNTRIES")
print(f"Countries: {df['Country'].nunique()}")