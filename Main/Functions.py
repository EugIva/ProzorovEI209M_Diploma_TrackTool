import datetime
import importlib
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, filedialog, ttk

from FlightRadar24 import FlightRadar24API

import Main.FlowVisualization.FlowInfo
import Main.PushNotify
import Main.TracksGeneration.Sniffer24 as snf
import Main.TracksGeneration.Trails24 as trl

sniffer = None


# Запуск сниффера
def launch_timer(session_time_entry, latitude_entry, longitude_entry, radius_entry, filename_entry, callsign_entry,
                 origin_airport_entry, on_ground_combobox, file_info_label):
    """
    Запуск генерации треков - онлайн-сниффера
    """
    global sniffer

    if not os.path.exists('Exports/sniffer'):
        os.makedirs('Exports/sniffer')

    file_path_info = os.path.join("Exports", "sniffer", f"{filename_entry.get()}.json")

    total_seconds = int(session_time_entry.get())
    finish_time = time.time() + total_seconds
    point_area = (float(latitude_entry.get()), float(longitude_entry.get()), int(radius_entry.get()))
    bounds = fr_api.get_bounds_by_point(point_area[0], point_area[1], point_area[2])
    filename = f"Exports/sniffer/{filename_entry.get()}.json"

    dir_path, file_name = os.path.split(filename)
    file_name_short = os.path.splitext(file_name)[0]

    file_existing_choose(filename)

    sniff = snf.Sniffer24(bounds, filename, finish_time, callsign_entry.get(), origin_airport_entry.get(),
                          on_ground_combobox.get())
    sniff.launch_counter()

    Main.FlowVisualization.FlowInfo.display_flow_info(file_path_info, file_info_label, None)
    Main.PushNotify.notify_popup('Генерация треков', f'Создание файла {file_name_short} с потоком завершено успешно')


def file_existing_choose(filename):
    """
    Проверка наличия одноимённого файла и выбор действия в случае наличия такого
    """
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            file_content = f.read()
            if file_content:
                try:
                    data = json.loads(file_content)
                    # Проверка, что файл не пустой
                    if data:
                        # Получение времени из файла чтобы пихнуть его в название
                        f.close()
                        delete_json_file(filename, data)

                    else:
                        # Очистка пустого файла
                        f.close()
                        delete_json_file(filename, 0)
                except json.JSONDecodeError:
                    f.close()
                    print("Файл не корректный, удаление...")
                    delete_json_file(filename, 0)
            else:
                f.close()
                # Очистка пустого файла
                delete_json_file(filename, 0)
    else:
        print(f"Создание нового файла {filename}...")


def delete_json_file(filename, data):
    """
    Уведомление о совпадающих именах и удаление лишних
    """
    root = tk.Tk()
    root.title("Удаление файла")
    root.geometry("400x100")
    root.iconbitmap("Content/UI/attention.ico")

    label1 = ttk.Label(root, text=f"Найдено совпадение имени файлов.")
    label1.pack(pady=5)
    label2 = ttk.Label(root, text=f"Вы уверены, что хотите удалить файл {filename}?")
    label2.pack()

    def yes_button_command():
        try:
            os.remove(filename)
            messagebox.showinfo("Удаление файла", f"Файл {filename} успешно удален")
            root.destroy()
        except FileNotFoundError:
            messagebox.showerror("Ошибка", f"Файл {filename} не найден")
            root.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении файла {filename}: {e}")
            root.destroy()

    def rename_button_command():
        try:
            time_only = 0
            for item in data:
                datatime = item['time']
                datetime_object = datetime.datetime.strptime(datatime, '%Y-%m-%d %H:%M:%S.%f')  # ! или без .f
                time_only = datetime_object.strftime('%m%d %H%M%S')

            dir_path, file_name = os.path.split(filename)
            file_name_short, _ = os.path.splitext(file_name)
            # Переименование файла
            new_file_name = f'{file_name_short}_{time_only}.json'
            new_file_path = os.path.join(dir_path, new_file_name)
            os.rename(filename, new_file_path)

            file_name_txt = os.path.splitext(file_name)[0]
            file_newName_short = os.path.splitext(new_file_path)[0]
            messagebox.showinfo("Переименование файла",
                                f"Предыдущий файл {file_name_txt} успешно переименован и помещён в {file_newName_short}")
            root.destroy()
        except Exception as e:
            print(f"{e}")
            messagebox.showerror("Ошибка", f"Ошибка при переименовании файла {filename}: {e}")
            root.destroy()

    yes_button = ttk.Button(root, text=" Да ", command=yes_button_command)
    yes_button.pack(side=tk.LEFT, padx=10)

    rename_button = ttk.Button(root, text="Переименовать предыдущий", command=rename_button_command)
    rename_button.pack(side=tk.LEFT, ipadx=20)

    def no_button_command():
        root.destroy()

    no_button = ttk.Button(root, text=" Нет ", command=no_button_command)
    no_button.pack(side=tk.RIGHT, padx=10)

    root.mainloop()


