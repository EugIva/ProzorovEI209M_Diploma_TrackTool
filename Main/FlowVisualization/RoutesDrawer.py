import datetime
import json
import os

import matplotlib.patches as patches
import matplotlib.pyplot as plt


def RoutesDrawer2D(file_path):
    """
    Рисовка треков в 2Д формате
    """

    with open(f'{file_path}', 'r') as file:
        data = json.load(file)

    dir_path, file_name = os.path.split(file_path)
    file_name_short = os.path.splitext(file_name)[0]

    routes = {}

    for entry in data:
        time = entry['time']
        datetime_object = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
        time_only = datetime_object.strftime('%m%d %H%M')

        callsign = entry['callsign']
        if callsign not in routes:
            routes[callsign] = {'Latitude': [], 'Longitude': []}
        routes[callsign]['Latitude'].append(float(entry['latitude']))
        routes[callsign]['Longitude'].append(float(entry['longitude']))

    # отрисовка маршрутов
    plt.figure(figsize=(12, 8), num='Отрисовка треков на плоскости')

    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    color_idx = 0

    for callsign, route in routes.items():
        plt.plot(route['Longitude'], route['Latitude'], label=callsign, color=colors[color_idx])
        color_idx = (color_idx + 1) % len(colors)

    # отрисовка UUEE
    rect1_coords = [(37.386441, 55.970013), (37.386732, 55.969541), (37.442101, 55.977772), (37.441769, 55.978297)]
    rect2_coords = [(37.386079, 55.967435), (37.386382, 55.966815), (37.444251, 55.975374), (37.443908, 55.976101)]
    rect1 = patches.Rectangle((min(x[0] for x in rect1_coords), min(y[1] for y in rect1_coords)),
                              abs(max(x[0] for x in rect1_coords) - min(x[0] for x in rect1_coords)),
                              abs(max(y[1] for y in rect1_coords) - min(y[1] for y in rect1_coords)),
                              linewidth=0.1, edgecolor='black', facecolor='black')
    rect2 = patches.Rectangle((min(x[0] for x in rect2_coords), min(y[1] for y in rect2_coords)),
                              abs(max(x[0] for x in rect2_coords) - min(x[0] for x in rect2_coords)),
                              abs(max(y[1] for y in rect2_coords) - min(y[1] for y in rect2_coords)),
                              linewidth=0.1, edgecolor='black', facecolor='black')
    plt.text(37.451741, 55.996027, 'SVO \ UUEE', color='black')
    plt.gca().add_patch(rect1)
    plt.gca().add_patch(rect2)

    # отрисовка легенд
    plt.xlabel('Longitude \ Долгота')
    plt.ylabel('Latitude \ Широта')
    plt.title('Трековая информация')
    plt.legend()

    # создание папки
    if not os.path.exists('Exports/drawRoutes2D'):
        os.makedirs('Exports/drawRoutes2D')

    # сохранение результатов
    plt.savefig(os.path.join('Exports/drawRoutes2D', f'flightTracks_{file_name_short}.png'))
    plt.show()
