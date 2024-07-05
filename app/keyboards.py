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
# 1
group = InlineKeyboardMarkup()
group_1 = InlineKeyboardButton(
    'Поменять кол-во просмотров на новые посты', callback_data='Поменять просмотры'
)
group_2 = InlineKeyboardButton(
    'Получить список постов', callback_data='Получить список постов'
)
group_3 = InlineKeyboardButton(
    'Добавить накрутку на старый пост', callback_data='Накрутить старый пост'
)
group_4 = InlineKeyboardButton(
    'Переключить статус накрутки', callback_data='Переключить статус накрутки'
)
group_5 = InlineKeyboardButton(
    'Отключить накрутку на все существующие заказы', callback_data='Отключить накрутку'
)
group_6 = InlineKeyboardButton(
    'Перейти к накрутке подписчиков', callback_data='Накрутка подписчиков'
)
group.add(group_1).add(group_2).add(group_3).add(group_4).add(group_6)


orders = InlineKeyboardMarkup()
orders_1 = InlineKeyboardButton(
    'Отключить накрутку в заказе', callback_data='Отключить накрутку в заказе'
)
orders_2 = InlineKeyboardButton(
    'Включить накрутку в заказе', callback_data='Включить обратно накрутку в заказе'
)
orders_3 = InlineKeyboardButton(
    'Вернуться к группе', callback_data='Вернуться к группе'
)
orders.add(orders_1).add(orders_2).add(orders_3)

subs_none = InlineKeyboardMarkup()
subs_menu = InlineKeyboardButton(
    'Вернуться к группе', callback_data='Вернуться к группе'
)
subs_none_1 = InlineKeyboardButton(
    'Добавить накрутку', callback_data='Добавить накрутку'
)
subs_none.add(subs_none_1).add(subs_menu)

subs_going = InlineKeyboardMarkup()
subs_going_1 = InlineKeyboardButton(
    'Изменить параметры накрутки', callback_data='Изменить параметры накрутки'
)
subs_going_2 = InlineKeyboardButton(
    'Переключить статус подписчиков', callback_data='Переключить статус подписчиков'
)
subs_going.add(subs_going_1).add(subs_going_2).add(subs_menu)
