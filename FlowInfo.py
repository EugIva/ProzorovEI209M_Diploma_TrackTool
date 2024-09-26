import datetime
import json
import os
from tkinter import ttk
from tqdm import tqdm
from collections import defaultdict
import tkinter as tk


def display_flow_info(file_path, label, graph_frame):
    try:
        print('Загружаю аналитику:')
        with open(file_path, 'r') as f:
            data = json.load(f)

        dir_path, file_name = os.path.split(file_path)
        file_name_short = os.path.splitext(file_name)[0]

        pbar_unique = tqdm(data)
        pbar_unique.set_description('Считаю количество рейсов')
        unique_flights = len(set(flight['id'] for flight in pbar_unique))

        # Создаём словарь для хранения id по callsign
        callsign_ids = defaultdict(set)

        # Заполняем словарь
        for flight in data:
            callsign_ids[flight['callsign']].add(flight['id'])

        pbar_iteration = tqdm(callsign_ids.items())
        pbar_iteration.set_description('Проверяю дубликаты названий рейсов')
        # Проверяем на дубликаты
        duplicate_callsigns = {callsign: ids for callsign, ids in pbar_iteration if len(ids) > 1}

        pbar_time = tqdm(data)
        pbar_time.set_description('Считаю время')
        time_values = [datetime.datetime.strptime(flight['time'], '%Y-%m-%d %H:%M:%S.%f') for flight in pbar_time]
        time_range = (min(time_values), max(time_values))

        time_diff = time_range[1] - time_range[0]

        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        max_decimal_places = 0

        pbar_places = tqdm(data)
        pbar_places.set_description('Считаю точность координат')
        for flight in pbar_places:
            lat = float(flight['latitude'])
            lon = float(flight['longitude'])
            max_decimal_places = max(max_decimal_places, len(str(lat).split('.')[1]), len(str(lon).split('.')[1]))

        info_text = f"Файл:                                     {file_name_short}\n"
        info_text += f"\n"
        info_text += f"Уникальных рейсов:                        {unique_flights}\n"
        info_text += f"Максимальная точность координат:          {max_decimal_places} после запятой\n"
        info_text += f"Диапазон времени:                         {time_range[0].strftime('%Y-%m-%d %H:%M:%S')} - {time_range[1].strftime('%Y-%m-%d %H:%M:%S')}\n"
        info_text += f"Всего времени:                            {days} дней, {hours} ч, {minutes} мин, {seconds} сек\n"
        info_text += f"Дублирующиеся номера рейсов (callsigns):  {'найдены совпадения' if duplicate_callsigns else 'отсутствуют'}\n \n"

        # Выводим найденные дубликаты
        if duplicate_callsigns:
            text_frame = ttk.Frame(label)
            text_frame.grid(row=0, column=0, columnspan=5, sticky='nsew')

            # Настройка размеров ячейки для text_frame (текстовое поле с прокруткой)
            label.grid_rowconfigure(0, weight=1)
            label.grid_columnconfigure(0, weight=1)

            text_widget = tk.Text(text_frame, font=('Fira Code SemiBold', 10), foreground='grey', borderwidth=0,
                                  wrap='word', height=11, width=100)
            scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
            text_widget.config(yscrollcommand=scrollbar.set)
            text_widget.grid(row=0, column=1, sticky='nsew')
            scrollbar.grid(row=0, column=0, sticky='ns')

            # Настройка размеров ячейки для text_widget и scrollbar
            text_frame.grid_rowconfigure(0, weight=1)
            text_frame.grid_columnconfigure(0, weight=1)
            text_frame.grid_columnconfigure(1, weight=0)

            # Вставляем текст в поле
            text_widget.insert(tk.END, info_text)
            for callsign, ids in duplicate_callsigns.items():
                text_widget.insert(tk.END, f"Callsign ")
                text_widget.insert(tk.END, f" {callsign} ", 'highlightline')
                text_widget.insert(tk.END, f" = {', '.join(map(str, ids))}\n")

            text_widget.tag_configure('highlightline', background='SkyBlue', foreground="Black", selectbackground='RoyalBlue', selectforeground='white')
            text_widget.config(state='disabled')  # делаем поле только для чтения
        else:
            # Удаляем текстовое поле с прокруткой, если оно существует
            for widget in label.winfo_children():
                if widget != label:
                    widget.destroy()

            label.grid(row=0, column=0, columnspan=5, sticky='nsew')  # Обновляем текст метки
            label.config(text=info_text)

    except FileNotFoundError:
        label.config(text="Ошибка загрузки информации: файл не найден")
    except json.JSONDecodeError:
        label.config(text="Ошибка загрузки информации: ошибка декодирования JSON")
    except ValueError:
        label.config(text="Ошибка загрузки информации: отсутствие или неверный формат времени")
    except Exception as e:
        label.config(text=f"Ошибка загрузки информации: {str(e)}")
        print(e)
