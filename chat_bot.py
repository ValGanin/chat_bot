#!/usr/bin/env python3
import os
import time
import glob
import pdfplumber
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Программы и XPATH кнопок
PROGRAMS = {
    "ai": {
        "name": "Искусственный интеллект",
        "url": "https://abit.itmo.ru/program/master/ai",
        "btn_xpath": '//*[@id="__next"]/div/main/div[3]/div[4]/div/div/button'
    },
    "ai_product": {
        "name": "AI Product",
        "url": "https://abit.itmo.ru/program/master/ai_product",
        "btn_xpath": '//*[@id="__next"]/div/main/div[3]/div[4]/div/div/button'
    }
}
DOWNLOAD_DIR = os.getcwd()

# Скачивает PDF по JS-клику
def download_pdf(url, btn_xpath, download_dir=DOWNLOAD_DIR):
    opts = Options()
    prefs = {
        "download.default_directory": os.path.abspath(download_dir),
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    }
    opts.add_experimental_option("prefs", prefs)
    opts.add_argument("--headless=new")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts
    )
    try:
        driver.get(url)
        time.sleep(3)
        btn = driver.find_element(By.XPATH, btn_xpath)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(5)
    finally:
        driver.quit()

    # Возвращает путь к последнему скачанному PDF
    pdfs = sorted(
        glob.glob(os.path.join(download_dir, '*.pdf')),
        key=os.path.getmtime,
        reverse=True
    )
    return pdfs[0] if pdfs else None

# Извлекает названия дисциплин из таблиц PDF
def extract_disciplines(pdf_path):
    seen = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                # Предполагаем, что первая строка — заголовок
                for row in table[1:]:
                    if len(row) >= 2 and row[1]:
                        name = row[1].strip()
                        if name and name not in seen:
                            seen.append(name)
    return seen

# Извлекает весь текст из PDF
def extract_all_text(pdf_path):
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texts.append(t)
    return "\n".join(texts)

# Удаляет все скаченные PDF после работы
def cleanup_pdfs(download_dir=DOWNLOAD_DIR):
    for f in glob.glob(os.path.join(download_dir, '*.pdf')):
        try:
            os.remove(f)
        except:
            pass

# Выбор программы пользователем
def choose_program():
    print("Выберите программу:")
    for key, info in PROGRAMS.items():
        print(f"  {key} — {info['name']}")
    while True:
        sel = input("Ключ (ai/ai_product): ").strip().lower()
        if sel in PROGRAMS:
            return sel
        print("Неверный ввод, повторите.")

# Выводит список в колонки
def print_columns(items, cols=2):
    n = len(items)
    rows = (n + cols - 1) // cols
    matrix = []
    for r in range(rows):
        row = []
        for c in range(cols):
            idx = c * rows + r
            row.append(items[idx] if idx < n else "")
        matrix.append(row)
    widths = [max(len(matrix[r][c]) for r in range(rows)) for c in range(cols)]
    for r in range(rows):
        line = "  ".join(matrix[r][c].ljust(widths[c]) for c in range(cols))
        print(line)

# Главная функция
def main():
    prog = choose_program()
    info = PROGRAMS[prog]
    print(f"\nСкачиваю PDF учебного плана «{info['name']}»...")
    pdf_file = download_pdf(info['url'], info['btn_xpath'])
    if not pdf_file:
        print("Ошибка: не скачался PDF.")
        return

    try:
        print("Парсю названия дисциплин...")
        disciplines = extract_disciplines(pdf_file)
        if disciplines:
            print(f"Найдено дисциплин: {len(disciplines)}")
            print("Первые 10:")
            for d in disciplines[:10]: print(" -", d)
        else:
            print("Не удалось найти дисциплины в таблицах PDF.")

        print("\nВведите ключ для поиска по названиям дисциплин или общему тексту (стоп — выход):")
        all_text = extract_all_text(pdf_file)
        while True:
            q = input("Поиск: ").strip()
            if q.lower() in ("стоп", "exit", "выход"):
                print("Завершение работы.")
                break
            found = [d for d in disciplines if q.lower() in d.lower()]
            if found:
                if len(found) == 1:
                    print("Найдена дисциплина:")
                    print(" -", found[0])
                else:
                    print(f"Найдено {len(found)} дисциплин:")
                    print_columns(found)
            else:
                matches = [line.strip() for line in all_text.splitlines() if q.lower() in line.lower()]
                if matches:
                    print(f"Найдено {len(matches)} совпадений в тексте, показываю 5:")
                    for m in matches[:5]: print(" -", m)
                else:
                    print("Ничего не найдено.")
    finally:
        cleanup_pdfs()

if __name__ == "__main__":
    main()