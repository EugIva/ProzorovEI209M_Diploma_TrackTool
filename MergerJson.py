import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import datetime
import FlowInfo
import PushNotify
from functions import file_existing_choose
from tqdm import tqdm

def find_merge_json_files():
    json_files = filedialog.askopenfilenames(filetypes=[("JSON Files", "*.json")])
    return json_files


def find_json_files(self):
    initial_dir = "Exports/trails"
    self.json_files = filedialog.askopenfilenames(initialdir=initial_dir, filetypes=[("JSON Files", "*.json")])
    self.file_entry_merger.delete(0, tk.END)
    self.file_entry_merger.insert(tk.END, ', '.join(self.json_files))
    display_json_files(self)


def display_json_files(self):
    self.treeview.delete(*self.treeview.get_children())
    flights = {}
    total_flights = 0
    for file in self.json_files:
        with open(file, 'r') as f:
            data = json.load(f)
            for item in data:
                id = item['id']
                if id not in flights:
                    flights[id] = {'items': [item], 'file': file}
                else:
                    flights[id]['items'].append(item)
    for id, flight in flights.items():
        items = flight['items']
        items.sort(key=lambda x: x['time'])
        first_time = datetime.datetime.strptime(items[0]['time'], '%Y-%m-%d %H:%M:%S.%f')
        last_time = datetime.datetime.strptime(items[-1]['time'], '%Y-%m-%d %H:%M:%S.%f')
        flight_time = last_time - first_time
        route_points = len(items)
        callsign = items[0]['callsign']
        airport_origin = items[0]['airportOrigin']
        airport_destination = items[0]['airportDestination']
        self.treeview.insert("", "end", text=flight['file'],
                             values=(id, callsign, str(flight_time), route_points, airport_origin, airport_destination),
                             tags=(flight['file'],))
        total_flights += 1
    self.stats_label.config(text=f"Количество рейсов: {total_flights}, Удалено: 0")


def merge_json_files(self):
    try:
        output_file_name = self.output_file_entry.get()
        if output_file_name:
            file_path = f"Exports/jsonMerge/{output_file_name}.json"
            file_existing_choose(file_path)
            merged_data = []

            pbar = tqdm(self.treeview.get_children())
            for item in pbar:
                pbar.set_description('Сохранение нового потока')
                if self.treeview.exists(item):
                    file_path = self.treeview.item(item, 'tags')[0]
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        flight_data = [item_data for item_data in data if
                                       item_data['id'] == self.treeview.item(item, 'values')[0]]
                        flight_data.sort(key=lambda x: x['time'], reverse=True)
                        merged_data.extend(flight_data)

            output_folder = "Exports/jsonMerge"

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            output_file_path = os.path.join(output_folder, output_file_name + ".json")

            with open(output_file_path, 'w') as f:
                json.dump(merged_data, f, indent=4)

            FlowInfo.display_flow_info(output_file_path, self.file_info_label_merger, None)

            self.stats_label.config(text=f"Создание файлов завершено успешно и помещено в {output_file_path}")
            print("JSON файл успешно создан.")
            PushNotify.notify_popup('Объединение и редактирование JSON',
                                    f'Создание файла {output_file_name} завершено успешно')
        else:
            print("Введите название для создания файла.")
    except Exception as e:
        print(f"{e}")
        messagebox.showerror("Ошибка", "Файл не корректный. Проверьте формат или содержимое файла.")


def delete_selected_items(self):
    selection = self.treeview.selection()
    for item in selection:
        self.treeview.delete(item)
    total_flights = len(self.treeview.get_children())
    stats_text = self.stats_label.cget("text")
    if ", " in stats_text:
        _, deleted_flights_str = stats_text.split(", ")
        if ": " in deleted_flights_str:
            _, deleted_flights_str = deleted_flights_str.split(": ")
            deleted_flights = int(deleted_flights_str) + len(selection)
        else:
            deleted_flights = len(selection)
    else:
        deleted_flights = len(selection)
    self.stats_label.config(text=f"Количество рейсов: {total_flights}, Удалено: {deleted_flights}")
