# Retail Intelligence & Demand Forecasting

An end-to-end retail analytics and demand forecasting project that transforms raw transactional data into actionable business insights using Python, PostgreSQL, machine learning, and Power BI.

The project covers the complete analytics workflow: data cleaning, database modeling, SQL analytics, customer segmentation, product performance analysis, demand forecasting, and interactive business intelligence dashboards.

## Project Overview

Retail businesses need to understand not only what has happened historically, but also which customers and products drive performance and what demand may look like in the future.

This project builds an analytics pipeline around retail transaction data to answer questions such as:

- Which products generate the most revenue and sales volume?
- Which customer segments contribute the most value?
- Which customers may be at risk of becoming inactive?
- How well are customers retained over time?
- Which countries contribute the most revenue?
- What demand can be expected for high-volume products over the next four weeks?

The final analytical layer is presented through a three-page Power BI dashboard covering executive performance, customer analytics, and product demand forecasting.

---

## Tech Stack

**Programming & Data Processing**
- Python
- pandas
- NumPy

**Machine Learning & Forecasting**
- scikit-learn
- Random Forest
- Naive Forecasting
- Moving Average Models

**Database & Analytics**
- PostgreSQL
- SQL
- SQLAlchemy
- psycopg2

**Business Intelligence**
- Power BI
- DAX
- Power Query

**Development**
- Git
- GitHub
- Visual Studio Code
- Python Virtual Environments

---

## Project Architecture

```text
Raw Retail Data
      |
      v
Python ETL & Data Cleaning
      |
      v
Processed Transaction Data
      |
      v
PostgreSQL Database
      |
      +--------------------+
      |                    |
      v                    v
SQL Analytics Views    Forecasting Pipeline
      |                    |
      |               Model Evaluation
      |                    |
      |               Best Model Selection
      |                    |
      |               4-Week Forecasts
      |                    |
      +----------+---------+
                 |
                 v
              Power BI
                 |
      +----------+----------+
      |          |          |
 Executive   Customer    Product &
 Overview    Analytics   Demand Analytics
```

---

## Power BI Dashboards

### Executive Overview

Provides a high-level view of retail performance, including:

- Total Revenue
- Total Orders
- Total Customers
- Average Order Value
- Monthly Revenue Trend
- Top Products by Revenue
- Revenue by Country
- Customer Segment Distribution
- Product Demand Forecast

![Executive Overview](powerbi/executive-overview.png)

### Customer Analytics

Focuses on customer behavior, segmentation, value, and retention.

Key analysis includes:

- Total Customers
- Champion Customers
- At-Risk Customers
- Average Customer Value
- RFM Customer Segmentation
- Customer Value by Segment
- Average Orders by Customer Segment
- Cohort Retention Analysis

![Customer Analytics](powerbi/Customer-Analytics.png)

### Product & Demand Analytics

Analyzes product performance and future demand.

Key components include:

- Units Sold
- Total Revenue
- Total Products
- Forecast Units
- Top Products by Revenue
- Top Products by Units Sold
- Interactive Product Selection
- Four-Week Product Demand Forecast
- Product-Level Tooltip Analysis

![Product & Demand Analytics](powerbi/Product-and-Demand-Analytics.png)

---

## Customer Segmentation

Customers are segmented using **RFM analysis**:

- **Recency** – how recently a customer purchased
- **Frequency** – how frequently the customer purchases
- **Monetary Value** – how much revenue the customer generates

The resulting business-oriented customer segments include:

- Champions
- Loyal Customers
- Potential Loyalists
- At Risk
- Lost Customers
- New Customers

This allows customer performance to be analyzed beyond aggregate revenue and order metrics.

---

## Cohort Retention Analysis

Customer retention is analyzed by grouping customers according to their first purchase month.

The cohort matrix tracks the percentage of customers who return in subsequent months, providing insight into:

- Customer retention behavior
- Repeat purchasing
- Long-term engagement
- Differences between acquisition cohorts

The resulting retention matrix is visualized as a heatmap in Power BI.

---

## Demand Forecasting

The forecasting pipeline evaluates multiple forecasting approaches independently for each selected product.

The models evaluated are:

1. Naive Forecast
2. 4-Week Moving Average
3. 8-Week Moving Average
4. Random Forest

Forecast performance is compared using **Mean Absolute Error (MAE)**.

Instead of applying one forecasting model to every product, the pipeline automatically selects the model with the lowest MAE for each product.

### Model Selection Results

The evaluation of 20 forecastable products selected:

| Model | Products Selected |
|---|---:|
| Random Forest | 8 |
| Naive | 6 |
| Moving Average 4 | 3 |
| Moving Average 8 | 3 |

This product-level model selection allows products with different demand patterns to use different forecasting approaches.

