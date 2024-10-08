import datetime
import sys
import os
import json
import time
import random

from loguru import logger
import asyncio
import requests
import numpy as np
import sqlite3

import dal
from auth import first_hour_wait


async def calculate_view_distribution(post_hour, total_views, cur_hour):
    # Первые 6 свечек - это 10-и минутки в первый час. Остальное - все прочие часы.
    base_distribution = np.array([
        0.25, 0.2, 0.18, 0.15, 0.12, 0.1, 0.55, 0.4, 0.35, 0.28, 0.23, 0.18, 0.15, 0.1, 0.08, 0.1, 0.08, 0.1, 0.13, 0.16,
        0.13, 0.11, 0.09, 0.06, 0.08, 0.06, 0.05, 0.04, 0.04])

    # Night - early morning distribution from 21:00 to 06:59
    night_distribution = np.array([
        0.65, 0.5, 0.45, 0.4, 0.35, 0.3, 0.2, 0.15, 0.2, 0.4,
        0.7, 0.9, 0.7, 0.6, 0.55, 0.45, 0.33, 0.14, 0.11, 0.08, 0.2, 0.05,
        0.04, 0.04])
    night_distribution_main = np.array([
        0.65, 0.5, 0.3, 0.25, 0.2, 0.18, 0.15, 0.12, 0.2, 0.4,
        0.7, 0.9, 0.7, 0.6, 0.5, 0.4, 0.3, 0.15, 0.11, 0.1, 0.2, 0.05,
        0.04, 0.04])

    # ВРЕМЕННО ВЫКЛЮЧИЛИ НОЧНУЮ ДИСТРИБУЦИЮ
    # if post_hour >= 21 or post_hour < 7:
    #     if post_hour < 10:
    #         post_hour += 24
    #     post_hour -= 21
    #
    #     night_distribution_main[post_hour] = night_distribution[post_hour]
    #     night_distribution = night_distribution_main[post_hour:]
    #     rand = np.random.choice([0.03, 0.04, 0.05], 77 - len(night_distribution))
    #     full_distribution = np.concatenate((
    #         night_distribution,
    #         rand
    #     ))
    # else:
    if True:
        rand = np.random.choice([0.03, 0.04, 0.05], 77 - len(base_distribution))
        full_distribution = np.concatenate((
            base_distribution,
            rand
        ))

    full_distribution = full_distribution + np.random.uniform(low=-0.003, high=0.003, size=(77,))
    normalized_distribution = full_distribution[:77] / full_distribution[:77].sum()
    views_distribution = np.round(normalized_distribution * total_views).astype(int)
    views_distribution = np.where(views_distribution < 24, np.random.randint(low=24, high=31), views_distribution)

    np_and = np.logical_and(views_distribution >= 85, views_distribution < 100)
    views_distribution = np.where(np_and, views_distribution + 15, views_distribution)

    accumulated_views = views_distribution.cumsum()
    if accumulated_views[-1] > total_views:
        last_necessary_order = np.argmax(accumulated_views >= total_views)
        views_distribution = views_distribution[:last_necessary_order + 1]

    return views_distribution[cur_hour:]


async def get_channel_name(channel_url):
    # Assuming the channel URL is in the format "https://t.me/channelname"
    # This splits the URL by '/' and returns the last part as the channel name
    return channel_url.split('/')[-1]


async def send_order(channel_url, post_id, order_views, left_amount, full_amount, profile):
    channel_name = await get_channel_name(channel_url)
    # Service 1107 cannot manage requests with less than 100 views,
    # so we reroute request to a different service id
    with open(f'services/services_{profile}.json', 'r') as file:
        file_data = json.load(file)

    if order_views > 200:
        service_id = file_data['service_id_higher_than_200']
        api_key = file_data['api_key_higher_than_200']
        service_url = file_data['url_higher_than_200']

    elif 100 <= order_views <= 200:
        service_id = file_data['service_id_100_200']
        api_key = file_data['api_key_100_200']
        service_url = file_data['url_100_200']

    else:
        service_id = file_data['service_id_lower_than_100']
        api_key = file_data['api_key_lower_than_100']
        service_url = file_data['url_lower_than_100']

    post_link = f"{channel_url}/{post_id}"
    order_url = f"{service_url}/api/v2?action=add&service={service_id}&link={post_link}&quantity={order_views}&key={api_key}"
    response = requests.post(order_url)  # Updated to use POST as specified in the PDF
    response_json = response.json()
    if not response_json.get('order', None):
        logger.error(f"Произошла ошибка при создании ордера на {order_views} просмотров на пост с ID {post_id} "
                     f"в канале '{channel_name}' - {response_json}")
        return None

    logger.info(f"Ордер на {order_views} для поста с ID {post_id} в канале {channel_name} был создан - {response_json}")
    return response_json


