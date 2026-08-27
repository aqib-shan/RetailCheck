/* ============================================================
   RETAIL INTELLIGENCE PLATFORM
   ANALYTICS VIEWS
   ============================================================ */


/* ============================================================
   1. EXECUTIVE KPI VIEW
   ============================================================ */

CREATE OR REPLACE VIEW vw_sales_kpis AS

SELECT
    COUNT(DISTINCT invoice_no) AS total_orders,
    COUNT(DISTINCT customer_id) AS total_customers,
    ROUND(SUM(line_total), 2) AS total_revenue,
    SUM(quantity) AS units_sold,

    ROUND(
        SUM(line_total)
        / NULLIF(COUNT(DISTINCT invoice_no), 0),
        2
    ) AS average_order_value

FROM transactions

WHERE is_valid_sale = TRUE;


/* ============================================================
   2. MONTHLY SALES VIEW
   ============================================================ */

CREATE OR REPLACE VIEW vw_monthly_sales AS

SELECT
    DATE_TRUNC('month', invoice_date)::date AS month,
    ROUND(SUM(line_total), 2) AS revenue,
    COUNT(DISTINCT invoice_no) AS orders,
    COUNT(DISTINCT customer_id) AS customers,
    SUM(quantity) AS units_sold

FROM transactions

WHERE is_valid_sale = TRUE

GROUP BY DATE_TRUNC('month', invoice_date)::date

ORDER BY month;


/* ============================================================
   3. PRODUCT PERFORMANCE VIEW
   ============================================================ */

CREATE OR REPLACE VIEW vw_product_performance AS

SELECT
    stock_code,
    MAX(description) AS product,
    SUM(quantity) AS units_sold,
    ROUND(SUM(line_total), 2) AS revenue,
    COUNT(DISTINCT invoice_no) AS orders

FROM transactions

WHERE is_valid_sale = TRUE
    AND stock_code NOT IN ('DOT', 'POST', 'M')

GROUP BY stock_code;


/* ============================================================
   4. COUNTRY PERFORMANCE VIEW
   ============================================================ */

CREATE OR REPLACE VIEW vw_country_performance AS

SELECT
    country,
    ROUND(SUM(line_total), 2) AS revenue,
    COUNT(DISTINCT invoice_no) AS orders,
    COUNT(DISTINCT customer_id) AS customers,
    SUM(quantity) AS units_sold

FROM transactions

WHERE is_valid_sale = TRUE

GROUP BY country;


/* ============================================================
   5. CUSTOMER PERFORMANCE VIEW
   ============================================================ */

CREATE OR REPLACE VIEW vw_customer_performance AS

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

GROUP BY customer_id;


/* ============================================================
   6. RFM CUSTOMER SEGMENTATION VIEW
   ============================================================ */

CREATE OR REPLACE VIEW vw_customer_rfm AS

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
            SELECT MAX(invoice_date)::date + 1
            FROM transactions
        ) - last_purchase_date::date AS recency,

        frequency,
        monetary

    FROM customer_metrics
),

rfm_scores AS (

    SELECT
        *,

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
)

SELECT
    customer_id,
    recency,
    frequency,
    monetary,
    recency_score,
    frequency_score,
    monetary_score,

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

FROM rfm_scores;


/* ============================================================
   7. RFM SEGMENT SUMMARY VIEW
   ============================================================ */

CREATE OR REPLACE VIEW vw_rfm_segment_summary AS

SELECT
    customer_segment,
    COUNT(*) AS customers,
    ROUND(AVG(recency), 1) AS avg_recency_days,
    ROUND(AVG(frequency), 2) AS avg_orders,
    ROUND(AVG(monetary), 2) AS avg_customer_value,
    ROUND(SUM(monetary), 2) AS segment_revenue

FROM vw_customer_rfm

GROUP BY customer_segment;


/* ============================================================
   8. CUSTOMER COHORT RETENTION VIEW
   ============================================================ */

CREATE OR REPLACE VIEW vw_cohort_retention AS

WITH customer_orders AS (

    SELECT DISTINCT
        customer_id,
        DATE_TRUNC('month', invoice_date)::date AS order_month

    FROM transactions

    WHERE is_valid_sale = TRUE
        AND customer_id IS NOT NULL
),

customer_cohorts AS (

    SELECT
        customer_id,
        MIN(order_month) AS cohort_month

    FROM customer_orders

    GROUP BY customer_id
),

cohort_activity AS (

    SELECT
        o.customer_id,
        c.cohort_month,
        o.order_month,

        (
            EXTRACT(
                YEAR FROM AGE(
                    o.order_month,
                    c.cohort_month
                )
            ) * 12

            +

            EXTRACT(
                MONTH FROM AGE(
                    o.order_month,
                    c.cohort_month
                )
            )

        )::INTEGER AS cohort_index

    FROM customer_orders o

    JOIN customer_cohorts c
        ON o.customer_id = c.customer_id
),

cohort_counts AS (

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
        100.0
        * cc.active_customers
        / cs.cohort_size,
        2
    ) AS retention_rate

FROM cohort_counts cc

JOIN cohort_sizes cs
    ON cc.cohort_month = cs.cohort_month

ORDER BY
    cc.cohort_month,
    cc.cohort_index;


/* ============================================================
   9. RETURN ANALYSIS VIEW
   ============================================================ */

CREATE OR REPLACE VIEW vw_returns AS

SELECT
    DATE_TRUNC('month', invoice_date)::date AS month,

    COUNT(*) FILTER (
        WHERE is_return = TRUE
    ) AS return_lines,

    ABS(
        SUM(quantity) FILTER (
            WHERE is_return = TRUE
        )
    ) AS returned_units,

    ROUND(
        ABS(
            SUM(line_total) FILTER (
                WHERE is_return = TRUE
                AND unit_price > 0
            )
        ),
        2
    ) AS return_value

FROM transactions

GROUP BY DATE_TRUNC('month', invoice_date)::date

ORDER BY month;