"""Register the configured public webhook URL with Telegram."""

import asyncio
import os

from dotenv import load_dotenv
from telegram import Bot


async def configure() -> None:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
    if not token or not webhook_url:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_URL first")
    async with Bot(token) as bot:
        success = await bot.set_webhook(webhook_url)
        info = await bot.get_webhook_info()
    print(f"Webhook configured: {success}")
    print(f"URL: {info.url}")


if __name__ == "__main__":
    asyncio.run(configure())
