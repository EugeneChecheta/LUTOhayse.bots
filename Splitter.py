#!/usr/bin/env python3
"""
Скрипт склеивает изображения из папки PHOTOSPLIT в коллажи 3x4 (3 столбца, 4 строки).
Если фотографий больше 12, создаётся несколько выходных файлов.
Результаты сохраняются в папку SPLIT.
"""

import os
import sys
import glob
from PIL import Image

# ---------- НАСТРОЙКИ ----------
COLS = 3
ROWS = 4
CELLS_PER_COLLAGE = COLS * ROWS
INPUT_DIR = "PHOTOSPLIT"
OUTPUT_DIR = "SPLIT"
# Допустимые расширения (без учёта регистра)
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')
# Формат и качество выходных файлов
OUTPUT_FORMAT = 'JPEG'
OUTPUT_QUALITY = 95
# Цвет фона для пустых ячеек и полей (белый)
BACKGROUND_COLOR = (255, 255, 255)
# ---------------------------------

def get_image_files(directory):
    """Возвращает отсортированный список полных путей к изображениям в папке."""
    if not os.path.isdir(directory):
        print(f"Ошибка: папка '{directory}' не найдена.", file=sys.stderr)
        sys.exit(1)

    files = []
    for ext in IMAGE_EXTENSIONS:
        files.extend(glob.glob(os.path.join(directory, f'*{ext}')))
        files.extend(glob.glob(os.path.join(directory, f'*{ext.upper()}')))
    # Удаляем дубликаты и сортируем
    files = sorted(list(set(files)))
    return files

def resize_to_fit(image, target_size):
    """
    Изменяет размер изображения так, чтобы оно вписывалось в target_size,
    сохраняя пропорции. Возвращает новое изображение на белом фоне.
    """
    target_w, target_h = target_size
    img = image.copy()
    # Конвертируем в RGB, если есть альфа-канал
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGBA')
        background = Image.new('RGBA', img.size, BACKGROUND_COLOR + (255,))
        background.paste(img, mask=img.split()[-1])  # используем альфа-канал как маску
        img = background.convert('RGB')
    else:
        img = img.convert('RGB')

    # Вычисляем коэффициент масштабирования
    ratio = min(target_w / img.width, target_h / img.height)
    new_size = (int(img.width * ratio), int(img.height * ratio))
    img = img.resize(new_size, Image.Resampling.LANCZOS)

    # Создаём холст нужного размера и вставляем по центру
    canvas = Image.new('RGB', target_size, BACKGROUND_COLOR)
    offset = ((target_w - new_size[0]) // 2, (target_h - new_size[1]) // 2)
    canvas.paste(img, offset)
    return canvas

def main():
    # Получаем список всех изображений
    image_paths = get_image_files(INPUT_DIR)
    if not image_paths:
        print(f"В папке '{INPUT_DIR}' не найдено изображений.")
        sys.exit(0)

    print(f"Найдено изображений: {len(image_paths)}")

    # Создаём выходную папку, если её нет
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Открываем все изображения, чтобы вычислить глобальный максимальный размер
    # Это обеспечит одинаковый размер ячеек во всех коллажах
    opened_images = []
    global_max_w, global_max_h = 0, 0
    for path in image_paths:
        try:
            im = Image.open(path)
            opened_images.append((path, im))
            w, h = im.size
            if w > global_max_w:
                global_max_w = w
            if h > global_max_h:
                global_max_h = h
        except Exception as e:
            print(f"Не удалось открыть {path}: {e}", file=sys.stderr)

    if global_max_w == 0 or global_max_h == 0:
        print("Не удалось прочитать размеры ни одного изображения.")
        sys.exit(1)

    cell_size = (global_max_w, global_max_h)
    print(f"Размер ячейки (по максимальному изображению): {cell_size}")

    # Группируем изображения по 12
    total = len(opened_images)
    num_collages = (total + CELLS_PER_COLLAGE - 1) // CELLS_PER_COLLAGE

    for collage_idx in range(num_collages):
        start = collage_idx * CELLS_PER_COLLAGE
        end = min(start + CELLS_PER_COLLAGE, total)
        chunk = opened_images[start:end]

        # Создаём холст коллажа: ширина = COLS*cell_w, высота = ROWS*cell_h
        canvas_w = COLS * global_max_w
        canvas_h = ROWS * global_max_h
        collage = Image.new('RGB', (canvas_w, canvas_h), BACKGROUND_COLOR)

        for i, (path, im) in enumerate(chunk):
            # Масштабируем изображение под размер ячейки
            processed = resize_to_fit(im, cell_size)
            # Вычисляем позицию в сетке (построчно)
            row = i // COLS
            col = i % COLS
            x = col * global_max_w
            y = row * global_max_h
            collage.paste(processed, (x, y))
            im.close()  # освобождаем исходное изображение

        # Сохраняем результат
        output_name = f"collage_{collage_idx + 1:03d}.jpg"
        output_path = os.path.join(OUTPUT_DIR, output_name)
        collage.save(output_path, format=OUTPUT_FORMAT, quality=OUTPUT_QUALITY)
        print(f"Сохранён коллаж: {output_path}")

    print("Готово.")

if __name__ == "__main__":
    main()