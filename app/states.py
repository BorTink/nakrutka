from aiogram.dispatcher.filters.state import State, StatesGroup


# Определение состояний для работы бота
class BaseStates(StatesGroup):
    warranty = State()  # Состояние для обработки гарантийного случая
    instructions = State()  # Состояние для обработки запроса инструкции по использованию инструмента
    question = State()
    wish = State()
