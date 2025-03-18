# AiSorter.py

import json
import os
import pickle
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

import pandas as pd
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from Main import Functions, PushNotify
from Main.Functions import folder_existing_choose


class FlightTrackClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super(FlightTrackClassifier, self).__init__()
        # Определяем LSTM слой с заданными параметрами
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        # Определяем линейный слой для классификации
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        # Прямой проход через LSTM слой
        lstm_out, _ = self.lstm(x)
        # Прямой проход через линейный слой, используя последний временной шаг из LSTM
        out = self.fc(lstm_out[:, -1, :])
        return out


def load_data(file_path):
    """
    Загружает данные из JSON-файла и преобразует их в DataFrame.
    :param file_path: Путь к JSON-файлу.
    :return: DataFrame с данными.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            data = json.load(file)  # Загружаем данные как JSON
        except json.JSONDecodeError as e:
            print(f"Ошибка при декодировании JSON: {e}")
            return None
    if not isinstance(data, list):
        print("Данные не представлены в виде списка.")
        return None
    df = pd.DataFrame(data)
    if 'id' not in df.columns:
        print("Колонка 'id' отсутствует в DataFrame. Добавляю искусственный 'id'.")
        df['id'] = df.index  # Просто используем индекс как 'id'
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'],
                                    format='%Y-%m-%d %H:%M:%S.%f')  # Преобразуем поле 'time' в формат datetime
    else:
        print("Колонка 'time' отсутствует в DataFrame.")
    return df


def create_slices(df, slice_length=20):
    """
    Разбивает треки на разрезы фиксированной длины.
    :param df: DataFrame с данными.
    :param slice_length: Длина разреза.
    :return: Список разрезов (каждый разрез — это DataFrame).
    """
    slices = []
    grouped = df.groupby('id')  # Группируем данные по ID рейса
    for _, group in tqdm(grouped, desc=f"Создание разрезов"):
        num_points = len(group)
        if num_points < slice_length:
            slices.append(group.copy())  # Если трек короче slice_length, добавляем его целиком как разрез
        else:
            for i in range(num_points - slice_length + 1):
                slice_df = group.iloc[i:i + slice_length]  # Создаем разрез длиной slice_length
                slices.append(slice_df)
    return slices


def prepare_data_for_model(slices, scaler):
    """
    Подготавливает данные для модели.
    :param slices: Список разрезов данных.
    :param scaler: Нормализатор данных.
    :return: Нормализованные данные.
    """
    X = []
    for slice_df in tqdm(slices, desc=f"Подготовка данных"):
        slice_df['time'] = pd.to_datetime(slice_df['time'],
                                          format='%Y-%m-%d %H:%M:%S.%f')  # Преобразуем время в формат datetime
        slice_data = slice_df[
            ['groundSpeed_Kts', 'altitude_Ft', 'latitude', 'longitude', 'time']].copy()  # Выбираем необходимые поля
        slice_data['time_diff'] = slice_data['time'].diff().dt.total_seconds().fillna(
            0)  # Вычисляем разницу во времени между точками
        slice_data.drop(columns=['time'], inplace=True)  # Удаляем колонку 'time'
        X.append(slice_data.values)  # Преобразуем данные в массивы
    X_normalized = [scaler.transform(slice) for slice in X]  # Нормализуем данные
    return X_normalized


# Функция collate_fn использует pad_sequence для заполнения тензоров разного размера до одинакового размера.
def collate_fn(batch):
    """
    Функция для объединения тензоров разного размера в один батч.
    :param batch: Батч данных.
    :return: Объединенные тензоры данных и меток.
    """
    data, labels = zip(*batch)
    data = pad_sequence(data, batch_first=True)  # Заполняем тензоры до одинакового размера
    labels = torch.tensor(labels, dtype=torch.long)  # Преобразуем метки в тензор
    return data, labels


def classify_flights(new_df, model_folder, slice_length=20):
    """
    Классифицирует новые рейсы с использованием обученной модели.
    :param new_df: DataFrame с новыми данными.
    :param model_folder: Папка, содержащая файлы модели и нормализатора.
    :param slice_length: Длина разреза.
    :return: Списки некорректных и корректных рейсов, а также результаты классификации.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # Определяем устройство (CPU или GPU)
    with open(os.path.join(model_folder, "scaler.pkl"), "rb") as f:
        scaler = pickle.load(f)  # Загружаем нормализатор

    # Убедимся, что входные данные содержат только необходимые признаки
    required_columns = ['groundSpeed_Kts', 'altitude_Ft', 'latitude', 'longitude', 'time', 'callsign']
    missing_columns = [col for col in required_columns if col not in new_df.columns]
    if missing_columns:
        print(f"Отсутствуют следующие обязательные поля: {missing_columns}")
        return [], [], {}

    new_slices = create_slices(new_df, slice_length=slice_length)  # Создаем разрезы данных
    X_new = prepare_data_for_model(new_slices, scaler)  # Подготавливаем данные для модели

    # Проверяем размер входных данных
    if not X_new or X_new[0].shape[1] != 5:
        print("Размер входных данных не соответствует ожидаемому (ожидается 5 признаков).")
        return [], [], {}

    class NewFlightDataset(Dataset):
        def __init__(self, X):
            self.X = X

        def __len__(self):
            return len(self.X)

        def __getitem__(self, idx):
            return torch.tensor(self.X[idx], dtype=torch.float32), 0  # Возвращаем 0 как заглушку для метки

    new_dataset = NewFlightDataset(X_new)  # Создаем новый датасет
    new_loader = DataLoader(new_dataset, batch_size=8, shuffle=False,
                            collate_fn=collate_fn)  # Создаем DataLoader с функцией collate_fn
    flight_results = {}
    slice_index = 0

    # Определяем размер входных данных
    input_size = X_new[0].shape[1]
    hidden_size = 64
    num_layers = 2
    output_size = 2

    model = FlightTrackClassifier(input_size, hidden_size, num_layers, output_size)  # Инициализируем модель
    model.load_state_dict(
        torch.load(os.path.join(model_folder, "flight_track_classifier.pth")))  # Загружаем состояние модели
    model.to(device)  # Переносим модель на устройство (CPU или GPU)
    model.eval()  # Переводим модель в режим оценки

    with torch.no_grad():  # Отключаем вычисление градиентов
        for batch_X, _ in tqdm(new_loader, desc=f"Работа модели"):
            batch_X = batch_X.to(device)  # Переносим данные на устройство
            outputs = model(batch_X)  # Прямой проход модели
            _, predicted = torch.max(outputs, 1)  # Получаем предсказанные метки
            for i, pred in enumerate(predicted):
                slice_id = new_slices[slice_index]['id'].iloc[0]  # Получаем ID разреза
                slice_callsign = new_slices[slice_index]['callsign'].iloc[0]  # Получаем callsign разреза
                if slice_id not in flight_results:
                    flight_results[slice_id] = {'callsign': slice_callsign, 'correct': True,
                                                'slices': []}  # Инициализируем результаты для разреза
                flight_results[slice_id]['slices'].append(pred.item())  # Добавляем предсказанную метку
                if pred.item() == 1:
                    flight_results[slice_id]['correct'] = False  # Обновляем статус разреза, если он некорректный
                slice_index += 1  # Переходим к следующему разрезу

    incorrect_ids = [[flight_id, result['callsign']] for flight_id, result in flight_results.items() if
                     not result['correct']]  # Собираем некорректные рейсы
    correct_ids = [[flight_id, result['callsign']] for flight_id, result in flight_results.items() if
                   result['correct']]  # Собираем корректные рейсы
    return incorrect_ids, correct_ids, flight_results


