import json
import os
import tkinter as tk
from tkinter import ttk, filedialog

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tqdm import tqdm

import Main


class RouteCutter:
    def __init__(self, root):
        self.root = root
        self.flights = {}
        self.selected_flight = None
        self.selected_rows = []
        self.cut_rows = {}  # Словарь для хранения вырезанных строк для каждого рейса

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # форма выбора файла
        self.file_frame = ttk.Frame(self.main_frame)
        self.file_frame.pack(fill="x")

        self.file_label = ttk.Label(self.file_frame, text="Выберите файл(ы):", font=('Fira Code SemiBold', 10), foreground='grey',
                                    justify="right", anchor="e")
        self.file_label.pack(side="left", padx=10, pady=10)

        self.file_entry = ttk.Entry(self.file_frame, width=60)
        self.file_entry.pack(side="left", padx=10, pady=10)

        self.file_button = ttk.Button(self.file_frame, text="Поиск", command=self.find_json_files)
        self.file_button.pack(side="left", padx=10, pady=10)

        self.save_button = ttk.Button(self.file_frame, text="Сохранить", command=self.save_changes,
                                      style='Accent.TButton')
        self.save_button.pack(side="left", padx=10, pady=10)

        self.open_folder_button_cutter = ttk.Button(self.file_frame, text="Открыть папку",
                                                    command=lambda: Main.Functions.open_folder("flowSorted"))
        self.open_folder_button_cutter.pack(side="left", padx=10, pady=10)

        # выбор рейса
        self.flight_frame = ttk.Frame(self.main_frame)
        self.flight_frame.pack(fill="x")

        self.flight_label = ttk.Label(self.flight_frame, text="   Выберите рейс:", font=('Fira Code SemiBold', 10), foreground='grey')
        self.flight_label.pack(side="left", padx=10, pady=10)

        self.flight_combo = ttk.Combobox(self.flight_frame)
        self.flight_combo.pack(side="left", padx=10, pady=10)
        self.flight_combo.bind("<<ComboboxSelected>>", self.on_flight_selected)

        # кнопки слева
        self.left_buttons_frame = ttk.Frame(self.flight_frame)
        self.left_buttons_frame.pack(side="left")

        self.cut_button = ttk.Button(self.left_buttons_frame, text="Вырезать", command=self.cut_selected_rows)
        self.cut_button.pack(side="left", padx=10, pady=10)

        # кнопки справа
        self.right_buttons_frame = ttk.Frame(self.flight_frame)
        self.right_buttons_frame.pack(side="right")

        self.delete_button = ttk.Button(self.right_buttons_frame, text="Удалить", command=self.delete_selected_rows)
        self.delete_button.pack(side="right", padx=10, pady=10)

        self.clear_button = ttk.Button(self.right_buttons_frame, text="Очистить", command=self.clear_right_table)
        self.clear_button.pack(side="right", padx=10, pady=10)

        # таблицы и графики
        self.tables_frame = ttk.Frame(self.main_frame)
        self.tables_frame.pack(fill="both", expand=True)

        self.left_table_frame = ttk.Frame(self.tables_frame)
        self.left_table_frame.pack(side="left", fill="both", expand=True)

        self.right_table_frame = ttk.Frame(self.tables_frame)
        self.right_table_frame.pack(side="right", fill="both", expand=True)

        self.left_table = ttk.Treeview(self.left_table_frame,
                                       columns=("row", "time", "latitude", "longitude", "altitude"), show="headings")
        self.left_table.column("row", width=50)
        self.left_table.column("time", width=150)
        self.left_table.column("latitude", width=100)
        self.left_table.column("longitude", width=100)
        self.left_table.column("altitude", width=100)
        self.left_table.heading("row", text="Номер строки")
        self.left_table.heading("time", text="Время")
        self.left_table.heading("latitude", text="Широта")
        self.left_table.heading("longitude", text="Долгота")
        self.left_table.heading("altitude", text="Высота")
        self.left_table.pack(fill="both", expand=True, pady=5, ipady=80)

        self.yscrollbar_left = ttk.Scrollbar(self.left_table, orient="vertical",
                                             command=self.left_table.yview)
        self.yscrollbar_left.pack(side="right", fill="y")
        self.left_table.config(yscrollcommand=self.yscrollbar_left.set)

        self.right_table = ttk.Treeview(self.right_table_frame,
                                        columns=("row", "time", "latitude", "longitude", "altitude"), show="headings")
        self.right_table.column("row", width=50)
        self.right_table.column("time", width=150)
        self.right_table.column("latitude", width=100)
        self.right_table.column("longitude", width=100)
        self.right_table.column("altitude", width=100)
        self.right_table.heading("row", text="Номер строки")
        self.right_table.heading("time", text="Время")
        self.right_table.heading("latitude", text="Широта")
        self.right_table.heading("longitude", text="Долгота")
        self.right_table.heading("altitude", text="Высота")
        self.right_table.pack(fill="both", expand=True, pady=5, ipady=80)

        self.yscrollbar_right = ttk.Scrollbar(self.right_table, orient="vertical",
                                              command=self.right_table.yview)
        self.yscrollbar_right.pack(side="right", fill="y")
        self.right_table.config(yscrollcommand=self.yscrollbar_right.set)

        # кнопки графиков
        self.left_plot_frame = ttk.Frame(self.left_table_frame)
        self.left_plot_frame.pack(fill="both", expand=True, ipady=10)

        self.right_plot_frame = ttk.Frame(self.right_table_frame)
        self.right_plot_frame.pack(fill="both", expand=True, ipady=10)

        self.left_figure = plt.Figure(figsize=(5, 4), dpi=100)
        self.left_ax = self.left_figure.add_subplot(111)
        self.left_canvas = FigureCanvasTkAgg(self.left_figure, master=self.left_plot_frame)
        self.left_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        self.left_toolbar = NavigationToolbar2Tk(self.left_canvas, self.left_plot_frame)
        self.left_toolbar.update()
        self.left_canvas._tkcanvas.pack(side="top", fill="both", expand=True)

        self.right_figure = plt.Figure(figsize=(5, 4), dpi=100)
        self.right_ax = self.right_figure.add_subplot(111)
        self.right_canvas = FigureCanvasTkAgg(self.right_figure, master=self.right_plot_frame)
        self.right_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        self.right_toolbar = NavigationToolbar2Tk(self.right_canvas, self.right_plot_frame)
        self.right_toolbar.update()
        self.right_canvas._tkcanvas.pack(side="top", fill="both", expand=True)

        # биндинг ивент
        self.left_table.bind("<Button-1>", self.select_row)

    def find_json_files(self):
        """
        Выбрать файл для дальнейшей работы, проверить совпадения
        """
        file_path = filedialog.askopenfilename(title="Выберите файл", filetypes=[("JSON Files", "*.json")])
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)
            self.clear_right_table()  # Очистить правую таблицу и словарь cut_rows
            self.load_json_file(file_path)
            self.selected_rows = []  # Очистить выбранные строки

            dir_path, file_name = os.path.split(file_path)
            file_name_short = os.path.splitext(file_name)[0]
            file_extension = os.path.splitext(file_name)[1]
            cut_file_path = os.path.join(dir_path, f"Cut_{file_name_short}{file_extension}")
            Main.Functions.file_existing_choose(cut_file_path)

    def load_json_file(self, file_path):
        """
        Загрузить выбранный файл
        """
        self.cut_rows = {}  # очистить cut_rows
        with open(file_path, 'r') as file:
            data = json.load(file)
            self.flights = {}
            for i, flight in enumerate(data):
                flight['row'] = i
                if flight['id'] not in self.flights:
                    self.flights[flight['id']] = []
                self.flights[flight['id']].append(flight)
            self.update_flight_combo()

    def update_flight_combo(self):
        """
        Заполнить комбобокс выбора рейса
        """
        callsigns = set(flight['callsign'] for flight_id in self.flights for flight in self.flights[flight_id])
        sorted_callsigns = sorted(list(callsigns))
        self.flight_combo['values'] = sorted_callsigns

    def on_flight_selected(self, event):
        self.selected_flight = self.flight_combo.get()
        self.selected_rows = []  # очистить выбранные строки
        self.display_flight_data()
        self.plot_flight_data()

    def display_flight_data(self):
        """
        Отобразить информацию о рейсе в левой таблице
        """
        self.left_table.delete(*self.left_table.get_children())
        for flight_id in self.flights:
            for row in self.flights[flight_id]:
                if row['callsign'] == self.selected_flight:
                    time = row.get('time', 'Unknown')
                    latitude = row.get('latitude', 0)
                    longitude = row.get('longitude', 0)
                    altitude = row.get('altitude_Ft', 0)
                    self.left_table.insert('', 'end', values=(
                        row['row'], time, latitude, longitude, int(float(altitude) * 0.3048)))
        self.plot_flight_data()

        # Очистить правую таблицу и загрузить сохраненные вырезанные строки для выбранного рейса
        self.right_table.delete(*self.right_table.get_children())
        if self.selected_flight in self.cut_rows:
            for row in self.cut_rows[self.selected_flight]:
                self.right_table.insert('', 'end', values=row)
        self.plot_cut_data()

    def plot_flight_data(self):
        """
        Нарисовать трек самолёта
        """
        self.left_ax.clear()
        data = [row for flight_id in self.flights for row in self.flights[flight_id] if
                row['callsign'] == self.selected_flight]
        latitudes = [float(row.get('latitude', 0)) for row in data]
        longitudes = [float(row.get('longitude', 0)) for row in data]

        # нарисовать путь самолёта
        self.left_ax.plot(longitudes, latitudes, 'b-')
        self.left_ax.scatter(longitudes, latitudes, c='r')

        # подстветить выбранные точки
        if self.selected_rows:
            selected_latitudes = [float(row[2]) for row in self.selected_rows]
            selected_longitudes = [float(row[3]) for row in self.selected_rows]
            self.left_ax.scatter(selected_longitudes, selected_latitudes, c='g', s=100, edgecolors='black',
                                 linewidths=2)

        # пометить начало трека
        if data:
            first_latitude = float(data[0].get('latitude', 0))
            first_longitude = float(data[0].get('longitude', 0))
            self.left_ax.scatter([first_longitude], [first_latitude], marker='s', c='lime', s=100, edgecolors='black',
                                 linewidths=2)

        self.left_canvas.draw()

    def select_row(self, event):
        """
        Выбрать строки(у)
        """
        rows = self.left_table.selection()
        if rows:
            self.selected_rows = [self.left_table.item(row, 'values') for row in rows]
            self.highlight_selected_points()

    def cut_selected_rows(self):
        """
        Вырезать выбранные строки
        """
        # взять выбранные строки
        selection = self.left_table.selection()
        self.selected_rows = []
        for item in selection:
            # Добавить значения выбранных элементов в список
            self.selected_rows.append(self.left_table.item(item, 'values'))

        # проверка на наличие таких же строк
        existing_rows = [self.right_table.item(row, 'values') for row in self.right_table.get_children()]
        new_rows = [row for row in self.selected_rows if row not in existing_rows]

        # Добавить новые строки в словарь cut_rows
        if self.selected_flight not in self.cut_rows:
            self.cut_rows[self.selected_flight] = []
        self.cut_rows[self.selected_flight].extend(new_rows)

        # Очистить правую таблицу и вставить вырезанные строки
        self.right_table.delete(*self.right_table.get_children())
        for row in self.cut_rows[self.selected_flight]:
            self.right_table.insert('', 'end', values=row)

        self.plot_cut_data()

    def plot_cut_data(self):
        """
        Отобразить на схеме вырезанные строки (правая таблица)
        """
        self.right_ax.clear()
        data = [self.right_table.item(row, 'values') for row in self.right_table.get_children()]
        if data:  # Проверяем что массив не пуст
            try:
                latitudes = [float(row[2]) for row in data if row[2].replace('.', '', 1).isdigit()]
                longitudes = [float(row[3]) for row in data if row[3].replace('.', '', 1).isdigit()]
                self.right_ax.plot(longitudes, latitudes, 'b-')
                self.right_ax.scatter(longitudes, latitudes, c='r')
            except ValueError:
                print("Некорректное значение данных.")
        self.right_canvas.draw()

    def delete_selected_rows(self):
        """
        Удалить записи из правой таблицы
        """
        # Получить выбранный элементы
        selection = self.right_table.selection()
        if selection:
            for item in selection:
                self.right_table.delete(item)
            # Обновить словарь cut_rows
            if self.selected_flight in self.cut_rows:
                self.cut_rows[self.selected_flight] = [self.right_table.item(row, 'values') for row in
                                                       self.right_table.get_children()]
            self.plot_cut_data()

    def clear_right_table(self):
        """
        Очистить записи в правой таблице
        """
        # Очистить нужную таблицу
        self.right_table.delete(*self.right_table.get_children())
        # Очистить словарь cut_rows для выбранного рейса
        if self.selected_flight in self.cut_rows:
            self.cut_rows[self.selected_flight] = []
        self.plot_cut_data()

    def highlight_selected_points(self):
        """
        Выделить на графике выбираемые строки
        """
        self.left_ax.clear()
        data = [row for flight_id in self.flights for row in self.flights[flight_id] if
                row['callsign'] == self.selected_flight]
        latitudes = [float(row.get('latitude', 0)) for row in data]
        longitudes = [float(row.get('longitude', 0)) for row in data]

        # Проложить всю траекторию полета
        self.left_ax.plot(longitudes, latitudes, 'b-')
        self.left_ax.scatter(longitudes, latitudes, c='r')

        # Выделить выбранные точки
        if self.selected_rows:
            selected_latitudes = [float(row[2]) for row in self.selected_rows]
            selected_longitudes = [float(row[3]) for row in self.selected_rows]
            self.left_ax.scatter(selected_longitudes, selected_latitudes, c='g', s=100, edgecolors='black',
                                 linewidths=2)

        self.left_canvas.draw()

    def save_changes(self):
        """
        Экспортировать результат вырезания
        """
        # Загрузить исходный файл в массив данных
        original_file_path = self.file_entry.get()
        with open(original_file_path, 'r') as file:
            data = json.load(file)

        # Извлечь номера строк из cut_rows
        cut_row_numbers = []
        for flight_callsign, rows in self.cut_rows.items():
            for row in rows:
                cut_row_numbers.append(row[0])

        cut_data = []
        pbar = tqdm(cut_row_numbers)
        for row_number in pbar:
            pbar.set_description('Сохранение вырезанных сегментов')
            # Добавляем в cut_data строку из data, по индексу row_number - 1
            row_number = int(row_number)
            cut_data.append(data[row_number])

        # Фильтрация строк из исходных данных на основе значений cut_row_numbers
        new_data = [row for index, row in enumerate(data) if index not in cut_row_numbers]

        # сохранить в новый файл
        dir_path, file_name = os.path.split(original_file_path)
        file_name_short = os.path.splitext(file_name)[0]
        file_extension = os.path.splitext(file_name)[1]
        cut_file_path = os.path.join(dir_path, f"Cut_{file_name_short}{file_extension}")

        # Сохранение в новый файл
        with open(cut_file_path, 'w') as file:
            json.dump(cut_data, file, indent=4)

        print(f"Вырезанные участки сохранены в {cut_file_path}")

        Main.PushNotify.notify_popup('Обрезка треков',
                                     f'Вырезание участков треков сохранено в {file_name_short} и завершено успешно')


if __name__ == "__main__":
    root = tk.Tk()
    app = RouteCutter(root)
    root.mainloop()
