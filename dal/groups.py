import sqlite3 as sq

from schemas import Group


class Groups:
    @classmethod
    async def create_db(cls):
        global db, cur
        db = sq.connect('tg.db', isolation_level=None)
        db.row_factory = sq.Row
        cur = db.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS groups(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            link TEXT,
            last_update DATETIME DEFAULT now()
            deleted INTEGER DEFAULT 0
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS order(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER FOREIGN KEY groups,
            post_id INTEGER,
            full_amount INTEGER,
            left_amount INTEGER,
            completed INTEGER DEFAULT 0,
            stopped INTEGER DEFAULT 0,
            created_date DATETIME DEFAULT now()
            )
        """)

    @classmethod
    async def get_groups_list(cls):
        cur.execute("""
            SELECT *
            FROM groups
            WHERE deleted == 0
            ORDER BYH last_update DESC
        """)

        groups = cur.fetchall()
        if groups:
            return [Group(**res) for res in groups]

    @classmethod
    async def add_group(cls, name, link):
        cur.execute("""
            INSERT INTO groups (name, link)
            VALUES (?, ?)
        """, (name, link))

