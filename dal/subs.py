import dal
from schemas import Sub, SubWithGroupInfo


class Subs:
    @classmethod
    async def create_db(cls):
        async with dal.Connection() as cur:
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS subs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                full_amount INTEGER,
                left_amount INTEGER,
                hour INTEGER DEFAULT 0,
                
                started INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                stopped INTEGER DEFAULT 0,
                sub_deleted INTEGER DEFAULT 0,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (group_id) REFERENCES groups(id)
                )
            """)

    @classmethod
    async def get_not_started_subs_list(cls):
        async with dal.Connection() as cur:
            await cur.execute("""
                SELECT subs.*, groups.link as group_link
                FROM subs
                JOIN groups ON groups.id = subs.group_id
                WHERE sub_deleted == 0
                AND started == 0
                AND completed = 0
                ORDER BY last_update DESC
                LIMIT 1
            """)

            subs = await cur.fetchall()
            return [SubWithGroupInfo(**res) for res in subs]

    @classmethod
    async def get_subs_list(cls):
        async with dal.Connection() as cur:
            await cur.execute("""
                    SELECT subs.*, groups.link as group_link
                    FROM subs
                    JOIN groups ON groups.id = subs.group_id
                    WHERE sub_deleted == 0
                    AND completed = 0
                    ORDER BY last_update DESC
                """)

            subs = await cur.fetchall()
            return [SubWithGroupInfo(**res) for res in subs]

    @classmethod
    async def get_sub_by_group_id(cls, group_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                    SELECT *
                    FROM subs
                    WHERE sub_deleted = 0
                    AND completed = 0
                    AND group_id = ?
                    ORDER BY last_update DESC
                    LIMIT 1
                """, (group_id,))

            sub = await cur.fetchone()
            if sub:
                return Sub(**sub)
            else:
                return None

    @classmethod
    async def add_sub(cls, group_id, amount):
        async with dal.Connection() as cur:
            await cur.execute("""
                INSERT INTO subs (group_id, full_amount, left_amount)
                VALUES (?, ?, ?)
            """, (group_id, amount, amount))

    @classmethod
    async def update_left_amount_by_group_id(cls, group_id, amount):
        async with dal.Connection() as cur:
            await cur.execute("""
                UPDATE subs
                SET left_amount = ?,
                last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                WHERE group_id = ?
                AND completed = 0
            """, (amount, group_id))

    @classmethod
    async def update_hour_by_group_id(cls, group_id, hour):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE subs
                    SET hour = ?,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE group_id = ?
                    AND completed = 0
                """, (hour, group_id))

    @classmethod
    async def update_completed_by_group_id(cls, group_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE subs
                    SET completed = 1,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE group_id = ?
                    AND completed = 0
                """, (group_id,))

    @classmethod
    async def update_stopped_by_group_id(cls, group_id, stopped):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE subs
                    SET stopped = ?,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE group_id = ?
                    AND completed = 0
                """, (stopped, group_id))

    @classmethod
    async def update_started_by_group_id(cls, group_id, started):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE subs
                    SET started = ?,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE group_id = ?
                    AND completed = 0
                """, (started, group_id))

    @classmethod
    async def update_sub_info_by_group_id(cls, group_id, full_amount):
        async with dal.Connection() as cur:
            await cur.execute("""
                        UPDATE subs
                        SET full_amount = ?,
                        left_amount = ?,
                        last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                        WHERE group_id = ?
                        AND completed = 0
                    """, (full_amount, full_amount, group_id))
