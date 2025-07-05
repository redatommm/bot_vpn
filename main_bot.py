import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from start import register_start_module
from buy import register_purchase_module
from Profile import register_profile_module
from support import register_support_module
from connect import register_connect_module
from admin_commands import register_admin_module
from user_manager import UserManager

# Инициализация логгера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Инициализация UserManager
try:
    user_manager = UserManager(
        credentials_file='VPN Bot Configuration.json',
        spreadsheet_name='VPN Bot Users'  # Название вашей Google таблицы
    )
    logger.info("UserManager успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка при инициализации UserManager: {e}")
    user_manager = None

async def cleanup_task():
    """Задача очистки истекших конфигов"""
    while True:
        try:
            await asyncio.sleep(3600)  # Каждый час
            db_manager.cleanup_expired_configs()
            logger.info("Автоматическая очистка истекших конфигов выполнена")
        except Exception as e:
            logger.error(f"Ошибка в задаче очистки: {e}")

async def main():
    logger.info("Инициализация бота...")
    
    bot = Bot(
        token="7617460226:AAGeAJpF27oanXsxkmYLtBynypYP5xCQ5tc",
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp["user_manager"] = user_manager

    logger.info("Регистрация модулей...")
    register_start_module(dp)
    register_purchase_module(dp)
    register_profile_module(dp)
    register_support_module(dp, admin_chat_id=None)
    register_connect_module(dp)
    register_admin_module(dp)

    try:
        logger.info("Бот успешно запущен и готов к работе!")
        
        # Запускаем задачу очистки в фоне
        asyncio.create_task(cleanup_task())
        
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Произошла ошибка при запуске бота: {e}")
    finally:
        logger.info("Завершение работы бота...")
        await bot.session.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