def folder_existing_choose(folder_name):
    """
    Проверка существования одноимённой папки и выбор действия в случае наличия такой
    """
    if os.path.exists(folder_name):
        root = tk.Tk()
        root.title("Папка с таким именем уже существует")
        root.geometry("400x100")
        root.iconbitmap("Content/UI/attention.ico")

        label1 = ttk.Label(root, text=f"Найдено совпадение имени папки.")
        label1.pack(pady=5)
        label2 = ttk.Label(root, text=f"Вы уверены, что хотите удалить папку {folder_name}?")
        label2.pack()

        def yes_button_command():
            try:
                import shutil
                shutil.rmtree(folder_name)
                messagebox.showinfo("Удаление папки", f"Папка {folder_name} успешно удалена")
                root.destroy()
            except FileNotFoundError:
                messagebox.showerror("Ошибка", f"Папка {folder_name} не найдена")
                root.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при удалении папки {folder_name}: {e}")
                root.destroy()

        def rename_button_command():
            try:
                # Получение времени создания папки
                creation_time = datetime.datetime.fromtimestamp(os.path.getctime(folder_name))
                time_only = creation_time.strftime('%m%d %H%M%S')

                # Переименование папки
                new_folder_name = f'{folder_name}_{time_only}'
                os.rename(folder_name, new_folder_name)

                messagebox.showinfo("Переименование папки",
                                    f"Предыдущая папка {folder_name} успешно переименована в {new_folder_name}")
                root.destroy()
            except Exception as e:
                print(f"{e}")
                messagebox.showerror("Ошибка", f"Ошибка при переименовании папки {folder_name}: {e}")
                root.destroy()

        def no_button_command():
            root.destroy()

        yes_button = ttk.Button(root, text="Удалить", command=yes_button_command)
        yes_button.pack(side=tk.LEFT, padx=10)

        rename_button = ttk.Button(root, text="Переименовать предыдущую", command=rename_button_command)
        rename_button.pack(side=tk.LEFT, ipadx=20)

        no_button = ttk.Button(root, text="Нет", command=no_button_command)
        no_button.pack(side=tk.RIGHT, padx=10)

        root.mainloop()
    else:
        print(f"Создание новой папки {folder_name}...")


def delete_file(filename):
    try:
        os.remove(filename)
        messagebox.showinfo("Удаление файла", f"Файл {filename} успешно удален")
    except FileNotFoundError:
        messagebox.showerror("Ошибка", f"Файл {filename} не найден")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при удалении файла {filename}: {e}")


def start_programm(full_module_path, function_name, *args, **kwargs):
    """
    Универсальный запуск подпрограмм
    """
    # деление на package и module
    module_parts = full_module_path.split('.')
    package_name = '.'.join(module_parts[:-1])
    module_name = module_parts[-1]

    # проверка путей к модулям
    package_dir = os.path.join(os.path.dirname(__file__), *package_name.split('.'))
    if package_dir not in sys.path:
        sys.path.insert(0, package_dir)

    try:
        module = importlib.import_module(full_module_path)
        function = getattr(module, function_name)
        return function(*args, **kwargs)
    except Exception as e:
        print(f"{e}")
        messagebox.showerror("Ошибка", "Файл не корректный или не выбран. Проверьте формат или содержимое файла.")


def open_folder(folder_name):
    """
    Кнопка "открыть папку"
    """
    root_dir = os.path.dirname(os.path.dirname(__file__))

    folder_path = os.path.join(root_dir, "Exports", f"{folder_name}")
    if os.path.exists(folder_path):
        if os.name == 'nt':
            os.startfile(folder_path)
        elif os.name == 'posix':
            subprocess.run(['open', folder_path])
    else:
        print("Папка не обнаружена")


