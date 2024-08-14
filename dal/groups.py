from schemas import Group
import dal


class Groups:
    @classmethod
    async def create_db(cls):
        async with dal.Connection() as cur:
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS groups(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                link TEXT,
                new_post_id INTEGER,
                amount INTEGER,
                reactions_amount INTEGER DEFAULT 0,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                setup INTEGER DEFAULT 0,
                auto_orders INTEGER DEFAULT 0,
                auto_reactions INTEGER DEFAULT 0,
                deleted INTEGER DEFAULT 0
                )
            """)

    @classmethod
    async def get_groups_list(cls):
        async with dal.Connection() as cur:
            await cur.execute("""
                SELECT *
                FROM groups
                WHERE deleted == 0
                ORDER BY last_update DESC
            """)

            groups = await cur.fetchall()
            return [Group(**res) for res in groups]

    @classmethod
    async def get_not_setup_groups_list(cls):
        async with dal.Connection() as cur:
            await cur.execute("""
                SELECT *
                FROM groups
                WHERE deleted == 0
                AND setup = 0
                ORDER BY last_update DESC
            """)

            groups = await cur.fetchall()
            return [Group(**res) for res in groups]

    @classmethod
    async def get_group_by_id(cls, group_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                    SELECT *
                    FROM groups
                    WHERE deleted == 0
                    AND id = ?
                    ORDER BY last_update DESC
                """, (group_id,))

            group = await cur.fetchone()
            if group:
                return Group(**group)
            else:
                return None

    @classmethod
    async def get_new_post_id_by_group_id(cls, group_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                        SELECT new_post_id
                        FROM groups
                        WHERE deleted == 0
                        AND id = ?
                        ORDER BY last_update DESC
                    """, (group_id,))

            new_post_id = await cur.fetchone()
            if new_post_id:
                return int(new_post_id['new_post_id'])
            else:
                return None

    @classmethod
    async def get_views_stats_by_group_id(cls, group_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                SELECT SUM(full_amount - left_amount) as cnt
                FROM orders
                WHERE last_update >= datetime('now', '-1 month')
                AND group_id = ?
            """, (group_id,))

            stats = await cur.fetchone()
            stats = stats['cnt']
            if stats:
                return int(stats)
            else:
                return None

    @classmethod
    async def get_subs_stats_by_group_id(cls, group_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                    SELECT SUM(full_amount - left_amount) as cnt
                    FROM subs
                    WHERE last_update >= datetime('now', '-1 month')
                    AND group_id = ?
                """, (group_id,))

            stats = await cur.fetchone()
            stats = stats['cnt']
            if stats:
                return int(stats)
            else:
                return None

    @classmethod
    async def add_group(cls, name, link, amount):
        async with dal.Connection() as cur:
            await cur.execute("""
                INSERT INTO groups (name, link, amount)
                VALUES (?, ?, ?)
            """, (name, link, amount))

    @classmethod
    async def update_amount_by_id(cls, group_id, amount):
        async with dal.Connection() as cur:
            await cur.execute("""
                UPDATE groups
                SET amount = ?,
                last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                WHERE id = ?
            """, (amount, group_id))

    @classmethod
    async def update_reactions_amount_by_id(cls, group_id, reactions_amount):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE groups
                    SET reactions_amount = ?,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE id = ?
                """, (reactions_amount, group_id))

    @classmethod
    async def update_auto_orders_by_id(cls, group_id, auto_orders):
        async with dal.Connection() as cur:
            await cur.execute("""
                UPDATE groups
                SET auto_orders = ?,
                last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                WHERE id = ?
            """, (auto_orders, group_id))

    @classmethod
    async def update_auto_reactions_by_id(cls, group_id, auto_reactions):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE groups
                    SET auto_reactions = ?,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE id = ?
                """, (auto_reactions, group_id))

    @classmethod
    async def update_setup_by_id(cls, group_id, setup):
        async with dal.Connection() as cur:
            await cur.execute("""
                UPDATE groups
                SET setup = ?,
                last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                WHERE id = ?
            """, (setup, group_id))

    @classmethod
    async def update_new_post_id_by_id(cls, group_id, new_post_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                        UPDATE groups
                        SET new_post_id = ?,
                        last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                        WHERE id = ?
                    """, (new_post_id, group_id))

    @classmethod
    async def delete_by_id(cls, group_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE groups
                    SET deleted = 1,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE id = ?
                """, (group_id, ))

    @classmethod
    async def drop_setups(cls):
        async with dal.Connection() as cur:
            await cur.execute("""
                UPDATE groups
                SET setup = 0,
                last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
            """)
