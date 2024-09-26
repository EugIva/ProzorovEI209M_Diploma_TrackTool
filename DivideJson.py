import os
import json
from tkinter import messagebox
import PushNotify


def divide_json_file(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        dir_path, file_name = os.path.split(file_path)
        file_name_short = os.path.splitext(file_name)[0]

        # создание папки
        if not os.path.exists('Exports/jsonDivide'):
            os.makedirs('Exports/jsonDivide')

        if not os.path.exists(f'Exports/jsonDivide/{file_name_short}'):
            os.makedirs(f'Exports/jsonDivide/{file_name_short}')

        # группировка данных по callsign
        callsign_data = {}
        for item in data:
            if 'callsign' in item and item['callsign']:
                key = item['callsign']
            else:
                key = item['id']
            if key not in callsign_data:
                callsign_data[key] = []
            callsign_data[key].append(item)

        # создание json файлов для каждого callsign
        for key, items in callsign_data.items():
            file_name = os.path.join(f'Exports/jsonDivide/{file_name_short}', f"{key}.json")
            with open(file_name, 'w') as f:
                json.dump(items, f, indent=4)

        PushNotify.notify_popup('Разделение JSON', f'Преобразование потока {file_name_short} завершено успешно')
    except Exception as e:
        print(f"{e}")
        messagebox.showerror("Ошибка", "Файл не корректный. Проверьте формат или содержимое файла.")
