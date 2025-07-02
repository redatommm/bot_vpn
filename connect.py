from aiogram import F, types, Router
from aiogram.filters import Command
import logging
from Profile import db_manager
import os
import random
import string
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = Router(name="connect_router")

def generate_client_config(username: str, trial_end: str) -> str:
    """Генерация конфигурационного файла OpenVPN для клиента"""
    # Базовая конфигурация OpenVPN
    config = f"""client
dev tun
proto udp
remote your-vpn-server.com 1194
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
    return config

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

        # Генерируем конфигурацию
        username = f"user_{user_id}"
        config = generate_client_config(username, user_data[2])  # trial_end

        # Создаем временный файл конфигурации
        config_filename = f"vpn_config_{user_id}.ovpn"
        with open(config_filename, "w") as f:
            f.write(config)

        # Отправляем файл пользователю
        with open(config_filename, "rb") as f:
            await message.answer_document(
                document=types.FSInputFile(config_filename),
                caption="📎 Ваш конфигурационный файл OpenVPN\n\n"
                        "1. Скачайте файл\n"
                        "2. Установите OpenVPN на ваше устройство\n"
                        "3. Импортируйте этот файл в OpenVPN\n"
                        "4. Подключитесь к VPN"
            )

        # Удаляем временный файл
        os.remove(config_filename)

    except Exception as e:
        logger.error(f"Ошибка при подключении VPN: {e}")
        await message.answer("⚠️ Произошла ошибка при генерации конфигурации")

def register_connect_module(dp):
    """Регистрация модуля подключения VPN"""
    dp.include_router(router) 