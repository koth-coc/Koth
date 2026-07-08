CREATE TABLE IF NOT EXISTS koths (
    id              TEXT PRIMARY KEY,
    guild_id        BIGINT NOT NULL,
    th_level        INTEGER,
    start_time      TIMESTAMPTZ,
    log_channel_id  BIGINT,
    reg_channel_id  BIGINT,
    clan_link       TEXT,
    status          TEXT NOT NULL DEFAULT 'created',
    reminder_sent   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS registrations (
    id            SERIAL PRIMARY KEY,
    koth_id       TEXT NOT NULL REFERENCES koths(id) ON DELETE CASCADE,
    discord_id    BIGINT NOT NULL,
    player_tag    TEXT NOT NULL,
    player_name   TEXT NOT NULL,
    clan_name     TEXT,
    league        TEXT,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (koth_id, discord_id),
    UNIQUE (koth_id, player_tag)
);
