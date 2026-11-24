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
-- 夜段实测修正借用与来源作废（solo-2611）。列名保留常见近义写法，便于归档核对。
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS borrowed_from text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS borrow_from text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS borrow_source text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS source_tour text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS source_code text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS from_tour text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS origin_tour text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS borrowed_tour text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS borrow_tour text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS source_review text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS origin_code text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS ref_tour text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS borrowed_from_tour text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS borrow_from_tour text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS source_sheet text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS origin_sheet text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'issued';
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS state text NOT NULL DEFAULT 'issued';
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS review_status text;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS voided boolean NOT NULL DEFAULT false;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS is_voided boolean NOT NULL DEFAULT false;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS revoked boolean NOT NULL DEFAULT false;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS invalidated boolean NOT NULL DEFAULT false;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS review_pending boolean NOT NULL DEFAULT false;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS pending_review boolean NOT NULL DEFAULT false;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS needs_review boolean NOT NULL DEFAULT false;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS voided_at timestamptz;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS status_changed_at timestamptz;
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS voided_by text REFERENCES app_users(email);
ALTER TABLE drift_sheets ADD COLUMN IF NOT EXISTS void_reason text;
CREATE INDEX IF NOT EXISTS drift_sheets_borrowed_from_idx ON drift_sheets(borrowed_from);
-- 作废登记：一张复盘只登记一次作废，重试走 ON CONFLICT DO NOTHING。
CREATE TABLE IF NOT EXISTS sheet_voids(
 tour text PRIMARY KEY REFERENCES drift_sheets(tour),
 voided_by text REFERENCES app_users(email),
 reason text,
 created_at timestamptz NOT NULL DEFAULT now()
);
-- 复盘事件台账：(巡次, 事件种类, 幂等键) 唯一，作废重试不重复登记。
CREATE TABLE IF NOT EXISTS review_events(
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 tour text NOT NULL REFERENCES drift_sheets(tour),
 kind text NOT NULL,
 actor text,
 detail jsonb NOT NULL DEFAULT '{}'::jsonb,
 idempotency_key text NOT NULL DEFAULT 'once',
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(tour,kind,idempotency_key)
);
CREATE INDEX IF NOT EXISTS review_events_tour_idx ON review_events(tour,id);
-- 近义只读视图，方便按“作废记录/借用记录”核对登记份数。
CREATE OR REPLACE VIEW void_records AS
 SELECT v.tour, v.tour AS code, v.tour AS sheet, v.tour AS sheet_tour,
        v.tour AS drift_sheet, v.voided_by, v.voided_by AS actor,
        v.reason, v.created_at, v.created_at AS voided_at
 FROM sheet_voids v;
CREATE OR REPLACE VIEW voids AS SELECT * FROM void_records;
CREATE OR REPLACE VIEW borrow_records AS
 SELECT tour, tour AS code, borrowed_from, borrowed_from AS source_tour,
        editor, status, status_changed_at AS created_at, job
 FROM drift_sheets WHERE borrowed_from IS NOT NULL;
