import sqlite3 as sq

import dal
from schemas import Order


class Orders:
    @classmethod
    async def create_db(cls):
        global db, cur
        db, cur = await dal.Groups.get_db_cur()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            post_id INTEGER,
            full_amount INTEGER,
            left_amount INTEGER,
            completed INTEGER DEFAULT 0,
            stopped INTEGER DEFAULT 0,
            deleted INTEGER DEFAULT 0,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (group_id) REFERENCES groups(id)
            )
        """)

    @classmethod
    async def get_orders_list(cls):
        cur.execute("""
            SELECT *
            FROM orders
            WHERE deleted == 0
            ORDER BY created_date DESC
        """)

        orders = cur.fetchall()
        return [Order(**res) for res in orders]

    @classmethod
    async def get_orders_list_by_group_id(cls, group_id):
        cur.execute("""
                SELECT *
                FROM orders
                WHERE deleted == 0
                AND group_id = ?
                ORDER BY created_date DESC
            """, (group_id,))

        orders = cur.fetchall()
        return [Order(**res) for res in orders]

    @classmethod
    async def get_order_by_id(cls, order_id):
        cur.execute("""
                SELECT *
                FROM orders
                WHERE deleted == 0
                AND post_id = ?
                ORDER BY created_date DESC
            """, (order_id,))

        order = cur.fetchone()
        if order:
            return Order(**order)
        else:
            return None

    @classmethod
    async def add_order(cls, group_id, post_id, amount):
        cur.execute("""
            INSERT INTO orders (group_id, post_id, full_amount, left_amount)
            VALUES (?, ?, ?, ?)
        """, (group_id, post_id, amount, amount))

    @classmethod
    async def update_amount_by_id(cls, order_id, amount):
        cur.execute("""
            UPDATE orders
            SET amount = ?
            WHERE post_id = ?
        """, (amount, order_id))
        db.commit()

    @classmethod
    async def update_auto_orders_by_id(cls, order_id, auto_orders):
        cur.execute("""
                UPDATE orders
                SET auto_orders = ?
                WHERE post_id = ?
            """, (auto_orders, order_id))

    @classmethod
    async def update_stopped_by_id(cls, order_id, stopped):
        cur.execute("""
                    UPDATE orders
                    SET stopped = ?
                    WHERE post_id = ?
                """, (stopped, order_id))
