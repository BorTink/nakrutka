import os
import json

from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from dotenv import load_dotenv

import dal
import app.keyboards as kb
from utils import add_info_to_state, get_info_from_state

# Создание объектов бота, хранилища и диспетчера
load_dotenv()
bot = Bot(os.getenv('TOKEN'))

storage = MemoryStorage()  # Создаем хранилище в памяти для запоминания состояний
# Создаем диспетчера, через которого бот будет запускаться, вместе с утилитой для логов,
dp = Dispatcher(bot=bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(state='*', commands=['start'])
async def start(message: types.Message, state: FSMContext):
    await message.answer(
        'Здравствуйте.',
        reply_markup=kb.always
    )

    profile = await get_info_from_state(state, 'profile')
    if not profile:
        await add_info_to_state(state, 'profile', 1)
        profile = 1

    groups = await dal.Groups.get_groups_list_by_profile(profile)
    if not groups:
        await message.answer(
            f'Профиль - {profile}. \n\nСписок групп пуст. Добавьте группу для накрутки',
            reply_markup=kb.start_without_groups
        )
    else:
        text = f'Профиль - {profile}. \n\nСписок групп для накрутки: \n'
        for group in groups:
            text += f'{group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров\n'

        await message.answer(
            text,
            reply_markup=kb.start
        )


@dp.message_handler(state='*', text='Вернуться к списку групп')
async def back_to_group(message: types.Message, state: FSMContext):
    profile = await get_info_from_state(state, 'profile')
    if not profile:
        await add_info_to_state(state, 'profile', 1)
        profile = 1

    groups = await dal.Groups.get_groups_list_by_profile(profile)
    if not groups:
        await message.answer(
            f'Профиль - {profile}. \n\nСписок групп пуст. Добавьте группу для накрутки',
            reply_markup=kb.start_without_groups
        )
    else:
        text = f'Профиль - {profile}. \n\nСписок групп для накрутки: \n'
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
    await add_info_to_state(state, 'amount', int(message.text))

    await message.answer(
        'Введите название этой группы (не обязательно актуальное, это нужно для отображения в боте)'
    )
    await state.set_state('Название группы')


@dp.message_handler(state='Название группы')
async def get_group(message: types.Message, state: FSMContext):
    link = await get_info_from_state(state, 'link')
    amount = await get_info_from_state(state, 'amount')
    profile = await get_info_from_state(state, 'profile')
    if not profile:
        await add_info_to_state(state, 'profile', 1)
        profile = 1

    await dal.Groups.add_group(
        name=message.text,
        link=link,
        amount=amount,
        profile=profile
    )
    await message.answer(
        f'Группа {message.text} была добавлена'
    )
    await state.set_state('None')

    groups = await dal.Groups.get_groups_list_by_profile(profile)
    if not groups:
        await message.answer(
            f'Профиль - {profile}. \n\nСписок групп пуст. Добавьте группу для накрутки',
            reply_markup=kb.start_without_groups
        )
    else:
        text = f'Профиль - {profile}. \n\nСписок групп для накрутки: \n'
        for group in groups:
            text += f'{group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров\n'

        await message.answer(
            text,
            reply_markup=kb.start
        )


@dp.callback_query_handler(state='*', text='Сменить профиль')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    profile = await get_info_from_state(state, 'profile')
    profile_list = await dal.Groups.get_profile_list()
    await callback.message.answer(
        f'Нынешний профиль - {profile}. Введите номер нового профиля.\n'
        f'Существующие профили \n(чтобы создать новый профиль введите новую цифру):\n\n{"; ".join(profile_list)}'
    )
    await callback.message.answer('Введите номер профиля')
    await state.set_state('Сменить профиль')


@dp.message_handler(state='Сменить профиль')
async def get_link(message: types.Message, state: FSMContext):
    if not message.text.isnumeric():
        await message.answer(
            'Введите число'
        )
    elif int(message.text) <= 0:
        await message.answer(
            'Введите число больше 0'
        )
    else:
        profile = int(message.text)
        await add_info_to_state(state, 'profile', profile)

        groups = await dal.Groups.get_groups_list_by_profile(profile)
        if not groups:
            await message.answer(
                f'Профиль - {profile}. \n\nСписок групп пуст. Добавьте группу для накрутки',
                reply_markup=kb.start_without_groups
            )
        else:
            text = f'Профиль - {profile}. \n\nСписок групп для накрутки: \n'
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
    profile = await get_info_from_state(state, 'profile')
    groups = await dal.Groups.get_groups_list_by_profile(profile)
    this_group = None
    for group in groups:
        if group.id == int(message.text):
            this_group = group
            await add_info_to_state(state, 'group_id', group.id)

            await state.set_state('В группе')
            views_stats = await dal.Groups.get_views_stats_by_group_id(group.id)
            subs_stats = await dal.Groups.get_subs_stats_by_group_id(group.id)
            await message.answer(
           f'Профиль - {group.profile}\n'
                f'Выбрана группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров | '
                f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_orders else "АКТИВНА"} | '
                f'За последний месяц накручено: \n'
                f'{views_stats} просмотров \n'
                f'{subs_stats} подписчиков',
                reply_markup=kb.group
            )
            break

    if not this_group:
        await message.answer(
            'Такого id группы в этом профиле не существует'
        )
        await state.set_state('None')

        text = f'Профиль - {profile}. \n\nСписок групп для накрутки: \n'
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


