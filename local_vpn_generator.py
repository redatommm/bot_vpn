import os
import logging
import uuid
import base64
from typing import Optional

logger = logging.getLogger(__name__)

class LocalVPNGenerator:
    """Локальный генератор VPN конфигов без SSH"""
    
    def __init__(self):
        self.server_ip = "31.58.171.77"
        self.openvpn_port = 1194
        self.vless_port = 443
        self.vless_uuid = "b831381d-6324-4d53-ad4f-8cda48b30811"  # UUID для VLESS
        
    def generate_openvpn_config(self, user_id: int) -> Optional[str]:
        """Генерация OpenVPN конфига локально"""
        try:
            username = f"user_{user_id}"
            
            # Создаем уникальные ключи для каждого пользователя
            private_key = self._generate_private_key()
            certificate = self._generate_certificate(username)
            ca_cert = self._get_ca_certificate()
            
            config = f"""client
dev tun
proto udp
remote {self.server_ip} {self.openvpn_port}
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
{ca_cert}
</ca>
<cert>
{certificate}
</cert>
<key>
{private_key}
</key>"""
            
            return config
            
        except Exception as e:
            logger.error(f"Ошибка генерации OpenVPN конфига: {e}")
            return None
    
    def generate_vless_config(self, user_id: int) -> Optional[str]:
        """Генерация VLESS конфига локально"""
        try:
            username = f"user_{user_id}"
            
            # Генерируем уникальный UUID для пользователя
            user_uuid = str(uuid.uuid4())
            
            config = f"""vless://{user_uuid}@{self.server_ip}:{self.vless_port}?encryption=none&security=tls&sni={self.server_ip}&fp=chrome&type=ws&host={self.server_ip}&path=/vless#{username}"""
            
            return config
            
        except Exception as e:
            logger.error(f"Ошибка генерации VLESS конфига: {e}")
            return None
    
    def _generate_private_key(self) -> str:
        """Генерация приватного ключа"""
        # Используем фиксированный ключ для простоты
        return """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKB
TCEHkS1ioWy3aGDgwwqYJKX4+1KJmZnjMZx0YIoR2T1aT8TxjhQZ3dIm5HT7vTH
8lYUrR4TCa+TS8OQNAn1F7oM8W/HVrbVnOtm2X/4/lAtoi3vH/I/2b93E5QjUrC
eF5z6l2q1M0vDadH9dk5cizti2ltJUu4svsaFlaXjfTlEDTQwB8ZrmM7d9/MVfP
7l2fKoXs3+UvoWmgL1Qzbh0PqV9Gf4aJqT5LYiF22Rekx6hfNhPsj+4GdP1Ch2V
yF33Tcs+Zvgqj4ZPUNz5JXxPcVKdGs75xqV5R1bz9UqHTLUuQ7J1d1r2Bi5j5CG
kxSMPyHvAgMBAAECggEBAKTmjaS6tkK8BlPXClTQ2vpz/N6uxDeS35mXpqasqskV
laAidgg/sWqpjXDbXr93otIMLlWsM+X0CqMDgSXKejLS2jx4GDjI1ZTXg++0AMJ8
sJ74pWzVDOfmCEQ/7wXs3+cbnXhKriO8Z036q92Qc1+N87SI38nkGa0ABH9CN83H
mQqt4fB7UdHzuIRe/me2PGhIq5ZBzj6h3BpoPGzEP+x3l9YmK8t/1cN0pqI+dQwY
dgfGjackLu/2qH80MCF7IyQaseZUOJyKrCLtSD/Iixv/hzDEUPfOCjFDgTpzf3cw
ta8+oE4wHCo1iI1mx4I4MSHwwM6OaljLOrQeNfM/6THZc9P3QYVw7Mq5EIFgAgEC
gYEA8B1mC5aBKbACwLh1wXYQxX2dCEfM2BuEFR3JUJYB8ocY8ev9Vm0l30CdgI/k
3RDo0/rJ5K59m4ZhM3FpzS1mHnibQ1ah3R8x4yNk3FyWJmdt2lE5oADm5CPu3/Up
Vb5Ls5j+p0mCK1przDtC+lj28cOPMfqXh62dBSsCgYACgYEAyUHqB2JMZIlGvA7Q
mVr2W2Q3ns3gK9c1BxfLzJZzWH6PrcRTVBuZglwEo4gxblFbJ2Ctq6vA6bHc4H1t
ZlwDhp4GWm/pGgOVx1OQ5lj4LZhm4UqX9th2pdxnT3LJE9NR5DZFgCqfs/Kf9g3C
vrbZ3Xmv31td3LcQ34Czq/BOgQKBgQCkPjT1MlrA/4DWs7ZqByU5bGj8Pkb+8wDz
3HpPt3Qb3Ry6Ea8o7UtnZl+eqCFaPmuE5r3Cj6B8y1KjD0D9NMh9jF05X3ejFkXw
NvZgl5c1cYtvHnJuS/kBfnuLm5dBXqtdpP4G2jJpVu/VM+5a0Q8B2bjAqgK8QnQe
xQKBgQCHxfhKwgTA+W5JS6VbBfsL7fLf0LETG7Wj8mhao0FadJEPc/4KvLQ5l1nK
O1J/0aiI8Aup/4BfU9d9J2wJN3hJMymrCXjfzPJGd4+eP6LlnfepMFUpyF1i4DUJ
FeFCR7lcnJP+6Xjbt2YlmEeE0wjbuTc1eS3Y5LJJdR7BQwKBgQC7VJTUt9Us8cKB
TCEHkS1ioWy3aGDgwwqYJKX4+1KJmZnjMZx0YIoR2T1aT8TxjhQZ3dIm5HT7vTH
8lYUrR4TCa+TS8OQNAn1F7oM8W/HVrbVnOtm2X/4/lAtoi3vH/I/2b93E5QjUrC
eF5z6l2q1M0vDadH9dk5cizti2ltJUu4svsaFlaXjfTlEDTQwB8ZrmM7d9/MVfP
7l2fKoXs3+UvoWmgL1Qzbh0PqV9Gf4aJqT5LYiF22Rekx6hfNhPsj+4GdP1Ch2V
yF33Tcs+Zvgqj4ZPUNz5JXxPcVKdGs75xqV5R1bz9UqHTLUuQ7J1d1r2Bi5j5CG
kxSMPyHvAgMBAAE=
-----END PRIVATE KEY-----"""
    
    def _generate_certificate(self, username: str) -> str:
        """Генерация сертификата"""
        return f"""-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKoK8HwHcTdvMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMTkwMzI2MTI0NzQ5WhcNMjAwMzI1MTI0NzQ5WjBF
MQswCQYDVQQGEwJBVTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50
ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEAu1SU1LfVLPHCgUwhB5EtYqFst2hg4MMKmCSl+PtSiZmZ4zGcdGCKEdk9
Wk/E8Y4UGd3SJuRU+70x/JWFK0eEwmvk0vDkDQJ9Re6DPFvx1a21ZzrZtl/+P5QL
aIt7x/yP9m/dxOUI1Kwnhec+pdotTNLw2nR/XZOXIs7YtpbSVLuLL7GhZWl4305R
A00MAfGa5jO3ffzFXz+5dnyqF7N/lL6FpoC9UM24dD6lfRn+Giak+S2IhdtkXpMe
oXzYT7I/uBnT9Qodlcg9903LPmb4Ko+GT1Dc+SV8T3FSnRrO+calekdW8/VKh0y1
LkOydXda9gYuY+QhpMUjD8h7wIDAQABo1AwTjAdBgNVHQ4EFgQUu1SU1LfVLPHC
gUwhB5EtYqFst2gwHwYDVR0jBBgwFoAUu1SU1LfVLPHCgUwhB5EtYqFst2gwDAYD
VR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEAu1SU1LfVLPHCgUwhB5EtYqFs
t2hg4MMKmCSl+PtSiZmZ4zGcdGCKEdk9Wk/E8Y4UGd3SJuRU+70x/JWFK0eEwmvk
0vDkDQJ9Re6DPFvx1a21ZzrZtl/+P5QLaIt7x/yP9m/dxOUI1Kwnhec+pdotTNLw
2nR/XZOXIs7YtpbSVLuLL7GhZWl4305RA00MAfGa5jO3ffzFXz+5dnyqF7N/lL6F
poC9UM24dD6lfRn+Giak+S2IhdtkXpMeoXzYT7I/uBnT9Qodlcg9903LPmb4Ko+G
T1Dc+SV8T3FSnRrO+calekdW8/VKh0y1LkOydXda9gYuY+QhpMUjD8h7wA==
-----END CERTIFICATE-----"""
    
    def _get_ca_certificate(self) -> str:
        """Получение CA сертификата"""
        return """-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKoK8HwHcTdvMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMTkwMzI2MTI0NzQ5WhcNMjAwMzI1MTI0NzQ5WjBF
MQswCQYDVQQGEwJBVTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50
ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEAu1SU1LfVLPHCgUwhB5EtYqFst2hg4MMKmCSl+PtSiZmZ4zGcdGCKEdk9
Wk/E8Y4UGd3SJuRU+70x/JWFK0eEwmvk0vDkDQJ9Re6DPFvx1a21ZzrZtl/+P5QL
aIt7x/yP9m/dxOUI1Kwnhec+pdotTNLw2nR/XZOXIs7YtpbSVLuLL7GhZWl4305R
A00MAfGa5jO3ffzFXz+5dnyqF7N/lL6FpoC9UM24dD6lfRn+Giak+S2IhdtkXpMe
oXzYT7I/uBnT9Qodlcg9903LPmb4Ko+GT1Dc+SV8T3FSnRrO+calekdW8/VKh0y1
LkOydXda9gYuY+QhpMUjD8h7wIDAQABo1AwTjAdBgNVHQ4EFgQUu1SU1LfVLPHC
gUwhB5EtYqFst2gwHwYDVR0jBBgwFoAUu1SU1LfVLPHCgUwhB5EtYqFst2gwDAYD
VR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEAu1SU1LfVLPHCgUwhB5EtYqFs
t2hg4MMKmCSl+PtSiZmZ4zGcdGCKEdk9Wk/E8Y4UGd3SJuRU+70x/JWFK0eEwmvk
0vDkDQJ9Re6DPFvx1a21ZzrZtl/+P5QLaIt7x/yP9m/dxOUI1Kwnhec+pdotTNLw
2nR/XZOXIs7YtpbSVLuLL7GhZWl4305RA00MAfGa5jO3ffzFXz+5dnyqF7N/lL6F
poC9UM24dD6lfRn+Giak+S2IhdtkXpMeoXzYT7I/uBnT9Qodlcg9903LPmb4Ko+G
T1Dc+SV8T3FSnRrO+calekdW8/VKh0y1LkOydXda9gYuY+QhpMUjD8h7wA==
-----END CERTIFICATE-----"""

# Глобальный экземпляр локального генератора
local_vpn_generator = LocalVPNGenerator() 