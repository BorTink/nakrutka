import datetime
import sys
import os
import json
import time
import random
import math

from loguru import logger
import asyncio
import requests
import numpy as np
import sqlite3

from utils import generate_random_list
import dal

first_hour_wait = 3600


async def calculate_view_distribution(post_hour, total_reactions_count, cur_hour):
    base_distribution = np.array([
        0.25, 0.2, 0.18, 0.15, 0.12, 0.1, 0.55, 0.4, 0.35, 0.28, 0.23, 0.18, 0.15, 0.1, 0.08, 0.1, 0.08, 0.1, 0.13, 0.16,
        0.13, 0.11, 0.09, 0.06, 0.08, 0.06, 0.05, 0.04, 0.04])

    if True:
        rand = np.random.choice([0.03, 0.04, 0.05], 77 - len(base_distribution))
        full_distribution = np.concatenate((
            base_distribution,
            rand
        ))

    full_distribution = full_distribution + np.random.uniform(low=-0.003, high=0.003, size=(77,))
    normalized_distribution = full_distribution[:77] / full_distribution[:77].sum()
    reactions_count_distribution = np.round(normalized_distribution * total_reactions_count).astype(int)
    reactions_count_distribution = np.where(reactions_count_distribution < 10, reactions_count_distribution + 10, reactions_count_distribution)

    np_and = np.logical_and(reactions_count_distribution >= 85, reactions_count_distribution < 100)
    reactions_count_distribution = np.where(np_and, reactions_count_distribution + 15, reactions_count_distribution)

    accumulated_reactions_count = reactions_count_distribution.cumsum()
    if accumulated_reactions_count[-1] > total_reactions_count:
        last_necessary_reaction = np.argmax(accumulated_reactions_count >= total_reactions_count)
        reactions_count_distribution = reactions_count_distribution[:last_necessary_reaction + 1]

    return reactions_count_distribution[cur_hour:]


async def get_channel_name(channel_url):
    # Assuming the channel URL is in the format "https://t.me/channelname"
    # This splits the URL by '/' and returns the last part as the channel name
    return channel_url.split('/')[-1]


async def send_reaction(channel_url, post_id, reactions_count):
    channel_name = await get_channel_name(channel_url)
    # Service 1107 cannot manage requests with less than 100 reactions_count,
    # so we reroute request to a different service id
    with open('services.json', 'r') as file:
        file_data = json.load(file)

    service_ids = file_data['reactions_service_ids']
    api_key = file_data['reactions_api_key']
    service_url = file_data['reactions_url']
    post_link = f"{channel_url}/{post_id}"

    response_json = None
    reactions_spread_list = generate_random_list(reactions_count, len(service_ids))
    for i in range(len(service_ids)):
        cur_count = math.ceil(reactions_spread_list[i])
        if cur_count < 10:
            cur_count += 10
        reaction_url = f"{service_url}/api/v2?action=add&service={service_ids[i]}&link={post_link}&quantity={cur_count}&key={api_key}"
        response = requests.post(reaction_url)  # Updated to use POST as specified in the PDF
        response_json = response.json()

    logger.info(f"Order for reactions placed for {reactions_count} reactions for post ID {post_id} in channel '{channel_name}' at {datetime.datetime.now().time()}")
    return response_json


async def distribute_reactions_count_over_periods(channel_url, reaction_id, distributions, hour):
    if distributions.size == 0:
        await dal.Reactions.update_completed_by_id(reaction_id=reaction_id, completed=1)
        logger.info(f'Ордер на реакции с id = {reaction_id} был завершен раньше времени')
        await dal.Reactions.update_left_amount_by_id(reaction_id=reaction_id, amount=0)

    for reactions_count in distributions:
        do_reaction = await dal.Reactions.get_reaction_by_id(reaction_id=reaction_id)

        if do_reaction.started == 0:
            await dal.Reactions.update_started_by_id(reaction_id=reaction_id, started=1)

        if do_reaction.stopped == 1 and do_reaction.completed == 0 and do_reaction.reaction_deleted == 0:
            logger.info(f'Ордер на реакции с id = {reaction_id} был остановлен')
            break

        if do_reaction.completed == 1 or do_reaction.reaction_deleted == 1:
            logger.info(f'Ордер на реакции с id = {reaction_id} был завершен или удален')
            break

        await dal.Reactions.update_hour_by_id(reaction_id=reaction_id, hour=hour + 1)

        await send_reaction(channel_url, do_reaction.post_id, reactions_count)
        if hour <= 6:
            logger.info(f"Накрутка на 1 час была создана - {hour} отрезок ({hour * 10 - 10} минут).")
        else:
            logger.info(f"Накрутка на {hour - 5} час была создана.")

        left_amount = int(do_reaction.left_amount) - int(reactions_count)
        await dal.Reactions.update_left_amount_by_id(reaction_id=reaction_id, amount=left_amount)
        if left_amount <= 0:
            await dal.Reactions.update_completed_by_id(reaction_id=reaction_id, completed=1)
            logger.info(f'Ордер на реакции с id = {reaction_id} был завершен')
            break

        hour += 1

        if hour < 6:
            await asyncio.sleep(first_hour_wait / 6)
        elif hour == 6:
            await asyncio.sleep(first_hour_wait / 6 + 120)
        else:
            await asyncio.sleep(first_hour_wait)


async def start_post_reactions_increasing(channel_url, reaction_id, reactions_count, cur_hour, post_time):
    post_time = post_time.astimezone().hour
    distributions = await calculate_view_distribution(post_time, reactions_count, cur_hour)
    await distribute_reactions_count_over_periods(channel_url, reaction_id, distributions, hour=cur_hour)


async def start_backend():
    await dal.Groups.create_db()
    await dal.Reactions.create_db()
    logger.info('Программа для накрутки реакций была запущена')

    while True:
        reactions = await dal.Reactions.get_reactions_list()
        for reaction in reactions:
            if reaction.hour > 71:
                await dal.Reactions.update_completed_by_id(reaction_id=reaction.id, completed=1)

            elif any([
                reaction.started == 0,
                reaction.completed == 0 and reaction.stopped == 0 and
                (
                    reaction.hour < 6 and
                    (datetime.datetime.utcnow() - reaction.last_update) > datetime.timedelta(
                    seconds=first_hour_wait + 20)
                    or
                    reaction.hour >= 6 and
                    (datetime.datetime.utcnow() - reaction.last_update) > datetime.timedelta(
                    seconds=first_hour_wait + 20)
                )
            ]):
                logger.info(f'Совершается ордер на реакции - {reaction.group_link}/{reaction.post_id}')
                channel_url = reaction.group_link
                reactions_count_final = reaction.full_amount

                asyncio.create_task(
                    start_post_reactions_increasing(
                        channel_url, reaction.id, reactions_count_final, reaction.hour, reaction.created_date
                    )
                )

        await asyncio.sleep(random.randrange(15, 35))


def drop_group_setups():
    asyncio.run(dal.Groups.drop_setups())


def main():
    logger.info('Запускаем программу для накрутки реакций...')
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
