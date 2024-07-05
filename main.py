from aiogram import executor

import dal
from app.handlers import dp


async def on_startup(_):
    await dal.Groups.create_db()
    await dal.Orders.create_db()
    await dal.Subs.create_db()
    print('Бот успешно запущен!')

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True, timeout=None)
