import datetime
import sys
import os
import time
import random

from telethon import TelegramClient, events
from loguru import logger
import asyncio
import sqlite3

import dal
import views

# Telegram API credentials
api_id = 19418891
api_hash = '9dc4be6c707b19578aa61328972af119'
client = TelegramClient('session_Danek', api_id, api_hash)


async def setup_event_listener(channel_url, group_id):
    async def new_message_handler(event):
        group = await dal.Groups.get_group_by_id(group_id=group_id)
        if group.deleted or group.auto_orders == 0:
            logger.info(f'Автонакрутка - Убираем автонакрутку в группе {group.name}')
            await dal.Groups.update_setup_by_id(group_id=group_id, setup=0)
            client.remove_event_handler(new_message_handler, events.NewMessage(chats=channel))
        elif group.auto_orders == 1:
            logger.info(f'Автонакрутка - Добавляем заказ на пост {event.message.id} в группе {group.name}')

            order_id = await dal.Orders.add_order(group_id=group_id, post_id=event.message.id, amount=group.amount)
            await dal.Orders.update_started_by_id(order_id=order_id, started=1)
            await views.start_post_views_increasing(
                channel_url, order_id, group.amount, cur_hour=0, post_time=datetime.datetime.now()
            )
        else:
            logger.warning(f'Автонакрутка - Пропускаем пост {event.message.id} в группе {group.name} - выключен авто ордер')

    try:
        channel = await client.get_entity(channel_url)
        client.add_event_handler(new_message_handler, events.NewMessage(chats=channel))
    except Exception as exc:
        logger.error(f'Группы {channel_url} не существует. Удаляем группу')
        await dal.Groups.delete_by_id(group_id=group_id)


async def start_backend():
    await dal.Groups.create_db()
    await dal.Orders.create_db()
    logger.info('Трекер постов для каналов был запущен')

    while True:
        groups = await dal.Groups.get_not_setup_groups_list()
        for group in groups:

            channel_url = group.link
            group_id = group.id

            if group.auto_orders == 1:
                logger.info(f'Автонакрутка - прослушиваем группу {group.name}')
                asyncio.create_task(setup_event_listener(channel_url, group_id))
                await dal.Groups.update_setup_by_id(group_id=group_id, setup=1)

        await asyncio.sleep(random.randrange(15, 35))


def drop_group_setups():
    asyncio.run(dal.Groups.drop_setups())


def main():
    logger.info('Запускаем трекер постов для каналов...')
    try:
        with client:
            client.loop.run_until_complete(start_backend())
    except KeyboardInterrupt:
        drop_group_setups()
        logger.info(f'Программа прекратила работу.')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)
    except sqlite3.OperationalError:
        logger.info(f'Ошибка - database is locked. Пробуем перезапустить')
        time.sleep(10.5)
    except Exception as exc:
        drop_group_setups()
        logger.info(f'Программа прекратила работу. Ошибка - {type(exc)}')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)


if __name__ == "__main__":
    while True:
        main()
