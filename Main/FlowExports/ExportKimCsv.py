import csv
import datetime
import json
import math
import os
from datetime import datetime

from tqdm import tqdm

import Main.MathVincenty
import Main.PushNotify
from Main.AircraftInfo import get_aircraft_data
from Main.ArportInfo import get_airport_data
from Main.Functions import folder_existing_choose


def convert_csv_kim(self, file_path, catalog_id, commentary, name, variant_id):
    """
    Начало преобразования потока в другой формат
    """
    with open(file_path, 'r') as file:
        json_data = json.load(file)
    filename = os.path.basename(file_path).split('.')[0]  # Используем только название файла без расширения

    export_dir = f'Exports/csvKIM/{filename}'
    folder_existing_choose(export_dir)
    print(f"Начато преобразование потока в CSV формат для КИМ")

    export_to_kim(self, json_data, filename, name, commentary, catalog_id, variant_id)

    print(f"Преобразование в CSV для КИМ успешно, помещено в {filename}")
    Main.PushNotify.notify_popup('Преобразование для КИМ',
                                 f'Конвертация потока {filename} в CSV для КИМ завершена успешно')


def export_to_kim(self, json_data, filename, name, commentary, catalog_id, variant_id):
    """
    Преобразование потока в другой формат - в csv таблицы для импорта в КИМ
    """
    export_dir = f'Exports/csvKIM/{filename}'

    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    flights = parse_json_data(json_data)

    # создаётся в новой директории
    create_flow_file(flights, os.path.join(export_dir, f'flow({filename}).flow'), name, commentary, catalog_id,
                     variant_id)
    create_trips_file(self, flights, os.path.join(export_dir, f'flow({filename})_trips.csv'))
    create_route_file(flights, os.path.join(export_dir, f'flow({filename})_route.csv'))


def parse_json_data(json_data):
    # Группировка данных по рейсам
    flights = {}
    for point in json_data:
        flight_id = point['id']
        if flight_id not in flights:
            flights[flight_id] = []
        flights[flight_id].append(point)
    return flights


def calculate_distance(points):
    # Расчет ортодромической дистанции между точками
    distance = 0
    for i in range(len(points) - 1):
        lat1, lon1 = points[i]['latitude'], points[i]['longitude']
        lat2, lon2 = points[i + 1]['latitude'], points[i + 1]['longitude']
        distance += Main.MathVincenty.vincenty((lat1, lon1), (lat2, lon2))
    return distance


def create_flow_file(flights, file_path, name, commentary, catalog_id, variant_id):
    """
    Создание файла .flow (описание потока)
    """
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';', quoting=csv.QUOTE_ALL, quotechar='"')
        writer.writerow([
            "TITLE", "COMMENT", "DATE", "TYPE", "CAT_ID", "PARENT_CAT_ID", "VARIANT_NUMBER", "UPDATE_DATE",
            "CSV_VERSION"
        ])
        earliest_time = min([min([point['time'] for point in flight]) for flight in flights.values()])
        # Преобразование времени в необходимый формат
        date_format = "%Y-%m-%d %H:%M:%S.%f"
        update_date_format = "%d.%m.%Y %H:%M:%S"
        parsed_date = datetime.strptime(earliest_time, date_format)
        formatted_date = parsed_date.strftime("%d.%m.%Y")
        update_date = datetime.now().strftime(update_date_format)

        writer.writerow([
            name,  # "TITLE"
            commentary,  # COMMENT
            formatted_date,  # DATE
            1,  # TYPE
            catalog_id,  # CAT_ID
            1,  # PARENT_CAT_ID
            variant_id,  # VARIANT_NUMBER
            update_date,  # UPDATE_DATE
            "1.2.9"  # CSV_VERSION
        ])


