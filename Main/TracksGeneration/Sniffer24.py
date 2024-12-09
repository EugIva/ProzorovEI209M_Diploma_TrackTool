import time
from datetime import datetime

import requests
from FlightRadar24.api import FlightRadar24API


# Получение треков с помощью онлайн сниффера
class Sniffer24:
    time_step = 1

    def __init__(self, borders, destination_filename, finish_time, callsign, origin_airport, on_ground):
        self.out_filename = destination_filename
        self.out = open(self.out_filename, "a")
        self.out.close()
        self.fr_api = FlightRadar24API()
        self.zone = borders
        self.finish = finish_time
        self.callsign = callsign
        self.origin_airport = origin_airport
        if on_ground == 'В воздухе':
            self.on_ground = '0'
        elif on_ground == 'На земле':
            self.on_ground = '1'
        elif on_ground == '':
            self.on_ground = on_ground

    def launch_counter(self):
        """
        Получение треков с помощью онлайн сниффера
        """
        timing = time.time()
        self.out = open(self.out_filename, "a")
        self.out.write('[ \n')
        self.out.close()
        try:
            while timing < self.finish:
                if time.time() - timing > self.time_step:
                    self.out = open(self.out_filename, "a")
                    timing = time.time()
                    flights = self.fr_api.get_flights(bounds=self.zone)

                    size = len(flights)
                    for i in range(size):
                        if self.callsign and flights[i].callsign not in self.callsign.split(','):
                            continue
                        if self.origin_airport and flights[i].origin_airport_iata not in self.origin_airport.split(','):
                            continue
                        if self.on_ground and str(flights[i].on_ground) != self.on_ground:
                            continue
                        print(flights[i].callsign)
                        print(flights[i].latitude)
                        print(flights[i].longitude)

                        # flight = flights[i]
                        # flight_details = self.fr_api.get_flight_details(flight)
                        # flight_history = flight_details['trail']
                        # print(flight_history)
                        # flight_promote = flight_details['identification']
                        # print(flight_promote)
                        # print(flight_details.keys())

                        # вывод нужных данных
                        self.out.write(
                            '    { "time": "' + str(datetime.now()) + '", ' +
                            '"id": "' + str(flights[i].id) + '", ' +
                            '"callsign": "' + str(flights[i].callsign) + '", ' +
                            '"aircraftCode": "' + str(flights[i].aircraft_code) + '", ' +
                            '"flightNumber": "' + str(flights[i].number) + '", ' +
                            '"airlineIcao": "' + str(flights[i].airline_icao) + '", ' +
                            '"onGround": "' + str(flights[i].on_ground) + '", ' +
                            '"groundSpeed_Kts": "' + str(flights[i].ground_speed) + '", ' +
                            '"verticalSpeed": "' + str(flights[i].vertical_speed) + '", ' +
                            '"altitude_Ft": "' + str(flights[i].altitude) + '", ' +
                            '"latitude": "' + str(flights[i].latitude) + '", ' +
                            '"longitude": "' + str(flights[i].longitude) + '", ' +
                            '"airportOrigin": "' + str(flights[i].origin_airport_iata) + '", ' +
                            '"airportDestination": "' + str(flights[i].destination_airport_iata) + '"' +
                            ' } ,\n')
                    self.out.close()
        except requests.exceptions.ConnectionError or TimeoutError or requests.exceptions.ConnectTimeout \
               or AttributeError:
            self.out_filename = "1" + self.out_filename
            if timing < self.finish and len(self.out_filename) < 20:
                print("Ошибка подключения " + str(datetime.now()) + ". Попытка переподключения...")
                self.launch_counter()
        self.out = open(self.out_filename, "a")
        self.out.seek(self.out.tell() - 3)
        self.out.truncate()
        self.out.write('\n ]')
        self.out.close()
