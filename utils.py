import random
import os
import json


async def add_info_to_state(state, key, value):
    async with state.proxy() as data:
        data[key] = value


async def get_info_from_state(state, key):
    async with state.proxy() as data:
        return data.get(key, None)


def generate_random_list(total_sum, n):
    min_value = total_sum / (n * 2)
    numbers = [random.uniform(min_value, total_sum / n) for _ in range(n)]

    # Normalize the sum to match the total_sum
    sum_numbers = sum(numbers)
    normalized_numbers = [num * (total_sum / sum_numbers) for num in numbers]

    return normalized_numbers


async def create_services_file_if_not_exists(profile):
    services_path = os.path.dirname(os.path.abspath(__file__)) + f'/services/services_{profile}.json'

    if not os.path.exists(services_path):
        with open(f'services/services_1.json', 'r') as file:
            file_data = json.load(file)

        with open(services_path, 'w') as new_file:
            json.dump(file_data, new_file, ensure_ascii=False)
