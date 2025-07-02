from aiogram import types, F, Router
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import Dispatcher
import sqlite3, os, logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = Router(name="profile_router")

class DatabaseManager:
    """Класс для управления подключением к базе данных"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = self.init_db()
        
    def init_db(self):
        """Инициализация базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Удаляем существующую таблицу, если она есть
            cursor.execute("DROP TABLE IF EXISTS users")
            
            # Создаем таблицу заново с новой структурой
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                subscription_status TEXT DEFAULT 'Пробная',
                subscription_end TEXT DEFAULT NULL,
                trial_end TEXT DEFAULT NULL,
                devices_connected INTEGER DEFAULT 1
            )
            """)
            conn.commit()
            return conn
        except sqlite3.Error as e:
            logger.error(f"Ошибка базы данных: {e}")
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            return sqlite3.connect(self.db_path)
    
    def get_user(self, user_id: int) -> Optional[tuple]:
        """Получение данных пользователя"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT subscription_status, subscription_end, trial_end, devices_connected
            FROM users WHERE user_id = ?
        """, (user_id,))
        return cursor.fetchone()
    
    def check_trial_status(self, user_id: int) -> bool:
        """Проверка статуса пробного периода"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT trial_end FROM users WHERE user_id = ?
        """, (user_id,))
        result = cursor.fetchone()
        
        if not result or not result[0]:
            return False
            
        trial_end = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
        return datetime.now() < trial_end
    
    def add_user(self, user_id: int, username: str, first_name: str):
        """Добавление нового пользователя"""
        # Устанавливаем дату окончания пробного периода (3 дня)
        trial_end = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, trial_end) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, trial_end)
        )
        self.conn.commit()
        logger.info(f"Добавлен новый пользователь: {user_id} с пробным периодом до {trial_end}")

# Инициализация базы данных
DB_PATH = os.path.join(os.path.dirname(__file__), 'vpn_users.db')
db_manager = DatabaseManager(DB_PATH)

async def ensure_user_exists(message: types.Message):
    """Проверяет существование пользователя в БД, при необходимости добавляет"""
    user_id = message.from_user.id
    if not db_manager.get_user(user_id):
        db_manager.add_user(
            user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )

@router.message(F.text == "👤 Профиль")
async def profile_handler(message: types.Message):
    """Обработчик кнопки 'Профиль'"""
    try:
        user_id = message.from_user.id
        user_data = db_manager.get_user(user_id)

        if not user_data:
            await message.answer("Сначала нажмите /start")
            return

        # Проверяем статус пробного периода
        is_trial_active = db_manager.check_trial_status(user_id)
        
        # Определяем статус подписки
        if is_trial_active:
            subscription_status = "✅ Пробный период"
            subscription_end = user_data[2]  # trial_end
        else:
            is_active = "✅ Активна" if user_data[0].lower() == "активна" else "❌ Неактивна"
            subscription_status = is_active
            subscription_end = user_data[1] or 'не указано'
        
        # Формируем сообщение профиля
        profile_message = (
            f"👤 <b>Ваш профиль</b>\n"
            f"├ Устройств: {user_data[3]}\n"
            f"└ ID: <code>{user_id}</code>\n\n"
            f"💳 <b>Подписка:</b>\n"
            f"├ Статус: {subscription_status}\n"
            f"└ Окончание: {subscription_end}"
        )

        # Кнопка для продления
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔄 Продлить подписку", callback_data="renew_subscription")
        ]])

        await message.answer(profile_message, reply_markup=keyboard, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка в profile_handler: {e}")
        await message.answer("⚠️ Ошибка при загрузке профиля")

@router.callback_query(F.data == "renew_subscription")
async def renew_subscription_handler(callback: types.CallbackQuery):
    """Обработчик кнопки продления подписки"""
    try:
        user_id = callback.from_user.id
        user_data = db_manager.get_user(user_id)
        
        renew_message = (
            f"🔔 <b>Продление подписки</b>\n\n"
            f"Текущая подписка истекает: {user_data[1] or 'не указано'}\n\n"
            f"Выберите срок продления:"
        )
        
        renew_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1 месяц - 299₽", callback_data="renew_1month")],
            [InlineKeyboardButton(text="3 месяца - 799₽", callback_data="renew_3month")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_profile")]
        ])
        
        await callback.message.edit_text(renew_message, reply_markup=renew_keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в renew_subscription_handler: {e}")
        await callback.answer("⚠️ Ошибка при продлении", show_alert=True)

@router.callback_query(F.data == "back_to_profile")
async def back_to_profile_handler(callback: types.CallbackQuery):
    """Обработчик кнопки возврата в профиль"""
    try:
        user_id = callback.from_user.id
        user_data = db_manager.get_user(user_id)

        if not user_data:
            await callback.answer("Сначала нажмите /start", show_alert=True)
            return

        # Проверяем статус пробного периода
        is_trial_active = db_manager.check_trial_status(user_id)
        
        # Определяем статус подписки
        if is_trial_active:
            subscription_status = "✅ Пробный период"
            subscription_end = user_data[2]  # trial_end
        else:
            is_active = "✅ Активна" if user_data[0].lower() == "активна" else "❌ Неактивна"
            subscription_status = is_active
            subscription_end = user_data[1] or 'не указано'
        
        # Формируем сообщение профиля
        profile_message = (
            f"👤 <b>Ваш профиль</b>\n"
            f"├ Устройств: {user_data[3]}\n"
            f"└ ID: <code>{user_id}</code>\n\n"
            f"💳 <b>Подписка:</b>\n"
            f"├ Статус: {subscription_status}\n"
            f"└ Окончание: {subscription_end}"
        )

        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔄 Продлить подписку", callback_data="renew_subscription")
        ]])

        await callback.message.edit_text(
            text=profile_message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в back_to_profile_handler: {e}")
        await callback.answer("⚠️ Ошибка при возврате", show_alert=True)

def register_profile_module(dp: Dispatcher):
    """Регистрация модуля профиля"""
    dp.include_router(router)

def register_profile_module(dp):
    dp.include_router(router)
