import dal
from schemas import Order, OrderWithGroupInfo


class Orders:
    @classmethod
    async def create_db(cls):
        async with dal.Connection() as cur:
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS orders(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                post_id INTEGER,
                full_amount INTEGER,
                left_amount INTEGER,
                hour INTEGER DEFAULT 0,
                
                started INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                stopped INTEGER DEFAULT 0,
                order_deleted INTEGER DEFAULT 0,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
                FOREIGN KEY (group_id) REFERENCES groups(id)
                )
            """)

    @classmethod
    async def get_orders_list(cls):
        async with dal.Connection() as cur:
            await cur.execute("""
                    SELECT orders.*, groups.link as group_link
                    FROM orders
                    JOIN groups ON groups.id = orders.group_id
                    WHERE order_deleted == 0
                    ORDER BY last_update DESC
                """)

            orders = await cur.fetchall()
            return [OrderWithGroupInfo(**res) for res in orders]

    @classmethod
    async def get_orders_list_by_group_id(cls, group_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                    SELECT *
                    FROM orders
                    WHERE order_deleted == 0
                    AND group_id = ?
                    ORDER BY last_update DESC
                """, (group_id,))

            orders = await cur.fetchall()
            return [Order(**res) for res in orders]

    @classmethod
    async def get_not_completed_orders_list_by_group_id(cls, group_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                        SELECT *
                        FROM orders
                        WHERE order_deleted == 0
                        AND completed = 0
                        AND group_id = ?
                        ORDER BY last_update DESC
                    """, (group_id,))

            orders = await cur.fetchall()
            return [Order(**res) for res in orders]

    @classmethod
    async def get_order_by_id(cls, order_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                    SELECT *
                    FROM orders
                    WHERE order_deleted == 0
                    AND id = ?
                    ORDER BY last_update DESC
                """, (order_id,))

            order = await cur.fetchone()
            if order:
                return Order(**order)
            else:
                return None

    @classmethod
    async def get_order_by_group_and_post(cls, group_id, post_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                        SELECT *
                        FROM orders
                        WHERE order_deleted == 0
                        AND group_id = ?
                        AND post_id = ?
                        ORDER BY last_update DESC
                    """, (group_id, post_id,))

            order = await cur.fetchone()
            if order:
                return Order(**order)
            else:
                return None

    @classmethod
    async def get_not_completed_order_by_group_and_post(cls, group_id, post_id):
        async with dal.Connection() as cur:
            await cur.execute("""
                            SELECT *
                            FROM orders
                            WHERE order_deleted == 0
                            AND completed = 0
                            AND group_id = ?
                            AND post_id = ?
                            ORDER BY last_update DESC
                        """, (group_id, post_id,))

            order = await cur.fetchone()
            if order:
                return Order(**order)
            else:
                return None

    @classmethod
    async def add_order(cls, group_id, post_id, amount, stopped=0):
        async with dal.Connection() as cur:
            await cur.execute("""
                INSERT INTO orders (group_id, post_id, full_amount, left_amount, stopped)
                VALUES (?, ?, ?, ?, ?)
                RETURNING id
            """, (group_id, post_id, amount, amount, stopped))
            order_id = await cur.fetchone()
            order_id = dict(order_id)
            if order_id:
                return int(order_id['id'])
            else:
                return None

    @classmethod
    async def update_left_amount_by_id(cls, order_id, amount):
        async with dal.Connection() as cur:
            await cur.execute("""
                UPDATE orders
                SET left_amount = ?,
                last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                WHERE id = ?
            """, (amount, order_id))

    @classmethod
    async def update_completed_by_id(cls, order_id, completed):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE orders
                    SET completed = ?,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE id = ?
                """, (completed, order_id))

    @classmethod
    async def update_stopped_by_id(cls, order_id, stopped):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE orders
                    SET stopped = ?,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE id = ?
                """, (stopped, order_id))

    @classmethod
    async def update_started_by_id(cls, order_id, started):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE orders
                    SET started = ?,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE id = ?
                """, (started, order_id))

    @classmethod
    async def update_hour_by_id(cls, order_id, hour):
        async with dal.Connection() as cur:
            await cur.execute("""
                    UPDATE orders
                    SET hour = ?,
                    last_update = strftime('%Y-%m-%d %H:%M:%S', datetime('now'))
                    WHERE id = ?
                """, (hour, order_id))
