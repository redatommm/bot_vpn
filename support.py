from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import asyncio
import logging
from typing import Optional
from google_logger import GoogleLogger

class SupportStates(StatesGroup):
    WAITING_FOR_QUESTION = State()
    ANSWERING_QUESTION = State()

class SupportModule:
    def __init__(self, dp: Dispatcher, admin_chat_id: int = None, google_logger: Optional[GoogleLogger] = None):
        self.dp = dp
        self.admin_chat_id = admin_chat_id
        self.google_logger = google_logger
        self.active_requests = {}
        self.register_handlers()

    def register_handlers(self):
        self.dp.message.register(self.handle_support_request, F.text == "🆘 Техподдержка")
        self.dp.callback_query.register(self.handle_support_callback, F.data.startswith("support_"))
        self.dp.message.register(self.handle_user_question, SupportStates.WAITING_FOR_QUESTION)

    async def handle_support_request(self, message: types.Message, state: FSMContext):
        if self.google_logger:
            self.google_logger.log_user_action(
                user_id=message.from_user.id,
                username=message.from_user.username,
                action="Обращение в поддержку",
                additional_info="Пользователь начал диалог с поддержкой"
            )
        
        await state.set_state(SupportStates.WAITING_FOR_QUESTION)
        await message.answer(
            "<b>🛠 Техническая поддержка</b>\n\n"
            "Опишите вашу проблему или вопрос в одном сообщении.\n"
            "Наш нейро-ассистент ответит вам в этом же чате.\n\n"
            "<i>Для отмены используйте /cancel</i>",
            parse_mode="HTML"
        )

    async def handle_user_question(self, message: types.Message, state: FSMContext):
        question = message.text
        user_id = message.from_user.id
        
        if self.google_logger:
            self.google_logger.log_user_action(
                user_id=message.from_user.id,
                username=message.from_user.username,
                action="Вопрос в поддержку",
                additional_info=f"Вопрос: {question}"
            )
        
        self.active_requests[user_id] = (message.message_id, question)
        await message.answer("🔄 Ваш вопрос принят в обработку...")
        await asyncio.sleep(2)
        ai_response = (
            f"🤖 <b>Нейро-ассистент отвечает:</b>\n\n"
            f"Ваш вопрос: <i>{question}</i>\n\n"
            f"1. Проверьте настройки бота\n"
            f"2. Убедитесь, что у вас последняя версия\n"
            f"3. Попробуйте перезапустить процесс"
        )
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="❌ Закрыть обращение", callback_data="support_close")
        ]])
        await message.answer(ai_response, reply_markup=reply_markup, parse_mode="HTML")
        await state.clear()
        if self.admin_chat_id:
            await message.bot.send_message(
                self.admin_chat_id,
                f"📨 Новый вопрос в поддержку от @{message.from_user.username}:\n\n{question}"
            )

    async def handle_support_callback(self, callback: types.CallbackQuery, state: FSMContext):
        action = callback.data.split("_")[1]
        if action == "close":
            if self.google_logger:
                self.google_logger.log_user_action(
                    user_id=callback.from_user.id,
                    username=callback.from_user.username,
                    action="Закрытие обращения",
                    additional_info="Пользователь закрыл обращение в поддержку"
                )
            await callback.message.delete()
            await callback.answer("Обращение закрыто")
        elif action == "start":
            await state.set_state(SupportStates.WAITING_FOR_QUESTION)
            await callback.message.edit_text(
                "Опишите вашу проблему или вопрос в одном сообщении:",
                reply_markup=None
            )
            await callback.answer()

def register_support_module(dp: Dispatcher, admin_chat_id=None, google_logger: Optional[GoogleLogger] = None):
    support = SupportModule(dp, admin_chat_id, google_logger)
    return support
