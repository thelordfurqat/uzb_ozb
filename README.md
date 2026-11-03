# Özbek alifbo Telegram bot

Python + Aiogram 3 asosidagi ommaviy Telegram transliteratsiya boti.

## Imkoniyatlar

- Kirill → amaldagi lotin
- Kirill → yangi lotin (ÖZ)
- Amaldagi lotin → yangi lotin (ÖZ)
- Yangi lotin → amaldagi lotin
- Yangi lotin → kirill
- Amaldagi lotin → kirill
- Avtomatik rejim
- DOCX, PDF, XLSX, PPTX, TXT va RTF fayllarini qayta işlaş
- Foydalanuvçi uçun alohida tanlangan transliteratsiya rejimi
- Fayllar vaqtinçalik papkada qayta işlanadi va jarayon tugagaç öçiriladi

## 1. Telegram bot tokenini oliş

1. Telegramda `@BotFather`ni oçing.
2. `/newbot` yuboring.
3. Bot nomi va username kiriting.
4. BotFather bergan tokenni nusxalang.

Tokenni heç kimga yubormang va ommaviy GitHub repozitoriyiga joylamang.

## 2. Lokal işga tuşiriş

Python 3.11 yoki 3.12 tavsiya qilinadi.

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Kutubxonalarni örnating:

```bash
pip install -r requirements.txt
```

`.env.example` faylidan `.env` nusxa yarating va tokenni kiriting:

```env
BOT_TOKEN=123456:ABC...
```

Botni işga tuşiring:

```bash
python bot.py
```

## 3. Railway orqali cloud hosting

1. GitHub’da yangi private yoki public repository yarating.
2. Uşbu papkadagi fayllarni repozitoriyga yuklang.
3. Railway’da akkaunt oçib, **New Project → Deploy from GitHub Repo** ni tanlang.
4. Repozitoriyingizni ulang.
5. Railway loyihasining **Variables** bölimiga quyidagini qöşing:

```env
BOT_TOKEN=BotFather_bergan_token
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=8
```

6. Railway Dockerfile orqali avtomatik build va deploy qiladi.
7. Deploy loglarida `Bot işga tuşmoqda` yozuvi çiqqaç, Telegramda botga `/start` yuboring.

Bu bot polling rejimida işlaydi; alohida domen yoki webhook sozlaş şart emas. Railway’da doimiy işlaydigan service/worker kerak. Tarif va bepul limitlar platforma qoidalariga boğliq.

## 4. Fayllar böyiça muhim çeklovlar

- Telegramdan yuklab oliş uçun fayl hajmi 19 MB bilan çeklangan.
- PDF: faqat içidan matn ajratib oliş mumkin bölgan PDFlar. Skanerlangan PDF uçun OCR yöq.
- PDF natijasi qayta yaratiladi: asl sahifa dizayni, rasmlar, jadvallar va maket töliq saqlanmaydi.
- DOCX va PPTX: matn ögiriladi; bir paragraf içida bir neçta turli şrift/run işlatilgan bölsa, ayrim formatlaş birinçi run uslubiga birlaşişi mumkin.
- XLSX: matnli kataklar ögiriladi, formulalar özgartirilmaydi.
- RTF: matn saqlanadi, murakkab formatlaş yöqolişi mumkin.
- Hujjatlar qayta işlaş tugagaç vaqtinçalik papkadan öçiriladi. Bot matn va fayllarni doimiy bazaga yozmaydi.

## 5. Loyiha tuzilişi

```text
uzbek_alpha_telegram_bot/
├── bot.py
├── transliterator.py
├── file_converter.py
├── requirements.txt
├── Dockerfile
├── railway.json
├── Procfile
├── .env.example
├── .gitignore
└── README.md
```

## 6. Xavfsizlik

- `.env` faylini Git’ga yubormang.
- Bot tokeni oşkor bölsa, BotFather orqali tokenni yangilang.
- Ommaviy botda katta fayllar va spamdan himoya uçun limit mavjud.
- Işlab çiqariş muhitida loglarni va hosting sarfini kuzatib boring.
