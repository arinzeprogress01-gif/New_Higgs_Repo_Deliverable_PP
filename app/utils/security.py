# security.py
from passlib.context import CryptContext

# Create a password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to hash a plain password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Function to verify a password against the hash
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

"""INITIAL ISSUES: Bcrypt package and passlib was initial incompatible and could hash password effectively, giving 'password should not exceed 72 bytes errors'. pip uninstall bcrypt -y and pip uninstall passlib -y done and new packages, pip install bcrypt==4.0.1
pip install passlib[bcrypt]==1.7.4 solved it"""
