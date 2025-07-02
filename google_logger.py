import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class GoogleLogger:
    def __init__(self, credentials_file, spreadsheet_name):
        """
        Инициализация логгера для Google Sheets
        
        :param credentials_file: путь к файлу с учетными данными Google
        :param spreadsheet_name: название таблицы в Google Sheets
        """
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open(spreadsheet_name)
            self.worksheet = self.spreadsheet.sheet1
            
            # Проверяем, есть ли заголовки в таблице
            if not self.worksheet.row_values(1):
                self.worksheet.append_row([
                    'Дата и время',
                    'ID пользователя',
                    'Имя пользователя',
                    'Действие',
                    'Дополнительная информация'
                ])
            
            logger.info("Google Logger успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации Google Logger: {e}")
            raise

    def log_user_action(self, user_id, username, action, additional_info=""):
        """
        Логирование действия пользователя
        
        :param user_id: ID пользователя в Telegram
        :param username: имя пользователя в Telegram
        :param action: действие пользователя
        :param additional_info: дополнительная информация
        """
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.worksheet.append_row([
                current_time,
                str(user_id),
                username or "Не указано",
                action,
                additional_info
            ])
            
            logger.info(f"Действие пользователя {username} ({user_id}) успешно залогировано")
            
        except Exception as e:
            logger.error(f"Ошибка при логировании действия пользователя: {e}")

    def get_user_history(self, user_id):
        """
        Получение истории действий пользователя
        
        :param user_id: ID пользователя в Telegram
        :return: список действий пользователя
        """
        try:
            all_records = self.worksheet.get_all_records()
            user_history = [record for record in all_records if str(record['ID пользователя']) == str(user_id)]
            return user_history
        except Exception as e:
            logger.error(f"Ошибка при получении истории пользователя: {e}")
            return [] 