@dp.callback_query_handler(state='В группе', text='Переключить статус накрутки')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    group_id = await get_info_from_state(state, 'group_id')
    group = await dal.Groups.get_group_by_id(group_id)
    await dal.Groups.update_auto_orders_by_id(group_id=group_id, auto_orders=0 if group.auto_orders else 1)
    await dal.Groups.update_new_post_id_by_id(group_id=group_id, new_post_id=None)

    group_id = await get_info_from_state(state, 'group_id')
    group = await dal.Groups.get_group_by_id(group_id)
    views_stats = await dal.Groups.get_views_stats_by_group_id(group_id)
    subs_stats = await dal.Groups.get_subs_stats_by_group_id(group_id)

    await callback.message.answer(
        f'Профиль - {group.profile}\n'
        f'Выбрана группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров | '
        f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_orders else "АКТИВНА"} | '
        f'За последний месяц накручено: \n'
        f'{views_stats} просмотров \n'
        f'{subs_stats} подписчиков',
        reply_markup=kb.group
    )


@dp.message_handler(state='Новое значение накрутки')
async def get_link(message: types.Message, state: FSMContext):
    group_id = await get_info_from_state(state, 'group_id')
    await dal.Groups.update_amount_by_id(group_id=group_id, amount=int(message.text))
    await message.answer('Кол-во было успешно обновлено.')

    group = await dal.Groups.get_group_by_id(group_id)
    await state.set_state('В группе')
    views_stats = await dal.Groups.get_views_stats_by_group_id(group_id)
    subs_stats = await dal.Groups.get_subs_stats_by_group_id(group_id)

    await message.answer(
        f'Профиль - {group.profile}\n'
        f'Выбрана группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров | '
        f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_orders else "АКТИВНА"} | '
        f'За последний месяц накручено: \n'
        f'{views_stats} просмотров \n'
        f'{subs_stats} подписчиков',
        reply_markup=kb.group
    )


@dp.callback_query_handler(state='В группе', text='Накрутить старый пост')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        'Введите id поста для накрутки'
    )
    await state.set_state('Введите id поста для накрутки')


