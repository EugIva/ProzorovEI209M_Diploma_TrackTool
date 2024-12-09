import json
import time
from datetime import datetime

from FlightRadar24.api import FlightRadar24API
from tqdm import tqdm


# Получение треков путём доставания архивной информации о пройденном пути
class Trails24:
    def __init__(self, coords, destination_filename):
        self.out_filename = destination_filename
        self.coords = coords
        self.fr_api = FlightRadar24API()

    def launch_counter(self, iterations=1, pause_time=0, pause_trail_time=0):
        """
        Получение треков путём доставания архивной информации о пройденном пути
        """
        flight_data = {}
        for i in tqdm(range(iterations)):
            try:
                print(f"  \n Старт итерации № {i + 1} сохранения треков. Не выключайте программу.")
                for j, coord in tqdm(enumerate(self.coords)):
                    print(
                        f" \n Старт сохранения треков для координат {coord[0]}: {coord[2]}, {coord[3]} в ходе итерации {i + 1}. Не выключайте программу.")
                    self.write_flights_on_zone(flight_data, coord)
                    if j < len(self.coords) - 1:  # если это не последняя координата
                        time.sleep(pause_trail_time)
                with open(self.out_filename, "w") as f:
                    json.dump(flight_data, f)
            except Exception as e:
                print(f"launch_counter error: {e}")
            if i < iterations - 1:
                print(f"Пауза между итерациями. Осталось {pause_time} секунд.")
                time.sleep(pause_time)

        with open(self.out_filename, "w") as f:
            f.write('[ \n')
            for flight_id, data in flight_data.items():
                data.sort(key=lambda x: x['time'], reverse=True)
                for point in data:
                    f.write('   ' + json.dumps(point) + ',\n')
            f.seek(f.tell() - 3)
            f.truncate()
            f.write('\n ]')
        print("Файл сохранён.")

    # значения vertical_speed, on_ground одинаковые всё время цикла т.к. этих данных нет во flight details.
    def write_flights_on_zone(self, flight_data, coord):
        city, radius, latitude, longitude = coord
        bounds = self.fr_api.get_bounds_by_point(latitude, longitude, radius)
        flights = self.fr_api.get_flights(bounds=bounds)

        for flight in flights:
            print(flight.callsign)
            details = self.fr_api.get_flight_details(flight)

            # Используем метод get() для получения значения 'trail' с обработкой отсутствия ключа
            flight_history = details.get('trail')

            if flight_history is None:
                print(f"Ошибка: Не удалось спарсить рейс {flight.callsign} (ID: {flight.id}). Отсутствует ключ 'trail'.")
                continue  # Пропускаем текущий рейс и переходим к следующему

            flight_id = flight.id
            flight_time_dep = details['time']['real']['departure']
            flight_time_arr = details['time']['estimated']['arrival']

            time_dep = ''
            time_arr = ''

            if flight_id not in flight_data:
                flight_data[flight_id] = []
            unique_points = set()

            for point in flight_history:
                try:
                    time_dep = datetime.fromtimestamp(flight_time_dep).strftime(
                        '%Y-%m-%d %H:%M:%S.%f') if flight_time_dep else 'NULL'
                    time_arr = datetime.fromtimestamp(flight_time_arr).strftime(
                        '%Y-%m-%d %H:%M:%S.%f') if flight_time_arr else 'NULL'
                except ValueError:
                    time_dep = 'NULL'
                    time_arr = 'NULL'

            for point in flight_history:
                data = (
                    datetime.fromtimestamp(point['ts']).strftime('%Y-%m-%d %H:%M:%S.%f'),
                    flight.id,
                    flight.callsign,
                    flight.aircraft_code,
                    flight.number,
                    flight.airline_icao,
                    flight.on_ground,
                    point['spd'],
                    flight.vertical_speed,
                    point['alt'],
                    point['lat'],
                    point['lng'],
                    flight.origin_airport_iata,
                    flight.destination_airport_iata,
                    time_dep,
                    time_arr,
                    point['hd']
                )
                unique_points.add(data)

            flight_data[flight_id] = [dict(zip([
                "time",
                "id",
                "callsign",
                "aircraftCode",
                "flightNumber",
                "airlineIcao",
                "onGround",
                "groundSpeed_Kts",
                "verticalSpeed",
                "altitude_Ft",
                "latitude",
                "longitude",
                "airportOrigin",
                "airportDestination",
                "origin_time",
                "destination_time",
                "head_direction"
            ], point)) for point in unique_points]
