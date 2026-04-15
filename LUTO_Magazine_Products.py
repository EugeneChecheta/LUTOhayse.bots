import os
from PIL import Image, ImageDraw, ImageFont

# Словарь соответствия букв типа и русских названий
TYPE_NAMES = {
    'A': 'Бауэн',
    'P': 'Тайль',
    'R': 'Бальт',
    'K': 'Царт',
    'Z': 'Андэр',
    'T': 'Вельтраум',
    'F': 'Зофа',
    'J': 'Фэст',
    'G': 'Унви',
    'V': 'Вэрт'
}

BASE_DIR = "Photo"
PRODUCTS_DIR = os.path.join(BASE_DIR, "Products")
MAGAZINE_DIR = os.path.join(BASE_DIR, "LUTO_Magazine")

# Параметры обрезки фона
WHITE_THRESHOLD = 240          # пиксели ярче этого считаются фоном
# Параметры рамки
BORDER_PERCENT = 0.05          # размер рамки в процентах от меньшей стороны изображения
# Параметры полей для текста
TEXT_PADDING = 10               # отступ внутри поля
MIN_FONT_SIZE = 10
MAX_FONT_SIZE = 200
FONT_STEP = 1                   # шаг изменения шрифта при подборе

def get_font(size):
    """Загружает шрифт Arial заданного размера или возвращает шрифт по умолчанию."""
    font_paths = [
        "arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except IOError:
            continue
    return ImageFont.load_default()

def find_latest_image(folder_path):
    """
    В папке ищет все файлы .png, из имени пытается извлечь число.
    Возвращает путь к файлу с наибольшим числом или None.
    """
    if not os.path.isdir(folder_path):
        return None
    png_files = []
    for f in os.listdir(folder_path):
        if f.lower().endswith('.png'):
            base = os.path.splitext(f)[0]
            try:
                num = int(base)  # предполагаем, что имя состоит только из цифр
                png_files.append((num, os.path.join(folder_path, f)))
            except ValueError:
                continue
    if not png_files:
        return None
    png_files.sort(key=lambda x: x[0])
    return png_files[-1][1]

def crop_white_borders(image, threshold=WHITE_THRESHOLD):
    """
    Обрезает белые поля изображения.
    Возвращает новое изображение без лишнего фона.
    """
    gray = image.convert('L')
    # Пиксели ярче threshold считаем фоном (белым), остальные – объектом (чёрным)
    mask = gray.point(lambda p: 255 if p < threshold else 0, mode='1')
    bbox = mask.getbbox()
    if bbox:
        return image.crop(bbox)
    else:
        return image

def add_white_border(image, percent=BORDER_PERCENT):
    """
    Добавляет белую рамку вокруг изображения.
    Ширина рамки = percent * min(ширина, высота) исходного изображения.
    """
    w, h = image.size
    border = int(percent * min(w, h))
    if border == 0:
        return image
    new_w = w + 2 * border
    new_h = h + 2 * border
    new_img = Image.new('RGB', (new_w, new_h), 'white')
    new_img.paste(image, (border, border))
    return new_img

def get_optimal_font_size(text, target_width, max_size=MAX_FONT_SIZE, min_size=MIN_FONT_SIZE, step=FONT_STEP):
    """
    Подбирает размер шрифта так, чтобы ширина текста была не больше target_width.
    Возвращает (font, text_width, text_height) для подобранного размера.
    Если текст пустой, возвращает (None, 0, 0).
    """
    if not text:
        return None, 0, 0

    font = None
    text_width = 0
    text_height = 0
    for size in range(max_size, min_size - 1, -step):
        font = get_font(size)
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        if text_width <= target_width:
            break
    return font, text_width, text_height

def create_magazine_image(obj_img, top_text, bottom_text):
    """
    Создаёт итоговое изображение для журнала.
    Если текст пуст, соответствующее поле не добавляется.
    """
    W, H = obj_img.size

    # Определяем параметры верхнего поля
    top_font, top_w, top_h = get_optimal_font_size(top_text, W - 2 * TEXT_PADDING)
    top_field_height = top_h + 2 * TEXT_PADDING if top_text else 0

    # Определяем параметры нижнего поля
    bottom_font, bottom_w, bottom_h = get_optimal_font_size(bottom_text, W - 2 * TEXT_PADDING)
    bottom_field_height = bottom_h + 2 * TEXT_PADDING if bottom_text else 0

    total_height = top_field_height + H + bottom_field_height
    new_img = Image.new('RGB', (W, total_height), 'white')
    new_img.paste(obj_img, (0, top_field_height))

    draw = ImageDraw.Draw(new_img)

    # Верхний текст
    if top_text:
        top_x = (W - top_w) // 2
        top_y = TEXT_PADDING
        draw.text((top_x, top_y), top_text, fill='black', font=top_font)

    # Нижний текст
    if bottom_text:
        bottom_x = (W - bottom_w) // 2
        bottom_y = top_field_height + H + TEXT_PADDING
        draw.text((bottom_x, bottom_y), bottom_text, fill='black', font=bottom_font)

    return new_img

def main():
    if not os.path.isdir(PRODUCTS_DIR):
        print(f"Ошибка: папка {PRODUCTS_DIR} не найдена.")
        return

    # Создаём целевую папку и подпапки для каждого типа
    os.makedirs(MAGAZINE_DIR, exist_ok=True)
    for folder in TYPE_NAMES.values():
        os.makedirs(os.path.join(MAGAZINE_DIR, folder), exist_ok=True)

    # Получаем список подпапок (кодов) в папке Products
    try:
        code_folders = [d for d in os.listdir(PRODUCTS_DIR)
                        if os.path.isdir(os.path.join(PRODUCTS_DIR, d))]
    except OSError as e:
        print(f"Ошибка чтения папки {PRODUCTS_DIR}: {e}")
        return

    code_folders.sort()

    for code_folder in code_folders:
        # Проверяем формат кода: S<тип>...
        if len(code_folder) < 2 or code_folder[0] != 'S' or code_folder[1] not in TYPE_NAMES:
            print(f"Предупреждение: папка {code_folder} не соответствует формату кода (S<тип>...). Пропускаем.")
            continue

        type_letter = code_folder[1]
        type_rus = TYPE_NAMES[type_letter]

        # Ищем последнее изображение в папке продукта
        product_dir = os.path.join(PRODUCTS_DIR, code_folder)
        source_image = find_latest_image(product_dir)
        if source_image is None:
            print(f"Предупреждение: в папке {product_dir} нет подходящих PNG. Пропускаем.")
            continue

        target_file = os.path.join(MAGAZINE_DIR, type_rus, code_folder + ".png")
        if os.path.isfile(target_file):
            print(f"Пропуск {code_folder}: уже обработано.")
            continue

        # Формируем тексты (нижний теперь пустой)
        top_text = f"{type_rus} {code_folder}"
        bottom_text = ""

        try:
            with Image.open(source_image) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                # 1. Обрезка белого фона
                cropped_img = crop_white_borders(img)
                # 2. Добавление белой рамки (5% от края)
                bordered_img = add_white_border(cropped_img, percent=BORDER_PERCENT)
                # 3. Создание итогового изображения с текстом
                final_img = create_magazine_image(bordered_img, top_text, bottom_text)
                final_img.save(target_file)
                print(f"Сохранено: {target_file}")
        except Exception as e:
            print(f"Ошибка при обработке {code_folder}: {e}")

    print("\nРабота скрипта завершена.")

if __name__ == "__main__":
    main()