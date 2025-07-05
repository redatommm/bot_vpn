#!/bin/bash
# Скрипт для настройки SSH-ключей

echo "Настройка SSH-ключей для автоматического подключения..."

# Создаем SSH ключ если его нет
if [ ! -f ~/.ssh/vpn_server_key ]; then
    echo "Создаю SSH ключ..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/vpn_server_key -N ""
fi

# Копируем ключ на сервер
echo "Копирую ключ на сервер..."
ssh-copy-id -i ~/.ssh/vpn_server_key.pub root@31.58.171.77

echo "SSH ключи настроены!"
echo "Теперь можно подключаться без пароля." 