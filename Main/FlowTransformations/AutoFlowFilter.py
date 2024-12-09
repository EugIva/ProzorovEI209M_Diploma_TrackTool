import json
import os
import time
from tkinter import messagebox

from tqdm import tqdm

import Main.FlowVisualization.FlowInfo
import Main.MathVincenty
import Main.PushNotify
from Main.Functions import file_existing_choose


def filter_flow(self, file_path, filtered_info_label):
    """
    Преобразование потока путём отсеивания рейсов, которые не проходят по отмеченным условиям
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        output_dir = "Exports/flowFiltered"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        file_name = os.path.basename(file_path)
        output_file_path = os.path.join(output_dir, f"Filtered_{file_name}")

        dir_path, file_name = os.path.split(file_path)
        file_name_short = os.path.splitext(file_name)[0]

        file_existing_choose(output_file_path)

        flights = {}
        for item in data:
            if item['id'] not in flights:
                flights[item['id']] = []
            flights[item['id']].append(item)

        filtered_flights = {}
        pbar = tqdm(flights.items())
        for flight_id, flight_data in pbar:
            pbar.set_description('Выполнение автоматического фильтрования потока')
            if self.min_points_var.get() and len(flight_data) < int(self.min_points_entry.get()):
                continue

            if self.airport_origin_var.get() and any(item['airportOrigin'] == "" for item in flight_data):
                continue

            if self.airport_destination_var.get() and any(item['airportDestination'] == "" for item in flight_data):
                continue

            if self.check_flightNumber_var.get() and any(item['flightNumber'] == "" for item in flight_data):
                continue

            if self.type_vs_var.get() and any(item['aircraftCode'] == "" for item in flight_data):
                continue

            if self.bort_number_var.get() and any(item['id'] == "" for item in flight_data):
                continue

            if self.no_missing_coords_var.get() and any(
                    item['latitude'] == "" or item['longitude'] == "" for item in flight_data):
                continue

            if self.no_missing_altitude_var.get() and any(item['altitude_Ft'] == "" for item in flight_data):
                continue

            if self.speed_var.get() and any(item['groundSpeed_Kts'] == "" for item in flight_data):
                continue

            if self.callsign_var.get() and any(item['callsign'] == "" for item in flight_data):
                continue

            if self.check_dep_time_var.get() and any(item['origin_time'] == "NULL" for item in flight_data):
                continue

            if self.check_arr_time_var.get() and any(item['destination_time'] == "NULL" for item in flight_data):
                continue

            if self.takeoff_to_landing_var.get():
                if flight_data:
                    takeoff_landing = (flight_data[0]['altitude_Ft'], flight_data[-1]['altitude_Ft'])
                else:
                    continue

                if takeoff_landing[0] * 0.3048 > int(self.takeoff_to_landing_entry.get()) or takeoff_landing[
                    1] * 0.3048 > int(self.takeoff_to_landing_entry.get()):
                    continue

            # "обрезать высоту 0м"
            if self.cut_altitude_var.get():
                flight_data = [item for item in flight_data if item['altitude_Ft'] != 0]

            # дистанция между точками
            if self.min_distance_var.get():
                distances = []
                for i in range(len(flight_data) - 1):
                    point1 = (flight_data[i]['latitude'], flight_data[i]['longitude'])
                    point2 = (flight_data[i + 1]['latitude'], flight_data[i + 1]['longitude'])
                    distance = Main.MathVincenty.vincenty(point1, point2)
                    distances.append(distance)
                if any(distance > int(self.min_distance_entry.get()) for distance in distances):
                    continue

            # время полёта не менее
            if self.flight_time_var.get():
                if flight_data:
                    start_time = min(item['time'] for item in flight_data)
                    end_time = max(item['time'] for item in flight_data)
                else:
                    continue

                start_time_timestamp = int(
                    time.mktime(time.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f"))) - time.timezone
                end_time_timestamp = int(time.mktime(time.strptime(end_time, "%Y-%m-%d %H:%M:%S.%f"))) - time.timezone

                flight_time_timestamp = end_time_timestamp - start_time_timestamp
                flight_time_entry_timestamp = int(self.flight_time_entry.get()) * 60

                if flight_time_timestamp < flight_time_entry_timestamp:
                    continue

            # проверка на соответсвие названию аэропорта
            if self.airport_origin_checkbox_var.get() and any(
                    item['airportOrigin'] != self.airport_origin_entry.get() for item in flight_data):
                continue
            if self.airport_destination_checkbox_var.get() and any(
                    item['airportDestination'] != self.airport_destination_entry.get() for item in flight_data):
                continue

            filtered_flights[flight_id] = flight_data

        print('Фильтрация завершена. Дождитесь сохранения JSON файла')
        with open(output_file_path, 'w') as f:
            json.dump([item for flight_data in filtered_flights.values() for item in flight_data], f, indent=4)
        print(f"Процесс авто-фильтрации завершен успешно. Результат сохранен в файле {output_file_path}")

        Main.FlowVisualization.FlowInfo.display_flow_info(output_file_path, filtered_info_label, None)

        Main.PushNotify.notify_popup('Авто-фильтрация потока',
                                     f'Преобразование потока {file_name_short} завершено успешно')

    except Exception as e:
        print(f"{e}")
        messagebox.showerror("Ошибка", "Файл не корректный. Проверьте формат или содержимое файла.")


def update_min_distance_entry(self, min_distance_var, min_distance_entry):
    if min_distance_var.get():
        min_distance_entry.config(state='normal')
        min_distance_entry.delete(0, 'end')
        min_distance_entry.insert(0, '50')
    else:
        min_distance_entry.delete(0, 'end')
        min_distance_entry.config(state='disabled')


def update_flight_time_entry(self, flight_time_var, flight_time_entry):
    if flight_time_var.get():
        flight_time_entry.config(state='normal')
        flight_time_entry.delete(0, 'end')
        flight_time_entry.insert(0, '30')
    else:
        flight_time_entry.delete(0, 'end')
        flight_time_entry.config(state='disabled')


def update_airport_origin_entry(self, airport_origin_var, airport_origin_entry, airport_origin_checkbox_var):
    if airport_origin_var.get():
        airport_origin_entry.config(state='normal')
        airport_origin_checkbox_var.set(0)
    else:
        airport_origin_entry.delete(0, 'end')
        airport_origin_entry.config(state='disabled')


def update_takeoff_to_landing_entry(self, takeoff_to_landing_var, takeoff_to_landing_entry):
    if takeoff_to_landing_var.get():
        takeoff_to_landing_entry.config(state='normal')
        takeoff_to_landing_entry.delete(0, 'end')
        takeoff_to_landing_entry.insert(0, '1000')
    else:
        takeoff_to_landing_entry.delete(0, 'end')
        takeoff_to_landing_entry.config(state='disabled')


def update_airport_destination_entry(self, airport_destination_var, airport_destination_entry,
                                     airport_destination_checkbox_var):
    if airport_destination_var.get():
        airport_destination_entry.config(state='normal')
        airport_destination_checkbox_var.set(0)
    else:
        airport_destination_entry.delete(0, 'end')
        airport_destination_entry.config(state='disabled')


def update_min_points_entry(self, min_points_var, min_points_entry):
    if min_points_var.get():
        min_points_entry.config(state='normal')
        min_points_entry.delete(0, 'end')
        min_points_entry.insert(0, '70')
    else:
        min_points_entry.delete(0, 'end')
        min_points_entry.config(state='disabled')


###
def update_airport_origin_checkbox(self, airport_origin_checkbox_var, airport_origin_entry, airport_origin_checkbox):
    if airport_origin_checkbox_var.get():
        airport_origin_checkbox_var.set(0)
        airport_origin_entry.config(state='normal')
        self.airport_origin_checkbox.config(state='disabled')
        self.airport_origin_checkbox_var.set(1)
        self.airport_origin_button.config(state='disabled')  # блок "аэропорт вылета"
    else:
        airport_origin_checkbox_var.set(1)
        airport_origin_entry.config(state='disabled')
        self.airport_origin_checkbox.config(state='normal')
        self.airport_origin_checkbox_var.set(0)
        self.airport_origin_button.config(state='normal')  # анблок "аэропорт вылета" button


def update_airport_destination_checkbox(self, airport_destination_checkbox_var, airport_destination_entry,
                                        airport_destination_checkbox):
    if airport_destination_checkbox_var.get():
        airport_destination_checkbox_var.set(0)
        airport_destination_entry.config(state='normal')
        self.airport_destination_checkbox.config(state='disabled')
        self.airport_destination_checkbox_var.set(1)
        self.airport_destination_button.config(state='disabled')  # блок "аэропорт прилёта"
    else:
        airport_destination_checkbox_var.set(1)
        airport_destination_entry.config(state='disabled')
        self.airport_destination_checkbox.config(state='normal')
        self.airport_destination_checkbox_var.set(0)
        self.airport_destination_button.config(state='normal')  # анблок "аэропорт прилёта" button


def update_airport_origin(self, airport_origin_var, airport_origin_checkbox_named,
                          airport_origin_entry):  # кнопки во втором столбике
    if airport_origin_var.get():
        airport_origin_var.set(1)
        airport_origin_checkbox_named.config(state='disabled')
        airport_origin_entry.delete(0, 'end')
        airport_origin_entry.config(state='disabled')
        self.airport_origin_button.config(state='disabled')
    else:
        airport_origin_var.set(0)
        airport_origin_checkbox_named.config(state='normal')
        self.airport_origin_button.config(state='normal')
        airport_origin_entry.config(state='normal')


def update_airport_destination(self, airport_destination_var, airport_destination_checkbox_named,
                               airport_destination_entry):
    if airport_destination_var.get():
        airport_destination_var.set(1)
        airport_destination_checkbox_named.config(state='disabled')
        airport_destination_entry.delete(0, 'end')
        airport_destination_entry.config(state='disabled')
        self.airport_destination_button.config(state='disabled')
    else:
        airport_destination_var.set(0)
        airport_destination_checkbox_named.config(state='normal')
        airport_destination_entry.config(state='normal')
        self.airport_destination_button.config(state='normal')