class AiSorterInterface:
    def __init__(self, root):
        self.root = root
        self.font_txt = ('Fira Code SemiBold', 10)
        self.font_txt_light = ('Fira Code Light', 8)
        self.ai_trainer_frame = ttk.Frame(root)
        self.ai_trainer_frame.pack(fill="x")

        self.correct_ids = set()
        self.incorrect_ids = set()

        # Форма выбора файла для обработки
        self.working_file_label_ai_trainer = ttk.Label(self.ai_trainer_frame, text="Выберите файл для обработки:",
                                                       font=self.font_txt,
                                                       foreground='grey', justify="right", anchor="e")
        self.working_file_label_ai_trainer.grid(row=0, column=0, padx=10, pady=10)
        self.working_file_entry_ai_trainer = ttk.Entry(self.ai_trainer_frame, width=60)
        self.working_file_entry_ai_trainer.grid(row=0, column=1, padx=10, pady=10)
        self.working_file_button_ai_trainer = ttk.Button(self.ai_trainer_frame, text="Поиск",
                                                         command=self.select_working_file)
        self.working_file_button_ai_trainer.grid(row=0, column=2, padx=10, pady=10)
        self.working_open_folder_button_ai_trainer = ttk.Button(self.ai_trainer_frame, text="Открыть папку",
                                                                compound='left',
                                                                command=self.open_folder)
        self.working_open_folder_button_ai_trainer.grid(row=0, column=4, padx=10, pady=10)

        # Форма выбора файлов модели
        self.model_file_label_ai_sorting = ttk.Label(self.ai_trainer_frame, text="Выберите файлы модели:",
                                                     font=self.font_txt,
                                                     foreground='grey', justify="right", anchor="e")
        self.model_file_label_ai_sorting.grid(row=1, column=0, padx=10, pady=10)
        self.model_file_entry_ai_sorting = ttk.Entry(self.ai_trainer_frame, width=60)
        self.model_file_entry_ai_sorting.grid(row=1, column=1, padx=10, pady=10)
        self.model_file_button_ai_sorting = ttk.Button(self.ai_trainer_frame, text="Поиск",
                                                       command=self.select_model_folder)
        self.model_file_button_ai_sorting.grid(row=1, column=2, padx=10, pady=10)
        self.model_open_folder_button_ai_sorting = ttk.Button(self.ai_trainer_frame, text="Открыть папку",
                                                              compound='left',
                                                              command=lambda: Functions.open_folder("AI\Results"))
        self.model_open_folder_button_ai_sorting.grid(row=2, column=0, padx=20, pady=20, sticky="ew", ipadx=6, ipady=6)

        # Кнопка для запуска классификации
        self.start_ai_sorting_button = ttk.Button(self.ai_trainer_frame, text="Обработать", compound='left',
                                                  style='Accent.TButton',
                                                  command=self.start_classification)
        self.start_ai_sorting_button.grid(row=2, column=1, padx=20, pady=20, sticky="ew", ipadx=6, ipady=6)

        # Кнопка информации
        help_file = 'Content\help_texts.txt'
        help_texts = Functions.read_help_texts(help_file)
        self.help_aiSorter = help_texts['help_aiSorter']
        self.ai_Sorter_info_button = ttk.Button(self.ai_trainer_frame, text="⍰",
                                                command=lambda: Functions.show_info(self, self.help_aiSorter),
                                                style='Toolbutton')
        self.ai_Sorter_info_button.grid(row=2, column=2, padx=5, pady=5)

    def select_working_file(self):
        """
        Выбирает файл для обработки.
        """
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            self.working_file_entry_ai_trainer.delete(0, tk.END)
            self.working_file_entry_ai_trainer.insert(0, file_path)

    def select_model_folder(self):
        """
        Выбирает папку с моделью.
        """
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.model_file_entry_ai_sorting.delete(0, tk.END)
            self.model_file_entry_ai_sorting.insert(0, folder_path)

    def open_folder(self):
        """
        Открывает папку.
        """
        folder_path = filedialog.askdirectory()
        if folder_path:
            os.startfile(folder_path)

    def start_classification(self):
        """
        Начинает процесс классификации новых данных.
        """
        working_file_path = self.working_file_entry_ai_trainer.get()
        model_folder = self.model_file_entry_ai_sorting.get()

        if not working_file_path:
            print("Файл для обработки не выбран.")
            return

        if not model_folder:
            print("Папка с моделью не выбрана.")
            return

        new_data = load_data(working_file_path)  # Загружаем новые данные
        if new_data is None:
            print("Не удалось загрузить новые данные.")
            return

        new_df = pd.DataFrame(new_data)  # Преобразуем данные в DataFrame
        print(f"Загружено {len(new_df)} записей из {working_file_path}")
        # дебаг данных
        # print("Первые 5 строк данных:")
        # print(new_df.head())

        incorrect_ids, correct_ids, flight_results = classify_flights(new_df, model_folder)  # Классифицируем рейсы
        results = {
            "incorrect_ids": incorrect_ids,
            "correct_ids": correct_ids
        }

        # Получаем имя файла без расширения
        working_file_name = os.path.splitext(os.path.basename(working_file_path))[0]
        model_folder_name = os.path.basename(model_folder)

        # Создаем папку для сохранения результатов
        results_folder = os.path.join("Exports\AI\Results", f"{model_folder_name}_{working_file_name}")
        folder_existing_choose(results_folder)
        if not os.path.exists(results_folder):
            os.makedirs(results_folder)

        # Сохраняем результаты
        results_file_path = os.path.join(results_folder, f"ResultClassifier_{working_file_name}.json")
        with open(results_file_path, "w", encoding="utf-8") as results_file:
            json.dump(results, results_file, ensure_ascii=False, separators=(',', ': '), indent=4)
        print(f"Результаты сохранены в файл '{results_file_path}'")
        print(f"Корректных рейсов: {len(correct_ids)}")
        print(f"Некорректных рейсов: {len(incorrect_ids)}")

        PushNotify.notify_popup('Применение модели',
                                f'Сортировка файла ML-моделью завершена успешно, файлы помещены в {results_file_path} ')

        # автоматическая сортировка по шаблону
        try:
            self._auto_export_sorted_files(
                source_path=working_file_path,
                template_path=results_file_path,
                output_dir=results_folder
            )
        except Exception as e:
            error_msg = f'Ошибка постобработки: {str(e)}'
            print(error_msg)
            PushNotify.notify_popup('Ошибка постобработки', error_msg)

    def _auto_export_sorted_files(self, source_path, template_path, output_dir):
        """Автоматическая сортировка треков на основе шаблона классификации"""
        try:
            # Загрузка шаблона классификации
            with open(template_path, 'r', encoding='utf-8') as f:
                classification = json.load(f)

            # Преобразование списков ID в множества для быстрого поиска
            correct_ids = {tuple(item) for item in classification['correct_ids']}
            incorrect_ids = {tuple(item) for item in classification['incorrect_ids']}

            # Загрузка исходных данных
            with open(source_path, 'r', encoding='utf-8') as file:
                all_flights = json.load(file)

            correct_flights = []
            incorrect_flights = []

            # Группировка треков по ID и callsign
            flights_by_id = {}
            for flight in all_flights:
                flight_id = flight.get('id')
                callsign = flight.get('callsign')
                key = (flight_id, callsign)
                if key not in flights_by_id:
                    flights_by_id[key] = []
                flights_by_id[key].append(flight)

            # Прогресс-бар для визуализации процесса
            pbar_flights = tqdm(flights_by_id.items(), desc='Сортировка треков по шаблону')
            for key, flights in pbar_flights:
                if key in correct_ids:
                    correct_flights.extend(flights)
                elif key in incorrect_ids:
                    incorrect_flights.extend(flights)

            # Формирование путей для сохранения
            base_name = os.path.splitext(os.path.basename(source_path))[0]
            correct_output = os.path.join(output_dir, f"{base_name}_CORRECT.json")
            incorrect_output = os.path.join(output_dir, f"{base_name}_INCORRECT.json")

            # Сохранение результатов
            with open(correct_output, 'w', encoding='utf-8') as f:
                json.dump(correct_flights, f, ensure_ascii=False, indent=4)

            with open(incorrect_output, 'w', encoding='utf-8') as f:
                json.dump(incorrect_flights, f, ensure_ascii=False, indent=4)

            PushNotify.notify_popup('Автоматическая сортировка',
                                    f'Файлы успешно разделены и сохранены в:\n{output_dir}')

            return correct_output, incorrect_output

        except Exception as e:
            error_msg = f'Ошибка автоматической сортировки: {str(e)}'
            print(error_msg)
            PushNotify.notify_popup('Ошибка сортировки', error_msg)
            raise