def create_trips_file(self, flights, file_path):
    """
    Создание файла trips.csv (таблица рейсов)
    """
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';', quoting=csv.QUOTE_ALL, quotechar='"')
        writer.writerow([
            "TRIP_IDENT", "ACFT_IDENT", "ACFT_TYPE", "DEP_AD_LAT", "DEP_AD_RUS", "DEP_ID", "DEST_AD_LAT", "DEST_AD_RUS",
            "DEST_ID",
            "DEP_TIME", "DEST_TIME", "RUSSIA_CODE", "WEIGHT_CAT", "FLY_TYPE", "REG_NUMBER", "STAND_ID_DEP",
            "STAND_ID_DEST", "PRIORITET",
            "DISTANCE", "AIRLHIST_ID", "SID_ID", "STAR_ID", "RUNWAY_DEP_ID", "RUNWAY_DEST_ID", "OBT", "IBT",
            "PREV_TRIP_IDENT", "NEXT_TRIP_IDENT"
        ])

        pbar = tqdm(flights.items())
        for flight_id, points in pbar:
            pbar.set_description("Создание файла trips.csv")
            distance = calculate_distance(points)
            first_point = points[-1]
            last_point = points[0]

            true_russia_code = f"{'R' if get_airport_data('iata_code', first_point['airportOrigin'], 'iso_code') == 'RU' else 'Z'}{'R' if get_airport_data('iata_code', first_point['airportDestination'], 'iso_code') == 'RU' else 'Z'}"

            russia_code = ('RR' if self.russia_code_var.get() else f'{true_russia_code}')
            date_format = "%Y-%m-%d %H:%M:%S.%f"

            #  DEST_TIME или есть, или берётся из последней точки маршрута
            dest_time = None if first_point['destination_time'] == 'NULL' else datetime.strptime(first_point['destination_time'], date_format).strftime("%d.%m.%Y %H:%M:%S")
            if dest_time is None:
                dest_time = datetime.strptime(last_point['time'], date_format).strftime("%d.%m.%Y %H:%M:%S")

            writer.writerow([
                replace_letters_with_numbers(flight_id),  # "TRIP_IDENT"
                first_point['callsign'],  # "ACFT_IDENT"
                first_point['aircraftCode'],  # "ACFT_TYPE"
                get_airport_data('iata_code', first_point['airportOrigin'], 'icao_code'),  # "DEP_AD_LAT";
                get_airport_data('iata_code', first_point['airportOrigin'], 'icao_code'),  # "DEP_AD_RUS"
                None,  # "DEP_ID"
                get_airport_data('iata_code', first_point['airportDestination'], 'icao_code'),  # "DEST_AD_LAT"
                get_airport_data('iata_code', first_point['airportDestination'], 'icao_code'),  # "DEST_AD_RUS"
                None,  # "DEST_ID"
                None if first_point['origin_time'] == 'NULL' else datetime.strptime(first_point['origin_time'],
                                                                                    date_format).strftime(
                    "%d.%m.%Y %H:%M:%S"),  # "DEP_TIME"
                dest_time,  # "DEST_TIME"
                russia_code,  # "RUSSIA_CODE"
                'H' if get_aircraft_data('ICAO', first_point['aircraftCode'], 'WTC') is None else get_aircraft_data(
                    'ICAO', first_point['aircraftCode'], 'WTC'),  # "WEIGHT_CAT"
                None,  # "FLY_TYPE
                first_point['flightNumber'],  # "REG_NUMBER"
                -1,  # STAND_ID_DEP
                -1,  # STAND_ID_DEST
                1,  # "PRIORITET"
                distance,  # "DISTANCE"
                None,  # "AIRLHIST_ID"
                None,  # "SID_ID"
                None,  # "STAR_ID"
                None,  # "RUNWAY_DEP_ID"
                None,  # ;"RUNWAY_DEST_ID"
                None,  # "OBT";
                None,  # "IBT"
                None,  # "PREV_TRIP_IDENT";
                None  # "NEXT_TRIP_IDENT"
            ])


