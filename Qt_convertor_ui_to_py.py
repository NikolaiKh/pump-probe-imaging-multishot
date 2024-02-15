import os
import subprocess

def convert_ui_to_py(ui_file):
    # Убедитесь, что файл существует
    if not os.path.exists(ui_file):
        print(f"Файл '{ui_file}' не найден.")
        return

    # Извлеките имя файла без расширения
    base_name = os.path.splitext(ui_file)[0]

    # Определите имя файла .py для создания
    py_file = base_name + ".py"

    # Вызовите pyuic5 через subprocess
    try:
        subprocess.run(["pyuic6", "-o", py_file, ui_file], check=True)
        print(f"Файл '{ui_file}' успешно конвертирован в '{py_file}'.")
    except subprocess.CalledProcessError:
        print(f"Ошибка при конвертации файла '{ui_file}'.")

if __name__ == "__main__":
    ui_file = "interface.ui"  # Путь к вашему файлу .ui
    convert_ui_to_py(ui_file)
