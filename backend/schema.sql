CREATE TABLE IF NOT EXISTS relay_posts(
 code text PRIMARY KEY,name text NOT NULL,max_range_ms integer NOT NULL CHECK(max_range_ms>0)
);
CREATE TABLE IF NOT EXISTS clock_refs(
 code text PRIMARY KEY,label text NOT NULL,enabled boolean NOT NULL DEFAULT true,
 uncertainty_ms smallint NOT NULL CHECK(uncertainty_ms>0)
);
CREATE TABLE IF NOT EXISTS tour_days(
 code text PRIMARY KEY, post text NOT NULL REFERENCES relay_posts(code),tour_day date NOT NULL,
 switch_minute int NOT NULL CHECK(switch_minute BETWEEN 0 AND 1439), UNIQUE(post,tour_day)
);
CREATE TABLE IF NOT EXISTS log_pairs(
 code text PRIMARY KEY,tour text NOT NULL REFERENCES tour_days(code),
 clock text NOT NULL REFERENCES clock_refs(code), source_at timestamptz NOT NULL,
 observed_at timestamptz NOT NULL, import_note text NOT NULL, UNIQUE(tour,clock,source_at)
);
CREATE TABLE IF NOT EXISTS log_notes(
 pair text PRIMARY KEY REFERENCES log_pairs(code),
 note text NOT NULL, label text NOT NULL CHECK(label IN ('unstable','human')),
 signed_by text NOT NULL REFERENCES app_users(email)
);
CREATE TABLE IF NOT EXISTS drift_sheets(
 tour text PRIMARY KEY REFERENCES tour_days(code), editor text NOT NULL REFERENCES app_users(email),
 corrections jsonb NOT NULL, job bigint UNIQUE NOT NULL REFERENCES app_jobs(id)
);
