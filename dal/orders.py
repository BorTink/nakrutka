import sqlite3 as sq

import dal
from schemas import Order, OrderWithGroupInfo
from contextlib import closing


class Orders:
    @classmethod
    async def create_db(cls):
        global db
        db = await dal.Groups.get_db()

        with closing(db.cursor()) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                post_id INTEGER,
                full_amount INTEGER,
                left_amount INTEGER,
                
                started INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                stopped INTEGER DEFAULT 0,
                order_deleted INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
                FOREIGN KEY (group_id) REFERENCES groups(id)
                )
            """)

    @classmethod
    async def get_not_started_orders_list(cls):
        with closing(db.cursor()) as cur:
            cur.execute("""
                SELECT orders.*, groups.link as group_link
                FROM orders
                JOIN groups ON groups.id = orders.group_id
                WHERE order_deleted == 0
                AND started == 0
                ORDER BY created_date DESC
            """)

            orders = cur.fetchall()
            return [OrderWithGroupInfo(**res) for res in orders]

    @classmethod
    async def get_orders_list_by_group_id(cls, group_id):
        with closing(db.cursor()) as cur:
            cur.execute("""
                    SELECT *
                    FROM orders
                    WHERE order_deleted == 0
                    AND group_id = ?
                    ORDER BY created_date DESC
                """, (group_id,))

            orders = cur.fetchall()
            return [Order(**res) for res in orders]

    @classmethod
    async def get_order_by_id(cls, order_id):
        with closing(db.cursor()) as cur:
            cur.execute("""
                    SELECT *
                    FROM orders
                    WHERE order_deleted == 0
                    AND post_id = ?
                    ORDER BY created_date DESC
                """, (order_id,))

            order = cur.fetchone()
            if order:
                return Order(**order)
            else:
                return None

    @classmethod
    async def add_order(cls, group_id, post_id, amount, stopped=0):
        with closing(db.cursor()) as cur:
            cur.execute("""
                INSERT INTO orders (group_id, post_id, full_amount, left_amount, stopped)
                VALUES (?, ?, ?, ?, ?)
            """, (group_id, post_id, amount, amount, stopped))

    @classmethod
    async def update_left_amount_by_id(cls, order_id, amount):
        with closing(db.cursor()) as cur:
            cur.execute("""
                UPDATE orders
                SET left_amount = ?
                WHERE post_id = ?
            """, (amount, order_id))

    @classmethod
    async def update_completed_by_id(cls, order_id, completed):
        with closing(db.cursor()) as cur:
            cur.execute("""
                    UPDATE orders
                    SET completed = ?
                    WHERE post_id = ?
                """, (completed, order_id))

    @classmethod
    async def update_stopped_by_id(cls, order_id, stopped):
        with closing(db.cursor()) as cur:
            cur.execute("""
                    UPDATE orders
                    SET stopped = ?
                    WHERE post_id = ?
                """, (stopped, order_id))

    @classmethod
    async def update_started_by_id(cls, order_id, started):
        with closing(db.cursor()) as cur:
            cur.execute("""
                        UPDATE orders
                        SET started = ?
                        WHERE post_id = ?
                    """, (started, order_id))