import datetime
import sys
import os
import json
import random
import time

from loguru import logger
import asyncio
import requests
import sqlite3
import numpy as np

import dal

# Telegram API credentials
api_id = 19418891
api_hash = '9dc4be6c707b19578aa61328972af119'


async def calculate_view_distribution(total_views, cur_hour):
    full_distribution_list = [15, 9, 8, 7, 7, 7, 7, 7, 7, 7, 7, 7]
    full_distribution = np.array(full_distribution_list)

    full_distribution = full_distribution * np.random.uniform(low=0.75, high=1.25, size=(len(full_distribution_list),))

    normalized_distribution = full_distribution / full_distribution.sum()
    views_distribution = np.round(normalized_distribution * total_views).astype(int)
    views_distribution = np.where(views_distribution < 10, views_distribution + 10, views_distribution)

    accumulated_views = views_distribution.cumsum()
    if accumulated_views[-1] > total_views:
        last_necessary_order = np.argmax(accumulated_views >= total_views)
        views_distribution = views_distribution[:last_necessary_order + 1]

    return views_distribution[cur_hour:]


async def get_channel_name(channel_url):
    # Assuming the channel URL is in the format "https://t.me/channelname"
    # This splits the URL by '/' and returns the last part as the channel name
    return channel_url.split('/')[-1]


async def send_sub(channel_url, subs_count, group_name, cur_hour, profile):
    with open(f'services/services_{profile}.json', 'r') as file:
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

    logger.info(f"Ордер на {subs_count} подписчиков в канале '{group_name}' на  период {cur_hour} был размещен в "
                f"{datetime.datetime.now().time()}")
    return response_json


async def start_post_views_increasing(channel_url, group_id, total_views, cur_hour, subs_wait_time):
    distributions = await calculate_view_distribution(total_views, cur_hour)
    group = await dal.Groups.get_group_by_id(group_id=group_id)

    first_start = True
    if distributions.size == 0:
        await dal.Subs.update_completed_by_group_id(group_id=group_id)
        logger.info(f'Ордер для подписчиков в группе {group.name} был завершен раньше времени')
        await dal.Subs.update_left_amount_by_group_id(group_id=group_id, amount=0)

    for subs_count in distributions:
        do_sub = await dal.Subs.get_sub_by_group_id(group_id=group_id)

        if total_views != do_sub.full_amount:
            await dal.Subs.update_hour_by_group_id(group_id=group_id, hour=0)
            await dal.Subs.update_started_by_group_id(group_id=group_id, started=0)
            logger.info(f'Кол-во подписчиков в ордере в группе {group.name} было изменено. Пересобираем распределение')
            break

        if not first_start:
            await asyncio.sleep(subs_wait_time)
        first_start = False

        if do_sub.started == 0:
            await dal.Subs.update_started_by_group_id(group_id=group_id, started=1)

        while do_sub.stopped == 1 and do_sub.completed == 0 and do_sub.sub_deleted == 0:
            logger.info(f'Ордер для подписчиков в группе {group.name} был остановлен')
            break

        if do_sub.completed == 1:
            logger.info(f'Ордер для подписчиков в группе {group.name} был завершен')
            break

        if do_sub.sub_deleted == 1:
            logger.info(f'Ордер для подписчиков в группе {group.name} был удален')
            break

        if subs_count > do_sub.left_amount:
            subs_count = do_sub.left_amount

        await dal.Subs.update_hour_by_group_id(group_id=group_id, hour=cur_hour + 1)

        profile = await dal.Groups.get_group_profile_by_id(do_sub.group_id)
        await send_sub(channel_url, subs_count, group.name, cur_hour, profile)  # Place the sub
        left_amount = int(do_sub.left_amount) - int(subs_count)

        await dal.Subs.update_left_amount_by_group_id(group_id=group_id, amount=left_amount)
        if left_amount <= 0:
            await dal.Subs.update_completed_by_group_id(group_id=group_id)
            logger.info(f'Ордер для подписчиков в группе {group.name} был завершен')
            break

        cur_hour += 1


async def start_backend():
    await dal.Groups.create_db()
    await dal.Subs.create_db()
    logger.info('Программа для накрутки подписчиков была запущена')

    while True:
        subs = await dal.Subs.get_subs_list()

        for sub in subs:
            if sub.left_amount <= 0:
                await dal.Subs.update_completed_by_group_id(group_id=sub.group_id)

            elif any([
                sub.started == 0,
                sub.completed == 0 and sub.stopped == 0 and
                (datetime.datetime.utcnow() - sub.last_update) > datetime.timedelta(seconds=subs_wait_time + 2)
            ]):
                logger.info(f'Выполняем ордер для подписчиков - {sub.group_link}')
                channel_url = sub.group_link

                profile = await dal.Groups.get_group_profile_by_id(sub.group_id)
                with open(f'services/services_{profile}.json', 'r') as file:
                    file_data = json.load(file)

                subs_wait_time = file_data['subs_wait_time']

                asyncio.create_task(
                    start_post_views_increasing(
                        channel_url=channel_url,
                        group_id=sub.group_id,
                        total_views=sub.full_amount,
                        cur_hour=sub.hour,
                        subs_wait_time=subs_wait_time
                    )
                )

        await asyncio.sleep(random.randrange(15, 35))


def main():
    logger.info('Запускаем программу для накрутки подписчиков...')
    try:
        asyncio.run(start_backend())
    except KeyboardInterrupt:
        logger.info(f'Программа прекратила работу.')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)
    except sqlite3.OperationalError:
        logger.info(f'Ошибка - database is locked. Пробуем перезапустить')
        time.sleep(10.5)
    except Exception as exc:
        logger.info(f'Программа прекратила работу. Ошибка - {type(exc)}')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)


if __name__ == "__main__":
    while True:
        main()
