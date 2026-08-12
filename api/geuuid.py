import uuid
import hashlib


def get_uuid():
    mac = uuid.getnode()
    mac_address = ':'.join(['{:02x}'.format((mac >> i) & 0xff) for i in range(0, 48, 8)])
    _uuid = hashlib.sha256(mac_address.encode()).hexdigest()
    return _uuid


if __name__ == '__main__':
    print(get_uuid())