async def distribute_views_over_periods(channel_url, order_id, distributions, hour):
    if distributions.size == 0:
        await dal.Orders.update_completed_by_id(order_id=order_id, completed=1)
        logger.info(f'Ордер с order_id = {order_id} был завершен раньше времени')
        await dal.Orders.update_left_amount_by_id(order_id=order_id, amount=0)

    for views in distributions:
        do_order = await dal.Orders.get_order_by_id(order_id=order_id)

        if do_order.started == 0:
            await dal.Orders.update_started_by_id(order_id=order_id, started=1)

        if do_order.stopped == 1 and do_order.completed == 0 and do_order.order_deleted == 0:
            logger.info(f'Ордер с order_id = {order_id} был остановлен')
            break

        if do_order.completed == 1 or do_order.order_deleted == 1:
            logger.info(f'Ордер с order_id = {order_id} был завершен или удален')
            break

        await dal.Orders.update_hour_by_id(order_id=order_id, hour=hour + 1)
        hour += 1

        profile = await dal.Groups.get_group_profile_by_id(do_order.group_id)
        await send_order(channel_url, do_order.post_id, views, do_order.left_amount, do_order.full_amount, profile)
        if hour <= 6:
            logger.info(f"Накрутка на 1 час была создана - {hour} отрезок ({hour * 10 - 10} минут).")
        else:
            logger.info(f"Накрутка на {hour - 5} час была создана.")

        left_amount = int(do_order.left_amount) - int(views)
        await dal.Orders.update_left_amount_by_id(order_id=order_id, amount=left_amount)
        if left_amount <= 0:
            await dal.Orders.update_completed_by_id(order_id=order_id, completed=1)
            logger.info(f'Ордер с order_id = {order_id} был завершен')
            break

        if hour < 6:
            await asyncio.sleep(first_hour_wait // 6)
        elif hour == 6:
            await asyncio.sleep(first_hour_wait // 6 + 120)
        else:
            await asyncio.sleep(first_hour_wait)


async def start_post_views_increasing(channel_url, order_id, views, cur_hour, post_time):
    post_time = post_time.astimezone().hour
    distributions = await calculate_view_distribution(post_time, views, cur_hour)
    await distribute_views_over_periods(channel_url, order_id, distributions, hour=cur_hour)


async def start_backend():
    await dal.Groups.create_db()
    await dal.Orders.create_db()
    logger.info('Программа для накрутки просмотров была запущена')

    while True:
        orders = await dal.Orders.get_orders_list()
        for order in orders:
            if order.hour > 71:
                await dal.Orders.update_completed_by_id(order_id=order.id, completed=1)

            elif any([
                order.started == 0,
                order.completed == 0 and order.stopped == 0 and
                (
                    order.hour < 6 and
                    (datetime.datetime.utcnow() - order.last_update) > datetime.timedelta(seconds=first_hour_wait // 6 + 20)
                    or
                    order.hour >= 6 and
                    (datetime.datetime.utcnow() - order.last_update) > datetime.timedelta(
                    seconds=first_hour_wait + 20)
                )
            ]):
                logger.info(f'Совершается ордер - {order.group_link}/{order.post_id}')
                channel_url = order.group_link
                views_final = order.full_amount

                asyncio.create_task(
                    start_post_views_increasing(
                        channel_url, order.id, views_final, order.hour, order.created_date
                    )
                )

        await asyncio.sleep(random.randrange(15, 35))


def drop_group_setups():
    asyncio.run(dal.Groups.drop_setups())


def main():
    logger.info('Запускаем программу для накрутки просмотров...')
    try:
        asyncio.run(start_backend())
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
        pass
    except Exception as exc:
        logger.info(f'Программа прекратила работу. Ошибка - {exc}')
        drop_group_setups()
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)


if __name__ == "__main__":
    while True:
        main()
