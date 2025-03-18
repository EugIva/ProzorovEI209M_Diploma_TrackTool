# AiTrainer.py
import datetime
import json
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset
import torch.nn as nn
import torch.optim as optim
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from tqdm import tqdm
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from torch.nn.utils.rnn import pad_sequence
from Main import Functions
from Main.Functions import folder_existing_choose
import logging

# Настройка логгирования
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()


class FlightDataset(Dataset):
    def __init__(self, X, y):
        self.X = X
        self.y = y

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return torch.tensor(self.X[idx], dtype=torch.float32), torch.tensor(self.y[idx], dtype=torch.long)


class FlightTrackClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super(FlightTrackClassifier, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        out = self.fc(lstm_out[:, -1, :])  # Берем последний временной шаг
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
            logger.error(f"Ошибка при декодировании JSON: {e}")
            return None
    if not isinstance(data, list):
        logger.error("Данные не представлены в виде списка.")
        return None
    df = pd.DataFrame(data)
    if 'id' not in df.columns:
        logger.warning("Колонка 'id' отсутствует в DataFrame. Добавляю искусственный 'id'.")
        df['id'] = df.index  # Просто используем индекс как 'id'
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])  # Преобразуем поле 'time' в формат datetime
    else:
        logger.warning("Колонка 'time' отсутствует в DataFrame.")
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
    for _, group in tqdm(grouped, desc=f"Создание разрезов", disable=False):
        num_points = len(group)
        if num_points < slice_length:
            slices.append(group.copy())  # Если трек короче slice_length, добавляем его целиком как разрез
        else:
            for i in range(num_points - slice_length + 1):
                slice_df = group.iloc[i:i + slice_length]  # Создаем разрез длиной slice_length
                slices.append(slice_df)
    print(f"Количество разрезов: {len(slices)}")
    return slices


def prepare_dataset(correct_slices, defected_slices):
    """
    Создает датасет для обучения.
    :param correct_slices: Список корректных разрезов.
    :param defected_slices: Список некорректных разрезов.
    :return: X_train, X_test, y_train, y_test, scaler.
    """
    correct_labels = [0] * len(correct_slices)
    defected_labels = [1] * len(defected_slices)
    all_slices = correct_slices + defected_slices
    all_labels = correct_labels + defected_labels

    # Выбираем только необходимые поля
    X = [slice_df[['groundSpeed_Kts', 'altitude_Ft', 'latitude', 'longitude', 'time']].copy() for slice_df in
         tqdm(all_slices, desc=f"Копирование разрезов", disable=False)]

    # Преобразуем время в разницу во времени между последовательными точками
    for slice_df in tqdm(X, desc=f"Подготовка данных", disable=False):
        slice_df['time_diff'] = slice_df['time'].diff().dt.total_seconds().fillna(0)
        slice_df.drop(columns=['time'], inplace=True)

    # Преобразуем данные в массивы
    X = [slice_df.values for slice_df in X]

    # Нормализация данных
    scaler = MinMaxScaler()
    X_normalized = [scaler.fit_transform(slice) for slice in X]

    # Преобразуем данные в тензоры
    X = [x.reshape((x.shape[0], x.shape[1])) for x in X_normalized]
    y = all_labels

    # Разделяем данные на обучающую и тестовую выборки
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test, scaler


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


