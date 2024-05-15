from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

import dal
import app.keyboards as kb
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
        for group in groups:
            text += f'{group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров\n'

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
        for group in groups:
            text += f'{group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров\n'

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
            'Введите кол-во накручиваемых просмотров на каждый новый пост \n'
            '(эти данные сохранятся, но накрутка будет временно выключена. Включить ее можно будет в меню)'
        )
        await state.set_state('Кол-во накрутки')


@dp.message_handler(state='Кол-во накрутки')
async def get_link(message: types.Message, state: FSMContext):
    if not message.text.isnumeric():
        await message.answer(
            'Введите число'
        )
    else:
        await add_info_to_state(state, 'amount', int(message.text))

        await message.answer(
            'Введите название этой группы (не обязательно актуальное, это нужно для отображения в боте)'
        )
        await state.set_state('Название группы')


@dp.message_handler(state='Название группы')
async def get_group(message: types.Message, state: FSMContext):
    link = await get_info_from_state(state, 'link')
    amount = await get_info_from_state(state, 'amount')
    await dal.Groups.add_group(
        name=message.text,
        link=link,
        amount=amount
    )
    await message.answer(
        f'Группа {message.text} была добавлена'
    )
    await state.set_state('None')

    groups = await dal.Groups.get_groups_list()
    if not groups:
        await message.answer(
            'Список групп пуст. Добавьте группу для накрутки',
            reply_markup=kb.start_without_groups
        )
    else:
        text = 'Список групп для накрутки: \n'
        for group in groups:
            text += f'{group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров\n'

        await message.answer(
            text,
            reply_markup=kb.start
        )


@dp.callback_query_handler(state='*', text='Посмотреть посты у группы')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        'Введите id группы для просмотра ее постов'
    )
    await state.set_state('Введите id группы')


@dp.message_handler(state='Введите id группы')
async def get_link(message: types.Message, state: FSMContext):
    groups = await dal.Groups.get_groups_list()
    this_group = None
    for group in groups:
        if group.id == int(message.text):
            this_group = group
            await add_info_to_state(state, 'group_id', group.id)

            await state.set_state('В группе')
            await message.answer(
                f'Выбрана группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров',
                reply_markup=kb.group
            )
            break

    if not this_group:
        await message.answer(
            'Такого id группы не существует'
        )
        await state.set_state('None')

        text = 'Список групп для накрутки: \n'
        for group in groups:
            text += f'{group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров\n'

        await message.answer(
            text,
            reply_markup=kb.start
        )

#  ------------- ВНУТРИ ГРУППЫ -------------------------


@dp.callback_query_handler(state='В группе', text='Поменять просмотры')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    group_id = await get_info_from_state(state, 'group_id')
    group = await dal.Groups.get_group_by_id(group_id)
    await callback.message.answer(
        f'Сейчас в группе автоматически накручивается - {group.amount} просмотров. \n'
        f'Введите новое значение'
    )
    await state.set_state('Новое значение накрутки')


@dp.message_handler(state='Новое значение накрутки')
async def get_link(message: types.Message, state: FSMContext):
    if not message.text.isnumeric():
        await message.answer(
            'Введите число'
        )
    else:
        group_id = await get_info_from_state(state, 'group_id')
        await dal.Groups.update_amount_by_id(int(message.text), group_id)
        await message.answer('Кол-во было успешно обновлено.')

        group = await dal.Groups.get_group_by_id(group_id)
        await state.set_state('В группе')
        await message.answer(
            f'Выбрана группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров',
            reply_markup=kb.group
        )


@dp.callback_query_handler(state='В группе', text='Получить список постов')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        'Введите id группы для просмотра ее постов'
    )
    await state.set_state('Введите id группы')


@dp.callback_query_handler(state='В группе', text='Накрутить старый пост')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        'Введите id группы для просмотра ее постов'
    )
    await state.set_state('Введите id группы')
