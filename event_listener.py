import datetime
import sys
import os
import time
import random
import json

from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetHistoryRequest
from loguru import logger
from dateutil import parser
import asyncio
import sqlite3

import dal

# Telegram API credentials
api_id = 19418891
api_hash = '9dc4be6c707b19578aa61328972af119'


async def add_orders_to_last_posts(group, last_post_id):
    with open('last_timeout.json', 'r') as f:
        data = json.load(f)

    data[group.name] = str(datetime.datetime.now())

    with open('last_timeout.json', 'w') as f:
        json.dump(data, f)

    new_post_id = group.new_post_id
    await asyncio.sleep(abs(last_post_id - new_post_id) * 1.5 + 0.1)
    while True:
        if last_post_id < new_post_id:
            break
        cur_order = await dal.Orders.get_order_by_group_and_post(group_id=group.id, post_id=new_post_id)
        if not cur_order:
            logger.info(
                f'Автонакрутка просмотров - Добавляем заказ на пост {new_post_id} в группе {group.name}')

            await dal.Orders.add_order(group_id=group.id, post_id=new_post_id, amount=group.amount)
            if group.auto_reactions == 1:
                logger.info(
                    f'Автонакрутка реакций - Добавляем заказ на пост {new_post_id} в группе {group.name}')

                await dal.Reactions.add_reaction(group_id=group.id, post_id=new_post_id,
                                                 amount=group.reactions_amount)

        new_post_id += 1
        await asyncio.sleep(random.uniform(0.2, 0.9))

    await dal.Groups.update_new_post_id_by_id(group.id, new_post_id)


async def setup_event_listener(channel_url, group_id, client):
    async def new_message_handler(event):
        group = await dal.Groups.get_group_by_id(group_id=group_id)
        if group.deleted or group.auto_orders == 0:
            logger.info(f'Автонакрутка - Убираем автонакрутку в группе {group.name}')
            await dal.Groups.update_setup_by_id(group_id=group_id, setup=0)
            client.remove_event_handler(new_message_handler, events.NewMessage(chats=channel))
        elif group.auto_orders == 1:
            await add_orders_to_last_posts(group, event.message.id)
            await dal.Groups.update_new_post_id_by_id(group_id=group_id, new_post_id=event.message.id + 1)
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

        with open('last_timeout.json', 'r') as file:
            last_timeout = json.load(file)

        for key in last_timeout:
            last_timeout[key] = parser.parse(last_timeout[key])
        groups = await dal.Groups.get_groups_list()
        for group in groups:
            last_check = last_timeout.get(group.name, None)
            channel_url = group.link
            group_id = group.id

            if group.auto_orders == 0:
                continue
            if not group.new_post_id:
                last_post_id = await get_last_message(client, channel_url)
                if not group.new_post_id:
                    new_post_id = last_post_id + 1
                    await dal.Groups.update_new_post_id_by_id(group_id, new_post_id)
                    logger.info(
                        f'Автонакрутка - new_post_id в группе {group.name} был обновлен'
                    )
            elif not last_check or datetime.datetime.now() > last_check + datetime.timedelta(minutes=20):
                last_post_id = await get_last_message(client, channel_url)
                if last_post_id >= group.new_post_id:
                    await add_orders_to_last_posts(group, last_post_id)
                    await asyncio.sleep(random.randrange(2, 4))

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