def find_file(file_entry, title):
    """
    Кнопка "поиск" для выбора файла.
    """
    file_entry.delete(0, tk.END)
    file_path = filedialog.askopenfilename(initialdir="Exports/trails/", title=f"{title}")
    if file_path:
        file_entry.insert(0, file_path)


def launch_trail_getter(treeview, filename_entry, iterations_entry, pause_entry, pause_trail_entry, file_info_label):
    """
    Запуск получения треков с помощью слепка
    """
    try:
        filename = filename_entry.get()

        if not filename.endswith('.json'):
            filename += '.json'

        if not os.path.exists('Exports/trails'):
            os.makedirs('Exports/trails')

        filename = os.path.join('Exports', 'trails', filename)

        dir_path, file_name = os.path.split(filename)
        file_name_short = os.path.splitext(file_name)[0]

        file_existing_choose(filename)

        coords = []
        for row in treeview.get_children():
            coord = treeview.item(row)['values']
            coords.append((coord[0], float(coord[1]), float(coord[2]), float(coord[3])))

        getter = trl.Trails24(coords, filename)
        iterations = int(iterations_entry.get()) if iterations_entry.get() else 1
        pause_time = int(pause_entry.get()) if pause_entry.get() else 0
        pause_trail_time = int(pause_trail_entry.get()) if pause_trail_entry.get() else 0

        getter.launch_counter(iterations, pause_time, pause_trail_time)

        file_path = f"Exports/trails/{filename_entry.get()}.json"
        Main.FlowVisualization.FlowInfo.display_flow_info(file_path, file_info_label, None)

        Main.PushNotify.notify_popup('Генерация треков',
                                     f'Создание файла {file_name_short} со слепком потока завершено успешно')

    except Exception as e:
        print(f"launch_trail_getter error: {e}")


# Коды для кнопок на форме слепка
def add_coords_to_table(treeview, city_entry, radius_entry, latitude_entry, longitude_entry):
    """
    Кнопка на форме слепка для добавления координат в таблицу
    """
    try:
        city = city_entry.get()
        radius = radius_entry.get()
        latitude = latitude_entry.get()
        longitude = longitude_entry.get()

        if city and radius and latitude and longitude:
            treeview.insert('', 'end', values=(city, radius, latitude, longitude))
            city_entry.delete(0, 'end')
            radius_entry.delete(0, 'end')
            latitude_entry.delete(0, 'end')
            longitude_entry.delete(0, 'end')
    except Exception as e:
        print(f"{e}")
        messagebox.showerror("Ошибка", "Файл не корректный или не выбран. Проверьте формат или содержимое файла.")


def delete_coords_from_table(treeview):
    """
    Кнопка на форме слепка для удаления координат из таблицы
    """
    try:
        selected_item = treeview.selection()[0]
        treeview.delete(selected_item)
    except Exception as e:
        print(f"{e}")


