import os
import re
import itertools
import pandas as pd
from collections import Counter
from PIL import Image, ImageDraw, ImageFont


# ====================== 1. Создание папок ======================
def get_valid_codes(max_length):
    """Генерирует все допустимые коды модулей T (Вельтраум)"""
    modules = ['01', '02', '03', '04', '05', '07']
    valid_codes = set()

    for length in range(1, max_length + 1):
        for code_tuple in itertools.product(modules, repeat=length):
            code = ''.join(code_tuple)

            # Проверяем наличие запрещенных комбинаций
            counts = Counter(code_tuple)

            # Модуль 05 - только если длина 1
            if counts.get('05', 0) > 0 and length != 1:
                continue
            if counts.get('05', 0) > 1:
                continue

            # Модуль 07 - только если длина 1
            if counts.get('07', 0) > 0 and length != 1:
                continue
            if counts.get('07', 0) > 1:
                continue

            # Модуль 02 - только в конце, не более одного
            if counts.get('02', 0) > 1:
                continue
            if counts.get('02', 0) == 1:
                if code_tuple[-1] != '02':
                    continue

            # Модуль 03 - только в начале, не более одного
            if counts.get('03', 0) > 1:
                continue
            if counts.get('03', 0) == 1:
                if code_tuple[0] != '03':
                    continue

            # Правила для модуля 04 (угловой, аналогично 06 в P)
            count_04 = counts.get('04', 0)
            if count_04 > 0:
                starts_with_04 = code_tuple[0] == '04'
                ends_with_04 = code_tuple[-1] == '04'

                if starts_with_04 and ends_with_04:
                    max_04_allowed = 4
                else:
                    max_04_allowed = 2

                if count_04 > max_04_allowed:
                    continue

                # Проверка на последовательные 04
                has_consecutive_04 = False
                for i in range(len(code_tuple) - 1):
                    if code_tuple[i] == '04' and code_tuple[i + 1] == '04':
                        has_consecutive_04 = True
                        break

                if has_consecutive_04 and code != '0404':
                    continue

            # Модуль 01 - может быть в любом месте, но не более одного?
            # В задании указано "в любом месте", но без ограничения количества
            # Оставим без ограничений, кроме общей проверки

            # Проверяем, что 05 и 07 не сочетаются с другими модулями
            if ('05' in code or '07' in code) and length > 1:
                continue

            valid_codes.add(code)

    return valid_codes


