from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt.exceptions import InvalidTokenError
import os
from dotenv import load_dotenv
from dal_users import du_get_user_by_user_name

DB_NAME_USERS = "users.db"

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM","SHA256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES",60))

bearer_scheme = HTTPBearer()


def create_access_token(user_name: str) -> str:
    user = du_get_user_by_user_name(user_name,DB_NAME_USERS)

    if user is None:
        raise HTTPException(status_code=400,detail="Invalid user_name")

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_name,
        "administrator": False,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme))->dict|None:
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_name = payload.get("sub")

    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    if not user_name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = du_get_user_by_user_name(user_name,DB_NAME_USERS)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user_name or password",
        )

    return user
# token = create_access_token(user_name="ariel")
# print(token)
# rev_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
# print(rev_token)