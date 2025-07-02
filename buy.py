from aiogram import F, types, Router, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import logging
from typing import Optional
from google_logger import GoogleLogger

logger = logging.getLogger(__name__)
router = Router(name="purchase_router")

class PurchaseStates(StatesGroup):
    SELECT_PRODUCT = State()
    CONFIRMATION = State()
    PAYMENT = State()

prices = {1: 100, 3: 250, 12: 800}

@router.message(F.text == "🛒 Купить VPN")
async def start_vpn_purchase(message: types.Message, state: FSMContext, google_logger: Optional[GoogleLogger] = None):
    if google_logger:
        google_logger.log_user_action(
            user_id=message.from_user.id,
            username=message.from_user.username,
            action="Начало покупки",
            additional_info="Пользователь начал процесс покупки VPN"
        )
    await show_tariffs(message)
    await state.set_state(PurchaseStates.SELECT_PRODUCT)

async def show_tariffs(target: types.Message | types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1 месяц - 100₽", callback_data="vpn_1")],
            [InlineKeyboardButton(text="3 месяца - 250₽", callback_data="vpn_3")],
            [InlineKeyboardButton(text="1 год - 800₽", callback_data="vpn_12")],
        ]
    )
    text = "🔐 <b>GhostLink VPN - Выберите тариф:</b>"

    if isinstance(target, types.Message):
        await target.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await target.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("vpn_"))
@router.callback_query(F.data == "vpn_back")
@router.callback_query(F.data == "confirm_purchase")
@router.callback_query(F.data == "purchase_yes")
async def process_callback(callback: types.CallbackQuery, state: FSMContext, google_logger: Optional[GoogleLogger] = None):
    try:
        action = callback.data
        if action == "vpn_back":
            await show_tariffs(callback)
            await state.set_state(PurchaseStates.SELECT_PRODUCT)
        elif action.startswith("vpn_"):
            await handle_tariff_selection(callback, state, google_logger)
        elif action == "confirm_purchase":
            await handle_confirmation(callback, state)
        elif action == "purchase_yes":
            await handle_payment(callback, state, google_logger)

        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка обработки callback: {e}")
        if google_logger:
            google_logger.log_user_action(
                user_id=callback.from_user.id,
                username=callback.from_user.username,
                action="Ошибка при покупке",
                additional_info=str(e)
            )
        await callback.answer("⚠️ Произошла ошибка", show_alert=True)

async def handle_tariff_selection(callback: types.CallbackQuery, state: FSMContext, google_logger: Optional[GoogleLogger] = None):
    period = int(callback.data.split("_")[1])
    await state.update_data(
        product_name=f"GhostLink VPN на {period} мес.",
        price=prices[period],
        period=period
    )
    
    if google_logger:
        google_logger.log_user_action(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            action="Выбор тарифа",
            additional_info=f"Выбран тариф на {period} месяцев за {prices[period]}₽"
        )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить", callback_data="confirm_purchase")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="vpn_back")]
        ]
    )
    await callback.message.edit_text(
        f"<b>🔒 GhostLink VPN на {period} мес.</b>\n\n"
        f"<i>Преимущества:</i>\n"
        f"✅ Безлимитный трафик\n"
        f"✅ Высокая скорость\n"
        f"✅ Нулевой пинг\n"
        f"✅ Поддержка всех устройств\n\n"
        f"<b>Цена: {prices[period]}₽</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(PurchaseStates.SELECT_PRODUCT)

async def handle_confirmation(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="purchase_yes")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="vpn_back")]
        ]
    )
    await callback.message.edit_text(
        f"<b>Подтверждение покупки</b>\n\n"
        f"Товар: <b>{data['product_name']}</b>\n"
        f"Цена: <b>{data['price']}₽</b>\n\n"
        f"Подтверждаете покупку?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(PurchaseStates.CONFIRMATION)

async def handle_payment(callback: types.CallbackQuery, state: FSMContext, google_logger: Optional[GoogleLogger] = None):
    data = await state.get_data()
    payment_id = random.randint(10000, 99999)
    
    if google_logger:
        google_logger.log_user_action(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            action="Оплата",
            additional_info=f"Создан платеж #{payment_id} на сумму {data['price']}₽"
        )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=f"https://example.com/pay/{payment_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="confirm_purchase")]
        ]
    )
    await callback.message.edit_text(
        f"<b>Оплата #{payment_id}</b>\n"
        f"Сумма: <b>{data['price']}₽</b>\n\n"
        "Нажмите кнопку ниже для оплаты:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(PurchaseStates.PAYMENT)

def register_purchase_module(dp: Dispatcher, google_logger: Optional[GoogleLogger] = None):
    dp.include_router(router)