@dp.message_handler(state='Введите id поста для накрутки')
async def get_link(message: types.Message, state: FSMContext):
    if not message.text.isnumeric():
        await message.answer(
            'Введите число'
        )
    else:
        group_id = await get_info_from_state(state, 'group_id')
        new_post_id = int(message.text)

        orders = await dal.Orders.get_orders_list_by_group_id(group_id)
        for i in orders:
            if new_post_id == i.post_id:
                await message.answer('Для такого поста уже существует ордер')
                new_post_id = None

        if new_post_id:
            await add_info_to_state(state, 'post_id', new_post_id)
            await message.answer(
                'Введите, сколько нужно накрутить просмотров на этот пост'
            )
            await state.set_state('Старый пост - кол-во накрутки')


@dp.message_handler(state='Старый пост - кол-во накрутки')
async def get_link(message: types.Message, state: FSMContext):
    group_id = await get_info_from_state(state, 'group_id')
    post_id = await get_info_from_state(state, 'post_id')
    amount = int(message.text)

    await dal.Orders.add_order(group_id, post_id, amount, stopped=1)

    await message.answer(
        'Ордер был добавлен'
    )

    group = await dal.Groups.get_group_by_id(group_id)
    await state.set_state('В группе')
    views_stats = await dal.Groups.get_views_stats_by_group_id(group_id)
    subs_stats = await dal.Groups.get_subs_stats_by_group_id(group_id)

    await message.answer(
        f'Профиль - {group.profile}\n'
        f'Выбрана группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров | '
        f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_orders else "АКТИВНА"} | '
        f'За последний месяц накручено: \n'
        f'{views_stats} просмотров \n'
        f'{subs_stats} подписчиков',
        reply_markup=kb.group
    )


@dp.callback_query_handler(state='В группе', text='Получить список постов')
async def get_posts(callback: types.CallbackQuery, state: FSMContext):
    group_id = await get_info_from_state(state, 'group_id')
    orders = await dal.Orders.get_not_completed_orders_list_by_group_id(group_id)
    if orders:
        text = 'Список заказов: \n'
        for order in orders: # TODO: оптимизировать текст и вывод постов (если слишком много)
            text += (
                f'{order.post_id} | Всего для накрутки: {order.full_amount} | Осталось накрутить: {order.left_amount} | '
                f'Статус: {"остановлено" if order.stopped else "окончено" if order.completed else "в процессе"}\n')
        await state.set_state('В заказах')
        await callback.message.answer(
            text,
            reply_markup=kb.orders
        )
    else:
        group = await dal.Groups.get_group_by_id(group_id)
        await callback.message.answer(
            'Заказов пока нет.'
        )
        views_stats = await dal.Groups.get_views_stats_by_group_id(group_id)
        subs_stats = await dal.Groups.get_subs_stats_by_group_id(group_id)

        await callback.message.answer(
            f'Профиль - {group.profile}\n'
            f'Выбрана группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров | '
            f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_orders else "АКТИВНА"} | '
            f'За последний месяц накручено: \n'
            f'{views_stats} просмотров \n'
            f'{subs_stats} подписчиков',
            reply_markup=kb.group
        )


@dp.callback_query_handler(state='В группе', text='Отключить накрутку')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    group_id = await get_info_from_state(state, 'group_id')
    group = await dal.Groups.get_group_by_id(group_id)
    views_stats = await dal.Groups.get_views_stats_by_group_id(group_id)
    subs_stats = await dal.Groups.get_subs_stats_by_group_id(group_id)


    orders = await dal.Orders.get_not_completed_orders_list_by_group_id(group_id)
    if orders:
        for order in orders:
            await dal.Orders.update_stopped_by_id(order_id=order.id, stopped=1)

        await callback.message.answer(
            'Накрутка на все заказы была остановлена'
        )
    else:
        await callback.message.answer(
            'У этой группы нет незавершенных заказов'
        )

    await callback.message.answer(
        f'Профиль - {group.profile}\n'
        f'Выбрана группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров | '
        f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_orders else "АКТИВНА"} | '
        f'За последний месяц накручено: \n'
        f'{views_stats} просмотров \n'
        f'{subs_stats} подписчиков',
        reply_markup=kb.group
    )


