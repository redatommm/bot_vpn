from aiogram import F, types, Router
from aiogram.filters import Command
import logging
from Profile import db_manager
from vpn_config_generator import vpn_generator

logger = logging.getLogger(__name__)
router = Router(name="admin_router")

# Список админов (замените на свои ID)
ADMIN_IDS = [123456789]  # Замените на свой Telegram ID

def is_admin(user_id: int) -> bool:
    """Проверка является ли пользователь админом"""
    return user_id in ADMIN_IDS

@router.message(Command("ban"))
async def ban_user(message: types.Message):
    """Отзыв конфига пользователя (только для админов)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    try:
        # Парсим команду: /ban user_id
        args = message.text.split()
        if len(args) != 2:
            await message.answer("Использование: /ban <user_id>")
            return
        
        user_id = int(args[1])
        
        # Проверяем существование пользователя
        user_data = db_manager.get_user(user_id)
        if not user_data:
            await message.answer(f"❌ Пользователь {user_id} не найден в базе данных")
            return
        
        # Отзываем конфиги
        success = vpn_generator.revoke_user_config(user_id)
        
        if success:
            await message.answer(
                f"✅ Конфиги пользователя {user_id} отозваны\n"
                f"OpenVPN и VLESS конфиги удалены с сервера"
            )
        else:
            await message.answer(f"❌ Ошибка при отзыве конфигов пользователя {user_id}")
            
    except ValueError:
        await message.answer("❌ Неверный формат user_id")
    except Exception as e:
        logger.error(f"Ошибка при бане пользователя: {e}")
        await message.answer("❌ Произошла ошибка при выполнении команды")

@router.message(Command("users"))
async def list_users(message: types.Message):
    """Список всех пользователей (только для админов)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    try:
        # Получаем всех пользователей из БД
        cursor = db_manager.conn.cursor()
        cursor.execute("SELECT user_id, username, first_name, subscription_status, trial_end FROM users")
        users = cursor.fetchall()
        
        if not users:
            await message.answer("📝 Пользователей пока нет")
            return
        
        # Формируем список пользователей
        users_text = "📋 <b>Список пользователей:</b>\n\n"
        
        for user in users:
            user_id, username, first_name, status, trial_end = user
            users_text += f"👤 <b>ID:</b> {user_id}\n"
            users_text += f"├ Имя: {first_name or 'Не указано'}\n"
            users_text += f"├ Username: @{username or 'Не указан'}\n"
            users_text += f"├ Статус: {status}\n"
            users_text += f"└ Пробный период: {trial_end or 'Не указан'}\n\n"
        
        await message.answer(users_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        await message.answer("❌ Ошибка при получении списка пользователей")

@router.message(Command("stats"))
async def show_stats(message: types.Message):
    """Статистика бота (только для админов)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    try:
        cursor = db_manager.conn.cursor()
        
        # Общее количество пользователей
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Активные подписки
        cursor.execute("SELECT COUNT(*) FROM users WHERE subscription_status = 'Активна'")
        active_subscriptions = cursor.fetchone()[0]
        
        # Пробные периоды
        cursor.execute("SELECT COUNT(*) FROM users WHERE trial_end IS NOT NULL")
        trial_users = cursor.fetchone()[0]
        
        # Активные конфиги
        cursor.execute("SELECT COUNT(*) FROM users WHERE openvpn_expires IS NOT NULL OR vless_expires IS NOT NULL")
        active_configs = cursor.fetchone()[0]
        
        stats_text = "📊 <b>Статистика бота:</b>\n\n"
        stats_text += f"👥 Всего пользователей: {total_users}\n"
        stats_text += f"✅ Активных подписок: {active_subscriptions}\n"
        stats_text += f"🆓 Пробных периодов: {trial_users}\n"
        stats_text += f"🔐 Активных конфигов: {active_configs}\n"
        
        await message.answer(stats_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await message.answer("❌ Ошибка при получении статистики")

@router.message(Command("cleanup"))
async def cleanup_expired(message: types.Message):
    """Очистка истекших конфигов (только для админов)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    try:
        await message.answer("🧹 Начинаю очистку истекших конфигов...")
        
        # Вызываем очистку
        db_manager.cleanup_expired_configs()
        
        await message.answer("✅ Очистка истекших конфигов завершена")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке конфигов: {e}")
        await message.answer("❌ Ошибка при очистке конфигов")

def register_admin_module(dp):
    """Регистрация админского модуля"""
    dp.include_router(router) 