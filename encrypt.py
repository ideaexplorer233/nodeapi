from datetime import datetime, timedelta

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

# Because PyCharm think jose is not python-jose,
# So we ignore error here.
# noinspection PyPackageRequirements
from jose import JWTError, jwt
# noinspection PyPackageRequirements
from jose.exceptions import ExpiredSignatureError

from passlib.context import CryptContext

import controller
from models import User

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_TIME = timedelta(days=7)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/account/login")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def authenticate(name_or_email: str, password: str) -> User | None:
    user = await controller.get_user(name_or_email)
    if user is None:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta = ACCESS_TOKEN_EXPIRE_TIME):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_token_data(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        data: str = payload.get("sub")
        if data is None:
            raise credentials_exception
        return data
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception


async def get_current_user(token_data: str = Depends(get_token_data)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        session_uuid, user_id = token_data.split(":", 1)
    except ValueError:
        raise credentials_exception
    user = await controller.get_user_by_id(int(user_id))
    if user is None:
        raise credentials_exception
    return user
