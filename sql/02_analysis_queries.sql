/* ============================================================
   RETAIL INTELLIGENCE & DEMAND FORECASTING PLATFORM
   Business Analytics Queries

   Dataset: UCI Online Retail
   Database: PostgreSQL
   ============================================================ */


/* ============================================================
   1. EXECUTIVE KPIs
   ============================================================ */

SELECT
    COUNT(DISTINCT invoice_no) AS total_orders,
    COUNT(DISTINCT customer_id) AS total_customers,
    ROUND(SUM(line_total), 2) AS total_revenue,
    SUM(quantity) AS units_sold
FROM transactions
WHERE is_valid_sale = TRUE;


/* ============================================================
   2. AVERAGE ORDER VALUE
   ============================================================ */

SELECT
    ROUND(AVG(order_revenue), 2) AS average_order_value
FROM (
    SELECT
        invoice_no,
        SUM(line_total) AS order_revenue
    FROM transactions
    WHERE is_valid_sale = TRUE
    GROUP BY invoice_no
) orders;


/* ============================================================
   3. MONTHLY SALES PERFORMANCE
   ============================================================ */

SELECT
    DATE_TRUNC('month', invoice_date) AS month,
    ROUND(SUM(line_total), 2) AS revenue,
    COUNT(DISTINCT invoice_no) AS orders,
    SUM(quantity) AS units_sold,
    COUNT(DISTINCT customer_id) AS customers
FROM transactions
WHERE is_valid_sale = TRUE
GROUP BY DATE_TRUNC('month', invoice_date)
ORDER BY month;


/* ============================================================
   4. TOP PRODUCTS BY REVENUE
   Excludes operational/service codes
   ============================================================ */

SELECT
    stock_code,
    MAX(description) AS product,
    SUM(quantity) AS units_sold,
    ROUND(SUM(line_total), 2) AS revenue
FROM transactions
WHERE is_valid_sale = TRUE

    -- Remove non-product operational records
    AND stock_code NOT IN ('DOT', 'POST', 'M')

GROUP BY stock_code
ORDER BY revenue DESC
LIMIT 10;


/* ============================================================
   5. TOP PRODUCTS BY UNITS SOLD
   ============================================================ */

SELECT
    stock_code,
    MAX(description) AS product,
    SUM(quantity) AS units_sold,
    ROUND(SUM(line_total), 2) AS revenue
FROM transactions
WHERE is_valid_sale = TRUE
    AND stock_code NOT IN ('DOT', 'POST', 'M')
GROUP BY stock_code
ORDER BY units_sold DESC
LIMIT 10;


/* ============================================================
   6. COUNTRY PERFORMANCE
   ============================================================ */

SELECT
    country,
    ROUND(SUM(line_total), 2) AS revenue,
    COUNT(DISTINCT invoice_no) AS orders,
    COUNT(DISTINCT customer_id) AS customers,
    SUM(quantity) AS units_sold
FROM transactions
WHERE is_valid_sale = TRUE
GROUP BY country
ORDER BY revenue DESC;


/* ============================================================
   7. TOP CUSTOMERS BY LIFETIME REVENUE
   ============================================================ */

SELECT
    customer_id,
    COUNT(DISTINCT invoice_no) AS orders,
    ROUND(SUM(line_total), 2) AS lifetime_revenue,
    SUM(quantity) AS units_purchased,
    MIN(invoice_date) AS first_purchase,
    MAX(invoice_date) AS last_purchase
FROM transactions
WHERE is_valid_sale = TRUE
    AND customer_id IS NOT NULL
GROUP BY customer_id
ORDER BY lifetime_revenue DESC
LIMIT 20;


/* ============================================================
   8. SALES BY DAY OF WEEK
   ============================================================ */

SELECT
    EXTRACT(ISODOW FROM invoice_date) AS day_number,
    TRIM(TO_CHAR(invoice_date, 'Day')) AS day_of_week,
    ROUND(SUM(line_total), 2) AS revenue,
    COUNT(DISTINCT invoice_no) AS orders
FROM transactions
WHERE is_valid_sale = TRUE
GROUP BY
    EXTRACT(ISODOW FROM invoice_date),
    TRIM(TO_CHAR(invoice_date, 'Day'))
ORDER BY day_number;


/* ============================================================
   9. RETURN ANALYSIS
   ============================================================ */

SELECT
    COUNT(*) FILTER (
        WHERE is_return = TRUE
    ) AS return_lines,

    ABS(SUM(quantity) FILTER (
        WHERE is_return = TRUE
    )) AS returned_units,

    ROUND(
        ABS(SUM(line_total) FILTER (
            WHERE is_return = TRUE
            AND unit_price > 0
        )),
        2
    ) AS return_value

FROM transactions;


/* ============================================================
   10. MONTHLY RETURN TREND
   ============================================================ */

SELECT
    DATE_TRUNC('month', invoice_date) AS month,

    COUNT(*) FILTER (
        WHERE is_return = TRUE
    ) AS return_lines,

    ABS(SUM(quantity) FILTER (
        WHERE is_return = TRUE
    )) AS returned_units

FROM transactions
GROUP BY DATE_TRUNC('month', invoice_date)
ORDER BY month;

