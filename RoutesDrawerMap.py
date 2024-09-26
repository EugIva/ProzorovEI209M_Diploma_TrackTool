import json
from tkinter import messagebox
import random
from PIL import ImageTk, Image


def display_tracks(self, file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)

        plane_marker = ImageTk.PhotoImage(Image.open('content/UI/startSniff.png'))

        tracks = {}
        for track in data:
            aircraft_id = track["id"]
            if aircraft_id not in tracks:
                tracks[aircraft_id] = []
            tracks[aircraft_id].append((float(track["latitude"]), float(track["longitude"])))

        for aircraft_id, track in tracks.items():
            if len(track) < 2:
                continue

            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            color = f"#{r:02x}{g:02x}{b:02x}"

            canvas_line_positions = []
            for i in range(len(track)):
                canvas_line_positions.append(track[i])
                canvas_line_positions.append(track[i])

            path = self.map_widget.set_path(canvas_line_positions, color=color, width=2)

            # лейбл callsign и самолётик в начало треков
            first_point = track[-1]
            callsign = next(track for track in data if track["id"] == aircraft_id)["callsign"]
            marker = self.map_widget.set_marker(first_point[0], first_point[1], text=callsign, icon=plane_marker,
                                                text_color=color)

    except FileNotFoundError:
        messagebox.showerror("Ошибка", "Файл не найден")
    except json.JSONDecodeError:
        messagebox.showerror("Ошибка", "Неверный формат файла")
    except Exception as e:
        messagebox.showerror("Ошибка", "Неизвестная ошибка: " + str(e))
        print(e)


def change_data_source(self, value):
    if value == "OpenStreetMap":
        self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
    elif value == "Google Maps":
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
    elif value == "Google спутник":
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
    elif value == "Google рельеф":
        self.map_widget.set_tile_server("https://mts0.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}&s=Ga")


def clear_map(path, marker):
    try:
        messagebox.showinfo("Карта очищена", "Маркеры и треки удалены.")
    except Exception as e:
        messagebox.showerror("Ошибка", "Неизвестная ошибка: " + str(e))
        print(e)