@dp.callback_query_handler(state='В группе', text='Сменить профиль у группы')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    profile = await get_info_from_state(state, 'profile')
    profile_list = await dal.Groups.get_profile_list()
    await callback.message.answer(
        f'Нынешний профиль - {profile}. Введите номер нового профиля.\n'
        f'Существующие профили \n(чтобы создать новый профиль введите новую цифру):\n\n{"; ".join(profile_list)}'
    )
    await state.set_state('В группе - новый профиль')


@dp.message_handler(state='В группе - новый профиль')
async def group__new_profile(message: types.Message, state: FSMContext):
    if not message.text.isnumeric():
        await message.answer(
            'Введите число'
        )
    elif int(message.text) <= 0:
        await message.answer(
            'Введите число больше 0'
        )
    else:
        profile = int(message.text)
        await add_info_to_state(state, 'profile', profile)

        group_id = await get_info_from_state(state, 'group_id')
        await dal.Groups.update_profile_by_id(group_id, profile)

        group = await dal.Groups.get_group_by_id(group_id)
        views_stats = await dal.Groups.get_views_stats_by_group_id(group_id)
        subs_stats = await dal.Groups.get_subs_stats_by_group_id(group_id)

        await message.answer(
            f'Профиль - {group.profile}\n'
            f'Выбрана группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров | '
            f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_orders else "АКТИВНА"} | '
            f'За последний месяц накручено: \n'
            f'{views_stats} просмотров \n'
            f'{subs_stats} подписчиков',
            reply_markup=kb.group
        )


@dp.callback_query_handler(state='В группе', text='Накрутка подписчиков')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    group_id = await get_info_from_state(state, 'group_id')
    group = await dal.Groups.get_group_by_id(group_id)
    sub = await dal.Subs.get_sub_by_group_id(group_id)

    await state.set_state('В подписчиках')
    with open(f'services_{group.profile}.json', 'r') as file:
        file_data = json.load(file)

    subs_wait_time = file_data['subs_wait_time']

    if sub:
        text = (f'{"Ведется накрутка подписчиков" if not sub.stopped else "Накрутка временно приостановлена"}: \n'
                f'Необходимо накрутить - {sub.full_amount} \n'
                f'Осталось накрутить - {sub.left_amount} \n'
                f'Период накрутки - {subs_wait_time} секунд \n')
        await callback.message.answer(
            text,
            reply_markup=kb.subs_going
        )
    else:
        await callback.message.answer(
            'Накрутка подписчиков в данный момент не ведется',
            reply_markup=kb.subs_none
        )


@dp.callback_query_handler(state='В подписчиках', text=['Добавить накрутку', 'Изменить параметры накрутки'])
async def add_subs(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'Изменить параметры накрутки':
        await callback.message.answer(
            'Сейчас вам необходимо будет ввести обновленные значения для накрутки'
        )

    await callback.message.answer(
        'Введите общее кол-во подписчиков для накрутки'
    )
    await state.set_state('Новые подписчики - общее кол-во')


@dp.message_handler(state='Новые подписчики - общее кол-во')
async def get_link(message: types.Message, state: FSMContext):
    if not message.text.isnumeric():
        await message.answer(
            'Введите число'
        )
    else:
        group_id = await get_info_from_state(state, 'group_id')
        full_amount = int(message.text)

        sub = await dal.Subs.get_sub_by_group_id(group_id)
        if sub:
            await dal.Subs.update_sub_info_by_group_id(group_id, full_amount)
            await message.answer(
                'Изменения были добавлены в накрутку'
            )
        else:
            await dal.Subs.add_sub(group_id, full_amount)
            await message.answer(
                'Накрутка подписчиков была добавлена. Она уже начинается'
            )

        group = await dal.Groups.get_group_by_id(group_id)
        await state.set_state('В группе')
        views_stats = await dal.Groups.get_views_stats_by_group_id(group_id)
        subs_stats = await dal.Groups.get_subs_stats_by_group_id(group_id)

        await message.answer(
            f'Профиль - {group.profile}\n'
            f'Выбрана группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров | '
            f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_orders else "АКТИВНА"} | '
            f'За последний месяц накручено: \n'
            f'{views_stats} просмотров \n'
            f'{subs_stats} подписчиков',
            reply_markup=kb.group
        )


