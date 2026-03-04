import os
import asyncio
import logging
import random
import cv2
import numpy as np
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ultralytics import YOLO

# --- НАСТРОЙКИ ---
TOKEN = "8729886738:AAF7_JkSA_YHh9k5J7NJudBTCkUKHHQBZ6Y"

# Просто вставьте ссылки на ваши каналы сюда
CHANNEL_1_URL = "https://t.me/+6aSOOyoAhUs4NTNk"
CHANNEL_2_URL = "https://t.me/+qqip4xoKuIA4NmQ0"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация нейросети (скачается автоматически при первом запуске)
try:
    model = YOLO('yolov8n.pt') 
except Exception as e:
    print(f"Critial Error: Neural Engine failed to load: {e}")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хакерские декорации
DIVIDER = "--------------------------------"

# Клавиатура с кнопками
def get_sub_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="DARK_SIDE", url=CHANNEL_1_URL))
    builder.row(InlineKeyboardButton(text="DARK_FROUD", url=CHANNEL_2_URL))
    builder.row(InlineKeyboardButton(text="✅ ПОЛУЧИТЬ ДАННЫЕ", callback_data="check_fake"))
    return builder.as_markup()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    photo = FSInputFile("photo.png")  # путь к фото

    welcome_text = (
        "<b>🤖Бот для поиска человека по фото.\n\n"
        "📝Бот анализирует изображение и определяет возможное местоположение человека на основе окружающих объектов, фона, архитектуры, природных элементов и других визуальных деталей."
        "\n\n📸 Отправьте фотографию, чтобы определить возможное местоположение:</b>"
    )

    await message.answer_photo(
        photo=photo,
        caption=welcome_text,
        parse_mode="HTML"
    )

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    # Этап 1: Имитация начала анализа
    status_msg = await message.answer(
        "📷 <b>ПОЛУЧЕНИЕ ИЗОБРАЖЕНИЯ...</b>\n"
        "<code>[██░░░░░░░░░░░░░░░░] 10%</code>",
        parse_mode="HTML"
    )

    # Пути для файлов
    path_in = f"in_{message.from_user.id}.jpg"
    path_out = f"out_{message.from_user.id}.jpg"

    # Скачиваем фото
    file = await bot.get_file(message.photo[-1].file_id)
    await bot.download_file(file.file_path, path_in)

    # Этап 2: Имитация работы нейросети (крутим проценты)
    stages = [
        ("🧠 СКАНИРОВАНИЕ ОБЪЕКТОВ", 35),
        ("🔍 ПОИСК ПО БАЗАМ ДАННЫХ", 65),
        ("🌐 ГЕО-ТРИАНГУЛЯЦИЯ", 90),
        ("💾 ФОРМИРОВАНИЕ ОТЧЕТА", 100)
    ]

    for text, proc in stages:
        await asyncio.sleep(1.2) # Задержка для эффекта реальности
        bar = "█" * (proc // 6) + "░" * (16 - (proc // 6))
        await status_msg.edit_text(
            f"<b>{text}</b>\n<code>[{bar}] {proc}%</code>",
            parse_mode="HTML"
        )

    # Этап 3: РЕАЛЬНАЯ ОБРАБОТКА ФОТО (YOLO + CV2)
    # Загружаем изображение
    img = cv2.imread(path_in)
    
    # Запускаем YOLO для поиска людей (чтобы их исключить)
    results = model(path_in, verbose=False)
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
    # Создаем маску, где есть люди
    for res in results:
        for box in res.boxes:
            if int(box.cls[0]) == 0: # person
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)

    # Находим контуры всего подряд (Canny)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Рисуем контуры только там, где НЕТ людей (маска пустая)
    for cnt in contours:
        if cv2.contourArea(cnt) > 50: # игнорируем мелкий шум
            # Получаем центр контура
            M = cv2.moments(cnt)
            if M["m00"] > 0:
                cx, cy = int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])
                
                # Если центр контура попадает на область БЕЗ человека (mask == 0)
                if mask[cy, cx] == 0:
                    # Рисуем красный контур (BGR: 0, 0, 255)
                    cv2.drawContours(img, [cnt], -1, (0, 0, 255), 2)

    # Сохраняем обработанное фото
    cv2.imwrite(path_out, img)
    
    # Удаляем сообщение о загрузке
    await status_msg.delete()

    # Этап 4: Финальный байт с фото и зашифрованными данными
    caption = (
        f"<b>✅ ОТЧЕТ СКАНИРОВАНИЯ ГОТОВ</b>\n"
        f"{DIVIDER}\n"
        f"📍 <b>Локация:</b> <code>[******]</code>\n"
        f"📂 <b>Метаданные:</b> <code>[****** ****** ********]</code>\n"
        f"🆔 <b>Объект:</b> Идентифицирован\n"
        f"{DIVIDER}\n"
        f"⚠️ <b>ДОСТУП ОГРАНИЧЕН.</b> Для получения полной геолокации, "
        f"необходимо подписаться на каналы:"
    )
    
    # Отправляем ОБРАБОТАННОЕ фото с контурами
    await message.answer_photo(
        types.FSInputFile(path_out), 
        caption=caption, 
        reply_markup=get_sub_keyboard(),
        parse_mode="HTML"
    )

    # Удаляем временные файлы
    if os.path.exists(path_in): os.remove(path_in)
    if os.path.exists(path_out): os.remove(path_out)

