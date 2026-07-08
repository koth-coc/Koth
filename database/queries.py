from .connection import pool


# ---------- koth helpers ----------

async def create_koth(koth_id, guild_id, th_level, start_time, log_channel_id, reg_channel_id):
    async with pool().acquire() as con:
        await con.execute(
            """INSERT INTO koths (id, guild_id, th_level, start_time, log_channel_id, reg_channel_id)
               VALUES ($1,$2,$3,$4,$5,$6)""",
            koth_id, guild_id, th_level, start_time, log_channel_id, reg_channel_id,
        )


async def get_koth(koth_id):
    async with pool().acquire() as con:
        return await con.fetchrow("SELECT * FROM koths WHERE id = $1", koth_id)


async def update_koth(koth_id, **fields):
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(fields.keys()))
    async with pool().acquire() as con:
        await con.execute(
            f"UPDATE koths SET {set_clause} WHERE id = $1",
            koth_id, *fields.values(),
        )


async def delete_koth(koth_id):
    async with pool().acquire() as con:
        await con.execute("DELETE FROM koths WHERE id = $1", koth_id)


async def get_koths_due_for_reminder():
    async with pool().acquire() as con:
        return await con.fetch(
            """SELECT * FROM koths
               WHERE reminder_sent = FALSE
                 AND start_time IS NOT NULL
                 AND start_time <= now()"""
        )


async def mark_reminder_sent(koth_id):
    async with pool().acquire() as con:
        await con.execute("UPDATE koths SET reminder_sent = TRUE WHERE id = $1", koth_id)


async def get_all_koths(guild_id):
    async with pool().acquire() as con:
        return await con.fetch(
            """SELECT k.*, COUNT(r.id) AS registration_count
               FROM koths k
               LEFT JOIN registrations r ON r.koth_id = k.id
               WHERE k.guild_id = $1
               GROUP BY k.id
               ORDER BY k.created_at DESC""",
            guild_id,
        )


# ---------- registration helpers ----------

async def add_registration(koth_id, discord_id, player_tag, player_name, clan_name, league):
    async with pool().acquire() as con:
        await con.execute(
            """INSERT INTO registrations (koth_id, discord_id, player_tag, player_name, clan_name, league)
               VALUES ($1,$2,$3,$4,$5,$6)""",
            koth_id, discord_id, player_tag, player_name, clan_name, league,
        )


async def get_registrations(koth_id):
    async with pool().acquire() as con:
        return await con.fetch("SELECT * FROM registrations WHERE koth_id = $1", koth_id)


async def find_registration(koth_id, discord_id, player_tag):
    async with pool().acquire() as con:
        return await con.fetchrow(
            "SELECT * FROM registrations WHERE koth_id = $1 AND discord_id = $2 AND player_tag = $3",
            koth_id, discord_id, player_tag,
        )


async def remove_registration(reg_id):
    async with pool().acquire() as con:
        await con.execute("DELETE FROM registrations WHERE id = $1", reg_id)


async def is_tag_registered_for_koth(koth_id, player_tag):
    async with pool().acquire() as con:
        return await con.fetchrow(
            "SELECT 1 FROM registrations WHERE koth_id = $1 AND player_tag = $2",
            koth_id, player_tag,
        )