@dp.callback_query_handler(state='В подписчиках', text='Переключить статус подписчиков')
async def switch_subs(callback: types.CallbackQuery, state: FSMContext):
    group_id = await get_info_from_state(state, 'group_id')
    sub = await dal.Subs.get_sub_by_group_id(group_id)
    stopped = int(sub.stopped) - 1
    stopped = abs(stopped)
    await dal.Subs.update_stopped_by_group_id(group_id, stopped=stopped)

    await callback.message.answer(
        f'Накрутка подписчиков была {"приостановлена" if stopped else "включена"}.'
    )

    group = await dal.Groups.get_group_by_id(group_id)
    await state.set_state('В группе')
    views_stats = await dal.Groups.get_views_stats_by_group_id(group_id)
    subs_stats = await dal.Groups.get_subs_stats_by_group_id(group_id)

    await callback.message.answer(
        f'Профиль - {group.profile}\n'
        f'Выбрана группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров | '
        f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_orders else "АКТИВНА"} | '
        f'За последний месяц накручено: \n'
        f'{views_stats} просмотров \n'
        f'{subs_stats} подписчиков',
        reply_markup=kb.group
    )


@dp.callback_query_handler(
    state=['В заказах', 'В подписчиках', 'В реакциях', 'В ордерах реакций'], text='Вернуться к группе'
)
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state('В группе')
    group_id = await get_info_from_state(state, 'group_id')
    group = await dal.Groups.get_group_by_id(group_id)

    views_stats = await dal.Groups.get_views_stats_by_group_id(group_id)
    subs_stats = await dal.Groups.get_subs_stats_by_group_id(group_id)

    await callback.message.answer(
        f'Профиль - {group.profile}\n'
        f'Выбрана группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров | '
        f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_orders else "АКТИВНА"} | '
        f'За последний месяц накручено: \n'
        f'{views_stats} просмотров \n'
        f'{subs_stats} подписчиков',
        reply_markup=kb.group
    )


@dp.callback_query_handler(state='В заказах', text=['Отключить накрутку в заказе', 'Включить обратно накрутку в заказе'])
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'Отключить накрутку в заказе':
        await add_info_to_state(state, 'stopped', 1)
    elif callback.data == 'Включить обратно накрутку в заказе':
        await add_info_to_state(state, 'stopped', 0)

    await callback.message.answer(
        'Введите id поста'
    )
    await state.set_state('Введите id поста')


@dp.message_handler(state='Введите id поста')
async def get_link(message: types.Message, state: FSMContext):
    if not message.text.isnumeric():
        await message.answer(
            'Введите число'
        )
    else:
        post_id = int(message.text)
        group_id = await get_info_from_state(state, 'group_id')

        group = await dal.Groups.get_group_by_id(group_id)
        this_order = await dal.Orders.get_order_by_group_and_post(group_id=group_id, post_id=post_id)

        if not this_order:
            await message.answer(
                'Такого заказа не существует'
            )

            await state.set_state('В группе')
            views_stats = await dal.Groups.get_views_stats_by_group_id(group_id)
            subs_stats = await dal.Groups.get_subs_stats_by_group_id(group_id)

            await message.answer(
                f'Профиль - {group.profile}\n'
                f'Выбрана группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров | '
                f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_orders else "АКТИВНА"} | '
                f'За последний месяц накручено: \n'
                f'{views_stats} просмотров \n'
                f'{subs_stats} подписчиков',
                reply_markup=kb.group
            )

        else:
            stopped = await get_info_from_state(state, 'stopped')
            await dal.Orders.update_stopped_by_id(order_id=this_order.id, stopped=stopped)
            text = f'Заказ c post_id = {post_id} был '
            text += 'возобновлен' if stopped == 0 else 'остановлен'
            await message.answer(
                text
            )

            await state.set_state('В группе')
            views_stats = await dal.Groups.get_views_stats_by_group_id(group_id)
            subs_stats = await dal.Groups.get_subs_stats_by_group_id(group_id)

            await message.answer(
                f'Профиль - {group.profile}\n'
                f'Выбрана группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.amount} просмотров | '
                f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_orders else "АКТИВНА"} | '
                f'За последний месяц накручено: \n'
                f'{views_stats} просмотров \n'
                f'{subs_stats} подписчиков',
                reply_markup=kb.group
            )


