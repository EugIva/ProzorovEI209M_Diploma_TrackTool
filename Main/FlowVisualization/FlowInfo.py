import json
import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from tqdm import tqdm


def load_json_data(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("Файл не найден")
    except json.JSONDecodeError:
        raise json.JSONDecodeError("Ошибка декодирования JSON")
    except Exception as e:
        raise Exception(f"Ошибка загрузки информации: {str(e)}")


def calculate_unique_flights(data):
    """
    Расчёт количества рейсов в файле
    """
    pbar_unique = tqdm(data)
    pbar_unique.set_description('Считаю количество рейсов')
    return len(set(flight['id'] for flight in pbar_unique))


def find_duplicate_callsigns(data):
    """
    Поиск разных рейсов с одинаковыми позывными
    """
    callsign_ids = {}
    pbar_iteration = tqdm(data)
    pbar_iteration.set_description('Проверяю дубликаты названий рейсов')
    for flight in pbar_iteration:
        if flight['callsign'] not in callsign_ids:
            callsign_ids[flight['callsign']] = set()
        callsign_ids[flight['callsign']].add(flight['id'])
    return {callsign: ids for callsign, ids in callsign_ids.items() if len(ids) > 1}


def calculate_time_range(data):
    """
    Расчёт первого и последнего времени, записанного в файле, и диапазон
    """
    pbar_time = tqdm(data)
    pbar_time.set_description('Считаю время')
    time_values = [datetime.strptime(flight['time'], '%Y-%m-%d %H:%M:%S.%f') for flight in pbar_time]
    time_range = (min(time_values), max(time_values))
    time_diff = time_range[1] - time_range[0]
    days = time_diff.days
    hours, remainder = divmod(time_diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return time_range, days, hours, minutes, seconds


def calculate_max_decimal_places(data):
    """
    Вычисление максимальной точности координат, записанных в файле
    """
    max_decimal_places = 0
    pbar_places = tqdm(data)
    pbar_places.set_description('Считаю точность координат')
    for flight in pbar_places:
        lat = float(flight['latitude'])
        lon = float(flight['longitude'])
        max_decimal_places = max(max_decimal_places, len(str(lat).split('.')), len(str(lon).split('.')))
    return max_decimal_places


def display_flow_info(file_path, label, graph_frame):
    """
    Отображение информации на форме приложения
    """
    try:
        print('Загружаю аналитику:')
        data = load_json_data(file_path)

        dir_path, file_name = os.path.split(file_path)
        file_name_short = os.path.splitext(file_name)[0]

        unique_flights = calculate_unique_flights(data)
        duplicate_callsigns = find_duplicate_callsigns(data)
        time_range, days, hours, minutes, seconds = calculate_time_range(data)
        max_decimal_places = calculate_max_decimal_places(data)

        info_text = f"Файл:                                     {file_name_short}\n"
        info_text += f"\n"
        info_text += f"Уникальных рейсов:                        {unique_flights}\n"
        info_text += f"Максимальная точность координат:          {max_decimal_places} после запятой\n"
        info_text += f"Диапазон времени:                         {time_range[0].strftime('%Y-%m-%d %H:%M:%S')} - {time_range[1].strftime('%Y-%m-%d %H:%M:%S')}\n"
        info_text += f"Всего времени:                            {days} дней, {hours} ч, {minutes} мин, {seconds} сек\n"
        info_text += f"Дублирующиеся номера рейсов (callsigns):  {'найдены совпадения' if duplicate_callsigns else 'отсутствуют'}\n \n"

        if duplicate_callsigns:
            text_frame = ttk.Frame(label)
            text_frame.grid(row=0, column=0, columnspan=5, sticky='nsew')
            label.grid_rowconfigure(0, weight=1)
            label.grid_columnconfigure(0, weight=1)

            text_widget = tk.Text(text_frame, font=('Fira Code SemiBold', 10), foreground='grey', borderwidth=0,
                                  wrap='word', height=11, width=100)
            scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
            text_widget.config(yscrollcommand=scrollbar.set)
            text_widget.grid(row=0, column=1, sticky='nsew')
            scrollbar.grid(row=0, column=0, sticky='ns')

            text_frame.grid_rowconfigure(0, weight=1)
            text_frame.grid_columnconfigure(0, weight=1)
            text_frame.grid_columnconfigure(1, weight=0)

            text_widget.insert(tk.END, info_text)
            for callsign, ids in duplicate_callsigns.items():
                text_widget.insert(tk.END, f"Callsign ")
                text_widget.insert(tk.END, f" {callsign} ", 'highlightline')
                text_widget.insert(tk.END, f" = {', '.join(map(str, ids))}\n")

            text_widget.tag_configure('highlightline', background='SkyBlue', foreground="Black",
                                      selectbackground='RoyalBlue', selectforeground='white')
            text_widget.config(state='disabled')
        else:
            for widget in label.winfo_children():
                if widget != label:
                    widget.destroy()
            label.config(text=info_text)

    except Exception as e:
        label.config(text=f"Ошибка загрузки информации: {str(e)}")
        print(e)
