import csv
import os


def get_aircraft_data(column_name, value, target_column):
    """
    Извлекает данные из CSV-файла по заданным критериям.

    :column_name: Название колонки, по которой производится поиск.
    IATA;  ICAO;  Manufacturer and Aircraft Type / Model;  WTC

    WTC - это весовая категория Wake Turbulence Categories. L = Light, M = Medium, H = Heavy, J = Super

    :value: Значение в колонке, по которому производится поиск.
    :target_column: Название колонки, значение из которой нужно получить.

    Возвращает значение из целевой колонки или None, если строка не найдена.
    """
    csv_file_path = os.path.join('Content', 'aircraft_info.csv')

    with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            if row[column_name] == value:
                return row[target_column]
    return None