@dp.callback_query_handler(state='В группе', text='Перейти к реакциям')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    group_id = await get_info_from_state(state, 'group_id')
    group = await dal.Groups.get_group_by_id(group_id)

    await state.set_state('В реакциях')

    await callback.message.answer(
        f'Накрутка РЕАКЦИЙ в группе группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.reactions_amount} реакций | '
        f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_reactions else "АКТИВНА"} | ',
        reply_markup=kb.reactions
    )


@dp.callback_query_handler(state='В реакциях', text='Поменять просмотры')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    group_id = await get_info_from_state(state, 'group_id')
    group = await dal.Groups.get_group_by_id(group_id)
    await callback.message.answer(
        f'Сейчас в группе автоматически накручивается - {group.reactions_amount} реакций. \n'
        f'Введите новое значение'
    )
    await state.set_state('Реакции - Новое значение накрутки')


@dp.message_handler(state='Реакции - Новое значение накрутки')
async def get_link(message: types.Message, state: FSMContext):
    group_id = await get_info_from_state(state, 'group_id')
    await dal.Groups.update_reactions_amount_by_id(group_id=group_id, reactions_amount=int(message.text))
    await message.answer('Кол-во было успешно обновлено.')

    group = await dal.Groups.get_group_by_id(group_id)
    await state.set_state('В реакциях')

    await message.answer(
        f'Накрутка РЕАКЦИЙ в группе группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.reactions_amount} реакций | '
        f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_reactions else "АКТИВНА"} | ',
        reply_markup=kb.reactions
    )


@dp.callback_query_handler(state='В реакциях', text='Получить список реакций')
async def get_posts(callback: types.CallbackQuery, state: FSMContext):
    group_id = await get_info_from_state(state, 'group_id')
    reactions = await dal.Reactions.get_not_completed_reactions_list_by_group_id(group_id)
    if reactions:
        text = 'Список ордеров реакций: \n'
        for reaction in reactions: # TODO: оптимизировать текст и вывод постов (если слишком много)
            text += (
                f'{reaction.post_id} | Всего для накрутки: {reaction.full_amount} | Осталось накрутить: {reaction.left_amount} | '
                f'Статус: {"остановлено" if reaction.stopped else "окончено" if reaction.completed else "в процессе"}\n')
        await state.set_state('В ордерах реакций')
        await callback.message.answer(
            text,
            reply_markup=kb.reactions_orders
        )
    else:
        group = await dal.Groups.get_group_by_id(group_id)
        await callback.message.answer(
            'Ордеров реакций пока нет.'
        )

        await callback.message.answer(
            f'Накрутка РЕАКЦИЙ в группе группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.reactions_amount} реакций | '
            f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_reactions else "АКТИВНА"} | ',
            reply_markup=kb.reactions
        )


@dp.callback_query_handler(state='В реакциях', text='Реакции - старый пост')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        'Введите id поста для накрутки'
    )
    await state.set_state('Реакции - Введите id поста для накрутки')


