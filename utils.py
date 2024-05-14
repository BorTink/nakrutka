async def add_info_to_state(state, key, value):
    async with state.proxy as data:
        data[key] = value


async def get_info_from_state(state, key):
    async with state.proxy as data:
        return data[key]
