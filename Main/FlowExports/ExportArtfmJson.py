import datetime
import json
import os
import pathlib
from datetime import datetime
from tkinter import messagebox

from tqdm import tqdm

import Main.MathVincenty
import Main.PushNotify
from Main.AircraftInfo import get_aircraft_data
from Main.ArportInfo import get_airport_data
from Main.Functions import file_existing_choose


def convert_json_atfm(self, json_file, catalog_id, commentary, name, user_id, number):
    """
    Преобразование потока в другой формат - в json поток для импорта в ATFM
    """
    try:
        with open(json_file, 'r') as f:
            json_data = json.load(f)

        output_file = os.path.join(os.path.basename(json_file).replace('.json', '_atfm.json'))
        output_dir = pathlib.Path('Exports/jsonATFM')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / output_file

        file_existing_choose(output_file)

        atfm_data = {
            "CatalogId": int(catalog_id),
            "Commentary": commentary,
            "Name": name,
            "Date": convert_string_to_iso(min(trip["time"] for trip in json_data)),
            "UserId": int(user_id),
            "StochId": None,
            "Updatedate": datetime.now().isoformat(),
            "IsDelete": False,
            "IsOperative": False,
            "ParentId": None,
            "Number": int(number),
            "Trips": []
        }

        trip_dict = {}
        pbar = tqdm(json_data)
        for trip in pbar:

            true_russia_code = f"{'R' if get_airport_data('iata_code', trip['airportOrigin'], 'iso_code') == 'RU' else 'Z'}{'R' if get_airport_data('iata_code', trip['airportDestination'], 'iso_code') == 'RU' else 'Z'}"
            russia_code = ('RR' if self.russia_code_var_atfm.get() else f'{true_russia_code}')

            pbar.set_description("Выполнение преобразования JSON в ATFM формат")
            trip_id = trip["id"]
            if trip_id not in trip_dict:
                trip_dict[trip_id] = {
                    "TripId": convert_string_to_int(trip_id),
                    "CatalogId": int(catalog_id),
                    "AircraftCode": trip["callsign"],
                    "WeightCat": 'H' if get_aircraft_data('ICAO', trip['aircraftCode'],
                                                          'WTC') is None else get_aircraft_data('ICAO',
                                                                                                trip['aircraftCode'],
                                                                                                'WTC'),
                    "AircraftType": trip["aircraftCode"],
                    "DepartureCode": get_airport_data('iata_code', trip["airportOrigin"], 'icao_code'),
                    "DepartureId": None,
                    "DepartureTime": convert_string_to_iso2(trip.get("origin_time")) if trip.get(
                        "origin_time") else None,
                    "ArrivalCode": get_airport_data('iata_code', trip["airportDestination"], 'icao_code'),
                    "ArrivalId": None,
                    "ArrivalTime": convert_string_to_iso2(trip.get("destination_time")) if trip.get(
                        "destination_time") else None,
                    "RussiaCode": russia_code,
                    "FlightType": None,
                    "RegNumber": trip["flightNumber"],
                    "Prioritet": None,
                    "Route": []
                }
                atfm_data["Trips"].append(trip_dict[trip_id])

            latitude = trip["latitude"]
            longitude = trip["longitude"]
            altitude = float(trip["altitude_Ft"]) * 0.3048
            moment = trip["time"]
            speed = float(trip["groundSpeed_Kts"]) * 1.852
            is_climb = 0 if float(trip["verticalSpeed"]) == 0 else 1 if float(trip["verticalSpeed"]) > 0 else 2

            route = {
                "TripId": convert_string_to_int(trip_id),
                "CatalogId": int(catalog_id),
                "PointNumber": len(trip_dict[trip_id]["Route"]) + 1,
                "Latitude": float(latitude),
                "Longitude": float(longitude),
                "Altitude": float(altitude),
                "Moment": convert_string_to_iso(moment),
                "PointCode": " ",
                "VerticalProfile": int(is_climb),
                "HorizontalProfile": None,
                "FlightPhase": int(is_climb),
                "PointId": None,
                "SectorId": None,
                "FirCode": None,
                "SectorCode": None,
                "Distance": None,
                "Speed": speed,
                "TurnLatitude": None,
                "TurnLongitude": None,
                "TurnRadius": None
            }

            trip_dict[trip_id]["Route"].insert(0, route)

        # заполнение графы "расстояние от аэропорта вылета"
        for trip in atfm_data["Trips"]:
            routes = trip["Route"]
            distances = []
            for i in range(len(routes) - 1):
                point1 = (routes[i]["Latitude"], routes[i]["Longitude"])
                point2 = (routes[i + 1]["Latitude"], routes[i + 1]["Longitude"])
                distance = Main.MathVincenty.vincenty(point1, point2)
                distances.append(distance)
            for i, route in enumerate(routes):
                if i == 0:
                    route["Distance"] = 0
                else:
                    route["Distance"] = sum(distances[:i])

        print('Преобразование выполнено. Дождитесь сохранения JSON файла')
        with open(output_file, 'w') as f:
            json.dump([atfm_data], f, indent=4)

        print(f"Преобразование в JSON для ATFM успешно, помещено в {output_file}")

        dir_path, file_name = os.path.split(json_file)
        file_name_short = os.path.splitext(file_name)[0]
        Main.PushNotify.notify_popup('Преобразование для ATFM',
                                     f'Конвертация потока {file_name_short} для ATFM модели завершена успешно')

    except Exception as e:
        print(f"{e}")
        messagebox.showerror("Ошибка", "Файл не корректный. Проверьте формат или содержимое файла.")


def convert_string_to_int(s):
    return int(''.join(filter(str.isdigit, s)))


def convert_time_to_iso(time):
    return time.isoformat()


def convert_string_to_iso(date_string):
    """
    Конвертация времени в другой формат
    """
    date_object = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S.%f")
    iso_string = date_object.strftime("%Y-%m-%dT%H:%M:%S")
    return iso_string


def convert_string_to_iso2(date_string):
    """
    Конвертация с проверкой на наличие такого поля в данных
    """
    if date_string is None or date_string == 'NULL':
        return None
    else:
        try:
            date_object = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S.%f")
            iso_string = date_object.strftime("%Y-%m-%dT%H:%M:%S")
            return iso_string
        except ValueError:
            return None