@dp.message_handler(state='Реакции - Введите id поста для накрутки')
async def get_link(message: types.Message, state: FSMContext):
    if not message.text.isnumeric():
        await message.answer(
            'Введите число'
        )
    elif int(message.text) <= 0:
        await message.answer(
            'Введите число больше 0'
        )
    else:
        group_id = await get_info_from_state(state, 'group_id')
        new_post_id = int(message.text)

        reactions = await dal.Reactions.get_reactions_list_by_group_id(group_id)
        for i in reactions:
            if new_post_id == i.post_id:
                await message.answer('Для такого поста уже существует ордер')
                new_post_id = None

        if new_post_id:
            await add_info_to_state(state, 'post_id', new_post_id)
            await message.answer(
                'Введите, сколько нужно накрутить реакций на этот пост'
            )
            await state.set_state('Реакции - Старый пост кол-во')


@dp.message_handler(state='Реакции - Старый пост кол-во')
async def get_link(message: types.Message, state: FSMContext):
    group_id = await get_info_from_state(state, 'group_id')
    post_id = await get_info_from_state(state, 'post_id')
    amount = int(message.text)

    await dal.Reactions.add_reaction(group_id, post_id, amount, stopped=1)

    await message.answer(
        'Ордер был добавлен'
    )

    group = await dal.Groups.get_group_by_id(group_id)
    await state.set_state('В реакциях')

    await message.answer(
        f'Накрутка РЕАКЦИЙ в группе группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.reactions_amount} реакций | '
        f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_reactions else "АКТИВНА"} | ',
        reply_markup=kb.reactions
    )


@dp.callback_query_handler(state='В реакциях', text='Реакции - переключить статус')
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    group_id = await get_info_from_state(state, 'group_id')
    group = await dal.Groups.get_group_by_id(group_id)
    await dal.Groups.update_auto_reactions_by_id(group_id=group_id, auto_reactions=0 if group.auto_reactions else 1)

    group_id = await get_info_from_state(state, 'group_id')
    group = await dal.Groups.get_group_by_id(group_id)

    await callback.message.answer(
        f'Накрутка РЕАКЦИЙ в группе группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.reactions_amount} реакций | '
        f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_reactions else "АКТИВНА"} | ',
        reply_markup=kb.reactions
    )


@dp.callback_query_handler(state='В ордерах реакций', text=['Реакции - отключить заказ', 'Реакции - включить заказ'])
async def add_group(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'Реакции - отключить заказ':
        await add_info_to_state(state, 'stopped', 1)
    elif callback.data == 'Реакции - включить заказ':
        await add_info_to_state(state, 'stopped', 0)

    await callback.message.answer(
        'Введите id поста'
    )
    await state.set_state('Реакции - Введите id поста')


@dp.message_handler(state='Реакции - Введите id поста')
async def get_post_id_reactions(message: types.Message, state: FSMContext):
    if not message.text.isnumeric():
        await message.answer(
            'Введите число'
        )
    else:
        post_id = int(message.text)
        group_id = await get_info_from_state(state, 'group_id')

        group = await dal.Groups.get_group_by_id(group_id)
        this_order = await dal.Reactions.get_reaction_by_group_and_post(group_id=group_id, post_id=post_id)

        if not this_order:
            await message.answer(
                'Такого заказа на реакции не существует'
            )

            await state.set_state('В реакциях')

            await message.answer(
                f'Накрутка РЕАКЦИЙ в группе группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.reactions_amount} реакций | '
                f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_reactions else "АКТИВНА"} | ',
                reply_markup=kb.reactions
            )

        else:
            stopped = await get_info_from_state(state, 'stopped')
            await dal.Reactions.update_stopped_by_id(reaction_id=this_order.id, stopped=stopped)
            text = f'Заказ на реакции c post_id = {post_id} был '
            text += 'возобновлен' if stopped == 0 else 'остановлен'
            await message.answer(
                text
            )

            await state.set_state('В реакциях')

            await message.answer(
                f'Накрутка РЕАКЦИЙ в группе группа - {group.id} | {group.name} | {group.link} | Новый пост - {group.reactions_amount} реакций | '
                f'Статус - {"ПРИОСТАНОВЛЕНА" if not group.auto_reactions else "АКТИВНА"} | ',
                reply_markup=kb.reactions
            )