The selected models are then used to generate a **four-week demand forecast** for each product.

---

## Forecasting Pipeline

The forecasting workflow follows these steps:

```text
Historical Transactions
        |
        v
Weekly Product Demand
        |
        v
Select Forecastable Products
        |
        v
Evaluate Candidate Models
        |
        v
Compare MAE
        |
        v
Select Best Model per Product
        |
        v
Generate 4-Week Forecast
        |
        v
Save Forecast Results
        |
        v
Load Forecasts into PostgreSQL
        |
        v
Visualize in Power BI
```

The current pipeline evaluates **20 products** and generates four future weekly observations for each product, producing **80 forecast records**.

---

## Project Structure

```text
retail-intelligence/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── docs/
│
├── notebooks/
│
├── powerbi/
│   ├── Customer-Analytics.png
│   ├── executive-overview.png
│   ├── Product-and-Demand-Analytics.png
│   └── tool_tip_demo.png
│
├── sql/
│   ├── 01_create_schema.sql
│   ├── 02_analysis_queries.sql
│   └── 03_analytics_views.sql
│
├── src/
│   ├── config.py
│   ├── data_profile.py
│   ├── etl.py
│   ├── forecast_products.py
│   ├── forecast.py
│   ├── generate_forecasts.py
│   ├── load_database.py
│   └── load_forecasts.py
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Local Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd retail-intelligence
```

### 2. Create a Python Virtual Environment

Python 3.10 is recommended for this project.

Windows:

```powershell
py -3.10 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database named:

```text
retail_intelligence
```

Copy `.env.example` to `.env` and configure your database credentials:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=retail_intelligence
DB_USER=postgres
DB_PASSWORD=your_password
```

The `.env` file is excluded from Git and should never be committed.

### 5. Create the Database Schema

Run:

```text
sql/01_create_schema.sql
```

against the `retail_intelligence` PostgreSQL database.

### 6. Prepare the Data

Run the ETL pipeline as required to generate:

```text
data/processed/clean_transactions.csv
```

### 7. Load Transactions into PostgreSQL

```powershell
python -m src.load_database
```

The loader clears existing transaction records before loading the processed dataset, preventing duplicate rows when the command is rerun.

For the current processed dataset, successful verification produces:

```text
536,641 transactions
```

### 8. Evaluate Forecasting Models

```powershell
python -m src.forecast_products
```

This evaluates candidate forecasting models and saves the results to:

```text
data/processed/forecast_model_evaluation.csv
```

### 9. Generate Product Forecasts

```powershell
python -m src.generate_forecasts
```

Forecasts are saved to:

```text
data/processed/product_demand_forecasts.csv
```

### 10. Load Forecasts into PostgreSQL

```powershell
python -m src.load_forecasts
```

The current pipeline loads:

```text
80 forecast rows
```

representing four forecast weeks for 20 products.

---

## Reproducing the Forecast Pipeline

After the database and processed data have been prepared, the core workflow can be executed with:

```powershell
python -m src.load_database
python -m src.forecast_products
python -m src.generate_forecasts
python -m src.load_forecasts
```

---

## Analytics Layer

SQL views provide a reusable analytics layer between the transactional database and Power BI.

The analytics layer supports areas such as:

- Executive KPIs
- Monthly sales trends
- Country performance
- Product performance
- Customer RFM analysis
- Customer segmentation
- Cohort retention
- Forecast integration

This keeps business logic centralized instead of reproducing transformations independently inside dashboard visuals.

---

## Key Project Features

- End-to-end ETL pipeline using Python
- PostgreSQL relational analytics database
- Reusable SQL analytics views
- RFM-based customer segmentation
- Cohort retention analysis
- Product performance analysis
- Multi-model demand forecasting
- MAE-based model selection per product
- Four-week product demand forecasts
- Interactive Power BI dashboard
- Product-level report-page tooltips
- Reproducible Python virtual environment
- Environment-variable based database configuration

---

## Dashboard Highlights

The completed solution provides three analytical perspectives:

**Executive Overview** provides management-level visibility into revenue, orders, customers, geographic performance, product performance, and overall trends.

**Customer Analytics** provides deeper insight into customer value, behavioral segments, purchase frequency, at-risk customers, and retention.

**Product & Demand Analytics** connects historical product performance with forward-looking demand forecasts and allows individual products to be explored interactively.

---

## Future Improvements

Potential extensions include:

- Automated scheduled data refresh
- Additional time-series forecasting models
- Forecast confidence intervals
- Hyperparameter optimization
- Product category-level forecasting
- Customer churn prediction
- Automated model retraining
- Cloud database deployment
- Power BI Service deployment
- Pipeline orchestration

---

## Author

**Palden Tamang**

Computer Science | Data Analytics | Software Development

GitHub: TAMANGP2