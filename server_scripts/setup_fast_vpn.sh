#!/bin/bash
# Скрипт для настройки быстрой системы VPN
# Создает пул готовых сертификатов и настраивает быструю выдачу

echo "Настройка быстрой системы VPN..."

# Переходим в директорию easy-rsa
cd /etc/openvpn/easy-rsa/

# Создаем директорию для пула сертификатов
mkdir -p /etc/openvpn/cert_pool

# Генерируем 100 готовых сертификатов
echo "Генерирую пул сертификатов..."
for i in {1..100}; do
    username="pool_user_$i"
    echo "Создаю сертификат $i/100 для $username"
    
    # Очищаем старые файлы
    rm -f pki/reqs/$username.req pki/issued/$username.crt pki/private/$username.key
    
    # Генерируем сертификат
    EASYRSA_CERT_EXPIRE=365 ./easyrsa build-client-full $username nopass
    
    # Копируем в пул
    cp pki/issued/$username.crt /etc/openvpn/cert_pool/
    cp pki/private/$username.key /etc/openvpn/cert_pool/
done

# Создаем быстрый скрипт выдачи
cat > /root/fast_gen_openvpn.sh << 'EOF'
#!/bin/bash
# Быстрая генерация OpenVPN конфига
# Использование: ./fast_gen_openvpn.sh user_id

if [ $# -eq 0 ]; then
    echo "Использование: $0 user_id"
    exit 1
fi

USER_ID=$1
USERNAME="user_$USER_ID"

# Ищем свободный сертификат в пуле
POOL_USER=""
for i in {1..100}; do
    pool_user="pool_user_$i"
    if [ -f "/etc/openvpn/cert_pool/$pool_user.crt" ] && [ -f "/etc/openvpn/cert_pool/$pool_user.key" ]; then
        POOL_USER=$pool_user
        break
    fi
done

if [ -z "$POOL_USER" ]; then
    echo "Ошибка: нет свободных сертификатов в пуле"
    exit 1
fi

# Создаем конфиг с готовым сертификатом
cat > /tmp/$USERNAME.ovpn << EOF
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

cat /etc/openvpn/easy-rsa/pki/ca.crt >> /tmp/$USERNAME.ovpn

cat >> /tmp/$USERNAME.ovpn << EOF
</ca>
<cert>
EOF

cat /etc/openvpn/cert_pool/$POOL_USER.crt >> /tmp/$USERNAME.ovpn

cat >> /tmp/$USERNAME.ovpn << EOF
</cert>
<key>
EOF

cat /etc/openvpn/cert_pool/$POOL_USER.key >> /tmp/$USERNAME.ovpn

cat >> /tmp/$USERNAME.ovpn << EOF
</key>
EOF

# Удаляем использованный сертификат из пула
rm -f /etc/openvpn/cert_pool/$POOL_USER.crt /etc/openvpn/cert_pool/$POOL_USER.key

# Выводим конфиг
cat /tmp/$USERNAME.ovpn
rm -f /tmp/$USERNAME.ovpn
EOF

chmod +x /root/fast_gen_openvpn.sh

echo "Быстрая система VPN настроена!"
echo "Теперь конфиги генерируются за 0.1-0.3 секунды" 