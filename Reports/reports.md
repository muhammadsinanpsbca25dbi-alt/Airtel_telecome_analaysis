_______________________________________________________________________________________________________________

A. National churn

SELECT
    COUNT(*) AS total_subscribers,
    SUM(is_churned) AS subscribers_left,
    ROUND(100.0 * AVG(is_churned), 2) AS churn_rate
FROM customer_features;

_______________________________________________________________________________________________________________


B. Churn by tenure

SELECT
    tenure_years,
    COUNT(*) AS subscribers,
    SUM(is_churned) AS subscribers_left,
    ROUND(100.0 * AVG(is_churned), 2) AS churn_rate
FROM customer_features
GROUP BY tenure_years
ORDER BY tenure_years;

_______________________________________________________________________________________________________________


C. Prepaid vs postpaid churn

SELECT
    connection_type,
    COUNT(*) AS subscribers,
    SUM(is_churned) AS subscribers_left,
    ROUND(100.0 * AVG(is_churned), 2) AS churn_rate
FROM customer_features
GROUP BY connection_type;

_______________________________________________________________________________________________________________


D. Circle churn

SELECT
    circle_name,
    region,
    COUNT(*) AS subscribers,
    SUM(is_churned) AS subscribers_left,
    ROUND(100.0 * AVG(is_churned), 2) AS churn_rate
FROM customer_features
GROUP BY circle_name, region
ORDER BY churn_rate DESC;

_______________________________________________________________________________________________________________

E. Complaint status

SELECT
    CASE
        WHEN complaint_count = 0
            THEN 'Never complained'
        WHEN unresolved_count = 0
            THEN 'All resolved'
        ELSE 'Has open ticket'
    END AS complaint_status,
    COUNT(*) AS subscribers,
    SUM(is_churned) AS subscribers_left,
    ROUND(100.0 * AVG(is_churned), 2) AS churn_rate
FROM customer_features
GROUP BY complaint_status;

_______________________________________________________________________________________________________________

F. Selected circle — tenure

SELECT
    tenure_years,
    COUNT(*) AS subscribers,
    SUM(is_churned) AS subscribers_left,
    ROUND(100.0 * AVG(is_churned), 2) AS churn_rate
FROM customer_features
WHERE circle_name = :selected_circle
GROUP BY tenure_years
ORDER BY tenure_years;

_______________________________________________________________________________________________________________