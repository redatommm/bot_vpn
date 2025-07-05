#!/bin/bash
# Скрипт для генерации OpenVPN конфига
# Использование: ./gen_openvpn.sh username

if [ $# -eq 0 ]; then
    echo "Использование: $0 username"
    exit 1
fi

USERNAME=$1

# Проверяем, что easy-rsa установлен
if [ ! -d "/etc/openvpn/easy-rsa" ]; then
    echo "Ошибка: easy-rsa не найден в /etc/openvpn/easy-rsa"
    exit 1
fi

# Переходим в директорию easy-rsa
cd /etc/openvpn/easy-rsa/

# Проверяем наличие easyrsa
if [ ! -f "./easyrsa" ]; then
    echo "Ошибка: easyrsa не найден"
    exit 1
fi

# Создаем директорию для конфигов, если её нет
mkdir -p /etc/openvpn/client-configs/files

# Ищем доступный сертификат в пуле
POOL_USER=""
for i in {1..50}; do
    pool_user="user_$i"
    if [ -f "/etc/openvpn/cert_pool/$pool_user.crt" ] && [ -f "/etc/openvpn/cert_pool/$pool_user.key" ]; then
        POOL_USER=$pool_user
        break
    fi
done

if [ -n "$POOL_USER" ]; then
    cp /etc/openvpn/cert_pool/$POOL_USER.crt pki/issued/$USERNAME.crt
    cp /etc/openvpn/cert_pool/$POOL_USER.key pki/private/$USERNAME.key
    rm -f /etc/openvpn/cert_pool/$POOL_USER.crt /etc/openvpn/cert_pool/$POOL_USER.key
else
    EASYRSA_CERT_EXPIRE=365 ./easyrsa build-client-full $USERNAME nopass
    if [ ! -f "pki/issued/$USERNAME.crt" ] || [ ! -f "pki/private/$USERNAME.key" ]; then
        echo "Ошибка: не удалось создать сертификаты для $USERNAME"
        exit 1
    fi
fi

cat > /etc/openvpn/client-configs/files/$USERNAME.ovpn << EOF
client
dev tun
proto udp
remote 31.58.171.77 1194
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-CBC
auth SHA256
comp-lzo
verb 3
<ca>
EOF
cat pki/ca.crt >> /etc/openvpn/client-configs/files/$USERNAME.ovpn
cat >> /etc/openvpn/client-configs/files/$USERNAME.ovpn << EOF
</ca>
<cert>
EOF
cat pki/issued/$USERNAME.crt >> /etc/openvpn/client-configs/files/$USERNAME.ovpn
cat >> /etc/openvpn/client-configs/files/$USERNAME.ovpn << EOF
</cert>
<key>
EOF
cat pki/private/$USERNAME.key >> /etc/openvpn/client-configs/files/$USERNAME.ovpn
cat >> /etc/openvpn/client-configs/files/$USERNAME.ovpn << EOF
</key>
EOF

cat /etc/openvpn/client-configs/files/$USERNAME.ovpn 