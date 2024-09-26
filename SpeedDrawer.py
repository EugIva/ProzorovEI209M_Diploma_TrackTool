import json
import os
from tkinter import messagebox

from matplotlib import pyplot as plt


def draw_speed_graph(file_path, speed_type_var):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        dir_path, file_name = os.path.split(file_path)
        name_short = os.path.splitext(file_name)[0]

        speed_type = speed_type_var.get()

        aircraft_ids = set(item["id"] for item in data)
        for aircraft_id in aircraft_ids:
            aircraft_data = [item for item in data if item["id"] == aircraft_id]
            callsigns = [item["callsign"] for item in aircraft_data]
            times = [item["time"] for item in aircraft_data]
            speeds = [float(item[speed_type]) for item in aircraft_data]

            plt.plot(times, speeds, label=callsigns[0])

        plt.xlabel("Время")
        plt.ylabel("Скорость")
        plt.title("График скорости")
        plt.legend()
        fig = plt.gcf()
        fig.canvas.manager.set_window_title("График скорости")

        # создание папки
        if not os.path.exists('Exports/drawSpeed'):
            os.makedirs('Exports/drawSpeed')

        # сохранение результатов
        plt.savefig(os.path.join('Exports/drawSpeed', f'flightTracks_{name_short}.png'))
        plt.show()

    except Exception as e:
        print(f"{e}")
        messagebox.showerror("Ошибка", "Файл не корректный. Проверьте формат или содержимое файла.")
