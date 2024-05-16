import asyncio
from telethon import TelegramClient, events
import requests
import numpy as np
import datetime

# Telegram API credentials
api_id = 19418891
api_hash = '9dc4be6c707b19578aa61328972af119'
client = TelegramClient('sessionTestAnton', api_id, api_hash)


def calculate_view_distribution(post_hour, total_views):
    # Define the base distribution for a 72-hour period
    base_distribution = np.array([
        0.180, 0.134, 0.097, 0.084, 0.064, 0.047, 0.023, 0.016, 0.008, 0.007,
        0.008, 0.007, 0.008, 0.012, 0.016, 0.016, 0.013, 0.012, 0.012, 0.004,
        0.008, 0.004, 0.004, 0.004])

    # Early morning distribution from 00:00 to 05:59
    night_distribution = np.array([
         0.8, 0.7, 0.5, 0.4, 0.4, 0.3, 0.3, 0.3, 0.15, 0.4,
         0.8, 1, 0.8, 0.9, 0.65, 0.5, 0.45, 0.14, 0.11, 0.08, 0.2, 0.05,
         0.04, 0.04])
    night_distribution_main = np.array([
        0.8, 0.7, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.15, 0.4,
        0.8, 1, 0.8, 0.9, 0.65, 0.5, 0.45, 0.14, 0.11, 0.08, 0.2, 0.05,
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
        views_per_post = round(views_per_post/0.4)  # Изменяем кол-во постов, т.к. 60% недолив на этой услуге
        service_id = 362

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

        send_order(channel_url, post_id, views)  # Place the order
        print(f"Order for hour {hour + 1} is placed.")


async def setup_event_listener(channel_url, views_final):
    channel = await client.get_entity(channel_url)

    @client.on(events.NewMessage(chats=channel))
    async def handler(event):
        post_time = event.message.date.astimezone().hour
        distributions = calculate_view_distribution(post_time, views_final)
        await distribute_views_over_periods(channel_url, event.message.id, distributions)


async def main():
    try:
        with open('Client.txt', 'r') as file:
            lines = file.readlines()
            channel_url = lines[0].strip()
            views_final = int(lines[1].strip())
    except Exception as e:
        print(f"Failed to read 'Client.txt': {e}")
        return

    await client.start()
    await setup_event_listener(channel_url, views_final)
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
