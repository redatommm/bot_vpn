from aiogram import F, types, Router
from aiogram.filters import Command
import logging
from Profile import db_manager
import os
import random
import string
from datetime import datetime, timedelta
from vpn_config_generator import vpn_generator

logger = logging.getLogger(__name__)
router = Router(name="connect_router")

def generate_client_config(username: str, trial_end: str) -> str:
    """Генерация конфигурационного файла OpenVPN для клиента"""
    # Используем реальную генерацию через SSH
    user_id = int(username.replace("user_", ""))
    config = vpn_generator.generate_openvpn_config(user_id)
    if config:
        return config
    else:
        # Fallback на заглушку если SSH не работает
        return f"""client
dev tun
proto udp
remote 31.58.171.77 1194
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-CBC
verb 3
auth-user-pass
<ca>
-----BEGIN CERTIFICATE-----
YOUR_CA_CERTIFICATE_HERE
-----END CERTIFICATE-----
</ca>
<cert>
-----BEGIN CERTIFICATE-----
YOUR_CLIENT_CERTIFICATE_HERE
-----END CERTIFICATE-----
</cert>
<key>
-----BEGIN PRIVATE KEY-----
YOUR_CLIENT_KEY_HERE
-----END PRIVATE KEY-----
</key>
"""

@router.message(F.text == "🔌 Подключить VPN")
async def connect_vpn(message: types.Message):
    """Обработчик кнопки подключения VPN"""
    try:
        user_id = message.from_user.id
        user_data = db_manager.get_user(user_id)

        if not user_data:
            await message.answer("Сначала нажмите /start")
            return

        # Проверяем статус пробного периода
        is_trial_active = db_manager.check_trial_status(user_id)
        
        if not is_trial_active and user_data[0].lower() != "активна":
            await message.answer(
                "❌ У вас нет активной подписки!\n"
                "Пожалуйста, продлите подписку для использования VPN."
            )
            return

        # Создаем клавиатуру для выбора типа VPN
        from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔐 OpenVPN", callback_data="get_openvpn")],
            [InlineKeyboardButton(text="🚀 VLESS (Xray)", callback_data="get_vless")]
        ])
        
        await message.answer(
            "🔌 <b>Выберите тип VPN подключения:</b>\n\n"
            "🔐 <b>OpenVPN</b> - классический протокол, работает везде\n"
            "🚀 <b>VLESS</b> - современный протокол, быстрее и стабильнее",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка при подключении VPN: {e}")
        await message.answer("⚠️ Произошла ошибка при генерации конфигурации")

@router.callback_query(F.data == "get_openvpn")
async def get_openvpn_config(callback: types.CallbackQuery):
    """Обработчик получения OpenVPN конфига"""
    try:
        user_id = callback.from_user.id
        user_data = db_manager.get_user(user_id)

        if not user_data:
            await callback.answer("Сначала нажмите /start", show_alert=True)
            return

        # Проверяем статус пробного периода
        is_trial_active = db_manager.check_trial_status(user_id)
        
        if not is_trial_active and user_data[0].lower() != "активна":
            await callback.answer(
                "❌ У вас нет активной подписки!",
                show_alert=True
            )
            return

        await callback.message.edit_text("⏳ Генерирую OpenVPN конфиг...")
        
        # Проверяем истек ли предыдущий конфиг
        if db_manager.check_config_expired(user_id, 'openvpn'):
            # Генерируем новый конфигурацию
            username = f"user_{user_id}"
            config = generate_client_config(username, user_data[2])  # trial_end

            if not config:
                await callback.message.edit_text("❌ Ошибка генерации конфига. Попробуйте позже.")
                return

            # Устанавливаем срок действия (3 дня)
            db_manager.set_config_expires(user_id, 'openvpn', 3)

            # Создаем временный файл конфигурации
            config_filename = f"openvpn_config_{user_id}.ovpn"
            with open(config_filename, "w") as f:
                f.write(config)

            # Отправляем файл пользователю
            with open(config_filename, "rb") as f:
                await callback.message.answer_document(
                    document=types.FSInputFile(config_filename),
                    caption="🔐 <b>Ваш OpenVPN конфиг</b>\n\n"
                            "📱 <b>Инструкция:</b>\n"
                            "1. Скачайте файл\n"
                            "2. Установите OpenVPN на устройство\n"
                            "3. Импортируйте этот файл\n"
                            "4. Подключитесь к VPN\n\n"
                            "🌐 <b>Сервер:</b> 31.58.171.77:1194\n"
                            "⏰ <b>Срок действия:</b> 3 дня",
                    parse_mode="HTML"
                )

            # Удаляем временный файл
            os.remove(config_filename)
            await callback.message.delete()
        else:
            await callback.message.edit_text("❌ У вас уже есть активный OpenVPN конфиг. Дождитесь истечения срока действия.")

    except Exception as e:
        logger.error(f"Ошибка при генерации OpenVPN: {e}")
        await callback.answer("⚠️ Ошибка при генерации конфига", show_alert=True)

@router.callback_query(F.data == "get_vless")
async def get_vless_config(callback: types.CallbackQuery):
    """Обработчик получения VLESS конфига"""
    try:
        user_id = callback.from_user.id
        user_data = db_manager.get_user(user_id)

        if not user_data:
            await callback.answer("Сначала нажмите /start", show_alert=True)
            return

        # Проверяем статус пробного периода
        is_trial_active = db_manager.check_trial_status(user_id)
        
        if not is_trial_active and user_data[0].lower() != "активна":
            await callback.answer(
                "❌ У вас нет активной подписки!",
                show_alert=True
            )
            return

        # Проверяем истек ли предыдущий конфиг
        if db_manager.check_config_expired(user_id, 'vless'):
            await callback.message.edit_text("⏳ Генерирую VLESS конфиг...")
            
            # Генерируем VLESS конфигурацию
            try:
                vless_link = vpn_generator.generate_vless_config(user_id)
            except Exception as e:
                logger.error(f"Ошибка генерации VLESS: {e}")
                await callback.message.edit_text("❌ Ошибка генерации конфига. Попробуйте позже.")
                return

            if not vless_link:
                await callback.message.edit_text("❌ Ошибка генерации VLESS конфига. Попробуйте позже.")
                return

            # Устанавливаем срок действия (3 дня)
            db_manager.set_config_expires(user_id, 'vless', 3)

            await callback.message.edit_text(
                f"🚀 <b>Ваш VLESS конфиг</b>\n\n"
                f"📋 <b>Ссылка для подключения:</b>\n"
                f"<code>{vless_link}</code>\n\n"
                f"📱 <b>Инструкция:</b>\n"
                f"1. Скопируйте ссылку выше\n"
                f"2. Установите V2rayNG или V2rayN\n"
                f"3. Добавьте конфиг через QR-код или вручную\n"
                f"4. Подключитесь к VPN\n\n"
                f"🌐 <b>Сервер:</b> 31.58.171.77:443\n"
                f"⏰ <b>Срок действия:</b> 3 дня",
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text("❌ У вас уже есть активный VLESS конфиг. Дождитесь истечения срока действия.")

    except Exception as e:
        logger.error(f"Ошибка при генерации VLESS: {e}")
        await callback.answer("⚠️ Ошибка при генерации конфига", show_alert=True)

def register_connect_module(dp):
    """Регистрация модуля подключения VPN"""
    dp.include_router(router) 