import datetime
import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tqdm import tqdm
import Main.PushNotify
from Main.Functions import folder_existing_choose


class FlowSorter:
    def __init__(self, gui):
        self.gui = gui
        self.correct_items = []
        self.incorrect_items = []
        self.last_move = None
        self.correct_ids = set()
        self.incorrect_ids = set()
        self.flights = {}

    def find_json_files(self):
        json_files = filedialog.askopenfilenames(initialdir="Exports/trails", filetypes=[("JSON Files", "*.json")])
        self.gui.json_files = json_files
        self.gui.file_entry_sorting.delete(0, tk.END)
        self.gui.file_entry_sorting.insert(tk.END, ', '.join(json_files))
        self.display_json_files()

    def find_sorting_frame_files(self):
        file_path = filedialog.askopenfilename(initialdir="Exports/", filetypes=[("JSON Files", "*.json")])
        if file_path:
            try:
                self.gui.file_entry_autosorting.delete(0, tk.END)
                self.gui.file_entry_autosorting.insert(tk.END, file_path)  # Вставляем полный путь без запятых
                with open(file_path, 'r') as file:
                    template = json.load(file)
                    self.correct_ids = {(item[0], item[1]) for item in template.get("correct_ids", [])}
                    self.incorrect_ids = {(item[0], item[1]) for item in template.get("incorrect_ids", [])}
                    # Обновляем метки с информацией о шаблоне
                    self.update_template_info(len(self.correct_ids), len(self.incorrect_ids))
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить шаблон: {str(e)}")

    def update_template_info(self, correct_count, incorrect_count):
        # Обновляем метки с информацией о шаблоне
        self.gui.correct_template_value.config(text=str(correct_count))
        self.gui.incorrect_template_value.config(text=str(incorrect_count))

    def display_json_files(self):
        """
        Отображение потоков в табличке
        """
        self.correct_items.clear()
        self.incorrect_items.clear()
        self.gui.correct_count_label.config(text=f"")
        self.gui.incorrect_count_label.config(text=f"")
        self.gui.treeview_sorting.delete(*self.gui.treeview_sorting.get_children())
        flights = {}
        total_flights = 0
        for file in self.gui.json_files:
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
            self.gui.treeview_sorting.insert("", "end", text=flight['file'],
                                             values=(id, callsign, str(flight_time), route_points, airport_origin,
                                                     airport_destination),
                                             tags=(flight['file'],))
            total_flights += 1
        self.gui.stats_label_sorting.config(text=f"Общее количество рейсов: {total_flights}")

        # Обновляем метку с общим количеством рейсов
        self.gui.total_flights_value.config(text=str(total_flights))

    def move_to_correct(self):
        """
        Пометка рейса как корректного и перенос в определённый список
        """
        selection = self.gui.treeview_sorting.selection()
        for item in selection:
            self.correct_items.append(self.gui.treeview_sorting.item(item, 'values'))
            self.gui.treeview_sorting.delete(item)
        self.gui.correct_count_label.config(text=f"Корректных: {len(self.correct_items)}")
        self.last_move = 'correct'

    def move_to_incorrect(self):
        """
        Пометка рейса как некорректного и перенос в определённый список
        """
        selection = self.gui.treeview_sorting.selection()
        for item in selection:
            self.incorrect_items.append(self.gui.treeview_sorting.item(item, 'values'))
            self.gui.treeview_sorting.delete(item)
        self.gui.incorrect_count_label.config(text=f"Испорченных: {len(self.incorrect_items)}")
        self.last_move = 'incorrect'

    def undo_last_move(self):
        """
        Отмена последнего действия, возврат ранее отмеченного рейса из категории в список
        """
        if self.last_move == 'correct':
            if self.correct_items:
                last_item = self.correct_items.pop()
                self.gui.treeview_sorting.insert("", "end", text='возврат из корректных',
                                                 values=(
                                                     last_item[0], last_item[1], last_item[2], last_item[3],
                                                     last_item[4],
                                                     last_item[5]))
                self.gui.correct_count_label.config(text=f"Корректных: {len(self.correct_items)}")
        elif self.last_move == 'incorrect':
            if self.incorrect_items:
                last_item = self.incorrect_items.pop()
                self.gui.treeview_sorting.insert("", "end", text='возврат из испорченных',
                                                 values=(
                                                     last_item[0], last_item[1], last_item[2], last_item[3],
                                                     last_item[4],
                                                     last_item[5]))
                self.gui.incorrect_count_label.config(text=f"Испорченных: {len(self.incorrect_items)}")
        self.last_move = None

    def clear_sort(self):
        self.correct_items.clear()
        self.incorrect_items.clear()
        self.gui.correct_count_label.config(text=f"Сортировка очищена")
        self.gui.incorrect_count_label.config(text=f"")

    def export_sorted_files(self):
        """
        Ручная сортировка рейсов потока на качественные и некачественные
        """
        if self.gui.sort_notebook.tab(self.gui.sort_notebook.select(), 'text').strip() == " Автоматическая сортировка ":
            self.auto_export_sorted_files()
        else:
            self.manual_export_sorted_files()

    def manual_export_sorted_files(self):
        try:
            output_folder = "Exports/flowSorted"
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            folder_name = self.gui.sorted_name_var.get()
            if folder_name:
                folder_path = os.path.join(output_folder, folder_name)
                folder_existing_choose(folder_path)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                correct_file_path = os.path.join(folder_path, f"{folder_name}_Correct.json")
                correct_data = []
                pbar_correct = tqdm(self.correct_items)
                for id in pbar_correct:
                    pbar_correct.set_description('Сохранение корректных треков')
                    for file in self.gui.json_files:
                        with open(file, 'r') as f:
                            data = json.load(f)
                            correct_data.extend([item_data for item_data in data if item_data['id'] == id[0]])
                with open(correct_file_path, 'w') as f:
                    json.dump(correct_data, f, indent=4)
                incorrect_file_path = os.path.join(folder_path, f"{folder_name}_Incorrect.json")
                incorrect_data = []
                pbar_incorrect = tqdm(self.incorrect_items)
                for id in pbar_incorrect:
                    pbar_incorrect.set_description('Сохранение испорченных треков')
                    for file in self.gui.json_files:
                        with open(file, 'r') as f:
                            data = json.load(f)
                            incorrect_data.extend([item_data for item_data in data if item_data['id'] == id[0]])
                print('Сортировка завершена, дождитесь сохранения файлов...')
                with open(incorrect_file_path, 'w') as f:
                    json.dump(incorrect_data, f, indent=4)
                print("Поток успешно отсортирован.")
                self.correct_items.clear()
                self.incorrect_items.clear()
                self.gui.correct_count_label.config(text=f"")
                self.gui.incorrect_count_label.config(text=f"")
                self.gui.stats_label_sorting.config(
                    text=f"Создание файлов завершено успешно и сохранено в {folder_name}")
                Main.PushNotify.notify_popup('Сортировка треков потока',
                                             f'Создание файлов завершено успешно и сохранено в {folder_name} ')
            else:
                print("Введите название для создания файла.")
        except Exception as e:
            print(f"{e}")
            messagebox.showerror("Ошибка", "Файл не корректный. Проверьте формат или содержимое файла.")

    def auto_export_sorted_files(self):
        main_file_path = self.gui.file_entry_sorting.get()
        output_name = self.gui.sorted_name_var.get()

        if not main_file_path or not output_name:
            messagebox.showwarning("Предупреждение", "Выберите файл потока и укажите имя выходных файлов.")
            return

        try:
            output_dir = os.path.join("Exports", "flowSorted", output_name)
            folder_existing_choose(output_dir)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            with open(main_file_path, 'r') as file:
                self.flights = json.load(file)

            correct_flights = []
            incorrect_flights = []

            # Разделяем рейсы по id
            flights_by_id = {}
            for flight in self.flights:
                flight_id = flight.get('id')
                callsign = flight.get('callsign')
                key = (flight_id, callsign)
                if key not in flights_by_id:
                    flights_by_id[key] = []
                flights_by_id[key].append(flight)

            pbar_flights = tqdm(flights_by_id.items())
            for key, flights in pbar_flights:
                pbar_flights.set_description('Сортировка треков по шаблону')
                if key in self.correct_ids:
                    correct_flights.extend(flights)
                elif key in self.incorrect_ids:
                    incorrect_flights.extend(flights)

            correct_output_path = os.path.join(output_dir, f"{output_name}_Correct.json")
            incorrect_output_path = os.path.join(output_dir, f"{output_name}_Incorrect.json")

            with open(correct_output_path, 'w') as correct_file:
                json.dump(correct_flights, correct_file, indent=4)

            with open(incorrect_output_path, 'w') as incorrect_file:
                json.dump(incorrect_flights, incorrect_file, indent=4)

            Main.PushNotify.notify_popup('Автоматическая сортировка треков потока',
                                         f'Создание файлов завершено успешно и сохранено в {output_dir} ')

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отсортировать файлы: {str(e)}")
