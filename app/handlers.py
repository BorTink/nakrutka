from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

import dal
import states
import keyboards as kb
from utils import add_info_to_state, get_info_from_state

# Создание объектов бота, хранилища и диспетчера
bot = Bot('6413929628:AAEXGT4F1fDsIOonxzk700ADXQ30JoXEm70')  # Вводим сюда токен нашего бота
storage = MemoryStorage()  # Создаем хранилище в памяти для запоминания состояний
# Создаем диспетчера, через которого бот будет запускаться, вместе с утилитой для логов,
dp = Dispatcher(bot=bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(state='*', commands=['start'])
async def start(message: types.Message):
    await message.answer(
        'Здравствуйте.',
        reply_markup=kb.always
    )
    groups = await dal.Groups.get_groups_list()
    if not groups:
        await message.answer(
            'Список групп пуст. Добавьте группу для накрутки',
            reply_markup=kb.start_without_groups
        )
    else:
        text = 'Список групп для накрутки: \n'
        index = 1
        for group in groups:
            text += f'{index} | {group.name} | {group.link} \n'

        await message.answer(
            text,
            reply_markup=kb.start
        )


@dp.message_handler(state='*', text='Вернуться к списку групп')
async def back_to_group(message: types.Message):
    groups = await dal.Groups.get_groups_list()
    if not groups:
        await message.answer(
            'Список групп пуст. Добавьте группу для накрутки',
            reply_markup=kb.start_without_groups
        )
    else:
        text = 'Список групп для накрутки: \n'
        index = 1
        for group in groups:
            text += f'{index} | {group.name} | {group.link} \n'

        await message.answer(
            text,
            reply_markup=kb.start
        )


@dp.callback_query_handler(state='*', text='Добавить группу')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('Введите ссылку на группу')
    await state.set_state('Ссылка на группу')


@dp.message_handler(state='Ссылка на группу')
async def get_link(message: types.Message, state: FSMContext):
    if 'https://t.me/' not in message.text:
        await message.answer(
            'Введите корректную ссылку'
        )
    else:
        await add_info_to_state(state, 'link', message.text)

        await message.answer(
            'Введите название этой группы (не обязательно актуальное, это нужно для отображения в боте)'
        )
        await state.set_state('Название группы')


@dp.message_handler(state='Название группы')
async def get_group(message: types.Message, state: FSMContext):
    link = await get_info_from_state(state, 'link')
    await dal.Groups.add_group(
        name=message.text,
        link=link
    )
    await message.answer(
        f'Группа {message.text} была добавлена'
    )