/* ============================================================
   11. CUSTOMER COHORT RETENTION
   ============================================================ */

WITH customer_orders AS (

    -- Get one record per customer per purchase month
    SELECT DISTINCT
        customer_id,
        DATE_TRUNC('month', invoice_date)::date AS order_month

    FROM transactions

    WHERE is_valid_sale = TRUE
        AND customer_id IS NOT NULL
),

customer_cohorts AS (

    -- Determine each customer's first purchase month
    SELECT
        customer_id,
        MIN(order_month) AS cohort_month

    FROM customer_orders

    GROUP BY customer_id
),

cohort_activity AS (

    -- Calculate number of months since first purchase
    SELECT
        o.customer_id,
        c.cohort_month,
        o.order_month,

        (
            EXTRACT(YEAR FROM AGE(o.order_month, c.cohort_month)) * 12
            +
            EXTRACT(MONTH FROM AGE(o.order_month, c.cohort_month))
        )::INTEGER AS cohort_index

    FROM customer_orders o

    JOIN customer_cohorts c
        ON o.customer_id = c.customer_id
),

cohort_counts AS (

    -- Count active customers in each cohort/month
    SELECT
        cohort_month,
        cohort_index,
        COUNT(DISTINCT customer_id) AS active_customers

    FROM cohort_activity

    GROUP BY
        cohort_month,
        cohort_index
),

cohort_sizes AS (

    -- Month 0 represents original cohort size
    SELECT
        cohort_month,
        active_customers AS cohort_size

    FROM cohort_counts

    WHERE cohort_index = 0
)

SELECT
    cc.cohort_month,
    cc.cohort_index,
    cc.active_customers,
    cs.cohort_size,

    ROUND(
        100.0 * cc.active_customers / cs.cohort_size,
        2
    ) AS retention_rate

FROM cohort_counts cc

JOIN cohort_sizes cs
    ON cc.cohort_month = cs.cohort_month

ORDER BY
    cc.cohort_month,
    cc.cohort_index;

/* ============================================================
   12. RFM CUSTOMER SEGMENTATION
   ============================================================ */

WITH customer_metrics AS (

    SELECT
        customer_id,

        MAX(invoice_date) AS last_purchase_date,

        COUNT(DISTINCT invoice_no) AS frequency,

        ROUND(SUM(line_total), 2) AS monetary

    FROM transactions

    WHERE is_valid_sale = TRUE
        AND customer_id IS NOT NULL

    GROUP BY customer_id
),

rfm_values AS (

    SELECT
        customer_id,

        (
            DATE '2011-12-10'
            - last_purchase_date::date
        ) AS recency,

        frequency,
        monetary

    FROM customer_metrics
),

rfm_scores AS (

    SELECT
        *,

        -- Lower recency is better, so scoring is reversed
        5 - NTILE(4) OVER (
            ORDER BY recency
        ) AS recency_score,

        NTILE(4) OVER (
            ORDER BY frequency
        ) AS frequency_score,

        NTILE(4) OVER (
            ORDER BY monetary
        ) AS monetary_score

    FROM rfm_values
),

rfm_segments AS (

    SELECT
        *,

        CASE

            WHEN recency_score = 4
                AND frequency_score >= 3
                AND monetary_score >= 3
                THEN 'Champions'

            WHEN recency_score >= 3
                AND frequency_score >= 3
                THEN 'Loyal Customers'

            WHEN recency_score = 4
                AND frequency_score <= 2
                THEN 'New Customers'

            WHEN recency_score <= 2
                AND frequency_score >= 3
                THEN 'At Risk'

            WHEN recency_score = 1
                AND frequency_score <= 2
                THEN 'Lost Customers'

            ELSE 'Potential Loyalists'

        END AS customer_segment

    FROM rfm_scores
)

SELECT
    customer_id,
    recency,
    frequency,
    monetary,
    recency_score,
    frequency_score,
    monetary_score,
    customer_segment

FROM rfm_segments

ORDER BY monetary DESC;

/* ============================================================
   13. WEEKLY PRODUCT DEMAND
   ============================================================ */

SELECT
    stock_code,
    MAX(description) AS product,
    DATE_TRUNC('week', invoice_date)::date AS week_start,
    SUM(quantity) AS units_sold,
    ROUND(SUM(line_total), 2) AS revenue
FROM transactions
WHERE is_valid_sale = TRUE
    AND stock_code NOT IN ('DOT', 'POST', 'M')
GROUP BY
    stock_code,
    DATE_TRUNC('week', invoice_date)::date
ORDER BY
    stock_code,
    week_start;

/* ============================================================
   14. PRODUCTS SUITABLE FOR FORECASTING
   ============================================================ */

SELECT
    stock_code,
    MAX(description) AS product,
    COUNT(DISTINCT DATE_TRUNC('week', invoice_date)) AS active_weeks,
    SUM(quantity) AS total_units,
    ROUND(SUM(line_total), 2) AS total_revenue
FROM transactions
WHERE is_valid_sale = TRUE
    AND stock_code NOT IN ('DOT', 'POST', 'M')
GROUP BY stock_code
HAVING COUNT(DISTINCT DATE_TRUNC('week', invoice_date)) >= 40
ORDER BY total_units DESC
LIMIT 20;