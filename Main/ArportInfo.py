import csv
import os


def get_airport_data(column_name, value, target_column):
    """
    Извлекает данные из CSV-файла по заданным критериям.

    iata_code;  icao_code;  name_rus;   name_eng;   city_rus;   city_eng;   gmt_offset; country_rus;    country_eng;
    iso_code;   latitude;   longitude;  runway_length;  runway_elevation;   phone;  fax;    email;  website

    :column_name: Название колонки, по которой производится поиск.
    :value: Значение в колонке, по которому производится поиск.
    :target_column: Название колонки, значение из которой нужно получить.

    Возвращает значение из целевой колонки или None, если строка не найдена.
    """

    csv_file_path = os.path.join('Content', 'airport_info.csv')

    # разные кодировки, если UTF-8 не работает
    encodings = ['utf-8', 'ISO-8859-1', 'latin-1']
    for encoding in encodings:
        try:
            with open(csv_file_path, 'r', newline='', encoding=encoding) as file:
                reader = csv.DictReader(file, delimiter=';')
                for row in reader:
                    if row[column_name] == value:
                        return row[target_column]
        except UnicodeDecodeError:
            continue
    return None
