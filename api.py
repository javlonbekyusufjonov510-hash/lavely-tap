import os
import hmac
import hashlib
import json
import time

from urllib.parse import parse_qsl
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SECRET_KEY")

if not TOKEN or not URL or not KEY:
    raise ValueError("Environment variables missing")

supabase = create_client(URL, KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://javlonbekyusufjonov510-hash.github.io"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TelegramData(BaseModel):
    initData: str

def check_telegram(init_data):
    values = dict(parse_qsl(init_data))
    received_hash = values.pop("hash", None)

    if not received_hash:
        raise HTTPException(401, "Telegram tekshiruvi xato")

    data_check = "\n".join(
        f"{key}={value}" for key, value in sorted(values.items())
    )

    secret = hmac.new(
        b"WebAppData", TOKEN.encode(), hashlib.sha256
    ).digest()

    calculated = hmac.new(
        secret, data_check.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        raise HTTPException(401, "Telegram ma'lumoti noto'g'ri")

    auth_date = int(values.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        raise HTTPException(401, "Telegram sessiyasi eskirgan")

    user = json.loads(values["user"])
    return int(user["id"])

@app.get("/")
def home():
    return {"status": "LAVELY TAP API ishlayapti!"}

@app.post("/tap")
def tap(data: TelegramData):
    telegram_id = check_telegram(data.initData)
    result = supabase.rpc(
        "tap_player",
        {"p_telegram_id": telegram_id}
    ).execute()
    return result.data

@app.post("/balance")
def balance(data: TelegramData):
    telegram_id = check_telegram(data.initData)
    result = (
        supabase.table("players")
        .select("balance,taps,cooldown_until")
        .eq("telegram_id", telegram_id)
        .execute()
    )

    if not result.data:
        return {"balance": 0, "taps": 0, "cooldown_until": None}

    return result.data[0]
@app.post("/referral")
def referral(data: TelegramData, referrer_id: int):
    telegram_id = check_telegram(data.initData)

    result = supabase.rpc(
        "register_referral",
        {
            "p_telegram_id": telegram_id,
            "p_referrer_id": referrer_id
        }
    ).execute()

    return result.data
