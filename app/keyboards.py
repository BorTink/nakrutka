from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

always = ReplyKeyboardMarkup(resize_keyboard=True)
always_1 = KeyboardButton('Вернуться к списку групп')
always.add(always_1)

start = InlineKeyboardMarkup()
start_1 = InlineKeyboardButton(
    'Добавить группу', callback_data='Добавить группу'
)
start_2 = InlineKeyboardButton(
    'Посмотреть посты у группы', callback_data='Посмотреть посты у группы'
)
start.add(start_1).add(start_2)

start_without_groups = InlineKeyboardMarkup()
start_without_groups.add(start_1)

group = InlineKeyboardMarkup()
group_1 = InlineKeyboardButton(
    'Поменять кол-во просмотров на новые накрутки', callback_data='Поменять просмотры'
)
group_2 = InlineKeyboardButton(
    'Получить список постов', callback_data='Получить список постов'
)
group_3 = InlineKeyboardButton(
    'Добавить накрутку на старый пост', callback_data='Накрутить старый пост'
)
group.add(group_1).add(group_2).add(group_3)


orders = InlineKeyboardMarkup()
orders_1 = InlineKeyboardButton(
    'Отключить накрутку в заказе', callback_data='Отключить накрутку в заказе'
)
orders_2 = InlineKeyboardButton(
    'Включить обратно накрутку в заказе', callback_data='Включить обратно накрутку в заказе'
)
orders.add(orders_1).add(orders_2)