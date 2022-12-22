import PySimpleGUI as sg
import textwrap

COL_WIDTH = 60
TITLE_FONT = ("Arial bold", 26)


class Gui:
    def __init__(self, songs):
        # settings
        sg.theme("DarkRed")

        # define layout
        col1 = [
            [
                sg.Text("PLAYER", font=TITLE_FONT),
                sg.Push(),
                sg.Checkbox(
                    "Enable Buzzers", key="-ENABLE-", enable_events=True, default=True
                ),
                sg.Button("PLAY", key="-PLAYPAUSE-", enable_events=True),
            ],
            [
                sg.ProgressBar(
                    1.0, orientation="h", size=(COL_WIDTH, 10), key="-PROGRESS-"
                )
            ],
            [sg.StatusBar("No song loaded", size=(COL_WIDTH, 1), key="-SONG_DISPLAY-")],
            [
                sg.Multiline(
                    size=(COL_WIDTH, 7),
                    key="-SONG_INFO-",
                    disabled=True,
                    no_scrollbar=True,
                )
            ],
            [sg.T()],
            [sg.VPush()],
            [
                sg.Text("LIBRARY", font=TITLE_FONT),
                sg.Push(),
                sg.Button(" ✓ ", key="-MARK-", enable_events=True),
                sg.Button("LOAD", key="-LOAD-", enable_events=True),
            ],
            [
                sg.Listbox(
                    values=[song.title for song in songs],
                    enable_events=True,
                    size=(COL_WIDTH, 20),
                    key="-SONGS-",
                    no_scrollbar=True,
                )
            ],
        ]

        col2 = [
            [sg.Text("TEAMS", font=TITLE_FONT)],
            [
                sg.Frame(
                    "RED",
                    [
                        [
                            sg.Text("Points:", pad=(15, 15)),
                            sg.StatusBar(
                                "0",
                                size=(1, 1),
                                key="-RED_POINTS-",
                                font=("Arial", 26),
                            ),
                            sg.T(s=2),
                            sg.Text("Time Penalty:", pad=(15, 15)),
                            sg.StatusBar(
                                "-",
                                size=(2, 1),
                                key="-RED_PENALTIES-",
                                font=("Arial", 26),
                            ),
                            sg.Push(),
                            sg.Button(
                                "UPDATE",
                                key="-EDIT_RED-",
                                enable_events=True,
                                pad=(15, 15),
                            ),
                        ]
                    ],
                    expand_x=True,
                )
            ],
            [
                sg.Frame(
                    "BLUE",
                    [
                        [
                            sg.Text("Points:", pad=(15, 15)),
                            sg.StatusBar(
                                "0",
                                size=(1, 1),
                                key="-BLUE_POINTS-",
                                font=("Arial", 26),
                            ),
                            sg.T(s=2),
                            sg.Text("Time Penalty:", pad=(15, 15)),
                            sg.StatusBar(
                                "-",
                                size=(2, 1),
                                key="-BLUE_PENALTIES-",
                                font=("Arial", 26),
                            ),
                            sg.Push(),
                            sg.Button(
                                "UPDATE",
                                key="-EDIT_BLUE-",
                                enable_events=True,
                                pad=(15, 15),
                            ),
                        ]
                    ],
                    expand_x=True,
                )
            ],
            [sg.T()],
            [sg.VPush()],
            [sg.Text("EVENT LOG", font=TITLE_FONT)],
            [
                sg.Multiline(
                    size=(COL_WIDTH, 21),
                    key="-LOG-",
                    disabled=True,
                    no_scrollbar=True,
                )
            ],
        ]

        layout = [
            [
                sg.Column(col1, expand_y=True),
                sg.T(),
                sg.Column(col2, expand_y=True),
            ]
        ]

        window = sg.Window(
            "Music Quiz Control Board", layout, finalize=True, font=("Arial", 15)
        )
        self.window = window
        self.set_song_index(0)
        sg.cprint_set_output_destination(self.window, "-LOG-")

    def get_event(self):
        event, values = self.window.read(timeout=10)
        if event == sg.WIN_CLOSED:
            event = "Exit"
        return event

    def song_index(self):
        return self.window["-SONGS-"].get_indexes()[0]

    def set_song_index(self, index):
        self.window["-SONGS-"].update(set_to_index=[index])

    def reload_song_list(self, songs):
        index = self.song_index()
        names = ["   ✓   " + s.title if s.used else s.title for s in songs]
        self.window["-SONGS-"].update(
            values=names, set_to_index=index, scroll_to_index=index
        )

    def update_player_info(self, song):
        self.window["-SONG_DISPLAY-"].update(song.title)
        self.window["-SONG_INFO-"].update(song.note)

    def log(self, msg, new=False, indent=False):
        if new:
            sg.cprint("")
        msg = textwrap.shorten(msg, width=COL_WIDTH)
        if indent:
            msg = "   •   " + msg
        sg.cprint(msg)

    def update_progress_bar(self, position):
        self.window["-PROGRESS-"].update(position)

    # popup related
    def open_popup(self, msg):
        # define layout
        layout = [
            [
                sg.Push(),
                sg.Text(msg.upper(), font=TITLE_FONT),
                sg.Push(),
            ],
            [
                sg.Frame(
                    "PENALTY",
                    [
                        [
                            sg.Button(
                                "+5 seconds",
                                key="-PENALTY-",
                                enable_events=True,
                                pad=((10, 0), 10),
                            ),
                            sg.Button(
                                "Clear",
                                key="-CLEAR_PENALTY-",
                                enable_events=True,
                                pad=(10, 10),
                            ),
                        ]
                    ],
                    expand_x=True,
                    pad=(5, 20),
                ),
                sg.Frame(
                    "POINTS",
                    [
                        [
                            sg.Spin(
                                values=list(range(1, 11)),
                                initial_value=1,
                                size=(2, 1),
                                key="-POINTS-",
                                pad=((10, 0), 10),
                                font=("Arial", 20),
                            ),
                            sg.Button(
                                "Award",
                                key="-GIVE-",
                                enable_events=True,
                                pad=((10, 0), 10),
                            ),
                            sg.Button(
                                "Deduct",
                                key="-DEDUCT-",
                                enable_events=True,
                                pad=(10, 10),
                            ),
                        ]
                    ],
                    expand_x=True,
                    pad=(5, 20),
                ),
            ],
            [
                sg.Push(),
                sg.Button(
                    "DONE",
                    key="-DONE-",
                    enable_events=True,
                ),
                sg.Push(),
            ],
        ]

        popup = sg.Window(msg, layout, finalize=True, font=("Arial", 15))
        self.popup = popup

    def get_popup_event(self):
        if self.popup is None:
            return None
        event, values = self.popup.read(timeout=10)
        if event == sg.WIN_CLOSED:
            event = "Exit"
        return event

    def close_popup(self):
        self.popup.close()
        self.popup = None
