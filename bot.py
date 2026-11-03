import asyncio
import logging
import os
import re
import tempfile
import time
from pathlib import Path
from collections import defaultdict, deque

from aiogram import Bot, Dispatçer, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from dotenv import load_dotenv

from transliterator import convert, MODES
from file_converter import convert_file, SUPPORTED_EXTENSIONS, MAX_FILE_BYTES

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("BOT_TOKEN .env faylida körsatilmagan.")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("uzbek-alpha-bot")

bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatçer()

USER_MODE = defaultdict(lambda: "auto")
USER_RATE = defaultdict(deque)
MAX_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "8"))

MODE_LABELS = {
    "auto": "Avtomatik",
    "cyrToOld": "Кирилл → O‘Z",
    "cyr": "Кирилл → ÖZ",
    "old": "O‘Z → ÖZ",
    "newToOld": "ÖZ → O‘Z",
    "newToCyr": "ÖZ → Кирилл",
    "oldToCyr": "O‘Z → Кирилл",
}
LABEL_TO_MODE = {v: k for k, v in MODE_LABELS.items()}

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Avtomatik")],
            [KeyboardButton(text="Кирилл → ÖZ"), KeyboardButton(text="O‘Z → ÖZ")],
            [KeyboardButton(text="ÖZ → O‘Z"), KeyboardButton(text="ÖZ → Кирилл")],
            [KeyboardButton(text="Кирилл → O‘Z"), KeyboardButton(text="O‘Z → Кирилл")],
            [KeyboardButton(text="ℹ️ Yordam")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Matn yuboring yoki fayl biriktiring…",
    )

def allowed(user_id: int) -> bool:
    now = time.monotonic()
    q = USER_RATE[user_id]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= MAX_REQUESTS_PER_MINUTE:
        return False
    q.append(now)
    return True

def help_text() -> str:
    return (
        "<b>Özbek alifbo bot</b>\n\n"
        "Matn yuboring yoki DOCX, PDF, XLSX, PPTX, TXT, RTF faylini biriktiring.\n\n"
        "<b>Rejimlar:</b>\n"
        "• Avtomatik — kirill va amaldagi lotinni yangi lotinga ögiradi.\n"
        "• Кирилл → ÖZ\n"
        "• O‘Z → ÖZ\n"
        "• ÖZ → O‘Z\n"
        "• ÖZ → Кирилл\n"
        "• O‘Z → Кирилл\n\n"
        "Fayl yuborişdan oldin kerakli rejimni tanlang. Natija alohida fayl sifatida qaytariladi.\n\n"
        "PDF böyiça: matnli PDF fayllari qayta işlanadi. Skanerlangan, faqat rasm körinişidagi PDF hozirça OCR qilinmaydi.\n"
        "Hujjatlar qayta işlaş vaqtida vaqtinçalik saqlanadi va iş tugagaç öçiriladi."
    )

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Assalomu alaykum!\n\n"
        "<b>Özbek alifbo bot</b>ga xuş kelibsiz.\n"
        "Matn yoki hujjat yuboring. Avval kerakli transliteratsiya yönalişini tanlaşingiz mumkin.",
        reply_markup=main_keyboard(),
    )

@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(help_text(), reply_markup=main_keyboard())

@dp.message(F.text.in_(list(LABEL_TO_MODE.keys())))
async def select_mode(message: Message):
    mode = LABEL_TO_MODE[message.text]
    USER_MODE[message.from_user.id] = mode
    await message.answer(f"Rejim tanlandi: <b>{MODE_LABELS[mode]}</b>\nEndi matn yoki fayl yuboring.")

@dp.message(F.text == "ℹ️ Yordam")
async def help_button(message: Message):
    await message.answer(help_text(), reply_markup=main_keyboard())

@dp.message(F.document)
async def handle_document(message: Message):
    if not allowed(message.from_user.id):
        await message.answer("Sörovlar juda tez yuborilmoqda. Bir daqiqadan keyin qayta urinib köring.")
        return

    doc = message.document
    filename = doc.file_name or "document"
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        await message.answer("Bu fayl turi qöllab-quvvatlanmaydi. DOCX, PDF, XLSX, PPTX, TXT yoki RTF yuboring.")
        return
    if doc.file_size and doc.file_size > MAX_FILE_BYTES:
        await message.answer("Fayl hajmi 19 MB dan oşmasligi kerak.")
        return

    status = await message.answer("Fayl qabul qilindi. Qayta işlanmoqda…")
    in_path = None
    out_path = None
    try:
        with tempfile.TemporaryDirectory(prefix="uzalpha_") as td:
            in_path = Path(td) / Path(filename).name
            out_path = Path(td) / f"{Path(filename).stem}_transliteratsiya{ext}"
            telegram_file = await bot.get_file(doc.file_id)
            await bot.download_file(telegram_file.file_path, destination=in_path)

            mode = USER_MODE[message.from_user.id]
            result_info = await asyncio.to_thread(convert_file, in_path, out_path, mode)

            caption = (
                f"✅ Tayyor!\n"
                f"Yönaliş: <b>{MODE_LABELS[mode]}</b>\n"
                f"Format: <b>{ext.upper()[1:]}</b>"
            )
            if result_info.get("note"):
                caption += f"\n\n<i>{result_info['note']}</i>"

            await message.answer_document(
                document=FSInputFile(out_path),
                caption=caption,
            )
        await status.delete()
    except Exception as exc:
        log.exception("File conversion failed")
        await status.edit_text(
            "Faylni qayta işlaşda xatolik yuz berdi.\n"
            f"<code>{escape_html(str(exc)[:700])}</code>\n\n"
            "Agar PDF bölsa, uning içida tanlanadigan matn borligini tekşiring."
        )

def escape_html(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

@dp.message(F.text)
async def handle_text(message: Message):
    if not allowed(message.from_user.id):
        await message.answer("Sörovlar juda tez yuborilmoqda. Bir daqiqadan keyin qayta urinib köring.")
        return
    text = message.text or ""
    if len(text) > 35000:
        await message.answer("Matn juda uzun. Iltimos, 35 000 belgidan kiçik qismlarga bölib yuboring.")
        return
    mode = USER_MODE[message.from_user.id]
    result = convert(text, mode)
    if not result:
        await message.answer("Ögiriş uçun matn yuboring.")
        return
    if len(result) <= 4000:
        await message.answer(f"<pre>{escape_html(result)}</pre>")
    else:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as f:
            f.write(result)
            path = Path(f.name)
        try:
            await message.answer_document(FSInputFile(path), caption=f"✅ Tayyor. Rejim: {MODE_LABELS[mode]}")
        finally:
            path.unlink(missing_ok=True)

@dp.message()
async def fallback(message: Message):
    await message.answer("Matn yuboring yoki qöllab-quvvatlanadigan hujjatni biriktiring.", reply_markup=main_keyboard())

async def main():
    log.info("Bot işga tuşmoqda")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
