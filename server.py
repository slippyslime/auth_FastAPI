# Fast API Server
from typing import Optional
import base64
import hmac
import hashlib
import json

from fastapi import FastAPI, Form, Cookie, Body
from fastapi.responses import Response


app = FastAPI()

SECRET_KEY = "3950ab414263046e38b067b2e5d35772d04182a0700aaf9a58fb3832f0292eb2"
PASSWORD_SALT = "4aa402cadd06731b0bd006998fee48dfb86f7e29cceff7302962eaaa042e7d01"


def sign_data(data: str) -> str:
    """Возвращает подписанные данные data"""
    return hmac.new(
        SECRET_KEY.encode(),
        msg=data.encode(),
        digestmod=hashlib.sha256
    ).hexdigest().upper()


def get_username_from_signed_string(username_signed: str) -> Optional[str]:
    username_base64, sign = username_signed.split('.')
    username = base64.b64decode(username_base64.encode()).decode()
    valid_sign = sign_data(username)
    if hmac.compare_digest(valid_sign, sign):
        return username


def verify_password(username: str, password: str) -> bool:
    password_hash = hashlib.sha256( (password + PASSWORD_SALT).encode() )\
        . hexdigest().lower()
    stored_password_hash = users[username]["password"].lower()
    return password_hash == stored_password_hash


users = {
    "alexey@user.com": {
        "name": "Алексей",
        "password": "362513bf3686ddee122d032da19e57f32447ae775f59f430099523c97e73fdb9",
        "balance": 100_000
    },
    "petr@user.com": {
        "name": "Пётр",
        "password": "ac958ead09423ab2aa750fb61f16e6b082962dac7ae00a24187babc24749f2e5",
        "balance": 555_555
    }
}


@app.get("/")
def index_page(username: Optional[str] = Cookie(default=None)):
    with open('templates/login.html', 'r') as f:
        login_page = f.read()
    if not username:
        return Response(login_page, media_type='text/html')
    valid_username = get_username_from_signed_string(username)
    if not valid_username:
        response = Response(login_page, media_type='text/html')
        response.delete_cookie(key='username')
        return response
    try:
        user = users[valid_username]
    except KeyError:
        response = Response(login_page, media_type='text/html')
        response.delete_cookie(key='username')
        return response
    return Response(
        f"Привет, {users[valid_username]['name']}!<br />"
        f"Баланс: {users[valid_username]['balance']}",
        media_type='text/html')


@app.post("/login")
def process_login_page(username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if not user or not verify_password(username, password):
        return Response(
            json.dumps({
                "succes": False,
                "message": "Я вас не знаю!"
            }),
            media_type="application/json")
    
    response = Response(
        json.dumps({
            "succes": True,
            "message": f"Привет, {user['name']}!<br />Баланс: {user['balance']}"
        }),
        media_type='application/json')
    
    username_signed = base64.b64encode(username.encode()).decode() + '.' + sign_data(username)
    response.set_cookie(key="username", value=username_signed)
    return response