# Обработка нажатия на кнопку "Дешифровать данные" (просто выдаем ошибку)
@dp.callback_query(F.data == "check_fake")
async def check_callback(callback: types.CallbackQuery):
    await callback.answer(
        "❌ ОШИБКА: Подписки не обнаружены! \n\n"
        "Система обновит данные через 5-10 минут. "
        "Убедитесь, что вы подписаны на оба канала.", 
        show_alert=True
    )

async def main():
    print("Бот запущен. Ждет фото...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")



# import os
# import random
# import cv2
# import numpy as np
# import asyncio
# import logging
# from aiogram import Bot, Dispatcher, types, F
# from aiogram.filters import Command
# from ultralytics import YOLO
# from aiogram.types import FSInputFile
# # Настройка логирования
# logging.basicConfig(level=logging.INFO)

# TOKEN = "8729886738:AAF7_JkSA_YHh9k5J7NJudBTCkUKHHQBZ6Y" 

# try:
#     model = YOLO('yolov8n.pt') 
# except Exception as e:
#     print(f"Critial Error: Neural Engine failed to load: {e}")

# bot = Bot(token=TOKEN)
# dp = Dispatcher()

# # Хакерские декорации
# DIVIDER = "--------------------------------"
# PREFIX = "<code>[SYSTEM]</code>"

# @dp.message(Command("start"))
# async def start_cmd(message: types.Message):
#     photo = FSInputFile("photo.png")  # путь к фото

#     welcome_text = (
#         "<b>🤖Бот для поиска человека по фото.\n\n"
#         "📝Бот анализирует изображение и определяет возможное местоположение человека на основе окружающих объектов, фона, архитектуры, природных элементов и других визуальных деталей."
#         "\n\n📸 Отправьте фотографию, чтобы определить возможное местоположение:</b>"
#     )

#     await message.answer_photo(
#         photo=photo,
#         caption=welcome_text,
#         parse_mode="HTML"
#     )

# @dp.message(F.photo)
# async def handle_photo(message: types.Message):
#     status_msg = await message.answer(
#         "📷 <b>ИНИЦИАЛИЗАЦИЯ ВИЗУАЛЬНОГО АНАЛИЗА</b>\n"
#         "<code>[██░░░░░░░░░░░░░░░░] 10% — Получение изображения</code>",
#         parse_mode="HTML"
#     )

#     path_in = f"in_{message.from_user.id}.jpg"
#     path_out = f"out_{message.from_user.id}.jpg"

#     file = await bot.get_file(message.photo[-1].file_id)
#     await bot.download_file(file.file_path, path_in)

