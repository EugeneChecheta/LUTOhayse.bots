#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
# Корневая папка (где лежит скрипт)
ROOT_DIR = Path(__file__).parent.absolute()

# Путь к файлу с таблицей
EXCEL_PATH = ROOT_DIR / "DataBase" / "Materials_log.xlsx"

# Путь к исходным фотографиям (ожидается структура: Photo/Materials/<code>/1.jpg)
SOURCE_PHOTO_ROOT = ROOT_DIR / "Photo" / "Materials"

# Путь для сохранения обработанных фотографий
TARGET_ROOT = ROOT_DIR / "Photo" / "LUTO_Magazine" / "Matrials"

# Параметры оформления
LIGHT_CREAM = (255, 253, 240)          # более светлый и нежный фон
DARK_BROWN = (101, 67, 33)             # тёмно-коричневый текст
FONT_NAME = "arial.ttf"                 # предпочтительный шрифт
FONT_SIZE = 60                           # размер шрифта

# Высота нижней полосы (рамки) для текста
BAR_HEIGHT = 180

# Отступы от краёв полосы по горизонтали (для центрирования текста)
HORIZONTAL_PADDING = 20

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
def get_target_folder_name(material_type: str, color_name: str) -> str:
    """
    Определяет имя папки для сохранения в зависимости от типа материала.
    Для эко-кожи возвращает "Эко-кожа X", где X — первое слово из цвета (Domus, Boom, Nappa).
    Для остальных типов возвращает сам тип.
    """
    if material_type == "Эко-кожа":
        first_word = color_name.split()[0] if color_name.split() else ""
        return f"Эко-кожа {first_word}"
    else:
        return material_type

def draw_centered_text(draw, font, text_lines, bar_rect, color):
    """
    Рисует многострочный текст, центрированный по горизонтали и вертикали
    внутри области bar_rect (x, y, width, height).
    """
    x0, y0, bar_width, bar_height = bar_rect

    # Вычисляем размеры текстового блока
    line_heights = []
    line_widths = []
    total_text_height = 0
    for line in text_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        line_widths.append(line_width)
        line_heights.append(line_height)
        total_text_height += line_height

    # Межстрочный интервал
    spacing = int(0.2 * line_heights[0]) if line_heights else 0
    total_text_height += spacing * (len(text_lines) - 1)

    # Начальная позиция Y для центрирования по вертикали
    y = y0 + (bar_height - total_text_height) // 2

    for i, line in enumerate(text_lines):
        line_width = line_widths[i]
        x = x0 + (bar_width - line_width) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += line_heights[i] + spacing

# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
def main():
    # Проверяем существование файла Excel
    if not EXCEL_PATH.exists():
        print(f"Ошибка: файл {EXCEL_PATH} не найден.")
        sys.exit(1)

    # Читаем таблицу (используем только столбцы B, C, D)
    try:
        df = pd.read_excel(EXCEL_PATH, usecols="B:D", header=0)
        df.columns = ["code", "type", "color"]
    except Exception as e:
        print(f"Ошибка при чтении Excel: {e}")
        sys.exit(1)

    # Удаляем строки с полностью пустыми значениями
    df = df.dropna(subset=["code", "type", "color"]).reset_index(drop=True)

    # Пытаемся загрузить шрифт Arial
    try:
        font = ImageFont.truetype(FONT_NAME, FONT_SIZE)
    except IOError:
        print("Предупреждение: шрифт Arial не найден, используется шрифт по умолчанию.")
        font = ImageFont.load_default()

    # Счётчики для отчёта
    total = len(df)
    processed = 0
    skipped = 0

    for idx, row in df.iterrows():
        code = str(row["code"]).strip()
        mat_type = str(row["type"]).strip()
        color = str(row["color"]).strip()

        if not code or not mat_type or not color:
            print(f"Строка {idx+2}: пропущена из-за пустых значений.")
            skipped += 1
            continue

        # Путь к исходному изображению: Photo/Materials/<code>/1.jpg
        source_dir = SOURCE_PHOTO_ROOT / code
        source_img = source_dir / "1.jpg"

        if not source_img.exists():
            print(f"Предупреждение: изображение не найдено: {source_img}")
            skipped += 1
            continue

        # Определяем целевую папку
        target_folder_name = get_target_folder_name(mat_type, color)
        target_dir = TARGET_ROOT / target_folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{code}.jpg"

        try:
            # Открываем исходное изображение
            with Image.open(source_img) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")

                orig_width, orig_height = img.size

                # --- Добавляем рамку цвета фона (примерно 5% от меньшей стороны) ---
                border = max(1, int(0.05 * min(orig_width, orig_height)))
                # Новые размеры с учётом рамки (изображение + рамка со всех сторон)
                framed_width = orig_width + 2 * border
                framed_height = orig_height + 2 * border

                # --- Создаём финальное изображение с нижней полосой для текста ---
                final_width = framed_width
                final_height = framed_height + BAR_HEIGHT
                final_img = Image.new("RGB", (final_width, final_height), LIGHT_CREAM)

                # Вставляем исходное изображение в центр рамки (поверх фона)
                final_img.paste(img, (border, border))

                # --- Рисуем текст на нижней полосе ---
                draw = ImageDraw.Draw(final_img)
                # Область для текста: от верха полосы (после рамки) до низа
                text_bar_rect = (0, framed_height, final_width, BAR_HEIGHT)
                text_lines = [f"{code} - {mat_type}", color]
                draw_centered_text(draw, font, text_lines, text_bar_rect, DARK_BROWN)

                # Сохраняем результат
                final_img.save(target_path, "JPEG", quality=95)
                processed += 1
                print(f"Обработано: {code} -> {target_path}")

        except Exception as e:
            print(f"Ошибка при обработке {code}: {e}")
            skipped += 1

    print(f"\nГотово. Обработано: {processed}, пропущено: {skipped}")

if __name__ == "__main__":
    main()