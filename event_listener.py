import datetime
import sys
import os
import time
import random

from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from loguru import logger
import asyncio
import sqlite3

import dal

# Telegram API credentials
api_id = 19418891
api_hash = '9dc4be6c707b19578aa61328972af119'


async def get_last_message(client, channel_url):
    channel_entity = await client.get_entity(channel_url)
    posts = await client.get_messages(channel_entity)
    last_post = posts[0]

    return last_post.id


async def start_backend(client, last_reboot_day):
    await dal.Groups.create_db()
    await dal.Orders.create_db()
    logger.info('Трекер постов для каналов был запущен')

    while True:
        groups = await dal.Groups.get_groups_list()
        for group in groups:

            channel_url = group.link
            group_id = group.id

            if group.auto_orders == 1:
                last_post_id = await get_last_message(client, channel_url)
                if not group.new_post_id:
                    new_post_id = last_post_id + 1
                    await dal.Groups.update_new_post_id_by_id(group_id, new_post_id)
                    logger.info(
                        f'Автонакрутка - new_post_id в группе {group.name} был обновлен'
                    )
                elif last_post_id >= group.new_post_id:
                    new_post_id = group.new_post_id
                    while True:
                        logger.info(
                            f'Автонакрутка просмотров - Добавляем заказ на пост {new_post_id} в группе {group.name}')

                        await dal.Orders.add_order(group_id=group_id, post_id=new_post_id, amount=group.amount)
                        if group.auto_reactions == 1:
                            logger.info(
                                f'Автонакрутка реакций - Добавляем заказ на пост {new_post_id} в группе {group.name}')

                            await dal.Reactions.add_reaction(group_id=group_id, post_id=new_post_id,
                                                             amount=group.reactions_amount)

                        new_post_id += 1
                        if last_post_id < new_post_id:
                            break

                    await dal.Groups.update_new_post_id_by_id(group_id, new_post_id)

        now = datetime.datetime.now()
        if all([
            now.day != last_reboot_day,
            now.hour == 3,
            3 < datetime.datetime.now().minute < 10
        ]):
            break

        await asyncio.sleep(random.randrange(7, 12))


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
