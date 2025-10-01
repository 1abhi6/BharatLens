# hashing (passlib)
# from passlib.context import CryptContext
from passlib.hash import argon2

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return argon2.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return argon2.hash(password)