def create_ct_folders():
    """Создает папки CT для допустимых комбинаций модулей Вельтраум"""
    base_path = "./Photo/Construction"

    if not os.path.exists(base_path):
        os.makedirs(base_path)
        print(f"Создана базовая папка: {base_path}")

    print("Этап 1: Создание папок CT")
    print("-" * 40)

    # Запрашиваем максимальную длину кода
    while True:
        try:
            max_length = int(input("Введите максимальную длину кода (1-10): "))
            if 1 <= max_length <= 10:
                break
            print("Число должно быть от 1 до 10")
        except ValueError:
            print("Введите целое число")

    # Генерируем допустимые коды
    valid_codes = get_valid_codes(max_length)

    created_count = 0
    existed_count = 0

    for code in sorted(valid_codes, key=lambda x: (len(x), x)):
        folder_name = f"CT{code}"
        folder_path = os.path.join(base_path, folder_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            created_count += 1
        else:
            existed_count += 1

    print(f"Создано папок: {created_count}")
    print(f"Уже существовало: {existed_count}")
    print(f"Всего папок CT: {len(valid_codes)}")
    print()


# ====================== 2. Создание файлов с размерами ======================
def calculate_sizes(modules, module_lengths):
    """Вычисляет размеры дивана на основе последовательности модулей Вельтраум"""
    if len(modules) <= 1:
        if modules and modules[0] in module_lengths:
            return [str(module_lengths[modules[0]])]
        return []

    # Находим индексы угловых модулей (04), которые не на краях
    split_indices = []
    for i, module in enumerate(modules):
        if module == "04" and 0 < i < len(modules) - 1:
            split_indices.append(i)

    if not split_indices:
        total = sum(module_lengths.get(m, 0) for m in modules)
        return [str(total)]

    sizes = []
    start_idx = 0

    for split_idx in split_indices:
        segment = modules[start_idx:split_idx + 1]
        size = sum(module_lengths.get(m, 0) for m in segment)
        sizes.append(str(size))
        start_idx = split_idx

    last_segment = modules[start_idx:]
    last_size = sum(module_lengths.get(m, 0) for m in last_segment)
    sizes.append(str(last_size))

    return sizes


def create_size_files():
    """Создает файлы size.txt в папках CT для модулей Вельтраум"""
    print("Этап 2: Создание файлов с размерами")
    print("-" * 40)

    excel_path = "./Database/Moduls_log.xlsx"
    base_path = "./Photo/Construction"

    # Читаем таблицу с модулями
    try:
        df = pd.read_excel(excel_path, sheet_name="Модули")
    except FileNotFoundError:
        print(f"Ошибка: Файл {excel_path} не найден.")
        return
    except Exception as e:
        print(f"Ошибка при чтении Excel: {e}")
        return

    # Фильтруем только модули Вельтраум (код начинается с T)
    weltraum_df = df[df["Код модуля"].str.startswith("T", na=False)].copy()

    # Создаем словарь с длинами модулей
    module_lengths = {}
    for _, row in weltraum_df.iterrows():
        code = str(row["Код модуля"])
        code_num = code[1:] if len(code) > 1 else ""
        length = row["Длина"]
        if pd.notna(length):
            module_lengths[code_num] = int(length)

    # Ищем папки CT
    ct_folders = []
    try:
        all_folders = os.listdir(base_path)
        ct_folders = [f for f in all_folders
                      if os.path.isdir(os.path.join(base_path, f))
                      and f.startswith("CT")]
    except FileNotFoundError:
        print(f"Ошибка: Папка {base_path} не найдена.")
        return

    print(f"Найдено папок CT: {len(ct_folders)}")

    processed = 0
    for folder in ct_folders:
        folder_path = os.path.join(base_path, folder)
        numeric_part = folder[2:]
        modules = re.findall(r'\d{2}', numeric_part)

        if not modules:
            continue

        # Проверяем, что все модули есть в словаре
        missing_modules = [m for m in modules if m not in module_lengths]
        if missing_modules:
            continue

        # Вычисляем размеры
        sizes = calculate_sizes(modules, module_lengths)

        if not sizes:
            continue

        # Создаем файл size.txt
        output_file = os.path.join(folder_path, "size.txt")
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(sizes))
            processed += 1
        except Exception:
            continue

    print(f"Создано файлов size.txt: {processed}")
    print()


# ====================== 3. Создание изображений с разметками ======================
def read_size_file(folder_path):
    """Читает размеры из файла size.txt"""
    size_file = os.path.join(folder_path, "size.txt")
    if not os.path.exists(size_file):
        return None

    try:
        with open(size_file, 'r') as f:
            sizes = [line.strip() for line in f.readlines() if line.strip()]
            sizes = [int(size) for size in sizes[:3]]
            return sizes
    except:
        return None


def rotate_image(img, rotation_angle):
    """Вращает изображение на заданный угол"""
    if rotation_angle != 0:
        img = img.rotate(-rotation_angle, expand=True, resample=Image.NEAREST)
    return img