def create_route_file(flights, file_path):
    """
    Создание файла route.csv (таблица маршрутов)
    """
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';', quoting=csv.QUOTE_ALL, quotechar='"')
        writer.writerow([
            "TRIP_IDENT", "POINTS_ID", "SEGMENTS_ID", "FIRS_ID", "SECTOR_ID", "LATITUDE", "LONGITUDE", "FIRS_CODE",
            "ISCLIMB", "AIRWAYS_ID",
            "SEG_STAT", "DIST", "POINT_NUMBER", "MOMENT", "MOMENT2", "SPEED", "LAT_C", "LONG_C", "VERT_SPEED", "KSI",
            "PHI", "RTURN",
            "VERT_PROFILE", "EASTWESTDIRECT", "ISSTRAIGHT", "VERTICAL_POINT", "SECTOR_CODE", "ATC", "NAVIGATION_POINT",
            "ISHOLDINGZONE",
            "PROCEDURE_TYPE", "MERGE_POINT", "SS_POINT_ID", "ALTITUDE", "POINT", "END_POINT", "AC_WEIGHT", "VER_ID",
            "VER_X", "VER_Y",
            "ACCELERATION", "THRUST", "INOUT", "AC_CONFIGURATION", "AC_SPOILERS", "FRA_POINTS_ID"
        ])

        pbar = tqdm(flights.items())
        for flight_id, points in pbar:
            pbar.set_description("Создание файла route.csv")
            distances = []
            for i in range(len(points) - 1, 0, -1):  # Вычисляем дистанции в обратном порядке
                point1 = (points[i]["latitude"], points[i]["longitude"])
                point2 = (points[i - 1]["latitude"], points[i - 1]["longitude"])
                distance = Main.MathVincenty.vincenty(point1, point2)
                distances.append(distance)

            total_distance = 0
            for i, point in enumerate(reversed(points)):
                if i == 0:
                    total_distance = 0
                else:
                    total_distance += distances[i - 1]

                update_date_format = "%Y-%m-%d %H:%M:%S.%f"
                moment2 = (None if points[i + 1]['time'] == 'NULL' else datetime.strptime(points[i + 1]['time'],
                                                                                          update_date_format).strftime(
                    "%d.%m.%Y %H:%M:%S")) if i < len(points) - 1 else None
                head_direction_rad = (math.radians(point.get('head_direction', 0)) if point.get('head_direction',
                                                                                                0) is not None and point.get(
                    'head_direction', 0) != 0 else 0)

                writer.writerow([
                    replace_letters_with_numbers(flight_id),  # TRIP_IDENT
                    -1,  # POINTS_ID
                    -1,  # SEGMENTS_ID
                    -1,  # FIRS_ID
                    -1,  # SECTOR_ID
                    point['latitude'],  # LATITUDE
                    point['longitude'],  # LONGITUDE
                    None,  # FIRS_CODE
                    None,  # ISCLIMB
                    0,  # AIRWAYS_ID
                    -1,  # SEG_STAT
                    total_distance,  # DIST
                    i + 1,  # POINT_NUMBER
                    None if point['time'] == 'NULL' else datetime.strptime(point['time'], update_date_format).strftime(
                        "%d.%m.%Y %H:%M:%S"),  # MOMENT
                    moment2,  # MOMENT2
                    point['groundSpeed_Kts'],  # SPEED
                    0,  # LAT_C
                    0,  # LONG_C
                    point['verticalSpeed'],  # VERT_SPEED
                    head_direction_rad,  # KSI  было 0
                    0,  # PHI
                    0,  # RTURN
                    0,  # VERT_PROFILE
                    None,  # EASTWESTDIRECT
                    1,  # ISSTRAIGHT
                    0,  # VERTICAL_POINT
                    0,  # SECTOR_CODE
                    0,  # ATC
                    -1,  # NAVIGATION_POINT
                    None,  # ISHOLDINGZONE
                    None,  # PROCEDURE_TYPE
                    -1,  # MERGE_POINT
                    -1,  # SS_POINT_ID
                    point['altitude_Ft'] * 0.3048,  # футы в метры #ALTITUDE
                    None,  # POINT было 0
                    -1,  # END_POINT
                    -1,  # AC_WEIGHT
                    -1,  # VER_ID
                    -1,  # VER_X
                    -1,  # VER_Y
                    0,  # ACCELERATION
                    -1,  # THRUST
                    -1,  # INOUT
                    -1,  # AC_CONFIGURATION
                    -1,  # AC_SPOILERS
                    -1,  # FRA_POINTS_ID
                ])


def replace_letters_with_numbers(input_string):
    """
    Создаем словарь для замены букв на цифры (в киме id рейса должен быть только из цифр)
    """
    letter_to_number = {
        'a': '1', 'b': '2', 'c': '3', 'd': '4', 'e': '5', 'f': '6',
        'g': '7', 'h': '8', 'i': '9', 'j': '0', 'k': '1', 'l': '2',
        'm': '3', 'n': '4', 'o': '5', 'p': '6', 'q': '7', 'r': '8',
        's': '9', 't': '0', 'u': '1', 'v': '2', 'w': '3', 'x': '4',
        'y': '5', 'z': '6'
    }
    # Заменяем буквы на цифры
    result = ''.join(letter_to_number.get(char, char) for char in input_string)
    return result


