from telethon import TelegramClient, events
import asyncio
import requests
import numpy as np
import datetime

import dal

# Telegram API credentials
api_id = 19418891
api_hash = '9dc4be6c707b19578aa61328972af119'
client = TelegramClient('sessionTestAnton', api_id, api_hash)


def calculate_view_distribution(post_hour, total_views):
    base_distribution = np.array([
        1, 0.55, 0.4, 0.35, 0.28, 0.23, 0.18, 0.15, 0.1, 0.08, 0.1, 0.08, 0.1, 0.13, 0.16,
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

    if post_hour >= 21 or post_hour < 7:
        if post_hour < 10:
            post_hour += 24
        post_hour -= 21

        night_distribution_main[post_hour] = night_distribution[post_hour]
        night_distribution = night_distribution_main[post_hour:]
        rand = np.random.choice([0.03, 0.04, 0.05], 72 - len(night_distribution))
        full_distribution = np.concatenate((
            night_distribution,
            rand
        ))
    else:
        rand = np.random.choice([0.03, 0.04, 0.05], 72 - len(base_distribution))
        full_distribution = np.concatenate((
            base_distribution,
            rand
        ))

    full_distribution = full_distribution + np.random.uniform(low=-0.003, high=0.003, size=(72,))
    normalized_distribution = full_distribution[:72] / full_distribution[:72].sum()
    views_distribution = np.round(normalized_distribution * total_views).astype(int)
    views_distribution = np.where(views_distribution < 10, views_distribution + 10, views_distribution)

    accumulated_views = views_distribution.cumsum()
    if accumulated_views[-1] > total_views:
        last_necessary_order = np.argmax(accumulated_views >= total_views)
        views_distribution[last_necessary_order + 1:] = 0

    return views_distribution


def get_channel_name(channel_url):
    # Assuming the channel URL is in the format "https://t.me/channelname"
    # This splits the URL by '/' and returns the last part as the channel name
    return channel_url.split('/')[-1]


def send_order(channel_url, post_id, views_per_post):
    channel_name = get_channel_name(channel_url)
    # Service 1107 cannot manage requests with less than 100 views,
    # so we reroute request to a different service id
    if views_per_post > 100:
        service_id = 1107  # Update this with the correct service ID from soc-proof.su if needed
    else:
        service_id = 997

    api_key = '14b5170f4b9abff14a3a6719e05fe54e'  # Updated API key from your message
    post_link = f"{channel_url}/{post_id}"
    order_url = f"https://partner.soc-proof.su/api/v2?action=add&service={service_id}&link={post_link}&quantity={views_per_post}&key={api_key}"
    response = requests.post(order_url)  # Updated to use POST as specified in the PDF
    print(f"Order placed for {views_per_post} views for post ID {post_id} in channel '{channel_name}' at {datetime.datetime.now().time()}")
    return response.json()


async def distribute_views_over_periods(channel_url, post_id, distributions):
    first_order = True
    second_order = True
    for hour, views in enumerate(distributions):
        if not first_order and not second_order:
            # Wait for 3600 seconds (1 hour) before placing the next order
            await asyncio.sleep(3600)
        elif first_order:
            first_order = False
        else:
            # On second order wait for 3900 seconds (1 hour 5 minutes) to correct TgStats spikes
            await asyncio.sleep(3900)
            second_order = False

        do_order = await dal.Orders.get_order_by_id(order_id=post_id)

        if do_order.started == 0:
            await dal.Orders.update_started_by_id(order_id=post_id, started=1)

        while do_order.stopped == 1 and do_order.completed == 0 and do_order.order_deleted == 0:
            await asyncio.sleep(10)
            do_order = await dal.Orders.get_order_by_id(order_id=post_id)

        if do_order.completed == 1 or do_order.order_deleted == 1:
            print(f'Order with post_id = {post_id} is completed or deleted')
            break

        send_order(channel_url, post_id, views)  # Place the order
        print(f"Order for hour {hour + 1} is placed.")

        left_amount = int(do_order.left_amount) - int(views)
        await dal.Orders.update_left_amount_by_id(order_id=post_id, amount=left_amount)
        if do_order.left_amount < 0:
            await dal.Orders.update_completed_by_id(post_id, 1)
            print(f'Order with post_id = {post_id} is completed')
            break


async def setup_event_listener(channel_url, views_final, group_id):
    channel = await client.get_entity(channel_url)

    @client.on(events.NewMessage(chats=channel))
    async def handler(event):
        await dal.Orders.add_order(group_id=group_id, post_id=event.message.id, amount=views_final)
        await start_post_views_increasing(channel_url, event.message.id, views_final)


async def start_post_views_increasing(channel_url, post_id, views):
    post_time = datetime.datetime.now().astimezone().hour
    distributions = calculate_view_distribution(post_time, views)
    await distribute_views_over_periods(channel_url, post_id, distributions)


async def start_backend():
    await dal.Groups.create_db()
    await dal.Orders.create_db()
    print('Backend started')

    while True:
        groups = await dal.Groups.get_not_setup_groups_list()
        for group in groups:
            print(f'Check group - {group.name}')

            channel_url = group.link
            group_id = group.id
            views_final = group.amount

            asyncio.create_task(setup_event_listener(channel_url, views_final, group_id))
            await dal.Groups.update_setup_by_id(group_id=group_id, setup=1)

        orders = await dal.Orders.get_not_started_orders_list()
        for order in orders:
            print(f'Check order - {order.group_link}/{order.post_id}')

            channel_url = order.group_link
            views_final = order.left_amount

            asyncio.create_task(start_post_views_increasing(channel_url, order.post_id, views_final))

        await asyncio.sleep(5)


if __name__ == "__main__":
    print('Backend post views increasing programm has been started')
    with client:
        client.loop.run_until_complete(start_backend())
