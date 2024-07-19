import aiosqlite as sq

from pathlib import Path


class Connection:
    db = None
    cur = None

    async def __aenter__(self):
        tg_db_path = str(Path(__file__).parent.parent) + '/tg.db'
        self.db = await sq.connect(tg_db_path, isolation_level=None, timeout=5)
        self.db.row_factory = sq.Row
        self.cur = await self.db.cursor()

        return self.cur

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.commit()
        await self.cur.close()
        await self.db.close()
