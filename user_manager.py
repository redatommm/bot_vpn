import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self, credentials_file, spreadsheet_name):
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open(spreadsheet_name)
            self.worksheet = self.spreadsheet.sheet1
            
            # Проверяем заголовки
            headers = self.worksheet.row_values(1)
            expected_headers = [
                '№',
                'Telegram ID',
                'Username',
                'Дата регистрации',
                'Пробный лимит',
                'Активная подписка',
                'Дата окончания подписки',
                'Общая сумма покупок'
            ]
            if headers != expected_headers:
                logger.warning(f"Заголовки таблицы не соответствуют ожидаемым. Ожидаемые: {expected_headers}, Фактические: {headers}. Очищаю и устанавливаю новые заголовки.")
                self.worksheet.clear()
                self.worksheet.append_row(expected_headers)
            
            logger.info(f"UserManager успешно инициализирован для таблицы '{spreadsheet_name}'.")
        except gspread.exceptions.SpreadsheetNotFound:
            logger.error(f"Ошибка: Google таблица с именем '{spreadsheet_name}' не найдена. Убедитесь, что название таблицы верное и сервисный аккаунт имеет к ней доступ.")
            raise
        except gspread.exceptions.APIError as e:
            logger.error(f"Ошибка Google Sheets API при инициализации: {e}")
            raise
        except Exception as e:
            logger.error(f"Неизвестная ошибка при инициализации UserManager: {e}")
            raise

    def find_user_row(self, telegram_id):
        try:
            logger.debug(f"Поиск пользователя с Telegram ID: {telegram_id}")
            all_records = self.worksheet.get_all_records()
            for idx, user_data in enumerate(all_records, start=2):
                if str(user_data.get('Telegram ID')) == str(telegram_id):
                    logger.debug(f"Пользователь {telegram_id} найден в строке {idx}.")
                    return idx, user_data
            logger.debug(f"Пользователь {telegram_id} не найден.")
            return None, None
        except Exception as e:
            logger.error(f"Ошибка при поиске пользователя {telegram_id}: {e}")
            return None, None

    def add_user(self, telegram_id, username, trial_limit='no use'):
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            all_records = self.worksheet.get_all_records()
            next_number = len(all_records) + 1
            row_data = [
                next_number,
                telegram_id,
                username or '',
                now,
                trial_limit,
                'нет',
                '',
                0
            ]
            logger.info(f"Попытка добавить пользователя {telegram_id} с данными: {row_data}")
            self.worksheet.append_row(row_data)
            logger.info(f"Пользователь {telegram_id} успешно добавлен.")
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя {telegram_id}: {e}")
            return False

    def update_user(self, telegram_id, **kwargs):
        try:
            logger.info(f"Попытка обновить пользователя {telegram_id} с данными: {kwargs}")
            row_idx, user = self.find_user_row(telegram_id)
            if not user:
                logger.warning(f"Не удалось обновить пользователя {telegram_id}: пользователь не найден.")
                return False
            
            # Получаем текущие значения из таблицы, чтобы обновить их
            current_values = self.worksheet.row_values(row_idx)

            mapping = {
                'username': 2,
                'trial_limit': 4,
                'active_subscription': 5,
                'subscription_end': 6,
                'total_purchases': 7
            }
            for key, col_idx in mapping.items():
                if key in kwargs:
                    current_values[col_idx] = kwargs[key]
            
            self.worksheet.update(f'A{row_idx}:H{row_idx}', [current_values])
            logger.info(f"Пользователь {telegram_id} успешно обновлен.")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении пользователя {telegram_id}: {e}")
            return False

    def get_user(self, telegram_id):
        try:
            logger.debug(f"Получение данных пользователя с Telegram ID: {telegram_id}")
            _, user = self.find_user_row(telegram_id)
            if user:
                logger.debug(f"Данные пользователя {telegram_id} получены: {user}")
            else:
                logger.debug(f"Данные пользователя {telegram_id} не найдены.")
            return user
        except Exception as e:
            logger.error(f"Ошибка при получении данных пользователя {telegram_id}: {e}")
            return None 