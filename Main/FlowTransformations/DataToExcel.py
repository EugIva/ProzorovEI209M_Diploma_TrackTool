import json
import os
from tkinter import messagebox

import pandas as pd

import Main.PushNotify


def convert_json_excel(file_path):
    """
    Преобразование потока в Excel табличку
    """
    try:
        with open(f'{file_path}') as f:
            data = json.load(f)

        dir_path, file_name = os.path.split(file_path)
        file_name_short = os.path.splitext(file_name)[0]

        aircraft_data = {}
        for item in data:
            aircraft_id = item['id']
            callsign = item['callsign']
            if callsign:
                if callsign not in aircraft_data:
                    aircraft_data[callsign] = []
                aircraft_data[callsign].append(item)
            else:
                if aircraft_id not in aircraft_data:
                    aircraft_data[aircraft_id] = []
                aircraft_data[aircraft_id].append(item)

        # создание папки
        if not os.path.exists('Exports/excelExports'):
            os.makedirs('Exports/excelExports')

        if not os.path.exists(f'Exports/excelExports/{file_name_short}'):
            os.makedirs(f'Exports/excelExports/{file_name_short}')

        for key, items in aircraft_data.items():
            df = pd.DataFrame(items)

            if key in aircraft_data:
                excel_file_path = os.path.join(f'Exports/excelExports/{file_name_short}', f'{key}.xlsx')
            else:
                excel_file_path = os.path.join(f'Exports/excelExports/{file_name_short}', f'{key}.xlsx')

            df.to_excel(excel_file_path, index=False, engine='openpyxl')

            workbook = pd.ExcelWriter(excel_file_path)
            df.to_excel(workbook, index=False)
            workbook.close()

        Main.PushNotify.notify_popup('Конвертация в Excel',
                                     f'Преобразование потока {file_name_short}  завершено успешно')

    except Exception as e:
        print(f"{e}")
        messagebox.showerror("Ошибка", "Файл не корректный. Проверьте формат или содержимое файла.")
