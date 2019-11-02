import binascii

from cryptography.hazmat import backends
from cryptography.hazmat.primitives.ciphers import (
    Cipher,
    algorithms,
    modes,
)

__all__ = [
    'aes_cbc_encrypt',
    'aes_cbc_decrypt',
    'aes_ecb_encrypt',
    'aes_ecb_decrypt',
    'rsa_encrypt',
]


def aes_cbc_encrypt(plain_text: bytes, key: bytes, iv: bytes) -> bytes:
    return aes_encrypt(plain_text, key, modes.CBC(iv))


def aes_cbc_decrypt(cipher_text: bytes, key: bytes, iv: bytes) -> bytes:
    return aes_decrypt(cipher_text, key, modes.CBC(iv))


def aes_ecb_encrypt(plain_text: bytes, key: bytes) -> bytes:
    return aes_encrypt(plain_text, key, modes.ECB())


def aes_ecb_decrypt(cipher_text: bytes, key: bytes) -> bytes:
    return aes_decrypt(cipher_text, key, modes.ECB())


def aes_encrypt(plain_text: bytes, key: bytes, mode: modes) -> bytes:
    padding = 16 - len(plain_text) % 16
    plain_text = plain_text + bytearray([padding] * padding)
    backend = backends.default_backend()
    cipher = Cipher(algorithms.AES(key), mode, backend=backend)
    encryptor = cipher.encryptor()
    return cipher.encryptor().update(plain_text) + encryptor.finalize()


def aes_decrypt(cipher_text: bytes, key: bytes, mode: modes) -> bytes:
    backend = backends.default_backend()
    cipher = Cipher(algorithms.AES(key), mode, backend=backend)
    decryptor = cipher.decryptor()
    plain_text = decryptor.update(cipher_text) + decryptor.finalize()
    return plain_text[:-ord(plain_text[len(plain_text) - 1:])]


def rsa_encrypt(plain_text: bytes, modulus: str, exponent: int) -> str:
    rs = pow(int(binascii.hexlify(plain_text), 16), exponent, int(modulus, 16))
    return format(rs, "x").zfill(256)
