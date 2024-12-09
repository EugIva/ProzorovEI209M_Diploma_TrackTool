import json
import random
from tkinter import messagebox

from PIL import ImageTk, Image
from tqdm import tqdm


def display_tracks(self, file_path):
    """
    Рисовка треков на окне с картой
    """

    try:
        with open(file_path, 'r') as file:
            data = json.load(file)

        # путь к файлу
        image = Image.open('Content/UI/MapPlane.png')

        tracks = {}

        for track in data:
            aircraft_id = track["id"]
            if aircraft_id not in tracks:
                tracks[aircraft_id] = []
            tracks[aircraft_id].append((float(track["latitude"]), float(track["longitude"])))

        pbar = tqdm(tracks.items())
        for aircraft_id, track in pbar:
            pbar.set_description("Загрузка рейсов для отрисовки")
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

            # Лейбл callsign и самолётик в начало треков
            first_point = track[-1]  # Assuming the first point is the start of the track
            callsign = next(track for track in data if track["id"] == aircraft_id)["callsign"]
            head_direction = next(track for track in data if track["id"] == aircraft_id).get("head_direction", 0)

            # Проверка на значение hd
            if not isinstance(head_direction, (int, float)):
                if isinstance(head_direction, list):
                    messagebox.showerror("Ошибка", "Угол поворота должен быть числом, а не списком.")
                else:
                    messagebox.showerror("Ошибка", "Угол поворота должен быть числом.")
                continue

            # поворот иконки самолёта туда, куда head direction
            rotated_image = image.rotate(head_direction)
            rotated_image_tk = ImageTk.PhotoImage(rotated_image)

            marker = self.map_widget.set_marker(first_point[0], first_point[1], text=callsign, icon=rotated_image_tk,
                                                text_color=color)

    except FileNotFoundError:
        messagebox.showerror("Ошибка", "Файл не найден")
    except json.JSONDecodeError:
        messagebox.showerror("Ошибка", "Неверный формат файла")
    except Exception as e:
        messagebox.showerror("Ошибка", "Неизвестная ошибка: " + str(e))
        print(e)


# некоторые карты отсюда: https://apidocs.geoapify.com/docs/maps/
def change_data_source(self, value):
    if value == "OpenStreetMap":
        self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
    elif value == "Google Maps":
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
    elif value == "Google спутник":
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
    elif value == "Google гибрид":
        self.map_widget.set_tile_server("http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga")
    elif value == "Google рельеф":
        self.map_widget.set_tile_server("https://mts0.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}&s=Ga")
    elif value == "Светлая":
        self.map_widget.set_tile_server("https://maps.geoapify.com/v1/tile/positron/{z}/{x}/{y}.png?apiKey=3a81f44946bf490dba43a870c374911c")
    elif value == "Тёмная":
        self.map_widget.set_tile_server("https://maps.geoapify.com/v1/tile/dark-matter-brown/{z}/{x}/{y}.png?apiKey=3a81f44946bf490dba43a870c374911c")
    elif value == "Схематичная":
        self.map_widget.set_tile_server("https://maps.geoapify.com/v1/tile/maptiler-3d/{z}/{x}/{y}.png?apiKey=3a81f44946bf490dba43a870c374911c")
    elif value == "Пустая":
        self.map_widget.set_tile_server("http://khm.google.com/kh/v=89&hl=ru&x=%2&y=%3&z=%1&s=Galileo")



def clear_map(self):
    try:
        self.map_widget.delete_all_path()
        self.map_widget.delete_all_marker()
        messagebox.showinfo("Карта очищена", "Маркеры и треки удалены.")
    except Exception as e:
        messagebox.showerror("Ошибка", "Неизвестная ошибка: " + str(e))
        print(e)