def create_snake_image(modules, cells_folder):
    """Создает изображение змейкой из нескольких модулей Вельтраум"""
    images = []
    positions = []

    x, y = 0, 0
    direction = 0  # 0: right, 1: down, 2: left, 3: up
    rotation_angle = 0

    for i, module in enumerate(modules):
        module_filename = f"T{module}.png"
        module_path = os.path.join(cells_folder, module_filename)

        if not os.path.exists(module_path):
            return None, 0, 0, False

        img = Image.open(module_path).convert('RGBA')

        # Поворачиваем модуль 04 (кроме первого)
        if module == "04" and i > 0:
            img = rotate_image(img, 90)

        # Применяем общий угол поворота
        if rotation_angle != 0:
            img = rotate_image(img, rotation_angle)

        images.append(img)

        if i == 0:
            positions.append((x, y))
        else:
            prev_img = images[i - 1]
            prev_width, prev_height = prev_img.size

            if direction == 0:  # right
                x += prev_width
            elif direction == 1:  # down
                y += prev_height
            elif direction == 2:  # left
                x -= img.width
            elif direction == 3:  # up
                y -= img.height

            positions.append((x, y))

        # Обновляем направление для модуля 04
        if module == "04" and i > 0:
            direction = (direction + 1) % 4
            rotation_angle = (rotation_angle + 90) % 360

    # Создаем холст
    min_x = min(x for x, y in positions)
    max_x = max(x + img.width for (x, y), img in zip(positions, images))
    min_y = min(y for x, y in positions)
    max_y = max(y + img.height for (x, y), img in zip(positions, images))

    canvas_width = max_x - min_x
    canvas_height = max_y - min_y

    if canvas_width == 0 or canvas_height == 0:
        canvas_width = images[0].width
        canvas_height = images[0].height

    canvas = Image.new('RGBA', (canvas_width, canvas_height), (255, 255, 255, 0))

    for img, (x, y) in zip(images, positions):
        adjusted_x = x - min_x
        adjusted_y = y - min_y
        canvas.paste(img, (adjusted_x, adjusted_y), img if img.mode == 'RGBA' else None)

    direction_changes = sum(1 for i, module in enumerate(modules) if module == "04" and i > 0)
    first_module_is_04 = (modules[0] == "04")

    return canvas, rotation_angle, direction_changes, first_module_is_04


def create_image_with_dimensions(sofa_image, sizes):
    """Создает изображение с размерами на светло-сером фоне"""
    scale_factor = 10
    sofa_width = sofa_image.width * scale_factor
    sofa_height = sofa_image.height * scale_factor
    scaled_sofa = sofa_image.resize((sofa_width, sofa_height), Image.NEAREST)

    padding_top = 150
    padding_right = 150
    padding_bottom = 150
    padding_left = 50

    total_width = sofa_width + padding_left + padding_right
    total_height = sofa_height + padding_top + padding_bottom

    light_gray = (245, 245, 245)
    result_image = Image.new('RGB', (total_width, total_height), light_gray)

    sofa_x = padding_left
    sofa_y = padding_top
    result_image.paste(scaled_sofa, (sofa_x, sofa_y), scaled_sofa)

    if sizes:
        add_dimension_lines(result_image, sofa_x, sofa_y, sofa_width, sofa_height, sizes)

    return result_image


