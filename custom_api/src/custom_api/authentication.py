import logging
import os
import secrets

import click
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext

logging.getLogger("passlib").setLevel(logging.ERROR)

load_dotenv()

### CLI ###
@click.command()
@click.password_option()
def hash_password_cli(password: str) -> str:
    return hash_password(password=password, show_hashed_password=True)


def hash_password(password: str, show_hashed_password: bool = False) -> str:
    hashed_password: str = PWD_CONTEXT.hash(password)
    if show_hashed_password:
        print(f"Hashed password: {hashed_password}")
    return hashed_password


### Basic Auth ###
PWD_CONTEXT: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECURITY: HTTPBasic = HTTPBasic(description="Security scheme for basic authentication")
HASHED_PASSWORD: str = hash_password(password=os.getenv("CUSTOM_API_PASSWORD", ""))


def verify_user(username: str) -> bool:
    user: str = os.getenv("CUSTOM_API_USER", "")
    return not user or secrets.compare_digest(username, user)


def verify_password(plain_password: str) -> bool:
    if not HASHED_PASSWORD:
        return True
    return PWD_CONTEXT.verify(plain_password, HASHED_PASSWORD)


def verify_basic_auth(credentials: HTTPBasicCredentials = Depends(SECURITY)) -> str:
    correct_username: bool = verify_user(credentials.username)
    correct_password: bool = verify_password(credentials.password)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
