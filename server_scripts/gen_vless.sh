#!/bin/bash
# Скрипт для генерации VLESS конфига
# Использование: ./gen_vless.sh username

if [ $# -eq 0 ]; then
    echo "Использование: $0 username"
    exit 1
fi

USERNAME=$1

# Генерируем UUID
UUID=$(cat /proc/sys/kernel/random/uuid)

# Создаем директорию для пользователей, если её нет
mkdir -p /etc/xray/users

# Сохраняем UUID для пользователя
echo "$UUID" > /etc/xray/users/$USERNAME.uuid

# Создаем VLESS ссылку
VLESS_LINK="vless://$UUID@31.58.171.77:443?encryption=none&security=tls&type=tcp#$USERNAME"

# Сохраняем ссылку в файл
echo "$VLESS_LINK" > /etc/xray/users/$USERNAME.vless

# Создаем JSON конфиг для Xray
cat > /etc/xray/users/$USERNAME.json << EOF
{
  "v": "2",
  "ps": "$USERNAME",
  "add": "31.58.171.77",
  "port": "443",
  "id": "$UUID",
  "aid": "0",
  "net": "tcp",
  "type": "none",
  "host": "",
  "path": "",
  "tls": "tls"
}
EOF

echo "VLESS конфиг создан для пользователя $USERNAME"
echo "UUID: $UUID"
echo "Ссылка: $VLESS_LINK"
echo "Файлы сохранены в /etc/xray/users/" 