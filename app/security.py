import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

ENCRYPTION_KEY = os.getenv("DATASYNC_ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise RuntimeError(
        "DATASYNC_ENCRYPTION_KEY is not configured."
    )

fernet = Fernet(ENCRYPTION_KEY.encode())


def encrypt_value(value: str) -> str:
    return fernet.encrypt(
        value.encode()
    ).decode()


def decrypt_value(value: str) -> str:
    return fernet.decrypt(
        value.encode()
    ).decode()