#     await asyncio.sleep(1.2)
#     await status_msg.edit_text(
#         "🧠 <b>АНАЛИЗ ИЗОБРАЖЕНИЯ</b>\n"
#         "<code>[████░░░░░░░░░░░░░░] 25% — Нормализация и улучшение качества</code>",
#         parse_mode="HTML"
#     )

#     await asyncio.sleep(1.2)
#     await status_msg.edit_text(
#         "🔍 <b>ВЫДЕЛЕНИЕ ОБЪЕКТОВ</b>\n"
#         "<code>[███████░░░░░░░░░░] 45% — Обнаружение ключевых элементов</code>",
#         parse_mode="HTML"
#     )

#     await asyncio.sleep(1.2)
#     await status_msg.edit_text(
#         "📦 <b>КЛАССИФИКАЦИЯ ОБЪЕКТОВ</b>\n"
#         "<code>[███████████░░░░░] 65% — Формирование сигнатур объектов</code>",
#         parse_mode="HTML"
#     )

#     await asyncio.sleep(1.2)
#     await status_msg.edit_text(
#         "🗄 <b>ПОИСК В БАЗЕ ДАННЫХ</b>\n"
#         "<code>[██████████████░░] 85% — Сравнение с существующими записями</code>",
#         parse_mode="HTML"
#     )

#     await asyncio.sleep(1.2)
#     await status_msg.edit_text(
#         "✅ <b>АНАЛИЗ ЗАВЕРШЁН</b>\n"
#         "<code>[████████████████] 100% — Совпадения обработаны</code>",
#         parse_mode="HTML"
#     )

#     # ОБРАБОТКА
#     img = cv2.imread(path_in)
#     results = model(path_in, verbose=False)
#     mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
#     for res in results:
#         for box in res.boxes:
#             if int(box.cls[0]) == 0: # person
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)

#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     edges = cv2.Canny(gray, 50, 150)
#     contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#     for cnt in contours:
#         if cv2.contourArea(cnt) > 50:
#             M = cv2.moments(cnt)
#             if M["m00"] > 0:
#                 cx, cy = int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])
#                 if mask[cy, cx] == 0:
#                     cv2.drawContours(img, [cnt], -1, (0, 0, 255), 2) # (0, 0, 255) — это чистый красный в BGR

#     cv2.imwrite(path_out, img)

#     await status_msg.edit_text(
#         f"📍 <b>ГЕО-ЛОКАЦИЯ...</b>\n"
#         f"<code>[####################] 100% - Шифрование завершено</code>",
#         parse_mode="HTML"
#     )

#     # ОТПРАВКА
#     caption = (
#         f"<b>✅ ОТЧЕТ СКАНИРОВАНИЯ</b>\n"
#         f"{DIVIDER}\n"
#         f"👤 <code>Био-цели: Исключены</code>\n"
#         f"🏗 <code>Инфраструктура: Выделена</code>\n"
#         f"🌐 <code>Геолокация: Австрия, Вена</code>"
#     )
    
#     await message.answer_photo(
#         types.FSInputFile(path_out), 
#         caption=caption, 
#         parse_mode="HTML"
#     )
    
# # Генерируем случайное смещение в радиусе центра Вены
#     # 0.01 градуса ~ это примерно 1 км, что создает реалистичный разброс
#     lat = 48.2082 + random.uniform(-0.005, 0.005)
#     lon = 16.3738 + random.uniform(-0.005, 0.005)
    
#     # Отправляем локацию пользователю
#     await message.answer_location(latitude=lat, longitude=lon)
    
#     # Лог для консоли (опционально, для отладки)
#     print(f"Target locked: Vienna Sector [{lat}, {lon}]")

#     await status_msg.delete()

#     os.remove(path_in)
#     os.remove(path_out)

# async def main():
#     print("Terminal Active...")
#     await dp.start_polling(bot)

# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except (KeyboardInterrupt, SystemExit):

#         print("Terminal Offline.")
