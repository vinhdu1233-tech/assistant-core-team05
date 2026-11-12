-- Lab 5 Part F: Analytics queries

-- F1: How many questions per intent?
SELECT
    intent,
    COUNT(*) AS requests
FROM interaction
GROUP BY intent
ORDER BY intent;


-- F2: Average time taken per intent?
SELECT
    intent,
    ROUND(AVG(latency_ms), 1) AS avg_latency_ms
FROM interaction
GROUP BY intent
ORDER BY intent;


-- F3: Which topics got the most thumbs-down?
SELECT
    i.topic,
    COUNT(*) AS thumbs_down
FROM interaction AS i
JOIN feedback AS f
    ON f.request_id = i.request_id
WHERE f.rating = -1
    AND i.topic IS NOT NULL
GROUP BY i.topic
ORDER BY thumbs_down DESC, i.topic;


-- H2: What percentage of interactions used a backup answer?
SELECT
    ROUND(
        100.0 * SUM(CASE WHEN degraded = 1 THEN 1 ELSE 0 END)
        / COUNT(*),
        2
    ) AS degraded_percentage
FROM interaction;
