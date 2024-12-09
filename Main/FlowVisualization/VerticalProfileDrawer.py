import datetime
import json
import os

import matplotlib.pyplot as plt


def vertical_routes_drawer(file_path):
    """
    Рисовка вертикальных профилей
    """

    with open(f'{file_path}') as f:
        data = json.load(f)

    dir_path, file_name = os.path.split(file_path)
    file_name_short = os.path.splitext(file_name)[0]

    altitude_profiles = {}

    for aircraft in data:
        aircraft_callsign = aircraft['callsign']

        altitude_ft = int(aircraft['altitude_Ft'])
        time = aircraft['time']

        # футы в метры
        altitude_m = altitude_ft * 0.3048

        datetime_object = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
        time_only = datetime_object.strftime('%H:%M')

        if aircraft_callsign not in altitude_profiles:
            altitude_profiles[aircraft_callsign] = {'times': [], 'altitudes': []}
        altitude_profiles[aircraft_callsign]['times'].append(time_only)
        altitude_profiles[aircraft_callsign]['altitudes'].append(altitude_m)

    fig, ax = plt.subplots()

    for i, (aircraft_callsign, profile) in enumerate(altitude_profiles.items()):
        ax.plot(profile['times'], profile['altitudes'], label=aircraft_callsign)

    ax.set_xlabel('Время (час)')
    ax.set_ylabel('Высота (метры)')
    ax.legend()

    fig.canvas.manager.set_window_title('Вертикальные профили')
    plt.title('Вертикальные профили')

    folder_path = 'Exports/drawVerticalProfiles'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    plt.savefig(os.path.join(folder_path, f'verticalProfiles_{file_name_short}.png'))

    plt.show()
