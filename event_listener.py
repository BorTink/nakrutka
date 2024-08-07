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
import reactions

# Telegram API credentials
api_id = 19418891
api_hash = '9dc4be6c707b19578aa61328972af119'


async def setup_event_listener(channel_url, group_id, client):
    async def new_message_handler(event):
        group = await dal.Groups.get_group_by_id(group_id=group_id)
        if group.deleted or group.auto_orders == 0:
            logger.info(f'Автонакрутка - Убираем автонакрутку в группе {group.name}')
            await dal.Groups.update_setup_by_id(group_id=group_id, setup=0)
            client.remove_event_handler(new_message_handler, events.NewMessage(chats=channel))
        elif group.auto_orders == 1:
            logger.info(f'Автонакрутка просмотров - Добавляем заказ на пост {event.message.id} в группе {group.name}')

            await dal.Orders.add_order(group_id=group_id, post_id=event.message.id, amount=group.amount)
            if group.auto_reactions == 1:
                logger.info(f'Автонакрутка реакций - Добавляем заказ на пост {event.message.id} в группе {group.name}')

                await dal.Reactions.add_reaction(group_id=group_id, post_id=event.message.id, amount=group.reactions_amount)
        else:
            logger.warning(f'Автонакрутка - Пропускаем пост {event.message.id} в группе {group.name} - выключен авто ордер')

    try:
        if not client.is_connected():
            logger.warning('Клиент отключился. Переподключаемся')
            await client.connect()

        channel = await client.get_entity(channel_url)
        client.add_event_handler(new_message_handler, events.NewMessage(chats=channel))
    except Exception as exc:
        logger.error(f'Группы {channel_url} не существует. Удаляем группу')
        await dal.Groups.delete_by_id(group_id=group_id)


async def start_backend(client, last_reboot_day):
    await dal.Groups.create_db()
    await dal.Orders.create_db()
    logger.info('Трекер постов для каналов был запущен')

    while True:
        groups = await dal.Groups.get_not_setup_groups_list()
        for group in groups:

            channel_url = group.link
            group_id = group.id

            if group.auto_orders == 1:
                logger.info(f'Автонакрутка просмотров - прослушиваем группу {group.name}')
                await dal.Groups.update_setup_by_id(group_id=group_id, setup=1)
                asyncio.create_task(setup_event_listener(channel_url, group_id, client))

        now = datetime.datetime.now()
        if all([
            now.day != last_reboot_day,
            now.hour == 3,
            3 < datetime.datetime.now().minute < 10
        ]):
            break

        await asyncio.sleep(random.randrange(2, 4))

def drop_group_setups():
    asyncio.run(dal.Groups.drop_setups())


async def main():
    logger.info('Запускаем трекер постов для каналов...')
    last_reboot_day = 0
    while True:
        client = TelegramClient('session_Danek', api_id, api_hash, auto_reconnect=True)
        await client.connect()

        async with client:
            await start_backend(client, last_reboot_day)

        logger.warning('Плановое переподключение клиента в 3 часа ночи.')
        last_reboot_day = datetime.datetime.now().day
        await client.disconnect()
        await dal.Groups.drop_setups()


if __name__ == "__main__":
    try:
        while True:
            asyncio.run(main())
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
        logger.info(f'Программа прекратила работу. Ошибка - {exc}')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)
