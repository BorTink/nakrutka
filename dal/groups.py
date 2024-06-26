import sqlite3 as sq

from schemas import Group
from contextlib import closing


class Groups:
    @classmethod
    async def create_db(cls):
        global db
        db = sq.connect('tg.db', isolation_level=None)
        db.row_factory = sq.Row

        with closing(db.cursor()) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS groups(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                link TEXT,
                amount INTEGER,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                setup INTEGER DEFAULT 0,
                auto_orders INTEGER DEFAULT 0,
                deleted INTEGER DEFAULT 0
                )
            """)

    @classmethod
    async def get_db(cls):
        return db

    @classmethod
    async def get_groups_list(cls):
        with closing(db.cursor()) as cur:
            cur.execute("""
                SELECT *
                FROM groups
                WHERE deleted == 0
                ORDER BY last_update DESC
            """)

            groups = cur.fetchall()
            return [Group(**res) for res in groups]

    @classmethod
    async def get_not_setup_groups_list(cls):
        with closing(db.cursor()) as cur:
            cur.execute("""
                SELECT *
                FROM groups
                WHERE deleted == 0
                AND setup = 0
                ORDER BY last_update DESC
            """)

            groups = cur.fetchall()
            return [Group(**res) for res in groups]

    @classmethod
    async def get_group_by_id(cls, group_id):
        with closing(db.cursor()) as cur:
            cur.execute("""
                    SELECT *
                    FROM groups
                    WHERE deleted == 0
                    AND id = ?
                    ORDER BY last_update DESC
                """, (group_id,))

            group = cur.fetchone()
            if group:
                return Group(**group)
            else:
                return None

    @classmethod
    async def get_stats_by_group_id(cls, group_id):
        with closing(db.cursor()) as cur:
            cur.execute("""
                SELECT SUM(full_amount - left_amount) as cnt
                FROM orders
                WHERE last_update >= datetime('now', '-1 month')
                AND group_id = ?
            """, (group_id,))

            stats = cur.fetchone()
            stats = stats['cnt']
            if stats:
                return int(stats)
            else:
                return None

    @classmethod
    async def add_group(cls, name, link, amount):
        with closing(db.cursor()) as cur:
            cur.execute("""
                INSERT INTO groups (name, link, amount)
                VALUES (?, ?, ?)
            """, (name, link, amount))

    @classmethod
    async def update_amount_by_id(cls, group_id, amount):
        with closing(db.cursor()) as cur:
            cur.execute("""
                UPDATE groups
                SET amount = ?,
                last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                WHERE id = ?
            """, (amount, group_id))

    @classmethod
    async def update_auto_orders_by_id(cls, group_id, auto_orders):
        with closing(db.cursor()) as cur:
            cur.execute("""
                UPDATE groups
                SET auto_orders = ?,
                last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                WHERE id = ?
            """, (auto_orders, group_id))

    @classmethod
    async def update_setup_by_id(cls, group_id, setup):
        with closing(db.cursor()) as cur:
            cur.execute("""
                UPDATE groups
                SET setup = ?,
                last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                WHERE id = ?
            """, (setup, group_id))

    @classmethod
    async def delete_by_id(cls, group_id):
        with closing(db.cursor()) as cur:
            cur.execute("""
                    UPDATE groups
                    SET deleted = 1,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE id = ?
                """, (group_id, ))

    @classmethod  # ВАЖНО ОТМЕТИТЬ ЧТО ЭТО НЕ АСИНХРОНКА
    def drop_setups(cls):
        with closing(db.cursor()) as cur:
            cur.execute("""
                UPDATE groups
                SET setup = 0,
                last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
            """)