def add_dimension_lines(image, sofa_x, sofa_y, sofa_width, sofa_height, sizes):
    """Добавляет размерные линии на изображение"""
    draw = ImageDraw.Draw(image)
    line_color = (0, 0, 0)
    text_color = (0, 0, 0)

    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()

    sofa_left = sofa_x
    sofa_top = sofa_y
    sofa_right = sofa_x + sofa_width
    sofa_bottom = sofa_y + sofa_height

    # Верхний размер
    if len(sizes) >= 1:
        size_text = str(sizes[0])
        line_y = sofa_top - 50
        text_y = line_y - 40

        draw.line([(sofa_left, sofa_top), (sofa_left, line_y)], fill=line_color, width=3)
        draw.line([(sofa_right, sofa_top), (sofa_right, line_y)], fill=line_color, width=3)
        draw.line([(sofa_left, line_y), (sofa_right, line_y)], fill=line_color, width=3)

        bbox = draw.textbbox((0, 0), size_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = sofa_left + (sofa_width - text_width) // 2
        draw.text((text_x, text_y), size_text, fill=text_color, font=font)

    # Правый размер
    if len(sizes) >= 2:
        size_text = str(sizes[1])
        line_x = sofa_right + 50

        draw.line([(sofa_right, sofa_top), (line_x, sofa_top)], fill=line_color, width=3)
        draw.line([(sofa_right, sofa_bottom), (line_x, sofa_bottom)], fill=line_color, width=3)
        draw.line([(line_x, sofa_top), (line_x, sofa_bottom)], fill=line_color, width=3)

        bbox = draw.textbbox((0, 0), size_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = line_x + 20
        text_y = sofa_top + (sofa_height - text_height) // 2
        draw.text((text_x, text_y), size_text, fill=text_color, font=font)

    # Нижний размер
    if len(sizes) >= 3:
        size_text = str(sizes[2])
        line_y = sofa_bottom + 50
        text_y = line_y + 40

        draw.line([(sofa_left, sofa_bottom), (sofa_left, line_y)], fill=line_color, width=3)
        draw.line([(sofa_right, sofa_bottom), (sofa_right, line_y)], fill=line_color, width=3)
        draw.line([(sofa_left, line_y), (sofa_right, line_y)], fill=line_color, width=3)

        bbox = draw.textbbox((0, 0), size_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = sofa_left + (sofa_width - text_width) // 2
        draw.text((text_x, text_y), size_text, fill=text_color, font=font)


def create_cell_images():
    """Создает изображения cells.png в папках CT для модулей Вельтраум"""
    print("Этап 3: Создание изображений с разметками")
    print("-" * 40)

    base_path = "./Photo/Construction"
    cells_folder = os.path.join(base_path, "cells")

    if not os.path.exists(cells_folder):
        print(f"Ошибка: Папка {cells_folder} не найдена.")
        return

    # Ищем папки CT
    ct_folders = []
    try:
        all_folders = os.listdir(base_path)
        ct_folders = [f for f in all_folders
                      if os.path.isdir(os.path.join(base_path, f))
                      and f.startswith("CT")]
    except FileNotFoundError:
        print(f"Ошибка: Папка {base_path} не найдена.")
        return

    print(f"Обработка папок CT: {len(ct_folders)}")

    created = 0
    for folder in ct_folders:
        folder_path = os.path.join(base_path, folder)
        numeric_part = folder[2:]
        modules = re.findall(r'\d{2}', numeric_part)

        if not modules:
            continue

        # Читаем размеры
        sizes = read_size_file(folder_path)

        # Проверяем наличие файлов модулей
        missing_files = []
        for module in modules:
            module_filename = f"T{module}.png"
            module_path = os.path.join(cells_folder, module_filename)
            if not os.path.exists(module_path):
                missing_files.append(module_filename)

        if missing_files:
            continue

        # Создаем изображение
        if len(modules) == 1:
            module_filename = f"T{modules[0]}.png"
            module_path = os.path.join(cells_folder, module_filename)
            sofa_img = Image.open(module_path).convert('RGBA')
        else:
            sofa_img, _, _, _ = create_snake_image(modules, cells_folder)
            if sofa_img is None:
                continue

        # Создаем финальное изображение
        result_img = create_image_with_dimensions(sofa_img, sizes)
        output_path = os.path.join(folder_path, "cells.png")
        result_img.save(output_path, 'PNG', dpi=(300, 300))
        created += 1

    print(f"Создано изображений cells.png: {created}")
    print()


# ====================== Основная функция ======================
def main():
    print("=" * 50)
    print("ОБЪЕДИНЕННЫЙ СКРИПТ ДЛЯ МОДУЛЕЙ T (ВЕЛЬТРАУМ)")
    print("=" * 50)

    # Проверяем наличие необходимых файлов и папок
    if not os.path.exists("./Database/Moduls_log.xlsx"):
        print("ОШИБКА: Файл ./Database/Moduls_log.xlsx не найден.")
        return

    # Запускаем этапы по порядку
    create_ct_folders()
    create_size_files()
    create_cell_images()

    print("=" * 50)
    print("ВСЕ ОПЕРАЦИИ ЗАВЕРШЕНЫ")
    print("=" * 50)


if __name__ == "__main__":
    main()