# Настройка VPN бота

## 1. Подготовка сервера

### Установка OpenVPN
```bash
# На сервере 31.58.171.77
apt update
apt install openvpn easy-rsa

# Настройка easy-rsa
cd /etc/openvpn/easy-rsa/
./easyrsa init-pki
./easyrsa build-ca nopass
./easyrsa build-server-full server nopass
./easyrsa gen-dh

# Копирование файлов
cp pki/ca.crt pki/issued/server.crt pki/private/server.key /etc/openvpn/
cp pki/dh.pem /etc/openvpn/

# Создание конфига сервера
cat > /etc/openvpn/server.conf << EOF
port 1194
proto udp
dev tun
ca ca.crt
cert server.crt
key server.key
dh dh.pem
server 10.8.0.0 255.255.255.0
ifconfig-pool-persist ipp.txt
push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 8.8.8.8"
push "dhcp-option DNS 8.8.4.4"
keepalive 10 120
cipher AES-256-CBC
auth SHA256
comp-lzo
user nobody
group nobody
persist-key
persist-tun
status openvpn-status.log
verb 3
explicit-exit-notify 1
EOF

# Включение IP forwarding
echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
sysctl -p

# Запуск OpenVPN
systemctl enable openvpn@server
systemctl start openvpn@server
```

### Установка Xray
```bash
# Скачивание и установка Xray
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install

# Создание конфига Xray
cat > /usr/local/etc/xray/config.json << EOF
{
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "port": 443,
      "protocol": "vless",
      "settings": {
        "clients": [],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {
          "certificates": [
            {
              "certificateFile": "/etc/ssl/certs/ssl-cert-snakeoil.pem",
              "keyFile": "/etc/ssl/private/ssl-cert-snakeoil.key"
            }
          ]
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom"
    }
  ]
}
EOF

# Запуск Xray
systemctl enable xray
systemctl start xray
```

## 2. Копирование скриптов на сервер

```bash
# Копируем скрипты на сервер
scp server_scripts/gen_openvpn.sh root@31.58.171.77:/root/
scp server_scripts/gen_vless.sh root@31.58.171.77:/root/
scp server_scripts/revoke_user.sh root@31.58.171.77:/root/

# Делаем скрипты исполняемыми
ssh root@31.58.171.77 "chmod +x /root/*.sh"
```

## 3. Настройка бота

### Обновление конфигурации
В файле `vpn_config_generator.py` замените:
```python
vpn_generator = VPNConfigGenerator(
    host="31.58.171.77",
    port=22,
    username="root",  # Замените на своего пользователя
    password="your_password"  # Замените на свой пароль
)
```

### Установка зависимостей
```bash
pip install -r requirements.txt
```

## 4. Тестирование

1. Запустите бота: `python main_bot.py`
2. Отправьте команду `/start`
3. Нажмите "🔌 Подключить VPN"
4. Выберите тип конфига (OpenVPN или VLESS)

## 5. Команды для управления

### Добавление пользователя в Xray
```bash
# На сервере
/root/gen_vless.sh user_123456
```

### Отзыв пользователя
```bash
# На сервере
/root/revoke_user.sh user_123456
```

## 6. Структура файлов

```
vpn_bot/
├── main_bot.py              # Основной файл бота
├── connect.py               # Модуль подключения VPN
├── vpn_config_generator.py  # Генератор конфигов
├── Profile.py               # Управление профилями
├── requirements.txt         # Зависимости
└── server_scripts/         # Скрипты для сервера
    ├── gen_openvpn.sh      # Генерация OpenVPN
    ├── gen_vless.sh        # Генерация VLESS
    └── revoke_user.sh      # Отзыв конфигов
```

## 7. Безопасность

- Используйте SSH ключи вместо паролей
- Ограничьте доступ к серверу только необходимыми портами
- Регулярно обновляйте сертификаты
- Мониторьте логи подключений 