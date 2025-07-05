#!/usr/bin/env python3
"""
Скрипт для автоматической очистки истекших VPN конфигов
Запускается по расписанию (cron) или вручную
"""

import logging
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Profile import db_manager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция очистки"""
    try:
        logger.info("Начинаю очистку истекших конфигов...")
        
        # Вызываем очистку из db_manager
        db_manager.cleanup_expired_configs()
        
        logger.info("Очистка истекших конфигов завершена")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке конфигов: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 