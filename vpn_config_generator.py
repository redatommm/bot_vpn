import paramiko
import os
import logging
import tempfile
from typing import Optional, Tuple
import uuid
import time

logger = logging.getLogger(__name__)

class VPNConfigGenerator:
    """Класс для генерации VPN конфигов через SSH"""
    
    def __init__(self, host: str, port: int, username: str, password: str = None, key_path: str = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_path = key_path
        self._ssh_client = None
        self._last_connection = 0
        self._connection_timeout = 600  # 10 минут
        
    def _get_ssh_client(self) -> paramiko.SSHClient:
        """Создание SSH клиента с кэшированием"""
        current_time = time.time()
        
        # Проверяем существующее подключение
        if (self._ssh_client and 
            current_time - self._last_connection < self._connection_timeout):
            try:
                # Проверяем что подключение живо
                self._ssh_client.exec_command("echo test", timeout=3)
                return self._ssh_client
            except:
                pass
        
        # Закрываем старое подключение если есть
        if self._ssh_client:
            try:
                self._ssh_client.close()
            except:
                pass
        
        # Создаем новое подключение
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if self.key_path and os.path.exists(self.key_path):
                client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_path,
                    timeout=5,
                    banner_timeout=5
                )
            else:
                client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=5,
                    banner_timeout=5
                )
            
            self._ssh_client = client
            self._last_connection = current_time
            logger.info("SSH подключение установлено")
            return client
        except Exception as e:
            logger.error(f"Ошибка SSH подключения: {e}")
            raise
    
    def generate_openvpn_config(self, user_id: int) -> Optional[str]:
        """Генерация OpenVPN конфига"""
        try:
            client = self._get_ssh_client()
            
            # Используем быстрый скрипт для генерации
            command = f"timeout 5 /root/fast_gen_openvpn.sh {user_id}"
            
            stdin, stdout, stderr = client.exec_command(command, timeout=10)
            config_content = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error and "timeout" not in error.lower():
                logger.error(f"Ошибка генерации OpenVPN: {error}")
                return None
                
            if not config_content.strip():
                logger.error("Пустой конфиг OpenVPN")
                return None
                
            return config_content
            
        except Exception as e:
            logger.error(f"Ошибка генерации OpenVPN конфига: {e}")
            return None
    
    def generate_vless_config(self, user_id: int) -> Optional[str]:
        """Генерация VLESS конфига"""
        try:
            client = self._get_ssh_client()
            username = f"user_{user_id}"
            
            # Используем скрипт для генерации VLESS конфига с таймаутом
            command = f"timeout 10 /root/gen_vless.sh {username} && cat /etc/xray/users/{username}.vless"
            
            stdin, stdout, stderr = client.exec_command(command, timeout=15)
            config_content = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8')
            
            if error and "timeout" not in error.lower():
                logger.error(f"Ошибка генерации VLESS: {error}")
                return None
                
            if not config_content:
                logger.error("Пустой конфиг VLESS")
                return None
                
            return config_content
            
        except Exception as e:
            logger.error(f"Ошибка генерации VLESS конфига: {e}")
            return None
    
    def revoke_user_config(self, user_id: int) -> bool:
        """Отзыв конфига пользователя"""
        try:
            client = self._get_ssh_client()
            username = f"user_{user_id}"
            
            # Используем скрипт для отзыва с таймаутом
            command = f"""
            timeout 10 bash -c '
            if [ -f "/root/revoke_user.sh" ]; then
                chmod +x /root/revoke_user.sh
                /root/revoke_user.sh {username}
            else
                echo "Скрипт revoke_user.sh не найден"
                exit 1
            fi
            '
            """
            
            stdin, stdout, stderr = client.exec_command(command, timeout=15)
            error = stderr.read().decode('utf-8')
            
            if error and "не найден" not in error and "timeout" not in error.lower():
                logger.warning(f"Предупреждение при отзыве {username}: {error}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отзыва конфига: {e}")
            return False

# Глобальный экземпляр генератора
# Используем SSH ключ для автоматического подключения
import os
vpn_generator = VPNConfigGenerator(
    host="31.58.171.77",
    port=22,
    username="root",
    key_path=os.path.expanduser("~/.ssh/vpn_server_key")  # Используем SSH ключ
) 