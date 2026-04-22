"""Initial schema — all Phase 1 tables + indexes + triggers + pdpd_delete_lead

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-22

Applies Phase 1 validation patches:
- P1: no CREATE EXTENSION (gen_random_uuid is built-in since PG 13)
- P2: pdpd_delete_lead sets phone_raw='DELETED' (NOT NULL safe)
"""
from __future__ import annotations

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


SCHEMA_SQL = """
CREATE TABLE companies (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name       TEXT NOT NULL,
  industry   TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE hr_users (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id        UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  email             TEXT UNIQUE NOT NULL,
  phone_e164        TEXT,
  full_name         TEXT NOT NULL,
  telegram_chat_id  TEXT,
  api_key_hash      TEXT NOT NULL,
  role              TEXT NOT NULL DEFAULT 'recruiter'
                    CHECK (role IN ('recruiter','admin')),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_login_at     TIMESTAMPTZ
);
CREATE INDEX idx_hr_company ON hr_users(company_id);

CREATE TABLE jobs (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id           UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  created_by           UUID NOT NULL REFERENCES hr_users(id),
  title                TEXT NOT NULL,
  salary_min_vnd       INTEGER,
  salary_max_vnd       INTEGER,
  salary_text          TEXT,
  location_raw         TEXT NOT NULL,
  location_district    TEXT NOT NULL,
  location_city        TEXT NOT NULL,
  location_lat         NUMERIC(9,6) NOT NULL,
  location_lng         NUMERIC(9,6) NOT NULL,
  start_date           DATE,
  shift                TEXT CHECK (shift IN ('day','night','rotating','flexible')),
  requirements_raw     TEXT,
  requirements_parsed  JSONB,
  target_hires         INTEGER NOT NULL DEFAULT 1,
  status               TEXT NOT NULL DEFAULT 'draft'
                       CHECK (status IN ('draft','active','paused','closed')),
  ai_warnings          JSONB,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  published_at         TIMESTAMPTZ,
  closed_at            TIMESTAMPTZ
);
CREATE INDEX idx_jobs_active_company  ON jobs(company_id, status) WHERE status = 'active';
CREATE INDEX idx_jobs_active_district ON jobs(location_district) WHERE status = 'active';

CREATE TABLE content_variants (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id              UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  variant_index       SMALLINT NOT NULL,
  hook_style          TEXT NOT NULL
                      CHECK (hook_style IN ('urgency','salary_first','proximity','friendly','detailed')),
  copy_vietnamese     TEXT NOT NULL,
  final_copy          TEXT,
  generated_by_model  TEXT NOT NULL,
  token_usage         JSONB NOT NULL,
  generated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(job_id, variant_index)
);
CREATE INDEX idx_variants_job ON content_variants(job_id);

CREATE TABLE sources (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel       TEXT NOT NULL CHECK (channel IN ('facebook','zalo','direct','unknown','other')),
  external_id   TEXT,
  display_name  TEXT NOT NULL,
  notes         TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(channel, external_id)
);

CREATE TABLE campaigns (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  starts_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  ends_at     TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tracking_links (
  tracking_id    TEXT PRIMARY KEY,
  job_id         UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  variant_id     UUID NOT NULL REFERENCES content_variants(id) ON DELETE CASCADE,
  source_id      UUID NOT NULL REFERENCES sources(id),
  campaign_id    UUID REFERENCES campaigns(id),
  created_by     UUID NOT NULL REFERENCES hr_users(id),
  click_count    INTEGER NOT NULL DEFAULT 0,
  lead_count     INTEGER NOT NULL DEFAULT 0,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  first_click_at TIMESTAMPTZ,
  last_click_at  TIMESTAMPTZ
);
CREATE INDEX idx_tlinks_job      ON tracking_links(job_id);
CREATE INDEX idx_tlinks_variant  ON tracking_links(variant_id);
CREATE INDEX idx_tlinks_source   ON tracking_links(source_id);
CREATE INDEX idx_tlinks_campaign ON tracking_links(campaign_id);

CREATE TABLE link_clicks (
  id           BIGSERIAL PRIMARY KEY,
  tracking_id  TEXT NOT NULL REFERENCES tracking_links(tracking_id) ON DELETE CASCADE,
  ip_hash      TEXT,
  user_agent   TEXT,
  referrer     TEXT,
  clicked_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_clicks_tid_time ON link_clicks(tracking_id, clicked_at DESC);

CREATE TABLE leads (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phone_e164         TEXT NOT NULL,
  phone_raw          TEXT NOT NULL,
  full_name          TEXT NOT NULL,
  area_raw           TEXT,
  area_normalized    TEXT,
  area_district      TEXT,
  area_city          TEXT,
  area_lat           NUMERIC(9,6),
  area_lng           NUMERIC(9,6),
  source_channel     TEXT NOT NULL DEFAULT 'unknown'
                     CHECK (source_channel IN ('facebook','zalo','direct','unknown','other')),
  source_id          UUID REFERENCES sources(id),
  variant_id         UUID REFERENCES content_variants(id),
  tracking_id        TEXT REFERENCES tracking_links(tracking_id),
  campaign_id        UUID REFERENCES campaigns(id),
  entry_job_id       UUID REFERENCES jobs(id),
  user_agent         TEXT,
  ip_address         INET,
  is_duplicate_of    UUID REFERENCES leads(id),
  consent_record_id  UUID,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_active_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX idx_leads_phone_primary ON leads(phone_e164) WHERE is_duplicate_of IS NULL;
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX idx_leads_district   ON leads(area_district);
CREATE INDEX idx_leads_tracking   ON leads(tracking_id);
CREATE INDEX idx_leads_source     ON leads(source_channel, source_id);
CREATE INDEX idx_leads_variant    ON leads(variant_id);

CREATE TABLE consent_records (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id          UUID NOT NULL REFERENCES leads(id) ON DELETE RESTRICT,
  consent_version  TEXT NOT NULL,
  consent_text_vi  TEXT NOT NULL,
  purposes         JSONB NOT NULL,
  granted_at       TIMESTAMPTZ NOT NULL,
  ip_address       INET,
  user_agent       TEXT,
  revoked_at       TIMESTAMPTZ
);
CREATE INDEX idx_consent_lead ON consent_records(lead_id);
ALTER TABLE leads
  ADD CONSTRAINT fk_leads_consent FOREIGN KEY (consent_record_id)
  REFERENCES consent_records(id) DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE screening_sessions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id         UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  job_id          UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  status          TEXT NOT NULL DEFAULT 'in_progress'
                  CHECK (status IN ('in_progress','completed','abandoned')),
  turn_count      SMALLINT NOT NULL DEFAULT 0,
  extracted_data  JSONB NOT NULL DEFAULT '{}'::jsonb,
  started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_turn_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at    TIMESTAMPTZ,
  abandon_reason  TEXT,
  UNIQUE(lead_id, job_id)
);
CREATE INDEX idx_sessions_inprogress ON screening_sessions(last_turn_at) WHERE status = 'in_progress';
CREATE INDEX idx_sessions_job        ON screening_sessions(job_id);

CREATE TABLE screening_messages (
  id          BIGSERIAL PRIMARY KEY,
  session_id  UUID NOT NULL REFERENCES screening_sessions(id) ON DELETE CASCADE,
  turn_index  SMALLINT NOT NULL,
  role        TEXT NOT NULL CHECK (role IN ('user','assistant','system')),
  content     TEXT NOT NULL,
  token_usage JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_msg_session ON screening_messages(session_id, turn_index);

CREATE TABLE matches (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id                 UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  job_id                  UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  session_id              UUID REFERENCES screening_sessions(id),
  score_total             NUMERIC(5,2) NOT NULL CHECK (score_total BETWEEN 0 AND 100),
  score_location          NUMERIC(5,2) NOT NULL,
  score_availability      NUMERIC(5,2) NOT NULL,
  score_experience        NUMERIC(5,2) NOT NULL,
  score_response_quality  NUMERIC(5,2) NOT NULL,
  explanation_vi          TEXT NOT NULL,
  tier                    TEXT NOT NULL CHECK (tier IN ('hot','warm','cold')),
  distance_km             NUMERIC(6,2),
  rank_for_job            INTEGER,
  notified_hr             BOOLEAN NOT NULL DEFAULT FALSE,
  notified_at             TIMESTAMPTZ,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(lead_id, job_id)
);
CREATE INDEX idx_matches_rank       ON matches(job_id, score_total DESC);
CREATE INDEX idx_matches_unnotified ON matches(notified_hr, created_at) WHERE notified_hr = FALSE;
CREATE INDEX idx_matches_tier       ON matches(tier, job_id);

CREATE TABLE notifications_log (
  id             BIGSERIAL PRIMARY KEY,
  channel        TEXT NOT NULL CHECK (channel IN ('telegram','sms','email')),
  recipient      TEXT NOT NULL,
  match_id       UUID REFERENCES matches(id),
  lead_id        UUID REFERENCES leads(id),
  job_id         UUID REFERENCES jobs(id),
  payload        JSONB NOT NULL,
  status         TEXT NOT NULL CHECK (status IN ('sent','failed','retry')),
  error_message  TEXT,
  attempt_count  SMALLINT NOT NULL DEFAULT 1,
  sent_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_notif_retry ON notifications_log(status, sent_at) WHERE status IN ('failed','retry');

CREATE TABLE ai_calls (
  id             BIGSERIAL PRIMARY KEY,
  call_site      TEXT NOT NULL CHECK (call_site IN ('job_post_gen','screening_turn','scoring')),
  model          TEXT NOT NULL,
  input_tokens   INTEGER NOT NULL,
  cached_tokens  INTEGER NOT NULL DEFAULT 0,
  output_tokens  INTEGER NOT NULL,
  cost_usd       NUMERIC(10,6) NOT NULL,
  latency_ms     INTEGER,
  related_id     UUID,
  error_code     TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ai_calls_site_time ON ai_calls(call_site, created_at DESC);

CREATE OR REPLACE FUNCTION bump_tracking_click() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  UPDATE tracking_links
    SET click_count = click_count + 1,
        first_click_at = COALESCE(first_click_at, NEW.clicked_at),
        last_click_at  = NEW.clicked_at
  WHERE tracking_id = NEW.tracking_id;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_bump_click AFTER INSERT ON link_clicks
  FOR EACH ROW EXECUTE FUNCTION bump_tracking_click();

CREATE OR REPLACE FUNCTION bump_tracking_lead() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.tracking_id IS NOT NULL THEN
    UPDATE tracking_links SET lead_count = lead_count + 1
      WHERE tracking_id = NEW.tracking_id;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_bump_lead AFTER INSERT ON leads
  FOR EACH ROW EXECUTE FUNCTION bump_tracking_lead();

CREATE OR REPLACE FUNCTION pdpd_delete_lead(target_lead UUID)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
  UPDATE consent_records SET revoked_at = now() WHERE lead_id = target_lead;
  UPDATE leads
     SET phone_e164       = 'DELETED:' || substring(id::text, 1, 8),
         phone_raw        = 'DELETED',
         full_name        = 'DELETED',
         area_raw         = NULL,
         area_normalized  = NULL,
         area_district    = NULL,
         area_city        = NULL,
         area_lat         = NULL,
         area_lng         = NULL,
         ip_address       = NULL,
         user_agent       = NULL
   WHERE id = target_lead;
  UPDATE screening_messages SET content = '[redacted]'
   WHERE role = 'user'
     AND session_id IN (SELECT id FROM screening_sessions WHERE lead_id = target_lead);
END $$;
"""


