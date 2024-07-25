import dal
from schemas import Reaction, ReactionWithGroupInfo


class Reactions:
    @classmethod
    async def create_db(cls):
        async with dal.Connection() as cur:
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS reactions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                post_id INTEGER,
                full_amount INTEGER,
                left_amount INTEGER,
                hour INTEGER DEFAULT 0,

                started INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                stopped INTEGER DEFAULT 0,
                reaction_deleted INTEGER DEFAULT 0,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (group_id) REFERENCES groups(id)
                )
            """)

    @classmethod
    async def get_reactions_list(cls):
        async with dal.Connection() as cur:
            await cur.execute("""
                    SELECT reactions.*, groups.link as group_link
                    FROM reactions
                    JOIN groups ON groups.id = reactions.group_id
                    WHERE reaction_deleted == 0
                    ORDER BY last_update DESC
                """)

            reactions = await cur.fetchall()
            return [ReactionWithGroupInfo(**res) for res in reactions]

    @classmethod
    async def get_reactions_list_by_group_id(cls, group_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                    SELECT *
                    FROM reactions
                    WHERE reaction_deleted == 0
                    AND group_id = ?
                    ORDER BY last_update DESC
                """, (group_id,))

            reactions = await cur.fetchall()
            return [Reaction(**res) for res in reactions]

    @classmethod
    async def get_not_completed_reactions_list_by_group_id(cls, group_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                        SELECT *
                        FROM reactions
                        WHERE reaction_deleted == 0
                        AND completed = 0
                        AND group_id = ?
                        ORDER BY last_update DESC
                    """, (group_id,))

            reactions = await cur.fetchall()
            return [Reaction(**res) for res in reactions]

    @classmethod
    async def get_reaction_by_id(cls, reaction_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                    SELECT *
                    FROM reactions
                    WHERE reaction_deleted == 0
                    AND id = ?
                    ORDER BY last_update DESC
                """, (reaction_id,))

            reaction = await cur.fetchone()
            if reaction:
                return Reaction(**reaction)
            else:
                return None

    @classmethod
    async def get_reaction_by_group_and_post(cls, group_id, post_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                        SELECT *
                        FROM reactions
                        WHERE reaction_deleted == 0
                        AND group_id = ?
                        AND post_id = ?
                        ORDER BY last_update DESC
                    """, (group_id, post_id,))

            reaction = await cur.fetchone()
            if reaction:
                return Reaction(**reaction)
            else:
                return None

    @classmethod
    async def add_reaction(cls, group_id, post_id, amount, stopped=0):
        async with dal.Connection() as cur:
            await cur.execute("""
                INSERT INTO reactions (group_id, post_id, full_amount, left_amount, stopped)
                VALUES (?, ?, ?, ?, ?)
                RETURNING id
            """, (group_id, post_id, amount, amount, stopped))
            reaction_id = await cur.fetchone()
            reaction_id = dict(reaction_id)
            if reaction_id:
                return int(reaction_id['id'])
            else:
                return None

    @classmethod
    async def update_left_amount_by_id(cls, reaction_id, amount):
        async with dal.Connection() as cur:
            await cur.execute("""
                UPDATE reactions
                SET left_amount = ?,
                last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                WHERE id = ?
            """, (amount, reaction_id))

    @classmethod
    async def update_completed_by_id(cls, reaction_id, completed):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE reactions
                    SET completed = ?,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE id = ?
                """, (completed, reaction_id))

    @classmethod
    async def update_stopped_by_id(cls, reaction_id, stopped):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE reactions
                    SET stopped = ?,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE id = ?
                """, (stopped, reaction_id))

    @classmethod
    async def update_started_by_id(cls, reaction_id, started):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE reactions
                    SET started = ?,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE id = ?
                """, (started, reaction_id))

    @classmethod
    async def update_hour_by_id(cls, reaction_id, hour):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE reactions
                    SET hour = ?,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE id = ?
                """, (hour, reaction_id))
