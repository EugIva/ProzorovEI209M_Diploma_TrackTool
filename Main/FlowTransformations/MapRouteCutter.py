import pandas as pd
from tkinter import filedialog, ttk, Tk, messagebox
import tkinter as tk
from tkintermapview import TkinterMapView
from shapely.geometry import Polygon, Point
import numpy as np
import os
import logging
from PIL import Image, ImageTk
import json

from Main import PushNotify
from Main.FlowVisualization.RoutesDrawerMap import change_data_source
from tqdm import tqdm

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class MapRouteCutter:
    def __init__(self, root):
        self.root = root  # root теперь это ttk.Frame, а НЕ Tk
        self.flight_data_global = None
        self.drawn_polygons = []  # Хранит координаты полигонов
        self.original_filepath = None
        self.file_encoding = None
        self.file_format = None  # 'csv' или 'json'
        self.selected_flights = []  # Список выбранных TRIP_IDENT
        self.map_widget = None  # Карта
        self.polygon_id = None  # ID текущего полигона
        self.markers = []  # Список маркеров на карте
        self.is_drawing = False  # Флаг для отслеживания состояния рисования
        self.drawing_polygon = False  # Флаг для отслеживания рисования полигона
        self.polygon_coords = []  # Координаты текущего полигона
        self.setup_ui()

    def setup_ui(self):
        self.font_txt = ('Fira Code SemiBold', 10)

        # --- Основной фрейм ---
        self.main_frame = ttk.Frame(self.root)  # Размещаем во фрейме root
        self.main_frame.pack(fill="both", expand=True)

        # --- Фрейм выбора файла ---
        self.file_frame = ttk.Frame(self.main_frame)
        self.file_frame.pack(fill="both", pady=10)
        file_label = ttk.Label(self.file_frame, text="Выберите файл:", font=self.font_txt)
        file_label.pack(side="left", padx=10)
        self.file_entry = ttk.Entry(self.file_frame, width=60)
        self.file_entry.pack(side="left", padx=10)
        file_button = ttk.Button(self.file_frame, text="Обзор", command=self.load_data)
        file_button.pack(side="left", padx=10)

        # --- Фрейм выбора рейсов ---
        self.flight_frame = ttk.Frame(self.main_frame)
        self.flight_frame.pack(fill="x", pady=10)
        flight_label = ttk.Label(self.flight_frame, text="Выберите рейсы:", font=self.font_txt)
        flight_label.pack(side="left", padx=10)

        # --- Выбор карты ---
        self.data_source_var = tk.StringVar()
        self.data_source_var.set("OpenStreetMap")

        self.data_source_option = ttk.OptionMenu(self.file_frame, self.data_source_var, "OpenStreetMap",
                                                 "OpenStreetMap",
                                                 "Google Maps", "Google спутник", "Google гибрид", "Google рельеф",
                                                 "Светлая", "Тёмная", "Схематичная", "Пустая",
                                                 command=lambda value: change_data_source(self, value))
        self.data_source_option.pack(side="right", padx=5)

        self.data_source_label = ttk.Label(self.file_frame, text="Изображение карты:", font=self.font_txt,
                                           foreground='grey',
                                           justify="right", anchor="e")
        self.data_source_label.pack(side="right", padx=10)

        # Первый селектор рейсов и кнопка "Следующий"
        selector_frame_1 = ttk.Frame(self.flight_frame)
        selector_frame_1.pack(side="left", padx=5)
        self.flight_selector_1 = ttk.Combobox(selector_frame_1, values=[""], state="readonly", width=30)
        self.flight_selector_1.pack(side="left")
        self.flight_selector_1.current(0)  # По умолчанию пустое значение
        next_button_1 = ttk.Button(selector_frame_1, text=" > ", command=self.next_flight_1)
        next_button_1.pack(side="left", padx=2)

        # Второй селектор рейсов и кнопка "Следующий"
        selector_frame_2 = ttk.Frame(self.flight_frame)
        selector_frame_2.pack(side="left", padx=5)
        self.flight_selector_2 = ttk.Combobox(selector_frame_2, values=[""], state="readonly", width=30)
        self.flight_selector_2.pack(side="left")
        self.flight_selector_2.current(0)  # По умолчанию пустое значение
        next_button_2 = ttk.Button(selector_frame_2, text=" > ", command=self.next_flight_2)
        next_button_2.pack(side="left", padx=2)

        # --- Фрейм кнопок ---
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill="x", pady=10)
        self.start_drawing_button = ttk.Button(button_frame, text="Начать рисование", command=self.start_drawing)
        self.start_drawing_button.pack(side="left", padx=5)
        self.finish_drawing_button = ttk.Button(button_frame, text="Завершить рисование", command=self.finish_drawing,
                                                state="disabled")
        self.finish_drawing_button.pack(side="left", padx=5)
        self.clear_polygon_button = ttk.Button(button_frame, text="Очистить полигон", command=self.clear_polygon)
        self.clear_polygon_button.pack(side="left", padx=5)
        export_button = ttk.Button(button_frame, text="Экспорт", command=self.export_data, style='Accent.TButton')
        export_button.pack(side="right", padx=10)

        # --- Карта ---
        self.map_widget = TkinterMapView(self.main_frame, width=800, height=600, corner_radius=0)
        self.map_widget.set_position(55.9739763, 37.4151879)
        self.map_widget.set_zoom(11)
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_tile_server("https://tile.openstreetmap.org/{z}/{x}/{y}.png")  # OpenStreetMap

        # --- Привязка событий ---
        self.flight_selector_1.bind("<<ComboboxSelected>>", lambda event: self.update_map())
        self.flight_selector_2.bind("<<ComboboxSelected>>", lambda event: self.update_map())
        self.map_widget.add_left_click_map_command(self.add_polygon_point)

    def validate_coordinates(self, df):
        try:
            if not (-90 <= df['LATITUDE'].min() <= 90 and -90 <= df['LATITUDE'].max() <= 90):
                return False
            if not (-180 <= df['LONGITUDE'].min() <= 180 and -180 <= df['LONGITUDE'].max() <= 180):
                return False
            return True
        except KeyError:
            return False

    def load_json_data(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Пытаемся преобразовать JSON в DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict) and 'flights' in data:
                df = pd.DataFrame(data['flights'])
            else:
                messagebox.showerror("Ошибка", "Неизвестный формат JSON")
                return None

            # Проверяем и адаптируем столбцы
            if 'TRIP_IDENT' not in df.columns:
                # Проверка альтернативных названий для TRIP_IDENT
                id_columns = [col for col in df.columns if 'id' in col.lower() or 'ident' in col.lower()]
                if id_columns:
                    df['TRIP_IDENT'] = df[id_columns[0]]
                else:
                    df['TRIP_IDENT'] = range(len(df))  # Создаем искусственные ID

            # Проверка наличия столбцов с координатами
            coord_mapping = {
                'LATITUDE': ['lat', 'latitude', 'широта'],
                'LONGITUDE': ['lon', 'lng', 'longitude', 'долгота']
            }

            for target_col, possible_names in tqdm(coord_mapping.items(), desc=f"Загрузка json файла потока"):
                if target_col not in df.columns:
                    for col in df.columns:
                        if col.lower() in possible_names:
                            df[target_col] = df[col]
                            break

            # Преобразуем типы данных
            df['TRIP_IDENT'] = df['TRIP_IDENT'].astype(str)

            return df
        except Exception as e:
            logging.error(f"Ошибка при загрузке JSON: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить JSON: {e}")
            return None

    def load_csv_data(self, filepath):
        encodings_to_try = ['utf-8', 'cp1251', 'latin1']
        for encoding in tqdm(encodings_to_try, desc=f"Загрузка csv файла потока"):
            try:
                df = pd.read_csv(filepath, sep=';', encoding=encoding, quotechar='"', quoting=1)
                self.file_encoding = encoding
                if 'TRIP_IDENT' in df.columns:
                    df['TRIP_IDENT'] = df['TRIP_IDENT'].astype(str)
                return df
            except Exception as e:
                logging.error(f"Ошибка при загрузке CSV с кодировкой {encoding}: {e}")
                continue
        return None

    def load_data(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Supported files", "*.csv;*.json"), ("CSV files", "*.csv"), ("JSON files", "*.json"),
                       ("All files", "*.*")])
        if not filepath:
            return

        self.file_entry.delete(0, "end")
        self.file_entry.insert(0, filepath)

        # Определяем формат файла по расширению
        _, ext = os.path.splitext(filepath)
        self.file_format = ext.lower()

        if self.file_format == '.csv':
            df = self.load_csv_data(filepath)
        elif self.file_format == '.json':
            df = self.load_json_data(filepath)
            self.file_encoding = 'utf-8'  # Для JSON мы всегда будем использовать UTF-8
        else:
            messagebox.showerror("Ошибка", "Неподдерживаемый формат файла")
            return

        if df is not None and self.validate_coordinates(df):
            self.flight_data_global = df.copy()
            self.original_filepath = filepath

            # Получаем уникальные значения TRIP_IDENT для dropdown
            unique_flights = df['TRIP_IDENT'].unique().tolist()

            # Создаем список понятных для пользователя названий рейсов
            flight_display_names = []
            for flight_id in unique_flights:
                flight_data = df[df['TRIP_IDENT'] == flight_id]
                if 'ICAO_FLIGHT_PLAN_NAME' in flight_data.columns and not flight_data[
                    'ICAO_FLIGHT_PLAN_NAME'].isna().all():
                    # Если есть название плана полета ICAO, используем его вместе с ID
                    name = flight_data['ICAO_FLIGHT_PLAN_NAME'].iloc[0]
                    display_name = f"{flight_id} - {name}"
                else:
                    # Иначе используем только ID
                    display_name = flight_id
                flight_display_names.append(display_name)

            # Обновляем выпадающие списки, добавляя пустое значение в начало
            self.flight_selector_1["values"] = [""] + flight_display_names
            self.flight_selector_2["values"] = [""] + flight_display_names

            # Устанавливаем текущее значение на пустое (первый элемент)
            self.flight_selector_1.current(0)
            self.flight_selector_2.current(0)

            # Связываем отображаемые имена с фактическими ID
            self.flight_id_map = {"": None}  # Добавляем пустое значение в карту соответствия
            self.flight_id_map.update({display: unique_flights[i] for i, display in enumerate(flight_display_names)})

            self.initialize_map(df)
        else:
            messagebox.showerror("Ошибка", "Некорректные данные в файле или файл не удалось прочитать.")

    def get_flight_id_from_display(self, display_name):
        """Извлекает ID рейса из отображаемого имени."""
        if not display_name:
            return None

        if display_name in self.flight_id_map:
            return self.flight_id_map[display_name]

        # Если карта не содержит точного совпадения, пытаемся извлечь ID из отображаемого имени
        # Предполагается, что ID находится до первого символа '-'
        if ' - ' in display_name:
            return display_name.split(' - ')[0].strip()

        return display_name

    def initialize_map(self, df):
        try:
            center_lat = df['LATITUDE'].dropna().mean()
            center_lon = df['LONGITUDE'].dropna().mean()
            if pd.isna(center_lat) or pd.isna(center_lon):
                center_lat, center_lon = 0, 0  # Default
        except KeyError:
            center_lat, center_lon = 0, 0
            messagebox.showwarning("Предупреждение",
                                   "Отсутствуют столбцы LATITUDE или LONGITUDE. Карта установлена в (0, 0).")
        self.map_widget.set_position(center_lat, center_lon)
        self.map_widget.set_zoom(6)
        self.update_map()

    def update_map(self):
        if hasattr(self, 'is_drawing') and self.is_drawing:
            return

        self.is_drawing = True
        self.clear_map()  # Очищаем карту перед обновлением

        # Получаем выбранные рейсы из комбобоксов
        selected_display_1 = self.flight_selector_1.get()
        selected_display_2 = self.flight_selector_2.get()

        flight_id_1 = self.get_flight_id_from_display(selected_display_1)
        flight_id_2 = self.get_flight_id_from_display(selected_display_2)

        self.selected_flights = [flight_id_1, flight_id_2]
        colors = ['blue', 'red']  # Цвета для разных маршрутов

        for idx, flight_id in enumerate(filter(None, self.selected_flights)):  # Убираем пустые значения
            flight_data = self.flight_data_global[self.flight_data_global['TRIP_IDENT'] == str(flight_id)].dropna(
                subset=['LATITUDE', 'LONGITUDE'])
            if not flight_data.empty:
                # Добавляем линию (трассу)
                coordinates = flight_data[['LATITUDE', 'LONGITUDE']].to_numpy().tolist()
                if len(coordinates) > 1:  # Нужно хотя бы 2 точки для линии
                    self.map_widget.set_path(coordinates, color=colors[idx % len(colors)], width=2)

                # Добавляем картинки-маркеры для каждой точки трека
                for _, row in tqdm(flight_data.iterrows(), desc=f"Загрузка отрисовки"):
                    self.set_image_marker(row['LATITUDE'], row['LONGITUDE'], idx)

        # Добавляем маркеры для точек полигона
        for polygon_coords in self.drawn_polygons:
            for lat, lon in polygon_coords:
                self.set_polygon_image_marker(lat, lon)

        self.is_drawing = False

    def set_image_marker(self, lat, lon, idx):
        """Устанавливает картинку-маркер на указанную точку."""
        colors = ['blue', 'red']
        try:
            marker = self.map_widget.set_marker(
                lat, lon,
                icon_anchor="s",  # Якорь для центрирования картинки над точкой
                text="",  # Нет текста внутри маркера
                command=None,  # Нет действия при клике на маркер
                marker_color_circle=f"{colors[idx % len(colors)].capitalize()}",
                marker_color_outside=f"{colors[idx % len(colors)].capitalize()}"
            )
            self.markers.append(marker)
        except FileNotFoundError:
            marker = self.map_widget.set_marker(lat, lon)
            self.markers.append(marker)

    def set_polygon_image_marker(self, lat, lon):
        """Устанавливает специальную картинку-маркер для точек полигона."""
        try:
            marker = self.map_widget.set_marker(
                lat, lon,
                icon_anchor="s",  # Якорь для центрирования картинки над точкой
                text="",  # Нет текста внутри маркера
                command=None  # Нет действия при клике на маркер
            )
            self.markers.append(marker)
        except FileNotFoundError:
            marker = self.map_widget.set_marker(lat, lon)
            self.markers.append(marker)

    def clear_map(self):
        """Очищает карту от маркеров, линий и полигонов."""
        self.map_widget.delete_all_marker()
        self.map_widget.delete_all_path()
        if self.polygon_id is not None:
            self.map_widget.delete(self.polygon_id)
            self.polygon_id = None
        self.markers = []  # Очищаем список маркеров

    def start_drawing(self):
        self.drawing_polygon = True
        self.polygon_coords = []
        self.start_drawing_button.config(state="disabled")
        self.finish_drawing_button.config(state="normal")

    def add_polygon_point(self, event):
        if hasattr(self, 'drawing_polygon') and self.drawing_polygon:
            lat, lon = event
            self.polygon_coords.append((lat, lon))
            self.update_drawing_preview()

    def update_drawing_preview(self):
        # Удаляем предыдущий полигон, если он есть
        if self.polygon_id is not None:
            self.map_widget.delete(self.polygon_id)

        if len(self.polygon_coords) >= 2:
            # Рисуем временную линию (используем set_path)
            self.map_widget.set_path(self.polygon_coords + [self.polygon_coords[0]], color="gray",
                                     width=1)  # Замыкаем линию

        if len(self.polygon_coords) >= 3:
            # Рисуем полигон (используем set_polygon)
            self.polygon_id = self.map_widget.set_polygon(self.polygon_coords, outline_color="red", border_width=2,
                                                          fill_color=None)

    def finish_drawing(self):
        if self.drawing_polygon and len(self.polygon_coords) >= 3:
            self.handle_draw(self.polygon_coords)
        else:
            messagebox.showinfo("Информация", "Недостаточно точек для полигона (минимум 3).")
        self.drawing_polygon = False
        self.start_drawing_button.config(state="normal")
        self.finish_drawing_button.config(state="disabled")
        self.polygon_coords = []  # Сбрасываем координаты
        self.update_map()

    def clear_polygon(self):
        if self.polygon_id is not None:
            self.map_widget.delete(self.polygon_id)  # Удаляем полигон по ID
            self.polygon_id = None
        self.drawn_polygons = []  # Очищаем список полигонов

    def handle_draw(self, polygon_coords):
        self.remove_points_in_polygon(polygon_coords)
        self.drawn_polygons.append(polygon_coords)  # Сохраняем координаты полигона
        self.update_map()

    def remove_points_in_polygon(self, polygon_coords):
        polygon = Polygon([(lon, lat) for lat, lon in polygon_coords])  # Shapely: (lon, lat)
        updated_flight_data = self.flight_data_global.copy()
        drop_indices = []

        for flight_id in self.selected_flights:
            if flight_id is None:
                continue
            flight_data = self.flight_data_global[self.flight_data_global['TRIP_IDENT'] == str(flight_id)].dropna(
                subset=['LATITUDE', 'LONGITUDE'])
            for _, row in tqdm(flight_data.iterrows(), desc=f"Удаление точек"):
                point = Point(row['LONGITUDE'], row['LATITUDE'])
                if polygon.contains(point):
                    # Добавляем индекс для последующего удаления
                    drop_indices.append(row.name)

        # Удаляем все отмеченные строки одновременно
        if drop_indices:
            updated_flight_data = updated_flight_data.drop(index=drop_indices)

        self.flight_data_global = updated_flight_data  # Обновляем данные

    def export_data(self):
        if self.flight_data_global is None:
            messagebox.showwarning("Предупреждение", "Нет данных для экспорта.")
            return

        # Определяем путь для экспорта
        if self.original_filepath:
            base_name, ext = os.path.splitext(self.original_filepath)
            suggested_filepath = f"{base_name}_cut{ext}"
        else:
            suggested_filepath = ""

        export_filepath = filedialog.asksaveasfilename(
            defaultextension=self.file_format,
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json")],
            initialfile=os.path.basename(suggested_filepath) if suggested_filepath else ""
        )

        if not export_filepath:
            return

        _, export_ext = os.path.splitext(export_filepath)

        try:
            if export_ext.lower() == '.csv':
                # Экспорт в CSV
                encoding = self.file_encoding or 'utf-8'
                self.flight_data_global.to_csv(
                    export_filepath,
                    index=False,
                    sep=';',
                    encoding=encoding,
                    quotechar='"',
                    quoting=1
                )
            elif export_ext.lower() == '.json':
                # Экспорт в JSON
                result_json = self.flight_data_global.to_dict(orient='records')
                with open(export_filepath, 'w', encoding='utf-8') as f:
                    json.dump(result_json, f, ensure_ascii=False, indent=2)
            else:
                messagebox.showerror("Ошибка", "Неподдерживаемый формат файла для экспорта.")
                return

            PushNotify.notify_popup('Обрезка треков на карте',
                                    f'Данные преобразованы успешно, и сохранены в {export_filepath} ')
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте: {e}")
            logging.error(f"Ошибка при экспорте: {e}")

    def next_flight_1(self):
        """Переключает на следующий рейс в первом выпадающем списке."""
        current_index = self.flight_selector_1.current()
        values = self.flight_selector_1['values']

        if not values or len(values) <= 1:  # Если список пуст или только одно значение (пустое)
            return

        # Переключаемся на следующий элемент, или на первый, если достигнут конец списка
        next_index = (current_index + 1) % len(values)
        self.flight_selector_1.current(next_index)

        # Обновляем карту после смены рейса
        self.update_map()

    def next_flight_2(self):
        """Переключает на следующий рейс во втором выпадающем списке."""
        current_index = self.flight_selector_2.current()
        values = self.flight_selector_2['values']

        if not values or len(values) <= 1:  # Если список пуст или только одно значение (пустое)
            return

        # Переключаемся на следующий элемент, или на первый, если достигнут конец списка
        next_index = (current_index + 1) % len(values)
        self.flight_selector_2.current(next_index)

        # Обновляем карту после смены рейса
        self.update_map()
