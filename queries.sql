-- ==============================================================================
-- Sales Decline Investigation: Analytical SQL Queries
-- Dialect: SQLite
-- Description: Reproducible SQL queries executing against clean trusted data
-- Finance Rules Applied:
--   1. Revenue = quantity * unit_price for completed orders only.
--   2. USD -> INR converted at ₹85.0 per USD.
--   3. Exclude cancelled and refunded orders (do not subtract refunds).
--   4. Exclude quarantined / rejected records.
--   5. New vs Repeat customers defined by first completed order in Aug-Sept window.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 1: Monthly completed revenue (INR), orders, quantity, customers, and AOV
-- ------------------------------------------------------------------------------
SELECT 
    strftime('%Y-%m', o.order_date) AS month,
    COUNT(o.order_id) AS completed_orders,
    SUM(o.quantity) AS total_quantity,
    COUNT(DISTINCT o.customer_id) AS customer_count,
    ROUND(SUM(o.quantity * o.unit_price * CASE WHEN o.currency = 'USD' THEN 85.0 ELSE 1.0 END), 2) AS total_revenue_inr,
    ROUND(AVG(o.quantity * o.unit_price * CASE WHEN o.currency = 'USD' THEN 85.0 ELSE 1.0 END), 2) AS aov_inr
FROM clean_orders o
WHERE o.status = 'completed'
GROUP BY strftime('%Y-%m', o.order_date)
ORDER BY month ASC;


-- ------------------------------------------------------------------------------
-- Query 2: Top 10 products by completed revenue (INR)
-- ------------------------------------------------------------------------------
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    SUM(o.quantity) AS total_units_sold,
    COUNT(o.order_id) AS order_count,
    ROUND(SUM(o.quantity * o.unit_price * CASE WHEN o.currency = 'USD' THEN 85.0 ELSE 1.0 END), 2) AS total_revenue_inr
FROM clean_orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'completed'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_revenue_inr DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- Query 3: New vs repeat customer contribution (within dataset window)
-- Definition: First completed order date in Aug-Sept dataset is 'New', later dates are 'Repeat'
-- ------------------------------------------------------------------------------
WITH first_orders AS (
    SELECT 
        customer_id,
        MIN(order_date) AS first_completed_date
    FROM clean_orders
    WHERE status = 'completed'
    GROUP BY customer_id
),
classified_orders AS (
    SELECT 
        o.order_id,
        o.order_date,
        strftime('%Y-%m', o.order_date) AS month,
        o.customer_id,
        o.quantity * o.unit_price * CASE WHEN o.currency = 'USD' THEN 85.0 ELSE 1.0 END AS revenue_inr,
        CASE 
            WHEN o.order_date = f.first_completed_date THEN 'New'
            ELSE 'Repeat'
        END AS customer_type
    FROM clean_orders o
    JOIN first_orders f ON o.customer_id = f.customer_id
    WHERE o.status = 'completed'
)
SELECT 
    month,
    customer_type,
    COUNT(order_id) AS order_count,
    COUNT(DISTINCT customer_id) AS customer_count,
    ROUND(SUM(revenue_inr), 2) AS total_revenue_inr,
    ROUND(AVG(revenue_inr), 2) AS aov_inr
FROM classified_orders
GROUP BY month, customer_type
ORDER BY month ASC, customer_type DESC;


-- ------------------------------------------------------------------------------
-- Query 4: Regional performance breakdown by month
-- ------------------------------------------------------------------------------
SELECT 
    c.region,
    strftime('%Y-%m', o.order_date) AS month,
    COUNT(o.order_id) AS completed_orders,
    COUNT(DISTINCT o.customer_id) AS active_customers,
    SUM(o.quantity) AS total_quantity,
    ROUND(SUM(o.quantity * o.unit_price * CASE WHEN o.currency = 'USD' THEN 85.0 ELSE 1.0 END), 2) AS total_revenue_inr,
    ROUND(AVG(o.quantity * o.unit_price * CASE WHEN o.currency = 'USD' THEN 85.0 ELSE 1.0 END), 2) AS aov_inr
FROM clean_orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'completed'
GROUP BY c.region, strftime('%Y-%m', o.order_date)
ORDER BY c.region, month ASC;


-- ------------------------------------------------------------------------------
-- Query 5: Product category breakdown by month
-- ------------------------------------------------------------------------------
SELECT 
    p.category,
    strftime('%Y-%m', o.order_date) AS month,
    COUNT(o.order_id) AS completed_orders,
    SUM(o.quantity) AS total_quantity,
    ROUND(SUM(o.quantity * o.unit_price * CASE WHEN o.currency = 'USD' THEN 85.0 ELSE 1.0 END), 2) AS total_revenue_inr
FROM clean_orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.status = 'completed'
GROUP BY p.category, strftime('%Y-%m', o.order_date)
ORDER BY p.category, month ASC;
