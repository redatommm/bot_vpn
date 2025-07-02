from aiogram import F, types, Router, Dispatcher
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from typing import Dict, Tuple, Optional
from Profile import ensure_user_exists
from user_manager import UserManager

logger = logging.getLogger(__name__)
router = Router(name="start_router")

class SupportStates(StatesGroup):
    WAITING_FOR_QUESTION = State()
    ANSWERING_QUESTION = State()

@router.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext, user_manager: UserManager):
    await ensure_user_exists(message)

    # Регистрация пользователя в Google Sheets
    if user_manager:
        user = user_manager.get_user(message.from_user.id)
        if not user:
            user_manager.add_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username or '',
                trial_limit='no use'
            )
            logger.info(f"Пользователь {message.from_user.id} добавлен в Google Sheets")
        else:
            logger.info(f"Пользователь {message.from_user.id} уже есть в Google Sheets")
    else:
        logger.error("UserManager не доступен в start_handler! Этого не должно быть после исправлений.")

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🛒 Купить VPN")],
            [types.KeyboardButton(text="🔌 Подключить VPN")],
            [types.KeyboardButton(text="👤 Профиль")],
            [types.KeyboardButton(text="🆘 Техподдержка")],
        ],
        resize_keyboard=True
    )
    
    welcome_message = (
        "👋 Добро пожаловать в GhostLink VPN!\n\n"
        "🔒 Мы предлагаем безопасное и быстрое VPN-соединение.\n\n"
        "🎁 У вас есть 3 дня пробного периода!\n\n"
        "Выберите действие в меню ниже:"
    )
    
    await message.answer(welcome_message, reply_markup=keyboard)


def register_start_module(dp: Dispatcher):
    dp.include_router(router)
