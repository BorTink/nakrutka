import datetime
import sys
import os
import json

from telethon import TelegramClient
from loguru import logger
import asyncio
import requests

import dal

# Telegram API credentials
api_id = 19418891
api_hash = '9dc4be6c707b19578aa61328972af119'
client = TelegramClient('session_Danek', api_id, api_hash)


def get_channel_name(channel_url):
    # Assuming the channel URL is in the format "https://t.me/channelname"
    # This splits the URL by '/' and returns the last part as the channel name
    return channel_url.split('/')[-1]


def send_sub(channel_url, subs_count):
    channel_name = get_channel_name(channel_url)
    with open('services.json', 'r') as file:
        file_data = json.load(file)

    service_id = file_data['subscribers_service_id']
    api_key = file_data['subscribers_api_key']
    service_url = file_data['subscribers_url']

    payload = {
        'key': api_key,
        'action': 'add',
        'service': service_id,
        'link': channel_url,
        'quantity': subs_count
    }

    sub_url = f"{service_url}/api/v2"
    response = requests.post(sub_url, data=payload)
    response_json = response.json()

    logger.info(f"Order placed for {subs_count} subs in channel '{channel_name}' at {datetime.datetime.now().time()}")
    return response_json


async def start_post_views_increasing(channel_url, group_id):
    first_start = True
    while True:
        do_sub = await dal.Subs.get_sub_by_group_id(group_id=group_id)
        group = await dal.Groups.get_group_by_id(group_id=group_id)

        if not first_start:
            await asyncio.sleep(do_sub.minutes * 60)
        first_start = False

        if do_sub.started == 0:
            await dal.Subs.update_started_by_group_id(group_id=group_id, started=1)

        while do_sub.stopped == 1 and do_sub.completed == 0 and do_sub.sub_deleted == 0:
            await asyncio.sleep(120)
            do_sub = await dal.Subs.get_sub_by_group_id(group_id=group_id)

        if do_sub.completed == 1:
            logger.info(f'Order for subs in group {group.name} is completed')
            break

        if do_sub.sub_deleted == 1:
            logger.info(f'Order for subs in group {group.name} is deleted')
            break

        if do_sub.subs_count > do_sub.left_amount:
            do_sub.subs_count = do_sub.left_amount

        send_sub(channel_url, do_sub.subs_count)  # Place the sub
        left_amount = int(do_sub.left_amount) - int(do_sub.subs_count)

        await dal.Subs.update_left_amount_by_group_id(group_id=group_id, amount=left_amount)
        if left_amount <= 0:
            await dal.Subs.update_completed_by_group_id(group_id=group_id)
            logger.info(f'Order for subs in group {group.name} is completed')
            break


async def start_backend():
    await dal.Groups.create_db()
    await dal.Subs.create_db()
    logger.info('Backend started')

    while True:
        subs = await dal.Subs.get_subs_list()
        for sub in subs:
            if sub.left_amount <= 0:
                await dal.Subs.update_completed_by_group_id(group_id=sub.group_id)

            elif any([
                sub.started == 0,
                sub.completed == 0 and sub.stopped == 0 and
                (datetime.datetime.utcnow() - sub.last_update) > datetime.timedelta(seconds=sub.minutes * 60 + 2)
            ]):
                logger.info(f'Doing subs for - {sub.group_link}')
                channel_url = sub.group_link

                asyncio.create_task(
                    start_post_views_increasing(
                        channel_url=channel_url, group_id=sub.group_id
                    )
                )

        await asyncio.sleep(5)


def drop_group_setups():
    dal.Groups.drop_setups()


if __name__ == "__main__":
    logger.info('Backend post views increasing programm has been started')
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
    except Exception as exc:
        drop_group_setups()
        logger.info(f'Программа прекратила работу. Ошибка - {exc}')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)
