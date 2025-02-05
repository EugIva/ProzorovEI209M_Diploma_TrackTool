import os
import tkinter as tk
from tkinter import ttk

import TKinterModernThemes as TKMT
import tkintermapview

import Main.FlowTransformations.AutoFlowFilter
import Main.FlowTransformations.MergerJson
import Main.FlowVisualization.FlowInfo
import Main.Functions
from Main.FlowExports.ExportArtfmJson import convert_json_atfm
from Main.FlowExports.ExportKimCsv import convert_csv_kim
from Main.FlowTransformations.DivideJson import divide_json_file
from Main.FlowTransformations.FlowSorter import FlowSorter
from Main.FlowTransformations.RouteCutter import RouteCutter
from Main.FlowVisualization.RoutesDrawerMap import display_tracks, change_data_source, clear_map


class TrackTool(TKMT.ThemedTKinterFrame):
    def __init__(self, theme, mode, usecommandlineargs=True, usethemeconfigfile=True):
        super().__init__("TrackTool", theme, mode, usecommandlineargs, usethemeconfigfile)
        self.root.iconbitmap("Content/UI/logo.ico")
        self.create_initial_window()

    def create_initial_window(self):
        # первичное окно выбора функции
        self.initial_frame = tk.Frame(self.root)
        self.initial_frame.pack(expand=1, fill=tk.BOTH)

        # "Работа с данными"
        data_button = ttk.Button(self.initial_frame, text="Работа с данными", command=self.load_data_notebook, style='Accent.TButton')
        data_button.pack(fill=tk.X, expand=True, padx=400, pady=110, ipadx=80, ipady=10)

        # "Нейросетевые функции"
        neural_button = ttk.Button(self.initial_frame, text="Нейросетевые функции", command=self.load_neural_notebook, style='Accent.TButton')
        neural_button.pack(fill=tk.X, expand=True, padx=400, pady=110, ipadx=80, ipady=10)

    def load_data_notebook(self):
        self.initial_frame.pack_forget()
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=1, fill=tk.BOTH)

        # Вкладки
        self.settings_tab = ttk.Frame(self.notebook)
        self.sniffer_tab = ttk.Frame(self.notebook)
        self.file_tab = ttk.Frame(self.notebook)
        self.exports_tab = ttk.Frame(self.notebook)
        self.visualization_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.settings_tab, text="⚙")
        self.notebook.add(self.sniffer_tab, text=" Генерация треков ")
        self.notebook.add(self.file_tab, text=" Преобразования треков ")
        self.notebook.add(self.exports_tab, text=" Экспортирование треков ")
        self.notebook.add(self.visualization_tab, text=" Визуализация треков")

        # Вкладка "Снифер"
        self.sniffer_notebook = ttk.Notebook(self.sniffer_tab)
        self.sniffer_notebook.pack(expand=1, fill=tk.BOTH)
        self.sniffer_frame = ttk.Frame(self.sniffer_notebook)
        self.stamp_tab = ttk.Frame(self.sniffer_notebook)

        self.sniffer_notebook.add(self.sniffer_frame, text=" Онлайн-сниффер ")
        self.sniffer_notebook.add(self.stamp_tab, text=" Слепок ")

        # Вкладка "Работа над файлами"
        self.file_notebook = ttk.Notebook(self.file_tab)
        self.file_notebook.pack(expand=1, fill=tk.BOTH)
        self.excel_tab = ttk.Frame(self.file_notebook)
        self.divide_json_tab = ttk.Frame(self.file_notebook)
        self.json_merger_tab = ttk.Frame(self.file_notebook)
        self.auto_filter_tab = ttk.Frame(self.file_notebook)
        self.manual_sorting_tab = ttk.Frame(self.file_notebook)
        self.track_cutter_tab = ttk.Frame(self.file_notebook)

        self.file_notebook.add(self.excel_tab, text=" Экспорт в Excel ")
        self.file_notebook.add(self.divide_json_tab, text=" Разделение JSON ")
        self.file_notebook.add(self.json_merger_tab, text="Слияние и редактирование JSON")
        self.file_notebook.add(self.auto_filter_tab, text="Авто-фильтрация потока")
        self.file_notebook.add(self.manual_sorting_tab, text="Ручная сортировка потока")
        self.file_notebook.add(self.track_cutter_tab, text="Вырезание участков трека")

        # вкладка "экспортирование треков"
        self.exports_notebook = ttk.Notebook(self.exports_tab)
        self.exports_notebook.pack(expand=1, fill=tk.BOTH)

        self.export_to_atfm_tab = ttk.Frame(self.exports_notebook)
        self.export_to_kim_csv_tab = ttk.Frame(self.exports_notebook)

        self.exports_notebook.add(self.export_to_atfm_tab, text=" Экспорт в JSON для ATFM-model ")
        self.exports_notebook.add(self.export_to_kim_csv_tab, text=" Экспорт в CSV для КИМ ")

        # Вкладка "Визуализация"
        self.visualization_notebook = ttk.Notebook(self.visualization_tab)
        self.visualization_notebook.pack(expand=1, fill=tk.BOTH)
        self.flow_info_tab = ttk.Frame(self.visualization_notebook)
        self.speed_graph_tab = ttk.Frame(self.visualization_notebook)
        self.drawer2D_tab = ttk.Frame(self.visualization_notebook)
        self.drawerVertical_tab = ttk.Frame(self.visualization_notebook)
        self.drawer3D_tab = ttk.Frame(self.visualization_notebook)
        self.map_tab = ttk.Frame(self.visualization_notebook)

        self.visualization_notebook.add(self.flow_info_tab, text=" Информация о потоке ")
        self.visualization_notebook.add(self.drawer2D_tab, text=" Треки на плоскости ")
        self.visualization_notebook.add(self.drawerVertical_tab, text=" Вертикальные профили ")
        self.visualization_notebook.add(self.speed_graph_tab, text=" График скорости ")
        self.visualization_notebook.add(self.drawer3D_tab, text=" Отрисовка треков 3D ")
        self.visualization_notebook.add(self.map_tab, text=" Карта ")

        # Первичные переменные
        self.minutes_var = tk.StringVar()
        self.minutes_var.set("12")
        self.radius_var = tk.StringVar()
        self.radius_var.set("80000")
        self.latitude_var = tk.StringVar()
        self.latitude_var.set("55.975593")
        self.longitude_var = tk.StringVar()
        self.longitude_var.set("37.400021")

        self.city_var_trail = tk.StringVar()
        self.city_var_trail.set("Москва")
        self.radius_var_trail = tk.StringVar()
        self.radius_var_trail.set("80000")
        self.latitude_var_trail = tk.StringVar()
        self.latitude_var_trail.set("55.975593")
        self.longitude_var_trail = tk.StringVar()
        self.longitude_var_trail.set("37.400021")

        self.iterations_var_trail = tk.StringVar()
        self.iterations_var_trail.set("2")

        self.pause_var_trail = tk.StringVar()
        self.pause_var_trail.set("600")

        self.pause_var_trail_coords = tk.StringVar()
        self.pause_var_trail_coords.set("15")

        self.merged_name_var = tk.StringVar()
        self.merged_name_var.set("MergedFlow")

        self.sorted_name_var = tk.StringVar()
        self.sorted_name_var.set("SortedFlow")

        self.font_txt = ('Fira Code SemiBold', 10)
        self.font_txt_light = ('Fira Code Light', 8)
        self.font_buttons = ('Roboto Cn', 12)

        self.atfm_name_var = tk.StringVar()
        self.atfm_name_var.set("Track data")
        self.atfm_comment_var = tk.StringVar()
        self.atfm_comment_var.set("TrackTool exported")
        self.atfm_catalog_var = tk.StringVar()
        self.atfm_catalog_var.set("100")
        self.atfm_user_var = tk.StringVar()
        self.atfm_user_var.set("1")
        self.atfm_number_var = tk.StringVar()
        self.atfm_number_var.set("1")

        self.kim_name_var = tk.StringVar()
        self.kim_name_var.set("Track data")

        self.create_widgets()

        # справочные тексты
        help_file = 'Content\help_texts.txt'
        help_texts = Main.Functions.read_help_texts(help_file)
        self.help_sniffer = help_texts['help_sniffer']
        self.help_trails = help_texts['help_trails']
        self.help_excel = help_texts['help_excel']
        self.help_jsonDivide = help_texts['help_jsonDivide']
        self.help_jsonMerge = help_texts['help_jsonMerge']
        self.help_flowSorter = help_texts['help_flowSorter']
        self.help_flowFilter = help_texts['help_flowFilter']
        self.help_kim = help_texts['help_kim']
        self.help_draw2D = help_texts['help_draw2D']
        self.help_drawVert = help_texts['help_drawVert']
        self.help_drawSpeed = help_texts['help_drawSpeed']
        self.help_draw3D = help_texts['help_draw3D']
        self.help_drawMap = help_texts['help_drawMap']
        self.help_flowInfo = help_texts['help_flowInfo']
        self.help_atfm = help_texts['help_atfm']


    def create_widgets(self):
        # настройки
        self.settings_frame = ttk.Frame(self.settings_tab)
        self.settings_frame.pack(fill="both", expand=True)

        self.color_scheme_label = ttk.Label(self.settings_frame, text="Настройка цвета окна:", font=self.font_txt)
        self.color_scheme_label.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.color_scheme_var = tk.StringVar()
        self.color_scheme_var.set("☀ / ☽")

        self.color_scheme_option = ttk.OptionMenu(self.settings_frame, self.color_scheme_var, "", "dark", "light",
                                                  command=lambda value: change_color_scheme(self, value))
        self.color_scheme_option.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        def change_color_scheme(self, value):
            new_window = TrackTool("Sun-valley", value)
            self.root.withdraw()

        self.color_scheme_label = ttk.Label(self.settings_frame, text="Очистить все результаты:", font=self.font_txt)
        self.color_scheme_label.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        self.clear_exports_button = ttk.Button(self.settings_frame, text="Удалить",
                                               command=lambda: Main.Functions.clear_exports(self))
        self.clear_exports_button.grid(row=1, column=1, padx=10, pady=10)


        self.restart_button = ttk.Button(self.settings_frame, text="Сменить режим работы",
                                    command=self.restart_application)
        self.restart_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)


        # ВКЛАДКА "СНИФФЕР"

        self.on_ground_var = tk.IntVar()
        self.origin_airport_var = tk.IntVar()
        self.callsign_var = tk.IntVar()

        self.filter_frame_lbl = ttk.LabelFrame(self.sniffer_frame, text="Фильтры")
        self.filter_frame_lbl.grid(row=0, column=1, sticky="nsew")

        self.callsign_label = ttk.Label(self.filter_frame_lbl, text="По номеру рейса", font=self.font_txt,
                                        foreground='grey', justify="right", anchor="e")
        self.callsign_label.grid(row=0, column=0, padx=10, pady=10)

        self.callsign_switch = ttk.Checkbutton(self.filter_frame_lbl, variable=self.callsign_var,
                                               command=lambda: Main.Functions.clear_field(self.callsign_entry,
                                                                                          self.callsign_var) or (
                                                                   Main.Functions.enable_field(
                                                                       self.callsign_entry) if self.callsign_var.get() else Main.Functions.disable_field(
                                                                       self.callsign_entry)),
                                               style='Switch.TCheckbutton')
        self.callsign_switch.grid(row=0, column=1, padx=5, pady=10)
        self.callsign_entry = ttk.Entry(self.filter_frame_lbl, width=40)
        self.callsign_entry.grid(row=0, column=2, padx=10, pady=10)
        self.callsign_entry.config(state='disabled')

        self.origin_airport_label = ttk.Label(self.filter_frame_lbl, text="По АП вылета", font=self.font_txt,
                                              foreground='grey', justify="right", anchor="e")
        self.origin_airport_label.grid(row=1, column=0, padx=10, pady=10)

        self.origin_airport_switch = ttk.Checkbutton(self.filter_frame_lbl, variable=self.origin_airport_var,
                                                     command=lambda: Main.Functions.clear_field(
                                                         self.origin_airport_entry, self.origin_airport_var) or (
                                                                         Main.Functions.enable_field(
                                                                             self.origin_airport_entry) if self.origin_airport_var.get() else Main.Functions.disable_field(
                                                                             self.origin_airport_entry)),
                                                     style='Switch.TCheckbutton')
        self.origin_airport_switch.grid(row=1, column=1, padx=5, pady=10)
        self.origin_airport_entry = ttk.Entry(self.filter_frame_lbl, width=40)
        self.origin_airport_entry.grid(row=1, column=2, padx=10, pady=10)
        self.origin_airport_entry.config(state='disabled')

        self.on_ground_label = ttk.Label(self.filter_frame_lbl, text="По положению", font=self.font_txt,
                                         foreground='grey', justify="right", anchor="e")
        self.on_ground_label.grid(row=2, column=0, padx=10, pady=10)

        self.on_ground_switch = ttk.Checkbutton(self.filter_frame_lbl, variable=self.on_ground_var,
                                                command=lambda: Main.Functions.clear_field(self.on_ground_combobox,
                                                                                           self.on_ground_var) or (
                                                                    Main.Functions.enable_field(
                                                                        self.on_ground_combobox) if self.on_ground_var.get() else Main.Functions.disable_field(
                                                                        self.on_ground_combobox)),
                                                style='Switch.TCheckbutton')
        self.on_ground_switch.grid(row=2, column=1, padx=5, pady=10)
        self.on_ground_combobox = ttk.Combobox(self.filter_frame_lbl, values=['В воздухе', 'На земле'], width=37,
                                               state="readonly")
        self.on_ground_combobox.grid(row=2, column=2, padx=10, pady=10)
        self.on_ground_combobox.config(state='disabled')

        self.sniffer_frame_lbl = ttk.LabelFrame(self.sniffer_frame, text="Параметры сеанса")
        self.sniffer_frame_lbl.grid(row=0, column=0, sticky="nsew")

        self.button_frame = ttk.Frame(self.sniffer_frame)
        self.button_frame.grid(row=8, column=0, padx=10, sticky="ew")

        self.session_time_label = ttk.Label(self.sniffer_frame_lbl, text="Время работы (секунды)", font=self.font_txt,
                                            foreground='grey', justify="right", anchor="e")
        self.session_time_label.grid(row=1, column=0, padx=10, pady=10)
        self.session_time_entry = ttk.Spinbox(self.sniffer_frame_lbl, from_=1.0, to=99999999.0, width=38,
                                              textvariable=self.minutes_var)
        self.session_time_entry.grid(row=1, column=1, padx=10, pady=10)

        self.latitude_label = ttk.Label(self.sniffer_frame_lbl, text="Latitude \ Широта", font=self.font_txt,
                                        foreground='grey', justify="right", anchor="e")
        self.latitude_label.grid(row=2, column=0, padx=10, pady=10)
        self.latitude_entry = ttk.Spinbox(self.sniffer_frame_lbl, from_=1.0, to=99999999.0, increment=0.000001,
                                          width=38, textvariable=self.latitude_var)
        self.latitude_entry.grid(row=2, column=1, padx=10, pady=10)

        self.longitude_label = ttk.Label(self.sniffer_frame_lbl, text="Longitude \ Долгота", font=self.font_txt,
                                         foreground='grey', justify="right", anchor="e")
        self.longitude_label.grid(row=3, column=0, padx=10, pady=10)
        self.longitude_entry = ttk.Spinbox(self.sniffer_frame_lbl, from_=1.0, to=99999999.0, increment=0.000001,
                                           width=38, textvariable=self.longitude_var)
        self.longitude_entry.grid(row=3, column=1, padx=10, pady=10)

        self.radius_label = ttk.Label(self.sniffer_frame_lbl, text="Радиус зоны (метры)", font=self.font_txt,
                                      foreground='grey', justify="right", anchor="e")
        self.radius_label.grid(row=4, column=0, padx=10, pady=10)
        self.radius_entry = ttk.Spinbox(self.sniffer_frame_lbl, from_=1.0, to=99999999.0, increment=1000, width=38,
                                        textvariable=self.radius_var)
        self.radius_entry.grid(row=4, column=1, padx=10, pady=10)

        self.filename_label = ttk.Label(self.sniffer_frame_lbl, text="Имя файла", font=self.font_txt, foreground='grey',
                                        justify="right", anchor="e")
        self.filename_label.grid(row=5, column=0, padx=10, pady=10)
        self.filename_entry = ttk.Entry(self.sniffer_frame_lbl, width=45)
        self.filename_entry.insert(0, "NewSession")
        self.filename_entry.grid(row=5, column=1, padx=10, pady=5)

        self.folder_label = ttk.Label(self.sniffer_frame_lbl, text="Файл будет создан в: Exports/sniffer/",
                                      font=self.font_txt_light, foreground='grey', justify="left", anchor="w")
        self.folder_label.grid(row=6, column=1, columnspan=1, padx=5, pady=0)

        self.start_button = ttk.Button(self.button_frame, text="Запустить", compound='left',
                                       command=lambda: Main.Functions.launch_timer(self.session_time_entry,
                                                                                   self.latitude_entry,
                                                                                   self.longitude_entry,
                                                                                   self.radius_entry,
                                                                                   self.filename_entry,
                                                                                   self.callsign_entry,
                                                                                   self.origin_airport_entry,
                                                                                   self.on_ground_combobox,
                                                                                   self.file_info_label),
                                       style='Accent.TButton')
        self.start_button.grid(row=8, column=0, padx=10, pady=30)

        self.open_folder_button = ttk.Button(self.button_frame, text=" Открыть папку ", compound='left',
                                             command=lambda: Main.Functions.open_folder("sniffer"))
        self.open_folder_button.grid(row=8, column=1, padx=40, pady=10)

        self.sniffer_info_button = ttk.Button(self.button_frame, text="⍰",
                                              command=lambda: Main.Functions.show_info(self, self.help_sniffer),
                                              style='Toolbutton')
        self.sniffer_info_button.grid(row=8, column=2, padx=5, pady=5)

        self.sniffer_result_frame = ttk.Frame(self.sniffer_frame)
        self.sniffer_result_frame.grid(row=9, column=0, columnspan=5, padx=10, sticky="ew")

        self.file_info_label = ttk.Label(self.sniffer_result_frame, text="", font=self.font_txt, foreground='grey',
                                         justify="left", anchor="w")
        self.file_info_label.grid(row=0, column=0, columnspan=5, padx=10, pady=0, sticky="nsew")

        # Вкладка "Слепок"
        self.stamp_frame_lbl = ttk.LabelFrame(self.stamp_tab, text="Параметры сеанса")
        self.stamp_frame_lbl.grid(row=0, column=0, rowspan=4, sticky="nsew")

        self.trail_frame_upper_lbl = ttk.Frame(self.stamp_frame_lbl)
        self.trail_frame_upper_lbl.grid(row=0, column=0, sticky="ew")

        self.trail_frame_lower_lbl = ttk.Frame(self.stamp_frame_lbl)
        self.trail_frame_lower_lbl.grid(row=1, column=0, sticky="ew")

        self.city_label_trail = ttk.Label(self.trail_frame_upper_lbl, text="Город (имя точки)", font=self.font_txt,
                                          foreground='grey', justify="right", anchor="e")
        self.city_label_trail.grid(row=0, column=0, padx=10, pady=10)
        self.city_entry_trail = ttk.Entry(self.trail_frame_upper_lbl, width=45, textvariable=self.city_var_trail)
        self.city_entry_trail.grid(row=0, column=1, padx=10, pady=10)

        self.radius_label_trail = ttk.Label(self.trail_frame_upper_lbl, text="Радиус зоны (метры)", font=self.font_txt,
                                            foreground='grey', justify="right", anchor="e")
        self.radius_label_trail.grid(row=1, column=0, padx=10, pady=10)
        self.radius_entry_trail = ttk.Spinbox(self.trail_frame_upper_lbl, from_=1.0, to=99999999.0, increment=1000,
                                              width=38, textvariable=self.radius_var_trail)
        self.radius_entry_trail.grid(row=1, column=1, padx=10, pady=10)

        self.latitude_label_trail = ttk.Label(self.trail_frame_upper_lbl, text="Latitude \ Широта", font=self.font_txt,
                                              foreground='grey', justify="right", anchor="e")
        self.latitude_label_trail.grid(row=2, column=0, padx=10, pady=10)
        self.latitude_entry_trail = ttk.Spinbox(self.trail_frame_upper_lbl, from_=1.0, to=99999999.0,
                                                increment=0.000001, width=38, textvariable=self.latitude_var_trail)
        self.latitude_entry_trail.grid(row=2, column=1, padx=10, pady=10)

        self.longitude_label_trail = ttk.Label(self.trail_frame_upper_lbl, text="Longitude \ Долгота",
                                               font=self.font_txt, foreground='grey', justify="right", anchor="e")
        self.longitude_label_trail.grid(row=3, column=0, padx=10, pady=10)
        self.longitude_entry_trail = ttk.Spinbox(self.trail_frame_upper_lbl, from_=1.0, to=99999999.0,
                                                 increment=0.000001, width=38, textvariable=self.longitude_var_trail)
        self.longitude_entry_trail.grid(row=3, column=1, padx=10, pady=10)

        self.trail_table_buttons_lbl = ttk.Frame(self.trail_frame_upper_lbl)
        self.trail_table_buttons_lbl.grid(row=4, column=0)

        self.trail_add_coords_button = ttk.Button(self.trail_table_buttons_lbl, text=" Добавить ",
                                                  command=lambda: Main.Functions.add_coords_to_table(
                                                      self.trails_treeview, self.city_entry_trail,
                                                      self.radius_entry_trail, self.latitude_entry_trail,
                                                      self.longitude_entry_trail))
        self.trail_add_coords_button.grid(row=0, column=0, padx=20, pady=5, sticky="ew")

        self.trail_delete_coords_button = ttk.Button(self.trail_table_buttons_lbl, text=" Удалить ",
                                                     command=lambda: Main.Functions.delete_coords_from_table(
                                                         self.trails_treeview))
        self.trail_delete_coords_button.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        self.trail_import_coords_button = ttk.Button(self.trail_table_buttons_lbl, text=" Импорт ",
                                                     command=lambda: Main.Functions.import_coords_from_file(
                                                         self.trails_treeview))
        self.trail_import_coords_button.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        self.trail_export_coords_button = ttk.Button(self.trail_table_buttons_lbl, text=" Экспорт ",
                                                     command=lambda: Main.Functions.export_coords_to_file(
                                                         self.trails_treeview))
        self.trail_export_coords_button.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        self.trail_table_lbl = ttk.Frame(self.trail_frame_upper_lbl)
        self.trail_table_lbl.grid(row=4, column=1, sticky="ew")

        self.trails_treeview = ttk.Treeview(self.trail_table_lbl, columns=("City", "Radius", "Latitude", "Longitude"))
        self.trails_treeview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.trails_treeview.configure(height=5)

        self.trails_yscrollbar = ttk.Scrollbar(self.trail_table_lbl, orient="vertical",
                                               command=self.trails_treeview.yview)
        self.trails_yscrollbar.grid(row=0, column=1, sticky="ns")

        self.trails_treeview.config(yscrollcommand=self.trails_yscrollbar.set)

        self.trails_treeview.heading("#0", text="№")
        self.trails_treeview.heading("City", text="City")
        self.trails_treeview.heading("Radius", text="Radius")
        self.trails_treeview.heading("Latitude", text="Latitude")
        self.trails_treeview.heading("Longitude", text="Longitude")

        self.trails_treeview.column("#0", width=5)
        self.trails_treeview.column("City", width=50)
        self.trails_treeview.column("Radius", width=50)
        self.trails_treeview.column("Latitude", width=80)
        self.trails_treeview.column("Longitude", width=80)

        self.trail_table_lbl.rowconfigure(0, weight=1)
        self.trail_table_lbl.columnconfigure(0, weight=1)

        self.trails_treeview.heading("#0", text="№",
                                     command=lambda: Main.Functions.sort_by_column(self, self.treeview, "#0", 0))
        self.trails_treeview.heading("City", text="City",
                                     command=lambda: Main.Functions.sort_by_column(self, self.trails_treeview, "City",
                                                                                   0))
        self.trails_treeview.heading("Radius", text="Radius",
                                     command=lambda: Main.Functions.sort_by_column(self, self.trails_treeview, "Radius",
                                                                                   0))
        self.trails_treeview.heading("Latitude", text="Latitude",
                                     command=lambda: Main.Functions.sort_by_column(self, self.trails_treeview,
                                                                                   "Latitude", 0))
        self.trails_treeview.heading("Longitude", text="Longitude",
                                     command=lambda: Main.Functions.sort_by_column(self, self.trails_treeview,
                                                                                   "Longitude", 0))

        self.pause_trail_label = ttk.Label(self.trail_frame_upper_lbl, text="Пауза (сек)", font=self.font_txt,
                                           foreground='grey')
        self.pause_trail_label.grid(row=5, column=0, padx=10, pady=10)

        self.pause_trail_entry = ttk.Spinbox(self.trail_frame_upper_lbl, width=38, from_=0.0, to=99999999.0,
                                             increment=60, textvariable=self.pause_var_trail_coords)
        self.pause_trail_entry.grid(row=5, column=1, padx=10, pady=10)

        self.filename_label_trail = ttk.Label(self.trail_frame_lower_lbl, text="  Имя файла сеанса ",
                                              font=self.font_txt, foreground='grey', justify="right", anchor="e")
        self.filename_label_trail.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.filename_entry_trail = ttk.Entry(self.trail_frame_lower_lbl, width=45)
        self.filename_entry_trail.insert(0, "GetTrails")
        self.filename_entry_trail.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        self.folder_label_trail = ttk.Label(self.trail_frame_lower_lbl, text="Файл будет создан в: Exports/trails/",
                                            font=self.font_txt_light, foreground='grey', justify="left", anchor="w")
        self.folder_label_trail.grid(row=4, column=1, columnspan=1, padx=5, pady=0)

        self.duration_frame_lbl = ttk.LabelFrame(self.stamp_tab, text="Увеличить длительность")
        self.duration_frame_lbl.grid(row=0, column=1, columnspan=2, sticky="n")

        self.duration_checkbox = ttk.Checkbutton(self.duration_frame_lbl, text="Активно", style='Switch.TCheckbutton')
        self.duration_checkbox.grid(row=0, column=0, padx=10, pady=10)

        self.iterations_label = ttk.Label(self.duration_frame_lbl, text="Количество итераций", font=self.font_txt,
                                          foreground='grey')
        self.iterations_label.grid(row=1, column=0, padx=10, pady=10)

        self.iterations_entry = ttk.Spinbox(self.duration_frame_lbl, width=20, state='disabled', from_=2.0,
                                            to=99999999.0, increment=1)
        self.iterations_entry.grid(row=1, column=1, padx=10, pady=10)

        self.pause_label = ttk.Label(self.duration_frame_lbl, text="Пауза (сек)", font=self.font_txt, foreground='grey')
        self.pause_label.grid(row=2, column=0, padx=10, pady=10)

        self.pause_entry = ttk.Spinbox(self.duration_frame_lbl, width=20, state='disabled', from_=0.0, to=99999999.0,
                                       increment=60)
        self.pause_entry.grid(row=2, column=1, padx=10, pady=10)

        def toggle_entries():
            if self.duration_checkbox.instate(['selected']):
                self.iterations_entry.config(state='normal', textvariable=self.iterations_var_trail)
                self.pause_entry.config(state='normal', textvariable=self.pause_var_trail)
                self.iterations_var_trail.set(str(2))
                self.pause_var_trail.set(str(60))
                calculate_duration()
            else:
                self.iterations_entry.delete(0, 'end')
                self.pause_entry.delete(0, 'end')
                self.iterations_entry.config(state='disabled')
                self.pause_entry.config(state='disabled')
                calculate_duration()

        self.duration_checkbox.config(command=toggle_entries)

        self.button_frame_lbl = ttk.Frame(self.stamp_tab)
        self.button_frame_lbl.grid(row=1, column=1, rowspan=3, columnspan=2, sticky="nsew")

        self.start_button = ttk.Button(self.button_frame_lbl, text="Снять данные",
                                       command=lambda: Main.Functions.launch_trail_getter(self.trails_treeview,
                                                                                          self.filename_entry_trail,
                                                                                          self.iterations_entry,
                                                                                          self.pause_entry,
                                                                                          self.pause_trail_entry,
                                                                                          self.file_info_label_trail),
                                       style='Accent.TButton')
        self.start_button.grid(row=0, column=0, padx=130, pady=10, columnspan=2, sticky="ew")

        self.open_folder_button = ttk.Button(self.button_frame_lbl, text=" Открыть папку ",
                                             command=lambda: Main.Functions.open_folder("trails"))
        self.open_folder_button.grid(row=3, column=0, padx=130, pady=20, sticky="ew")

        self.stamp_info_button = ttk.Button(self.button_frame_lbl, text="⍰",
                                            command=lambda: Main.Functions.show_info(self, self.help_trails),
                                            style='Toolbutton')
        self.stamp_info_button.grid(row=4, column=0, padx=130, pady=10, sticky="ew")

        self.duration_time_label = ttk.Label(self.button_frame_lbl, text="Времени займёт ≈", font=self.font_txt,
                                             foreground='grey')
        self.duration_time_label.grid(row=1, column=0, padx=130, pady=0, sticky="ew")

        self.duration_time_value_label = ttk.Label(self.button_frame_lbl, text="", font=self.font_txt,
                                                   foreground='grey')
        self.duration_time_value_label.grid(row=2, column=0, padx=130, pady=0, sticky="ew")

        def calculate_duration():
            def format_time(all_time):
                hours = all_time // 3600
                minutes = (all_time % 3600) // 60
                seconds = all_time % 60
                return f"{hours} ч {minutes} мин {seconds} сек"

            try:
                iterations = int(self.iterations_entry.get())
                pause = int(self.pause_entry.get())
                pause_trail = int(self.pause_trail_entry.get())
                points_count = max(0, len(self.trails_treeview.get_children()) - 1)

                total_time = (iterations * pause) - pause
                total_time += points_count * pause_trail * iterations
                self.duration_time_value_label.config(text=format_time(total_time))
            except ValueError:
                try:
                    points_count = max(0, len(self.trails_treeview.get_children()) - 1)
                    pause_trail = int(self.pause_trail_entry.get())

                    total_time = points_count * pause_trail
                    self.duration_time_value_label.config(text=format_time(total_time))
                except ValueError:
                    self.duration_time_value_label.config(text=f"{0} ч {0} мин {0} сек")

        self.iterations_entry.config(command=calculate_duration)
        self.iterations_entry.bind('<KeyRelease>', lambda event: calculate_duration())

        self.pause_entry.config(command=calculate_duration)
        self.pause_entry.bind('<KeyRelease>', lambda event: calculate_duration())

        self.pause_trail_entry.config(command=calculate_duration)
        self.pause_trail_entry.bind('<KeyRelease>', lambda event: calculate_duration())

        self.trails_treeview.bind('<ButtonRelease>', lambda event: calculate_duration())

        self.duration_checkbox.config(command=toggle_entries)

        self.trails_result_frame = ttk.Frame(self.stamp_tab)
        self.trails_result_frame.grid(row=9, column=0, rowspan=3, columnspan=3, sticky="nsew")

        self.file_info_label_trail = ttk.Label(self.trails_result_frame, text="", font=self.font_txt, foreground='grey')
        self.file_info_label_trail.grid(row=0, column=0, columnspan=3, padx=10, pady=0, sticky="nsew")

        # ВКЛАДКА excel
        self.file_label = ttk.Label(self.excel_tab, text="Выберите файл:", font=self.font_txt, foreground='grey',
                                    justify="right", anchor="e")
        self.file_label.grid(row=0, column=0, padx=10, pady=10)

        self.file_entry = ttk.Entry(self.excel_tab, width=60)
        self.file_entry.grid(row=0, column=1, padx=10, pady=10)

        self.file_button = ttk.Button(self.excel_tab, text="Поиск",
                                      command=lambda: Main.Functions.find_file(self.file_entry,
                                                                               "Выбор файла для конвертации"))
        self.file_button.grid(row=0, column=2, padx=10, pady=10)

        self.convert_button = ttk.Button(self.excel_tab, text=" Преобразовать ", compound='left',
                                         command=lambda: Main.Functions.start_programm(
                                             'Main.FlowTransformations.DataToExcel', 'convert_json_excel',
                                             self.file_entry.get()), style='Accent.TButton')
        self.convert_button.grid(row=1, column=1, padx=10, pady=10)

        self.open_folder_button_excel = ttk.Button(self.excel_tab, text="Открыть папку", compound='left',
                                                   command=lambda: Main.Functions.open_folder("excelExports"))
        self.open_folder_button_excel.grid(row=2, column=1, padx=10, pady=10)

        self.excel_info_button = ttk.Button(self.excel_tab, text="⍰",
                                            command=lambda: Main.Functions.show_info(self, self.help_excel),
                                            style='Toolbutton')
        self.excel_info_button.grid(row=0, column=3, padx=5, pady=5)

        # Вкладка "Разделение JSON"
        self.file_label_divide = ttk.Label(self.divide_json_tab, text="Выберите файл:", font=self.font_txt,
                                           foreground='grey', justify="right", anchor="e")
        self.file_label_divide.grid(row=0, column=0, padx=10, pady=10)

        self.file_entry_divide = ttk.Entry(self.divide_json_tab, width=60)
        self.file_entry_divide.grid(row=0, column=1, padx=10, pady=10)

        self.file_button_divide = ttk.Button(self.divide_json_tab, text="Поиск",
                                             command=lambda: Main.Functions.find_file(self.file_entry_divide,
                                                                                      "Выбор JSON файла для порейсового извлечения новых JSON"))
        self.file_button_divide.grid(row=0, column=2, padx=10, pady=10)

        self.divide_button = ttk.Button(self.divide_json_tab, text=" Разделить JSON ", compound='left',
                                        command=lambda: divide_json_file(self.file_entry_divide.get()),
                                        style='Accent.TButton')
        self.divide_button.grid(row=1, column=1, padx=10, pady=10)

        self.open_folder_button_divide = ttk.Button(self.divide_json_tab, text="Открыть папку", compound='left',
                                                    command=lambda: Main.Functions.open_folder("jsonDivide"))
        self.open_folder_button_divide.grid(row=2, column=1, padx=10, pady=10)

        self.divide_info_button = ttk.Button(self.divide_json_tab, text="⍰",
                                             command=lambda: Main.Functions.show_info(self, self.help_jsonDivide),
                                             style='Toolbutton')
        self.divide_info_button.grid(row=0, column=3, padx=5, pady=5)

        # ВКЛАДКА "объединение Json"
        self.file_label_merger = ttk.Label(self.json_merger_tab, text="Выберите файл(ы):", font=self.font_txt,
                                           foreground='grey', justify="right", anchor="e")
        self.file_label_merger.grid(row=0, column=0, padx=10, pady=10)

        self.file_entry_merger = ttk.Entry(self.json_merger_tab, width=60)
        self.file_entry_merger.grid(row=0, column=1, padx=10, pady=10)

        self.file_button_merger = ttk.Button(self.json_merger_tab, text="Поиск",
                                             command=lambda: Main.FlowTransformations.MergerJson.find_json_files(self))
        self.file_button_merger.grid(row=0, column=2, padx=10, pady=10)

        self.merger_button = ttk.Button(self.json_merger_tab, text="Создать JSON", compound='left',
                                        command=lambda: Main.FlowTransformations.MergerJson.merge_json_files(self),
                                        style='Accent.TButton')
        self.merger_button.grid(row=0, column=3, padx=10, pady=10)

        self.open_folder_button_merger = ttk.Button(self.json_merger_tab, text="Открыть папку", compound='left',
                                                    command=lambda: Main.Functions.open_folder("jsonMerge"))
        self.open_folder_button_merger.grid(row=0, column=4, padx=10, pady=10)

        self.merger_info_button = ttk.Button(self.json_merger_tab, text="⍰",
                                             command=lambda: Main.Functions.show_info(self, self.help_jsonMerge),
                                             style='Toolbutton')
        self.merger_info_button.grid(row=0, column=5, padx=5, pady=5)

        self.file_label_merger = ttk.Label(self.json_merger_tab, text="Введите название:", font=self.font_txt,
                                           foreground='grey', justify="right", anchor="e")
        self.file_label_merger.grid(row=1, column=0, padx=10, pady=10)

        self.output_file_entry = ttk.Entry(self.json_merger_tab, width=60, textvariable=self.merged_name_var)
        self.output_file_entry.grid(row=1, column=1, padx=0, pady=10)

        self.listbox_frame = ttk.LabelFrame(self.json_merger_tab, text="Редактирование потока")
        self.listbox_frame.grid(row=3, column=0, columnspan=6, padx=10, pady=10)

        self.stats_frame = ttk.LabelFrame(self.listbox_frame)
        self.stats_frame.grid(row=2, column=0, columnspan=3, sticky="ew")

        self.stats_label = ttk.Label(self.stats_frame, font=self.font_txt)
        self.stats_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5)

        self.treeview = ttk.Treeview(self.listbox_frame, columns=(
            "id", "callsign", "flight_time", "route_points", "airport_origin", "airport_destination"))
        self.treeview.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        self.xscrollbar = ttk.Scrollbar(self.listbox_frame, orient="horizontal", command=self.treeview.xview)
        self.xscrollbar.grid(row=1, column=0, sticky="ew")

        self.yscrollbar = ttk.Scrollbar(self.listbox_frame, orient="vertical", command=self.treeview.yview)
        self.yscrollbar.grid(row=0, column=1, sticky="ns")

        self.treeview.config(xscrollcommand=self.xscrollbar.set, yscrollcommand=self.yscrollbar.set)

        self.treeview.heading("#0", text="Путь к файлу")
        self.treeview.heading("id", text="ID")
        self.treeview.heading("callsign", text="Номер рейса")
        self.treeview.heading("flight_time", text="Время полёта")
        self.treeview.heading("route_points", text="Точек маршрута")
        self.treeview.heading("airport_origin", text="Аэропорт вылета")
        self.treeview.heading("airport_destination", text="Аэропорт прилёта")

        self.treeview.column("#0", width=250)
        self.treeview.column("id", width=100)
        self.treeview.column("callsign", width=100)
        self.treeview.column("flight_time", width=100)
        self.treeview.column("route_points", width=100)
        self.treeview.column("airport_origin", width=100)
        self.treeview.column("airport_destination", width=120)

        self.delete_button = ttk.Button(self.listbox_frame, text="Удалить",
                                        command=lambda: Main.FlowTransformations.MergerJson.delete_selected_items(self))
        self.delete_button.grid(row=0, column=2, sticky="nsew", padx=20, pady=20)

        self.listbox_frame.rowconfigure(0, weight=1)
        self.listbox_frame.columnconfigure(0, weight=1)

        self.treeview.heading("#0", text="File Path",
                              command=lambda: Main.Functions.sort_by_column(self, self.treeview, "#0", 0))
        self.treeview.heading("id", text="ID",
                              command=lambda: Main.Functions.sort_by_column(self, self.treeview, "id", 0))
        self.treeview.heading("callsign", text="Callsign",
                              command=lambda: Main.Functions.sort_by_column(self, self.treeview, "callsign", 0))
        self.treeview.heading("flight_time", text="Flight Time",
                              command=lambda: Main.Functions.sort_by_column(self, self.treeview, "flight_time", 0))
        self.treeview.heading("route_points", text="Route Points",
                              command=lambda: Main.Functions.sort_by_column(self, self.treeview, "route_points", 0))
        self.treeview.heading("airport_origin", text="Airport Origin",
                              command=lambda: Main.Functions.sort_by_column(self, self.treeview, "airport_origin", 0))
        self.treeview.heading("airport_destination", text="Airport Destination",
                              command=lambda: Main.Functions.sort_by_column(self, self.treeview, "airport_destination",
                                                                            0))

        self.merger_result_frame = ttk.Frame(self.json_merger_tab)
        self.merger_result_frame.grid(row=4, column=0, rowspan=3, columnspan=3, sticky="nsew")

        self.file_info_label_merger = ttk.Label(self.merger_result_frame, text="", font=self.font_txt,
                                                foreground='grey')
        self.file_info_label_merger.grid(row=0, column=0, columnspan=3, padx=10, pady=0, sticky="nsew")

        # ВКЛАДКА drawer2D
        self.file_label2D = ttk.Label(self.drawer2D_tab, text="Выберите файл:", font=self.font_txt, foreground='grey',
                                      justify="right", anchor="e")
        self.file_label2D.grid(row=0, column=0, padx=10, pady=10)

        self.file_entry2D = ttk.Entry(self.drawer2D_tab, width=60)
        self.file_entry2D.grid(row=0, column=1, padx=10, pady=10)

        self.file_button2D = ttk.Button(self.drawer2D_tab, text="Поиск",
                                        command=lambda: Main.Functions.find_file(self.file_entry2D,
                                                                                 "Выбор файла для отрисовки треков на плоскости"))
        self.file_button2D.grid(row=0, column=2, padx=10, pady=10)

        self.drawer2d_button = ttk.Button(self.drawer2D_tab, text=" Отрисовать треки в 2D ", compound='left',
                                          command=lambda: Main.Functions.start_programm(
                                              'Main.FlowVisualization.RoutesDrawer', 'RoutesDrawer2D',
                                              self.file_entry2D.get()), style='Accent.TButton')
        self.drawer2d_button.grid(row=1, column=1, padx=10, pady=10)

        self.open_folder_button2D = ttk.Button(self.drawer2D_tab, text="Открыть папку", compound='left',
                                               command=lambda: Main.Functions.open_folder("drawRoutes2D"))
        self.open_folder_button2D.grid(row=2, column=1, padx=10, pady=10)

        self.drawer2D_info_button = ttk.Button(self.drawer2D_tab, text="⍰",
                                               command=lambda: Main.Functions.show_info(self, self.help_draw2D),
                                               style='Toolbutton')
        self.drawer2D_info_button.grid(row=0, column=3, padx=5, pady=5)

        # ВКЛАДКА drawerVertical
        self.file_labelVertical = ttk.Label(self.drawerVertical_tab, text="Выберите файл:", font=self.font_txt,
                                            foreground='grey', justify="right", anchor="e")
        self.file_labelVertical.grid(row=0, column=0, padx=10, pady=10)

        self.file_entryVertical = ttk.Entry(self.drawerVertical_tab, width=60)
        self.file_entryVertical.grid(row=0, column=1, padx=10, pady=10)

        self.file_buttonVertical = ttk.Button(self.drawerVertical_tab, text="Поиск",
                                              command=lambda: Main.Functions.find_file(self.file_entryVertical,
                                                                                       "Выбор файла для отрисовки вертикальных профилей треков"))
        self.file_buttonVertical.grid(row=0, column=2, padx=10, pady=10)

        self.drawerVertical_button = ttk.Button(self.drawerVertical_tab, text=" Отрисовать вертикальные профили",
                                                compound='left', command=lambda: Main.Functions.start_programm(
                'Main.FlowVisualization.VerticalProfileDrawer', 'vertical_routes_drawer',
                self.file_entryVertical.get()), style='Accent.TButton')
        self.drawerVertical_button.grid(row=1, column=1, padx=10, pady=10)

        self.open_folder_buttonVertical = ttk.Button(self.drawerVertical_tab, text="Открыть папку", compound='left',
                                                     command=lambda: Main.Functions.open_folder("drawVerticalProfiles"))
        self.open_folder_buttonVertical.grid(row=2, column=1, padx=10, pady=10)

        self.drawerVertical_info_button = ttk.Button(self.drawerVertical_tab, text="⍰",
                                                     command=lambda: Main.Functions.show_info(self, self.help_drawVert),
                                                     style='Toolbutton')
        self.drawerVertical_info_button.grid(row=0, column=3, padx=5, pady=5)

        # ВКЛАДКА drawer3D
        self.file_label3D = ttk.Label(self.drawer3D_tab, text="Выберите файл:", font=self.font_txt, foreground='grey',
                                      justify="right", anchor="e")
        self.file_label3D.grid(row=0, column=0, padx=10, pady=10)

        self.file_entry3D = ttk.Entry(self.drawer3D_tab, width=60)
        self.file_entry3D.grid(row=0, column=1, padx=10, pady=10)

        self.file_button3D = ttk.Button(self.drawer3D_tab, text="Поиск",
                                        command=lambda: Main.Functions.find_file(self.file_entry3D,
                                                                                 "Выбор файла для отрисовки треков в пространственном графике"))
        self.file_button3D.grid(row=0, column=2, padx=10, pady=10)

        self.drawer3D_button = ttk.Button(self.drawer3D_tab, text=" Отрисовать треки в 3D ", compound='left',
                                          command=lambda: Main.Functions.start_programm(
                                              'Main.FlowVisualization.RoutesDrawer3D', 'routes_drawer_3D',
                                              self.file_entry3D.get()), style='Accent.TButton')
        self.drawer3D_button.grid(row=1, column=1, padx=10, pady=10)

        self.open_folder_button3D = ttk.Button(self.drawer3D_tab, text="Открыть папку", compound='left',
                                               command=lambda: Main.Functions.open_folder("drawRoutes3D"))
        self.open_folder_button3D.grid(row=2, column=1, padx=10, pady=10)

        self.drawer3D_info_button = ttk.Button(self.drawer3D_tab, text="⍰",
                                               command=lambda: Main.Functions.show_info(self, self.help_draw3D),
                                               style='Toolbutton')
        self.drawer3D_info_button.grid(row=0, column=3, padx=5, pady=5)

        # ВКЛАДКА MAP
        frame = ttk.Frame(self.map_tab)
        frame.pack(side="top", fill="x", pady=10)

        self.file_path_label = ttk.Label(frame, text="Выберите файл:", font=self.font_txt, foreground='grey',
                                         justify="right", anchor="e")
        self.file_path_label.pack(side="left", padx=15)

        self.file_path_entry = ttk.Entry(frame, width=60)
        self.file_path_entry.pack(side="left", padx=5)

        self.file_buttonMap = ttk.Button(frame, text="Поиск",
                                         command=lambda: Main.Functions.find_file(self.file_path_entry,
                                                                                  "Выбор файла для отрисовки треков на карте"))
        self.file_buttonMap.pack(side="left", padx=5)

        self.display_button = ttk.Button(frame, text="Отобразить",
                                         command=lambda: display_tracks(self, self.file_path_entry.get()),
                                         style='Accent.TButton')
        self.display_button.pack(side="left", padx=5)

        self.clear_button = ttk.Button(frame, text="Очистить",
                                       command=lambda: clear_map(self))
        self.clear_button.pack(side="left", padx=5)

        self.data_source_label = ttk.Label(frame, text="Изображение карты:", font=self.font_txt, foreground='grey',
                                           justify="right", anchor="e")
        self.data_source_label.pack(side="left", padx=15)

        self.data_source_var = tk.StringVar()
        self.data_source_var.set("OpenStreetMap")

        self.data_source_option = ttk.OptionMenu(frame, self.data_source_var, "OpenStreetMap", "OpenStreetMap",
                                                 "Google Maps", "Google спутник", "Google гибрид", "Google рельеф",
                                                 "Светлая", "Тёмная", "Схематичная", "Пустая",
                                                 command=lambda value: change_data_source(self, value))
        self.data_source_option.pack(side="left", padx=5)

        self.map_widget = tkintermapview.TkinterMapView(self.map_tab, width=700, height=500, corner_radius=15)
        self.map_widget.set_position(55.9739763, 37.4151879)
        self.map_widget.set_zoom(11)
        self.map_widget.pack(side="bottom", fill="both", expand=True)

        self.map_info_button = ttk.Button(frame, text="⍰",
                                          command=lambda: Main.Functions.show_info(self, self.help_drawMap),
                                          style='Toolbutton')
        self.map_info_button.pack(side="left", padx=5, pady=5)

        # график скорости
        self.speed_graph_frame = ttk.Frame(self.speed_graph_tab)
        self.speed_graph_frame.pack(fill="both", expand=True)

        self.file_label_speed_graph = ttk.Label(self.speed_graph_frame, text="Выберите файл:", font=self.font_txt,
                                                foreground='grey', justify="right", anchor="e")
        self.file_label_speed_graph.grid(row=0, column=0, padx=10, pady=10)

        self.file_entry_speed_graph = ttk.Entry(self.speed_graph_frame, width=60)
        self.file_entry_speed_graph.grid(row=0, column=1, padx=10, pady=10)

        self.file_button_speed_graph = ttk.Button(self.speed_graph_frame, text="Поиск",
                                                  command=lambda: Main.Functions.find_file(self.file_entry_speed_graph,
                                                                                           "Выбор JSON файла для рисовки графика скорости"))
        self.file_button_speed_graph.grid(row=0, column=2, padx=10, pady=10)

        self.draw_button_speed_graph = ttk.Button(self.speed_graph_frame, text=" Отрисовать график скорости ",
                                                  command=lambda: Main.Functions.start_programm(
                                                      'Main.FlowVisualization.SpeedDrawer', 'draw_speed_graph',
                                                      self.file_entry_speed_graph.get(), self.speed_type_var),
                                                  style='Accent.TButton')
        self.draw_button_speed_graph.grid(row=3, column=1, padx=10, pady=10)

        self.open_folder_button_speed_graph = ttk.Button(self.speed_graph_frame, text="Открыть папку",
                                                         command=lambda: Main.Functions.open_folder("drawSpeed"))
        self.open_folder_button_speed_graph.grid(row=4, column=1, padx=10, pady=10)

        self.speed_graph_info_button = ttk.Button(self.speed_graph_frame, text="⍰",
                                                  command=lambda: Main.Functions.show_info(self, self.help_drawSpeed),
                                                  style='Toolbutton')
        self.speed_graph_info_button.grid(row=0, column=3, padx=5, pady=5)

        self.speed_type_var = tk.StringVar()
        self.speed_type_var.set("groundSpeed_Kts")

        self.speed_type_label = ttk.Label(self.speed_graph_frame, text="Тип скорости:", font=self.font_txt,
                                          foreground='grey', justify="right", anchor="e")
        self.speed_type_label.grid(row=1, column=0, padx=10, pady=10)

        self.speed_type_option = ttk.OptionMenu(self.speed_graph_frame, self.speed_type_var, "groundSpeed_Kts",
                                                "groundSpeed_Kts", "verticalSpeed")
        self.speed_type_option.grid(row=1, column=1, padx=10, pady=10)

        # экспорт для ATFM
        self.export_to_atfm_frame = ttk.Frame(self.export_to_atfm_tab)
        self.export_to_atfm_frame.pack(fill="both", expand=True)

        self.file_label_atfm = ttk.Label(self.export_to_atfm_frame, text="Выберите файл:", font=self.font_txt,
                                         foreground='grey', justify="right", anchor="e")
        self.file_label_atfm.grid(row=0, column=0, padx=10, pady=10)

        self.file_entry_atfm = ttk.Entry(self.export_to_atfm_frame, width=60)
        self.file_entry_atfm.grid(row=0, column=1, padx=10, pady=10)

        self.file_button_atfm = ttk.Button(self.export_to_atfm_frame, text="Поиск",
                                           command=lambda: Main.Functions.find_file(self.file_entry_atfm,
                                                                                    "Выбор JSON файла для преобразования и импорта в ATFM"))
        self.file_button_atfm.grid(row=0, column=2, padx=10, pady=10)

        self.convert_button_atfm = ttk.Button(self.export_to_atfm_frame, text=" Экспорт в JSON для ATFM-model ",
                                              style='Accent.TButton',
                                              command=lambda: convert_json_atfm(self, self.file_entry_atfm.get(),
                                                                                self.catalog_id_entry.get(),
                                                                                self.commentary_entry.get(),
                                                                                self.name_entry.get(),
                                                                                self.user_id_entry.get(),
                                                                                self.number_entry.get()))
        self.convert_button_atfm.grid(row=0, column=3, padx=10, pady=10)

        self.open_folder_button_atfm = ttk.Button(self.export_to_atfm_frame, text="Открыть папку",
                                                  command=lambda: Main.Functions.open_folder("jsonATFM"))
        self.open_folder_button_atfm.grid(row=0, column=4, padx=10, pady=10)

        self.atfm_info_button = ttk.Button(self.export_to_atfm_frame, text="⍰",
                                           command=lambda: Main.Functions.show_info(self, self.help_atfm),
                                           style='Toolbutton')
        self.atfm_info_button.grid(row=0, column=5, padx=5, pady=5)

        self.settings_label_frame = ttk.LabelFrame(self.export_to_atfm_frame, text="Настройки")
        self.settings_label_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

        self.name_label = ttk.Label(self.settings_label_frame, text="Название ", font=self.font_txt, foreground='grey',
                                    justify="right", anchor="e")
        self.name_label.grid(row=0, column=0, padx=10, pady=10)

        self.name_entry = ttk.Entry(self.settings_label_frame, width=55, textvariable=self.atfm_name_var)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)

        self.commentary_label = ttk.Label(self.settings_label_frame, text="Комментарий ", font=self.font_txt,
                                          foreground='grey', justify="right", anchor="e")
        self.commentary_label.grid(row=1, column=0, padx=10, pady=10)

        self.commentary_entry = ttk.Entry(self.settings_label_frame, width=55, textvariable=self.atfm_comment_var)
        self.commentary_entry.grid(row=1, column=1, padx=10, pady=10)

        self.catalog_id_label = ttk.Label(self.settings_label_frame, text="ID каталога ", font=self.font_txt,
                                          foreground='grey', justify="right", anchor="e")
        self.catalog_id_label.grid(row=2, column=0, padx=10, pady=10)

        self.catalog_id_entry = ttk.Entry(self.settings_label_frame, width=55, textvariable=self.atfm_catalog_var)
        self.catalog_id_entry.grid(row=2, column=1, padx=10, pady=10)

        self.user_id_label = ttk.Label(self.settings_label_frame, text="ID пользователя ", font=self.font_txt,
                                       foreground='grey', justify="right", anchor="e")
        self.user_id_label.grid(row=3, column=0, padx=10, pady=10)

        self.user_id_entry = ttk.Entry(self.settings_label_frame, width=55, textvariable=self.atfm_user_var)
        self.user_id_entry.grid(row=3, column=1, padx=10, pady=10)

        self.number_label = ttk.Label(self.settings_label_frame, text="Номер ", font=self.font_txt, foreground='grey',
                                      justify="right", anchor="e")
        self.number_label.grid(row=4, column=0, padx=10, pady=10)

        self.number_entry = ttk.Entry(self.settings_label_frame, width=55, textvariable=self.atfm_number_var)
        self.number_entry.grid(row=4, column=1, padx=10, pady=10)

        self.russia_code_label_atfm = ttk.Label(self.settings_label_frame, text="Russia code: 'RR'", font=self.font_txt,
                                                foreground='grey', justify="right", anchor="e")
        self.russia_code_label_atfm.grid(row=5, column=0, padx=10, pady=10)

        self.russia_code_var_atfm = tk.IntVar()
        self.russia_code_var_atfm_checkbox = ttk.Checkbutton(self.settings_label_frame,
                                                             variable=self.russia_code_var_atfm,
                                                             style='Switch.TCheckbutton')
        self.russia_code_var_atfm_checkbox.grid(row=5, column=1, padx=10, pady=10, sticky="w")

        # вкладка Экспорт в csv для КИМ

        def filename_show(filename):
            return os.path.basename(filename).split('.')[0]

        def update_filename_on_button_click(self):
            filename = self.file_entry_kim.get()
            if filename:
                self.filename_entry_kim.config(state="normal")
                self.filename_entry_kim.delete(0, tk.END)
                self.filename_entry_kim.insert(0, filename_show(filename))
                self.filename_entry_kim.config(state="readonly")
            else:
                self.filename_entry_kim.config(state="normal")
                self.filename_entry_kim.insert(-1, ' ')
                self.filename_entry_kim.config(state="readonly")

        self.export_to_kim_frame = ttk.Frame(self.export_to_kim_csv_tab)
        self.export_to_kim_frame.pack(fill="both", expand=True)

        self.file_label_kim = ttk.Label(self.export_to_kim_frame, text="Выберите файл:", font=self.font_txt,
                                        foreground='grey', justify="right", anchor="e")
        self.file_label_kim.grid(row=0, column=0, padx=10, pady=10)

        self.file_entry_kim = ttk.Entry(self.export_to_kim_frame, width=60)
        self.file_entry_kim.grid(row=0, column=1, padx=10, pady=10)

        self.file_button_kim = ttk.Button(self.export_to_kim_frame, text="Поиск", command=lambda: [
            Main.Functions.find_file(self.file_entry_kim, "Выбор JSON файла для преобразования и импорта в ATFM"),
            update_filename_on_button_click(self)])
        self.file_button_kim.grid(row=0, column=2, padx=10, pady=10)

        self.convert_button_kim = ttk.Button(self.export_to_kim_frame, text=" Экспорт в CSV для КИМ ",
                                             style='Accent.TButton',
                                             command=lambda: convert_csv_kim(self, self.file_entry_kim.get(),
                                                                             self.catalog_id_entry_kim.get(),
                                                                             self.commentary_entry_kim.get(),
                                                                             self.name_entry_kim.get(),
                                                                             self.variant_id_entry_kim.get()))
        self.convert_button_kim.grid(row=0, column=3, padx=10, pady=10)

        self.open_folder_button_kim = ttk.Button(self.export_to_kim_frame, text="Открыть папку",
                                                 command=lambda: Main.Functions.open_folder("csvKIM"))
        self.open_folder_button_kim.grid(row=0, column=4, padx=10, pady=10)

        self.kim_info_button = ttk.Button(self.export_to_kim_frame, text="⍰",
                                          command=lambda: Main.Functions.show_info(self, self.help_kim),
                                          style='Toolbutton')
        self.kim_info_button.grid(row=0, column=5, padx=5, pady=5)

        self.settings_label_frame_kim = ttk.LabelFrame(self.export_to_kim_frame, text="Настройки")
        self.settings_label_frame_kim.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

        self.filename_label_kim = ttk.Label(self.settings_label_frame_kim, text="Название файла", font=self.font_txt,
                                            foreground='grey', justify="right", anchor="e")
        self.filename_label_kim.grid(row=0, column=0, padx=10, pady=10)

        self.filename_entry_kim = ttk.Entry(self.settings_label_frame_kim,
                                            width=55)  # os.path.splitext(self.file_entry_kim)[0])
        self.filename_entry_kim.grid(row=0, column=1, padx=10, pady=10)
        self.filename_entry_kim.config(state="readonly")

        self.name_label_kim = ttk.Label(self.settings_label_frame_kim, text="Название потока", font=self.font_txt,
                                        foreground='grey', justify="right", anchor="e")
        self.name_label_kim.grid(row=1, column=0, padx=10, pady=10)

        self.name_entry_kim = ttk.Entry(self.settings_label_frame_kim, width=55, textvariable=self.kim_name_var)
        self.name_entry_kim.grid(row=1, column=1, padx=10, pady=10)

        self.commentary_label_kim = ttk.Label(self.settings_label_frame_kim, text="Комментарий ", font=self.font_txt,
                                              foreground='grey', justify="right", anchor="e")
        self.commentary_label_kim.grid(row=2, column=0, padx=10, pady=10)

        self.commentary_entry_kim = ttk.Entry(self.settings_label_frame_kim, width=55,
                                              textvariable=self.atfm_comment_var)
        self.commentary_entry_kim.grid(row=2, column=1, padx=10, pady=10)

        self.catalog_id_label_kim = ttk.Label(self.settings_label_frame_kim, text="ID каталога ", font=self.font_txt,
                                              foreground='grey', justify="right", anchor="e")
        self.catalog_id_label_kim.grid(row=3, column=0, padx=10, pady=10)

        self.catalog_id_entry_kim = ttk.Entry(self.settings_label_frame_kim, width=55,
                                              textvariable=self.atfm_catalog_var)
        self.catalog_id_entry_kim.grid(row=3, column=1, padx=10, pady=10)

        self.variant_id_label_kim = ttk.Label(self.settings_label_frame_kim, text="№ варианта ", font=self.font_txt,
                                              foreground='grey', justify="right", anchor="e")
        self.variant_id_label_kim.grid(row=4, column=0, padx=10, pady=10)

        self.variant_id_entry_kim = ttk.Entry(self.settings_label_frame_kim, width=55, textvariable=self.atfm_user_var)
        self.variant_id_entry_kim.grid(row=4, column=1, padx=10, pady=10)

        self.russia_code_label_kim = ttk.Label(self.settings_label_frame_kim, text="Russia code: 'RR'",
                                               font=self.font_txt, foreground='grey', justify="right", anchor="e")
        self.russia_code_label_kim.grid(row=5, column=0, padx=10, pady=10)

        self.russia_code_var = tk.IntVar()
        self.russia_code_var_checkbox = ttk.Checkbutton(self.settings_label_frame_kim, variable=self.russia_code_var,
                                                        style='Switch.TCheckbutton')
        self.russia_code_var_checkbox.grid(row=5, column=1, padx=10, pady=10, sticky="w")

        # Вкладка "Информация о потоке"
        self.flow_info_frame = ttk.Frame(self.flow_info_tab)
        self.flow_info_frame.pack(fill="both", expand=True)

        self.flow_info_frame_btns = ttk.Frame(self.flow_info_frame)
        self.flow_info_frame_btns.grid(row=0, column=0, rowspan=2, columnspan=3, sticky="nsew")
        # self.flow_info_frame_btns.pack(side="top", fill="both", expand=True)

        self.file_label_flow_info = ttk.Label(self.flow_info_frame_btns, text="Выберите файл:", font=self.font_txt,
                                              foreground='grey', justify="right", anchor="e")
        self.file_label_flow_info.grid(row=0, column=0, padx=10, pady=10)

        self.file_entry_flow_info = ttk.Entry(self.flow_info_frame_btns, width=60)
        self.file_entry_flow_info.grid(row=0, column=1, padx=10, pady=10)

        self.file_button_flow_info = ttk.Button(self.flow_info_frame_btns, text="Поиск",
                                                command=lambda: Main.Functions.find_file(self.file_entry_flow_info,
                                                                                         "Выбор JSON файла для отображения информации"))
        self.file_button_flow_info.grid(row=0, column=2, padx=10, pady=10)

        self.display_button_flow_info = ttk.Button(self.flow_info_frame_btns, text="Отобразить информацию",
                                                   command=lambda: Main.FlowVisualization.FlowInfo.display_flow_info(
                                                       self.file_entry_flow_info.get(),
                                                       self.flow_info_label,
                                                       None),
                                                   style='Accent.TButton')
        self.display_button_flow_info.grid(row=1, column=1, padx=10, pady=10)

        self.flow_info_info_button = ttk.Button(self.flow_info_frame_btns, text="⍰",
                                                command=lambda: Main.Functions.show_info(self, self.help_flowInfo),
                                                style='Toolbutton')
        self.flow_info_info_button.grid(row=0, column=3, padx=5, pady=5)

        self.flow_info_frame_result = ttk.Frame(self.flow_info_frame)
        self.flow_info_frame_result.grid(row=2, column=0, rowspan=4, columnspan=4, sticky="nsew")

        self.flow_info_label = ttk.Label(self.flow_info_frame_result, text="", font=self.font_txt, foreground='grey',
                                         justify="left", anchor="w")
        self.flow_info_label.grid(row=0, column=0, columnspan=3, rowspan=3, padx=10, pady=10)

        self.style = ttk.Style()
        self.style.configure('MyFrame.TFrame', background='black')

        # Вкладка "Авто-фильтрация потока"
        self.auto_filter_frame = ttk.Frame(self.auto_filter_tab)
        self.auto_filter_frame.pack(fill="both", expand=True)

        self.file_label_auto_filter = ttk.Label(self.auto_filter_frame, text="Выберите файл:", font=self.font_txt,
                                                foreground='grey', justify="right", anchor="e")
        self.file_label_auto_filter.grid(row=0, column=0, padx=10, pady=10)

        self.file_button_auto_filter = ttk.Button(self.auto_filter_frame, text="Поиск",
                                                  command=lambda: Main.Functions.find_file(self.file_entry_auto_filter,
                                                                                           "Выбор JSON файла для авто-фильтрации потока"))
        self.file_button_auto_filter.grid(row=0, column=2, padx=10, pady=10)

        self.filter_button = ttk.Button(self.auto_filter_frame, text="Фильтровать поток",
                                        command=lambda: Main.FlowTransformations.AutoFlowFilter.filter_flow(self,
                                                                                                            self.file_entry_auto_filter.get(),
                                                                                                            self.filtered_info_label),
                                        style='Accent.TButton')
        self.filter_button.grid(row=0, column=3, padx=10, pady=10)

        self.open_folder_button_filter = ttk.Button(self.auto_filter_frame, text="Открыть папку",
                                                    command=lambda: Main.Functions.open_folder("flowFiltered"))
        self.open_folder_button_filter.grid(row=0, column=4, padx=10, pady=10)

        self.auto_filter_info_button = ttk.Button(self.auto_filter_frame, text="⍰",
                                                  command=lambda: Main.Functions.show_info(self, self.help_flowFilter),
                                                  style='Toolbutton')
        self.auto_filter_info_button.grid(row=0, column=5, padx=5, pady=5)

        self.file_entry_auto_filter = ttk.Entry(self.auto_filter_frame, width=60)
        self.file_entry_auto_filter.grid(row=0, column=1, padx=10, pady=10)

        self.filter_frame = ttk.LabelFrame(self.auto_filter_frame, text="Фильтры")
        self.filter_frame.grid(row=1, column=0, columnspan=5, padx=10, pady=10)

        self.results_filter_frame = ttk.Frame(self.auto_filter_frame)
        self.results_filter_frame.grid(row=7, column=0, columnspan=5, padx=10, pady=10)

        self.filtered_info_label = ttk.Label(self.results_filter_frame, text="", font=self.font_txt, foreground='grey',
                                             justify="left", anchor="w")
        self.filtered_info_label.grid(row=0, column=0, columnspan=5, padx=10, pady=0)

        # столбик 1
        self.min_points_var = tk.IntVar()
        self.min_points_checkbox = ttk.Checkbutton(self.filter_frame, text="Точек маршрута не менее:",
                                                   variable=self.min_points_var,
                                                   command=lambda: Main.FlowTransformations.AutoFlowFilter.update_min_points_entry(
                                                       self, self.min_points_var, self.min_points_entry),
                                                   style='Switch.TCheckbutton')
        self.min_points_checkbox.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.min_points_entry = ttk.Entry(self.filter_frame, width=10, state='disabled')
        self.min_points_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.min_distance_var = tk.IntVar()
        self.min_distance_checkbox = ttk.Checkbutton(self.filter_frame,
                                                     text="Километров м-ду точками маршрута не более:",
                                                     variable=self.min_distance_var,
                                                     command=lambda: Main.FlowTransformations.AutoFlowFilter.update_min_distance_entry(
                                                         self, self.min_distance_var, self.min_distance_entry),
                                                     style='Switch.TCheckbutton')
        self.min_distance_checkbox.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.min_distance_entry = ttk.Entry(self.filter_frame, width=10, state='disabled')
        self.min_distance_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.flight_time_var = tk.IntVar()
        self.flight_time_checkbox = ttk.Checkbutton(self.filter_frame, text="Время полёта (мин) не менее:",
                                                    variable=self.flight_time_var,
                                                    command=lambda: Main.FlowTransformations.AutoFlowFilter.update_flight_time_entry(
                                                        self, self.flight_time_var, self.flight_time_entry),
                                                    style='Switch.TCheckbutton')
        self.flight_time_checkbox.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.flight_time_entry = ttk.Entry(self.filter_frame, width=10, state='disabled')
        self.flight_time_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        self.airport_origin_var_named = tk.StringVar()
        self.airport_origin_checkbox_var = tk.IntVar()
        self.airport_origin_checkbox_named = ttk.Checkbutton(self.filter_frame, text="Аэропорт вылета:",
                                                             variable=self.airport_origin_checkbox_var,
                                                             command=lambda: Main.FlowTransformations.AutoFlowFilter.update_airport_origin_checkbox(
                                                                 self, self.airport_origin_checkbox_var,
                                                                 self.airport_origin_entry,
                                                                 self.airport_origin_checkbox),
                                                             style='Switch.TCheckbutton')
        self.airport_origin_checkbox_named.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.airport_origin_entry = ttk.Entry(self.filter_frame, width=10, state='disabled')
        self.airport_origin_entry.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        self.airport_origin_button = ttk.Button(self.filter_frame, text="Аэропорт вылета:")

        self.airport_destination_var_named = tk.StringVar()
        self.airport_destination_checkbox_var = tk.IntVar()
        self.airport_destination_checkbox_named = ttk.Checkbutton(self.filter_frame, text="Аэропорт прилёта:",
                                                                  variable=self.airport_destination_checkbox_var,
                                                                  command=lambda: Main.FlowTransformations.AutoFlowFilter.update_airport_destination_checkbox(
                                                                      self, self.airport_destination_checkbox_var,
                                                                      self.airport_destination_entry,
                                                                      self.airport_destination_checkbox),
                                                                  style='Switch.TCheckbutton')
        self.airport_destination_checkbox_named.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.airport_destination_entry = ttk.Entry(self.filter_frame, width=10, state='disabled')
        self.airport_destination_entry.grid(row=4, column=1, padx=10, pady=10, sticky="w")
        self.airport_destination_button = ttk.Button(self.filter_frame, text="Аэропорт прилёта:")

        self.takeoff_to_landing_var = tk.IntVar()
        self.takeoff_to_landing_checkbox_named = ttk.Checkbutton(self.filter_frame,
                                                                 text="Порог высоты в начале и конце трека менее (м):",
                                                                 variable=self.takeoff_to_landing_var,
                                                                 command=lambda: Main.FlowTransformations.AutoFlowFilter.update_takeoff_to_landing_entry(
                                                                     self, self.takeoff_to_landing_var,
                                                                     self.takeoff_to_landing_entry),
                                                                 style='Switch.TCheckbutton')
        self.takeoff_to_landing_checkbox_named.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.takeoff_to_landing_entry = ttk.Entry(self.filter_frame, width=10, state='disabled')
        self.takeoff_to_landing_entry.grid(row=5, column=1, padx=10, pady=10, sticky="w")

        # столбик 2
        self.bort_number_var = tk.IntVar()
        self.bort_number_checkbox = ttk.Checkbutton(self.filter_frame, text="Указан номер борта",
                                                    variable=self.bort_number_var, style='Switch.TCheckbutton')
        self.bort_number_checkbox.grid(row=0, column=3, padx=10, pady=10, sticky="w")

        self.no_missing_coords_var = tk.IntVar()
        self.no_missing_coords_checkbox = ttk.Checkbutton(self.filter_frame, text="Нет пропущенных координат",
                                                          variable=self.no_missing_coords_var,
                                                          style='Switch.TCheckbutton')
        self.no_missing_coords_checkbox.grid(row=1, column=3, padx=10, pady=10, sticky="w")

        self.no_missing_altitude_var = tk.IntVar()
        self.no_missing_altitude_checkbox = ttk.Checkbutton(self.filter_frame, text="Нет пропущенной высоты",
                                                            variable=self.no_missing_altitude_var,
                                                            style='Switch.TCheckbutton')
        self.no_missing_altitude_checkbox.grid(row=2, column=3, padx=10, pady=10, sticky="w")

        self.airport_origin_var = tk.IntVar()
        self.airport_origin_checkbox = ttk.Checkbutton(self.filter_frame, text="Указан аэропорт вылета",
                                                       variable=self.airport_origin_var,
                                                       command=lambda: Main.FlowTransformations.AutoFlowFilter.update_airport_origin(
                                                           self, self.airport_origin_var,
                                                           self.airport_origin_checkbox_named,
                                                           self.airport_origin_entry), style='Switch.TCheckbutton')
        self.airport_origin_checkbox.grid(row=3, column=3, padx=10, pady=10, sticky="w")

        self.airport_destination_var = tk.IntVar()
        self.airport_destination_checkbox = ttk.Checkbutton(self.filter_frame, text="Указан аэропорт прилёта",
                                                            variable=self.airport_destination_var,
                                                            command=lambda: Main.FlowTransformations.AutoFlowFilter.update_airport_destination(
                                                                self, self.airport_destination_var,
                                                                self.airport_destination_checkbox_named,
                                                                self.airport_destination_entry),
                                                            style='Switch.TCheckbutton')
        self.airport_destination_checkbox.grid(row=4, column=3, padx=10, pady=10, sticky="w")

        self.cut_altitude_var = tk.IntVar()
        self.cut_altitude_checkbox = ttk.Checkbutton(self.filter_frame, text="Обрезать высоту 0м",
                                                     variable=self.cut_altitude_var, style='Switch.TCheckbutton')
        self.cut_altitude_checkbox.grid(row=5, column=3, padx=10, pady=10, sticky="w")

        # столбик 3
        self.speed_var = tk.IntVar()
        self.speed_checkbox = ttk.Checkbutton(self.filter_frame, text="Указана скорость", variable=self.speed_var,
                                              style='Switch.TCheckbutton')
        self.speed_checkbox.grid(row=0, column=4, padx=10, pady=10, sticky="w")

        self.callsign_var = tk.IntVar()  # позывной
        self.callsign_checkbox = ttk.Checkbutton(self.filter_frame, text="Указан callsign", variable=self.callsign_var,
                                                 style='Switch.TCheckbutton')
        self.callsign_checkbox.grid(row=1, column=4, padx=10, pady=10, sticky="w")

        self.type_vs_var = tk.IntVar()
        self.type_vs_checkbox = ttk.Checkbutton(self.filter_frame, text="Указан тип ВС", variable=self.type_vs_var,
                                                style='Switch.TCheckbutton')
        self.type_vs_checkbox.grid(row=2, column=4, padx=10, pady=10, sticky="w")

        self.check_dep_time_var = tk.IntVar()
        self.check_dep_time_checkbox = ttk.Checkbutton(self.filter_frame, text="Указано время вылета",
                                                       variable=self.check_dep_time_var, style='Switch.TCheckbutton')
        self.check_dep_time_checkbox.grid(row=3, column=4, padx=10, pady=10, sticky="w")

        self.check_arr_time_var = tk.IntVar()
        self.check_arr_time_checkbox = ttk.Checkbutton(self.filter_frame, text="Указано время прилёта",
                                                       variable=self.check_arr_time_var, style='Switch.TCheckbutton')
        self.check_arr_time_checkbox.grid(row=4, column=4, padx=10, pady=10, sticky="w")

        self.check_flightNumber_var = tk.IntVar()  # номер рейса
        self.check_flightNumber_checkbox = ttk.Checkbutton(self.filter_frame, text="Указан flightNumber",
                                                           variable=self.check_flightNumber_var,
                                                           style='Switch.TCheckbutton')
        self.check_flightNumber_checkbox.grid(row=5, column=4, padx=10, pady=10, sticky="w")

        # Вкладка "ручная сортировка потока"
        flow_sorter = FlowSorter(self)

        self.manual_sorting_frame = ttk.Frame(self.manual_sorting_tab)
        self.manual_sorting_frame.pack(fill="both", expand=True)

        self.file_label_sorting = ttk.Label(self.manual_sorting_frame, text="Выберите файл(ы):", font=self.font_txt,
                                            foreground='grey', justify="right", anchor="e")
        self.file_label_sorting.grid(row=0, column=0, padx=10, pady=10)

        self.file_entry_sorting = ttk.Entry(self.manual_sorting_frame, width=60)
        self.file_entry_sorting.grid(row=0, column=1, padx=10, pady=10)

        self.file_button_sorting = ttk.Button(self.manual_sorting_frame, text="Поиск",
                                              command=lambda: flow_sorter.find_json_files())
        self.file_button_sorting.grid(row=0, column=2, padx=10, pady=10)

        self.sorting_button = ttk.Button(self.manual_sorting_frame, text="Отсортировать", compound='left',
                                         command=lambda: flow_sorter.export_sorted_files(), style='Accent.TButton')
        self.sorting_button.grid(row=0, column=3, padx=10, pady=10)

        self.open_folder_button_sorting = ttk.Button(self.manual_sorting_frame, text="Открыть папку", compound='left',
                                                     command=lambda: Main.Functions.open_folder("flowSorted"))
        self.open_folder_button_sorting.grid(row=0, column=4, padx=10, pady=10)

        self.sorting_info_button = ttk.Button(self.manual_sorting_frame, text="⍰",
                                              command=lambda: Main.Functions.show_info(self, self.help_flowSorter),
                                              style='Toolbutton')
        self.sorting_info_button.grid(row=0, column=5, padx=5, pady=5)

        self.file_label_sorting = ttk.Label(self.manual_sorting_frame, text="Введите название:", font=self.font_txt,
                                            foreground='grey', justify="right", anchor="e")
        self.file_label_sorting.grid(row=1, column=0, padx=10, pady=10)

        self.output_file_entry_sorting = ttk.Entry(self.manual_sorting_frame, width=60,
                                                   textvariable=self.sorted_name_var)
        self.output_file_entry_sorting.grid(row=1, column=1, padx=0, pady=10)

        self.listbox_frame_sorting = ttk.LabelFrame(self.manual_sorting_frame, text="Сортировка потока")
        self.listbox_frame_sorting.grid(row=3, column=0, columnspan=6, padx=10, pady=10)

        self.stats_frame_sorting = ttk.Frame(self.listbox_frame_sorting)
        self.stats_frame_sorting.grid(row=2, column=0, columnspan=3, sticky="ew")

        self.stats_label_sorting = ttk.Label(self.stats_frame_sorting, font=self.font_txt)
        self.stats_label_sorting.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5)

        self.correct_count_label = ttk.Label(self.stats_frame_sorting, text="", font=self.font_txt)
        self.correct_count_label.grid(row=0, column=8, padx=50, pady=10)

        self.incorrect_count_label = ttk.Label(self.stats_frame_sorting, text="", font=self.font_txt)
        self.incorrect_count_label.grid(row=0, column=9, padx=2, pady=10)

        self.treeview_sorting = ttk.Treeview(self.listbox_frame_sorting, columns=(
            "id", "callsign", "flight_time", "route_points", "airport_origin", "airport_destination"))
        self.treeview_sorting.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        self.xscrollbar_sorting = ttk.Scrollbar(self.listbox_frame_sorting, orient="horizontal",
                                                command=self.treeview_sorting.xview)
        self.xscrollbar_sorting.grid(row=1, column=0, sticky="ew")

        self.yscrollbar_sorting = ttk.Scrollbar(self.listbox_frame_sorting, orient="vertical",
                                                command=self.treeview_sorting.yview)
        self.yscrollbar_sorting.grid(row=0, column=1, sticky="ns")

        self.treeview_sorting.config(xscrollcommand=self.xscrollbar_sorting.set,
                                     yscrollcommand=self.yscrollbar_sorting.set)

        self.treeview_sorting.heading("#0", text="Путь к файлу")
        self.treeview_sorting.heading("id", text="ID")
        self.treeview_sorting.heading("callsign", text="Номер рейса")
        self.treeview_sorting.heading("flight_time", text="Время полёта")
        self.treeview_sorting.heading("route_points", text="Точек маршрута")
        self.treeview_sorting.heading("airport_origin", text="Аэропорт вылета")
        self.treeview_sorting.heading("airport_destination", text="Аэропорт прилёта")

        self.treeview_sorting.column("#0", width=250)
        self.treeview_sorting.column("id", width=100)
        self.treeview_sorting.column("callsign", width=100)
        self.treeview_sorting.column("flight_time", width=100)
        self.treeview_sorting.column("route_points", width=100)
        self.treeview_sorting.column("airport_origin", width=100)
        self.treeview_sorting.column("airport_destination", width=120)

        self.listbox_frame_sorting.rowconfigure(0, weight=1)
        self.listbox_frame_sorting.columnconfigure(0, weight=1)

        self.treeview_sorting.heading("#0", text="File Path",
                                      command=lambda: Main.Functions.sort_by_column(self, self.treeview_sorting, "#0",
                                                                                    0))
        self.treeview_sorting.heading("id", text="ID",
                                      command=lambda: Main.Functions.sort_by_column(self, self.treeview_sorting, "id",
                                                                                    0))
        self.treeview_sorting.heading("callsign", text="Callsign",
                                      command=lambda: Main.Functions.sort_by_column(self, self.treeview_sorting,
                                                                                    "callsign", 0))
        self.treeview_sorting.heading("flight_time", text="Flight Time",
                                      command=lambda: Main.Functions.sort_by_column(self, self.treeview_sorting,
                                                                                    "flight_time", 0))
        self.treeview_sorting.heading("route_points", text="Route Points",
                                      command=lambda: Main.Functions.sort_by_column(self, self.treeview_sorting,
                                                                                    "route_points", 0))
        self.treeview_sorting.heading("airport_origin", text="Airport Origin",
                                      command=lambda: Main.Functions.sort_by_column(self, self.treeview_sorting,
                                                                                    "airport_origin", 0))
        self.treeview_sorting.heading("airport_destination", text="Airport Destination",
                                      command=lambda: Main.Functions.sort_by_column(self, self.treeview_sorting,
                                                                                    "airport_destination", 0))

        self.button_frame_sorting = ttk.Frame(self.listbox_frame_sorting)
        self.button_frame_sorting.grid(row=0, column=7, columnspan=1, rowspan=10, padx=10, pady=10)

        style_correct = ttk.Style()
        style_correct.configure("Correct.TButton", font=("Cooper Black", 13), foreground="DeepSkyBlue",
                                background="green")

        style_incorrect = ttk.Style()
        style_incorrect.configure("Incorrect.TButton", font=("Cooper Black", 13), foreground="MediumPurple",
                                  background="green")

        self.correct_pack_button = ttk.Button(self.button_frame_sorting, text="Корректный",
                                              command=lambda: flow_sorter.move_to_correct(), style="Correct.TButton")
        self.correct_pack_button.grid(row=0, column=2, padx=20, pady=20, sticky="ew", ipadx=6, ipady=6)

        self.incorrect_pack_button = ttk.Button(self.button_frame_sorting, text="Испорченный",
                                                command=lambda: flow_sorter.move_to_incorrect(),
                                                style="Incorrect.TButton")
        self.incorrect_pack_button.grid(row=1, column=2, padx=20, pady=20, sticky="ew", ipadx=6, ipady=6)

        self.remover_frame_sorting = ttk.Frame(self.button_frame_sorting)
        self.remover_frame_sorting.grid(row=2, column=0, columnspan=3, sticky="ew")

        self.undo_button = ttk.Button(self.remover_frame_sorting, text="Отменить шаг",
                                      command=lambda: flow_sorter.undo_last_move())
        self.undo_button.grid(row=0, column=1, padx=2, pady=20, sticky="ew", ipadx=0, ipady=0)

        self.undo_button = ttk.Button(self.remover_frame_sorting, text="Очистить всё",
                                      command=lambda: flow_sorter.clear_sort())
        self.undo_button.grid(row=0, column=2, padx=2, pady=20, sticky="ew", ipadx=0, ipady=0)

    # вкладка "вырезание участков треков" track_cutter_tab
        self.track_cutter_frame = ttk.Frame(self.track_cutter_tab)
        self.track_cutter_frame.pack(fill="both", expand=True)
        self.route_cutter = RouteCutter(self.track_cutter_frame)

    def restart_application(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.create_initial_window()

    def load_neural_notebook(self):
        self.initial_frame.pack_forget()
        self.neural_notebook = ttk.Notebook(self.root)
        self.neural_notebook.pack(expand=1, fill=tk.BOTH)

        self.neural_tab1 = ttk.Frame(self.neural_notebook)
        self.neural_tab2 = ttk.Frame(self.neural_notebook)

        self.neural_notebook.add(self.neural_tab1, text="Использование нейросети")
        self.neural_notebook.add(self.neural_tab2, text="Обучение нейросети")


    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = TrackTool("Sun-valley", "dark")
    #app.notebook.select(app.sniffer_tab)
    app.run()
