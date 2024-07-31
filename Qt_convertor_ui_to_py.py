import os
import subprocess

def convert_ui_to_py(ui_file):
    # is file exist?
    if not os.path.exists(ui_file):
        print(f"File '{ui_file}' is not found.")
        return

    # Извлеките имя файла без расширения
    base_name = os.path.splitext(ui_file)[0]

    # Определите имя файла .py для создания
    py_file = base_name + ".py"

    # Call pyuic6 through subprocess
    try:
        subprocess.run(["pyuic6", "-o", py_file, ui_file], check=True)
        print(f"File '{ui_file}' is converted to '{py_file}'.")
    except subprocess.CalledProcessError:
        print(f"Error during convertion of '{ui_file}'.")

if __name__ == "__main__":
    ui_file = "interface.ui"  # Путь к вашему файлу .ui
    convert_ui_to_py(ui_file)
