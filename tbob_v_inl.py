from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Токен бота
api = "7930585658:AAGkT27v_h3vGUh0ClYF1C3PqZ4558Mimco"
bot = Bot(token=api)
dp = Dispatcher(bot, storage=MemoryStorage())

# Начальное меню
start_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Рассчитать')],
        [
            KeyboardButton(text='Информация')
        ]
    ], resize_keyboard=True
)

# Inline-клавиатура для выбора действия в разделе "Рассчитать"
def create_inline_menu():
    inline_kb = InlineKeyboardMarkup()
    inline_kb.add(InlineKeyboardButton(text='Рассчитать норму калорий', callback_data='calories'))
    inline_kb.add(InlineKeyboardButton(text='Формулы расчёта', callback_data='formulas'))
    return inline_kb

# Inline-клавиатура для выбора пола
gender_menu = InlineKeyboardMarkup(row_width=2)
gender_menu.add(
    InlineKeyboardButton(text='Мужчина', callback_data='male'),
    InlineKeyboardButton(text='Женщина', callback_data='female')
)

# Машина состояний для расчета калорий
class CalorieCalculation(StatesGroup):
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_weight = State()
    waiting_for_height = State()

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def starter(message: types.Message):
    await message.answer('Добро пожаловать!', reply_markup=start_menu)

# Обработчик кнопки 'Рассчитать', вызывающий Inline-клавиатуру
@dp.message_handler(lambda message: message.text == 'Рассчитать')
async def main_menu(message: types.Message):
    await message.answer("Выберите опцию:", reply_markup=create_inline_menu())

# Обработчик кнопки 'Формулы расчёта', выводит формулу Миффлина-Сан Жеора
@dp.callback_query_handler(lambda call: call.data == 'formulas')
async def get_formulas(call: types.CallbackQuery):
    formula_text = ("Формула Миффлина-Сан Жеора:\n"
                    "Мужчины: 10 * вес + 6.25 * рост - 5 * возраст + 5\n"
                    "Женщины: 10 * вес + 6.25 * рост - 5 * возраст - 161")
    await call.message.answer(formula_text)

# Обработчик кнопки 'Рассчитать норму калорий', запуск машины состояний с выбором пола
@dp.callback_query_handler(lambda call: call.data == 'calories')
async def set_gender(call: types.CallbackQuery):
    await call.message.answer("Выберите ваш пол:", reply_markup=gender_menu)
    await CalorieCalculation.waiting_for_gender.set()  # Переход к состоянию ожидания выбора пола

# Обработчик выбора пола
@dp.callback_query_handler(lambda call: call.data in ['male', 'female'], state=CalorieCalculation.waiting_for_gender)
async def get_gender(call: types.CallbackQuery, state: FSMContext):
    gender = call.data
    await state.update_data(gender=gender)
    await call.message.answer("Введите ваш возраст:")
    await CalorieCalculation.waiting_for_age.set()  # Переход к состоянию ожидания возраста

# Обработчик для получения возраста
@dp.message_handler(state=CalorieCalculation.waiting_for_age)
async def get_age(message: types.Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await message.answer("Введите ваш вес в кг:")
    await CalorieCalculation.waiting_for_weight.set()  # Переход к состоянию ожидания веса

# Обработчик для получения веса
@dp.message_handler(state=CalorieCalculation.waiting_for_weight)
async def get_weight(message: types.Message, state: FSMContext):
    await state.update_data(weight=float(message.text))
    await message.answer("Введите ваш рост в см:")
    await CalorieCalculation.waiting_for_height.set()  # Переход к состоянию ожидания роста

# Обработчик для получения роста и завершение расчета
@dp.message_handler(state=CalorieCalculation.waiting_for_height)
async def calculate_calories(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    age = user_data['age']
    weight = user_data['weight']
    height = int(message.text)
    gender = user_data['gender']

    # Расчет нормы калорий по формуле Миффлина-Сан Жеора с учетом пола
    if gender == 'male':
        calories = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        calories = 10 * weight + 6.25 * height - 5 * age - 161

    await message.answer(f"Ваша расчетная норма калорий: {calories} ккал.")
    await state.finish()  # Завершение состояния

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
