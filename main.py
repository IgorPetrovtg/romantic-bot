import datetime
import json
import logging
import os
import random

from dotenv import load_dotenv
from telegram import Update
from telegram.error import Forbidden, TelegramError
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не задан BOT_TOKEN в переменных окружения или файле .env")

USERS_FILE = "users.json"
TZ_ALMATY = datetime.timezone(datetime.timedelta(hours=5))

MORNING_MESSAGES = [
    "Доброе утро ❤️ Пусть твой день будет таким же прекрасным, как ты.",
    "Я счастлив просто знать, что ты есть в моей жизни 🌸",
    "Ты делаешь мой мир теплее одним своим присутствием 💕",
    "Каждый день я влюбляюсь в тебя ещё сильнее ❤️",
    "Ты — мой уют, спокойствие и счастье 🌷",
    "Пусть сегодня у тебя всё получится ✨ Я в тебя верю.",
    "Даже самый тяжёлый день становится легче благодаря тебе ❤️",
    "Ты самое красивое, что случилось со мной 💫",
    "Я скучаю по тебе даже когда ты рядом ❤️",
    "Спасибо тебе за тепло и заботу 🌹",
    "Хочу чтобы ты чаще улыбалась 😊",
    "Ты вдохновляешь меня становиться лучше ❤️",
    "Пусть этот день принесёт тебе радость 🌸",
    "Ты — мой человек ❤️",
    "Мне спокойно, когда я думаю о тебе 🌙",
    "Ты очень важна для меня 💕",
    "Каждое утро хочется начинать с мысли о тебе ☀️",
    "Пусть у тебя сегодня будет много поводов улыбнуться ❤️",
    "Я очень ценю всё, что ты делаешь 🌷",
    "Ты делаешь этот мир красивее ✨",
    "Я люблю твою улыбку ❤️",
    "Пусть сегодняшний день будет лёгким и добрым 🌸",
    "Ты — лучшее, что было в моей жизни 💕",
    "Иногда мне кажется, что ты настоящее чудо ❤️",
    "Спасибо судьбе за тебя 🌹",
    "Ты приносишь в мою жизнь свет ☀️",
    "Я всегда рядом мысленно и сердцем ❤️",
    "Ты заслуживаешь самого лучшего 🌷",
    "Надеюсь, сегодня ты почувствуешь, как сильно тебя любят 💕",
]

NIGHT_MESSAGES = [
    "Спокойной ночи ❤️ Пусть тебе снятся только хорошие сны.",
    "Сладких снов, родная 🌙 Отдыхай и набирайся сил.",
    "Пусть эта ночь принесёт тебе покой и самые тёплые сны ✨",
]


def load_users() -> list[int]:
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_users(users: list[int]) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.message:
        return

    chat_id = update.effective_chat.id
    users = load_users()

    if chat_id not in users:
        users.append(chat_id)
        save_users(users)

    await update.message.reply_text(
        "Привет ❤️ Теперь я буду отправлять тебе тёплые слова каждый день.\n"
        "Если захочешь приостановить рассылку, нажми /stop."
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.message:
        return

    chat_id = update.effective_chat.id
    users = load_users()

    if chat_id in users:
        users.remove(chat_id)
        save_users(users)
        await update.message.reply_text(
            "Ежедневные сообщения отключены. Чтобы вернуть их, напиши /start 🌸"
        )
    else:
        await update.message.reply_text("Ты и так не подписан(а) на рассылку.")


async def broadcast_message(context: ContextTypes.DEFAULT_TYPE, pool: list[str]) -> None:
    users = load_users()
    if not users:
        return

    text = random.choice(pool)
    active_users = []
    changed = False

    for chat_id in users:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            active_users.append(chat_id)
        except Forbidden:
            logger.info("Пользователь %s заблокировал бота. Удаляю из списка.", chat_id)
            changed = True
        except TelegramError as err:
            logger.warning("Ошибка отправки пользователю %s: %s", chat_id, err)
            active_users.append(chat_id)

    if changed:
        save_users(active_users)


async def send_morning_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    await broadcast_message(context, MORNING_MESSAGES)


async def send_night_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    await broadcast_message(context, NIGHT_MESSAGES)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()

    if "люблю" in text:
        await update.message.reply_text("И я тебя люблю ❤️")
    elif "привет" in text:
        await update.message.reply_text("Привет 🌸")
    else:
        await update.message.reply_text("Ты самый прекрасный человек ❤️")


def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    if app.job_queue:
        app.job_queue.run_daily(
            send_morning_message,
            time=datetime.time(hour=9, minute=0, tzinfo=TZ_ALMATY),
        )
        app.job_queue.run_daily(
            send_night_message,
            time=datetime.time(hour=22, minute=0, tzinfo=TZ_ALMATY),
        )

    logger.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