def train_model(X_train, X_test, y_train, y_test, scaler, model_folder, num_epochs, batch_size, hidden_size,
                num_layers):
    """
    Обучает модель на основе подготовленных данных.
    :param X_train: Обучающие данные.
    :param X_test: Тестовые данные.
    :param y_train: Метки для обучающих данных.
    :param y_test: Метки для тестовых данных.
    :param scaler: Нормализатор данных.
    :param model_folder: Папка для сохранения модели и нормализатора.
    :param num_epochs: Количество эпох обучения.
    :param batch_size: Размер батча.
    :param hidden_size: Размер скрытого слоя LSTM.
    :param num_layers: Количество слоев LSTM.
    :return: Списки потерь и точности на обучающей и тестовой выборках.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # Определяем устройство (CPU или GPU)
    input_size = X_train[0].shape[1]  # Размер входного вектора
    output_size = 2  # Количество классов (например, 0 и 1)

    train_dataset = FlightDataset(X_train, y_train)  # Создаем датасет для обучения
    test_dataset = FlightDataset(X_test, y_test)  # Создаем датасет для тестирования

    # Создаем DataLoader для обучения и тестирования с функцией collate_fn
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

    # Инициализация модели, функции потерь и оптимизатора
    model = FlightTrackClassifier(input_size, hidden_size, num_layers, output_size).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    train_losses = []
    val_losses = []
    train_accuracies = []
    val_accuracies = []

    # Цикл обучения
    for epoch in range(num_epochs):
        model.train()  # Переводим модель в режим обучения
        running_loss = 0.0
        correct = 0
        total = 0

        logger.info(f"Эпоха {epoch + 1}, train_loader: {len(train_loader)} итераций")
        for batch_X, batch_y in tqdm(train_loader, desc=f"Эпоха {epoch + 1}, train_loader ", disable=False):
            batch_X = batch_X.to(device)  # Переносим данные на устройство
            batch_y = batch_y.to(device)  # Переносим метки на устройство

            optimizer.zero_grad()  # Обнуляем градиенты
            outputs = model(batch_X)  # Прямой проход модели
            loss = criterion(outputs, batch_y)  # Вычисляем потери
            loss.backward()  # Обратный проход
            optimizer.step()  # Обновляем параметры модели

            running_loss += loss.item()  # Суммируем потери
            _, predicted = torch.max(outputs, 1)  # Получаем предсказанные метки
            total += batch_y.size(0)  # Суммируем общее количество примеров
            correct += (predicted == batch_y).sum().item()  # Считаем количество правильно предсказанных примеров

        # Вычисляем среднюю потерю и точность за эпоху
        train_loss = running_loss / len(train_loader)
        train_accuracy = correct / total
        train_losses.append(train_loss)
        train_accuracies.append(train_accuracy)
        logger.info(f"Epoch [{epoch + 1}/{num_epochs}], Loss: {train_loss:.4f}, Accuracy: {train_accuracy:.4f}")

        # Оценка на валидационной выборке
        model.eval()  # Переводим модель в режим оценки
        val_running_loss = 0.0
        val_correct = 0
        val_total = 0

        logger.info(f"Эпоха {epoch + 1}, test_loader: {len(test_loader)} итераций")
        with torch.no_grad():  # Отключаем вычисление градиентов
            for batch_X, batch_y in tqdm(test_loader, desc=f"Эпоха {epoch + 1}, test_loader ", disable=False):
                batch_X = batch_X.to(device)  # Переносим данные на устройство
                batch_y = batch_y.to(device)  # Переносим метки на устройство

                outputs = model(batch_X)  # Прямой проход модели
                loss = criterion(outputs, batch_y)  # Вычисляем потери
                val_running_loss += loss.item()  # Суммируем потери
                _, predicted = torch.max(outputs, 1)  # Получаем предсказанные метки
                val_total += batch_y.size(0)  # Суммируем общее количество примеров
                val_correct += (
                            predicted == batch_y).sum().item()  # Считаем количество правильно предсказанных примеров

        # Вычисляем среднюю потерю и точность за эпоху
        val_loss = val_running_loss / len(test_loader)
        val_accuracy = val_correct / val_total
        val_losses.append(val_loss)
        val_accuracies.append(val_accuracy)
        logger.info(f"Validation Loss: {val_loss:.4f}, Validation Accuracy: {val_accuracy:.4f}")

    # Сохранение модели
    torch.save(model.state_dict(), os.path.join(model_folder, "flight_track_classifier.pth"))
    logger.info("Модель успешно сохранена в файл 'flight_track_classifier.pth'")

    # Сохранение нормализатора
    with open(os.path.join(model_folder, "scaler.pkl"), "wb") as f:
        pickle.dump(scaler, f)
    logger.info("Нормализатор сохранен в файл 'scaler.pkl'")

    # Оценка модели на тестовых данных
    model.eval()  # Переводим модель в режим оценки
    correct = 0
    total = 0
    with torch.no_grad():  # Отключаем вычисление градиентов
        for batch_X, batch_y in test_loader:
            batch_X = batch_X.to(device)  # Переносим данные на устройство
            outputs = model(batch_X)  # Прямой проход модели
            _, predicted = torch.max(outputs, 1)  # Получаем предсказанные метки
            total += batch_y.size(0)  # Суммируем общее количество примеров
            correct += (predicted == batch_y).sum().item()  # Считаем количество правильно предсказанных примеров

    accuracy = correct / total  # Вычисляем точность модели
    logger.info(f"Точность модели: {accuracy:.4f}")

    return train_losses, val_losses, train_accuracies, val_accuracies, accuracy  # Возвращаем данные для графиков и точность


class AiTrainerInterface:
    def __init__(self, root):
        self.root = root
        self.font_txt = ('Fira Code SemiBold', 10)
        self.font_txt_light = ('Fira Code Light', 8)
        self.ai_sorting_frame = ttk.Frame(root)
        self.ai_sorting_frame.pack(fill="both", expand=True)

        # Форма выбора файла корректных данных
        self.correct_file_label_ai_sorting = ttk.Label(self.ai_sorting_frame, text="Выберите файл корректных данных:",
                                                       font=self.font_txt,
                                                       foreground='grey', justify="right", anchor="e")
        self.correct_file_label_ai_sorting.grid(row=0, column=0, padx=10, pady=10)
        self.correct_file_entry_ai_sorting = ttk.Entry(self.ai_sorting_frame, width=60)
        self.correct_file_entry_ai_sorting.grid(row=0, column=1, padx=10, pady=10)
        self.correct_file_button_ai_sorting = ttk.Button(self.ai_sorting_frame, text="Поиск",
                                                         command=self.select_correct_file)
        self.correct_file_button_ai_sorting.grid(row=0, column=2, padx=10, pady=10)
        self.correct_open_folder_button_ai_sorting = ttk.Button(self.ai_sorting_frame, text="Открыть папку",
                                                                compound='left',
                                                                command=lambda: Functions.open_folder("AI\Models"))
        self.correct_open_folder_button_ai_sorting.grid(row=0, column=4, padx=10, pady=10)

        # Форма выбора файла некорректных данных
        self.incorrect_file_label_ai_sorting = ttk.Label(self.ai_sorting_frame,
                                                         text="Выберите файл некорректных данных:", font=self.font_txt,
                                                         foreground='grey', justify="right", anchor="e")
        self.incorrect_file_label_ai_sorting.grid(row=1, column=0, padx=10, pady=10)
        self.incorrect_file_entry_ai_sorting = ttk.Entry(self.ai_sorting_frame, width=60)
        self.incorrect_file_entry_ai_sorting.grid(row=1, column=1, padx=10, pady=10)
        self.incorrect_file_button_ai_sorting = ttk.Button(self.ai_sorting_frame, text="Поиск",
                                                           command=self.select_incorrect_file)
        self.incorrect_file_button_ai_sorting.grid(row=1, column=2, padx=10, pady=10)
        self.incorrect_open_folder_button_ai_sorting = ttk.Button(self.ai_sorting_frame, text="Открыть папку",
                                                                  compound='left',
                                                                  command=lambda: Functions.open_folder("AI\Models"))
        self.incorrect_open_folder_button_ai_sorting.grid(row=1, column=4, padx=10, pady=10)

        # Форма ввода названия модели
        self.model_folder_name_var = tk.StringVar()

        self.model_folder_name_var.set(f"AnomalyFinder_{datetime.date.today()}")
        self.model_folder_label_ai_sorting = ttk.Label(self.ai_sorting_frame, text="Введите название модели:",
                                                       font=self.font_txt,
                                                       foreground='grey', justify="right", anchor="e")
        self.model_folder_label_ai_sorting.grid(row=2, column=0, padx=10, pady=10)
        self.model_folder_entry_ai_sorting = ttk.Entry(self.ai_sorting_frame, width=60,
                                                       textvariable=self.model_folder_name_var)
        self.model_folder_entry_ai_sorting.grid(row=2, column=1, padx=0, pady=0)

        # Параметры модели
        self.num_epochs_var = tk.IntVar(value=100)  # Устанавливаем количество эпох в 100
        self.num_epochs_label = ttk.Label(self.ai_sorting_frame, text="Количество эпох:", font=self.font_txt,
                                          foreground='grey', justify="right", anchor="e")
        self.num_epochs_label.grid(row=3, column=0, padx=10, pady=10)
        self.num_epochs_entry = ttk.Entry(self.ai_sorting_frame, width=60, textvariable=self.num_epochs_var)
        self.num_epochs_entry.grid(row=3, column=1, padx=10, pady=10)

        self.batch_size_var = tk.IntVar(value=32)
        self.batch_size_label = ttk.Label(self.ai_sorting_frame, text="Размер батча:", font=self.font_txt,
                                          foreground='grey', justify="right", anchor="e")
        self.batch_size_label.grid(row=4, column=0, padx=10, pady=10)
        self.batch_size_entry = ttk.Entry(self.ai_sorting_frame, width=60, textvariable=self.batch_size_var)
        self.batch_size_entry.grid(row=4, column=1, padx=10, pady=10)

        self.hidden_size_var = tk.IntVar(value=64)
        self.hidden_size_label = ttk.Label(self.ai_sorting_frame, text="Размер скрытого слоя LSTM:", font=self.font_txt,
                                           foreground='grey', justify="right", anchor="e")
        self.hidden_size_label.grid(row=5, column=0, padx=10, pady=10)
        self.hidden_size_entry = ttk.Entry(self.ai_sorting_frame, width=60, textvariable=self.hidden_size_var)
        self.hidden_size_entry.grid(row=5, column=1, padx=10, pady=10)

        self.num_layers_var = tk.IntVar(value=2)
        self.num_layers_label = ttk.Label(self.ai_sorting_frame, text="Количество слоев LSTM:", font=self.font_txt,
                                          foreground='grey', justify="right", anchor="e")
        self.num_layers_label.grid(row=6, column=0, padx=10, pady=10)
        self.num_layers_entry = ttk.Entry(self.ai_sorting_frame, width=60, textvariable=self.num_layers_var)
        self.num_layers_entry.grid(row=6, column=1, padx=10, pady=10)

        self.open_folder_button_ai_sorting = ttk.Button(self.ai_sorting_frame, text="Открыть папку", compound='left',
                                                        command=lambda: Functions.open_folder("AI\Models"))
        self.open_folder_button_ai_sorting.grid(row=7, column=0, padx=20, pady=20, sticky="ew", ipadx=6, ipady=6)

        self.start_ai_sorting_button = ttk.Button(self.ai_sorting_frame, text="Начать обучение", compound='left',
                                                  style='Accent.TButton',
                                                  command=self.start_training)
        self.start_ai_sorting_button.grid(row=7, column=1, padx=20, pady=20, sticky="ew", ipadx=6, ipady=6)

        help_file = 'Content\help_texts.txt'
        help_texts = Functions.read_help_texts(help_file)
        self.help_aiTrainer = help_texts['help_aiTrainer']
        self.ai_trainer_info_button = ttk.Button(self.ai_sorting_frame, text="⍰",
                                                 command=lambda: Functions.show_info(self, self.help_aiTrainer),
                                                 style='Toolbutton')
        self.ai_trainer_info_button.grid(row=7, column=2, padx=5, pady=5)

        # Метка для вывода точности модели
        self.accuracy_label = ttk.Label(self.ai_sorting_frame, text="", font=self.font_txt)
        self.accuracy_label.grid(row=8, column=0, columnspan=5, padx=10, pady=10)

        # Фрейм для графиков
        self.plots_frame = ttk.Frame(self.ai_sorting_frame)
        self.plots_frame.grid(row=9, column=0, columnspan=5, padx=10, pady=10)
        self.plots_frame.grid_remove()  # Скрываем фрейм с графиками до начала обучения

    def select_correct_file(self):
        """
        Выбирает файл корректных данных.
        """
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            self.correct_file_entry_ai_sorting.delete(0, tk.END)
            self.correct_file_entry_ai_sorting.insert(0, file_path)

    def select_incorrect_file(self):
        """
        Выбирает файл некорректных данных.
        """
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            self.incorrect_file_entry_ai_sorting.delete(0, tk.END)
            self.incorrect_file_entry_ai_sorting.insert(0, file_path)

    def open_folder(self):
        """
        Открывает папку.
        """
        folder_path = filedialog.askdirectory()
        if folder_path:
            os.startfile(folder_path)

    def start_training(self):
        """
        Начинает процесс обучения модели.
        """
        correct_file_path = self.correct_file_entry_ai_sorting.get()
        incorrect_file_path = self.incorrect_file_entry_ai_sorting.get()
        model_folder = self.model_folder_entry_ai_sorting.get()
        output_dir = os.path.join("Exports", "AI", "Models", model_folder)
        folder_existing_choose(output_dir)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        correct_data = load_data(correct_file_path)
        incorrect_data = load_data(incorrect_file_path)

        if correct_data is not None and incorrect_data is not None:
            correct_slices = create_slices(correct_data)
            incorrect_slices = create_slices(incorrect_data)
            X_train, X_test, y_train, y_test, scaler = prepare_dataset(correct_slices, incorrect_slices)
            num_epochs = self.num_epochs_var.get()
            batch_size = self.batch_size_var.get()
            hidden_size = self.hidden_size_var.get()
            num_layers = self.num_layers_var.get()
            train_losses, val_losses, train_accuracies, val_accuracies, accuracy = train_model(X_train, X_test, y_train,
                                                                                               y_test, scaler,
                                                                                               output_dir, num_epochs,
                                                                                               batch_size, hidden_size,
                                                                                               num_layers)
            self.display_plots(train_losses, val_losses, train_accuracies, val_accuracies, accuracy)

    def display_plots(self, train_losses, val_losses, train_accuracies, val_accuracies, accuracy):
        """
        Отображает графики потерь и точности на экране.
        :param train_losses: Список потерь на обучающей выборке.
        :param val_losses: Список потерь на валидационной выборке.
        :param train_accuracies: Список точностей на обучающей выборке.
        :param val_accuracies: Список точностей на валидационной выборке.
        :param accuracy: Точность модели на тестовых данных.
        """
        # Показываем фрейм с графиками
        self.plots_frame.grid()

        # Устанавливаем текст метки с точностью модели
        self.accuracy_label.config(text=f"Точность модели: {accuracy:.4f}")

        # Создаем фигуры для графиков
        self.figure_loss = Figure(figsize=(5, 4), dpi=100)
        self.ax_loss = self.figure_loss.add_subplot(111)
        self.ax_loss.plot(train_losses, label='Train Loss')
        self.ax_loss.plot(val_losses, label='Validation Loss')
        self.ax_loss.set_title('Loss during training')
        self.ax_loss.set_xlabel('Epoch')
        self.ax_loss.set_ylabel('Loss')
        self.ax_loss.legend()

        self.figure_acc = Figure(figsize=(5, 4), dpi=100)
        self.ax_acc = self.figure_acc.add_subplot(111)
        self.ax_acc.plot(train_accuracies, label='Train Accuracy')
        self.ax_acc.plot(val_accuracies, label='Validation Accuracy')
        self.ax_acc.set_title('Accuracy during training')
        self.ax_acc.set_xlabel('Epoch')
        self.ax_acc.set_ylabel('Accuracy')
        self.ax_acc.legend()

        # Создаем холсты для графиков
        self.canvas_loss = FigureCanvasTkAgg(self.figure_loss, master=self.plots_frame)
        self.canvas_loss.draw()
        self.canvas_loss.get_tk_widget().grid(row=0, column=0, padx=5, pady=10)

        self.canvas_acc = FigureCanvasTkAgg(self.figure_acc, master=self.plots_frame)
        self.canvas_acc.draw()
        self.canvas_acc.get_tk_widget().grid(row=0, column=1, padx=5, pady=10)
