# import matplotlib.pyplot as plt
#
#    history = model.fit(X_train, y_train, epochs=10, batch_size=32, validation_split=0.2, verbose=1, callbacks=[early_stopping])
#
#    plt.plot(history.history['loss'], label='train loss')
#    plt.title('Loss during training')
#    plt.xlabel('Epoch')
#    plt.ylabel('Loss')
#    plt.legend()
#    plt.show()
#
#    plt.plot(history.history['accuracy'], label='train accuracy')
#    plt.title('accuracy during training')
#    plt.xlabel('Epoch')
#    plt.ylabel('accuracy')
#    plt.legend()
#    plt.show()

import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout
from tensorflow.keras.preprocessing.sequence import pad_sequences


def load_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    df = pd.DataFrame(data)
    return df


def preprocess_data(df):
    # Преобразование времени в числовой формат
    df['time'] = pd.to_datetime(df['time'])
    df['time'] = df['time'].map(lambda x: x.timestamp())

    # Удаление строк с некорректными данными
    df.dropna(inplace=True)

    # Выбор признаков
    features = ['time', 'latitude', 'longitude', 'altitude_Ft']
    X = df[features]
    y = df['id'].apply(lambda x: 1 if x in correct_ids else 0)  # 1 - корректный, 0 - некорректный

    # Стандартизация признаков
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y, scaler


# Загрузка данных
correct_df = load_data('CorrectData.json')
defected_df = load_data('DefectedData.json')

# Получение уникальных id для корректных и некорректных данных
correct_ids = set(correct_df['id'].unique())
defected_ids = set(defected_df['id'].unique())

# Объединение данных
all_df = pd.concat([correct_df, defected_df])

# Предварительная обработка данных
X, y, scaler = preprocess_data(all_df)

# Группировка данных по id
grouped = all_df.groupby('id')

# Создание временных рядов
sequences = []
labels = []

for group_id, group in grouped:
    sequence = group[['time', 'latitude', 'longitude', 'altitude_Ft']].values
    label = 1 if group_id in correct_ids else 0
    sequences.append(sequence)
    labels.append(label)

# Заполнение последовательностей до максимальной длины
max_length = max(len(seq) for seq in sequences)
X_sequences = pad_sequences(sequences, maxlen=max_length, dtype='float32', padding='post')

# Преобразование в numpy массивы
y_labels = np.array(labels)

# Разделение данных на тренировочную и тестовую выборки
X_train, X_test, y_train, y_test = train_test_split(X_sequences, y_labels, test_size=0.2, random_state=42)


# Создание модели LSTM
def create_lstm_model(input_shape):
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(32),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model


# Создание модели
model = create_lstm_model((X_train.shape[1], X_train.shape[2]))

# Обучение модели
model.fit(X_train, y_train, epochs=10, batch_size=32, validation_split=0.2)

# Сохранение модели
model.save('flight_track_lstm_model.h5')


def classify_new_data(file_path, model, scaler, max_length):
    new_df = load_data(file_path)
    new_df['time'] = pd.to_datetime(new_df['time'])
    new_df['time'] = new_df['time'].map(lambda x: x.timestamp())
    new_df.dropna(inplace=True)

    # Группировка данных по id
    grouped = new_df.groupby('id')

    # Создание временных рядов
    sequences = []
    ids = []

    for group_id, group in grouped:
        sequence = group[['time', 'latitude', 'longitude', 'altitude_Ft']].values
        ids.append(group_id)
        sequences.append(sequence)

    # Заполнение последовательностей до максимальной длины
    X_new_sequences = pad_sequences(sequences, maxlen=max_length, dtype='float32', padding='post')

    # Предсказание
    predictions = model.predict(X_new_sequences)
    predictions = (predictions > 0.5).astype(int).flatten()

    # Определение корректных и некорректных id
    correct_ids = [ids[i] for i in range(len(ids)) if predictions[i] == 1]
    defected_ids = [ids[i] for i in range(len(ids)) if predictions[i] == 0]

    return correct_ids, defected_ids


# Загрузка модели
model = tf.keras.models.load_model('flight_track_lstm_model.h5')

# Явная компиляция модели после загрузки
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Классификация новых данных
correct_ids, defected_ids = classify_new_data('new_data.json', model, scaler, max_length)
print("Корректные id:", correct_ids)
print("Некорректные id:", defected_ids)
