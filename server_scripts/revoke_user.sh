#!/bin/bash
# Скрипт для отзыва VPN конфигов пользователя
# Использование: ./revoke_user.sh username

if [ $# -eq 0 ]; then
    echo "Использование: $0 username"
    exit 1
fi

USERNAME=$1

echo "Отзываю конфиги для пользователя $USERNAME..."

# Отзыв OpenVPN сертификата
if [ -d "/etc/openvpn/easy-rsa" ]; then
    cd /etc/openvpn/easy-rsa/
    echo "Отзываю OpenVPN сертификат..."
    ./easyrsa revoke $USERNAME
    ./easyrsa gen-crl
    cp pki/crl.pem /etc/openvpn/
    systemctl reload openvpn@server
fi

# Удаление OpenVPN файлов
rm -f /etc/openvpn/client-configs/files/$USERNAME.ovpn

# Удаление VLESS файлов
rm -f /etc/xray/users/$USERNAME.uuid
rm -f /etc/xray/users/$USERNAME.vless
rm -f /etc/xray/users/$USERNAME.json

echo "Конфиги для пользователя $USERNAME отозваны и удалены" 