DOWN_SQL = """
DROP FUNCTION IF EXISTS pdpd_delete_lead(UUID);
DROP TRIGGER IF EXISTS trg_bump_lead ON leads;
DROP FUNCTION IF EXISTS bump_tracking_lead();
DROP TRIGGER IF EXISTS trg_bump_click ON link_clicks;
DROP FUNCTION IF EXISTS bump_tracking_click();
DROP TABLE IF EXISTS ai_calls CASCADE;
DROP TABLE IF EXISTS notifications_log CASCADE;
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS screening_messages CASCADE;
DROP TABLE IF EXISTS screening_sessions CASCADE;
DROP TABLE IF EXISTS consent_records CASCADE;
DROP TABLE IF EXISTS leads CASCADE;
DROP TABLE IF EXISTS link_clicks CASCADE;
DROP TABLE IF EXISTS tracking_links CASCADE;
DROP TABLE IF EXISTS campaigns CASCADE;
DROP TABLE IF EXISTS sources CASCADE;
DROP TABLE IF EXISTS content_variants CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;
DROP TABLE IF EXISTS hr_users CASCADE;
DROP TABLE IF EXISTS companies CASCADE;
"""


def _split_sql(sql: str) -> list[str]:
    """Split a SQL script into individual statements, respecting dollar-quoted strings.
    asyncpg rejects multi-statement prepared statements, so we execute one at a time.
    """
    statements: list[str] = []
    buf: list[str] = []
    in_dollar = False
    dollar_tag = ""
    i = 0
    while i < len(sql):
        ch = sql[i]
        if not in_dollar and ch == "$" and sql[i:i + 2] == "$$":
            in_dollar = True
            dollar_tag = "$$"
            buf.append("$$")
            i += 2
            continue
        if in_dollar and sql[i:i + len(dollar_tag)] == dollar_tag:
            in_dollar = False
            buf.append(dollar_tag)
            i += len(dollar_tag)
            continue
        if ch == ";" and not in_dollar:
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def upgrade() -> None:
    for stmt in _split_sql(SCHEMA_SQL):
        op.execute(stmt)


def downgrade() -> None:
    for stmt in _split_sql(DOWN_SQL):
        op.execute(stmt)
