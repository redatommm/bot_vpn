#!/bin/bash
# Скрипт для предварительной генерации пула сертификатов
# Запускать один раз для создания пула быстрых сертификатов

echo "Создаю пул предварительно сгенерированных сертификатов..."

# Переходим в директорию easy-rsa
cd /etc/openvpn/easy-rsa/

# Создаем директорию для пула
mkdir -p /etc/openvpn/cert_pool

# Генерируем 50 сертификатов заранее
for i in {1..50}; do
    username="user_$i"
    echo "Генерирую сертификат $i/50 для $username..."
    
    # Очищаем старые файлы
    rm -f pki/reqs/$username.req pki/issued/$username.crt pki/private/$username.key
    
    # Генерируем сертификат
    EASYRSA_CERT_EXPIRE=365 ./easyrsa build-client-full $username nopass
    
    # Копируем в пул
    cp pki/issued/$username.crt /etc/openvpn/cert_pool/
    cp pki/private/$username.key /etc/openvpn/cert_pool/
    
    echo "Сертификат $username готов"
done

echo "Пул сертификатов создан! Теперь конфиги будут генерироваться за 2-3 секунды." 