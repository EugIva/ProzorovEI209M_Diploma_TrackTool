import json
import matplotlib.pyplot as plt
import os
import datetime


def routes_drawer_3D(file_path):

    with open(f'{file_path}') as f:
        data = json.load(f)

    dir_path, file_name = os.path.split(file_path)
    file_name_short = os.path.splitext(file_name)[0]
    flight_trajectories = {}

    for aircraft in data:
        aircraft_callsign = aircraft['callsign']
        altitude_ft = int(aircraft['altitude_Ft'])
        latitude = float(aircraft['latitude'])
        longitude = float(aircraft['longitude'])
        time = aircraft['time']
        datetime_object = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
        time_only = datetime_object.strftime('%m%d %H%M')

        # из футов в метры
        altitude_m = altitude_ft * 0.3048

        if aircraft_callsign not in flight_trajectories:
            flight_trajectories[aircraft_callsign] = {'latitudes': [], 'longitudes': [], 'altitudes': []}
        flight_trajectories[aircraft_callsign]['latitudes'].append(latitude)
        flight_trajectories[aircraft_callsign]['longitudes'].append(longitude)
        flight_trajectories[aircraft_callsign]['altitudes'].append(altitude_m)

    fig = plt.figure('Треки в 3D')
    ax = fig.add_subplot(111, projection='3d')

    for i, (aircraft_callsign, trajectory) in enumerate(flight_trajectories.items()):
        ax.plot(trajectory['longitudes'], trajectory['latitudes'], trajectory['altitudes'], label=aircraft_callsign)

    ax.set_xlabel('Longitude \ Долгота')
    ax.set_ylabel('Latitude \ Широта')
    ax.set_zlabel('Высота (м)')
    ax.legend()

    folder_path = 'Exports/drawRoutes3D'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    plt.savefig(os.path.join(folder_path, f'routes3D_{file_name_short}.png'))

    plt.show()
