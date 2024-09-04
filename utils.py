import random


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
