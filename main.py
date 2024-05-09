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
        0.256, 0.124, 0.078, 0.070, 0.054, 0.047, 0.023, 0.016, 0.008, 0.007,
        0.008, 0.007, 0.008, 0.012, 0.016, 0.016, 0.013, 0.012, 0.012, 0.004,
        0.008, 0.004, 0.004, 0.004] + [0.004]*48)

    # Early morning distribution from 00:00 to 05:59
    early_morning_distribution = np.array([0.04, 0.03, 0.01, 0.01, 0.01, 0.03])

    if 0 <= post_hour < 6:
        early_distribution = early_morning_distribution[post_hour:]
        full_distribution = np.concatenate((early_distribution, base_distribution[:72 - len(early_distribution)]))
    else:
        full_distribution = base_distribution

    normalized_distribution = full_distribution[:72] / full_distribution[:72].sum()
    views_distribution = np.round(normalized_distribution * total_views).astype(int)
    views_distribution = np.where(views_distribution < 10, 11, views_distribution)

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
    service_id = 1107  # Update this with the correct service ID from soc-proof.su if needed
    api_key = '14b5170f4b9abff14a3a6719e05fe54e'  # Updated API key from your message
    post_link = f"{channel_url}/{post_id}"
    order_url = f"https://partner.soc-proof.su/api/v2?action=add&service={service_id}&link={post_link}&quantity={views_per_post}&key={api_key}"
    response = requests.post(order_url)  # Updated to use POST as specified in the PDF
    print(f"Order placed for {views_per_post} views for post ID {post_id} in channel '{channel_name}' at {datetime.datetime.now().time()}")
    return response.json()


async def distribute_views_over_periods(channel_url, post_id, distributions):
    first_order = True
    for hour, views in enumerate(distributions):
        if not first_order:
            # Wait for 3600 seconds (1 hour) before placing the next order
            await asyncio.sleep(3600)
        else:
            first_order = False  # The first order is handled immediately, no wait
        send_order(channel_url, post_id, views + 5)  # Place the order, always add 5 extra views
        print(f"Order for hour {hour} placed immediately if first, else after delay.")


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
