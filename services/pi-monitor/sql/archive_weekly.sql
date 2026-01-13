BEGIN TRANSACTION;

-- Compute last completed week in LOCAL TIME
-- Week = Sunday 00:00:00 → Saturday 23:59:59

DROP TABLE IF EXISTS _week_window;

CREATE TEMP TABLE _week_window AS
SELECT
    datetime(
        date('now', 'localtime', 'weekday 0', '-7 days')
    ) AS week_start,
    datetime(
        date('now', 'localtime', 'weekday 0', '-1 second')
    ) AS week_end;

-- Insert weekly aggregates (idempotent)
INSERT OR IGNORE INTO metrics_weekly_avg
    (week_start, week_end, source, name, avg_value, min_value, max_value, unit)
SELECT
    w.week_start,
    w.week_end,
    m.source,
    m.name,
    AVG(m.value) AS avg_value,
    MIN(m.value) AS min_value,
    MAX(m.value) AS max_value,
    m.unit
FROM metrics m
CROSS JOIN _week_window w
WHERE m.ts >= w.week_start
  AND m.ts <= w.week_end
GROUP BY m.source, m.name, m.unit;

-- Delete raw metrics older than the archived week
DELETE FROM metrics
WHERE ts < (SELECT week_start FROM _week_window);

DROP TABLE _week_window;

COMMIT;