def import_coords_from_file(treeview):
    """
    Кнопка на форме слепка для импортирования координат в таблицу
    """
    try:
        initial_dir = "Content\CoordPacks"
        file_path = filedialog.askopenfilename(title="Выберите файл со списком координат", initialdir=initial_dir,
                                               filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as f:
                coords = json.load(f)
                for coord in coords:
                    treeview.insert('', 'end',
                                    values=(coord['city'], coord['radius'], coord['latitude'], coord['longitude']))
    except Exception as e:
        print(f"{e}")
        messagebox.showerror("Ошибка", "Файл не корректный или не выбран. Проверьте формат или содержимое файла.")


def export_coords_to_file(treeview):
    """
    Кнопка на форме слепка для экспортирования координат из таблицы
    """
    try:
        initial_dir = "Content\CoordPacks"
        file_path = filedialog.asksaveasfilename(title="Save file", initialdir=initial_dir, defaultextension=".json",
                                                 filetypes=[("JSON files", "*.json")])
        if file_path:
            coords = []
            for row in treeview.get_children():
                coord = treeview.item(row)['values']
                coords.append({'city': coord[0], 'radius': coord[1], 'latitude': coord[2], 'longitude': coord[3]})
            with open(file_path, 'w') as f:
                json.dump(coords, f)
    except Exception as e:
        print(f"{e}")
        messagebox.showerror("Ошибка", "Что-то пошло не так.")


# Очистка полей в фильтре снифера
def clear_field(field, switch_var):
    """
    Очистка полей в фильтре снифера
    """
    if switch_var.get() == 0:
        if field.get() != "":
            if messagebox.askyesno("Очистка поля", "Поле будет очищено"):
                if isinstance(field, ttk.Combobox):
                    field.set('')
                else:
                    field.delete(0, tk.END)
                if isinstance(field, ttk.Combobox):
                    field.config(state='readonly')
                else:
                    field.config(state='disabled')
            else:
                switch_var.set(1)
        else:
            if isinstance(field, ttk.Combobox):
                field.config(state='readonly')
            else:
                field.config(state='disabled')
    else:
        if isinstance(field, ttk.Combobox):
            field.config(state='readonly')
        else:
            field.config(state='normal')


def enable_field(field):
    if isinstance(field, ttk.Combobox):
        field.config(state='readonly')
    else:
        field.config(state='normal')


def disable_field(field):
    if isinstance(field, ttk.Combobox):
        field.config(state='disabled')
    else:
        field.config(state='disabled')


# Окно справочной информации по кнопке "?", для каждой вкладки берётся свой текст из txt файла
def show_info(self, text):
    """
    Окно справочной информации по кнопке "?"
    """
    info_window = tk.Toplevel(self.root)
    info_window.title("Справочная информация")
    info_window.iconbitmap("Content/UI/logo.ico")
    wrapped_text = textwrap.fill(text, width=80)
    info_label = ttk.Label(info_window, text=wrapped_text, font=self.font_txt, foreground='grey', justify="left",
                           anchor="w", wraplength=400)
    info_label.pack(padx=10, pady=10)


def read_help_texts(file_name):
    """
    Получение информации для кнопки "?"
    """
    with open(file_name, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    help_texts = {}
    current_key = None

    for line in lines:
        line = line.strip()

        if line.startswith('### '):
            current_key = line[4:]
        elif current_key:
            if current_key not in help_texts:
                help_texts[current_key] = ''
            help_texts[current_key] += line + '\n'

    return help_texts


# форматирование экспорта
def clear_exports(self):
    """
    Очистка всех данных, сохранённых программой
    """
    confirmation_window = tk.Toplevel(self.root)
    confirmation_window.title("Подтверждение")
    confirmation_window.iconbitmap("Content/UI/attention.ico")

    confirmation_label = ttk.Label(confirmation_window,
                                   text="Вы уверены, что хотите удалить все файлы в директории 'Exports'?")
    confirmation_label.pack(padx=10, pady=10)

    def confirm_deletion():
        exports_dir = "Exports"
        if os.path.exists(exports_dir):
            shutil.rmtree(exports_dir)
            os.makedirs(exports_dir)
        confirmation_window.destroy()

    confirm_button = ttk.Button(confirmation_window, text="Да", command=confirm_deletion)
    confirm_button.pack(side="left", padx=10, pady=10)

    cancel_button = ttk.Button(confirmation_window, text="Нет", command=confirmation_window.destroy)
    cancel_button.pack(side="right", padx=10, pady=10)

    Main.PushNotify.notify_popup('Очистка контента', 'Все сгенерированные данные в папке exports удалены успешно')


def sort_by_column(self, tv, col, descending):
    """
    Сортировки столбиков таблиц
    """
    data = []
    if col == "#0":
        for child in tv.get_children(''):
            data.append((tv.item(child, 'text'), child))
    else:
        for child in tv.get_children(''):
            data.append((tv.set(child, col), child))
    if col == "route_points":
        data.sort(key=lambda x: int(x[0]), reverse=descending)
    elif col == "flight_time":
        def parse_time(time_str):
            try:
                return datetime.datetime.strptime(time_str, "%H:%M")
            except ValueError:
                return datetime.datetime.strptime(time_str, "%H:%M:%S")

        data.sort(key=lambda x: parse_time(x[0]), reverse=descending)
    else:
        data.sort(reverse=descending)
    for ix, item in enumerate(data):
        tv.move(item[1], '', ix)
    tv.heading(col, command=lambda: sort_by_column(self, tv, col, int(not descending)))


fr_api = FlightRadar24API()
