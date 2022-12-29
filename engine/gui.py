import PySimpleGUI as sg
import textwrap

COL_WIDTH = 60
TITLE_FONT = ("Arial bold", 26)
FONT = ("Arial", 15)


class Gui:
    def __init__(self, cfg):
        # settings
        sg.theme("DarkRed")

        # define layout
        col1 = [*get_player_layout(), [sg.VPush()], *get_library_layout(cfg)]
        col2 = [*get_teams_layout(cfg), *get_log_layout()]
        layout = [
            [sg.Column(col1, expand_y=True), sg.T(), sg.Column(col2, expand_y=True)]
        ]

        self.window = sg.Window(
            cfg.title,
            layout,
            finalize=True,
            font=FONT,
            enable_close_attempted_event=False,
        )
        self.set_song_index(0)
        sg.cprint_set_output_destination(self.window, "-LOG-")

    def get_event(self):
        event, values = self.window.read(timeout=10)
        if event == sg.WINDOW_CLOSED:
            event = "Exit"
        return event

    def song_index(self):
        return self.window["-SONGS-"].get_indexes()[0]

    def set_song_index(self, index):
        self.window["-SONGS-"].update(set_to_index=[index])

    def reload_song_list(self, songs, used):
        index = self.song_index()
        names = []
        for (i, s) in enumerate(songs):
            names.append("   ✓   " + s.title if used[i] else s.title)

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
    def open_popup(self, msg, cfg):
        self.popup = sg.Window(
            msg, get_popup_layout(msg, cfg), finalize=True, font=FONT, keep_on_top=True
        )

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


# Main window layout
def get_player_layout():
    return [
        [
            sg.Text("PLAYER", font=TITLE_FONT),
            sg.Push(),
            sg.Checkbox(
                "Enable Buzzers", key="-ENABLE-", enable_events=True, default=True
            ),
            sg.Button("PLAY", key="-PLAYPAUSE-", enable_events=True),
        ],
        [sg.ProgressBar(1.0, orientation="h", size=(COL_WIDTH, 10), key="-PROGRESS-")],
        [sg.StatusBar("No song loaded", size=(COL_WIDTH, 1), key="-SONG_DISPLAY-")],
        [
            sg.Multiline(
                size=(COL_WIDTH, 7),
                key="-SONG_INFO-",
                write_only=True,
                no_scrollbar=True,
                right_click_menu=['', ['Copy::info']]
            )
        ],
        [sg.T()],
    ]


def get_library_layout(cfg):
    return [
        [
            sg.Text("LIBRARY", font=TITLE_FONT),
            sg.Push(),
            sg.Button(" ✓ ", key="-MARK-", enable_events=True),
            sg.Button("LOAD", key="-LOAD-", enable_events=True),
        ],
        [
            sg.Listbox(
                values=[song.title for song in cfg.songs],
                enable_events=True,
                size=(COL_WIDTH, 25),
                key="-SONGS-",
                no_scrollbar=True,
            )
        ],
    ]


def get_team_layout(team):
    return [
        sg.Frame(
            team.name,
            [
                [
                    sg.Text("Points:", pad=(15, 15)),
                    sg.StatusBar(
                        "0",
                        size=(1, 1),
                        key=f"-{team.name}_POINTS-",
                        font=("Arial", 26),
                    ),
                    sg.T(s=2),
                    sg.Text("Time Penalty:", pad=(15, 15)),
                    sg.StatusBar(
                        "-",
                        size=(2, 1),
                        key=f"-{team.name}_PENALTIES-",
                        font=("Arial", 26),
                    ),
                    sg.Push(),
                    sg.Button(
                        "UPDATE",
                        key=f"-{team.name}_EDIT-",
                        enable_events=True,
                        pad=(15, 15),
                    ),
                ]
            ],
            expand_x=True,
        )
    ]


def get_teams_layout(cfg):
    return [
        [sg.Text("TEAMS", font=TITLE_FONT)],
        *[get_team_layout(team) for team in cfg.teams.values()],
        [sg.T()],
    ]


def get_log_layout():
    return [
        [sg.Text("EVENT LOG", font=TITLE_FONT)],
        [
            sg.Multiline(
                size=COL_WIDTH,
                key="-LOG-",
                write_only=True,
                no_scrollbar=True,
                expand_y=True,
                right_click_menu=['', ['Copy::log']]
            )
        ],
    ]


# Popup layout
def get_popup_layout(msg, cfg):
    return [
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
                            f"+{cfg.penalty_time} seconds",
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
