# JARVIS OS V2 — tez boshlash (Windows 11)

## 1. O‘rnatish

1. ZIP faylni alohida papkaga oching.
2. `scripts\setup_jarvis.bat` faylini ishga tushiring.
3. O‘rnatish tugagach, `scripts\run_jarvis.bat` ni ishga tushiring.

Yoki VS Code terminalida:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
python main.py --no-clap
```

## 2. API kalit

`.env` fayli loyihada saqlangan. `GEMINI_API_KEY=` qatoriga Google AI Studio kalitini o‘zingiz kiriting yoki JARVIS ochilganda setup oynasiga kiriting. Haqiqiy kalitni ZIP yoki GitHub’ga yuklamang.

## 3. Foydali buyruqlar

```powershell
jarvis --health
jarvis --enable-autostart
jarvis --disable-autostart
jarvis --no-clap
```

`--enable-autostart` Windows foydalanuvchi hisobiga kirilganda JARVIS’ni ishga tushiradi. Tray menyusida ham “Start with Windows” bandi mavjud.

## 4. Ovoz va wake-word

Oddiy ovozli rejim JARVIS oynasi ochilgach ishlaydi. Mahalliy “Hey JARVIS” rejimi ixtiyoriy: `openwakeword` va `onnxruntime` o‘rnatilishi va `.env` ichida `JARVIS_WAKE_WORD_ENABLED=1` hamda `JARVIS_WAKE_MODEL=hey_jarvis` deb ko‘rsatilishi mumkin (yoki lokal model fayli yo‘li beriladi). openWakeWord tanlangan modelni birinchi ishga tushirishda internet orqali yuklashi mumkin. Wake-word aniqlash lokal bajariladi; shundan keyingina Gemini Live sessiyasi ishga tushadi.

## 5. Xavfsizlik

- AI yozgan ixtiyoriy Python kod avtomatik bajarilmaydi.
- Code Helper / Dev Agent orqali kodni ishga tushirish standart holatda o‘chiq. Faqat kodni ko‘rib chiqqandan keyin `.env` ichida `JARVIS_ENABLE_CODE_EXECUTION=1` qilib yoqing. Bu sandbox emas; kod sizning Windows hisobingiz huquqlari bilan ishlaydi.
- O‘chirish, xabar yuborish, dastur o‘rnatish kabi xavfli amallar tasdiqsiz bajarilmaydi.
- Mikrofon va kamera imkoniyatlarini o‘zingiz boshqaring; wake-word rejimi standart holatda o‘chiq.

## 6. Tekshiruv

```powershell
python -m compileall -q .
python -m pytest tests/test_security.py tests/test_phase_features.py -q
```

Barcha testlar o‘tishi Windows qurilmadagi mikrofon, Gemini, kamera yoki EXE paketini avtomatik tasdiqlamaydi. Ularni alohida tekshiring.
